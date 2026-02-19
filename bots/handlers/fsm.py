from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from ..config import APPLICATIONS_CHAT_ID, RESOLVED_IMAGE_PATH, logger
from ..database import create_application, update_application_confirm_msg, has_pending_application
from ..loader import bot, dp

# FSM States
class ApplicationForm(StatesGroup):
    waiting_q1 = State()
    waiting_q2 = State()

class EventCreation(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_photo = State()
    waiting_min_price = State()
    waiting_max_price = State()
    waiting_date_time = State()
    waiting_venue = State()

class SettingsCity(StatesGroup):
    waiting_city_name = State()

class SettingsMaxPrice(StatesGroup):
    waiting_max_price = State()

class EventEdit(StatesGroup):
    waiting_title = State()
    waiting_datetime = State()
    waiting_venue = State()
    waiting_description = State()
    waiting_min_price = State()
    waiting_max_price = State()

class TheatreLinkCreation(StatesGroup):
    waiting_link_name = State()

class CinemaLinkCreation(StatesGroup):
    waiting_link_name = State()

class EventAvailability(StatesGroup):
    waiting_percent = State()
    waiting_number = State()

class ProfitProcess(StatesGroup):
    confirm = State()

class SpamBroadcast(StatesGroup):
    waiting_message = State()
    preview = State()


@dp.callback_query(F.data == "continue")
async def cb_continue(callback: types.CallbackQuery, state: FSMContext):
    if await has_pending_application(callback.from_user.id):
        await callback.answer("Ваша заявка уже на рассмотрении!", show_alert=True)
        try:
            await callback.message.delete()
        except:
            pass
        return

    await callback.answer()
    
    data = await state.get_data()
    msg_id = data.get("welcome_msg_id")
    
    question_text = (
        "<b>Вопрос 1/2</b>\n\n"
        "Есть ли у вас опыт в данной сфере?\n\n"
        "<i>Напишите ваш ответ сообщением.</i>"
    )
    
    if msg_id:
        try:
            await callback.message.edit_caption(caption=question_text, parse_mode="HTML")
        except:
            await callback.message.answer(question_text, parse_mode="HTML")
    else:
        await callback.message.answer(question_text, parse_mode="HTML")
    
    await state.set_state(ApplicationForm.waiting_q1)

@dp.message(ApplicationForm.waiting_q1)
async def process_q1(message: types.Message, state: FSMContext):
    await state.update_data(q1_answer=message.text)
    
    await message.answer(
        "<b>Вопрос 2/2</b>\n\n"
        "Откуда узнали о нас?\n\n"
        "<i>Напишите ваш ответ сообщением.</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(ApplicationForm.waiting_q2)

@dp.message(ApplicationForm.waiting_q2)
async def process_q2(message: types.Message, state: FSMContext):
    data = await state.get_data()
    q1 = data.get("q1_answer", "")
    q2 = message.text
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or ""
    
    app_id = await create_application(user_id, q1, q2)
    
    logger.info(f"Application created: id={app_id}, telegram_user_id={user_id}")
    
    if APPLICATIONS_CHAT_ID:
        app_text = (
            f"<b>📨 Новая заявка #{app_id}</b>\n\n"
            f"<b>От:</b> {full_name}\n"
            f"<b>Username:</b> @{username if username else 'нет'}\n"
            f"<b>ID:</b> <code>{user_id}</code>\n\n"
            f"<b>Вопрос 1:</b> Есть ли у вас опыт?\n"
            f"<i>{q1}</i>\n\n"
            f"<b>Вопрос 2:</b> Откуда узнали о нас?\n"
            f"<i>{q2}</i>"
        )
        
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Принять", callback_data=f"approve:{user_id}:{app_id}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"reject:{user_id}:{app_id}")
            ]
        ])
        
        try:
            await bot.send_message(APPLICATIONS_CHAT_ID, app_text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            logger.error(f"Failed to send to applications chat: {e}")
    
    confirm_msg = await message.answer(
        "<b>✅ Заявка отправлена!</b>\n\n"
        "Ваша заявка принята на рассмотрение.\n"
        "Мы уведомим вас о решении в ближайшее время.\n\n"
        "<i>Обычно это занимает до 24 часов.</i>",
        parse_mode="HTML"
    )
    
    await update_application_confirm_msg(app_id, confirm_msg.message_id)
    
    await state.clear()

# ============================================================================
# Settings City Handler
# ============================================================================

@dp.message(SettingsCity.waiting_city_name)
async def process_city_name(message: types.Message, state: FSMContext):
    """Process custom city name input."""
    city_name = message.text.strip()
    
    if len(city_name) < 2:
        await message.answer(
            "❌ Название города слишком короткое.\nВведите корректное название:",
            parse_mode="HTML"
        )
        return
    
    if len(city_name) > 50:
        await message.answer(
            "❌ Название города слишком длинное.\nВведите корректное название:",
            parse_mode="HTML"
        )
        return
    
    from ..database import update_worker_setting, update_link_setting, update_cinema_link_setting, get_venues_for_city, CITY_VENUES
    
    data = await state.get_data()
    link_id = data.get('link_id')
    link_type = data.get('type', 'theatre')
    
    # Update the city
    if link_id:
        if link_type == 'cinema':
            await update_cinema_link_setting(link_id, 'custom_city', city_name)
        else:
            await update_link_setting(link_id, 'custom_city', city_name)
    else:
        setting_key = 'cinema_custom_city' if link_type == 'cinema' else 'custom_city'
        await update_worker_setting(message.from_user.id, setting_key, city_name)
    
    # Check if city has predefined venues
    if city_name in CITY_VENUES:
        venues_info = f"\n\n✅ Найдено {len(CITY_VENUES[city_name])} локаций для города {city_name}."
    else:
        venues_info = f"\n\n⚠️ Для города {city_name} место проведения не будет отображаться."
    
    # Show confirmation and go back to settings
    from ..renderers import render_settings_menu
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    back_callback = f"menu_settings{'_cinema' if link_type == 'cinema' else ''}:{link_id}" if link_id else f"menu_settings{'_cinema' if link_type == 'cinema' else ''}"
    
    await message.answer(
        f"✅ <b>Город установлен: {city_name}</b>{venues_info}\n\n"
        f"<i>Афиша будет отображаться как \"Афиша {city_name}\"</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ К настройкам", callback_data=back_callback)]
        ])
    )
    
    await state.clear()

