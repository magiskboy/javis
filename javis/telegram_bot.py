from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)
import logging
from javis.agent import create_agent, process_prompt


logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be set in environment variables")

        self.app = Application.builder().token(token).build()
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.agent = create_agent()
        self.message_history = []

    async def handle_message(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        logger.info(f"User {update.effective_user.id} sent message: {update.message.text}")
        content, result = await process_prompt(update.message.text, self.agent, self.message_history)
        await update.message.reply_text(content)
        self.message_history = result.all_messages()

    def run(self):
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
