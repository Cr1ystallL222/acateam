import asyncio
import logging
import os
import sys
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from dotenv import load_dotenv
import aiosqlite

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")

AUTH_BOT_TOKEN = os.getenv("AUTH_BOT_TOKEN")

# Absolute path to database
DB_PATH = PROJECT_ROOT / "data" / "app.db"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth_bot")

if not AUTH_BOT_TOKEN or "PLACEHOLDER" in AUTH_BOT_TOKEN:
    logger.error("AUTH_BOT_TOKEN is missing or placeholder! Please update .env")

# Initialize Bot and Dispatcher
bot = Bot(token=AUTH_BOT_TOKEN) if AUTH_BOT_TOKEN else None
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    args = message.text.split(maxsplit=1)
    payload = args[1] if len(args) > 1 else None

    if payload and payload.startswith("reg_"):
        session_id = payload.split("_")[1]
        await handle_registration_start(message, session_id)
    else:
        await message.answer("Этот бот предназначен только для входа и регистрации. Пожалуйста, используйте сайт.")

async def handle_registration_start(message: types.Message, session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # Check session
        async with db.execute("SELECT status, session_expires_at FROM registration_sessions WHERE session_id = ?", (session_id,)) as cursor:
            row = await cursor.fetchone()
        
        if not row:
            await message.answer("Ошибка: Сессия регистрации не найдена.")
            return
            
        status, session_expires_at = row
        if status not in ["created", "draft"]:
             await message.answer("Эта сессия регистрации уже активна или использована.")
             return
             
        # Ask for contact
        kb = [
            [types.KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
        
        await db.execute("""
            UPDATE registration_sessions 
            SET status = 'waiting_contact', 
                telegram_user_id = ?, 
                chat_id = ?,
                telegram_username = ?,
                telegram_display_name = ?,
                updated_at = ?
            WHERE session_id = ?
        """, (message.from_user.id, message.chat.id, message.from_user.username, message.from_user.full_name, datetime.now(timezone.utc), session_id))
        await db.commit()
        
        await message.answer(
            "Для завершения регистрации, пожалуйста, нажмите кнопку ниже, чтобы поделиться контактом.", 
            reply_markup=keyboard
        )

@dp.message(F.contact)
async def handle_contact(message: types.Message):
    contact = message.contact
    if not contact: return
    
    # Validation: contact user id match
    if contact.user_id != message.from_user.id:
        await message.answer("Пожалуйста, отправьте СВОЙ контакт.")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        # Find active session for this user in 'waiting_contact'
        async with db.execute(
            "SELECT session_id FROM registration_sessions WHERE telegram_user_id = ? AND status = 'waiting_contact'", 
            (message.from_user.id,)
        ) as cursor:
            row = await cursor.fetchone()
            
        if not row:
            await message.answer("Активная сессия регистрации не найдена. Попробуйте начать заново с сайта.")
            return
            
        session_id = row[0]
        
        # Generate Code
        code = f"{secrets.randbelow(9000) + 1000}" 
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        code_expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        
        await db.execute("""
            UPDATE registration_sessions 
            SET status = 'code_issued',
                contact_phone = ?,
                code_hash = ?,
                code_expires_at = ?,
                updated_at = ?
            WHERE session_id = ?
        """, (contact.phone_number, code_hash, code_expires_at, datetime.now(timezone.utc), session_id))
        await db.commit()
        
        await message.answer(f"Ваш код: `{code}`\n\nВведите его на сайте.", reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")

async def main():
    if not bot:
        logger.error("No AUTH_BOT_TOKEN found. Exiting.")
        return
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
