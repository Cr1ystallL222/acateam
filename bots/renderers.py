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
    WELCOME_STICKER_ID,
    logger
)
from .database import (
    get_user_profits_stats, 
    get_or_create_referral, 
    save_last_menu_message_id,
    get_user_mamonts,
    get_theatre_links,
    get_cinema_links,
    get_link_by_id,
    get_cinema_link_by_id
)
from .utils import calculate_days_in_team, format_mamont_display
from .keyboards import (
    get_profile_keyboard, 
    get_theatre_keyboard,
    get_cinema_keyboard,
    get_clients_keyboard,
    get_stub_keyboard,
    get_events_keyboard,
    get_links_management_keyboard
)

async def render_profile_menu(chat_id: int, telegram_user_id: int, bot_user: dict, message_id: Optional[int] = None) -> int:
    """Render profile menu. Returns new message_id."""
    stats = await get_user_profits_stats(telegram_user_id)
    days_in_team = calculate_days_in_team(bot_user.get('joined_at'))
    balance = bot_user.get('balance') or 0
    balance_hold = bot_user.get('balance_hold') or 0
    
    balance_text = f"Баланс: <b>{balance}</b>"
    if balance_hold > 0:
        balance_text += f"\n  └ На удержании: <b>{balance_hold}</b>"
    
    caption = (
        f"🗃 <b>Твой профиль</b> <code>{telegram_user_id}</code>\n\n"
        f"💸 У тебя <b>{stats['profits_count']}</b> профитов на сумму <b>{stats['profits_sum']}</b> RUB\n"
        f"Средний профит: <b>{stats['profits_avg']}</b> RUB\n\n"
        f"{balance_text}\n\n"
        f"В команде: <b>{days_in_team}</b> дн."
    )
    
    is_admin = telegram_user_id in ADMIN_IDS
    keyboard = get_profile_keyboard(balance=balance, is_admin=is_admin)
    
    # Always delete old message to ensure Sticker appears before Menu
    if message_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        except:
            pass
            
    # Send sticker
    if WELCOME_STICKER_ID:
        try:
            await bot.send_sticker(chat_id, WELCOME_STICKER_ID)
        except Exception as e:
            logger.warning(f"Failed to send welcome sticker: {e}")
    
    # Send new message
    if PROFILE_PHOTO_PATH.exists():
        photo = FSInputFile(PROFILE_PHOTO_PATH)
        msg = await bot.send_photo(chat_id, photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
    else:
        logger.warning(f"Profile photo not found: {PROFILE_PHOTO_PATH}")
        msg = await bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=keyboard)
    
    await save_last_menu_message_id(telegram_user_id, msg.message_id)
    return msg.message_id

async def render_links_management_menu(chat_id: int, telegram_user_id: int, message_id: Optional[int] = None) -> int:
    """Render links management menu. Returns new message_id."""
    links = await get_theatre_links(telegram_user_id)
    
    # Build links list text
    if links:
        links_text = ""
        for idx, link in enumerate(links, start=1):
            city = link.get('custom_city') or "не указан"
            links_text += f"\n<b>Промокод №{idx}:</b> {link['name']}\n"
            links_text += f"<i>Адрес:</i> {city}\n"
    else:
        links_text = "\n<i>У вас пока нет ссылок.\nСоздайте первую ссылку!</i>\n"
    
    caption = (
        "🔗 <b>Ссылки для Театра</b>\n\n"
        "Ниже указаны ссылки и номера ваших конфигов\n\n"
        "🏷 <b>Текущие ссылки:</b>"
        f"{links_text}\n"
        "<i>Для настройки ссылки нажмите на соответствующий номер</i>"
    )
    
    keyboard = get_links_management_keyboard(links)
    
    # Try to edit existing message
    if message_id:
        try:
            await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=caption, parse_mode="HTML", reply_markup=keyboard)
            return message_id
        except TelegramBadRequest:
            try:
                await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=caption, parse_mode="HTML", reply_markup=keyboard)
                return message_id
            except TelegramBadRequest as e:
                logger.warning(f"Cannot edit message: {e}. Will delete and resend.")
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=message_id)
                except:
                    pass
    
    # Send new message
    msg = await bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=keyboard)
    await save_last_menu_message_id(telegram_user_id, msg.message_id)
    return msg.message_id


