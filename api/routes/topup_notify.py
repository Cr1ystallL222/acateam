"""
Top-up notification service.
Sends deposit requests to Telegram group.
"""
import aiohttp
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN") or os.getenv("BOT_TOKEN")
TOPUP_GROUP_ID = os.getenv("TOPUP_GROUP_ID")

from ..config import logger
from ..database import get_db_path
import aiosqlite


async def send_topup_notification(deposit_id: int, user: dict, amount: int):
    """Send top-up request to Telegram group."""
    if not TOPUP_GROUP_ID:
        logger.error("TOPUP_GROUP_ID not configured!")
        return
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not configured!")
        return
    
    # Build user link
    tg_user_id = user.get('telegram_user_id')
    display_name = user.get('display_name') or user.get('first_name') or f"ID: {user.get('id')}"
    
    # Get referrer info - use telegram_user_id to find referrer
    referrer_info = "Нет"
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        # First get user's referrer_user_id
        async with db.execute("""
            SELECT u2.telegram_username, u2.telegram_display_name, u2.first_name, u2.telegram_user_id
            FROM users u1
            JOIN users u2 ON u1.referrer_user_id = u2.id
            WHERE u1.telegram_user_id = ?
        """, (tg_user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                if row['telegram_username']:
                    referrer_info = f"@{row['telegram_username']}"
                else:
                    referrer_info = row['first_name'] or row['telegram_display_name'] or f"ID: {row['telegram_user_id']}"
    
    # Build message without emojis
    user_link = f"<a href='tg://user?id={tg_user_id}'>{display_name}</a>" if tg_user_id else display_name
    
    message = f"""<b>Новая заявка на пополнение</b>

Мамонт: {user_link}
Реферер: {referrer_info}
Сумма: <b>{amount:,}₽</b>

<i>Ответьте на это сообщение в формате:</i>
<code>Реквизиты
Название банка
Точная сумма</code>"""

    # Send to group
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": TOPUP_GROUP_ID,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            async with session.post(url, json=data) as resp:
                result = await resp.json()
                if result.get('ok'):
                    message_id = result['result']['message_id']
                    
                    # Save message_id to deposit
                    async with aiosqlite.connect(db_file) as db:
                        await db.execute("""
                            UPDATE deposits SET group_message_id = ?, status = 'awaiting_requisites'
                            WHERE id = ?
                        """, (message_id, deposit_id))
                        await db.commit()
                    
                    logger.info(f"Top-up notification sent: deposit_id={deposit_id}, message_id={message_id}")
                else:
                    logger.error(f"Failed to send top-up notification: {result}")
    except Exception as e:
        logger.error(f"Error sending top-up notification: {e}")


async def send_cancel_notification(deposit: dict, user: dict):
    """Notify group that deposit was cancelled by user."""
    if not TOPUP_GROUP_ID:
        return
    
    if not BOT_TOKEN:
        return
    
    display_name = user.get('display_name') or user.get('first_name') or f"ID: {user.get('id')}"
    tg_user_id = user.get('telegram_user_id')
    user_link = f"<a href='tg://user?id={tg_user_id}'>{display_name}</a>" if tg_user_id else display_name
    
    message = f"""<b>Заявка отменена</b>

Мамонт: {user_link}
Сумма: <b>{deposit['amount']:,}₽</b>

Пользователь отменил заявку."""

    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": TOPUP_GROUP_ID,
                "text": message,
                "parse_mode": "HTML",
                "reply_to_message_id": deposit.get('group_message_id')
            }
            async with session.post(url, json=data) as resp:
                result = await resp.json()
                if result.get('ok'):
                    logger.info(f"Cancel notification sent for deposit {deposit['id']}")
                else:
                    logger.error(f"Failed to send cancel notification: {result}")
    except Exception as e:
        logger.error(f"Error sending cancel notification: {e}")


async def send_paid_notification(deposit: dict, user: dict):
    """Notify group that user clicked 'I paid' button."""
    if not TOPUP_GROUP_ID:
        return
    
    if not BOT_TOKEN:
        return
    
    display_name = user.get('display_name') or user.get('first_name') or f"ID: {user.get('id')}"
    tg_user_id = user.get('telegram_user_id')
    user_link = f"<a href='tg://user?id={tg_user_id}'>{display_name}</a>" if tg_user_id else display_name
    
    message = f"""<b>Мамонт нажал "Я оплатил"</b>

Мамонт: {user_link}
Сумма: <b>{deposit.get('exact_amount', deposit['amount']):,}₽</b>
Реквизиты: <code>{deposit.get('requisites', 'N/A')}</code>
Банк: {deposit.get('bank_name', 'N/A')}"""

    # Build inline keyboard
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Подтвердить", "callback_data": f"topup_approve:{deposit['id']}"},
                {"text": "Отклонить", "callback_data": f"topup_reject:{deposit['id']}"}
            ]
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": TOPUP_GROUP_ID,
                "text": message,
                "parse_mode": "HTML",
                "reply_to_message_id": deposit.get('group_message_id'),
                "reply_markup": keyboard
            }
            async with session.post(url, json=data) as resp:
                result = await resp.json()
                if result.get('ok'):
                    logger.info(f"Paid notification sent for deposit {deposit['id']}")
                else:
                    logger.error(f"Failed to send paid notification: {result}")
    except Exception as e:
        logger.error(f"Error sending paid notification: {e}")

