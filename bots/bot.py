import asyncio
import warnings

# Suppress all Pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

from bots.loader import bot, dp
from bots.config import logger
from bots.database import ensure_bot_schema
from data.db import db
import bots.handlers  # This registers all handlers

import sys
from pathlib import Path

# Ensure project root is in sys.path for Render
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

async def main():
    await db.connect()
    logger.info("Main bot DB connected.")
    
    await ensure_bot_schema()
    
    # Notify startup
    from bots.services.logger_service import log_action
    await log_action("Bot started. System dates updated.", "INFO")
    
    logger.info("Starting main bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
