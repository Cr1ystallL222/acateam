import aiosqlite
import secrets
from typing import Optional
from .config import DB_PATH, logger

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

async def get_user_mamonts(telegram_user_id: int) -> list:
    """Get all mamonts for user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Get user_id from telegram_user_id
        async with db.execute("SELECT id FROM users WHERE telegram_user_id = ?", (telegram_user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return []
            user_id = row[0]
        
        # Get all mamonts for this user
        async with db.execute("""
            SELECT * FROM mamonts 
            WHERE referrer_user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
