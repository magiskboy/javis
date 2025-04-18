import asyncio
from dataclasses import dataclass

from javis import settings
from javis.agent import create_agent
from javis.telegram_bot import TelegramBot
from javis.agent import create_agent, process_prompt
import click


@dataclass
class Message:
    session_id: str
    user_id: str
    content: str
    date: str


cli = click.Group()


@cli.command()
def run_local():
    async def run():
        agent = create_agent()

        while True:
            try:
                user_input = input("> ")

                content = await process_prompt(user_input, agent, "1")
                print("javis:", content)

            except KeyboardInterrupt:
                break

    asyncio.run(run())


@cli.command()
def run_telebot():
    telegram_bot = TelegramBot(settings.TELEGRAM_BOT_TOKEN)
    telegram_bot.run()


if __name__ == "__main__":
    cli()
