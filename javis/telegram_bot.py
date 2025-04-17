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
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        self.agent = create_agent()

    async def handle_message(
        self, update: Update, _: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        print(f"User {user_id} sent message: {update.message.text}")
        content, result = await process_prompt(
            update.message.text, self.agent, str(user_id)
        )
        await update.message.reply_text(content)
        self.message_history = result.all_messages()

    def run(self):
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
