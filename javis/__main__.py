import asyncio
from javis.agent import create_agent


async def main():
    agent = create_agent()

    while True:
        try:
            user_input = input('> ')
            result = await agent.run(user_input)
            print('javis: ', result.data)

        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    asyncio.run(main())
