from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta, timezone

from ..loader import bot, dp
from ..config import SITE_URL, ADMIN_IDS, logger
from ..utils import format_cooldown_remaining, is_cooldown_active
from ..database import get_or_create_bot_user, get_or_create_referral, get_application_approval_data, approve_application, reject_application
from ..renderers import (
    render_theatre_menu,
    render_clients_menu,
    render_settings_menu,
    render_profile_menu,
    render_events_menu,
    render_links_management_menu
)

@dp.callback_query(F.data == "menu_admin")
async def cb_menu_admin(callback: types.CallbackQuery):
    if callback.from_user.id in ADMIN_IDS:
        await callback.answer("Админ панель скоро будет добавлена", show_alert=True)
    else:
        await callback.answer("Доступ запрещен", show_alert=True)

@dp.callback_query(F.data == "menu_theatre")
async def cb_menu_theatre(callback: types.CallbackQuery):
    """Open links management menu instead of direct theatre menu."""
    await callback.answer()
    msg_id = callback.message.message_id
    await render_links_management_menu(callback.message.chat.id, callback.from_user.id, msg_id)


@dp.callback_query(F.data.startswith("select_link:"))
async def cb_select_link(callback: types.CallbackQuery):
    """Select a specific link and open Theatre menu with it."""
    await callback.answer()
    link_id = int(callback.data.split(":")[1])
    msg_id = callback.message.message_id
    await render_theatre_menu(callback.message.chat.id, callback.from_user.id, msg_id, link_id=link_id)


@dp.callback_query(F.data == "create_link")
async def cb_create_link(callback: types.CallbackQuery, state: FSMContext):
    """Start link creation flow."""
    await callback.answer()
    
    from .fsm import TheatreLinkCreation
    
    text = (
        "🔗 <b>Создание ссылки</b>\n\n"
        "Введите название ссылки:\n\n"
        "<i>Например: Главная, VK, Telegram, Instagram</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="menu_theatre")]
    ])
    
    try:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)
    
    await state.set_state(TheatreLinkCreation.waiting_link_name)


@dp.callback_query(F.data == "menu_back_links")
async def cb_back_to_links(callback: types.CallbackQuery):
    """Return to links management menu from Theatre menu."""
    await callback.answer()
    msg_id = callback.message.message_id
    await render_links_management_menu(callback.message.chat.id, callback.from_user.id, msg_id)

@dp.callback_query(F.data == "menu_cinema")
async def cb_menu_cinema(callback: types.CallbackQuery):
    await callback.answer("Скоро будет доступно", show_alert=True)

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

# ============================================================================
# Settings Handlers
# ============================================================================

@dp.callback_query(F.data == "settings_min_price")
async def cb_settings_min_price(callback: types.CallbackQuery):
    """Show min price options."""
    await callback.answer()
    
    from ..database import MIN_PRICE_OPTIONS, get_worker_settings
    
    settings = await get_worker_settings(callback.from_user.id)
    current = settings.get('min_price_override')
    
    text = (
        "<b>💰 Минимальная цена</b>\n\n"
        "Выберите минимальную цену для событий:\n\n"
        "<i>Эта цена будет применяться\nко всем системным событиям\nдля ваших рефералов.</i>"
    )
    
    keyboard_buttons = []
    for price in MIN_PRICE_OPTIONS:
        mark = " ✓" if current == price else ""
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"{price}₽{mark}",
            callback_data=f"set_min_price:{price}"
        )])
    
    # Add "Reset" and "Back" buttons
    keyboard_buttons.append([InlineKeyboardButton(text="❌ Сбросить", callback_data="set_min_price:0")])
    keyboard_buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu_settings")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    try:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("set_min_price:"))
async def cb_set_min_price(callback: types.CallbackQuery):
    """Set min price value."""
    price = int(callback.data.split(":")[1])
    
    from ..database import update_worker_setting, MIN_PRICE_OPTIONS
    
    # Validate price
    if price == 0:
        # Reset
        await update_worker_setting(callback.from_user.id, 'min_price_override', None)
        await callback.answer("✅ Мин. цена сброшена", show_alert=True)
    elif price in MIN_PRICE_OPTIONS:
        await update_worker_setting(callback.from_user.id, 'min_price_override', price)
        await callback.answer(f"✅ Мин. цена установлена: {price}₽", show_alert=True)
    else:
        await callback.answer("❌ Недопустимое значение", show_alert=True)
        return
    
    # Return to settings menu    
    await render_settings_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id)


