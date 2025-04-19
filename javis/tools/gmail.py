from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from googleapiclient.discovery import build
from javis.helper import get_google_crendential


def get_gmail_service():
    creds = get_google_crendential()
    return build("gmail", "v1", credentials=creds)


def get_thread_metadata(thread_id: str) -> dict:
    """Get metadata from both the first and last messages of a thread.

    This function retrieves important email headers from both the first message (for thread context)
    and the last message (for proper reply chaining) in a Gmail thread.

    Args:
        thread_id (str): The Gmail thread ID to get metadata from

    Returns:
        dict: Thread metadata containing:
            - recipient (str): Original 'To' recipient
            - subject (str): Original email subject
            - message_id (str): Message-ID of the first message
            - references (str): Space-separated string of referenced message IDs
            - from_sender (str): Original sender's email address
            - last_message_id (str): Message-ID of the last message in thread,
                                   falls back to first message's ID if not found

    Example:
        >>> metadata = get_thread_metadata("thread_123")
        >>> print(metadata)
        {
            'recipient': 'user@example.com',
            'subject': 'Interview Invitation',
            'message_id': '<abc123@gmail.com>',
            'references': '<abc123@gmail.com> <def456@gmail.com>',
            'from_sender': 'hr@company.com',
            'last_message_id': '<def456@gmail.com>'
        }
    """
    service = get_gmail_service()

    # Get thread details
    thread = service.users().threads().get(userId="me", id=thread_id).execute()
    if len(thread["messages"]) <= 0:
        return {}

    metadata = {}

    # Get first message headers for original context
    first_message = thread["messages"][0]
    first_headers = first_message.get("payload", {}).get("headers", [])

    # Get last message for reply chaining
    last_message = thread["messages"][-1]
    last_headers = last_message.get("payload", {}).get("headers", [])

    # Process first message headers
    for header in first_headers:
        name = header.get("name", "").lower()
        value = header.get("value", "")
        if name == "to":
            metadata["recipient"] = value
        elif name == "subject":
            metadata["subject"] = value
        elif name == "message-id":
            metadata["message_id"] = value
        elif name == "from":
            metadata["from_sender"] = value

    # Process last message headers
    for header in last_headers:
        name = header.get("name", "").lower()
        value = header.get("value", "")
        if name == "message-id":
            metadata["last_message_id"] = value
        elif name == "references":
            metadata["references"] = value

    # If no references found in last message, start with first message ID
    if "references" not in metadata and "message_id" in metadata:
        metadata["references"] = metadata["message_id"]

    # If no last_message_id found, use first message's ID
    if "last_message_id" not in metadata:
        metadata["last_message_id"] = metadata.get("message_id", "")

    return metadata


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    is_html: bool = False,
    thread_id: Optional[str] = None,
) -> dict:
    """Send an email or reply to an existing thread using Gmail API.

    This function handles both new emails and replies to existing threads. For replies,
    it properly maintains email threading by setting appropriate headers (References, In-Reply-To)
    and using the last message in the thread as the reference point.

    Args:
        to_email (str): Recipient's email address
        subject (str): Email subject (for replies, "Re:" prefix is handled automatically)
        body (str): Email content
        cc (List[str], optional): List of CC recipients. Defaults to None.
        bcc (List[str], optional): List of BCC recipients. Defaults to None.
        is_html (bool, optional): Whether body content is HTML. Defaults to False.
        thread_id (str, optional): Gmail thread ID to reply to. Defaults to None.

    Returns:
        dict: Response containing:
            - status (str): 'success' or 'failed'
            - message_id (str): ID of the sent message
            - thread_id (str): ID of the email thread
            - label_ids (List[str]): Gmail labels applied to the message
            - recipient (str): Recipient email address
            - subject (str): Final subject used
            - cc (List[str]): CC recipients
            - bcc (List[str]): BCC recipients
            - is_reply (bool): Whether this was a reply to existing thread
            - error (str, optional): Error message if status is 'failed'

    Examples:
        # Send new email
        >>> result = await send_email(
        ...     "candidate@example.com",
        ...     "Interview Invitation",
        ...     "Would you be available for an interview?"
        ... )

        # Send reply in existing thread
        >>> result = await send_email(
        ...     "candidate@example.com",
        ...     "Re: Interview Invitation",
        ...     "Thank you for your response",
        ...     thread_id="thread_123"
        ... )
    """
    try:
        service = get_gmail_service()

        # Create message container
        message = MIMEMultipart()
        message["to"] = to_email
        # If replying to a thread, get original message metadata
        if thread_id:
            metadata = get_thread_metadata(thread_id)
            print(f"=====> metadata in send_email: {metadata}")
            message["In-Reply-To"] = metadata.get("last_message_id", "")
            # # Build References header: combine existing references with current message ID
            # existing_references = metadata.get("references", "")
            # # Split existing references into list, remove empty entries
            # ref_list = [ref for ref in existing_references.split(" ") if ref]
            # # Add current message ID to end if not already present
            # if message_id_to_reply not in ref_list:
            #     ref_list.append(message_id_to_reply)
            # # Limit number of references to avoid header being too long
            # max_refs = 15
            # message["References"] = " ".join(ref_list[-max_refs:])
            # message["References"] = metadata.get("references", "")
            message["References"] = metadata.get("last_message_id", "")

        message["subject"] = subject

        # if cc:
        #     message["cc"] = ", ".join(cc)
        # if bcc:
        #     message["bcc"] = ", ".join(bcc)
        print(f"=====> message in send_email: {message}")
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