async def render_theatre_menu(chat_id: int, telegram_user_id: int, message_id: Optional[int] = None, link_id: Optional[int] = None) -> int:
    """Render theatre menu. If link_id is provided, use that link's code."""
    
    # Get link by id or fallback
    if link_id:
        link = await get_link_by_id(link_id)
        if link:
            ref_link = f"{SITE_URL}/?cl={link['link_code']}"
            link_name = link.get('name', 'Без названия')
        else:
            # Fallback to old ref system
            ref_code = await get_or_create_referral(telegram_user_id, chat_id)
            ref_link = f"{SITE_URL}/?ref={ref_code}"
            link_name = None
    else:
        # Fallback to old ref system
        ref_code = await get_or_create_referral(telegram_user_id, chat_id)
        ref_link = f"{SITE_URL}/?ref={ref_code}"
        link_name = None
    
    if link_name:
        caption = (
            f"<b>Theatre</b> — {link_name}\n\n"
            f"Инструкция к боту: <a href=\"{THEATRE_GUIDE_URL}\">ТЫК</a>\n"
            f"Ваша реферальная ссылка: <code>{ref_link}</code>"
        )
    else:
        caption = (
            "<b>Theatre</b>\n\n"
            f"Инструкция к боту: <a href=\"{THEATRE_GUIDE_URL}\">ТЫК</a>\n"
            f"Ваша реферальная ссылка: <code>{ref_link}</code>"
        )
    
    keyboard = get_theatre_keyboard(ref_link, link_id=link_id)
    
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
        text = "<b>Ваши мамонты</b>\n\n<i>У вас пока нет мамонтов.\nПоделитесь реферальной ссылкой, чтобы привлечь первых клиентов!</i>"
        keyboard = get_stub_keyboard()
    else:
        # Count by status
        attached_count = len([m for m in mamonts if m['status'] == 'attached'])
        registered_count = len([m for m in mamonts if m['status'] == 'registered'])
        paid_count = len([m for m in mamonts if m['status'] == 'paid'])
        
        text = (
            f"<b>Ваши мамонты</b> ({len(mamonts)})\n\n"
            f"Привязано: <b>{attached_count}</b>\n"
            f"Зарегистрировано: <b>{registered_count}</b>\n"
            f"Оплатило: <b>{paid_count}</b>\n\n"
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

async def render_settings_menu(chat_id: int, telegram_user_id: int, message_id: Optional[int] = None, link_id: Optional[int] = None) -> int:
    """Render settings menu with current worker or link settings. Returns new message_id."""
    from .database import get_worker_settings, get_link_by_id
    from .keyboards import get_settings_keyboard
    
    if link_id:
        link = await get_link_by_id(link_id)
        if link:
            settings = link
            header = f"<b>⚙️ Настройки Театра ({link['name']})</b>\n\n"
        else:
            settings = await get_worker_settings(telegram_user_id)
            header = "<b>⚙️ Настройки Театра</b>\n\n"
    else:
        settings = await get_worker_settings(telegram_user_id)
        header = "<b>⚙️ Настройки Театра</b>\n\n"
    
    min_price = settings.get('min_price_override')
    max_price = settings.get('max_price_override')
    city = settings.get('custom_city')
    # If using worker settings, fallback to KRD if empty. If using link settings, fallback to KRD if empty too?
    # Logic: if link settings are empty, do they use worker settings?
    # User Request: "create 2 links... if change settings of 1 then changes 2".
    # This implies they want independent settings.
    # So if link settings are empty, they are just empty/default.
    
    if not city and not link_id:
         city = "Краснодар"
    
    min_price_display = f"{min_price}₽" if min_price else "не установлена"
    max_price_display = f"{max_price}₽" if max_price else "не установлена"
    city_display = city if city else "не указан"
    
    text = (
        f"{header}"
        f"💰 <b>Мин. цена:</b> {min_price_display}\n"
        f"💎 <b>Макс. цена:</b> {max_price_display}\n"
        f"🏙️ <b>Город:</b> {city_display}\n\n"
        "<i>Нажмите на настройку чтобы изменить её.</i>\n\n"
    )
    
    if link_id:
        text += "<i>Эти настройки применяются только к этой ссылке.</i>"
    else:
        text += "<i>Эти настройки применяются ко всем вашим рефералам.</i>"
        
    keyboard = get_settings_keyboard(settings, link_id=link_id)
    
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

async def render_events_menu(chat_id: int, telegram_user_id: int, message_id: Optional[int] = None, event_type: str = 'theatre') -> int:
    """Render events menu. Returns new message_id."""
    if event_type == 'cinema':
        text = "<b>🎬 События Кино</b>\n\n<i>Управление событиями кино</i>\n\nВыберите действие:"
    else:
        text = "<b>🎪 События</b>\n\n<i>Управление событиями театра</i>\n\nВыберите действие:"
        
    keyboard = get_events_keyboard(event_type)
    
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

async def render_cinema_links_management_menu(chat_id: int, telegram_user_id: int, message_id: Optional[int] = None) -> int:
    """Render cinema links management menu. Returns new message_id."""
    links = await get_cinema_links(telegram_user_id)
    
    # Build links list text
    if links:
        links_text = ""
        for idx, link in enumerate(links, start=1):
            city = link.get('custom_city') or "не указан"
            links_text += f"\n<b>Промокод №{idx}:</b> {link['name']}\n"
            links_text += f"<i>Адрес:</i> {city}\n"
    else:
        links_text = "\n<i>У вас пока нет ссылок.\nСоздайте первую ссылку!</i>\n"
    
    caption = (
        "🔗 <b>Ссылки для Кино</b>\n\n"
        "Ниже указаны ссылки и номера ваших конфигов\n\n"
        "🏷 <b>Текущие ссылки:</b>"
        f"{links_text}\n"
        "<i>Для настройки ссылки нажмите на соответствующий номер</i>"
    )
    
    keyboard = get_links_management_keyboard(links, type="cinema")
    
    # Try to edit existing message
    if message_id:
        try:
            await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=caption, parse_mode="HTML", reply_markup=keyboard)
            return message_id
        except Exception:
            try:
                await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=caption, parse_mode="HTML", reply_markup=keyboard)
                return message_id
            except Exception:
                pass
    
    # Send new message
    msg = await bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=keyboard)
    await save_last_menu_message_id(telegram_user_id, msg.message_id)
    return msg.message_id