# Max Price Input Handler
@dp.message(SettingsMaxPrice.waiting_max_price)
async def process_max_price(message: types.Message, state: FSMContext):
    """Process custom max price input."""
    from ..database import update_worker_setting, update_link_setting, get_worker_settings, get_link_by_id
    from ..renderers import render_settings_menu
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    data = await state.get_data()
    link_id = data.get('link_id')
    link_type = data.get('type', 'theatre')
    setting_key = data.get('setting', 'max_price_override')
    
    back_callback = f"menu_settings{'_cinema' if link_type == 'cinema' else ''}:{link_id}" if link_id else f"menu_settings{'_cinema' if link_type == 'cinema' else ''}"
    
    # Try to parse as number
    price_text = message.text.strip().replace('₽', '').replace(' ', '').replace(',', '')
    
    try:
        price = int(price_text)
    except ValueError:
        await message.answer(
            "❌ <b>Неверный формат</b>\n\n"
            "Пожалуйста, введите число (например: 5000)",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ К настройкам", callback_data=back_callback)]
            ])
        )
        return
    
    # Get current settings to check min/max price constraints
    current_settings = {}
    if link_id:
        if link_type == 'cinema':
            from ..database import get_cinema_link_by_id
            current_settings = await get_cinema_link_by_id(link_id) or {}
        else:
            current_settings = await get_link_by_id(link_id) or {}
    else:
        settings = await get_worker_settings(message.from_user.id)
        current_settings = settings if settings else {}
    
    # Determine what we are comparing against
    compare_min = None
    compare_max = None
    
    if link_type == 'cinema' and not link_id:
        compare_min = current_settings.get('cinema_min_price_override')
        compare_max = current_settings.get('cinema_max_price_override')
    else:
        compare_min = current_settings.get('min_price_override')
        compare_max = current_settings.get('max_price_override')
        
    # Validate based on what we are setting
    is_setting_min = 'min_price' in setting_key
    
    if is_setting_min:
        # We are setting MIN price, check against MAX
        if compare_max and price >= compare_max:
             await message.answer(
                f"❌ <b>Мин. цена должна быть меньше макс. цены</b>\n\n"
                f"Текущая макс. цена: {compare_max}₽\n"
                f"Введите значение меньше {compare_max}₽",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ К настройкам", callback_data=back_callback)]
                ])
            )
             return
    else:
        # We are setting MAX price, check against MIN
        if compare_min and price <= compare_min:
            await message.answer(
                f"❌ <b>Макс. цена должна быть больше мин. цены</b>\n\n"
                f"Текущая мин. цена: {compare_min}₽\n"
                f"Введите значение больше {compare_min}₽",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ К настройкам", callback_data=back_callback)]
                ])
            )
            return

    # Validate absolute ranges
    if price < 100: # lowered min for cinema flexibility
        await message.answer(
            "❌ <b>Слишком маленькая цена</b>\n\n"
            "Минимальная цена: 100₽",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ К настройкам", callback_data=back_callback)]
            ])
        )
        return
    
    if price > 100000:
        await message.answer(
            "❌ <b>Слишком большая цена</b>\n\n"
            "Максимальная цена: 100000₽",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ К настройкам", callback_data=back_callback)]
            ])
        )
        return
    
    # Save the price
    from ..database import update_cinema_link_setting
    if link_id:
        if link_type == 'cinema':
            await update_cinema_link_setting(link_id, setting_key, price)
        else:
            await update_link_setting(link_id, setting_key, price)
    else:
        target_setting = setting_key
        if link_type == 'cinema':
            if 'min_price' in setting_key: target_setting = 'cinema_min_price_override'
            elif 'max_price' in setting_key: target_setting = 'cinema_max_price_override'
            
        await update_worker_setting(message.from_user.id, target_setting, price)
    
    # Confirm and go back to settings
    await message.answer(
        f"✅ <b>Макс. цена установлена: {price}₽</b>\n\n"
        f"<i>Эта цена будет максимальной за место\nдля ваших рефералов.</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ К настройкам", callback_data=back_callback)]
        ])
    )
    
    await state.clear()

