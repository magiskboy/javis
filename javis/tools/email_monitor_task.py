import asyncio
import logging
from typing import List
from datetime import datetime, timedelta
import asyncpg
from pydantic_ai import Agent
from javis import settings
from javis.tools.email_base import get_gmail_service, extract_email_content
from javis.models.monitored_thread import MonitoredThread

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
        message_id (str): The Message-ID header value of the last processed message

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

        # Get the latest message
        latest_message = messages[-1]

        # Get message payload of the latest message
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=latest_message["id"])
            .execute()
        )

        # Get message ID from headers
        headers = msg["payload"]["headers"]
        message_id = None
        for header in headers:
            if header["name"].lower() == "message-id":
                message_id = header["value"]
                break

        if not message_id:
            message_id = latest_message["id"]

        # Extract message content
        content = extract_email_content(msg)

        return {
            "status": "success",
            "has_reply": True,
            "reply_content": content,
            "message_id": message_id,  # Using Message-ID header instead of Gmail ID
            "thread_id": thread_id,
        }

    except Exception as e:
        logger.error(f"Error checking email replies: {str(e)}")
        return {"status": "error", "error": str(e)}


async def check_threads(agent: Agent) -> None:
    """Check all monitored threads for new replies.

    This function:
    1. Removes expired threads from the database
    2. Gets all active threads
    3. Checks each thread for new replies
    4. Processes any new replies found
    5. Updates the last processed message ID

    Args:
        agent (Agent): The AI agent to process responses

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
                        candidate_email = thread.candidate_email
                        thread_id = reply_check["thread_id"]

                        rag = f"""
                        This is the candidate's response from the {candidate_email} in the thread {thread_id}:
                        {reply_check["reply_content"]}

                        And this is instructions to make the right decision:

                        You are a recruitment assistant responsible for reviewing candidate responses regarding their availability for a discussion. Based on the candidate's reply, you need to determine their intent and take the appropriate action as follows:

                        1. If the candidate declines to discuss
                        (e.g., they say they're not interested, not available, or politely refuse):
                        → Send a thank-you email and wish them well for the future.

                        2. If the candidate:
                        Does not provide a specific time
                        (e.g., "I'll check my schedule and get back to you", "I'm currently busy", "Maybe in the afternoon but not sure"), or

                        Offers a time slot shorter than 1 hour
                        (e.g., "I'm free for 15 minutes at 3 PM")
                        → Send an email requesting the candidate to confirm a specific time slot as soon as possible so that a meeting can be arranged.

                        3. If the candidate:
                        Provides a clear time window longer than 1 hour
                        (e.g., "I'm available from 2 PM to 4 PM"), or

                        Provides a start time without specifying duration
                        (e.g., "I'm free at 10 AM")
                        → Create a meeting in Google Calendar using the given time (default to 1 hour if no duration is provided), and send a confirmation email to the candidate.

                        IMPORTANT: When sending any email response, make sure to:
                        1. Use the thread_id: {thread_id} to maintain the email conversation
                        2. Keep the email professional and friendly
                        3. Don't mention AI or automation
                        """

                        from javis.agent import process_prompt

                        await process_prompt(rag, agent)

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
    from javis.agent import create_agent
    agent = create_agent()

    try:
        while is_running:
            try:
                print("Checking threads")
                await check_threads(agent)
                await asyncio.sleep(30)  # Check every 5 minutes
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
