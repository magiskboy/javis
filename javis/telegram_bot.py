import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()


class TelegramBot:
    def __init__(self):
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN must be set in environment variables")

        self.app = Application.builder().token(bot_token).build()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        await update.message.reply_html(
            rf"Chào {user.mention_html()}! Hãy gửi tin nhắn cho tôi, tôi sẽ lặp lại nó.",
        )

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await update.message.reply_text(
            "Gửi bất kỳ tin nhắn văn bản nào và tôi sẽ lặp lại!"
        )

    async def handle_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await update.message.reply_text(update.message.text)


telegram_bot = TelegramBot()
