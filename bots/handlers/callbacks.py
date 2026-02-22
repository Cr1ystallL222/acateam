from aiogram import types, F

from aiogram.fsm.context import FSMContext

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from aiogram.exceptions import TelegramBadRequest

from datetime import datetime, timedelta, timezone

from data.db import db as shared_db



from ..loader import bot, dp

from ..config import SITE_URL, ADMIN_IDS, logger, PROFITS_CHANNEL_ID, WORKERS_CHAT_ID, SYSTEM_CHAT_ID

from ..utils import format_cooldown_remaining, is_cooldown_active
from ..services.logger_service import log_action

from ..database import get_or_create_bot_user, get_or_create_referral, get_application_approval_data, approve_application, reject_application, add_manual_profit, db

from ..renderers import (

    render_settings_menu,

    render_profile_menu,

    render_events_menu,

    render_links_management_menu,

    render_theatre_menu,

    render_clients_menu

)

from ..keyboards import get_about_keyboard, get_about_back_keyboard



@dp.callback_query(F.data == "menu_admin")

async def cb_menu_admin(callback: types.CallbackQuery):

    if callback.from_user.id in ADMIN_IDS:

        await callback.answer("Админ панель скоро будет добавлена", show_alert=True)

    else:

        await callback.answer("Доступ запрещен", show_alert=True)



@dp.callback_query(F.data.startswith("menu_theatre"))

async def cb_menu_theatre(callback: types.CallbackQuery):

    """Open links management menu instead of direct theatre menu."""

    await callback.answer()

    

    # Check if we need to return to specific link

    parts = callback.data.split(":")

    link_id = int(parts[1]) if len(parts) > 1 else None

    

    msg_id = callback.message.message_id

    

    if link_id:

        await render_theatre_menu(callback.message.chat.id, callback.from_user.id, msg_id, link_id=link_id)

    else:

        await render_links_management_menu(callback.message.chat.id, callback.from_user.id, msg_id)





@dp.callback_query(F.data.startswith("select_link:"))

async def cb_select_link(callback: types.CallbackQuery):

    """Select a specific link and open Theatre menu with it."""

    await callback.answer()

    

    parts = callback.data.split(":")

    if len(parts) > 1 and parts[1]:

        link_id = int(parts[1])

        msg_id = callback.message.message_id

        await render_theatre_menu(callback.message.chat.id, callback.from_user.id, msg_id, link_id=link_id)

    else:

        # Fallback to links menu if no id

        await render_links_management_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id)





@dp.callback_query(F.data == "create_link")

async def cb_create_link(callback: types.CallbackQuery, state: FSMContext):

    """Start link creation flow."""

    await callback.answer()

    

    from .fsm import TheatreLinkCreation

    

    text = (

        "🔗 <b>Создание ссылки</b>\n\n"

        "Введите название ссылки:\n\n"

        "<i>Название ссылки ни на что не влияет, просто для удобства.</i>"

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
    """Render cinema links management menu."""
    from ..renderers import render_cinema_links_management_menu
    await render_cinema_links_management_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id)
    await callback.answer()

@dp.callback_query(F.data == "create_link_cinema")
async def cb_create_link_cinema(callback: types.CallbackQuery, state: FSMContext):
    """Start cinema link creation flow."""
    from .fsm import CinemaLinkCreation
    await callback.message.answer("📝 Введите название для новой ссылки кино:")
    await state.set_state(CinemaLinkCreation.waiting_link_name)
    await callback.answer()

@dp.callback_query(F.data.startswith("select_link_cinema:"))
async def cb_select_link_cinema(callback: types.CallbackQuery):
    """Select a specific cinema link to manage."""
    from ..renderers import render_cinema_menu
    link_id = int(callback.data.split(":")[1])
    await render_cinema_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id, link_id=link_id)
    await callback.answer()

@dp.callback_query(F.data == "menu_back_links_cinema")
async def cb_menu_back_links_cinema(callback: types.CallbackQuery):
    """Back to cinema links management."""
    from ..renderers import render_cinema_links_management_menu
    await render_cinema_links_management_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id)
    await callback.answer()

@dp.callback_query(F.data.startswith("menu_settings_cinema"))
async def cb_menu_settings_cinema(callback: types.CallbackQuery):
    """Render cinema settings menu."""
    from ..renderers import render_settings_menu_cinema
    link_id = None
    if ":" in callback.data:
        link_id = int(callback.data.split(":")[1])
    
    await render_settings_menu_cinema(callback.message.chat.id, callback.from_user.id, callback.message.message_id, link_id=link_id)
    await callback.answer()