# Event Creation Handlers
@dp.message(EventCreation.waiting_title)
async def process_event_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    
    await message.answer(
        "<b>Описание события</b>\n\n"
        "Введите описание события:\n\n"
        "<i>Напишите краткое описание того, что будет происходить на событии.</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(EventCreation.waiting_description)

@dp.message(EventCreation.waiting_description)
async def process_event_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    
    await message.answer(
        "<b>Фото события</b>\n\n"
        "Отправьте фото события:\n\n"
        "<i>Фото обязательно для создания события.\n"
        "Это поможет привлечь больше зрителей!</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(EventCreation.waiting_photo)

@dp.message(EventCreation.waiting_photo, F.photo)
async def process_event_photo(message: types.Message, state: FSMContext):
    # Save photo
    photo = message.photo[-1]  # Get highest resolution
    file_info = await bot.get_file(photo.file_id)
    
    # Create events photos directory
    import os
    photos_dir = "bots/images/events"
    os.makedirs(photos_dir, exist_ok=True)
    
    # Save with unique filename
    import time
    filename = f"event_{int(time.time())}_{photo.file_id}.jpg"
    file_path = os.path.join(photos_dir, filename)
    
    await bot.download_file(file_info.file_path, file_path)
    await state.update_data(photo_path=file_path)
    
    await message.answer(
        "<b>Минимальная цена</b>\n\n"
        "Введите минимальную цену за билет (в рублях):\n\n"
        "<i>Например: 1500</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(EventCreation.waiting_min_price)

@dp.message(EventCreation.waiting_photo)
async def process_event_photo_invalid(message: types.Message, state: FSMContext):
    await message.answer(
        "<b>Необходимо отправить фото!</b>\n\n"
        "Для создания события обязательно нужно загрузить фото.\n"
        "Пожалуйста, отправьте изображение события.",
        parse_mode="HTML"
    )

@dp.message(EventCreation.waiting_min_price)
async def process_min_price(message: types.Message, state: FSMContext):
    try:
        min_price = int(message.text)
        if min_price <= 0:
            raise ValueError()
        
        await state.update_data(min_price=min_price)
        
        await message.answer(
            "<b>Максимальная цена</b>\n\n"
            "Введите максимальную цену за билет (в рублях):\n\n"
            f"<i>Должна быть больше {min_price} рублей</i>",
            parse_mode="HTML"
        )
        
        await state.set_state(EventCreation.waiting_max_price)
        
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректную цену (только цифры больше 0)"
        )

@dp.message(EventCreation.waiting_max_price)
async def process_max_price(message: types.Message, state: FSMContext):
    try:
        max_price = int(message.text)
        data = await state.get_data()
        min_price = data.get('min_price', 0)
        
        if max_price <= min_price:
            await message.answer(
                f"Максимальная цена должна быть больше минимальной ({min_price} руб.)"
            )
            return
        
        await state.update_data(max_price=max_price)
        
        await message.answer(
            "<b>📅 Дата и время</b>\n\n"
            "Введите дату и время события:\n\n"
            "<i>Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Например: 15.03.2026 19:30</i>",
            parse_mode="HTML"
        )
        
        await state.set_state(EventCreation.waiting_date_time)
        
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректную цену (только цифры)"
        )

@dp.message(EventCreation.waiting_date_time)
async def process_date_time(message: types.Message, state: FSMContext):
    try:
        from datetime import datetime
        # Try to parse the date
        dt = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        formatted_dt = dt.strftime("%Y-%m-%d %H:%M")
        
        await state.update_data(date_time=formatted_dt)
        
        await message.answer(
            "<b>🏛 Место проведения</b>\n\n"
            "Введите место проведения события:\n\n"
            "<i>Например: Театр Драмы им. Горького - Основная сцена</i>",
            parse_mode="HTML"
        )
        
        await state.set_state(EventCreation.waiting_venue)
        
    except ValueError:
        await message.answer(
            "Неверный формат даты и времени.\n"
            "Используйте формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Например: 15.03.2026 19:30"
        )

@dp.message(EventCreation.waiting_venue)
async def process_venue(message: types.Message, state: FSMContext):
    await state.update_data(venue=message.text)
    
    # Get all data and create event
    data = await state.get_data()
    user_id = message.from_user.id
    event_type = data.get('event_type', 'theatre')
    menu_callback = "menu_events_cinema" if event_type == "cinema" else "menu_events"
    list_callback = "events_list_cinema" if event_type == "cinema" else "events_list"
    
    try:
        from ..database import create_event
        
        # Проверяем наличие фото
        if not data.get('photo_path'):
            await message.answer(
                "<b>Ошибка создания события</b>\n\n"
                "Не удалось найти фото события. Пожалуйста, начните создание заново и обязательно загрузите фото.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="В меню событий", callback_data=menu_callback)]
                ])
            )
            await state.clear()
            return
        
        event_id = await create_event(
            title=data['title'],
            description=data['description'],
            min_price=data['min_price'],
            max_price=data['max_price'],
            date_time=data['date_time'],
            venue=data['venue'],
            created_by=user_id,
            photo_path=data['photo_path'],
            event_type=event_type
        )
        
        # Verify event was actually created
        from ..database import get_event_by_id
        created_event = await get_event_by_id(event_id)
        if not created_event:
            logger.error(f"Event creation verification failed: event_id={event_id} not found in database")
            raise Exception("Event was not saved to database")
        
        logger.info(f"Event created and verified: id={event_id}, title={data['title']}, user={user_id}, type={event_type}")
        
        # Format date for display
        from datetime import datetime
        dt = datetime.strptime(data['date_time'], "%Y-%m-%d %H:%M")
        formatted_date = dt.strftime("%d.%m.%Y в %H:%M")
        
        success_text = (
            "<b>✅ Событие создано!</b>\n\n"
            f"<b>Название:</b> {data['title']}\n"
            f"<b>Дата:</b> {formatted_date}\n"
            f"<b>Место:</b> {data['venue']}\n"
            f"<b>Цены:</b> {data['min_price']} - {data['max_price']} руб.\n\n"
            "<i>Событие добавлено в список и доступно для бронирования!</i>"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Посмотреть событие", callback_data=f"view_event:{event_id}")],
            [InlineKeyboardButton(text="К списку событий", callback_data=list_callback)]
        ])
        
        await message.answer(success_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        await message.answer(
            "Произошла ошибка при создании события. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="В меню событий", callback_data=menu_callback)]
            ])
        )
    
    await state.clear()

