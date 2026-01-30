import asyncio
import logging
import os
import secrets
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    FSInputFile,
    InputMediaPhoto
)
from aiogram.types.copy_text_button import CopyTextButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv
import aiosqlite

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")

# Configuration
MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN") or os.getenv("BOT_TOKEN")
APPLICATIONS_CHAT_ID = os.getenv("APPLICATIONS_CHAT_ID")
SITE_URL = os.getenv("SITE_URL", "http://localhost:3000")
WELCOME_STICKER_ID = os.getenv("WELCOME_STICKER_ID", "")
WELCOME_IMAGE_PATH = os.getenv("WELCOME_IMAGE_PATH", "")

# New profile & theatre config
WELCOME_PHOTO_PATH = os.getenv("WELCOME_PHOTO_PATH", "bots/images/wealcom.jpg")
THEATRE_PHOTO_PATH = os.getenv("THEATRE_PHOTO_PATH", "bots/images/Teatre.jpg")
THEATRE_GUIDE_URL = os.getenv("THEATRE_GUIDE_URL", "https://telegra.ph/Instrukciya-01-30")

# Absolute path to database
DB_PATH = PROJECT_ROOT / "data" / "app.db"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main_bot")

if not MAIN_BOT_TOKEN:
    logger.error("MAIN_BOT_TOKEN is missing! Please update .env")
    sys.exit(1)

if not APPLICATIONS_CHAT_ID:
    logger.warning("APPLICATIONS_CHAT_ID is not set - applications won't be sent to group")
else:
    logger.info(f"Applications will be sent to chat: {APPLICATIONS_CHAT_ID}")