@dp.callback_query(F.data.startswith("settings_min_price_cinema"))
@dp.callback_query(F.data.startswith("settings_max_price_cinema"))
@dp.callback_query(F.data.startswith("settings_city_cinema"))
async def cb_cinema_settings_edit(callback: types.CallbackQuery, state: FSMContext):
    """Start editing a cinema setting."""
    data = callback.data
    parts = data.split(":")
    link_id = int(parts[1]) if len(parts) > 1 else None
    
    from ..database import get_worker_settings, get_cinema_link_by_id
    from .fsm import SettingsMaxPrice, SettingsCity
    
    await state.update_data(link_id=link_id, type='cinema')
    
    current = None
    if "min_price" in data:
        if link_id:
            link = await get_cinema_link_by_id(link_id)
            current = link.get('min_price_override') if link else None
        else:
            settings = await get_worker_settings(callback.from_user.id)
            current = settings.get('min_price_override')
        
        current_text = f"Текущее значение: {current}₽" if current else "Текущее значение: не установлено"
        await callback.message.answer(f"💰 Введите минимальную цену для <b>Кино</b>:\n\n{current_text}", parse_mode="HTML")
        await state.set_state(SettingsMaxPrice.waiting_max_price) # Reuse same state but with type='cinema' in data
        await state.update_data(setting='min_price_override')
    elif "max_price" in data:
        if link_id:
            link = await get_cinema_link_by_id(link_id)
            current = link.get('max_price_override') if link else None
        else:
            settings = await get_worker_settings(callback.from_user.id)
            current = settings.get('max_price_override')
        
        current_text = f"Текущее значение: {current}₽" if current else "Текущее значение: не установлено"
        await callback.message.answer(f"💎 Введите максимальную цену для <b>Кино</b>:\n\n{current_text}", parse_mode="HTML")
        await state.set_state(SettingsMaxPrice.waiting_max_price)
        await state.update_data(setting='max_price_override')
    else: # city
        if link_id:
            link = await get_cinema_link_by_id(link_id)
            current = link.get('custom_city') if link else None
        else:
            settings = await get_worker_settings(callback.from_user.id)
            current = settings.get('custom_city')
            
        current_text = f"Текущий город: {current}" if current else "Текущий город: не указан"
        await callback.message.answer(f"🏙️ Введите город для <b>Кино</b>:\n\n{current_text}", parse_mode="HTML")
        await state.set_state(SettingsCity.waiting_city_name)
    
    await callback.answer()



@dp.callback_query(F.data == "menu_clients")
async def cb_menu_clients(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    await render_clients_menu(callback.message.chat.id, callback.from_user.id, msg_id, service="theatre")

@dp.callback_query(F.data == "menu_clients_cinema")
async def cb_menu_clients_cinema(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    from ..renderers import render_clients_menu
    await render_clients_menu(callback.message.chat.id, callback.from_user.id, msg_id, service="cinema")



@dp.callback_query(F.data.startswith("menu_settings"))

async def cb_menu_settings(callback: types.CallbackQuery):

    await callback.answer()

    

    parts = callback.data.split(":")

    link_id = int(parts[1]) if len(parts) > 1 else None

    

    msg_id = callback.message.message_id

    await render_settings_menu(callback.message.chat.id, callback.from_user.id, msg_id, link_id=link_id)



# ============================================================================

# Settings Handlers

# ============================================================================



@dp.callback_query(F.data.startswith("settings_min_price"))

async def cb_settings_min_price(callback: types.CallbackQuery):

    """Show min price options."""

    await callback.answer()

    

    parts = callback.data.split(":")

    link_id = int(parts[1]) if len(parts) > 1 else None

    

    from ..database import MIN_PRICE_OPTIONS, get_worker_settings, get_link_by_id

    

    if link_id:

        link = await get_link_by_id(link_id)

        current = link.get('min_price_override') if link else None

    else:

        settings = await get_worker_settings(callback.from_user.id)

        current = settings.get('min_price_override')

    

    text = (

        "<b>💰 Минимальная цена</b>\n\n"

        "Выберите минимальную цену для событий:\n\n"

    )

    

    if link_id:

        text += "<i>Эта цена будет применяться только для этой ссылки.</i>"

    else:

        text += "<i>Эта цена будет применяться\nко всем системным событиям\nдля ваших рефералов.</i>"

    

    keyboard_buttons = []

    suffix = f":{link_id}" if link_id else ""

    

    for price in MIN_PRICE_OPTIONS:

        mark = " ✓" if current == price else ""

        keyboard_buttons.append([InlineKeyboardButton(

            text=f"{price}₽{mark}",

            callback_data=f"set_min_price:{price}{suffix}"

        )])

    

    # Add "Reset" and "Back" buttons

    keyboard_buttons.append([InlineKeyboardButton(text="❌ Сбросить", callback_data=f"set_min_price:0{suffix}")])

    

    back_callback = f"menu_settings:{link_id}" if link_id else "menu_settings"

    keyboard_buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)])

    

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

    parts = callback.data.split(":")

    price = int(parts[1])

    link_id = int(parts[2]) if len(parts) > 2 else None

    

    from ..database import update_worker_setting, update_link_setting, MIN_PRICE_OPTIONS

    

    # Validate price

    if price == 0:

        val = None

        msg = "✅ Мин. цена сброшена"

    elif price in MIN_PRICE_OPTIONS:

        val = price

        msg = f"✅ Мин. цена установлена: {price}₽"

    else:

        await callback.answer("❌ Недопустимое значение", show_alert=True)

        return



    if link_id:

        await update_link_setting(link_id, 'min_price_override', val)

    else:

        await update_worker_setting(callback.from_user.id, 'min_price_override', val)

        

    await callback.answer(msg, show_alert=True)

    

    # Return to settings menu    

    await render_settings_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id, link_id=link_id)





@dp.callback_query(F.data.startswith("settings_max_price"))

async def cb_settings_max_price(callback: types.CallbackQuery, state: FSMContext):

    """Prompt user to enter max price."""

    await callback.answer()

    

    parts = callback.data.split(":")

    link_id = int(parts[1]) if len(parts) > 1 else None

    

    from ..database import get_worker_settings, get_link_by_id

    from .fsm import SettingsMaxPrice

    

    current = None

    if link_id:

        link = await get_link_by_id(link_id)

        current = link.get('max_price_override') if link else None

    else:

        settings = await get_worker_settings(callback.from_user.id)

        current = settings.get('max_price_override')

    

    current_text = f"Текущее значение: {current}₽" if current else "Текущее значение: не установлено"

    

    text = (

        "<b>💎 Максимальная цена</b>\n\n"

        f"{current_text}\n\n"

        "Введите максимальную цену за место (в рублях):\n\n"

    )

    

    if link_id:

        text += "<i>Это будет максимальная цена за место для этой ссылки.</i>"

    else:

        text += "<i>Это будет максимальная цена за место\nдля ваших рефералов.</i>"

    

    suffix = f":{link_id}" if link_id else ""

    back_callback = f"menu_settings:{link_id}" if link_id else "menu_settings"

    

    keyboard = InlineKeyboardMarkup(inline_keyboard=[

        [InlineKeyboardButton(text="❌ Сбросить", callback_data=f"reset_max_price{suffix}")],

        [InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)]

    ])

    

    try:

        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)

    except:

        try:

            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)

        except:

            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)

    

    await state.set_state(SettingsMaxPrice.waiting_max_price)

    # Convert link_id to int/str correctly for state data (keeping it None if None)

    await state.update_data(link_id=link_id)