@dp.callback_query(F.data == "settings_max_price")
async def cb_settings_max_price(callback: types.CallbackQuery, state: FSMContext):
    """Prompt user to enter max price."""
    await callback.answer()
    
    from ..database import get_worker_settings
    from .fsm import SettingsMaxPrice
    
    settings = await get_worker_settings(callback.from_user.id)
    current = settings.get('max_price_override')
    
    current_text = f"Текущее значение: {current}₽" if current else "Текущее значение: не установлено"
    
    text = (
        "<b>💎 Максимальная цена</b>\n\n"
        f"{current_text}\n\n"
        "Введите максимальную цену за место (в рублях):\n\n"
        "<i>Это будет максимальная цена за место\nдля ваших рефералов.</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Сбросить", callback_data="reset_max_price")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_settings")]
    ])
    
    try:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)
    
    await state.set_state(SettingsMaxPrice.waiting_max_price)


@dp.callback_query(F.data == "reset_max_price")
async def cb_reset_max_price(callback: types.CallbackQuery, state: FSMContext):
    """Reset max price to default."""
    from ..database import update_worker_setting
    
    await update_worker_setting(callback.from_user.id, 'max_price_override', None)
    await callback.answer("✅ Макс. цена сброшена", show_alert=True)
    await state.clear()
    
    # Return to settings menu    
    await render_settings_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id)


@dp.callback_query(F.data == "settings_city")
async def cb_settings_city(callback: types.CallbackQuery, state: FSMContext):
    """Show city selection / input prompt."""
    await callback.answer()
    
    from ..database import get_available_cities, get_worker_settings
    
    settings = await get_worker_settings(callback.from_user.id)
    current_city = settings.get('custom_city') or "Краснодар"
    
    cities = get_available_cities()
    
    text = (
        "<b>🏙️ Настройка города</b>\n\n"
        f"Текущий город: <b>{current_city}</b>\n\n"
        "Выберите город из списка или введите свой:\n\n"
        "<i>Город влияет на название афиши\nи места проведения событий.</i>"
    )
    
    # Show popular cities as buttons (first 6)
    keyboard_buttons = []
    for i in range(0, min(6, len(cities)), 2):
        row = []
        for j in range(2):
            if i + j < len(cities):
                city = cities[i + j]
                mark = " ✓" if current_city == city else ""
                row.append(InlineKeyboardButton(
                    text=f"{city}{mark}",
                    callback_data=f"set_city:{city}"
                ))
        keyboard_buttons.append(row)
    
    # Add "Enter custom" and "Back" buttons
    keyboard_buttons.append([InlineKeyboardButton(text="✏️ Ввести свой город", callback_data="enter_custom_city")])
    keyboard_buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu_settings")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    try:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("set_city:"))
async def cb_set_city(callback: types.CallbackQuery):
    """Set city from predefined list."""
    city = callback.data.split(":", 1)[1]
    
    from ..database import update_worker_setting
    
    await update_worker_setting(callback.from_user.id, 'custom_city', city)
    await callback.answer(f"✅ Город: {city}", show_alert=True)
    
    # Return to settings menu
    await render_settings_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id)


@dp.callback_query(F.data == "enter_custom_city")
async def cb_enter_custom_city(callback: types.CallbackQuery, state: FSMContext):
    """Prompt user to enter custom city name."""
    await callback.answer()
    
    from ..handlers.fsm import SettingsCity
    
    text = (
        "<b>✏️ Введите название города</b>\n\n"
        "Напишите название города,\nкоторый будет отображаться\nв афише для ваших рефералов.\n\n"
        "<i>Например: Пермь, Казань, Москва</i>"
    )
    
    try:
        await callback.message.edit_caption(caption=text, parse_mode="HTML")
    except:
        try:
            await callback.message.edit_text(text=text, parse_mode="HTML")
        except:
            await callback.message.answer(text=text, parse_mode="HTML")
    
    await state.set_state(SettingsCity.waiting_city_name)

# End of Settings Handlers
# ============================================================================

