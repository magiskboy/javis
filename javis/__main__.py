import asyncio
from javis.agent import create_agent
from javis.telegram_bot import TelegramBot
from javis.agent import create_agent, process_prompt


async def main():
    telegram_bot = TelegramBot()
    agent = create_agent()
    message_history = []

    while True:
        try:
            user_input = input("> ")

            content, result = await process_prompt(user_input, agent, message_history)
            print('javis:', content)

            if len(result.all_messages()) < 5:
                message_history = result.all_messages()
            else:
                message_history = result.all_messages()[-5:]

        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    asyncio.run(main())