@dp.callback_query(F.data.startswith("settings_sys_seats"))
async def cb_settings_sys_seats(callback: types.CallbackQuery, state: FSMContext):
    """Prompt user to enter system seats available amount."""
    await callback.answer()
    
    parts = callback.data.split(":")
    # Check if first part contains _cinema
    is_cinema = "_cinema" in parts[0]
    link_id = int(parts[1]) if len(parts) > 1 else None
    
    from ..database import get_worker_settings, get_link_by_id, get_cinema_link_by_id
    from .fsm import SettingsSeats
    
    current = None
    if link_id:
        if is_cinema:
            link = await get_cinema_link_by_id(link_id)
            current = link.get('system_seats_override') if link else None
        else:
            link = await get_link_by_id(link_id)
            current = link.get('system_seats_override') if link else None
    else:
        settings = await get_worker_settings(callback.from_user.id)
        if is_cinema:
             current = settings.get('cinema_system_seats_override')
        else:
             current = settings.get('system_seats_override')
    
    if current is not None:
        display_current = f"{abs(current)}%" if current < 0 else str(current)
        current_text = f"Текущее значение: {display_current}"
    else:
        current_text = "Текущее значение: АВТО"
    
    text = (
        "<b>💺 Доступность системных мест</b>\n\n"
        f"{current_text}\n\n"
        "Введите количество доступных мест (например, '10' или '50%'):\n\n"
    )
    
    if link_id:
        text += "<i>Это будет количество свободных мест для системных событий по этой ссылке.</i>"
    else:
        text += "<i>Это будет количество свободных мест для системных событий ваших рефералов.</i>"
    
    type_suffix = "_cinema" if is_cinema else ""
    suffix = f":{link_id}" if link_id else ""
    back_callback = f"menu_settings{type_suffix}:{link_id}" if link_id else f"menu_settings{type_suffix}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Сбросить (АВТО)", callback_data=f"reset_sys_seats{type_suffix}{suffix}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)]
    ])
    
    try:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)
    
    await state.set_state(SettingsSeats.waiting_sys_seats)
    await state.update_data(link_id=link_id, is_cinema=is_cinema)


@dp.callback_query(F.data.startswith("reset_sys_seats"))
async def cb_reset_sys_seats(callback: types.CallbackQuery, state: FSMContext):
    """Reset system seats to default (AUTO)."""
    parts = callback.data.split(":")
    is_cinema = "_cinema" in parts[0]
    link_id = int(parts[1]) if len(parts) > 1 else None

    from ..database import update_worker_setting, update_link_setting, update_cinema_link_setting
    
    if link_id:
        if is_cinema:
            await update_cinema_link_setting(link_id, 'system_seats_override', None)
        else:
            await update_link_setting(link_id, 'system_seats_override', None)
    else:
        field = 'cinema_system_seats_override' if is_cinema else 'system_seats_override'
        await update_worker_setting(callback.from_user.id, field, None)
        
    await callback.answer("✅ Доступность мест сброшена", show_alert=True)
    await state.clear()
    
    # Return to settings menu
    if is_cinema:
        from ..renderers import render_settings_menu_cinema
        await render_settings_menu_cinema(callback.message.chat.id, callback.from_user.id, callback.message.message_id, link_id=link_id)
    else:
        from ..renderers import render_settings_menu
        await render_settings_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id, link_id=link_id)


@dp.callback_query(F.data.startswith("reset_max_price"))

async def cb_reset_max_price(callback: types.CallbackQuery, state: FSMContext):

    """Reset max price to default."""

    parts = callback.data.split(":")

    link_id = int(parts[1]) if len(parts) > 1 else None



    from ..database import update_worker_setting, update_link_setting

    

    if link_id:

        await update_link_setting(link_id, 'max_price_override', None)

    else:

        await update_worker_setting(callback.from_user.id, 'max_price_override', None)

        

    await callback.answer("✅ Макс. цена сброшена", show_alert=True)

    await state.clear()

    

    # Return to settings menu    

    await render_settings_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id, link_id=link_id)





@dp.callback_query(F.data.startswith("settings_city"))