@dp.callback_query(F.data == "menu_events")
async def cb_menu_events(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    await render_events_menu(callback.message.chat.id, callback.from_user.id, msg_id)

@dp.callback_query(F.data == "events_list")
async def cb_events_list(callback: types.CallbackQuery):
    await cb_events_list_page(callback, 1)

@dp.callback_query(F.data.startswith("events_page:"))
async def cb_events_page(callback: types.CallbackQuery):
    page = int(callback.data.split(":")[1])
    await cb_events_list_page(callback, page)

async def cb_events_list_page(callback: types.CallbackQuery, page: int):
    await callback.answer()
    msg_id = callback.message.message_id
    user_id = callback.from_user.id
    
    # Get database events ONLY - no more hardcoded static events
    from ..database import get_all_events
    all_events = await get_all_events()
    
    # Pagination settings
    events_per_page = 10
    total_events = len(all_events)
    total_pages = (total_events + events_per_page - 1) // events_per_page  # Ceiling division
    
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    start_idx = (page - 1) * events_per_page
    end_idx = start_idx + events_per_page
    page_events = all_events[start_idx:end_idx]
    
    if not all_events:
        text = "<b>Список событий</b>\n\n<i>Пока нет доступных событий.</i>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="menu_events")]
        ])
    else:
        text = f"<b>Список событий</b> ({total_events})\n<i>Страница {page} из {total_pages}</i>\n\n<i>Выберите событие для просмотра:</i>"
        
        keyboard_buttons = []
        for event in page_events:
            from datetime import datetime
            try:
                dt = datetime.strptime(event['date_time'], "%Y-%m-%d %H:%M")
                date_str = dt.strftime("%d.%m")
            except:
                date_str = "Дата"
            
            # Show event type
            if event.get('is_system', True):
                event_type = ""  # No prefix for system events
            elif event.get('created_by') == user_id:
                event_type = "Ваше "
            else:
                event_type = "Реферальное "
            
            button_text = f"{event_type}{event['title']} ({date_str})"
            
            # Use event ID directly (no more static_ prefix)
            event_id = event['id']
            keyboard_buttons.append([InlineKeyboardButton(
                text=button_text, 
                callback_data=f"view_event:{event_id}"
            )])
        
        # Pagination buttons
        pagination_buttons = []
        if page > 1:
            pagination_buttons.append(InlineKeyboardButton(text="⬅️ Пред.", callback_data=f"events_page:{page-1}"))
        if page < total_pages:
            pagination_buttons.append(InlineKeyboardButton(text="След. ➡️", callback_data=f"events_page:{page+1}"))
        
        if pagination_buttons:
            keyboard_buttons.append(pagination_buttons)
        
        keyboard_buttons.append([InlineKeyboardButton(text="Назад", callback_data="menu_events")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Universal message editing approach
    try:
        await bot.edit_message_caption(chat_id=callback.message.chat.id, message_id=msg_id, caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=msg_id, text=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
            except:
                pass
            await bot.send_message(chat_id=callback.message.chat.id, text=text, parse_mode="HTML", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("view_event:"))
async def cb_view_event(callback: types.CallbackQuery):
    """Show event details when clicking on event in list."""
    await callback.answer()
    
    event_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    msg_id = callback.message.message_id
    
    from ..database import get_event_by_id
    from aiogram.types import InputMediaPhoto, FSInputFile
    import os
    
    event = await get_event_by_id(event_id)
    
    if not event:
        await callback.message.answer("Событие не найдено")
        return
    
    # Format date
    try:
        dt = datetime.strptime(event['date_time'], "%Y-%m-%d %H:%M")
        date_str = dt.strftime("%d.%m.%Y в %H:%M")
    except:
        date_str = event['date_time']
    
    # Build event details text - new format
    text = f"<b>{event['title']}</b>\n"
    text += f"{date_str}\n"
    text += f"{event['venue']}\n\n"
    
    if event.get('description'):
        text += f"{event['description']}\n\n"
    
    text += f"<b>Цена:</b> {event['min_price']} - {event['max_price']}₽"
    
    # Show creator if not system event
    if not event.get('is_system', True) and event.get('creator_name'):
        text += f"\n\n<i>Создатель: {event['creator_name']}</i>"
    
    # Build keyboard buttons
    keyboard_buttons = []
    
    # Edit button (only for event creator or system events for admins)
    is_creator = event.get('created_by') == user_id
    is_admin = user_id in ADMIN_IDS
    
    if is_creator or (event.get('is_system', True) and is_admin):
        keyboard_buttons.append([InlineKeyboardButton(
            text="Редактировать",
            callback_data=f"edit_event:{event_id}"
        )])
    
    # Back button
    keyboard_buttons.append([InlineKeyboardButton(
        text="Назад",
        callback_data="events_list"
    )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Check if event has photo - convert relative path to absolute
    photo_path = event.get('photo_path')
    if photo_path:
        # Convert /images/... to absolute path
        if photo_path.startswith('/images/'):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            photo_path = os.path.join(base_dir, 'web', 'public', photo_path.lstrip('/'))
    
    has_photo = photo_path and os.path.exists(photo_path)
    
    if has_photo:
        try:
            photo = FSInputFile(photo_path)
            media = InputMediaPhoto(media=photo, caption=text, parse_mode="HTML")
            await callback.message.edit_media(media=media, reply_markup=keyboard)
            return
        except Exception as e:
            logger.warning(f"Failed to send photo for event {event_id}: {e}")
    
    # Fallback to text message
    try:
        await bot.edit_message_caption(
            chat_id=callback.message.chat.id,
            message_id=msg_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except:
        try:
            await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=msg_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except:
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
            except:
                pass
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard
            )


@dp.callback_query(F.data == "events_add")
async def cb_events_add(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    text = (
        "<b>Создание события</b>\n\n"
        "Давайте создадим новое событие!\n\n"
        "<b>Название события</b>\n\n"
        "Введите название события:\n\n"
        "<i>Например: Гамлет, Ромео и Джульетта, Концерт классической музыки</i>"
    )
    
    try:
        # Try to edit as text message first
        await callback.message.edit_text(text, parse_mode="HTML")
    except:
        try:
            # If that fails, try to edit as caption (for photo messages)
            await callback.message.edit_caption(caption=text, parse_mode="HTML")
        except:
            # If both fail, delete and send new message
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(text, parse_mode="HTML")
    
    from ..handlers.fsm import EventCreation
    await state.set_state(EventCreation.waiting_title)

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
    """Return to links management menu from clients/settings/events."""
    await callback.answer()
    msg_id = callback.message.message_id
    await render_links_management_menu(callback.message.chat.id, callback.from_user.id, msg_id)

@dp.callback_query(F.data == "copy_ref_link")
async def cb_copy_ref_link(callback: types.CallbackQuery):
    """Send ref link as separate message for easy copying (fallback for CopyTextButton)."""
    await callback.answer("Ссылка отправлена ниже", show_alert=False)
    
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
    
    
    # Get application data using adapter
    row = await get_application_approval_data(app_id)
    confirm_message_id = row['confirm_message_id'] if row else None
    chat_id = row['chat_id'] if row else None
    app_user_id = row['telegram_user_id'] if row else user_id
    
    # Approve matches logic
    await approve_application(app_id, admin_id, app_user_id)
    
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
    cooldown_until = (datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None)
    
    
    # Get application data using adapter
    row = await get_application_approval_data(app_id)
    confirm_message_id = row['confirm_message_id'] if row else None
    chat_id = row['chat_id'] if row else None
    app_user_id = row['telegram_user_id'] if row else user_id
    
    # Reject application
    await reject_application(app_id, admin_id, app_user_id, cooldown_until)
    
    logger.info(f"Application rejected: id={app_id}, telegram_user_id={user_id}, by={admin_id}")
    
    try:
        await callback.message.edit_text(
            callback.message.text + f"\n\n<b>ОТКЛОНЕНО</b> ({callback.from_user.full_name})",
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
            await bot.send_message(chat_id, "ОТКЛОНЕНО")
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
        await callback.message.answer("Вы не зарегистрированы. Используйте /start", parse_mode="HTML")
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
                "<b>Доступ не разрешён</b>\n\n"
                "Для получения доступа к боту необходимо пройти анкету.\n"
                "Используйте /start",
                parse_mode="HTML"
            )
        return
    
    ref_code = await get_or_create_referral(user_id, chat_id)
    ref_link = f"{SITE_URL}/?ref={ref_code}"
    
    await callback.message.answer(
        "<b>Ваша реферальная ссылка</b>\n\n"
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
        'attached': 'Привязан',
        'registered': 'Зарегистрирован', 
        'paid': 'Оплатил'
    }
    
    status_text = {
        'attached': 'Привязан',
        'registered': 'Зарегистрирован',
        'paid': 'Оплатил'
    }
    
    status = mamont['status']
    text = f"<b>{status_emoji.get(status, 'Неизвестно')} Мамонт #{mamont['mamont_id']}</b>\n\n"
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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="К списку мамонтов", callback_data="menu_clients")]
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

# ============================================================================
# Event Editing Callbacks
# ============================================================================

@dp.callback_query(F.data.startswith("edit_event:"))
async def cb_edit_event_menu(callback: types.CallbackQuery):
    await callback.answer()
    
    data_parts = callback.data.split(":")
    if len(data_parts) > 1:
        event_id = int(data_parts[1])
    else:
        # Handle case where event_id might be lost or handled differently
        await callback.message.answer("Ошибка: ID события не найден")
        return
    
    from ..database import get_event_by_id, get_worker_settings
    event = await get_event_by_id(event_id)
    settings = await get_worker_settings(callback.from_user.id)
    city = settings.get('custom_city', 'Краснодар')
    
    if not event:
        await callback.message.answer("Событие не найдено")
        return
        
    text = (
        f"<b>Редактирование события</b>\n\n"
        f"<b>Название:</b> {event['title']}\n"
        f"<b>Дата:</b> {event['date_time']}\n"
        f"<b>Место:</b> {event['venue']}\n"
        f"<b>Цены:</b> {event['min_price']} - {event['max_price']} ₽\n\n"
        f"<i>Ваш город настроек: {city}</i>\n"
        f"<i>Выберите, что хотите изменить:</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Название", callback_data=f"edit_event_title:{event_id}"),
            InlineKeyboardButton(text="Описание", callback_data=f"edit_event_desc:{event_id}")
        ],
        [
            InlineKeyboardButton(text="Дата и время", callback_data=f"edit_event_datetime:{event_id}"),
            InlineKeyboardButton(text="Место", callback_data=f"edit_event_venue:{event_id}")
        ],
        [
            InlineKeyboardButton(text="Мин. цена", callback_data=f"edit_event_min_price:{event_id}"),
            InlineKeyboardButton(text="Макс. цена", callback_data=f"edit_event_max_price:{event_id}")
        ],
        [InlineKeyboardButton(text="◀️ Назад к событию", callback_data=f"view_event:{event_id}")]
    ])
    
    try:
        # Try to edit caption if it's a photo message
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            # Try to edit text if it's a text message
            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
        except:
             # If type mismatch (photo <-> text) or other error, delete and send
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("edit_event_title:"))
async def cb_edit_title(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    event_id = int(callback.data.split(":")[1])
    
    from ..handlers.fsm import EventEdit
    await state.set_state(EventEdit.waiting_title)
    await state.update_data(event_id=event_id)
    
    await callback.message.answer(
        "<b>Изменение названия</b>\n\n"
        "Введите новое название события:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data=f"edit_event:{event_id}")]
        ])
    )

