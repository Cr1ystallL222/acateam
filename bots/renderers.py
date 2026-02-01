from typing import Optional
from aiogram.types import FSInputFile, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from .loader import bot
from .config import (
    SITE_URL, 
    PROFILE_PHOTO_PATH, 
    THEATRE_PHOTO_RESOLVED,
    THEATRE_GUIDE_URL,
    ADMIN_IDS,
    logger
)
from .database import (
    get_user_profits_stats, 
    get_or_create_referral, 
    save_last_menu_message_id,
    get_user_mamonts
)
from .utils import calculate_days_in_team, format_mamont_display
from .keyboards import (
    get_profile_keyboard, 
    get_theatre_keyboard, 
    get_clients_keyboard,
    get_stub_keyboard,
    get_events_keyboard
)

async def render_profile_menu(chat_id: int, telegram_user_id: int, bot_user: dict, message_id: Optional[int] = None) -> int:
    """Render profile menu. Returns new message_id."""
    stats = await get_user_profits_stats(telegram_user_id)
    days_in_team = calculate_days_in_team(bot_user.get('joined_at'))
    balance = bot_user.get('balance') or 0
    
    caption = (
        f"🗃 <b>Твой профиль</b> <code>{telegram_user_id}</code>\n\n"
        f"💸 У тебя <b>{stats['profits_count']}</b> профитов на сумму <b>{stats['profits_sum']}</b> RUB\n"
        f"Средний профит: <b>{stats['profits_avg']}</b> RUB\n\n"
        f"Баланс: <b>{balance}</b>\n\n"
        f"В команде: <b>{days_in_team}</b> дн."
    )
    
    is_admin = telegram_user_id in ADMIN_IDS
    keyboard = get_profile_keyboard(is_admin=is_admin)
    
    # Try to edit existing message
    if message_id:
        try:
            if PROFILE_PHOTO_PATH.exists():
                photo = FSInputFile(PROFILE_PHOTO_PATH)
                media = InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML")
                await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=keyboard)
                return message_id
            else:
                await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=caption, parse_mode="HTML", reply_markup=keyboard)
                return message_id
        except TelegramBadRequest as e:
            logger.warning(f"Cannot edit message: {e}. Will delete and resend.")
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except:
                pass
    
    # Send new message
    if PROFILE_PHOTO_PATH.exists():
        photo = FSInputFile(PROFILE_PHOTO_PATH)
        msg = await bot.send_photo(chat_id, photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
    else:
        logger.warning(f"Profile photo not found: {PROFILE_PHOTO_PATH}")
        msg = await bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=keyboard)
    
    await save_last_menu_message_id(telegram_user_id, msg.message_id)
    return msg.message_id

async def render_theatre_menu(chat_id: int, telegram_user_id: int, message_id: Optional[int] = None) -> int:
    """Render theatre menu. Returns new message_id."""
    ref_code = await get_or_create_referral(telegram_user_id, chat_id)
    ref_link = f"{SITE_URL}/?ref={ref_code}"
    
    caption = (
        "🎭 <b>Theatre</b>\n\n"
        f"📝 Инструкция к боту: <a href=\"{THEATRE_GUIDE_URL}\">ТЫК</a>\n"
        f"🔗 Ваша реферальная ссылка: <code>{ref_link}</code>"
    )
    
    keyboard = get_theatre_keyboard(ref_link)
    
    # Try to edit existing message
    if message_id:
        try:
            if THEATRE_PHOTO_RESOLVED.exists():
                photo = FSInputFile(THEATRE_PHOTO_RESOLVED)
                media = InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML")
                await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=keyboard)
                return message_id
            else:
                await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=caption, parse_mode="HTML", reply_markup=keyboard)
                return message_id
        except TelegramBadRequest as e:
            logger.warning(f"Cannot edit message: {e}. Will delete and resend.")
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except:
                pass
    
    # Send new message
    if THEATRE_PHOTO_RESOLVED.exists():
        photo = FSInputFile(THEATRE_PHOTO_RESOLVED)
        msg = await bot.send_photo(chat_id, photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
    else:
        logger.warning(f"Theatre photo not found: {THEATRE_PHOTO_RESOLVED}")
        msg = await bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=keyboard)
    
    await save_last_menu_message_id(telegram_user_id, msg.message_id)
    return msg.message_id

async def render_clients_menu(chat_id: int, telegram_user_id: int, message_id: Optional[int] = None) -> int:
    """Render clients menu with mamonts list. Returns new message_id."""
    
    # Get user's mamonts
    mamonts = await get_user_mamonts(telegram_user_id)
    
    if not mamonts:
        text = "<b>👥 Ваши мамонты</b>\n\n<i>У вас пока нет мамонтов.\nПоделитесь реферальной ссылкой, чтобы привлечь первых клиентов!</i>"
        keyboard = get_stub_keyboard()
    else:
        # Count by status
        attached_count = len([m for m in mamonts if m['status'] == 'attached'])
        registered_count = len([m for m in mamonts if m['status'] == 'registered'])
        paid_count = len([m for m in mamonts if m['status'] == 'paid'])
        
        text = (
            f"<b>👥 Ваши мамонты</b> ({len(mamonts)})\n\n"
            f"🔗 Привязано: <b>{attached_count}</b>\n"
            f"📝 Зарегистрировано: <b>{registered_count}</b>\n"
            f"💰 Оплатило: <b>{paid_count}</b>\n\n"
            f"<i>Выберите мамонта для просмотра деталей:</i>"
        )
        keyboard = get_clients_keyboard(mamonts)
    
    if message_id:
        try:
            await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=text, parse_mode="HTML", reply_markup=keyboard)
            return message_id
        except TelegramBadRequest:
            try:
                await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode="HTML", reply_markup=keyboard)
                return message_id
            except TelegramBadRequest as e:
                logger.warning(f"Cannot edit message: {e}. Will delete and resend.")
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=message_id)
                except:
                    pass
    
    msg = await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)
    await save_last_menu_message_id(telegram_user_id, msg.message_id)
    return msg.message_id

async def render_settings_menu(chat_id: int, telegram_user_id: int, message_id: Optional[int] = None) -> int:
    """Render settings stub menu. Returns new message_id."""
    text = "<b>⚙️ Раздел Настройки</b>\n\n<i>В разработке...</i>"
    keyboard = get_stub_keyboard()
    
    if message_id:
        try:
            await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=text, parse_mode="HTML", reply_markup=keyboard)
            return message_id
        except TelegramBadRequest:
            try:
                await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode="HTML", reply_markup=keyboard)
                return message_id
            except TelegramBadRequest as e:
                logger.warning(f"Cannot edit message: {e}. Will delete and resend.")
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=message_id)
                except:
                    pass
    
    msg = await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)
    await save_last_menu_message_id(telegram_user_id, msg.message_id)
    return msg.message_id

async def render_events_menu(chat_id: int, telegram_user_id: int, message_id: Optional[int] = None) -> int:
    """Render events menu. Returns new message_id."""
    text = "<b>🎪 События</b>\n\n<i>Управление событиями театра</i>\n\nВыберите действие:"
    keyboard = get_events_keyboard()
    
    if message_id:
        try:
            await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=text, parse_mode="HTML", reply_markup=keyboard)
            return message_id
        except TelegramBadRequest:
            try:
                await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode="HTML", reply_markup=keyboard)
                return message_id
            except TelegramBadRequest as e:
                logger.warning(f"Cannot edit message: {e}. Will delete and resend.")
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=message_id)
                except:
                    pass
    
    msg = await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)
    await save_last_menu_message_id(telegram_user_id, msg.message_id)
    return msg.message_id
