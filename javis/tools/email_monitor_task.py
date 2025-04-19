import asyncio
import logging
from typing import Dict, List
from datetime import datetime, timedelta
import asyncpg
from javis import settings
from javis.tools.email_base import get_gmail_service, extract_email_content
from javis.tools.calendar import create_calendar_event
from javis.tools.telegram import send_telegram_message
from javis.models.monitored_thread import MonitoredThread
import json
from pydantic import BaseModel, Field
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from javis.tools.gmail import send_email

logger = logging.getLogger(__name__)


# Flag to control the monitoring loop
is_running = True


async def get_db_connection():
    """Get a database connection.

    Returns:
        asyncpg.Connection: A connection to the PostgreSQL database.

    Raises:
        asyncpg.exceptions.PostgresError: If connection fails.
    """
    return await asyncpg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
    )


async def add_thread_to_monitor(
    thread_id: str,
    candidate_email: str,
    hr_telegram_id: str = "5318643303",
    expiry_hours: int = 48,
) -> None:
    """Add a thread to the monitoring list.

    Args:
        thread_id (str): Gmail thread ID to monitor
        candidate_email (str): Candidate's email address
        hr_telegram_id (str, optional): Telegram ID of HR to notify. Defaults to "5318643303"
        expiry_hours (int, optional): How long to monitor the thread. Defaults to 48 hours

    Raises:
        asyncpg.exceptions.PostgresError: If database operation fails
    """
    conn = await get_db_connection()
    try:
        expiry_time = datetime.now() + timedelta(hours=expiry_hours)
        await conn.execute(
            """
            INSERT INTO monitored_threads (
                thread_id, candidate_email, hr_telegram_id, expiry_time
            ) VALUES ($1, $2, $3, $4)
            ON CONFLICT (thread_id) 
            DO UPDATE SET 
                candidate_email = EXCLUDED.candidate_email,
                hr_telegram_id = EXCLUDED.hr_telegram_id,
                expiry_time = EXCLUDED.expiry_time,
                updated_at = CURRENT_TIMESTAMP
        """,
            thread_id,
            candidate_email,
            hr_telegram_id,
            expiry_time,
        )
        logger.info(f"Added thread to monitor: {thread_id}")
    finally:
        await conn.close()


async def remove_thread_from_monitor(thread_id: str) -> None:
    """Remove a thread from monitoring.

    Args:
        thread_id (str): The ID of the thread to remove from monitoring

    Raises:
        asyncpg.exceptions.PostgresError: If database operation fails
    """
    conn = await get_db_connection()
    try:
        await conn.execute(
            """
            DELETE FROM monitored_threads 
            WHERE thread_id = $1
        """,
            thread_id,
        )
    finally:
        await conn.close()


async def get_active_threads() -> List[MonitoredThread]:
    """Get all active monitored threads.

    Returns:
        List[MonitoredThread]: List of active threads that haven't expired

    Raises:
        asyncpg.exceptions.PostgresError: If database operation fails
    """
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT * FROM monitored_threads 
            WHERE expiry_time > CURRENT_TIMESTAMP
        """
        )
        return [MonitoredThread(**dict(row)) for row in rows]
    finally:
        await conn.close()


async def update_thread_message_id(thread_id: str, message_id: str) -> None:
    """Update the last processed message ID for a thread.

    Args:
        thread_id (str): The ID of the thread to update
        message_id (str): The ID of the last processed message

    Raises:
        asyncpg.exceptions.PostgresError: If database operation fails
    """
    conn = await get_db_connection()
    try:
        await conn.execute(
            """
            UPDATE monitored_threads 
            SET last_message_id = $2, updated_at = CURRENT_TIMESTAMP
            WHERE thread_id = $1
        """,
            thread_id,
            message_id,
        )
    finally:
        await conn.close()


async def remove_expired_threads() -> None:
    """Remove expired threads from the database.

    Raises:
        asyncpg.exceptions.PostgresError: If database operation fails
    """
    conn = await get_db_connection()
    try:
        await conn.execute(
            """
            DELETE FROM monitored_threads 
            WHERE expiry_time <= CURRENT_TIMESTAMP
        """
        )
    finally:
        await conn.close()

async def check_email_replies(thread_id: str) -> dict:
    """Check for replies in a specific email thread.

    Args:
        thread_id (str): The Gmail thread ID to check for replies

    Returns:
        dict: A dictionary containing:
            - status (str): 'success' or 'error'
            - has_reply (bool): Whether there are new replies (only if status is 'success')
            - reply_content (str, optional): Content of the reply if exists
            - message_id (str, optional): ID of the reply message if exists
            - thread_id (str, optional): The thread ID being checked
            - error (str, optional): Error message if status is 'error'

    Raises:
        Exception: If Gmail API call fails
    """
    try:
        service = get_gmail_service()

        # Get the thread
        thread = service.users().threads().get(userId="me", id=thread_id).execute()
        # Get messages in thread
        messages = thread.get("messages", [])
        # If there's only one message, there are no replies
        if len(messages) <= 1:
            return {"status": "success", "has_reply": False, "reply_content": None}

        # Get the most recent message (reply)
        latest_message = messages[-1]

        # Get message payload
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=latest_message["id"])
            .execute()
        )

        # Extract message content
        content = extract_email_content(msg)

        return {
            "status": "success",
            "has_reply": True,
            "reply_content": content,
            "message_id": latest_message["id"],
            "thread_id": thread_id,
        }

    except Exception as e:
        print(f"Error checking email replies: {str(e)}")
        return {"status": "error", "error": str(e)}


async def send_confirmation_email(to_email: str, meeting_time: datetime) -> dict:
    """Send a confirmation email to the candidate after scheduling the interview.

    Args:
        to_email (str): Candidate's email address
        meeting_time (datetime): Scheduled meeting time

    Returns:
        dict: Response from send_email function
    """
    subject = "Interview Confirmation"
    formatted_time = meeting_time.strftime("%A, %B %d, %Y at %I:%M %p")
    body = f"""Dear Candidate,