@dp.callback_query(F.data.startswith("edit_event_desc:"))
async def cb_edit_desc(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    event_id = int(callback.data.split(":")[1])
    
    from ..handlers.fsm import EventEdit
    await state.set_state(EventEdit.waiting_description)
    await state.update_data(event_id=event_id)
    
    await callback.message.answer(
        "<b>Изменение описания</b>\n\n"
        "Введите новое описание события:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data=f"edit_event:{event_id}")]
        ])
    )

@dp.callback_query(F.data.startswith("edit_event_venue:"))
async def cb_edit_venue(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    event_id = int(callback.data.split(":")[1])
    
    from ..handlers.fsm import EventEdit
    from ..database import get_worker_settings, get_venues_for_city
    
    await state.set_state(EventEdit.waiting_venue)
    await state.update_data(event_id=event_id)
    
    # Get venues for user's city
    settings = await get_worker_settings(callback.from_user.id)
    city = settings.get('custom_city', 'Краснодар')
    venues = get_venues_for_city(city)
    
    venues_text = "\n".join([f"• <code>{v}</code>" for v in venues])
    
    await callback.message.answer(
        f"<b>Изменение места проведения</b>\n\n"
        f"Ваш город: <b>{city}</b>\n\n"
        f"Доступные площадки:\n{venues_text}\n\n"
        f"Введите название места или скопируйте из списка выше:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data=f"edit_event:{event_id}")]
        ])
    )

