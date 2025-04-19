import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

from javis.tools.email_base import get_gmail_service, extract_email_content
from javis.tools.calendar import create_calendar_event
from javis.tools.telegram import send_telegram_message

logger = logging.getLogger(__name__)

# Store thread IDs and their monitoring info
monitored_threads: Dict[str, dict] = {}

# Flag to control the monitoring loop
is_running = True


async def add_thread_to_monitor(
    thread_id: str,
    candidate_email: str,
    hr_telegram_id: str = "5318643303",
    expiry_hours: int = 48,
) -> None:
    """Add a thread to the monitoring list.

    Args:
        thread_id: Gmail thread ID to monitor
        candidate_email: Candidate's email address
        hr_telegram_id: Telegram ID of HR to notify
        expiry_hours: How long to monitor the thread (default: 48 hours)
    """
    monitored_threads[thread_id] = {
        "candidate_email": candidate_email,
        "hr_telegram_id": hr_telegram_id,
        "expiry_time": datetime.now() + timedelta(hours=expiry_hours),
        "last_message_id": None,
    }


async def remove_thread_from_monitor(thread_id: str) -> None:
    """Remove a thread from monitoring."""
    if thread_id in monitored_threads:
        del monitored_threads[thread_id]


async def check_email_replies(thread_id: str) -> dict:
    """Check for replies in a specific email thread.

    Args:
        thread_id: The Gmail thread ID to check for replies

    Returns:
        dict: Response containing reply information or error details
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
        return {"status": "error", "error": str(e)}


async def process_candidate_reply(
    reply_content: str, candidate_email: str, hr_telegram_id: str
) -> dict:
    """Process a candidate's email reply and take appropriate action.

    Args:
        reply_content: The content of the candidate's reply email
        candidate_email: The candidate's email address
        hr_telegram_id: Telegram ID of the HR person to notify

    Returns:
        dict: Response containing processing results
    """
    try:
        # Simple keyword-based analysis of the reply
        reply_lower = reply_content.lower()

        # Check if candidate agrees to schedule
        if any(
            word in reply_lower
            for word in ["yes", "agree", "confirm", "available", "sure"]
        ):
            # For now, schedule for tomorrow at 10 AM as an example
            tomorrow = datetime.now() + timedelta(days=1)
            start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)

            # Create calendar event
            calendar_result = await create_calendar_event(
                summary=f"Interview with {candidate_email}",
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                description="Interview session",
                attendees=[candidate_email],
                timezone="Asia/Ho_Chi_Minh",
            )

            if "error" not in calendar_result:
                return {
                    "status": "success",
                    "action": "scheduled",
                    "calendar_event": calendar_result,
                }
            else:
                return {
                    "status": "error",
                    "error": f"Failed to create calendar event: {calendar_result['error']}",
                }

        else:  # Candidate likely declined or had other response
            # Notify HR via Telegram
            notification = f"Candidate {candidate_email} has responded to the interview invitation. Response: {reply_content[:200]}..."

            telegram_result = await send_telegram_message(
                recipient=hr_telegram_id, message=notification
            )

            return {
                "status": "success",
                "action": "notified_hr",
                "telegram_result": telegram_result,
            }

    except Exception as e:
        return {"status": "error", "error": str(e)}


async def check_threads() -> None:
    """Check all monitored threads for new replies."""
    current_time = datetime.now()

    # Create a list of threads to remove (expired or processed)
    threads_to_remove = []

    for thread_id, thread_info in monitored_threads.items():
        print(f"Checking thread {monitored_threads}")
        # Check if thread monitoring has expired
        if current_time > thread_info["expiry_time"]:
            threads_to_remove.append(thread_id)
            continue

        try:
            # Check for replies
            reply_check = await check_email_replies(thread_id)

            if reply_check["status"] == "success" and reply_check["has_reply"]:
                # If this is a new reply (not one we've processed before)
                if reply_check["message_id"] != thread_info["last_message_id"]:
                    # Process the reply
                    await process_candidate_reply(
                        reply_content=reply_check["reply_content"],
                        candidate_email=thread_info["candidate_email"],
                        hr_telegram_id=thread_info["hr_telegram_id"],
                    )

                    # Update the last processed message ID
                    thread_info["last_message_id"] = reply_check["message_id"]

        except Exception as e:
            logger.error(f"Error checking thread {thread_id}: {str(e)}")

    # Remove expired/processed threads
    for thread_id in threads_to_remove:
        await remove_thread_from_monitor(thread_id)


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
    """Stop the email monitoring task gracefully."""
    global is_running
    is_running = False