# Initialize Bot and Dispatcher with FSM storage
bot = Bot(token=MAIN_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# FSM States
class ApplicationForm(StatesGroup):
    waiting_q1 = State()
    waiting_q2 = State()

# ============================================================================
# PATH HELPERS
# ============================================================================

def get_welcome_image_path():
    if WELCOME_IMAGE_PATH:
        p = Path(WELCOME_IMAGE_PATH)
        if p.is_absolute():
            return p
        return PROJECT_ROOT / p
    return PROJECT_ROOT / "bots" / "welcom.jpg"

def get_profile_photo_path():
    p = Path(WELCOME_PHOTO_PATH)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p

def get_theatre_photo_path():
    p = Path(THEATRE_PHOTO_PATH)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p

RESOLVED_IMAGE_PATH = get_welcome_image_path()
PROFILE_PHOTO_PATH = get_profile_photo_path()
THEATRE_PHOTO_RESOLVED = get_theatre_photo_path()

# ============================================================================
# DATABASE
# ============================================================================

async def ensure_bot_schema():
    """Create bot-specific tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # bot_users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER UNIQUE,
                chat_id INTEGER,
                username TEXT,
                full_name TEXT,
                approved INTEGER DEFAULT 0,
                cooldown_until TEXT,
                joined_at TEXT,
                balance INTEGER DEFAULT 0,
                last_menu_message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # applications table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER,
                q1_text TEXT,
                q2_text TEXT,
                status TEXT DEFAULT 'pending',
                confirm_message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                decided_at TIMESTAMP,
                decided_by INTEGER
            )
        """)
        
        # Also ensure users table exists for referrals
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER UNIQUE,
                chat_id INTEGER,
                referral_code TEXT UNIQUE,
                telegram_username TEXT,
                telegram_display_name TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                email TEXT,
                consent_terms BOOLEAN DEFAULT 0,
                consent_pd BOOLEAN DEFAULT 0,
                consent_marketing BOOLEAN DEFAULT 0,
                consent_at TIMESTAMP,
                referrer_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(referrer_user_id) REFERENCES users(id)
            )
        """)
        
        # Migration helper
        async def add_column_if_missing(table, column, definition):
            try:
                cursor = await db.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in await cursor.fetchall()]
                if column not in columns:
                    logger.info(f"Migrating: Adding {column} to {table}...")
                    await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            except Exception as e:
                logger.error(f"Migration error for {table}.{column}: {e}")
        
        # Add new columns
        await add_column_if_missing("bot_users", "joined_at", "TEXT")
        await add_column_if_missing("bot_users", "balance", "INTEGER DEFAULT 0")
        await add_column_if_missing("bot_users", "last_menu_message_id", "INTEGER")
        await add_column_if_missing("applications", "confirm_message_id", "INTEGER")
        
        await db.commit()
    logger.info("Bot schema OK")

async def get_or_create_bot_user(telegram_user_id: int, chat_id: int, username: str, full_name: str) -> dict:
    """Upsert bot_user and return their record."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("SELECT * FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,)) as cursor:
            row = await cursor.fetchone()
        
        if row:
            await db.execute("""
                UPDATE bot_users SET chat_id = ?, username = ?, full_name = ? WHERE telegram_user_id = ?
            """, (chat_id, username, full_name, telegram_user_id))
            await db.commit()
            
            async with db.execute("SELECT * FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,)) as cursor:
                row = await cursor.fetchone()
            return dict(row)
        else:
            await db.execute("""
                INSERT INTO bot_users (telegram_user_id, chat_id, username, full_name)
                VALUES (?, ?, ?, ?)
            """, (telegram_user_id, chat_id, username, full_name))
            await db.commit()
            
            async with db.execute("SELECT * FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,)) as cursor:
                row = await cursor.fetchone()
            logger.info(f"Bot user created: telegram_user_id={telegram_user_id}, username={username}")
            return dict(row)

async def save_last_menu_message_id(telegram_user_id: int, message_id: int):
    """Save last menu message id for edit/delete pattern."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE bot_users SET last_menu_message_id = ? WHERE telegram_user_id = ?
        """, (message_id, telegram_user_id))
        await db.commit()

async def get_last_menu_message_id(telegram_user_id: int) -> Optional[int]:
    """Get last menu message id."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT last_menu_message_id FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row and row[0] else None

async def get_or_create_referral(telegram_user_id: int, chat_id: int) -> str:
    """Get or create referral code for approved user."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT referral_code FROM users WHERE telegram_user_id = ?", (telegram_user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return row[0]
        
        while True:
            new_ref = secrets.token_urlsafe(8)
            try:
                await db.execute("""
                    INSERT INTO users (telegram_user_id, chat_id, referral_code)
                    VALUES (?, ?, ?)
                """, (telegram_user_id, chat_id, new_ref))
                await db.commit()
                logger.info(f"Referral created: telegram_user_id={telegram_user_id}, code={new_ref}")
                return new_ref
            except aiosqlite.IntegrityError:
                async with db.execute("SELECT referral_code FROM users WHERE telegram_user_id = ?", (telegram_user_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row and row[0]:
                        return row[0]
                continue

async def get_user_profits_stats(telegram_user_id: int) -> dict:
    """Get profit stats for user from orders table."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM users WHERE telegram_user_id = ?", (telegram_user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {"profits_count": 0, "profits_sum": 0, "profits_avg": 0}
            user_id = row[0]
        
        async with db.execute("""
            SELECT COALESCE(SUM(qty), 0), COALESCE(SUM(total_price), 0) 
            FROM orders WHERE referrer_user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            profits_count = row[0] or 0
            profits_sum = row[1] or 0
            profits_avg = int(profits_sum / profits_count) if profits_count > 0 else 0
        
        return {
            "profits_count": profits_count,
            "profits_sum": profits_sum,
            "profits_avg": profits_avg
        }

# ============================================================================
# HELPERS
# ============================================================================

def format_cooldown_remaining(cooldown_until: str) -> str:
    try:
        cd = datetime.fromisoformat(cooldown_until)
        if cd.tzinfo is None:
            cd = cd.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if cd <= now:
            return "00:00"
        delta = cd - now
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    except:
        return "00:00"

def is_cooldown_active(cooldown_until: Optional[str]) -> bool:
    if not cooldown_until:
        return False
    try:
        cd = datetime.fromisoformat(cooldown_until)
        if cd.tzinfo is None:
            cd = cd.replace(tzinfo=timezone.utc)
        return cd > datetime.now(timezone.utc)
    except:
        return False

def calculate_days_in_team(joined_at: Optional[str]) -> int:
    if not joined_at:
        return 0
    try:
        joined = datetime.fromisoformat(joined_at)
        if joined.tzinfo is None:
            joined = joined.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - joined
        return max(0, delta.days)
    except:
        return 0

# ============================================================================
# KEYBOARDS
# ============================================================================

def get_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎭 Театр", callback_data="menu_theatre"),
            InlineKeyboardButton(text="🎬 Кино", callback_data="menu_cinema")
        ]
    ])

def get_theatre_keyboard(ref_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать реф. ссылку", copy_text=CopyTextButton(text=ref_link))],
        [
            InlineKeyboardButton(text="👥 Клиенты", callback_data="menu_clients"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_back_profile")]
    ])

def get_stub_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu_back_theatre")]
    ])

