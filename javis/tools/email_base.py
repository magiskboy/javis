import base64
from googleapiclient.discovery import build
from javis.helper import get_google_crendential


def get_gmail_service():
    """Get Gmail service instance."""
    creds = get_google_crendential()
    return build("gmail", "v1", credentials=creds)


def extract_email_content(msg: dict) -> str:
    """Extract plain text content from a Gmail message.

    Args:
        msg: Gmail message object

    Returns:
        str: Extracted text content
    """
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
    return content
