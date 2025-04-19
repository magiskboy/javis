from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
import logging
from javis.agent import create_agent, process_prompt
from javis.tools.messages import MessageStore

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be set in environment variables")

        self.app = Application.builder().token(token).build()
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        self.app.add_handler(CommandHandler("reset", self.handle_reset))
        self.agent = create_agent()
        self.message_store = MessageStore()

    async def handle_reset(self, update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /reset command by deleting user's message history"""
        user_id = str(update.effective_user.id)
        try:
            await self.message_store.initialize()
            await self.message_store.delete_messages(user_id)
            await update.message.reply_text("Your message history has been cleared! 🗑️")
        except Exception as e:
            await update.message.reply_text(
                "Sorry, there was an error clearing your message history. Please try again later."
            )
        finally:
            await self.message_store.close()

    async def handle_message(
        self, update: Update, _: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        print(f"User {user_id} sent message: {update.message.text}")
        content = await process_prompt(update.message.text, self.agent, str(user_id))
        await update.message.reply_text(content)

    async def run(self):
        import asyncio
        print('Telebot is running')
        return asyncio.to_thread(self.app.run_polling, allowed_updates=Update.ALL_TYPES)
