"""
Support chat handlers for Telegram bot.
Handles replies to support messages in the group.
Replies are saved to database and shown in widget (not sent to TG).
"""
import os
from pathlib import Path
from datetime import datetime, timezone
from aiogram import types, F
from aiogram.filters import Command
from dotenv import load_dotenv

# Load env
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SUPPORT_CHAT_ID = os.getenv("SUPPORT_CHAT_ID")

from ..config import logger
from ..database import db
from ..database import get_support_message_by_group_msg, update_support_ticket, add_support_reply
from ..loader import bot, dp


async def get_mamont_by_id(mamont_id: str) -> dict:
    """Get mamont by mamont_id (5-digit ID)."""
    row = await db.fetchone("SELECT * FROM mamonts WHERE mamont_id = ?", (str(mamont_id),))
    return dict(row) if row else None


async def get_user_by_id(user_id: int) -> dict:
    """Get user by database ID."""
    row = await db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
    return dict(row) if row else None


async def get_worker_display_info(user_id: int) -> str:
    """Get worker's display info (username or name) from bot_users via users table."""
    # Join users and bot_users to get full info
    # Join users and bot_users to get full info
    row = await db.fetchone("""
        SELECT u.telegram_username, u.telegram_display_name, bu.username, bu.full_name
        FROM users u
        LEFT JOIN bot_users bu ON u.telegram_user_id = bu.telegram_user_id
        WHERE u.id = ?
    """, (user_id,))
    
    if not row:
        return "Нет"
    
    # Prefer bot_users data (usually more complete), fallback to users
    username = row['username'] or row['telegram_username']
    display_name = row['full_name'] or row['telegram_display_name']
    
    if username:
        return f"@{username}"
    elif display_name:
        return display_name
    else:
        return "Неизвестно"


async def get_user_orders_count(user_id: int) -> int:
    """Get count of user orders."""
    row = await db.fetchone("SELECT COUNT(*) FROM orders WHERE user_id = ?", (user_id,))
    return row[0] if row else 0


async def get_user_support_tickets_count(user_id: int) -> int:
    """Get count of user support tickets."""
    row = await db.fetchone("SELECT COUNT(*) FROM support_tickets WHERE user_id = ?", (user_id,))
    return row[0] if row else 0


async def get_mamont_orders_count(mamont_id: str) -> int:
    """Get count of orders for a mamont."""
    # Try to find user linked to this mamont and count their orders
    row = await db.fetchone("""
        SELECT COUNT(*) FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN mamonts m ON m.tg_username = u.telegram_username OR m.email = u.email
        WHERE m.mamont_id = ?
    """, (str(mamont_id),))
    return row[0] if row else 0


# ============================================================================
# Support Handlers
# ============================================================================

# Only register if SUPPORT_CHAT_ID is configured
if SUPPORT_CHAT_ID:
    
    @dp.message(Command("info"), F.chat.id == int(SUPPORT_CHAT_ID))
    async def handle_info_command(message: types.Message):
        """Handle /info command to get mamont information by mamont_id."""
        
        # Parse mamont_id from command
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply("❌ Используйте: /info <ID мамонта>\nПример: /info 68125")
            return
        
        lookup_id = args[1].strip()
        
        # Find mamont by mamont_id
        mamont = await get_mamont_by_id(lookup_id)
        
        if not mamont:
            await message.reply(f"❌ Мамонт с ID {lookup_id} не найден")
            return
        
        # Get referrer info (worker)
        referrer_info = "Нет"
        if mamont.get('referrer_user_id'):
            referrer_info = await get_worker_display_info(mamont['referrer_user_id'])
        
        # Build user link
        display_name = mamont.get('first_name') or mamont.get('tg_name') or f"#{mamont['mamont_id']}"
        tg_username = mamont.get('tg_username')
        
        if tg_username:
            user_link = f"<a href='https://t.me/{tg_username}'>{display_name}</a>"
        else:
            user_link = display_name
        
        # Get status text
        status_map = {
            'attached': 'Привязан',
            'registered': 'Зарегистрирован',
            'paid': 'Оплатил'
        }
        status_text = status_map.get(mamont.get('status'), mamont.get('status', 'Неизвестно'))
        
        # Format response (minimal emojis)
        info_text = f"""<b>Информация о мамонте #{mamont['mamont_id']}</b>

Имя: {user_link}
Username: @{tg_username or 'Нет'}
Телефон: {mamont.get('phone') or 'Не указан'}
Email: {mamont.get('email') or 'Не указан'}

Статус: {status_text}
Воркер: {referrer_info}
Создан: {mamont.get('created_at', 'Неизвестно')}"""

        await message.reply(info_text, parse_mode="HTML")
    
    
    @dp.message(F.reply_to_message & (F.chat.id == int(SUPPORT_CHAT_ID)))
    async def handle_support_reply(message: types.Message):
        """Handle reply to support messages in the group."""
        
        # Skip if it's a command
        if message.text and message.text.startswith('/'):
            return
        
        # Check if this is a reply to a bot message
        reply_to = message.reply_to_message
        if not reply_to:
            return
        
        # Check if the original message was from our bot
        bot_info = await bot.get_me()
        if reply_to.from_user and reply_to.from_user.id != bot_info.id:
            return
        
        # Get the original support ticket
        original_message_id = reply_to.message_id
        ticket = await get_support_message_by_group_msg(original_message_id)
        
        if not ticket:
            # This might be a topup message, not a support message - ignore
            return
        
        # Get the reply text
        reply_text = message.text or message.caption or ""
        if not reply_text.strip():
            return
        
        try:
            # Save reply to database - user will see it in widget via polling
            await update_support_ticket(
                ticket['id'],
                reply_text=reply_text.strip(),
                replied_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            
            logger.info(f"Support reply saved for ticket {ticket['id']}")
            
            # Confirm in group
            # Get mamont info for better confirmation
            mamont_id = ticket.get('mamont_id')
            mamont_name = "Мамонт"
            if mamont_id:
                mamont = await get_mamont_by_id(mamont_id)
                if mamont:
                    mamont_name = mamont.get('first_name') or mamont.get('tg_name') or "Мамонт"
            
            display_id_str = f" (#{mamont_id})" if mamont_id else ""
            sent_msg = await message.reply(f"✅ Ответ отправлен в чат с мамонтом {mamont_name}{display_id_str}\n\nСтатус: Не прочитано 🔴")
            
            # Save reply to support_replies table
            await add_support_reply(
                ticket['id'],
                reply_text,
                sent_msg.message_id
            )
            
        except Exception as e:
            logger.error(f"Failed to save support reply: {e}")
            await message.reply(f"❌ Ошибка сохранения: {e}")
else:
    logger.warning("SUPPORT_CHAT_ID not configured, support handlers disabled")