@dp.callback_query(F.data.startswith("edit_event_datetime:"))
async def cb_edit_datetime(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    event_id = int(callback.data.split(":")[1])
    
    from ..handlers.fsm import EventEdit
    await state.set_state(EventEdit.waiting_datetime)
    await state.update_data(event_id=event_id)
    
    await callback.message.answer(
        "<b>Изменение даты и времени</b>\n\n"
        "Введите новую дату и время (ДД.ММ.ГГГГ ЧЧ:ММ):",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data=f"edit_event:{event_id}")]
        ])
    )

@dp.callback_query(F.data.startswith("edit_event_min_price:"))
async def cb_edit_min_price(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    event_id = int(callback.data.split(":")[1])
    
    from ..handlers.fsm import EventEdit
    await state.set_state(EventEdit.waiting_min_price)
    await state.update_data(event_id=event_id)
    
    await callback.message.answer(
        "<b>Изменение мин. цены</b>\n\n"
        "Введите новую минимальную цену:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data=f"edit_event:{event_id}")]
        ])
    )

@dp.callback_query(F.data.startswith("edit_event_max_price:"))
async def cb_edit_max_price(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    event_id = int(callback.data.split(":")[1])
    
    from ..handlers.fsm import EventEdit
    await state.set_state(EventEdit.waiting_max_price)
    await state.update_data(event_id=event_id)
    
    await callback.message.answer(
        "<b>Изменение макс. цены</b>\n\n"
        "Введите новую максимальную цену:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data=f"edit_event:{event_id}")]
        ])
    )
