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

from data.db import db

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")

AUTH_BOT_TOKEN = os.getenv("AUTH_BOT_TOKEN")

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

    if payload:
        if payload.startswith("reg_"):
            session_id = payload[4:]
            await handle_registration_start(message, session_id, intent_override='register')
        elif payload.startswith("auth_"):
            session_id = payload[5:]
            await handle_registration_start(message, session_id, intent_override='login')
        else:
            await message.answer("Ошибка: Неверный формат ссылки.")
    else:
        await message.answer("Этот бот предназначен только для входа и регистрации. Пожалуйста, используйте сайт.")

async def handle_registration_start(message: types.Message, session_id: str, intent_override: str = None):
    # Check session
    row = await db.fetchone(
        "SELECT status, session_expires_at, intent FROM registration_sessions WHERE session_id = ?",
        (session_id,)
    )
    
    if not row:
        await message.answer("Ошибка: Сессия регистрации не найдена.")
        return
        
    status = row['status']
    intent = row['intent'] or 'login'
    
    if intent_override:
        intent = intent_override
        await db.execute(
            "UPDATE registration_sessions SET intent = ? WHERE session_id = ?",
            (intent, session_id)
        )
    
    if status not in ["created", "draft"]:
         await message.answer("Эта сессия регистрации уже активна или использована.")
         return
    
    # CLEANUP: Mark old waiting_contact sessions for this user as expired
    logger.info(f"Cleaning up old sessions for telegram_user_id={message.from_user.id}")
    await db.execute("""
        UPDATE registration_sessions 
        SET status = 'expired' 
        WHERE telegram_user_id = ? 
        AND status = 'waiting_contact' 
        AND session_id != ?
    """, (message.from_user.id, session_id))
    logger.info(f"Old sessions marked as expired")
         
    # Ask for contact
    kb = [
        [types.KeyboardButton(text="📱 Поделиться контактом", request_contact=True)]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
    
    now_utc = datetime.utcnow()
    await db.execute("""
        UPDATE registration_sessions 
        SET status = 'waiting_contact', 
            telegram_user_id = ?, 
            chat_id = ?,
            telegram_username = ?,
            telegram_display_name = ?,
            updated_at = ?
        WHERE session_id = ?
    """, (message.from_user.id, message.chat.id, message.from_user.username, message.from_user.full_name, now_utc, session_id))
    
    logger.info(f"Session {session_id} updated: telegram_user_id={message.from_user.id}, username={message.from_user.username}, display_name={message.from_user.full_name}, intent={intent}")
    
    msg_text = "Для входа в аккаунт, пожалуйста, нажмите кнопку ниже, чтобы поделиться контактом."
    if intent == 'register':
         msg_text = "Для завершения регистрации, пожалуйста, нажмите кнопку ниже, чтобы поделиться контактом."
         
    await message.answer(
        msg_text, 
        reply_markup=keyboard
    )

@dp.message(F.contact)
async def handle_contact(message: types.Message):
    contact = message.contact
    if not contact: 
        logger.warning("Received message without contact")
        return
    
    tg_id = message.from_user.id
    phone = contact.phone_number
    phone_normalized = ''.join(filter(str.isdigit, phone))
    
    logger.info(f"=== CONTACT HANDLER START ===")
    logger.info(f"Telegram ID: {tg_id}")
    logger.info(f"Phone (last 4): {phone_normalized[-4:]}")
    logger.info(f"Username: {message.from_user.username}")
    
    # Validation: contact user id match
    if contact.user_id != message.from_user.id:
        logger.warning(f"Contact user_id mismatch: {contact.user_id} != {tg_id}")
        await message.answer("Пожалуйста, отправьте СВОЙ контакт.")
        return
    
    # Find ALL active sessions for this user in 'waiting_contact'
    all_sessions = await db.fetchall(
        "SELECT session_id, intent, status, created_at, updated_at FROM registration_sessions WHERE telegram_user_id = ? AND status = 'waiting_contact' ORDER BY updated_at DESC", 
        (tg_id,)
    )
        
    if not all_sessions:
        logger.error(f"❌ NO ACTIVE SESSION found for tg_id={tg_id}")
        await message.answer("Активная сессия регистрации не найдена. Попробуйте начать заново с сайта.")
        return
    
    # Log all candidate sessions
    logger.info(f"📋 Found {len(all_sessions)} session(s) in 'waiting_contact' status:")
    for idx, sess in enumerate(all_sessions):
        logger.info(f"   [{idx}] session_id={sess['session_id']}, intent='{sess['intent']}', updated_at={sess['updated_at']}")
    
    # SELECTION LOGIC: Pick the most recent session (first in DESC order)
    row = all_sessions[0]
    
    session_id = row['session_id']
    intent = row['intent']
    
    logger.info(f"✅ SELECTED Session: session_id={session_id}")
    logger.info(f"📋 Intent from DB: '{intent}' (type: {type(intent).__name__})")
    logger.info(f"📋 Status from DB: '{row['status']}'")
    logger.info(f"📋 Updated at: {row['updated_at']}")
    
    # CRITICAL: Check if intent is None or empty
    if not intent:
        logger.error(f"❌ INTENT IS EMPTY/NULL! Setting default to 'login'")
        intent = 'login'
    
    logger.info(f"🔀 FLOW DECISION: intent='{intent}'")
    
    now_utc = datetime.utcnow()
    
    # РАЗДЕЛЕНИЕ ЛОГИКИ ПО INTENT
    if intent == 'register':
        logger.info(f"🟢 REGISTER FLOW: Generating code WITHOUT DB check")
        logger.info(f"   → Skipping user lookup in database")
        logger.info(f"   → Generating OTP code directly")
        
        code = f"{secrets.randbelow(9000) + 1000}" 
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        code_expires_at = now_utc + timedelta(minutes=5)
        
        await db.execute("""
            UPDATE registration_sessions 
            SET status = 'code_issued',
                contact_phone = ?,
                code_hash = ?,
                code_expires_at = ?,
                updated_at = ?
            WHERE session_id = ?
        """, (phone, code_hash, code_expires_at, now_utc, session_id))
        
        logger.info(f"✅ Registration code issued: session={session_id}, phone_last4={phone_normalized[-4:]}, code={code}")
        
        await message.answer(
            f"📝 Для завершения регистрации введите код на сайте:\n\n`{code}`\n\n"
            "⏱ Код действителен 5 минут.",
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        logger.info(f"=== CONTACT HANDLER END (REGISTER) ===")
        return
    
    # LOGIN FLOW
    logger.info(f"🔵 LOGIN FLOW: Checking if user exists in DB")
    logger.info(f"   → Looking up phone in users table")
    
    existing_user = await db.fetchone(
        "SELECT id, first_name, last_name, referrer_user_id FROM users WHERE phone LIKE ?", 
        (f'%{phone_normalized[-10:]}%',)
    )
    
    logger.info(f"   → User lookup result: {'FOUND' if existing_user else 'NOT FOUND'}")

    if not existing_user:
        logger.info(f"❌ User not found - rejecting login attempt")
        await message.answer(
            "❌ Номер не найден в базе.\n\n"
            "Если у вас нет аккаунта, пожалуйста, зарегистрируйтесь на сайте.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        logger.info(f"=== CONTACT HANDLER END (LOGIN FAILED) ===")
        return
    
    logger.info(f"✅ User found: id={existing_user['id']}, name={existing_user['first_name']}")
    logger.info(f"   → Generating login token")
    login_token = secrets.token_urlsafe(32)
    token_expires_at = now_utc + timedelta(minutes=15)
    
    await db.execute("""
        UPDATE registration_sessions 
        SET status = 'login_ready',
            contact_phone = ?,
            login_token = ?,
            login_token_expires_at = ?,
            login_user_id = ?,
            updated_at = ?
        WHERE session_id = ?
    """, (phone, login_token, token_expires_at, existing_user['id'], now_utc, session_id))
    
    logger.info(f"✅ Login token generated and saved")
    
    # Get SITE_URL
    SITE_URL = os.getenv("SITE_URL", "http://localhost:3000")
    login_link = f"{SITE_URL}/auth/login-token?token={login_token}"
    
    user_name = existing_user['first_name'] or "пользователь"
    
    msg = f"👋 С возвращением, {user_name}!\n\n🔐 Ваша ссылка для входа:\n\n{login_link}\n\n⏱ Ссылка действительна 15 минут."

    await message.answer(
        msg,
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    logger.info(f"✅ Login link sent to user")
    
    # Notify referrer if exists
    if existing_user['referrer_user_id']:
        logger.info(f"   → Notifying referrer: user_id={existing_user['referrer_user_id']}")
        try:
            # Get referrer chat_id
            ref_row = await db.fetchone(
                "SELECT chat_id FROM users WHERE id = ?", 
                (existing_user['referrer_user_id'],)
            )
            
            if ref_row and ref_row['chat_id']:
                from bots.loader import bot as main_bot
                try:
                    await main_bot.send_message(
                        ref_row['chat_id'],
                        f"🔔 Ваш мамонт вошел в аккаунт!\n\n"
                        f"👤 {existing_user['first_name'] or ''} {existing_user['last_name'] or ''}\n"
                        f"📱 Телефон: {phone}"
                    )
                    logger.info(f"   → Referrer notified successfully")
                except Exception as e:
                    logger.warning(f"Could not notify referrer: {e}")
        except Exception as e:
            logger.warning(f"Error notifying referrer: {e}")
    
    logger.info(f"=== CONTACT HANDLER END (LOGIN SUCCESS) ===")

async def main():
    if not bot:
        logger.error("No AUTH_BOT_TOKEN found. Exiting.")
        return
    await db.connect()
    logger.info("Auth bot DB connected.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
