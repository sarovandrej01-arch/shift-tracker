import asyncio
import logging

from app.bot.bot import create_bot, create_storage
from app.bot.dispatcher import create_dispatcher


async def run_polling() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = create_bot()
    dispatcher = create_dispatcher(create_storage())
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_polling())
