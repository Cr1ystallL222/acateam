import asyncio
from bots.loader import bot, dp
from bots.config import logger
from bots.database import ensure_bot_schema
import bots.handlers  # This registers all handlers

async def main():
    await ensure_bot_schema()
    logger.info("Starting main bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
