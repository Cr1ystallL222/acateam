import asyncio
import warnings

# Suppress all Pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

from bots.loader import bot, dp
from bots.config import logger
from bots.database import ensure_bot_schema
import bots.handlers  # This registers all handlers

import sys
from pathlib import Path

# Ensure project root is in sys.path for Render
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

async def main():
    await ensure_bot_schema()
    
    # Try connecting to shared DB (sanity check)
    try:
        from data.db import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Shared DB connection OK.")
    except Exception as e:
        logger.warning(f"Shared DB connection skipped/failed (normal for purely local/sqlite run): {e}")

    # System events creation removed per user request
    
    logger.info("Starting main bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