# ============================================================================
# Event Editing Handlers
# ============================================================================

async def return_to_event_view(message, state, event_id):
    """Helper to return to event view after edit."""
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться к событию", callback_data=f"view_event:{event_id}")]
    ])
    
    await message.answer(
        "Нажмите кнопку ниже, чтобы увидеть обновленное событие:",
        reply_markup=keyboard
    )

@dp.message(EventEdit.waiting_title)
async def process_edit_title(message: types.Message, state: FSMContext):
    data = await state.get_data()
    event_id = data.get('event_id')
    
    from ..database import update_event
    await update_event(event_id, title=message.text)
    
    await message.answer("✅ Название событие обновлено!")
    await return_to_event_view(message, state, event_id)

@dp.message(EventEdit.waiting_description)
async def process_edit_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    event_id = data.get('event_id')
    
    from ..database import update_event
    await update_event(event_id, description=message.text)
    
    await message.answer("✅ Описание события обновлено!")
    await return_to_event_view(message, state, event_id)

@dp.message(EventEdit.waiting_venue)
async def process_edit_venue(message: types.Message, state: FSMContext):
    data = await state.get_data()
    event_id = data.get('event_id')
    
    from ..database import update_event
    await update_event(event_id, venue=message.text)
    
    await message.answer("✅ Место проведения обновлено!")
    await return_to_event_view(message, state, event_id)

