from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
<<<<<<< Updated upstream
import pickle
from pathlib import Path

# Get the current directory
CURRENT_DIR = Path(__file__).parent
CREDENTIALS_PATH = CURRENT_DIR / "credentials.json"
TOKEN_PATH = CURRENT_DIR / "token.pickle"

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
=======
from javis.helper import get_google_crendential
>>>>>>> Stashed changes


def get_gmail_service():
    """Initialize and return the Gmail API service.

    Returns:
        Resource: Gmail API service
    """
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"Credentials file not found at: {CREDENTIALS_PATH}"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

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
            print(f"Adding thread to monitor: {thread_id}")
            print(f"to_email: {to_email}")
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
            print(f"Error sending email: {e}")
            return {"status": "failed", "error": f"Failed to send email: {str(e)}"}

    except Exception as e:
        print(f"Error sending email: {e}")
        return {"status": "failed", "error": str(e)}