async def cb_settings_city(callback: types.CallbackQuery, state: FSMContext):

    """Show city selection / input prompt."""

    await callback.answer()

    

    parts = callback.data.split(":")

    link_id = int(parts[1]) if len(parts) > 1 else None

    

    from ..database import get_available_cities, get_worker_settings, get_link_by_id

    

    current_city = "Краснодар"

    if link_id:

        link = await get_link_by_id(link_id)

        if link and link.get('custom_city'):

             current_city = link.get('custom_city')

    else:

        settings = await get_worker_settings(callback.from_user.id)

        if settings.get('custom_city'):

            current_city = settings.get('custom_city')

    

    cities = await get_available_cities()

    

    text = (

        "<b>🏙️ Настройка города</b>\n\n"

        f"Текущий город: <b>{current_city}</b>\n\n"

        "Выберите город из списка или введите свой:\n\n"

        "<i>Город влияет на название афиши\nи места проведения событий.</i>"

    )

    

    suffix = f":{link_id}" if link_id else ""

    

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

                    callback_data=f"set_city:{city}{suffix}"

                ))

        keyboard_buttons.append(row)

    

    # Add "Enter custom" and "Back" buttons

    keyboard_buttons.append([InlineKeyboardButton(text="✏️ Ввести свой город", callback_data=f"enter_custom_city{suffix}")])

    

    back_callback = f"menu_settings:{link_id}" if link_id else "menu_settings"

    keyboard_buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)])

    

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

    # format: set_city:city_name:link_id or set_city:city_name

    parts = callback.data.split(":")

    city = parts[1]

    link_id = int(parts[2]) if len(parts) > 2 else None

    

    from ..database import update_worker_setting, update_link_setting

    

    if link_id:

        await update_link_setting(link_id, 'custom_city', city)

    else:

        await update_worker_setting(callback.from_user.id, 'custom_city', city)

        

    await callback.answer(f"✅ Город: {city}", show_alert=True)

    

    # Return to settings menu

    await render_settings_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id, link_id=link_id)





@dp.callback_query(F.data.startswith("enter_custom_city"))

async def cb_enter_custom_city(callback: types.CallbackQuery, state: FSMContext):

    """Prompt user to enter custom city name."""

    await callback.answer()

    

    parts = callback.data.split(":")

    link_id = int(parts[1]) if len(parts) > 1 else None

    

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

    await state.update_data(link_id=link_id)



# End of Settings Handlers

# ============================================================================



