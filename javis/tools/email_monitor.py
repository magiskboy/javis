import base64
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from javis.helper import get_google_crendential
from javis.tools.calendar import create_calendar_event
from javis.tools.telegram import send_telegram_message
from typing import List, Optional
from javis.tools.gmail import send_email
from javis.tools.email_monitor_task import add_thread_to_monitor


def get_gmail_service():
    """Get Gmail service instance."""
    creds = get_google_crendential()
    return build("gmail", "v1", credentials=creds)


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
        content = ""
        if "payload" in msg and "parts" in msg["payload"]:
            for part in msg["payload"]["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data", "")
                    if data:
                        content += base64.urlsafe_b64decode(data).decode("utf-8")
        elif "payload" in msg and "body" in msg["payload"]:
            data = msg["payload"]["body"].get("data", "")
            if data:
                content += base64.urlsafe_b64decode(data).decode("utf-8")

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
            # Extract potential date/time information
            # This is a simple implementation - you might want to use a more sophisticated
            # date/time extraction method in production

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


async def send_and_monitor_candidate_email(
    candidate_email: str,
    subject: str,
    body: str,
    hr_telegram_id: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    is_html: bool = False,
    expiry_hours: int = 48,
) -> dict:
    """Send an email to a candidate and start monitoring for replies.

    Args:
        candidate_email: Candidate's email address
        subject: Email subject
        body: Email body content
        hr_telegram_id: Telegram ID of HR to notify about replies
        cc: Optional list of CC recipients
        bcc: Optional list of BCC recipients
        is_html: Whether the body content is HTML
        expiry_hours: How long to monitor for replies

    Returns:
        dict: Response containing email sending and monitoring status
    """
    # Send the email
    email_result = await send_email(
        to_email=candidate_email,
        subject=subject,
        body=body,
        cc=cc,
        bcc=bcc,
        is_html=is_html,
    )

    if email_result["status"] == "success":
        # Start monitoring the thread
        await add_thread_to_monitor(
            thread_id=email_result["thread_id"],
            candidate_email=candidate_email,
            hr_telegram_id=hr_telegram_id,
            expiry_hours=expiry_hours,
        )

        return {
            "status": "success",
            "email_result": email_result,
            "monitoring": {
                "thread_id": email_result["thread_id"],
                "expiry_hours": expiry_hours,
            },
        }

    return {
        "status": "failed",
        "error": email_result.get("error", "Failed to send email"),
        "email_result": email_result,
    }
