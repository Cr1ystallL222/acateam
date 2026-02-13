"""
Support chat API router.
Handles messages from website support widget.
"""
import aiohttp
import os
import uuid
import aiofiles
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
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
                attachment_path TEXT,
                mamont_id TEXT,
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
                attachment_path TEXT,
                mamont_id TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)


@router.post("/api/support/send")
async def send_support_message(
    request: Request, 
    message: str = Form(""),
    file: Optional[UploadFile] = File(None)
):
    """Send a message to support group with optional photo."""
    
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
    
    if hasattr(user, 'keys'):
        user = dict(user)
    
    message_text = message.strip()
    # If file is present, message can be empty (caption), otherwise strictly required
    if not message_text and not file:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
    
    if len(message_text) > 4000:
        raise HTTPException(status_code=400, detail="Сообщение слишком длинное")

    # Handle file upload
    attachment_path = None
    upload_dir = PROJECT_ROOT / "data" / "uploads" / "support"
    
    if file:
        try:
            # Ensure directory exists
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            ext = file.filename.split('.')[-1] if '.' in file.filename else "jpg"
            filename = f"{uuid.uuid4()}.{ext}"
            file_path = upload_dir / filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            
            attachment_path = f"/uploads/support/{filename}"
            
        except Exception as e:
            logger.error(f"File upload error: {e}")
            raise HTTPException(status_code=500, detail="Ошибка загрузки файла")
    
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
            result = None
            
            if attachment_path:
                # Send Photo
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                
                data = aiohttp.FormData()
                data.add_field('chat_id', str(SUPPORT_CHAT_ID))
                data.add_field('caption', telegram_message)
                data.add_field('parse_mode', 'HTML')
                
                # Re-open the saved file to stream it to Telegram
                # We need to open it in a blocking way or use run_in_executor? 
                # aiohttp FormData supports opening files.
                f = open(upload_dir / filename, 'rb')
                data.add_field('photo', f, filename=filename)
                
                async with session.post(url, data=data) as resp:
                    result = await resp.json()
                
                f.close()
            else:
                # Send Text
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": SUPPORT_CHAT_ID,
                    "text": telegram_message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
                async with session.post(url, json=payload) as resp:
                    result = await resp.json()

            if result and result.get('ok'):
                group_message_id = result['result']['message_id']
                
                # Save to database
                await ensure_support_table()
                
                # Use execute_returning to get the ID
                ticket_id = await db.execute_returning("""
                    INSERT INTO support_tickets (
                        user_id, telegram_user_id, message, group_message_id, 
                        attachment_path, mamont_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, tg_user_id, message_text, group_message_id, attachment_path, str(display_id)))
                
                logger.info(f"Support message sent: user_id={user_id}, message_id={group_message_id}, has_file={bool(attachment_path)}")
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
    
    # Try to select attachment_path, but handle if it doesn't exist yet (though we updated schema)
    try:
        rows = await db.fetchall("""
            SELECT id, message, reply_text, created_at, replied_at, attachment_path
            FROM support_tickets
            WHERE user_id = ?
            ORDER BY created_at ASC
        """, (user_id,))
    except Exception:
        # Fallback if column missing (should not happen if migration worked)
        rows = await db.fetchall("""
            SELECT id, message, reply_text, created_at, replied_at
            FROM support_tickets
            WHERE user_id = ?
            ORDER BY created_at ASC
        """, (user_id,))
    
    messages = []
    for row in rows:
        # Add user message
        msg = {
            "id": row['id'],
            "text": row['message'],
            "isSupport": False,
            "timestamp": row['created_at']
        }
        if 'attachment_path' in row and row['attachment_path']:
            msg['attachment_url'] = row['attachment_path']
            
        messages.append(msg)
        
        # Add support reply if exists
        if row['reply_text']:
            messages.append({
                "id": f"{row['id']}_reply",
                "text": row['reply_text'],
                "isSupport": True,
                "timestamp": row['replied_at'] or row['created_at']
            })
    
    return {"messages": messages}
