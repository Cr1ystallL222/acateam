"""
Top-up handlers for main bot.
Handles reply parsing for requisites and confirm/edit callbacks.
"""
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from datetime import datetime, timedelta, timezone

from ..loader import bot, dp
from ..config import logger, TOPUP_GROUP_ID
from ..database import db


# ============================================================================
# Reply Handler - Parse requisites from admin reply
# ============================================================================

@dp.message(F.reply_to_message & F.chat.id == int(TOPUP_GROUP_ID) if TOPUP_GROUP_ID else F.text == "__never_match__")
async def handle_topup_reply(message: types.Message):
    """Handle admin reply with requisites."""
    if not message.reply_to_message:
        return
    
    # Get deposit by message_id
    reply_to_id = message.reply_to_message.message_id
    
    row = await db.fetchone("""
        SELECT d.*, u.telegram_user_id, u.first_name, u.telegram_display_name
        FROM deposits d
        JOIN users u ON d.user_id = u.id
        WHERE d.group_message_id = ?
    """, (reply_to_id,))
    
    deposit = dict(row) if row else None
    
    if not deposit:
        return  # Not a deposit reply
    
    deposit = dict(deposit)
    
    # Check if already has requisites
    if deposit['status'] not in ('awaiting_requisites', 'pending'):
        await message.reply("Реквизиты уже были отправлены или заявка завершена.")
        return
    
    # Parse the reply - expecting 3 lines
    lines = message.text.strip().split('\n')
    if len(lines) < 3:
        await message.reply("Неверный формат. Ответьте в формате:\n<code>Реквизиты\nНазвание банка\nТочная сумма</code>", parse_mode="HTML")
        return
    
    requisites = lines[0].strip()
    bank_name = lines[1].strip()
    try:
        exact_amount = int(''.join(filter(str.isdigit, lines[2])))
    except ValueError:
        await message.reply("Не удалось распознать сумму. Укажите число.")
        return
    
    # Build preview
    user_name = deposit.get('first_name') or deposit.get('telegram_display_name') or f"ID: {deposit['telegram_user_id']}"
    
    preview_text = f"""<b>Предпросмотр реквизитов</b>

Кому: {user_name}
Реквизиты: <code>{requisites}</code>
Банк: {bank_name}
Сумма: <b>{exact_amount:,}₽</b>

Подтвердите или отредактируйте данные."""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Подтвердить", callback_data=f"topup_confirm:{deposit['id']}:{requisites[:50]}:{bank_name[:30]}:{exact_amount}"),
            InlineKeyboardButton(text="Редактировать", callback_data=f"topup_edit:{deposit['id']}")
        ]
    ])
    
    await message.reply(preview_text, parse_mode="HTML", reply_markup=keyboard)


# ============================================================================
# Callback Handlers
# ============================================================================

@dp.callback_query(F.data.startswith("topup_confirm:"))
async def cb_topup_confirm(callback: types.CallbackQuery):
    """Confirm requisites and send to user."""
    parts = callback.data.split(":", 4)
    if len(parts) < 5:
        await callback.answer("Ошибка данных", show_alert=True)
        return
    
    deposit_id = int(parts[1])
    requisites = parts[2]
    bank_name = parts[3]
    exact_amount = int(parts[4])
    
    # Update deposit
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).replace(tzinfo=None)
    
    await db.execute("""
        UPDATE deposits 
        SET status = 'requisites_sent', requisites = ?, bank_name = ?, exact_amount = ?, expires_at = ?
        WHERE id = ?
    """, (requisites, bank_name, exact_amount, expires_at, deposit_id))
    
    # Get user info for confirmation
    user_info = await db.fetchone("""
        SELECT u.telegram_user_id, u.first_name, u.telegram_display_name
        FROM deposits d
        JOIN users u ON d.user_id = u.id
        WHERE d.id = ?
    """, (deposit_id,))
    
    user_name = "Пользователь"
    if user_info:
        user_name = user_info['first_name'] or user_info['telegram_display_name'] or f"ID: {user_info['telegram_user_id']}"
    
    await callback.message.edit_text(
        f"<b>Реквизиты отправлены</b>\n\n"
        f"Кому: {user_name}\n"
        f"Реквизиты: <code>{requisites}</code>\n"
        f"Банк: {bank_name}\n"
        f"Сумма: <b>{exact_amount:,}₽</b>\n\n"
        f"Таймер: 10 минут",
        parse_mode="HTML"
    )
    
    await callback.answer("Реквизиты отправлены пользователю!")
    logger.info(f"Requisites sent for deposit {deposit_id}")


