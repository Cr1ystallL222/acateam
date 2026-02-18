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
                user_read BOOLEAN DEFAULT FALSE,
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
                user_read BOOLEAN DEFAULT FALSE,
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
            
            # Check file size (Read into memory? Or check header?)
            # FastAPI UploadFile is spooled. We can check size by seeking?
            # Or just read and check len.
            # Safety: Read in chunks or check content-length header if reliable.
            # Let's read content.
            
            content = await file.read()
            if len(content) > 5 * 1024 * 1024: # 5MB
                raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 5Мб)")

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
                data.add_field('message_thread_id', '4')
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
                    "message_thread_id": 4,
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
            SELECT id, message, reply_text, created_at, replied_at, attachment_path, user_read
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
    has_unread = False
    
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
        
        # Add legacy reply if exists (migration fallback), BUT only if no new replies found later
        # We will filter duplicates after fetching replies
        if row.get('reply_text'):
            is_read = True
            if 'user_read' in row and row['user_read'] is not None:
                is_read = bool(row['user_read'])
                if not is_read:
                    has_unread = True
            
            messages.append({
                "id": f"{row['id']}_reply_legacy",
                "text": row['reply_text'],
                "isSupport": True,
                "timestamp": row.get('replied_at') or row['created_at'],
                "isRead": is_read
            })

    # Fetch new replies from support_replies table
    ticket_ids = [r['id'] for r in rows]
    if ticket_ids:
        placeholders = ",".join(["?"] * len(ticket_ids))
        replies = await db.fetchall(f"""
            SELECT id, ticket_id, reply_text, created_at, is_read 
            FROM support_replies 
            WHERE ticket_id IN ({placeholders})
            ORDER BY created_at ASC
        """, tuple(ticket_ids))
        
        for reply in replies:
            is_read = bool(reply['is_read'])
            if not is_read:
                has_unread = True
                
            messages.append({
                "id": f"{reply['ticket_id']}_reply_{reply['id']}",
                "text": reply['reply_text'],
                "isSupport": True,
                "timestamp": reply['created_at'],
                "isRead": is_read
            })
            
    # Filter out legacy replies if a new reply exists for the same ticket (deduplication)
    # Actually, legacy reply might be different from new reply? 
    # The bug is that we were writing to BOTH. So if both exist and texts are similar, it's a dupe.
    # Safe logic: If we have ANY reply in support_replies for a ticket, ignore the legacy reply_text for that ticket.
    
    # Get set of ticket IDs that have new replies
    tickets_with_new_replies = set()
    for msg in messages:
        # Convert ID to string for checking
        msg_id_str = str(msg['id'])
        if msg_id_str.startswith(f"{msg_id_str.split('_')[0]}_reply_") and 'legacy' not in msg_id_str:
             # Extract ticket_id. ID format: "{ticket_id}_reply_{reply_id}"
             try:
                 t_id = int(msg_id_str.split('_')[0])
                 tickets_with_new_replies.add(t_id)
             except:
                 pass

    # Filter messages
    final_messages = []
    for msg in messages:
        if 'legacy' in str(msg['id']):
            try:
                t_id = int(msg['id'].split('_')[0])
                if t_id in tickets_with_new_replies:
                    continue # Skip legacy if new reply exists
            except:
                pass
        final_messages.append(msg)
    
    messages = final_messages
            
    # Sort all messages by timestamp
    messages.sort(key=lambda x: x['timestamp'] if isinstance(x['timestamp'], datetime) else datetime.fromisoformat(str(x['timestamp'])))

    return {"messages": messages, "has_unread": has_unread}