# ============================================================================
# MENU RENDERERS (Single Message Pattern)
# ============================================================================

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
    
    keyboard = get_profile_keyboard()
    
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
    """Render clients stub menu. Returns new message_id."""
    text = "<b>👥 Раздел Клиенты</b>\n\n<i>В разработке...</i>"
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

# ============================================================================
# COMMANDS
# ============================================================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or ""
    
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
        # Application flow
        if WELCOME_STICKER_ID:
            try:
                await message.answer_sticker(WELCOME_STICKER_ID)
            except Exception as e:
                logger.warning(f"Failed to send sticker: {e}")
        
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Продолжить", callback_data="continue")]
        ])
        
        welcome_text = (
            "<b>🎬 Добро пожаловать в ACA Team!</b>\n\n"
            "Для получения доступа к боту, необходимо пройти короткую анкету.\n\n"
            "<i>Это займёт всего минуту.</i>"
        )
        
        if RESOLVED_IMAGE_PATH.exists():
            photo = FSInputFile(RESOLVED_IMAGE_PATH)
            sent_msg = await message.answer_photo(photo, caption=welcome_text, parse_mode="HTML", reply_markup=markup)
        else:
            sent_msg = await message.answer(welcome_text, parse_mode="HTML", reply_markup=markup)
        
        await state.update_data(welcome_msg_id=sent_msg.message_id)

# ============================================================================
# MENU CALLBACKS
# ============================================================================

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

# ============================================================================
# APPLICATION FLOW
# ============================================================================

@dp.callback_query(F.data == "continue")
async def cb_continue(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    msg_id = data.get("welcome_msg_id")
    
    question_text = (
        "<b>📝 Вопрос 1/2</b>\n\n"
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
        "<b>📝 Вопрос 2/2</b>\n\n"
        "Готовы ли вы выполнять все требования администрации?\n\n"
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
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO applications (telegram_user_id, q1_text, q2_text)
            VALUES (?, ?, ?)
        """, (user_id, q1, q2))
        app_id = cursor.lastrowid
        await db.commit()
    
    logger.info(f"Application created: id={app_id}, telegram_user_id={user_id}")
    
    if APPLICATIONS_CHAT_ID:
        app_text = (
            f"<b>📨 Новая заявка #{app_id}</b>\n\n"
            f"<b>От:</b> {full_name}\n"
            f"<b>Username:</b> @{username if username else 'нет'}\n"
            f"<b>ID:</b> <code>{user_id}</code>\n\n"
            f"<b>Вопрос 1:</b> Есть ли у вас опыт?\n"
            f"<i>{q1}</i>\n\n"
            f"<b>Вопрос 2:</b> Готовы ли выполнять требования?\n"
            f"<i>{q2}</i>"
        )
        
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"approve:{user_id}:{app_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{user_id}:{app_id}")
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
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE applications SET confirm_message_id = ? WHERE id = ?", (confirm_msg.message_id, app_id))
        await db.commit()
    
    await state.clear()

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

async def main():
    await ensure_bot_schema()
    logger.info("Starting main bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
