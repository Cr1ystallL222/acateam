from aiogram import types, F
import aiosqlite
from datetime import datetime, timedelta, timezone

from ..loader import bot, dp
from ..config import DB_PATH, SITE_URL, ADMIN_IDS, logger
from ..utils import format_cooldown_remaining, is_cooldown_active
from ..database import get_or_create_bot_user, get_or_create_referral
from ..renderers import (
    render_theatre_menu,
    render_clients_menu,
    render_settings_menu,
    render_profile_menu,
    render_events_menu
)

@dp.callback_query(F.data == "menu_admin")
async def cb_menu_admin(callback: types.CallbackQuery):
    if callback.from_user.id in ADMIN_IDS:
        await callback.answer("Админ панель скоро будет добавлена 🛠", show_alert=True)
    else:
        await callback.answer("Доступ запрещен", show_alert=True)

@dp.callback_query(F.data == "menu_theatre")
async def cb_menu_theatre(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    await render_theatre_menu(callback.message.chat.id, callback.from_user.id, msg_id)

@dp.callback_query(F.data == "menu_cinema")
async def cb_menu_cinema(callback: types.CallbackQuery):
    await callback.answer("Скоро будет доступно 🎬", show_alert=True)

@dp.callback_query(F.data == "menu_clients")
async def cb_menu_clients(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    await render_clients_menu(callback.message.chat.id, callback.from_user.id, msg_id)

@dp.callback_query(F.data == "menu_settings")
async def cb_menu_settings(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    await render_settings_menu(callback.message.chat.id, callback.from_user.id, msg_id)

@dp.callback_query(F.data == "menu_events")
async def cb_menu_events(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    await render_events_menu(callback.message.chat.id, callback.from_user.id, msg_id)

@dp.callback_query(F.data == "events_list")
async def cb_events_list(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    
    # Заглушка для списка событий
    text = "<b>📋 Список событий</b>\n\n<i>Функция в разработке...</i>\n\nЗдесь будет отображаться список всех событий театра."
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_events")]
    ])
    
    try:
        await bot.edit_message_caption(chat_id=callback.message.chat.id, message_id=msg_id, caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=msg_id, text=text, parse_mode="HTML", reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error editing message: {e}")

@dp.callback_query(F.data == "events_add")
async def cb_events_add(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    
    # Заглушка для добавления события
    text = "<b>➕ Добавить событие</b>\n\n<i>Функция в разработке...</i>\n\nЗдесь будет форма для добавления нового события в театр."
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_events")]
    ])
    
    try:
        await bot.edit_message_caption(chat_id=callback.message.chat.id, message_id=msg_id, caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=msg_id, text=text, parse_mode="HTML", reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error editing message: {e}")

@dp.callback_query(F.data == "menu_back_profile")
async def cb_back_to_profile(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    bot_user = await get_or_create_bot_user(
        callback.from_user.id, 
        callback.message.chat.id,
        callback.from_user.username or "",
        callback.from_user.full_name or ""
    )
    await render_profile_menu(callback.message.chat.id, callback.from_user.id, bot_user, msg_id)

@dp.callback_query(F.data == "menu_back_theatre")
async def cb_back_to_theatre(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    await render_theatre_menu(callback.message.chat.id, callback.from_user.id, msg_id)

@dp.callback_query(F.data == "copy_ref_link")
async def cb_copy_ref_link(callback: types.CallbackQuery):
    """Send ref link as separate message for easy copying (fallback for CopyTextButton)."""
    await callback.answer("Ссылка отправлена ниже ⬇️", show_alert=False)
    
    ref_code = await get_or_create_referral(callback.from_user.id, callback.message.chat.id)
    ref_link = f"{SITE_URL}/?ref={ref_code}"
    
    await callback.message.answer(
        f"<code>{ref_link}</code>",
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("approve:"))
async def cb_approve(callback: types.CallbackQuery):
    await callback.answer("Обрабатываю...")
    
    parts = callback.data.split(":")
    if len(parts) != 3:
        return
    
    _, user_id_str, app_id_str = parts
    user_id = int(user_id_str)
    app_id = int(app_id_str)
    admin_id = callback.from_user.id
    now_iso = datetime.now(timezone.utc).isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("""
            SELECT a.confirm_message_id, b.chat_id 
            FROM applications a 
            JOIN bot_users b ON a.telegram_user_id = b.telegram_user_id 
            WHERE a.id = ?
        """, (app_id,)) as cursor:
            row = await cursor.fetchone()
            confirm_message_id = row['confirm_message_id'] if row else None
            chat_id = row['chat_id'] if row else None
        
        await db.execute("""
            UPDATE applications SET status = 'approved', decided_at = ?, decided_by = ?
            WHERE id = ?
        """, (now_iso, admin_id, app_id))
        
        await db.execute("""
            UPDATE bot_users SET approved = 1, cooldown_until = NULL, joined_at = ?
            WHERE telegram_user_id = ?
        """, (now_iso, user_id))
        
        await db.commit()
    
    logger.info(f"Application approved: id={app_id}, telegram_user_id={user_id}, by={admin_id}")
    
    try:
        await callback.message.edit_text(
            callback.message.text + f"\n\n<b>✅ ОДОБРЕНО</b> ({callback.from_user.full_name})",
            parse_mode="HTML"
        )
    except:
        pass
    
    if chat_id:
        if confirm_message_id:
            try:
                await bot.delete_message(chat_id, confirm_message_id)
            except Exception as e:
                logger.warning(f"Failed to delete confirm message: {e}")
        
        try:
            await bot.send_message(chat_id, "✅")
            await bot.send_message(
                chat_id,
                "<b>Ваша заявка одобрена!</b>\n\n"
                "Поздравляем! Теперь вам доступен функционал бота.\n"
                "Напишите /start что бы открыть главное меню",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")

@dp.callback_query(F.data.startswith("reject:"))
async def cb_reject(callback: types.CallbackQuery):
    await callback.answer("Обрабатываю...")
    
    parts = callback.data.split(":")
    if len(parts) != 3:
        return
    
    _, user_id_str, app_id_str = parts
    user_id = int(user_id_str)
    app_id = int(app_id_str)
    admin_id = callback.from_user.id
    cooldown_until = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("""
            SELECT a.confirm_message_id, b.chat_id 
            FROM applications a 
            JOIN bot_users b ON a.telegram_user_id = b.telegram_user_id 
            WHERE a.id = ?
        """, (app_id,)) as cursor:
            row = await cursor.fetchone()
            confirm_message_id = row['confirm_message_id'] if row else None
            chat_id = row['chat_id'] if row else None
        
        await db.execute("""
            UPDATE applications SET status = 'rejected', decided_at = ?, decided_by = ?
            WHERE id = ?
        """, (now_iso, admin_id, app_id))
        
        await db.execute("""
            UPDATE bot_users SET approved = 0, cooldown_until = ?
            WHERE telegram_user_id = ?
        """, (cooldown_until, user_id))
        
        await db.commit()
    
    logger.info(f"Application rejected: id={app_id}, telegram_user_id={user_id}, by={admin_id}")
    
    try:
        await callback.message.edit_text(
            callback.message.text + f"\n\n<b>❌ ОТКЛОНЕНО</b> ({callback.from_user.full_name})",
            parse_mode="HTML"
        )
    except:
        pass
    
    if chat_id:
        if confirm_message_id:
            try:
                await bot.delete_message(chat_id, confirm_message_id)
            except Exception as e:
                logger.warning(f"Failed to delete confirm message: {e}")
        
        remaining = format_cooldown_remaining(cooldown_until)
        try:
            await bot.send_message(chat_id, "❌")
            await bot.send_message(
                chat_id,
                "<b>Ваша заявка отклонена</b>\n\n"
                "<i>Почему так могло произойти?</i>\n\n"
                "• Недостаточно информации в ответах\n"
                "• Не правильно заполнена заявка\n"
                "• Другие причины\n\n"
                f"Повторную заявку можно подать через: <b>{remaining}</b>\n\n"
                "<i>Используйте /start когда время истечёт.</i>",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")

@dp.callback_query(F.data == "get_ref")
async def cb_get_ref(callback: types.CallbackQuery):
    await callback.answer()
    
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bot_users WHERE telegram_user_id = ?", (user_id,)) as cursor:
            bot_user = await cursor.fetchone()
    
    if not bot_user:
        await callback.message.answer("❌ Вы не зарегистрированы. Используйте /start", parse_mode="HTML")
        return
    
    if bot_user['approved'] != 1:
        if is_cooldown_active(bot_user['cooldown_until']):
            remaining = format_cooldown_remaining(bot_user['cooldown_until'])
            await callback.message.answer(
                f"<b>⏳ Доступ ограничен</b>\n\n"
                f"Ваша заявка была отклонена.\n"
                f"Повторная попытка через: <b>{remaining}</b>",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer(
                "<b>⚠️ Доступ не разрешён</b>\n\n"
                "Для получения доступа к боту необходимо пройти анкету.\n"
                "Используйте /start",
                parse_mode="HTML"
            )
        return
    
    ref_code = await get_or_create_referral(user_id, chat_id)
    ref_link = f"{SITE_URL}/?ref={ref_code}"
    
    await callback.message.answer(
        "<b>🔗 Ваша реферальная ссылка</b>\n\n"
        f"<code>{ref_link}</code>\n\n"
        "<i>Нажмите на ссылку, чтобы скопировать.</i>",
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("mamont:"))
async def cb_mamont_details(callback: types.CallbackQuery):
    """Show mamont details with photo."""
    await callback.answer()
    
    mamont_id = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Get user_id from telegram_user_id
        async with db.execute("SELECT id FROM users WHERE telegram_user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await callback.message.answer("❌ Пользователь не найден")
                return
            referrer_user_id = row[0]
        
        # Get mamont details
        async with db.execute("""
            SELECT * FROM mamonts 
            WHERE mamont_id = ? AND referrer_user_id = ?
        """, (mamont_id, referrer_user_id)) as cursor:
            mamont = await cursor.fetchone()
    
    if not mamont:
        await callback.message.answer("❌ Мамонт не найден")
        return
    
    # Import image utilities
    from ..image_utils import create_mamont_image, get_mamont_display_name
    from aiogram.types import BufferedInputFile, InputMediaPhoto
    
    # Format mamont details
    status_emoji = {
        'attached': '🔗',
        'registered': '📝', 
        'paid': '💰'
    }
    
    status_text = {
        'attached': 'Привязан',
        'registered': 'Зарегистрирован',
        'paid': 'Оплатил'
    }
    
    status = mamont['status']
    text = f"<b>{status_emoji.get(status, '❓')} Мамонт #{mamont['mamont_id']}</b>\n\n"
    text += f"Статус: <b>{status_text.get(status, 'Неизвестно')}</b>\n\n"
    
    if status in ['registered', 'paid']:
        # Show all registration data
        if mamont['first_name']:
            text += f"<b>Имя:</b> {mamont['first_name']}\n"
        
        if mamont['last_name']:
            text += f"<b>Фамилия:</b> {mamont['last_name']}\n"
        
        if mamont['phone']:
            # Format phone number nicely
            phone = str(mamont['phone'])
            if phone.startswith('7') and len(phone) == 11:
                formatted_phone = f"+7 ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"
            else:
                formatted_phone = phone
            text += f"<b>Телефон:</b> <code>{formatted_phone}</code>\n"
        
        if mamont['email']:
            text += f"<b>Email:</b> <code>{mamont['email']}</code>\n"
        
        text += "\n"
        
        if mamont['tg_username']:
            text += f"<b>Telegram:</b> @{mamont['tg_username']}\n"
        elif mamont['tg_name']:
            text += f"<b>Telegram:</b> {mamont['tg_name']}\n"
    else:
        text += "<i>Данные появятся после регистрации мамонта на сайте</i>\n\n"
    
    # Add creation date
    if mamont['created_at']:
        try:
            from datetime import datetime
            created = datetime.fromisoformat(mamont['created_at'])
            text += f"<b>Привязан:</b> {created.strftime('%d.%m.%Y %H:%M')}"
        except:
            pass
    
    # Back button
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К списку мамонтов", callback_data="menu_clients")]
    ])
    
    try:
        # Generate mamont image with name overlay
        display_name = get_mamont_display_name(dict(mamont))
        img_bytes = create_mamont_image(display_name, mamont['mamont_id'])
        
        # Create input file
        photo = BufferedInputFile(img_bytes.read(), filename=f"mamont_{mamont['mamont_id']}.jpg")
        media = InputMediaPhoto(media=photo, caption=text, parse_mode="HTML")
        
        # Try to edit the message with new photo
        await callback.message.edit_media(media=media, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error creating mamont image: {e}")
        # Fallback to text-only edit
        try:
            await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
