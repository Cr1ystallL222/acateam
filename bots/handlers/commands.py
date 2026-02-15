from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, BufferedInputFile
import asyncio

from ..loader import bot, dp
from ..config import WELCOME_STICKER_ID, RESOLVED_IMAGE_PATH, ADMIN_IDS, logger
from ..utils import is_cooldown_active, format_cooldown_remaining, calculate_days_in_team, generate_me_image
from ..database import get_or_create_bot_user, has_pending_application, get_user_profits_stats
from ..renderers import render_profile_menu

@dp.message(Command("me"))
async def cmd_me(message: types.Message):
    """User stats command."""
    # 1. Send temporary loading message
    temp_msg = await message.answer("⚡️")
    
    # 2. Determine target user (Self or Reply)
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    else:
        target_user = message.from_user
        
    user_id = target_user.id
    username = target_user.username or ""
    full_name = target_user.full_name or "Unknown"
    
    # Ensure user exists in DB (even if just checking another user, we might need to ensure they are tracked? 
    # Actually if we check another user, they might not be in our DB if they haven't started the bot.
    # But `get_or_create_bot_user` requires chat_id which might be different if they rarely use it.
    # We'll use current chat_id for creation if needed, or just proceed.)
    try:
        user = await get_or_create_bot_user(user_id, message.chat.id, username, full_name)
    except Exception as e:
        # If database error or logic error, log and create dummy user dict
        logger.error(f"Error getting user {user_id}: {e}")
        user = {'joined_at': None}

    # Get stats
    stats = await get_user_profits_stats(user_id)
    days = calculate_days_in_team(user.get('joined_at'))
    
    photo_msg = None
    
    # Generate Image
    try:
        photo_bio = generate_me_image(
            nickname=full_name,
            total_profits=stats['profits_sum'],
            avg_profit=stats['profits_avg'],
            days_in_team=days
        )
        
        photo = BufferedInputFile(photo_bio.read(), filename="me.png")
        photo_msg = await message.answer_photo(photo)
        
    except Exception as e:
        logger.error(f"Error generating /me image: {e}")
        await message.answer("Произошла ошибка при генерации статистики.")
        
    # Auto-deletion after 20 seconds
    await asyncio.sleep(20)
    
    # Delete temp message
    try:
        await temp_msg.delete()
    except:
        pass
        
    # Delete photo message
    if photo_msg:
        try:
            await photo_msg.delete()
        except:
            pass
            
    # Delete user command message
    try:
        await message.delete()
    except:
        pass
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or ""
    
    # Log incoming message
    from ..services.logger_service import log_action
    await log_action(f"User started bot: {full_name} (@{username}, {user_id})", "VISIT")
    
    await state.clear()
    
    bot_user = await get_or_create_bot_user(user_id, chat_id, username, full_name)
    
    # Delete old menu message if exists
    old_msg_id = bot_user.get('last_menu_message_id')
    if old_msg_id:
        try:
            await bot.delete_message(chat_id, old_msg_id)
        except:
            pass
    
    if bot_user['approved'] == 1:
        # Show profile menu
        await render_profile_menu(chat_id, user_id, bot_user, None)
        
    elif is_cooldown_active(bot_user['cooldown_until']):
        remaining = format_cooldown_remaining(bot_user['cooldown_until'])
        await message.answer(
            "<b>⏳ Доступ ограничен</b>\n\n"
            "Ваша заявка была отклонена.\n"
            f"Повторная попытка через: <b>{remaining}</b>",
            parse_mode="HTML"
        )
    else:
        # Check if user has a pending application
        if await has_pending_application(user_id):
            await message.answer(
                "<b>⏳ Ваша заявка находится на рассмотрении</b>\n\n"
                "Пожалуйста, ожидайте решения администратора.",
                parse_mode="HTML"
            )
            return

        # Application flow
        if WELCOME_STICKER_ID:
            try:
                await message.answer_sticker(WELCOME_STICKER_ID)
            except Exception as e:
                logger.warning(f"Failed to send sticker: {e}")
        
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Продолжить", callback_data="continue")]
        ])
        
        welcome_text = (
            "<b>Добро пожаловать в ACA Team!</b>\n\n"
            "Для получения доступа к боту, необходимо пройти короткую анкету.\n\n"
            "<i>Это займёт всего минуту.</i>"
        )
        
        if RESOLVED_IMAGE_PATH.exists():
            photo = FSInputFile(RESOLVED_IMAGE_PATH)
            sent_msg = await message.answer_photo(photo, caption=welcome_text, parse_mode="HTML", reply_markup=markup)
        else:
            sent_msg = await message.answer(welcome_text, parse_mode="HTML", reply_markup=markup)
        
        await state.update_data(welcome_msg_id=sent_msg.message_id)
