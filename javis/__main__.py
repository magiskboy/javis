import asyncio
from javis.agent import create_agent


async def main():
    agent = create_agent()
    message_history = []

    while True:
        try:
            user_input = input('> ')

            result = await agent.run(
                user_input,
                message_history=message_history,
            )
            if len(result.all_messages()) < 5:
                message_history = result.all_messages()
            else:
                message_history = result.all_messages()[-5:]

            print('javis: ', result.data)

        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    asyncio.run(main())
