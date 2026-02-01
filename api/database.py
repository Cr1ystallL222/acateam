import aiosqlite
from .config import DB_PATH, logger

async def get_db_path():
    return DB_PATH

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