@dp.message(F.text == "/create_system_events")
async def cmd_create_system_events(message: types.Message):
    """Admin command to manually create system events."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Доступ запрещен")
        return
    
    await message.answer("Создаю системные события...")
    
    try:
        from ..database import create_system_events
        await create_system_events()
        await message.answer("✅ Системные события созданы успешно!")
    except Exception as e:
        logger.error(f"Error creating system events: {e}")
        await message.answer(f"Ошибка при создании событий: {e}")

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    """Top workers command."""
    # Check if we are in the correct chat
    TARGET_CHAT_ID = -1003594485909
    
    if message.chat.id != TARGET_CHAT_ID:
        return

    from ..database import get_project_stats, get_top_workers
    
    # Get stats
    stats = await get_project_stats()
    top_workers = await get_top_workers(10)
    
    turnover = stats['turnover']
    
    # Build text
    text = (
        "⭐️ <b>Касса проекта за все время</b>\n"
        f"     ┖ Оборот: {turnover} ₽\n\n"
        "<b>Топ-10 пользователей по сумме профитов:</b>\n\n"
    )
    
    if not top_workers:
        text += "Список пуст."
    else:
        for i, worker in enumerate(top_workers, 1):
            name = worker['full_name'] or worker['username'] or "Unknown"
            # Escape HTML in name just in case?
            # AIogram parses HTML, so tags in name might break it. 
            # Ideally use html.escape(name). 
            import html
            safe_name = html.escape(name)
            
            total = worker['total_revenue']
            count = worker['profits_count']
            
            text += f"{i}. {safe_name} — {total} ₽ — {count} шт\n"
            
    # Image path
    from pathlib import Path
    image_path = Path(__file__).parent.parent / "images" / "top_command.jpg"
    
    if image_path.exists():
        photo = FSInputFile(image_path)
        await message.answer_photo(photo, caption=text, parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Help command for specific chat."""
    # Check if we are in the correct chat
    TARGET_CHAT_ID = -1003594485909
    
    if message.chat.id != TARGET_CHAT_ID:
        return

    # Message content
    text = (
        "🔎 <b>Основная информация</b>\n\n"
        "⌛️ <b>График работы:</b> 07:00-00:00\n"
        "     ┖ <a href='https://t.me/ACATeamBot'>Бот - перейти</a>\n\n"
        "📖 <b>Основные команды Чата:</b>\n"
        "     ┠ /help - Показать это сообщение\n"
        "     ┠ /me - О себе\n"
        "     ┠ /top(d|w|m) - Топ проекта\n"
        "     ┖ /curators - наставники\n\n"
        "🏆 <b>Наш оборот:</b> 0"
    )
    
    # Image path
    from pathlib import Path
    # Assuming code is running from project root or relative path handling
    # The file structure seems to be bots/images/wealcom.jpg relative to project root
    # Using existing PROJECT_ROOT or relative path if possible. 
    # In bot.py PROJECT_ROOT is defined but here we are in a module.
    # Let's use relative path from this file: ../../images/wealcom.jpg
    
    image_path = Path(__file__).parent.parent / "images" / "wealcom.jpg"
    
    if image_path.exists():
        photo = FSInputFile(image_path)
        await message.answer_photo(photo, caption=text, parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)