async def render_cinema_menu(chat_id: int, telegram_user_id: int, message_id: Optional[int] = None, link_id: Optional[int] = None) -> int:
    """Render cinema menu."""
    from .config import CINEMA_GUIDE_URL, CINEMA_PHOTO_RESOLVED, CINEMA_SITE_URL
    
    # Get link by id or fallback
    if link_id:
        link = await get_cinema_link_by_id(link_id)
        if link:
            ref_link = f"{CINEMA_SITE_URL}/?cl={link['link_code']}"
            link_name = link.get('name', 'Без названия')
        else:
            ref_code = await get_or_create_referral(telegram_user_id, chat_id)
            ref_link = f"{CINEMA_SITE_URL}/?ref={ref_code}"
            link_name = None
    else:
        ref_code = await get_or_create_referral(telegram_user_id, chat_id)
        ref_link = f"{CINEMA_SITE_URL}/?ref={ref_code}"
        link_name = None
    
    if link_name:
        caption = (
            f"<b>Cinema</b> — {link_name}\n\n"
            f"Инструкция: <a href=\"{CINEMA_GUIDE_URL}\">ТЫК</a>\n"
            f"Ваша реферальная ссылка: <code>{ref_link}</code>"
        )
    else:
        caption = (
            "<b>Cinema</b>\n\n"
            f"Инструкция: <a href=\"{CINEMA_GUIDE_URL}\">ТЫК</a>\n"
            f"Ваша реферальная ссылка: <code>{ref_link}</code>"
        )
    
    keyboard = get_cinema_keyboard(ref_link, link_id=link_id)
    
    # Try to edit existing message
    if message_id:
        try:
            if CINEMA_PHOTO_RESOLVED.exists():
                photo = FSInputFile(CINEMA_PHOTO_RESOLVED)
                media = InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML")
                await bot.edit_message_media(chat_id=chat_id, message_id=message_id, media=media, reply_markup=keyboard)
                return message_id
            else:
                await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=caption, parse_mode="HTML", reply_markup=keyboard)
                return message_id
        except Exception:
            pass
    
    # Send new message
    if CINEMA_PHOTO_RESOLVED.exists():
        photo = FSInputFile(CINEMA_PHOTO_RESOLVED)
        msg = await bot.send_photo(chat_id, photo, caption=caption, parse_mode="HTML", reply_markup=keyboard)
    else:
        msg = await bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=keyboard)
    
    await save_last_menu_message_id(telegram_user_id, msg.message_id)
    return msg.message_id