@router.post("/api/support/read")
async def mark_support_read(request: Request):
    """Mark all support replies as read for current user."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Необходимо авторизоваться")
    
    if hasattr(user, 'keys'):
        user = dict(user)
    
    user_id = user.get('id')
    
    await ensure_support_table()
    
    # Update all replied tickets where user_read is false
    try:
        # First select the messages to update in Telegram
        if db.is_postgres:
            unread_tickets = await db.fetchall("""
                SELECT id, bot_message_id, reply_text, mamont_id 
                FROM support_tickets 
                WHERE user_id = ? AND reply_text IS NOT NULL AND (user_read IS FALSE OR user_read IS NULL)
            """, (user_id,))
        else:
            unread_tickets = await db.fetchall("""
                SELECT id, bot_message_id, reply_text, mamont_id 
                FROM support_tickets 
                WHERE user_id = ? AND reply_text IS NOT NULL AND (user_read = 0 OR user_read IS NULL)
            """, (user_id,))

        if db.is_postgres:
            await db.execute("""
                UPDATE support_tickets 
                SET user_read = TRUE 
                WHERE user_id = ? AND reply_text IS NOT NULL AND user_read = FALSE
            """, (user_id,))
        else:
            await db.execute("""
                UPDATE support_tickets 
                SET user_read = 1
                WHERE user_id = ? AND reply_text IS NOT NULL AND (user_read = 0 OR user_read IS NULL)
            """, (user_id,))
            
        # Fetch new unread replies BEFORE marking them as read (to get IDs)
        if db.is_postgres:
            unread_replies = await db.fetchall("""
                SELECT sr.id, sr.bot_message_id, st.mamont_id 
                FROM support_replies sr
                JOIN support_tickets st ON sr.ticket_id = st.id
                WHERE st.user_id = ? AND sr.is_read IS FALSE
            """, (user_id,))
        else:
             unread_replies = await db.fetchall("""
                SELECT sr.id, sr.bot_message_id, st.mamont_id 
                FROM support_replies sr
                JOIN support_tickets st ON sr.ticket_id = st.id
                WHERE st.user_id = ? AND (sr.is_read = 0 OR sr.is_read IS NULL)
            """, (user_id,))

        # Update support_replies table
        if db.is_postgres:
            await db.execute("""
                UPDATE support_replies
                SET is_read = TRUE
                WHERE ticket_id IN (SELECT id FROM support_tickets WHERE user_id = ?)
                AND is_read = FALSE
            """, (user_id,))
        else:
             await db.execute("""
                UPDATE support_replies
                SET is_read = 1
                WHERE ticket_id IN (SELECT id FROM support_tickets WHERE user_id = ?)
                AND (is_read = 0 OR is_read IS NULL)
            """, (user_id,))
            
        # Trigger Telegram edits asynchronously
        if unread_tickets or unread_replies:
            async with aiohttp.ClientSession() as session:
                # 1. Update legacy tickets (if any)
                for ticket in unread_tickets:
                    if not ticket.get('bot_message_id'):
                        continue
                    await edit_telegram_message(session, ticket['bot_message_id'], ticket.get('mamont_id'))

                # 2. Update new replies
                for reply in unread_replies:
                    if not reply.get('bot_message_id'):
                        continue
                    # Note: unread_replies query needs to join with support_tickets to get mamont_id?
                    # Yes, let's fix the query above first.
                    await edit_telegram_message(session, reply['bot_message_id'], reply.get('mamont_id'))

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error marking messages read: {e}")
        # Non-critical, just return ok
        return {"status": "ok"}

async def edit_telegram_message(session, message_id, mamont_id):
    """Helper to edit telegram message status."""
    try:
        mamont_name_str = "Мамонт"
        display_id_str = f" (#{mamont_id})" if mamont_id else ""
        
        if mamont_id:
            m_row = await db.fetchone("SELECT first_name, tg_name FROM mamonts WHERE mamont_id = ?", (str(mamont_id),))
            if m_row:
                mamont_name_str = m_row.get('first_name') or m_row.get('tg_name') or "Мамонт"
        
        new_text = f"✅ Ответ отправлен в чат с мамонтом {mamont_name_str}{display_id_str}\n\nСтатус: Прочитано 🟢"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
        payload = {
            "chat_id": SUPPORT_CHAT_ID,
            "message_thread_id": 4,
            "message_id": message_id,
            "text": new_text
        }
        await session.post(url, json=payload)
    except Exception as e:
        logger.error(f"Failed to edit TG message {message_id}: {e}")
