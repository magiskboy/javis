from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from googleapiclient.discovery import build
from javis.helper import get_google_crendential

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
) -> dict:
    """Send an email using Gmail API.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        cc: Optional list of CC recipients
        bcc: Optional list of BCC recipients
        is_html: Whether the body content is HTML (default: False)

    Returns:
        dict: Response containing status and message details or error information

    Examples:
        >>> await send_email(
        ...     "recipient@example.com",
        ...     "Hello",
        ...     "This is a test email"
        ... )

        >>> await send_email(
        ...     "recipient@example.com",
        ...     "HTML Test",
        ...     "<h1>Hello</h1><p>This is HTML content</p>",
        ...     cc=["cc@example.com"],
        ...     is_html=True
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
            # Send the email
            sent_message = (
                service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            # Store the thread ID for monitoring replies
            thread_id = sent_message.get("threadId")
            from javis.tools.email_monitor_task import add_thread_to_monitor

            await add_thread_to_monitor(thread_id, to_email)

            return {
                "status": "success",
                "message_id": sent_message["id"],
                "thread_id": thread_id,
                "label_ids": sent_message.get("labelIds", []),
                "recipient": to_email,
                "subject": subject,
                "cc": cc,
                "bcc": bcc,
            }

        except Exception as e:
            return {"status": "failed", "error": f"Failed to send email: {str(e)}"}

    except Exception as e:
        return {"status": "failed", "error": str(e)}