async def render_settings_menu_cinema(chat_id: int, telegram_user_id: int, message_id: Optional[int] = None, link_id: Optional[int] = None) -> int:
    """Render cinema settings menu."""
    from .database import get_worker_settings, get_cinema_link_by_id
    from .keyboards import get_settings_keyboard
    
    if link_id:
        link = await get_cinema_link_by_id(link_id)
        if link:
            settings = dict(link)
            settings['type'] = 'cinema'
            header = f"<b>⚙️ Настройки Кино ({link['name']})</b>\n\n"
        else:
            settings = await get_worker_settings(telegram_user_id)
            settings['type'] = 'cinema'
            header = "<b>⚙️ Настройки Кино</b>\n\n"
    else:
        settings = await get_worker_settings(telegram_user_id)
        settings['type'] = 'cinema'
        header = "<b>⚙️ Настройки Кино</b>\n\n"
    
    min_price = settings.get('min_price_override')
    max_price = settings.get('max_price_override')
    city = settings.get('custom_city')
    
    if not city and not link_id:
         city = "Краснодар"
    
    min_price_display = f"{min_price}₽" if min_price else "не установлена"
    max_price_display = f"{max_price}₽" if max_price else "не установлена"
    city_display = city if city else "не указан"
    
    text = (
        f"{header}"
        f"💰 <b>Мин. цена:</b> {min_price_display}\n"
        f"💎 <b>Макс. цена:</b> {max_price_display}\n"
        f"🏙️ <b>Город:</b> {city_display}\n\n"
        "<i>Нажмите на настройку чтобы изменить её.</i>\n\n"
    )
    
    if link_id:
        text += "<i>Эти настройки применяются только к этой ссылке.</i>"
    else:
        text += "<i>Эти настройки применяются ко всем вашим рефералам.</i>"
        
    keyboard = get_settings_keyboard(settings, link_id=link_id)
    
    if message_id:
        try:
            await bot.edit_message_caption(chat_id=chat_id, message_id=message_id, caption=text, parse_mode="HTML", reply_markup=keyboard)
            return message_id
        except Exception:
            try:
                await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode="HTML", reply_markup=keyboard)
                return message_id
            except Exception:
                pass
    
    msg = await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=keyboard)
    await save_last_menu_message_id(telegram_user_id, msg.message_id)
    return msg.message_id