@dp.callback_query(F.data.startswith("select_seats:"))
async def cb_select_seats(callback: types.CallbackQuery):
    await callback.answer()
    
    event_id = int(callback.data.split(":")[1])
    
    from ..database import get_event_by_id, get_event_seats
    event = await get_event_by_id(event_id)
    seats = await get_event_seats(event_id)
    
    if not event:
        await callback.message.answer("Событие не найдено")
        return
    
    # Create seat map visualization
    seat_map = create_seat_map_text(seats)
    
    # Format date
    from datetime import datetime
    try:
        dt = datetime.strptime(event['date_time'], "%Y-%m-%d %H:%M")
        formatted_date = dt.strftime("%d %B, %H:%M")
        weekday = dt.strftime("%A")
        weekdays = {
            'Monday': 'ПН', 'Tuesday': 'ВТ', 'Wednesday': 'СР', 
            'Thursday': 'ЧТ', 'Friday': 'ПТ', 'Saturday': 'СБ', 'Sunday': 'ВС'
        }
        weekday_ru = weekdays.get(weekday, weekday)
    except:
        formatted_date = event['date_time']
        weekday_ru = ""
    
    available_seats = len([s for s in seats if s['is_available']])
    
    text = (
        f"<b>{event['title']}</b>\n"
        f"{formatted_date}, {weekday_ru}\n"
        f"{event['venue']}\n\n"
        f"<b>Схема зала</b>    <b>Доступные билеты</b>\n\n"
        f"{seat_map}\n\n"
        f"Доступно: <b>{available_seats}</b> мест\n"
        f"Цены: <b>{event['min_price']} - {event['max_price']}</b> ₽\n\n"
        f"<i>Выберите ряд для бронирования:</i>"
    )
    
    # Create row selection keyboard
    keyboard_buttons = []
    rows = {}
    for seat in seats:
        row = seat['row_number']
        if row not in rows:
            rows[row] = {'available': 0, 'total': 0}
        rows[row]['total'] += 1
        if seat['is_available']:
            rows[row]['available'] += 1
    
    # Group rows by 3
    row_numbers = sorted(rows.keys())
    for i in range(0, len(row_numbers), 3):
        row_buttons = []
        for j in range(3):
            if i + j < len(row_numbers):
                row = row_numbers[i + j]
                available = rows[row]['available']
                if available > 0:
                    row_buttons.append(InlineKeyboardButton(
                        text=f"Ряд {row} ({available})",
                        callback_data=f"select_row:{event_id}:{row}"
                    ))
                else:
                    row_buttons.append(InlineKeyboardButton(
                        text=f"Ряд {row}",
                        callback_data="row_full"
                    ))
        if row_buttons:
            keyboard_buttons.append(row_buttons)
    
    keyboard_buttons.append([InlineKeyboardButton(text="Назад к событию", callback_data=f"view_event:{event_id}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Universal message editing approach for select_seats
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)

def create_seat_map_text(seats):
    """Create a text representation of the seat map."""
    # Group seats by price for color coding
    price_groups = {}
    for seat in seats:
        price = seat['price']
        if price not in price_groups:
            price_groups[price] = []
        price_groups[price].append(seat)
    
    # Create price legend
    sorted_prices = sorted(price_groups.keys())
    legend_items = []
    symbols = ['🔵', '🟢', '🟡', '🟠', '🔴', '🟣', '🟤', '⚫', '⚪', '🔘']
    
    price_symbols = {}
    for i, price in enumerate(sorted_prices):
        symbol = symbols[i % len(symbols)]
        price_symbols[price] = symbol
        legend_items.append(f"{symbol} {price}")
    
    legend = " ".join(legend_items[:5]) + "\n" + " ".join(legend_items[5:]) if len(legend_items) > 5 else " ".join(legend_items)
    
    # Create seat map
    rows = {}
    for seat in seats:
        row = seat['row_number']
        if row not in rows:
            rows[row] = {}
        rows[row][seat['seat_number']] = seat
    
    map_lines = [legend, ""]
    
    # Add stage
    map_lines.append("        СЦЕНА")
    map_lines.append("")
    
    # Add rows (show only first few rows for demo)
    for row_num in sorted(rows.keys())[:8]:  # Show first 8 rows
        row_seats = rows[row_num]
        line = f"Ряд {row_num:2d}: "
        
        for seat_num in sorted(row_seats.keys())[:20]:  # Show first 20 seats
            seat = row_seats[seat_num]
            if seat['is_available']:
                symbol = price_symbols[seat['price']]
            else:
                symbol = "ЗАНЯТО"
            line += symbol
        
        map_lines.append(line)
    
    if len(rows) > 8:
        map_lines.append(f"... и еще {len(rows) - 8} рядов")
    
    return "\n".join(map_lines)

@dp.callback_query(F.data == "row_full")
async def cb_row_full(callback: types.CallbackQuery):
    await callback.answer("Все места в этом ряду заняты", show_alert=True)

@dp.callback_query(F.data.startswith("select_row:"))
async def cb_select_row(callback: types.CallbackQuery):
    await callback.answer()
    
    parts = callback.data.split(":")
    event_id = int(parts[1])
    row_number = int(parts[2])
    
    from ..database import get_event_by_id, get_event_seats
    event = await get_event_by_id(event_id)
    seats = await get_event_seats(event_id)
    
    # Get seats for this row
    row_seats = [s for s in seats if s['row_number'] == row_number and s['is_available']]
    
    if not row_seats:
        await callback.answer("В этом ряду нет свободных мест", show_alert=True)
        return
    
    text = (
        f"<b>{event['title']}</b>\n"
        f"Ряд {row_number} - выберите место:\n\n"
        f"Цена за место в этом ряду: <b>{row_seats[0]['price']}</b> ₽\n\n"
        f"<i>Доступно мест: {len(row_seats)}</i>"
    )
    
    # Create seat selection keyboard
    keyboard_buttons = []
    for i in range(0, len(row_seats), 5):  # 5 seats per row
        seat_buttons = []
        for j in range(5):
            if i + j < len(row_seats):
                seat = row_seats[i + j]
                seat_buttons.append(InlineKeyboardButton(
                    text=f"Место {seat['seat_number']}",
                    callback_data=f"book_seat:{event_id}:{row_number}:{seat['seat_number']}"
                ))
        if seat_buttons:
            keyboard_buttons.append(seat_buttons)
    
    keyboard_buttons.append([InlineKeyboardButton(text="Выбрать другой ряд", callback_data=f"select_seats:{event_id}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Universal message editing approach for select_row
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("book_seat:"))
async def cb_book_seat(callback: types.CallbackQuery):
    await callback.answer()
    
    parts = callback.data.split(":")
    event_id = int(parts[1])
    row_number = int(parts[2])
    seat_number = int(parts[3])
    user_id = callback.from_user.id
    
    from ..database import reserve_seat, get_event_by_id
    
    # Try to reserve the seat
    success = await reserve_seat(event_id, row_number, seat_number, user_id)
    
    if success:
        event = await get_event_by_id(event_id)
        
        # Get seat price
        from ..database import get_event_seats
        seats = await get_event_seats(event_id)
        seat_price = None
        for seat in seats:
            if seat['row_number'] == row_number and seat['seat_number'] == seat_number:
                seat_price = seat['price']
                break
        
        text = (
            f"<b>✅ Место забронировано!</b>\n\n"
            f"<b>Событие:</b> {event['title']}\n"
            f"<b>Место:</b> Ряд {row_number}, Место {seat_number}\n"
            f"<b>Цена:</b> {seat_price} ₽\n\n"
            f"<i>Бронь действительна 15 минут.\n"
            f"Для оплаты обратитесь к администратору.</i>"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Забронировать еще", callback_data=f"select_seats:{event_id}")],
            [InlineKeyboardButton(text="К списку событий", callback_data="events_list")]
        ])
        
    else:
        text = (
            f"<b>Место уже занято</b>\n\n"
            f"К сожалению, это место уже забронировано.\n"
            f"Выберите другое место."
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Выбрать другое место", callback_data=f"select_row:{event_id}:{row_number}")],
            [InlineKeyboardButton(text="К списку событий", callback_data="events_list")]
        ])
    
    # Universal message editing approach for book_seat
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)
@dp.callback_query(F.data == "manage_events")
async def cb_manage_events(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    # Get all system events to show management options
    from ..database import get_all_events, is_event_hidden_by_referrer
    all_events = await get_all_events()
    system_events = [e for e in all_events if e['is_system']]
    
    if not system_events:
        text = "<b>Управление событиями</b>\n\n<i>Нет системных событий для управления.</i>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="events_list")]
        ])
    else:
        text = (
            "<b>Управление событиями</b>\n\n"
            "<i>Вы можете скрыть системные события от ваших рефералов.\n"
            "Скрытые события не будут отображаться у ваших рефералов.</i>\n\n"
            "Выберите событие для управления:"
        )
        
        keyboard_buttons = []
        for event in system_events[:8]:  # Show max 8 events
            from datetime import datetime
            try:
                dt = datetime.strptime(event['date_time'], "%Y-%m-%d %H:%M")
                date_str = dt.strftime("%d.%m")
            except:
                date_str = "Дата"
            
            # Check if event is hidden
            is_hidden = await is_event_hidden_by_referrer(event['id'], user_id)
            status = "Скрыто" if is_hidden else "Показано"
            
            button_text = f"[{status}] {event['title']} ({date_str})"
            keyboard_buttons.append([InlineKeyboardButton(
                text=button_text, 
                callback_data=f"toggle_event:{event['id']}"
            )])
        
        keyboard_buttons.append([InlineKeyboardButton(text="К списку событий", callback_data="events_list")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Universal message editing approach for manage_events
    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            try:
                await callback.message.delete()
            except:
                pass
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("toggle_event:"))
async def cb_toggle_event(callback: types.CallbackQuery):
    await callback.answer()
    
    event_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    from ..database import is_event_hidden_by_referrer, hide_event_for_referrals, unhide_event_for_referrals, get_event_by_id
    
    event = await get_event_by_id(event_id)
    if not event:
        await callback.answer("Событие не найдено", show_alert=True)
        return
    
    is_hidden = await is_event_hidden_by_referrer(event_id, user_id)
    
    if is_hidden:
        # Unhide event
        await unhide_event_for_referrals(event_id, user_id)
        action_text = "показано"
    else:
        # Hide event
        await hide_event_for_referrals(event_id, user_id)
        action_text = "скрыто"
    
    await callback.answer(f"Событие '{event['title']}' {action_text} для ваших рефералов", show_alert=True)
    
    # Refresh the management menu
    await cb_manage_events(callback)