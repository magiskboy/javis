from javis import settings
import telegram


async def send_telegram_message(
    recipient: str,
    message: str,
    parse_mode: str = None,
    disable_web_page_preview: bool = False,
) -> dict:
    """Send a message to a specific Telegram user using the bot.

    Args:
        recipient: The Telegram user identifier (user ID, @username, or phone number)
        message: The text message to send
        parse_mode: Optional. Mode for parsing entities in the message text (HTML, Markdown, MarkdownV2)
        disable_web_page_preview: Optional. Disables link previews in the message

    Returns:
        dict: Response containing status and message details or error information

    Examples:
        >>> await send_telegram_message("123456789", "Hello from the bot!")
        >>> await send_telegram_message("@username", "Hello with *bold* text", parse_mode="Markdown")
        >>> await send_telegram_message("+84123456789", "Hello via phone number!")
        >>> await send_telegram_message("0123456789", "Hello using local VN number!")
    """
    try:
        if not settings.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables")

        bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)

        chat_id = recipient

        # Send the message
        sent_message = await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
        )

        return {
            "status": "success",
            "message_id": sent_message.message_id,
            "chat_id": sent_message.chat.id,
            "sent_text": message,
            "timestamp": sent_message.date.isoformat(),
            "recipient_info": {
                "original_identifier": recipient,
                "resolved_chat_id": sent_message.chat.id,
                "username": sent_message.chat.username,
                "first_name": sent_message.chat.first_name,
                "last_name": sent_message.chat.last_name,
            },
        }

    except telegram.error.Unauthorized:
        return {
            "status": "failed",
            "error": "Bot was blocked by the user or not authorized to send messages",
        }
    except telegram.error.BadRequest as e:
        return {"status": "failed", "error": f"Invalid request: {str(e)}"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