@dp.callback_query(F.data == "menu_events")
async def cb_menu_events(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    await render_events_menu(callback.message.chat.id, callback.from_user.id, msg_id, event_type='theatre')

@dp.callback_query(F.data == "menu_events_cinema")
async def cb_menu_events_cinema(callback: types.CallbackQuery):
    await callback.answer()
    msg_id = callback.message.message_id
    await render_events_menu(callback.message.chat.id, callback.from_user.id, msg_id, event_type='cinema')



@dp.callback_query(F.data == "events_list")
async def cb_events_list(callback: types.CallbackQuery):
    await cb_events_list_page(callback, 1, 'theatre')

@dp.callback_query(F.data == "events_list_cinema")
async def cb_events_list_cinema(callback: types.CallbackQuery):
    await cb_events_list_page(callback, 1, 'cinema')



@dp.callback_query(F.data.startswith("events_page:"))
async def cb_events_page(callback: types.CallbackQuery):
    # Format: events_page:page OR events_page:type:page
    parts = callback.data.split(":")
    if len(parts) == 3:
        event_type = parts[1]
        page = int(parts[2])
    else:
        event_type = 'theatre'
        page = int(parts[1])

    await cb_events_list_page(callback, page, event_type)


async def cb_events_list_page(callback: types.CallbackQuery, page: int, event_type: str = 'theatre'):
    await callback.answer()
    msg_id = callback.message.message_id
    user_id = callback.from_user.id
    
    # Get database events ONLY - no more hardcoded static events
    from ..database import get_worker_events
    all_events = await get_worker_events(user_id, event_type)
    
    # Pagination settings
    events_per_page = 10
    total_events = len(all_events)
    total_pages = (total_events + events_per_page - 1) // events_per_page  # Ceiling division
    
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    start_idx = (page - 1) * events_per_page
    end_idx = start_idx + events_per_page
    page_events = all_events[start_idx:end_idx]
    
    back_callback = "menu_events_cinema" if event_type == "cinema" else "menu_events"

    if not all_events:
        text = "<b>Список событий</b>\n\n<i>Пока нет доступных событий.</i>"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data=back_callback)]
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
                ev_type_prefix = ""  # No prefix for system events
            elif event.get('created_by') == user_id:
                ev_type_prefix = "Ваше "
            else:
                ev_type_prefix = "Реферальное "
            
            button_text = f"{ev_type_prefix}{event['title']} ({date_str})"
            
            # Use event ID directly (no more static_ prefix)
            event_id = event['id']
            keyboard_buttons.append([InlineKeyboardButton(
                text=button_text, 
                callback_data=f"view_event:{event_id}"
            )])
        
        # Pagination buttons
        pagination_buttons = []
        if page > 1:
            pagination_buttons.append(InlineKeyboardButton(text="⬅️ Пред.", callback_data=f"events_page:{event_type}:{page-1}"))
        if page < total_pages:
            pagination_buttons.append(InlineKeyboardButton(text="След. ➡️", callback_data=f"events_page:{event_type}:{page+1}"))
        
        if pagination_buttons:
            keyboard_buttons.append(pagination_buttons)
        
        keyboard_buttons.append([InlineKeyboardButton(text="Назад", callback_data=back_callback)])
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

    

    if is_creator or event.get('is_system', True):

        keyboard_buttons.append([InlineKeyboardButton(

            text="Отред. ✏️" if event.get('is_system') else "Редактировать",

            callback_data=f"edit_event:{event_id}"

        )])

    

    # Back button
    back_callback = "events_list_cinema" if event.get('type') == 'cinema' else "events_list"
    keyboard_buttons.append([InlineKeyboardButton(
        text="Назад",
        callback_data=back_callback
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





@dp.callback_query(F.data.in_({"events_add", "events_add_cinema"}))
async def cb_events_add(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    is_cinema = callback.data == 'events_add_cinema'
    entity = "фильма" if is_cinema else "спектакля"
    example = "Дюна, Властелин колец" if is_cinema else "Гамлет, Ромео и Джульетта, Концерт классической музыки"

    text = (
        "<b>Создание события</b>\n\n"
        "Давайте создадим новое событие!\n\n"
        "<b>Название события</b>\n\n"
        f"Введите название {entity}:\n\n"
        f"<i>Например: {example}</i>"
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
    
    event_type = 'cinema' if callback.data == 'events_add_cinema' else 'theatre'
    await state.update_data(event_type=event_type)



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

    

    bot_user = await shared_db.fetchone("SELECT * FROM bot_users WHERE telegram_user_id = ?", (user_id,))

    

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

    

    # Get user_id from telegram_user_id

    row = await shared_db.fetchone("SELECT id FROM users WHERE telegram_user_id = ?", (user_id,))

    if not row:

        await callback.message.answer("❌ Пользователь не найден")

        return

    referrer_user_id = row['id']

    

    # Get mamont details

    mamont = await shared_db.fetchone("""

        SELECT * FROM mamonts 

        WHERE mamont_id = ? AND referrer_user_id = ?

    """, (mamont_id, referrer_user_id))

    

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

    

    from ..database import get_event_by_id, get_worker_settings, apply_event_override

    event = await get_event_by_id(event_id)

    settings = await get_worker_settings(callback.from_user.id)

    city = settings.get('custom_city', 'Краснодар')

    

    if not event:

        await callback.message.answer("Событие не найдено")

        return

    

    # Apply overrides for display
    display_event = await apply_event_override(event, callback.from_user.id)
    is_sys = event.get('is_system')
    sys_label = " (системное)" if is_sys else ""

    text = (

        f"<b>Редактирование события{sys_label} ⚙️</b>\n\n"

        f"<b>Название:</b> {display_event['title']}\n"

        f"<b>Дата:</b> {display_event['date_time']}\n"

        f"<b>Место:</b> {display_event['venue']}\n"

        f"<b>Цены:</b> {display_event['min_price']} - {display_event['max_price']} ₽\n\n"

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

        [

            InlineKeyboardButton(text="Доступность мест", callback_data=f"edit_event_availability:{event_id}"),

            InlineKeyboardButton(text="🖼 Фото", callback_data=f"edit_event_photo:{event_id}")

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


@dp.callback_query(F.data.startswith("edit_event_photo:"))

async def cb_edit_photo(callback: types.CallbackQuery, state: FSMContext):

    await callback.answer()

    event_id = int(callback.data.split(":")[1])

    

    from ..handlers.fsm import EventEdit

    await state.set_state(EventEdit.waiting_photo)

    await state.update_data(event_id=event_id)

    

    await callback.message.answer(

        "<b>Изменение фото</b>\n\n"

        "Отправьте новое фото для события:",

        parse_mode="HTML",

        reply_markup=InlineKeyboardMarkup(inline_keyboard=[

            [InlineKeyboardButton(text="Отмена", callback_data=f"edit_event:{event_id}")]

        ])

    )



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

    venues = await get_venues_for_city(city)

    

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

    from ..database import get_worker_events, is_event_hidden_by_referrer

    all_events = await get_worker_events(user_id)

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



# ============================================================================

# Event Availability Handlers

# ============================================================================



@dp.callback_query(F.data.startswith("edit_event_availability:"))

async def cb_edit_availability(callback: types.CallbackQuery):

    await callback.answer()

    

    event_id = int(callback.data.split(":")[1])

    

    from ..database import get_event_seats_stats, get_event_by_id

    event = await get_event_by_id(event_id)

    stats = await get_event_seats_stats(event_id)

    

    if not event:

        await callback.message.answer("Событие не найдено")

        return

        

    total = stats['total']

    free = stats['free']

    occupied = total - free

    percent_free = int((free / total * 100)) if total > 0 else 0

    

    text = (

        f"<b>Доступность мест</b>\n\n"

        f"Событие: <b>{event['title']}</b>\n\n"

        f"Всего мест: <b>{total}</b>\n"

        f"Занято: <b>{occupied}</b>\n"

        f"Свободно: <b>{free}</b> ({percent_free}%)\n"

        f"<i>Выберите способ изменения доступности:</i>"

    )

    

    keyboard = InlineKeyboardMarkup(inline_keyboard=[

        [

            InlineKeyboardButton(text="Установить % свободных", callback_data=f"set_avail_pct:{event_id}"),

            InlineKeyboardButton(text="Установить кол-во свободных", callback_data=f"set_avail_num:{event_id}")

        ],

        [InlineKeyboardButton(text="Назад к редактированию", callback_data=f"edit_event:{event_id}")]

    ])

    

    try:

        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)

    except:

        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)



@dp.callback_query(F.data.startswith("set_avail_pct:"))

async def cb_set_avail_pct(callback: types.CallbackQuery, state: FSMContext):

    await callback.answer()

    event_id = int(callback.data.split(":")[1])

    

    from ..handlers.fsm import EventAvailability

    await state.set_state(EventAvailability.waiting_percent)

    await state.update_data(event_id=event_id)

    

    await callback.message.answer(

        "<b>Установка % свободных мест</b>\n\n"

        "Введите процент свободных мест (0-100):\n"

        "<i>Случайным образом будут освобождены или заняты места.</i>",

        parse_mode="HTML",

        reply_markup=InlineKeyboardMarkup(inline_keyboard=[

            [InlineKeyboardButton(text="Отмена", callback_data=f"edit_event_availability:{event_id}")]

        ])

    )



@dp.callback_query(F.data.startswith("set_avail_num:"))

async def cb_set_avail_num(callback: types.CallbackQuery, state: FSMContext):

    await callback.answer()

    event_id = int(callback.data.split(":")[1])

    

    from ..handlers.fsm import EventAvailability

    await state.set_state(EventAvailability.waiting_number)

    await state.update_data(event_id=event_id)

    

    await callback.message.answer(

        "<b>Установка количества свободных мест</b>\n\n"

        "Введите точное количество свободных мест:\n"

        "<i>Случайным образом будут освобождены или заняты места.</i>",

        parse_mode="HTML",

        reply_markup=InlineKeyboardMarkup(inline_keyboard=[

            [InlineKeyboardButton(text="Отмена", callback_data=f"edit_event_availability:{event_id}")]

        ])

    )



@dp.callback_query(F.data == "profit_confirm")

async def cb_profit_confirm(callback: types.CallbackQuery, state: FSMContext):

    data = await state.get_data()

    worker_id = data.get('worker_id')

    amount = data.get('amount')

    preview_text = data.get('preview_text')

    worker_share = data.get('worker_share')

    note = data.get('note')



    if not worker_id or not amount:

        await callback.answer("❌ Ошибка данных", show_alert=True)

        return

        

    if not worker_share:

        worker_share = int(amount * 0.78)



    # Save to DB

    await add_manual_profit(callback.from_user.id, worker_id, amount, worker_share, note)



    # Image

    from pathlib import Path

    image_path = Path(__file__).parent.parent / "images" / "profit_image.jpg"

    photo = FSInputFile(image_path) if image_path.exists() else None



    # Send to workers chat

    if WORKERS_CHAT_ID:

        try:

            target_id = int(WORKERS_CHAT_ID)

            if photo:

                # Need to reopen photo or reuse? FSInputFile can be reused? 

                # Better create new instance to be safe

                photo_work = FSInputFile(image_path)

                await bot.send_photo(target_id, photo_work, caption=preview_text, parse_mode="HTML")

            else:

                await bot.send_message(target_id, preview_text, parse_mode="HTML")

        except Exception as e:

            logger.error(f"Failed to send to workers chat: {e}")



    # Send to profits channel

    if PROFITS_CHANNEL_ID:

        try:

            target_id = int(PROFITS_CHANNEL_ID)

            if photo:

                photo_chan = FSInputFile(image_path)

                await bot.send_photo(target_id, photo_chan, caption=preview_text, parse_mode="HTML")

            else:

                await bot.send_message(target_id, preview_text, parse_mode="HTML")

        except Exception as e:

            logger.error(f"Failed to send to profits channel: {e}")



    await callback.answer("✅ Отправлено")
    
    # Edit original message with success status and admin info
    admin_name = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name
    worker_name = data.get('worker_name')
    
    new_text = (
        "✅ <b>Профит зачислен</b>\n"
        f"└ {note}\n\n"
        f"💳 <b>Сумма:</b> {amount} ₽\n"
        f"  └ Доля воркера: {worker_share} ₽\n"
        f"👤 <b>Работник:</b> {worker_name}\n\n"
        f"<i>Отрисовал {admin_name}</i>"
    )

    try:
        await callback.message.edit_caption(caption=new_text, parse_mode="HTML", reply_markup=None)
    except:
        try:
            await callback.message.edit_text(text=new_text, parse_mode="HTML", reply_markup=None)
        except Exception as e:
            logger.error(f"Failed to edit profit message: {e}")

    # Log action to logs chat
    log_msg = (
        f"PROFIT CONFIRMED request by {admin_name}\n"
        f"Worker: {worker_name} ({worker_id})\n"
        f"Amount: {amount} RUB\n"
        f"Note: {note}"
    )
    # Using ACTION or SUCCESS level
    await log_action(log_msg, "SUCCESS")
    
    await state.clear()



@dp.callback_query(F.data == "profit_cancel")

async def cb_profit_cancel(callback: types.CallbackQuery, state: FSMContext):

    await callback.answer("❌ Отменено")

    try:

        await callback.message.delete()

    except:

        pass

    await state.clear()



# Withdrawal handlers

@dp.callback_query(F.data == "menu_withdraw")

async def cb_withdraw_request(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    

    # Get user balance

    user = await get_or_create_bot_user(user_id, None, None, None)

    balance = user.get('balance', 0)

    

    if balance <= 0:

        await callback.answer("Сумма для вывода должна быть больше 0", show_alert=True)

        return

        

    # Confirmation dialog

    text = (

        f"💳 <b>Вывод средств</b>\n\n"

        f"Сумма к выводу: <b>{balance} RUB</b>\n"

        f"Вы уверены, что хотите вывести средства?"

    )

    

    keyboard = InlineKeyboardMarkup(inline_keyboard=[

        [

            InlineKeyboardButton(text="Да, вывести", callback_data=f"withdraw_confirm:{balance}"),

            InlineKeyboardButton(text="Отмена", callback_data="withdraw_cancel_user")

        ]

    ])

    

    try:

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

    except TelegramBadRequest:

        # Message has media, so we can't edit text. 

        # We could edit caption, but let's delete and send new text for clear dialog.

        try:

            await callback.message.delete()

        except:

            pass

        await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)



@dp.callback_query(F.data == "withdraw_cancel_user")

async def cb_withdraw_cancel_user(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    user = await get_or_create_bot_user(user_id, None, None, None)

    await render_profile_menu(callback.message.chat.id, user_id, user, callback.message.message_id)



@dp.callback_query(F.data.startswith("withdraw_confirm:"))

async def cb_withdraw_confirm(callback: types.CallbackQuery):

    user_id = callback.from_user.id

    amount = int(callback.data.split(":")[1])

    

    # Re-check balance (race condition check)

    user = await get_or_create_bot_user(user_id, None, None, None)

    current_balance = user.get('balance', 0)

    

    if current_balance < amount:

        await callback.answer("❌ Недостаточно средств", show_alert=True)

        await render_profile_menu(callback.message.chat.id, user_id, user, callback.message.message_id)

        return



    # Deduct balance and add to hold

    # We update manually to ensure transaction safety-ish

    await db.execute("""

        UPDATE bot_users 

        SET balance = balance - ?, balance_hold = balance_hold + ? 

        WHERE telegram_user_id = ?

    """, (amount, amount, user_id))

    

    # Sync global users

    # users table usually matches bot_users. Let's update it too just in case?

    # Actually users.balance is typically profit_sum or real balance? 

    # Current implementation in database.py add_manual_profit updates users.balance too.

    # So we should deduct there too.

    # But wait, balance_hold is only in bot_users (I added it there).

    # So users.balance will decrease, but users.balance_hold doesn't exist.

    # That's fine, users table is for global auth. bot_users is for this bot.

    # Sync:

    await db.execute("""

        UPDATE users SET balance = balance - ? WHERE telegram_user_id = ?

    """, (amount, user_id))

    

    # Create withdrawal request

    await db.execute("""

        INSERT INTO withdrawal_requests (user_id, amount, status)

        VALUES ((SELECT id FROM users WHERE telegram_user_id = ?), ?, 'pending')

    """, (user_id, amount))

    

    # Get request ID

    row = await db.fetchone("SELECT last_insert_rowid() as id" if db.mode == 'sqlite' else "SELECT LASTVAL() as id") 

    # Note: asyncpg/sqlite handling might differ for last id.

    # But let's assume one of standard ways or fetch by user/latest.

    # Safer: fetch by user/created_at

    req_row = await db.fetchone("""

        SELECT id FROM withdrawal_requests 

        WHERE user_id = (SELECT id FROM users WHERE telegram_user_id = ?) 

        ORDER BY id DESC LIMIT 1

    """, (user_id,))

    req_id = req_row['id']

    

    # Notify System Chat

    if SYSTEM_CHAT_ID:

        full_name = user.get('full_name') or "User"

        username = user.get('username') or "no_user"

        

        # Escape HTML if needed, but for now just use simple strings

        worker_info = f"<a href='tg://user?id={user_id}'>{full_name}</a> (@{username})"

        msg_text = (

            f"Воркер {worker_info} ({user_id}) хочет вывести свой баланс\n\n"

            f"Сумма: {amount} RUB\n\n"

            f"<i>Чтобы подтвердить вывод, ответьте на это сообщение ссылкой с чеком на сумму вывода.</i>"

        )

        markup = InlineKeyboardMarkup(inline_keyboard=[

            [InlineKeyboardButton(text="Отклонить", callback_data=f"withdraw_reject:{req_id}")]

        ])

        

        try:

            sent_msg = await bot.send_message(SYSTEM_CHAT_ID, msg_text, parse_mode="HTML", reply_markup=markup)

            

            # Save group_message_id to request

            await db.execute("UPDATE withdrawal_requests SET group_message_id = ? WHERE id = ?", (sent_msg.message_id, req_id))

            

        except Exception as e:

            logger.error(f"Failed to send to system chat: {e}")

            # Refund? No, just log. Admin can fix.

            pass

            

    await callback.answer("✅ Заявка на вывод создана", show_alert=True)

    

    # Refresh profile

    user = await get_or_create_bot_user(user_id, None, None, None)

    await render_profile_menu(callback.message.chat.id, user_id, user, callback.message.message_id)



@dp.callback_query(F.data.startswith("withdraw_reject:"))

async def cb_withdraw_reject(callback: types.CallbackQuery):

    # Admin rejects

    # Check admin? Ideally yes, but if msg is in SYSTEM_CHAT...

    # SYSTEM_CHAT members are admins effectively.

    

    req_id = int(callback.data.split(":")[1])

    

    # Get request

    req = await db.fetchone("SELECT * FROM withdrawal_requests WHERE id = ?", (req_id,))

    if not req or req['status'] != 'pending':

        await callback.answer("Заявка уже обработана", show_alert=True)

        return

        

    amount = req['amount']

    # Get worker telegram id

    user_row = await db.fetchone("SELECT telegram_user_id FROM users WHERE id = ?", (req['user_id'],))

    worker_tg_id = user_row['telegram_user_id']

    

    # Refund funds

    await db.execute("""

        UPDATE bot_users 

        SET balance = balance + ?, balance_hold = balance_hold - ? 

        WHERE telegram_user_id = ?

    """, (amount, amount, worker_tg_id))

    

    await db.execute("""

        UPDATE users SET balance = balance + ? WHERE telegram_user_id = ?

    """, (amount, worker_tg_id))

    

    # Update status

    await db.execute("UPDATE withdrawal_requests SET status = 'rejected' WHERE id = ?", (req_id,))

    

    # Update admin message

    await callback.message.edit_text(f"{callback.message.text}\n\n❌ <b>Отклонено</b>", parse_mode="HTML")

    

    # Notify worker

    try:

        await bot.send_message(worker_tg_id, f"❌ Ваша заявка на вывод {amount} RUB была отклонена.")

    except:

        pass

    try:

        await callback.message.delete()

    except:

        pass

    await state.clear()

# ============================================================================
# About Project Handlers
# ============================================================================

@dp.callback_query(F.data == "menu_about")
async def cb_menu_about(callback: types.CallbackQuery):
    "Show About Project menu."
    from ..keyboards import get_about_keyboard
    
    text = (
        "<b>О проекте ACA Team</b>\n\n"
        "Мы — команда профессионалов, занимающаяся арбитражем трафика и монетизацией.\n"
        "Наш проект существует уже более года и объединяет лучших специалистов в этой области.\n\n"
        "Выберите раздел ниже:"
    )
    
    keyboard = get_about_keyboard()
    
    try:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)
    
@dp.callback_query(F.data == "about_curators")
async def cb_about_curators(callback: types.CallbackQuery):
    "Show curators list."
    from ..keyboards import get_about_back_keyboard
    
    text = (
        "<b>Кураторы проекта:</b>\n\n"
        "1. @afonac3\n"
        "2. @c6rr7\n"
        "3. @asfkolfgw\n\n"
        "<i>По всем вопросам обращайтесь к ним.</i>"
    )
    
    keyboard = get_about_back_keyboard()
    
    try:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)
    
@dp.callback_query(F.data == "about_manuals")
async def cb_about_manuals(callback: types.CallbackQuery):
    "Show manuals list."
    from ..keyboards import get_about_back_keyboard
    from ..config import THEATRE_GUIDE_URL
    
    text = (
        "<b>Мануалы и инструкции:</b>\n\n"
        f"1. <a href='{THEATRE_GUIDE_URL}'>Инструкция к боту</a>\n\n"
        "<i>Больше мануалов скоро появится!</i>"
    )
    
    keyboard = get_about_back_keyboard()
    
    try:
        await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await callback.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query(F.data == "about_chat")
async def cb_about_chat(callback: types.CallbackQuery):
    """Generate invite link for workers chat with rate limiting."""
    from ..config import WORKERS_CHAT_ID
    from ..keyboards import get_about_keyboard
    from ..database import update_bot_user_invite_link
    from data.db import db
    from datetime import datetime, timedelta
    
    # Check if WORKERS_CHAT_ID is set
    if not WORKERS_CHAT_ID:
        await callback.answer("Чат воркеров не настроен", show_alert=True)
        return

    try:
        chat_id = int(WORKERS_CHAT_ID)
    except ValueError:
        await callback.answer("Некорректный ID чата", show_alert=True)
        return
        
    user_id = callback.from_user.id
    
    # Fetch user data to check for existing link
    user_data = await db.fetchone("SELECT last_invite_link, last_invite_created_at FROM bot_users WHERE telegram_user_id = ?", (user_id,))
    
    current_time = datetime.now()
    
    if user_data and user_data['last_invite_created_at']:
        # Parse timestamp (it might be string or datetime depending on DB adapter/mode)
        last_created = user_data['last_invite_created_at']
        if isinstance(last_created, str):
            try:
                last_created = datetime.fromisoformat(last_created)
            except ValueError:
                # If format is different, try generic parsing or ignore
                pass
        
        # Determine time diff
        if isinstance(last_created, datetime):
            time_diff = current_time - last_created
            minutes_diff = time_diff.total_seconds() / 60
            
            # 1. Existing link valid (created < 15 mins ago)
            if minutes_diff < 15:
                # Show existing link
                invite_link = user_data['last_invite_link']
                if invite_link:
                    keyboard = get_about_keyboard(chat_link=invite_link)
                    try:
                        await callback.message.edit_reply_markup(reply_markup=keyboard)
                    except:
                        pass
                    
                    await callback.answer(
                        "✅ У вас уже есть активная ссылка!\n"
                        "Ссылка действительна 15 минут с момента создания.\n"
                        "Нажмите кнопку чтобы перейти.",
                        show_alert=True
                    )
                    return

            # 2. Rate limit (created < 20 mins ago)
            if minutes_diff < 20:
                wait_time = int(20 - minutes_diff)
                await callback.answer(
                    f"⏳ Пожалуйста подождите {wait_time} мин.\n"
                    "Ссылку можно создавать раз в 20 минут.",
                    show_alert=True
                )
                return

    await callback.answer("Создаю ссылку...", show_alert=False)
    
    try:
        # Generate invite link
        # 1 use, 15 minutes expire
        expire_date = current_time + timedelta(minutes=15)
        invite_link_obj = await bot.create_chat_invite_link(
            chat_id=chat_id,
            name=f"Invite for {user_id}",
            expire_date=expire_date,
            member_limit=1
        )
        
        invite_link = invite_link_obj.invite_link
        
        # Save to DB
        await update_bot_user_invite_link(user_id, invite_link, current_time)
        
        # Show alert
        await callback.answer(
            "✅ Ссылка создана!\n\n"
            "• Активна 15 минут\n"
            "• На 1 переход\n"
            "Нажмите кнопку еще раз чтобы перейти.",
            show_alert=True
        )
        
        # Update keyboard with URL button
        keyboard = get_about_keyboard(chat_link=invite_link)
        
        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Failed to update keyboard with link: {e}")
            
    except Exception as e:
        logger.error(f"Failed to generate invite link: {e}")
        await callback.answer(
            "❌ Ошибка создания ссылки.\n"
            "Возможно бот не админ в чате.",
            show_alert=True
        )

# ============================================================================
# Coupon Callbacks
# ============================================================================

@dp.callback_query(F.data == "menu_coupons_cinema")
async def cb_menu_coupons_cinema(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    from ..renderers import render_coupons_menu
    await render_coupons_menu(callback.message.chat.id, callback.from_user.id, callback.message.message_id)

@dp.callback_query(F.data == "create_coupon")
async def cb_create_coupon(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    text = (
        "<b>➕ Создание купона</b>\n\n"
        "Выберите тип купона:\n\n"
        "• <b>Пополнение баланса</b> - мамонт получит указанную сумму на баланс сайта.\n"
        "• <b>Скидка</b> - мамонт получит скидку на покупку билетов (процент или сумму)."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Пополнение баланса", callback_data="coupon_set_type:balance")],
        [InlineKeyboardButton(text="🎟 Скидка на билеты", callback_data="coupon_set_type:discount")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_coupons_cinema")]
    ])
    
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except:
        try:
            await callback.message.edit_caption(caption=text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)

