from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from googleapiclient.discovery import build
from javis.helper import get_google_crendential


def get_gmail_service():
    creds = get_google_crendential()
    return build("gmail", "v1", credentials=creds)


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    is_html: bool = False,
    thread_id: Optional[str] = None,
) -> dict:
    """Send an email using Gmail API.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        cc: Optional list of CC recipients
        bcc: Optional list of BCC recipients
        is_html: Whether the body content is HTML (default: False)
        thread_id: Optional thread ID to reply to an existing thread

    Returns:
        dict: Response containing status and message details or error information

    Examples:
        >>> # Send new email
        >>> await send_email(
        ...     "recipient@example.com",
        ...     "Hello",
        ...     "This is a test email"
        ... )

        >>> # Reply to existing thread
        >>> await send_email(
        ...     "recipient@example.com",
        ...     "Re: Hello",
        ...     "This is a reply",
        ...     thread_id="thread_123"
        ... )
    """
    try:
        service = get_gmail_service()

        # Create message container
        message = MIMEMultipart()
        message["to"] = to_email
        message["subject"] = subject

        if cc:
            message["cc"] = ", ".join(cc)
        if bcc:
            message["bcc"] = ", ".join(bcc)

        # Add body
        if is_html:
            msg = MIMEText(body, "html")
        else:
            msg = MIMEText(body, "plain")
        message.attach(msg)

        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        try:
            # Prepare the message request
            message_request = {"raw": raw_message}

            # If thread_id is provided, add it to continue the thread
            if thread_id:
                message_request["threadId"] = thread_id
                print(f"Sending reply to thread: {thread_id}")

            # Send the email
            sent_message = (
                service.users()
                .messages()
                .send(userId="me", body=message_request)
                .execute()
            )

            # Only monitor new threads (not replies)
            if not thread_id:
                new_thread_id = sent_message.get("threadId")
                from javis.tools.email_monitor_task import add_thread_to_monitor

                print(f"Adding new thread to monitor: {new_thread_id}")
                await add_thread_to_monitor(new_thread_id, to_email)

            return {
                "status": "success",
                "message_id": sent_message["id"],
                "thread_id": sent_message.get("threadId"),
                "label_ids": sent_message.get("labelIds", []),
                "recipient": to_email,
                "subject": subject,
                "cc": cc,
                "bcc": bcc,
                "is_reply": bool(thread_id),
            }

        except Exception as e:
            print(f"Error sending email: {e}")
            return {"status": "failed", "error": f"Failed to send email: {str(e)}"}

    except Exception as e:
        print(f"Error sending email: {e}")
        return {"status": "failed", "error": str(e)}
