from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from .config import logger
from data.db import db

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"}
    )

async def get_current_user(request: Request):
    user_id = request.cookies.get("auth_user_id")
    if not user_id:
        return None
    return row

async def ensure_global_user(telegram_user_id: int) -> Optional[dict]:
    """
    Ensure a user exists in the global 'users' table.
    If not, try to sync from 'bot_users'.
    """
    # 1. Check if exists
    row = await db.fetchone("SELECT * FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
    if row:
        return row
        
    # 2. If not, fetch from bot_users
    bot_user = await db.fetchone("SELECT * FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,))
    if not bot_user:
        return None
        
    # 3. Create in users
    # We map bot_users fields to users fields
    # bot_users: telegram_user_id, chat_id, username, full_name
    # users: telegram_user_id, chat_id, telegram_username, telegram_display_name
    
    try:
        await db.execute("""
            INSERT INTO users (telegram_user_id, chat_id, telegram_username, telegram_display_name)
            VALUES (?, ?, ?, ?)
        """, (
            bot_user['telegram_user_id'], 
            bot_user['chat_id'], 
            bot_user['username'], 
            bot_user['full_name']
        ))
        
        # 4. Return new row
        row = await db.fetchone("SELECT * FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
        logger.info(f"Synced bot_user {telegram_user_id} to global users table.")
        return row
    except Exception as e:
        logger.error(f"Failed to sync global user {telegram_user_id}: {e}")
        return None