@dp.message(EventEdit.waiting_datetime)
async def process_edit_datetime(message: types.Message, state: FSMContext):
    data = await state.get_data()
    event_id = data.get('event_id')
    
    try:
        from datetime import datetime
        dt = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        formatted_dt = dt.strftime("%Y-%m-%d %H:%M")
        
        from ..database import update_event
        await update_event(event_id, date_time=formatted_dt)
        
        await message.answer("✅ Дата и время обновлены!")
        await return_to_event_view(message, state, event_id)
        
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Используйте формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Например: 15.03.2026 19:30"
        )

@dp.message(EventEdit.waiting_min_price)
async def process_edit_min_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    event_id = data.get('event_id')
    
    try:
        price = int(message.text)
        if price <= 0: raise ValueError
        
        from ..database import update_event, get_event_by_id
        event = await get_event_by_id(event_id)
        
        if price >= event['max_price']:
            await message.answer(f"❌ Мин. цена должна быть меньше макс. цены ({event['max_price']}₽)")
            return
            
        await update_event(event_id, min_price=price)
        
        await message.answer("✅ Минимальная цена обновлена!")
        await return_to_event_view(message, state, event_id)
        
    except ValueError:
        await message.answer("❌ Введите корректное число больше 0")

@dp.message(EventEdit.waiting_max_price)
async def process_edit_max_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    event_id = data.get('event_id')
    
    try:
        price = int(message.text)
        
        from ..database import update_event, get_event_by_id
        event = await get_event_by_id(event_id)
        
        if price <= event['min_price']:
            await message.answer(f"❌ Макс. цена должна быть больше мин. цены ({event['min_price']}₽)")
            return
            
        await update_event(event_id, max_price=price)
        
        await message.answer("✅ Максимальная цена обновлена!")
        await return_to_event_view(message, state, event_id)
        
    except ValueError:
        await message.answer("❌ Введите корректное число")


# ============================================================================
# Theatre Link Creation Handler
# ============================================================================

@dp.message(TheatreLinkCreation.waiting_link_name)
async def process_link_name(message: types.Message, state: FSMContext):
    """Process theatre link name input."""
    link_name = message.text.strip()
    
    # Validate name length
    if len(link_name) < 2:
        await message.answer(
            "❌ Название ссылки слишком короткое.\nВведите минимум 2 символа:",
            parse_mode="HTML"
        )
        return
    
    if len(link_name) > 50:
        await message.answer(
            "❌ Название ссылки слишком длинное.\nМаксимум 50 символов:",
            parse_mode="HTML"
        )
        return
    
    try:
        from ..database import create_theatre_link
        
        link = await create_theatre_link(message.from_user.id, link_name)
        
        if link:
            await message.answer(
                f"✅ <b>Ссылка создана!</b>\n\n"
                f"<b>Название:</b> {link_name}\n"
                f"<b>Код:</b> <code>{link['link_code']}</code>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ К списку ссылок", callback_data="menu_theatre")]
                ])
            )
        else:
            await message.answer(
                "❌ Ошибка при создании ссылки. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ К списку ссылок", callback_data="menu_theatre")]
                ])
            )
            
    except Exception as e:
        logger.error(f"Error creating theatre link: {e}")
        await message.answer(
            "❌ Ошибка при создании ссылки. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ К списку ссылок", callback_data="menu_theatre")]
            ])
        )
    
    await state.clear()

