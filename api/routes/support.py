"""
Support chat API router.
Handles messages from website support widget.
"""
import aiohttp
import os
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN") or os.getenv("BOT_TOKEN")
SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")

from ..config import logger
from ..utils import get_current_user
from data.db import db


class SupportMessageRequest(BaseModel):
    message: str


router = APIRouter()


async def ensure_support_table():
    """Create support_tickets table if not exists."""
    if db.is_postgres:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                telegram_user_id BIGINT,
                message TEXT NOT NULL,
                group_message_id BIGINT,
                reply_text TEXT,
                replied_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
    else:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                telegram_user_id INTEGER,
                message TEXT NOT NULL,
                group_message_id INTEGER,
                reply_text TEXT,
                replied_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)


@router.post("/api/support/send")
async def send_support_message(request: Request, data: SupportMessageRequest):
    """Send a message to support group."""
    
    if not SUPPORT_CHAT_ID:
        logger.error("SUPPORT_CHAT_ID not configured!")
        raise HTTPException(status_code=500, detail="Поддержка временно недоступна")
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not configured!")
        raise HTTPException(status_code=500, detail="Поддержка временно недоступна")
    
    # Get user from auth cookie
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Необходимо авторизоваться")
    
    # Convert to dict if needed
    if hasattr(user, 'keys'):
        user = dict(user)
    
    message_text = data.message.strip()
    if not message_text:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
    
    if len(message_text) > 4000:
        raise HTTPException(status_code=400, detail="Сообщение слишком длинное")
    
    # Build user link with mamont_id
    user_id = user.get('id')
    tg_user_id = user.get('telegram_user_id')
    display_name = user.get('telegram_display_name') or user.get('first_name') or "Мамонт"
    tg_username = user.get('telegram_username')
    
    # Get mamont_id from mamonts table
    mamont_id = None
    row = await db.fetchone("""
        SELECT mamont_id FROM mamonts 
        WHERE tg_username = ? OR first_name = ? OR email = ?
        LIMIT 1
    """, (tg_username, user.get('first_name'), user.get('email')))
    if row:
        mamont_id = row['mamont_id']
    
    # Use mamont_id if found, otherwise fall back to user.id
    display_id = mamont_id if mamont_id else user_id
    
    # Create user link with name and mamont_id
    if tg_username:
        user_link = f"<a href='https://t.me/{tg_username}'>{display_name}</a> (#{display_id})"
    elif tg_user_id:
        user_link = f"<a href='tg://user?id={tg_user_id}'>{display_name}</a> (#{display_id})"
    else:
        user_link = f"{display_name} (#{display_id})"
    
    # Format message for Telegram group
    telegram_message = f"""<b>Сообщение в ТП от мамонта</b> {user_link}

<blockquote>{message_text}</blockquote>"""
    
    # Send to group
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": SUPPORT_CHAT_ID,
                "text": telegram_message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            async with session.post(url, json=payload) as resp:
                result = await resp.json()
                if result.get('ok'):
                    group_message_id = result['result']['message_id']
                    
                    # Save to database
                    await ensure_support_table()
                    
                    ticket_id = await db.execute_returning("""
                        INSERT INTO support_tickets (user_id, telegram_user_id, message, group_message_id)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, tg_user_id, message_text, group_message_id))
                    
                    logger.info(f"Support message sent: user_id={user_id}, message_id={group_message_id}")
                    return {"status": "ok", "message": "Сообщение отправлено", "ticket_id": ticket_id}
                else:
                    logger.error(f"Failed to send support message: {result}")
                    raise HTTPException(status_code=500, detail="Ошибка отправки сообщения")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending support message: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отправки сообщения")


@router.get("/api/support/messages")
async def get_support_messages(request: Request):
    """Get user's support messages and replies."""
    
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Необходимо авторизоваться")
    
    if hasattr(user, 'keys'):
        user = dict(user)
    
    user_id = user.get('id')
    
    await ensure_support_table()
    
    rows = await db.fetchall("""
        SELECT id, message, reply_text, created_at, replied_at
        FROM support_tickets
        WHERE user_id = ?
        ORDER BY created_at ASC
    """, (user_id,))
    
    messages = []
    for row in rows:
        # Add user message
        messages.append({
            "id": row['id'],
            "text": row['message'],
            "isSupport": False,
            "timestamp": row['created_at']
        })
        # Add support reply if exists
        if row['reply_text']:
            messages.append({
                "id": f"{row['id']}_reply",
                "text": row['reply_text'],
                "isSupport": True,
                "timestamp": row['replied_at'] or row['created_at']
            })
    
    return {"messages": messages}