Thank you for confirming your interview. We have scheduled the interview for {formatted_time} (Vietnam time).

We look forward to meeting with you. If you need to make any changes, please let us know.

Best regards,
HR Team"""

    return await send_email(to_email=to_email, subject=subject, body=body)


async def send_followup_email(to_email: str, analysis: dict) -> dict:
    """Send a follow-up email when candidate declines or needs clarification.

    Args:
        to_email (str): Candidate's email address
        analysis (dict): AI analysis of candidate's response

    Returns:
        dict: Response from send_email function
    """
    if analysis["suggested_action"] == "request_clarification":
        subject = "Interview Scheduling - Clarification Needed"
        body = """Dear Candidate,

Thank you for your response. We would appreciate if you could provide more specific details about your preferred interview time. Please let us know what dates and times work best for you.

Best regards,
HR Team"""
    else:
        subject = "Thank You for Your Response"
        body = """Dear Candidate,

Thank you for taking the time to respond to our interview invitation. We appreciate your feedback and wish you the best in your future endeavors.

Best regards,
HR Team"""

    return await send_email(to_email=to_email, subject=subject, body=body)


async def analyze_candidate_response(response_text: str) -> dict:
    from javis.agent import create_agent, process_prompt

    """Analyze candidate's email response using Gemini AI to determine their intent.

    Args:
        response_text (str): The candidate's email response text

    Returns:
        dict: Analysis result containing:
            - agrees_to_schedule (bool): Whether the candidate agrees to schedule
            - confirm_datetime (str): Extracted datetime if available (YYYY-MM-DD HH:MM)
            - confidence_score (float): Confidence in the analysis (0-1)
            - suggested_action (str): Recommended next action
            - explanation (str): Explanation of the analysis
    """
    agent = create_agent()

    prompt = f"""Analyze the following email response from a job candidate and determine if they are agreeing to schedule an interview.
                Consider the full context and nuances of their response, not just specific keywords.
                If they agree to schedule, carefully extract any mentioned date and time preferences.

                Response: {response_text}

                Provide your analysis in the following JSON format:
                {{
                    "agrees_to_schedule": true/false,
                    "confirm_datetime": "YYYY-MM-DD HH:MM" or null,
                    "confidence_score": 0.0-1.0,
                    "suggested_action": "schedule_interview" or "notify_hr" or "request_clarification",
                    "explanation": "Brief explanation of your analysis"
                }}

                Focus on understanding:
                1. Overall tone and context
                2. Any specific date/time preferences mentioned (convert to YYYY-MM-DD HH:MM format)
                3. Level of enthusiasm
                4. Any potential concerns raised

                Examples of datetime extraction:
                - "I can do next Monday at 2pm" → Extract next Monday's date and set time to 14:00
                - "Tomorrow afternoon at 3" → Extract tomorrow's date and set time to 15:00
                - "Friday morning" → Extract next Friday's date and set time to 09:00
                """

    return await process_prompt(prompt, agent)


async def process_candidate_reply(
    reply_content: str, candidate_email: str, hr_telegram_id: str
) -> dict:
    """Process a candidate's email reply and take appropriate action.

    Args:
        reply_content (str): The content of the candidate's reply email
        candidate_email (str): The candidate's email address
        hr_telegram_id (str): Telegram ID of the HR person to notify

    Returns:
        dict: A dictionary containing:
            - status (str): 'success' or 'error'
            - action (str, optional): 'scheduled' or 'notified_hr' if successful
            - calendar_event (dict, optional): Calendar event details if scheduled
            - telegram_result (dict, optional): Telegram notification result if sent
            - error (str, optional): Error message if status is 'error'
            - analysis (dict, optional): AI analysis of the response

    Raises:
        Exception: If calendar creation or telegram notification fails
    """
    try:
        # Use AI to analyze the candidate's response
        raw_response = await analyze_candidate_response(reply_content)

        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_response)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = raw_response.strip()
        analysis = json.loads(json_str)

        # If AI is confident the candidate agrees to schedule
        if (
            analysis["agrees_to_schedule"]
            and float(analysis["confidence_score"]) >= 0.5
        ):
            # Use the extracted datetime if available, otherwise default to tomorrow
            if analysis.get("confirm_datetime"):
                meeting_time = datetime.strptime(
                    analysis["confirm_datetime"], "%Y-%m-%d %H:%M"
                )
            else:
                meeting_time = datetime.now() + timedelta(days=1)
                meeting_time = meeting_time.replace(
                    hour=10, minute=0, second=0, microsecond=0
                )

            end_time = meeting_time + timedelta(hours=1)

            # Create calendar event
            calendar_result = await create_calendar_event(
                summary=f"Interview with {candidate_email}",
                start_time=meeting_time.isoformat(),
                end_time=end_time.isoformat(),
                description=f"Interview session\n\nCandidate Response Analysis:\n{analysis['explanation']}",
                attendees=[candidate_email],
                timezone="Asia/Ho_Chi_Minh",
            )

            if "error" not in calendar_result:
                # Send confirmation email
                email_result = await send_confirmation_email(
                    candidate_email, meeting_time
                )

                return {
                    "status": "success",
                    "action": "scheduled",
                    "calendar_event": calendar_result,
                    "email_result": email_result,
                    "analysis": analysis,
                }
            else:
                return {
                    "status": "error",
                    "error": f"Failed to create calendar event: {calendar_result['error']}",
                    "analysis": analysis,
                }

        else:  # AI suggests not scheduling or needs clarification
            # Send follow-up email
            email_result = await send_followup_email(candidate_email, analysis)

            # Notify HR via Telegram with AI analysis
            notification = (
                f"Candidate {candidate_email} has responded to the interview invitation.\n\n"
                f"Response: {reply_content[:200]}...\n\n"
                f"AI Analysis:\n"
                f"- Agrees to Schedule: {analysis['agrees_to_schedule']}\n"
                f"- Confidence: {analysis['confidence_score']:.2f}\n"
                f"- Suggested Action: {analysis['suggested_action']}\n"
                f"- Explanation: {analysis['explanation']}"
            )

            telegram_result = await send_telegram_message(
                recipient=hr_telegram_id, message=notification
            )

            return {
                "status": "success",
                "action": "notified_hr",
                "telegram_result": telegram_result,
                "email_result": email_result,
                "analysis": analysis,
            }

    except Exception as e:
        logger.error(f"Error processing candidate reply: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
        }


async def check_threads() -> None:
    """Check all monitored threads for new replies.

    This function:
    1. Removes expired threads from the database
    2. Gets all active threads
    3. Checks each thread for new replies
    4. Processes any new replies found
    5. Updates the last processed message ID

    Raises:
        Exception: If any step in the process fails
    """
    try:
        # Remove expired threads
        await remove_expired_threads()

        # Get active threads
        active_threads = await get_active_threads()
        for thread in active_threads:
            try:
                # Check for replies
                reply_check = await check_email_replies(thread.thread_id)
                if reply_check["status"] == "success" and reply_check["has_reply"]:
                    # If this is a new reply (not one we've processed before)
                    if reply_check["message_id"] != thread.last_message_id:
                        # Process the reply
                        await process_candidate_reply(
                            reply_content=reply_check["reply_content"],
                            candidate_email=thread.candidate_email,
                            hr_telegram_id=thread.hr_telegram_id,
                        )

                        # Update the last processed message ID
                        await update_thread_message_id(
                            thread.thread_id, reply_check["message_id"]
                        )

            except Exception as e:
                logger.error(f"Error checking thread {thread.thread_id}: {str(e)}")

    except Exception as e:
        logger.error(f"Error in check_threads: {str(e)}")


async def start_monitoring() -> None:
    """Start the email monitoring background task."""
    print("Gmail bot is running")
    global is_running
    is_running = True

    try:
        while is_running:
            try:
                print("Checking threads")
                await check_threads()
                await asyncio.sleep(10)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Wait a bit before retrying on error
    finally:
        logger.info("Email monitoring service stopped")


async def stop_monitoring() -> None:
    """Stop the email monitoring task gracefully.

    This function sets the is_running flag to False, which will cause the
    monitoring loop to exit after its current iteration completes.
    """
    global is_running
    is_running = False
