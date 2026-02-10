
from data.db import db, logger

async def ensure_schema():
    """Ensures that the database schema is up to date."""
    logger.info(f"Checking database schema in {db.mode} mode...")

    if db.mode == "sqlite":
        await _ensure_sqlite_schema()
    else:
        await _ensure_postgres_schema()

async def _ensure_postgres_schema():
    # Helper for adding columns if missing - simplified for generic verify, 
    # but ideally we just use IF NOT EXISTS for tables.
    
    # Users
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_user_id BIGINT UNIQUE,
            chat_id BIGINT,
            referral_code TEXT UNIQUE,
            telegram_username TEXT,
            telegram_display_name TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            email TEXT,
            consent_terms BOOLEAN DEFAULT FALSE,
            consent_pd BOOLEAN DEFAULT FALSE,
            consent_marketing BOOLEAN DEFAULT FALSE,
            consent_at TIMESTAMP,
            referrer_user_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            balance INTEGER DEFAULT 0
        )
    """)

    # Registration Sessions
    await db.execute("""
        CREATE TABLE IF NOT EXISTS registration_sessions (
            session_id TEXT PRIMARY KEY,
            status TEXT,
            telegram_user_id BIGINT,
            chat_id BIGINT,
            telegram_username TEXT,
            telegram_display_name TEXT,
            code_hash TEXT,
            code_expires_at TIMESTAMP,
            session_expires_at TIMESTAMP,
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            reg_first_name TEXT,
            reg_last_name TEXT,
            reg_phone TEXT,
            reg_email TEXT,
            consent_pd BOOLEAN DEFAULT FALSE,
            consent_marketing BOOLEAN DEFAULT FALSE,
            consent_at TIMESTAMP,
            contact_phone TEXT,
            visitor_id TEXT,
            intent TEXT,
            login_token TEXT,
            login_token_expires_at TIMESTAMP,
            login_user_id INTEGER
        )
    """)

    # Visits
    await db.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id SERIAL PRIMARY KEY,
            referral_code TEXT,
            referral_owner_user_id INTEGER REFERENCES users(id),
            visitor_id TEXT,
            ip TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Orders
    await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            movie TEXT,
            session_time TEXT,
            qty INTEGER,
            total_price INTEGER,
            referrer_user_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Mamonts (visitor tracking)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS mamonts (
            id SERIAL PRIMARY KEY,
            mamont_id TEXT UNIQUE NOT NULL,
            visitor_id TEXT UNIQUE NOT NULL,
            referrer_user_id INTEGER NOT NULL REFERENCES users(id),
            referral_code TEXT,
            status TEXT DEFAULT 'attached',
            tg_name TEXT,
            tg_username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Event Seats zone_name column check is skipped for minimal migration
    # Assuming fresh DB or handled by initial CREATE
    
    logger.info("Postgres schema initialized.")

async def _ensure_sqlite_schema():
    # Existing SQLite logic
    # Note: I am not importing aiosqlite directly, but using db.execute which handles it.
    # However, for PRAGMA we need connection context or just execute one by one.
    # db.execute connects each time.
    
    await db.execute("PRAGMA journal_mode = WAL")
    await db.execute("PRAGMA busy_timeout = 30000")

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
            updated_at TIMESTAMP,
            reg_first_name TEXT,
            reg_last_name TEXT,
            reg_phone TEXT,
            reg_email TEXT,
            consent_pd BOOLEAN DEFAULT 0,
            consent_marketing BOOLEAN DEFAULT 0,
            consent_at TIMESTAMP,
            contact_phone TEXT,
            visitor_id TEXT,
            intent TEXT,
            login_token TEXT,
            login_token_expires_at TIMESTAMP,
            login_user_id INTEGER
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
    
    # Migrations (Generic wrapper for SQLite only)
    async def add_column_if_missing(table, column, definition):
        try:
            # We can't easily do "PRAGMA table_info" via simple fetchall adapter if we don't have cursor
            # But we can try to selecting the column logic or just ignore for now as this is fallback
            # Implementing a check via selecting 1 row
            try:
                await db.execute(f"SELECT {column} FROM {table} LIMIT 1")
            except Exception:
                logger.info(f"Migrating: Adding {column} to {table}...")
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except Exception as e:
            logger.error(f"Migration error for {table}.{column}: {e}")

    await add_column_if_missing("users", "referrer_user_id", "INTEGER REFERENCES users(id)")
    await add_column_if_missing("users", "telegram_username", "TEXT")
    # ... (skipping exhaustive list for brevity as tables above are updated)
    await add_column_if_missing("users", "balance", "INTEGER DEFAULT 0")
    await add_column_if_missing("event_seats", "zone_name", "TEXT") # If table existed

async def get_current_user(session_id: str = None, telegram_user_id: int = None):
    """Get current user from session or telegram_user_id."""
    if telegram_user_id:
        return await db.fetchone("SELECT * FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
    
    if session_id:
        row = await db.fetchone("""
            SELECT u.* FROM users u
            JOIN registration_sessions rs ON u.telegram_user_id = rs.telegram_user_id
            WHERE rs.session_id = ? AND rs.status = 'completed'
        """, (session_id,))
        return row
    
    return None