# ============================================================================
# Cinema Link Creation Handler
# ============================================================================

@dp.message(CinemaLinkCreation.waiting_link_name)
async def process_cinema_link_name(message: types.Message, state: FSMContext):
    """Process cinema link name input."""
    link_name = message.text.strip()
    
    # Validate name length
    if len(link_name) < 2:
        await message.answer(
            "❌ Название ссылки слишком короткое.\nВведите минимум 2 символа:",
            parse_mode="HTML"
        )
        return
    
    if len(link_name) > 50:
        await message.answer(
            "❌ Название ссылки слишком длинное.\nМаксимум 50 символов:",
            parse_mode="HTML"
        )
        return
    
    try:
        from ..database import create_cinema_link
        
        link = await create_cinema_link(message.from_user.id, link_name)
        
        if link:
            await message.answer(
                f"✅ <b>Ссылка на Кино создана!</b>\n\n"
                f"<b>Название:</b> {link_name}\n"
                f"<b>Код:</b> <code>{link['link_code']}</code>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ К списку ссылок", callback_data="menu_cinema")]
                ])
            )
        else:
            await message.answer(
                "❌ Ошибка при создании ссылки. Попробуйте позже.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ К списку ссылок", callback_data="menu_cinema")]
                ])
            )
            
    except Exception as e:
        logger.error(f"Error creating cinema link: {e}")
        await message.answer(
            "❌ Ошибка при создании ссылки. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ К списку ссылок", callback_data="menu_cinema")]
            ])
        )
    
    await state.clear()

# ============================================================================
# Event Availability Handlers
# ============================================================================

@dp.message(EventAvailability.waiting_percent)
async def process_avail_percent(message: types.Message, state: FSMContext):
    try:
        percent = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите число от 0 до 100.")
        return
        
    if not (0 <= percent <= 100):
        await message.answer("Процент должен быть от 0 до 100.")
        return
        
    data = await state.get_data()
    event_id = data.get('event_id')
    
    from ..database import get_event_seats_stats, update_event_availability
    
    # Calculate target free count based on percent
    stats = await get_event_seats_stats(event_id)
    total = stats['total']
    
    target_free = int(total * (percent / 100))
    
    await update_event_availability(event_id, target_free)
    
    # Calculate actual stats after update
    stats = await get_event_seats_stats(event_id)
    real_percent = int((stats['free'] / total * 100)) if total > 0 else 0
    
    await message.answer(
        f"✅ <b>Доступность обновлена!</b>\n\n"
        f"Целевой процент: {percent}%\n"
        f"Свободных мест: {stats['free']} из {total} ({real_percent}%)",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="К управлению доступностью", callback_data=f"edit_event_availability:{event_id}")]
        ])
    )
    await state.clear()

@dp.message(EventAvailability.waiting_number)
async def process_avail_number(message: types.Message, state: FSMContext):
    try:
        number = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите целое число.")
        return
        
    data = await state.get_data()
    event_id = data.get('event_id')
    
    from ..database import get_event_seats_stats, update_event_availability
    
    stats = await get_event_seats_stats(event_id)
    total = stats['total']
    
    if not (0 <= number <= total):
        await message.answer(f"Количество должно быть от 0 до {total}.")
        return
    
    await update_event_availability(event_id, number)
    
    stats = await get_event_seats_stats(event_id)
    real_percent = int((stats['free'] / total * 100)) if total > 0 else 0
    
    await message.answer(
        f"✅ <b>Доступность обновлена!</b>\n\n"
        f"Целевое количество: {number}\n"
        f"Свободных мест: {stats['free']} из {total} ({real_percent}%)",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="К управлению доступностью", callback_data=f"edit_event_availability:{event_id}")]
        ])
    )
    await state.clear()