@dp.callback_query(F.data.startswith("topup_edit:"))
async def cb_topup_edit(callback: types.CallbackQuery):
    """Request new requisites."""
    deposit_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        f"<b>Редактирование</b>\n\n"
        f"Ответьте на исходное сообщение новыми данными:\n"
        f"<code>Реквизиты\nНазвание банка\nТочная сумма</code>",
        parse_mode="HTML"
    )
    
    await callback.answer("Ответьте на исходное сообщение")


# ============================================================================
# Approve / Reject Payment
# ============================================================================

@dp.callback_query(F.data.startswith("topup_approve:"))
async def cb_topup_approve(callback: types.CallbackQuery):
    """Approve payment and credit balance."""
    deposit_id = int(callback.data.split(":")[1])
    
    # Get deposit and user info
    deposit = await db.fetchone("""
        SELECT d.*, u.telegram_user_id, u.first_name, u.telegram_display_name, u.id as user_id
        FROM deposits d
        JOIN users u ON d.user_id = u.id
        WHERE d.id = ?
    """, (deposit_id,))
    
    if not deposit:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    
    deposit = dict(deposit)
    amount = deposit.get('exact_amount') or deposit['amount']
    
    # Update deposit status
    await db.execute("UPDATE deposits SET status = 'completed' WHERE id = ?", (deposit_id,))
    
    # Add balance to user
    await db.execute("UPDATE users SET balance = COALESCE(balance, 0) + ? WHERE id = ?", (amount, deposit['user_id']))
    
    user_name = deposit.get('first_name') or deposit.get('telegram_display_name') or f"ID: {deposit['telegram_user_id']}"
    
    await callback.message.edit_text(
        f"<b>Пополнение подтверждено</b>\n\n"
        f"Мамонт: {user_name}\n"
        f"Сумма: <b>{amount:,}₽</b>\n\n"
        f"Баланс пользователя пополнен.",
        parse_mode="HTML"
    )
    
    await callback.answer("Баланс пополнен!")
    logger.info(f"Deposit {deposit_id} approved, {amount}₽ credited to user {deposit['user_id']}")


@dp.callback_query(F.data.startswith("topup_reject:"))
async def cb_topup_reject(callback: types.CallbackQuery):
    """Reject payment."""
    deposit_id = int(callback.data.split(":")[1])
    
    # Get deposit info
    deposit = await db.fetchone("""
        SELECT d.*, u.telegram_user_id, u.first_name, u.telegram_display_name
        FROM deposits d
        JOIN users u ON d.user_id = u.id
        WHERE d.id = ?
    """, (deposit_id,))
    
    if not deposit:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    
    deposit = dict(deposit)
    
    # Update deposit status
    await db.execute("UPDATE deposits SET status = 'rejected' WHERE id = ?", (deposit_id,))
    
    user_name = deposit.get('first_name') or deposit.get('telegram_display_name') or f"ID: {deposit['telegram_user_id']}"
    
    await callback.message.edit_text(
        f"<b>Пополнение отклонено</b>\n\n"
        f"Мамонт: {user_name}\n"
        f"Сумма: <b>{deposit['amount']:,}₽</b>\n\n"
        f"Перевод не найден.",
        parse_mode="HTML"
    )
    
    await callback.answer("Заявка отклонена")
    logger.info(f"Deposit {deposit_id} rejected")


# ============================================================================
# Expiry notification (called by scheduled task or API)
# ============================================================================

async def notify_deposit_expired(deposit_id: int):
    """Notify group that deposit expired."""
    if not TOPUP_GROUP_ID:
        return
    
    row = await db.fetchone("""
        SELECT d.*, u.telegram_user_id, u.first_name, u.telegram_display_name
        FROM deposits d
        JOIN users u ON d.user_id = u.id
        WHERE d.id = ?
    """, (deposit_id,))
    
    deposit = row
    
    if not deposit:
        return
    
    deposit = dict(deposit)
    user_name = deposit.get('first_name') or deposit.get('telegram_display_name') or f"ID: {deposit['telegram_user_id']}"
    
    try:
        await bot.send_message(
            int(TOPUP_GROUP_ID),
            f"<b>Время истекло</b>\n\n"
            f"Мамонт: {user_name}\n"
            f"Сумма: {deposit['amount']:,}₽\n\n"
            f"Пользователь не успел оплатить в течение 10 минут.",
            parse_mode="HTML",
            reply_to_message_id=deposit['group_message_id'] if deposit['group_message_id'] else None
        )
    except Exception as e:
        logger.error(f"Failed to send expiry notification: {e}")

