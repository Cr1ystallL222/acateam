from .loader import bot
from ..config import LOG_CHAT_ID, logger
import asyncio

async def log_action(message: str, level: str = "INFO"):
    """
    Sends a log message to the configured LOG_CHAT_ID.
    """
    if not LOG_CHAT_ID:
        logger.warning(f"LOG_CHAT_ID not set. Log message skipped: {message}")
        return

    try:
        # Format message with level icon
        icons = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "🚨",
            "SUCCESS": "✅",
            "ACTION": "🎬",
            "VISIT": "👀",
            "PURCHASE": "💰"
        }
        icon = icons.get(level, "ℹ️")
        formatted_message = f"{icon} <b>{level}</b>\n\n{message}"
        
        await bot.send_message(chat_id=LOG_CHAT_ID, text=formatted_message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send log to Telegram: {e}")
