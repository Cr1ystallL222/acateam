from aiogram import types, F
from ..loader import dp
from ..config import WORKERS_CHAT_ID, logger

# Parse WORKERS_CHAT_ID safely
TARGET_CHAT_ID = None
try:
    if WORKERS_CHAT_ID:
        TARGET_CHAT_ID = int(WORKERS_CHAT_ID)
except ValueError:
    logger.error(f"Invalid WORKERS_CHAT_ID: {WORKERS_CHAT_ID}")

# Register handler only if chat ID is set
if TARGET_CHAT_ID:
    @dp.message(F.chat.id == TARGET_CHAT_ID, F.new_chat_members | F.left_chat_member | F.pinned_message)
    async def delete_system_messages(message: types.Message):
        """
        Delete system messages in workers chat:
        - New chat members
        - Left chat members
        - Pinned messages
        """
        try:
            await message.delete()
        except Exception as e:
            # Ignore errors (e.g. message already deleted, bot not admin)
            logger.debug(f"Failed to delete system message in workers chat: {e}")
