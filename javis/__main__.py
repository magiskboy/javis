import asyncio
from javis.agent import create_agent
from javis.telegram_bot import TelegramBot


async def main():
    telegram_bot = TelegramBot()
    agent = create_agent()
    message_history = []

    while True:
        try:
            user_input = input("> ")

            result = await agent.run(
                user_input,
                message_history=message_history,
            )
            for message in result.new_messages()[1:]:
                print(
                    "javis:",
                    "".join(
                        map(
                            lambda part: part.content,
                            filter(
                                lambda part: part.part_kind == "text", message.parts
                            ),
                        )
                    ),
                )

            if len(result.all_messages()) < 5:
                message_history = result.all_messages()
            else:
                message_history = result.all_messages()[-5:]

            # print('javis: ', result.data)

        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    asyncio.run(main())
