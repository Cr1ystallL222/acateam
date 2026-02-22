
from typing import Optional, List, Any
from data.db import db, logger
import secrets
import asyncio

MIN_PRICE_OPTIONS = [1000, 1500, 2000, 2500, 3000, 5000]

CITY_VENUES = {
    "Краснодар": [
        "Театр Драмы им. Горького",
        "Музыкальный театр",
        "Филармония им. Пономаренко",
        "Центральный концертный зал",
        "Дворец искусств «Премьера»"
    ],
    "Сочи": [
        "Зимний театр",
        "Зал органной и камерной музыки",
        "New Wave Hall",
        "Зеленый театр"
    ],
    "Ростов-на-Дону": [
        "Театр Горького",
        "Музыкальный театр",
        "Молодежный театр"
    ],
    "Москва": [
        "Большой театр",
        "МХТ им. Чехова",
        "Театр Наций",
        "Ленком",
        "Театр Сатиры"
    ],
    "Санкт-Петербург": [
        "Мариинский театр",
        "Михайловский театр",
        "Александринский театр",
        "БДТ им. Товстоногова"
    ]
}

CINEMA_VENUES = {
    "Краснодар": [
        "Киномакс-Краснодар",
        "Монитор СБС",
        "Монитор Красная Площадь",
        "Формула Кино OZ"
    ],
    "Сочи": [
        "Киноград",
        "Сити Старс",
        "Люксор IMAX"
    ],
    "Ростов-на-Дону": [
        "Киномакс-Дон",
        "Горизонт Cinema&Emotion",
        "Синема Стар"
    ],
    "Москва": [
        "Октябрь (КАРО 11)",
        "Формула Кино Европа",
        "Киномакс-Мозаика",
        "Синема Парк Ривьера",
        "Иллюзион"
    ],
    "Санкт-Петербург": [
        "Аврора",
        "Мираж Синема на Большом",
        "Кинополис",
        "Формула Кино Галерея"
    ]
}

async def ensure_bot_schema():
    """Create bot-specific tables."""
    logger.info(f"Checking bot schema in {db.mode} mode...")
    
    if db.mode == "sqlite":
        await _ensure_sqlite_bot_schema()
    else:
        await _ensure_postgres_bot_schema()
        
    # Seed default events if table is empty
    # db.execute handles connection, so we can check count easily
    row = await db.fetchone("SELECT COUNT(*) as count FROM events")
    if row and row['count'] == 0:
        await seed_default_events()
    
    # Always ensure theatre events exist and have correct type
    await seed_theatre_events()
        
    logger.info("Bot schema OK")

async def _ensure_postgres_bot_schema():
    # bot_users
    await db.execute("""
        CREATE TABLE IF NOT EXISTS bot_users (
            id SERIAL PRIMARY KEY,
            telegram_user_id BIGINT UNIQUE,
            chat_id BIGINT,
            username TEXT,
            full_name TEXT,
            approved INTEGER DEFAULT 0,
            cooldown_until TEXT,
            joined_at TEXT,
            balance INTEGER DEFAULT 0,
            last_menu_message_id INTEGER,
            last_invite_link TEXT,
            last_invite_created_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # applications
    await db.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
            telegram_user_id BIGINT,
            q1_text TEXT,
            q2_text TEXT,
            status TEXT DEFAULT 'pending',
            confirm_message_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            decided_at TIMESTAMP,
            decided_by BIGINT
        )
    """)

    # users (Shared table - ensure exists)
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

    # Events
    await db.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            photo_path TEXT,
            min_price INTEGER NOT NULL,
            max_price INTEGER NOT NULL,
            date_time TEXT,
            venue TEXT,
            is_system BOOLEAN DEFAULT FALSE,
            created_by BIGINT REFERENCES bot_users(telegram_user_id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            type TEXT DEFAULT 'cinema'
        )
    """)

    try:
        await db.execute("ALTER TABLE events ADD COLUMN type TEXT DEFAULT 'cinema'")
        logger.info("Added type column to events table")
    except Exception:
        pass
        
    # Миграция старых театральных событий: если событие системное, и его название одно из театральных (содержащих "Спектакль", "Комедия", "Балет", "Мюзикл", "Шоу"), меняем тип на theatre
    # Исключаем новые события кино, у которых id обычно меньше 100 (1, 2, 3...)
    try:
        await db.execute("""
            UPDATE events 
            SET type = 'theatre' 
            WHERE is_system = TRUE AND type = 'cinema' AND id >= 100 AND (
                title LIKE '%Спектакль%' OR 
                title LIKE '%Комедия%' OR 
                title LIKE '%Балет%' OR 
                title LIKE '%Мюзикл%' OR 
                title LIKE '%Шоу%' OR
                title LIKE '%Миры М.А.%' OR
                title LIKE '%Классика%'
            )
        """)
        logger.info("Migrated old theatre events to type='theatre'")
    except Exception as e:
        logger.error(f"Error migrating theatre events: {e}")

    # Event seats
    await db.execute("""
        CREATE TABLE IF NOT EXISTS event_seats (
            id SERIAL PRIMARY KEY,
            event_id INTEGER NOT NULL REFERENCES events(id),
            row_number INTEGER NOT NULL,
            seat_number INTEGER NOT NULL,
            price INTEGER NOT NULL,
            is_available BOOLEAN DEFAULT TRUE,
            reserved_by BIGINT REFERENCES bot_users(telegram_user_id),
            reserved_at TIMESTAMP,
            zone_name TEXT,
            UNIQUE(event_id, row_number, seat_number)
        )
    """)

    # Hidden events
    await db.execute("""
        CREATE TABLE IF NOT EXISTS hidden_events (
            id SERIAL PRIMARY KEY,
            event_id INTEGER NOT NULL REFERENCES events(id),
            hidden_by BIGINT NOT NULL REFERENCES bot_users(telegram_user_id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, hidden_by)
        )
    """)

    # Event overrides (for customized system events)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS event_overrides (
            id SERIAL PRIMARY KEY,
            event_id INTEGER NOT NULL REFERENCES events(id),
            telegram_user_id BIGINT NOT NULL REFERENCES bot_users(telegram_user_id),
            title TEXT,
            description TEXT,
            date_time TEXT,
            venue TEXT,
            min_price INTEGER,
            max_price INTEGER,
            photo_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, telegram_user_id)
        )
    """)

    # Worker settings
    await db.execute("""
        CREATE TABLE IF NOT EXISTS worker_settings (
            id SERIAL PRIMARY KEY,
            telegram_user_id BIGINT UNIQUE NOT NULL REFERENCES bot_users(telegram_user_id),
            min_price_override INTEGER DEFAULT NULL,
            max_price_override INTEGER DEFAULT NULL,
            custom_city TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cinema_min_price_override INTEGER DEFAULT NULL,
            cinema_max_price_override INTEGER DEFAULT NULL,
            cinema_custom_city TEXT DEFAULT NULL,
            system_seats_override INTEGER DEFAULT NULL,
            cinema_system_seats_override INTEGER DEFAULT NULL
        )
    """)
    
    # Theatre links
    await db.execute("""
        CREATE TABLE IF NOT EXISTS theatre_links (
            id SERIAL PRIMARY KEY,
            telegram_user_id BIGINT NOT NULL REFERENCES bot_users(telegram_user_id),
            name TEXT NOT NULL,
            link_code TEXT UNIQUE NOT NULL,
            custom_city TEXT DEFAULT NULL,
            min_price_override INTEGER DEFAULT NULL,
            max_price_override INTEGER DEFAULT NULL,
            system_seats_override INTEGER DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Cinema links
    await db.execute("""
        CREATE TABLE IF NOT EXISTS cinema_links (
            id SERIAL PRIMARY KEY,
            telegram_user_id BIGINT NOT NULL REFERENCES bot_users(telegram_user_id),
            name TEXT NOT NULL,
            link_code TEXT UNIQUE NOT NULL,
            custom_city TEXT DEFAULT NULL,
            min_price_override INTEGER DEFAULT NULL,
            max_price_override INTEGER DEFAULT NULL,
            system_seats_override INTEGER DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Deposits
    await db.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            requisites TEXT,
            bank_name TEXT,
            exact_amount INTEGER,
            group_message_id INTEGER,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Support tickets
    await db.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            message TEXT NOT NULL,
            reply_text TEXT,
            status TEXT DEFAULT 'open',
            group_message_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            replied_at TIMESTAMP,
            attachment_path TEXT,
            mamont_id TEXT
        )
    """)

    # Manual profits
    await db.execute("""
        CREATE TABLE IF NOT EXISTS manual_profits (
            id SERIAL PRIMARY KEY,
            worker_user_id INTEGER NOT NULL REFERENCES users(id),
            amount INTEGER NOT NULL,
            worker_share INTEGER,
            note TEXT,
            admin_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Withdrawal requests
    await db.execute("""
        CREATE TABLE IF NOT EXISTS withdrawal_requests (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            amount INTEGER NOT NULL,
            group_message_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migrations (Common for both SQLite and Postgres)
    async def add_column_if_missing(table, column, definition):
        try:
            # Check if column exists
            if db.mode == 'sqlite':
                await db.execute(f"SELECT {column} FROM {table} LIMIT 1")
            else:
                # Postgres check
                await db.execute(f"SELECT {column} FROM {table} LIMIT 1")
        except Exception:
            logger.info(f"Migrating: Adding {column} to {table}...")
            try:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            except Exception as e:
                # Ignore if it already exists (race condition or different error)
                logger.error(f"Migration error (might be already exists): {e}")

    await add_column_if_missing("bot_users", "joined_at", "TEXT")
    await add_column_if_missing("bot_users", "balance", "INTEGER DEFAULT 0")
    await add_column_if_missing("bot_users", "balance_hold", "INTEGER DEFAULT 0")
    await add_column_if_missing("bot_users", "last_menu_message_id", "INTEGER")
    await add_column_if_missing("bot_users", "last_invite_link", "TEXT")
    await add_column_if_missing("bot_users", "last_invite_created_at", "TIMESTAMP")
    await add_column_if_missing("applications", "confirm_message_id", "INTEGER")
    await add_column_if_missing("event_seats", "zone_name", "TEXT")
    await add_column_if_missing("worker_settings", "max_price_override", "INTEGER DEFAULT NULL")
    await add_column_if_missing("worker_settings", "cinema_min_price_override", "INTEGER DEFAULT NULL")
    await add_column_if_missing("worker_settings", "cinema_max_price_override", "INTEGER DEFAULT NULL")
    await add_column_if_missing("worker_settings", "cinema_custom_city", "TEXT DEFAULT NULL")
    await add_column_if_missing("worker_settings", "system_seats_override", "INTEGER DEFAULT NULL")
    await add_column_if_missing("worker_settings", "cinema_system_seats_override", "INTEGER DEFAULT NULL")
    await add_column_if_missing("theatre_links", "system_seats_override", "INTEGER DEFAULT NULL")
    await add_column_if_missing("cinema_links", "system_seats_override", "INTEGER DEFAULT NULL")
    await add_column_if_missing("deposits", "requisites", "TEXT")
    await add_column_if_missing("deposits", "bank_name", "TEXT")
    await add_column_if_missing("deposits", "exact_amount", "INTEGER")
    await add_column_if_missing("deposits", "group_message_id", "INTEGER")
    await add_column_if_missing("deposits", "expires_at", "TIMESTAMP")
    
    await add_column_if_missing("support_tickets", "attachment_path", "TEXT")
    await add_column_if_missing("support_tickets", "mamont_id", "TEXT")

async def _ensure_sqlite_bot_schema():
    await db.execute("PRAGMA journal_mode = WAL")
    await db.execute("PRAGMA busy_timeout = 30000")
    
    # Same SQLite DDL as before...
    # (Since I'm rewriting the file, I must include it)
    
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
            last_invite_link TEXT,
            last_invite_created_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ... other tables (abbreviated for the prompt response but I will write full file)
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
    
    # Events table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            photo_path TEXT,
            min_price INTEGER NOT NULL,
            max_price INTEGER NOT NULL,
            date_time TEXT,
            venue TEXT,
            is_system BOOLEAN DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES bot_users(telegram_user_id)
        )
    """)
    
    # Event seats table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS event_seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            row_number INTEGER NOT NULL,
            seat_number INTEGER NOT NULL,
            price INTEGER NOT NULL,
            is_available BOOLEAN DEFAULT 1,
            reserved_by INTEGER,
            reserved_at TIMESTAMP,
            zone_name TEXT,
            FOREIGN KEY(event_id) REFERENCES events(id),
            FOREIGN KEY(reserved_by) REFERENCES bot_users(telegram_user_id),
            UNIQUE(event_id, row_number, seat_number)
        )
    """)
    
    # Hidden events table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS hidden_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            hidden_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(event_id) REFERENCES events(id),
            FOREIGN KEY(hidden_by) REFERENCES bot_users(telegram_user_id),
            UNIQUE(event_id, hidden_by)
        )
    """)
    
    # Event overrides (for customized system events)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS event_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            telegram_user_id INTEGER NOT NULL,
            title TEXT,
            description TEXT,
            date_time TEXT,
            venue TEXT,
            min_price INTEGER,
            max_price INTEGER,
            photo_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(event_id) REFERENCES events(id),
            FOREIGN KEY(telegram_user_id) REFERENCES bot_users(telegram_user_id),
            UNIQUE(event_id, telegram_user_id)
        )
    """)
    
    # Worker settings table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS worker_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER UNIQUE NOT NULL,
            min_price_override INTEGER DEFAULT NULL,
            max_price_override INTEGER DEFAULT NULL,
            custom_city TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cinema_min_price_override INTEGER DEFAULT NULL,
            cinema_max_price_override INTEGER DEFAULT NULL,
            cinema_custom_city TEXT DEFAULT NULL,
            system_seats_override INTEGER DEFAULT NULL,
            cinema_system_seats_override INTEGER DEFAULT NULL,
            FOREIGN KEY(telegram_user_id) REFERENCES bot_users(telegram_user_id)
        )
    """)
    
    # Theatre links table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS theatre_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            link_code TEXT UNIQUE NOT NULL,
            custom_city TEXT DEFAULT NULL,
            min_price_override INTEGER DEFAULT NULL,
            max_price_override INTEGER DEFAULT NULL,
            system_seats_override INTEGER DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(telegram_user_id) REFERENCES bot_users(telegram_user_id)
        )
    """)

    # Cinema links table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS cinema_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            link_code TEXT UNIQUE NOT NULL,
            custom_city TEXT DEFAULT NULL,
            min_price_override INTEGER DEFAULT NULL,
            max_price_override INTEGER DEFAULT NULL,
            system_seats_override INTEGER DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(telegram_user_id) REFERENCES bot_users(telegram_user_id)
        )
    """)
    
    # Deposits table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            requisites TEXT,
            bank_name TEXT,
            exact_amount INTEGER,
            group_message_id INTEGER,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Support tickets table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            reply_text TEXT,
            status TEXT DEFAULT 'open',
            group_message_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            replied_at TIMESTAMP,
            attachment_path TEXT,
            mamont_id TEXT,
            user_read BOOLEAN DEFAULT FALSE,
            bot_message_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Manual profits table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS manual_profits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            worker_share INTEGER,
            note TEXT,
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(worker_user_id) REFERENCES users(id)
        )
    """)

    # Withdrawal requests table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS withdrawal_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            group_message_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Migrations (Common for both SQLite and Postgres)
    async def add_column_if_missing(table, column, definition):
        try:
            # Check if column exists
            if db.mode == 'sqlite':
                await db.execute(f"SELECT {column} FROM {table} LIMIT 1")
            else:
                # Postgres check
                await db.execute(f"SELECT {column} FROM {table} LIMIT 1")
        except Exception:
            logger.info(f"Migrating: Adding {column} to {table}...")
            try:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            except Exception as e:
                # Ignore if it already exists (race condition or different error)
                logger.error(f"Migration error (might be already exists): {e}")

    await add_column_if_missing("bot_users", "joined_at", "TEXT")
    await add_column_if_missing("bot_users", "balance", "INTEGER DEFAULT 0")
    await add_column_if_missing("bot_users", "balance_hold", "INTEGER DEFAULT 0")
    await add_column_if_missing("bot_users", "last_menu_message_id", "INTEGER")
    await add_column_if_missing("bot_users", "last_invite_link", "TEXT")
    await add_column_if_missing("bot_users", "last_invite_created_at", "TIMESTAMP")
    await add_column_if_missing("applications", "confirm_message_id", "INTEGER")
    await add_column_if_missing("event_seats", "zone_name", "TEXT")
    await add_column_if_missing("worker_settings", "max_price_override", "INTEGER DEFAULT NULL")
    await add_column_if_missing("worker_settings", "cinema_min_price_override", "INTEGER DEFAULT NULL")
    await add_column_if_missing("worker_settings", "cinema_max_price_override", "INTEGER DEFAULT NULL")
    await add_column_if_missing("worker_settings", "cinema_custom_city", "TEXT DEFAULT NULL")
    await add_column_if_missing("deposits", "requisites", "TEXT")
    await add_column_if_missing("deposits", "bank_name", "TEXT")
    await add_column_if_missing("deposits", "exact_amount", "INTEGER")
    await add_column_if_missing("deposits", "group_message_id", "INTEGER")
    await add_column_if_missing("deposits", "expires_at", "TIMESTAMP")
    
    await add_column_if_missing("support_tickets", "attachment_path", "TEXT")
    await add_column_if_missing("support_tickets", "mamont_id", "TEXT")
    await add_column_if_missing("support_tickets", "user_read", "BOOLEAN DEFAULT FALSE")
    await add_column_if_missing("support_tickets", "bot_message_id", "INTEGER")

    # Support replies table (New)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS support_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            reply_text TEXT NOT NULL,
            bot_message_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT FALSE,
            FOREIGN KEY(ticket_id) REFERENCES support_tickets(id)
        )
    """)
    if db.mode == 'postgres':
        # Ensure postgres uses SERIAL/BOOLEAN correctly if needed, but the above is generic enough except for AUTOINCREMENT
        # Actually standard SQL uses SERIAL for PG. My adapter might handle AUTOINCREMENT??
        # Usually for PG I should use SERIAL.
        pass

    # Quick PG fix for table creation if we are in PG mode within this function?
    # The code above uses AUTOINCREMENT which is SQLite specific usually.
    # We should separate or use IF NOT EXISTS with checks.
    # But bots/database.py uses one block.
    # Lets make it robust.


async def seed_default_events():
    """Insert default Cinema events.
    Clears existing system events first to ensure clean state.
    Uses dynamic future dates so events are always relevant."""
    # Only clear CINEMA system events (preserve theatre events!)
    logger.info("Clearing old cinema system events...")
    await db.execute("DELETE FROM hidden_events WHERE event_id IN (SELECT id FROM events WHERE is_system = TRUE AND type = 'cinema')")
    await db.execute("DELETE FROM event_seats WHERE event_id IN (SELECT id FROM events WHERE is_system = TRUE AND type = 'cinema')")
    await db.execute("DELETE FROM events WHERE is_system = TRUE AND type = 'cinema'")
    
    from datetime import datetime, timedelta
    import random
    
    now = datetime.now()
    
    # Cinema movies data mapped from web_cinema/data/movies.ts
    # Using relative day offsets: 0 = today, 1 = tomorrow, etc.
    # Prices mapped to min_price (and max_price + range)
    raw_events = [
        # Уже в кино
        {
            'id': 1, 'title': 'Грозовой перевал', 'description': 'История роковой любви Хитклиффа и Кэти. Мелодрама, драма. 18+', 
            'venue': 'Зал №1', 'day_offset': 0, 'hour': 19, 'min': 0, 
            'photo_path': '/movies_files/s7185.jpg', 'min_price': 450, 'max_price': 1000, 'is_system': 1
        },
        {
            'id': 2, 'title': 'Уволить Жору', 'description': 'Комедийная история о том, как сложно найти хорошего сотрудника. 16+', 
            'venue': 'Зал №2', 'day_offset': 0, 'hour': 14, 'min': 10,
            'photo_path': '/main_files/p7232.jpg', 'min_price': 350, 'max_price': 800, 'is_system': 1
        },
        {
            'id': 3, 'title': 'Убежище', 'description': 'Захватывающий триллер о выживании. 18+', 
            'venue': 'Зал №8', 'day_offset': 0, 'hour': 16, 'min': 30,
            'photo_path': '/main_files/p7217.jpg', 'min_price': 650, 'max_price': 1500, 'is_system': 1
        },
        {
            'id': 4, 'title': 'Здесь был Юра', 'description': 'Музыкальная комедия о поиске себя. 18+', 
            'venue': 'Зал №2', 'day_offset': 0, 'hour': 16, 'min': 45,
            'photo_path': '/main_files/p7210.jpg', 'min_price': 350, 'max_price': 800, 'is_system': 1
        },
        {
            'id': 5, 'title': 'Горничная', 'description': 'Напряженный триллер с неожиданными поворотами. 18+', 
            'venue': 'Зал №4', 'day_offset': 0, 'hour': 17, 'min': 10,
            'photo_path': '/main_files/p7167.jpg', 'min_price': 430, 'max_price': 900, 'is_system': 1
        },
        {
            'id': 6, 'title': 'Счастлив, когда ты нет', 'description': 'Комедия об отношениях и расставаниях. 18+', 
            'venue': 'Зал №6', 'day_offset': 0, 'hour': 21, 'min': 45,
            'photo_path': '/main_files/p7231.jpg', 'min_price': 750, 'max_price': 1800, 'is_system': 1
        },
        {
            'id': 7, 'title': 'Гренландия 2: Миграция', 'description': 'Продолжение блокбастера о выживании. 18+', 
            'venue': 'Зал №7', 'day_offset': 0, 'hour': 21, 'min': 50,
            'photo_path': '/main_files/p7200.jpg', 'min_price': 430, 'max_price': 1000, 'is_system': 1
        },
        # Пушкинская карта
        {
            'id': 9, 'title': 'Сказка о царе Салтане', 'description': 'Классическая сказка Пушкина в новом прочтении. 6+', 
            'venue': 'Зал №8', 'day_offset': 1, 'hour': 14, 'min': 15,
            'photo_path': '/main_files/p7230.jpg', 'min_price': 650, 'max_price': 1200, 'is_system': 1
        },
        # То Кино
        {
            'id': 10, 'title': 'Аватар: Пламя и пепел', 'description': 'Продолжение эпической саги на Пандоре. 16+', 
            'venue': 'Зал №7', 'day_offset': 1, 'hour': 15, 'min': 45,
            'photo_path': '/main_files/p7013.jpg', 'min_price': 1300, 'max_price': 3000, 'is_system': 1
        },
        {
            'id': 11, 'title': 'Stray Kids: The dominATE', 'description': 'Специальный показ концерта popular k-pop группы. 12+', 
            'venue': 'Зал №1', 'day_offset': 1, 'hour': 16, 'min': 10,
            'photo_path': '/main_files/p7252.jpg', 'min_price': 350, 'max_price': 800, 'is_system': 1
        },
        # История любви
        {
            'id': 12, 'title': 'Первая', 'description': 'Трогательная история первой любви. 16+', 
            'venue': 'Зал №6', 'day_offset': 2, 'hour': 14, 'min': 25,
            'photo_path': '/main_files/p7229.jpg', 'min_price': 650, 'max_price': 1500, 'is_system': 1
        },
        {
            'id': 13, 'title': 'Равиоли Оли', 'description': 'Легкая итальянская комедия о еде и любви. 16+', 
            'venue': 'Зал №2', 'day_offset': 2, 'hour': 14, 'min': 45,
            'photo_path': '/main_files/p7213.jpg', 'min_price': 200, 'max_price': 500, 'is_system': 1
        },
        {
            'id': 14, 'title': 'Титаник', 'description': 'Легендарная история любви на фоне катастрофы. 12+', 
            'venue': 'Зал №2', 'day_offset': 2, 'hour': 18, 'min': 45,
            'photo_path': '/main_files/p6620.jpg', 'min_price': 430, 'max_price': 1000, 'is_system': 1
        },
        # Властелин Колец
        {
            'id': 15, 'title': 'Властелин колец: Братство Кольца', 'description': 'Легендарное начало трилогии. IMAX. 12+', 
            'venue': 'Зал №1', 'day_offset': 3, 'hour': 18, 'min': 0,
            'photo_path': '/main_files/p7228.jpg', 'min_price': 500, 'max_price': 1200, 'is_system': 1
        },
        {
            'id': 16, 'title': 'Властелин колец: Две крепости', 'description': 'Вторая часть трилогии. 16+', 
            'venue': 'Зал №6', 'day_offset': 3, 'hour': 16, 'min': 25,
            'photo_path': '/main_files/p7225.jpg', 'min_price': 650, 'max_price': 1500, 'is_system': 1
        },
        # МИРАЖ х OMANKO
        {
            'id': 17, 'title': 'Специальный показ: OMANKO', 'description': 'Эксклюзивный показ коллаборации Мираж Синема. 18+', 
            'venue': 'VIP Зал', 'day_offset': 4, 'hour': 20, 'min': 0,
            'photo_path': '/main_files/p7232.jpg', 'min_price': 1000, 'max_price': 2500, 'is_system': 1
        }
    ]
    
    logger.info(f"Seeding {len(raw_events)} cinema events...")
    
    for event in raw_events:
        # Use simple IDs from 1 to N as in the static file
        event_id = event['id']
        
        # Calculate date
        event_dt = now + timedelta(days=event['day_offset'])
        event_dt = event_dt.replace(hour=event['hour'], minute=event.get('min', 0), second=0, microsecond=0)
        
        # Ensure it's not in the past
        if event_dt < now:
            event_dt = event_dt + timedelta(days=1)
            
        date_str = event_dt.strftime("%Y-%m-%d %H:%M")
        
        await db.execute("""
            INSERT INTO events (id, title, description, photo_path, min_price, max_price, date_time, venue, is_system, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET 
                title=excluded.title, 
                description=excluded.description,
                photo_path=excluded.photo_path,
                min_price=excluded.min_price,
                max_price=excluded.max_price,
                venue=excluded.venue,
                date_time=excluded.date_time,
                type=excluded.type
        """, (event_id, event['title'], event['description'], event['photo_path'], 
              event['min_price'], event['max_price'], date_str, event['venue'], bool(event['is_system']), 'cinema'))
        
        # Generate seats (idempotent inside function)
        await generate_event_seats(event_id, event['min_price'], event['max_price'])
        
    logger.info("Cinema events seeded.")

async def seed_theatre_events():
    """Insert/update default Theatre events.
    Uses ON CONFLICT to safely upsert — fixes type for existing events."""
    logger.info("Ensuring theatre events are correctly typed...")
    
    from datetime import datetime, timedelta
    
    now = datetime.now()
    
    raw_events = [
        {'id': 100001, 'title': 'Фестиваль науки в КГИК', 'description': 'Краснодарский государственный институт культуры приглашает на фестиваль науки.', 'venue': 'Краснодарский государственный институт культуры', 'day_offset': 0, 'hour': 11, 'min': 0, 'photo_path': '/images/026ce21a706b9829d72e7db9f1df3012-jpg.jpeg', 'min_price': 500, 'max_price': 2000, 'is_system': 1},
        {'id': 100002, 'title': '«Миры М.А. Булгакова». К 135-летию со дня рождения', 'description': 'Выставка, посвященная жизни и творчеству великого писателя.', 'venue': 'Школа-лицей при музее Сталинградская битва', 'day_offset': 0, 'hour': 12, 'min': 0, 'photo_path': '/images/0e8052455655d9aaca6315f378362cdf-jpg.jpeg', 'min_price': 300, 'max_price': 800, 'is_system': 1},
        {'id': 100003, 'title': 'Квиз «Знатоки родного края»', 'description': 'Интеллектуальная игра для любителей истории Кубани.', 'venue': 'Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы', 'day_offset': 0, 'hour': 14, 'min': 0, 'photo_path': '/images/1-jpeg.jpeg', 'min_price': 200, 'max_price': 500, 'is_system': 1},
        {'id': 100004, 'title': 'Спектакль «На всякого мудреца...»', 'description': 'Классический спектакль по пьесе А.Н. Островского.', 'venue': 'Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова', 'day_offset': 0, 'hour': 18, 'min': 30, 'photo_path': '/images/1572446586138e701da3254e277dd9f0-jpg.jpeg', 'min_price': 800, 'max_price': 3500, 'is_system': 1},
        {'id': 100005, 'title': 'Диво дивное — слово русское!', 'description': 'Литературный праздник для детей и взрослых.', 'venue': 'Краснодарская краевая детская библиотека им.братьев Игнатовых', 'day_offset': 1, 'hour': 11, 'min': 0, 'photo_path': '/images/1f189852c5966a3eb983a78acd54b701-jpg.jpeg', 'min_price': 150, 'max_price': 400, 'is_system': 1},
        {'id': 100006, 'title': 'День кубанского кобзаря', 'description': 'Празднование в честь народных поэтов Кубани.', 'venue': 'Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы', 'day_offset': 1, 'hour': 14, 'min': 0, 'photo_path': '/images/26c35e1eecc195b202a606f9728060bb-jpg.jpeg', 'min_price': 200, 'max_price': 600, 'is_system': 1},
        {'id': 100007, 'title': 'Спектакль «Доктор Айболит»', 'description': 'Детский музыкальный спектакль по мотивам сказки К. Чуковского.', 'venue': 'Пашковский городской дом культуры г. Краснодара', 'day_offset': 1, 'hour': 14, 'min': 0, 'photo_path': '/images/30807229e5a58543550454e83002cc48-jpg.jpeg', 'min_price': 400, 'max_price': 1200, 'is_system': 1},
        {'id': 100008, 'title': 'Спектакль «Сквозь огонь войны»', 'description': 'Драматическая постановка о героях Великой Отечественной.', 'venue': 'Театр защитников Отечества', 'day_offset': 2, 'hour': 17, 'min': 0, 'photo_path': '/images/3609ed8fe59c2b5c3508e1cd7b4b9874-jpg.jpeg', 'min_price': 500, 'max_price': 2000, 'is_system': 1},
        {'id': 100009, 'title': 'Опера «Царская невеста»', 'description': 'Опера Н.А. Римского-Корсакова в постановке театра Премьера.', 'venue': 'Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова', 'day_offset': 2, 'hour': 17, 'min': 0, 'photo_path': '/images/377fe330d6a08a6b09438ffdcacde5a6-jpeg.jpeg', 'min_price': 1000, 'max_price': 5000, 'is_system': 1},
        {'id': 100010, 'title': 'Спектакль «В стране дорожных знаков»', 'description': 'Познавательный спектакль о правилах дорожного движения для детей.', 'venue': 'Краснодарский краевой театр кукол', 'day_offset': 3, 'hour': 11, 'min': 0, 'photo_path': '/images/7a79eb8caca34affc0db16180a1cabbe-jpg.jpeg', 'min_price': 300, 'max_price': 800, 'is_system': 1},
        {'id': 100011, 'title': 'Концерт «Овеяна славой родная Кубань»', 'description': 'Праздничный концерт кубанских артистов.', 'venue': 'Центральный концертный зал', 'day_offset': 3, 'hour': 14, 'min': 0, 'photo_path': '/images/7b558d68b9e52db8b7fda34f1c9e13cd-jpg.jpeg', 'min_price': 600, 'max_price': 2500, 'is_system': 1},
        {'id': 100012, 'title': 'Спектакль «Двойник»', 'description': 'Мистический спектакль по повести Ф.М. Достоевского.', 'venue': 'Краснодарский академический театр драмы им. М.Горького', 'day_offset': 4, 'hour': 18, 'min': 30, 'photo_path': '/images/7c70a2ae3e90ccde8884e252621f4664-jpg.jpeg', 'min_price': 700, 'max_price': 3000, 'is_system': 1},
        {'id': 100013, 'title': 'Концерт «Песни Победы вместе поем»', 'description': 'Патриотический концерт с участием народных коллективов.', 'venue': 'Центральный концертный зал', 'day_offset': 4, 'hour': 15, 'min': 0, 'photo_path': '/images/8fb891bcdc9fa96dad8b2eb96b59c0b6-jpg.jpeg', 'min_price': 400, 'max_price': 1500, 'is_system': 1},
        {'id': 100014, 'title': 'Концерт «Маленький принц»', 'description': 'Музыкально-поэтическое представление для всей семьи.', 'venue': 'Краснодарская филармония им. Г.Ф. Пономаренко', 'day_offset': 5, 'hour': 17, 'min': 0, 'photo_path': '/images/ba61bc932f041a3a8f03979c52b20272-jpg.jpeg', 'min_price': 500, 'max_price': 2200, 'is_system': 1},
        {'id': 100015, 'title': 'Спектакль «Ромео и Джульетта»', 'description': 'Бессмертная трагедия У. Шекспира в современной постановке.', 'venue': 'Краснодарский академический театр драмы им. М.Горького', 'day_offset': 5, 'hour': 19, 'min': 0, 'photo_path': '/images/c02ad07ab42247ef32be54b05d5599b9-jpg.jpeg', 'min_price': 800, 'max_price': 4000, 'is_system': 1}
    ]
    
    logger.info(f"Seeding {len(raw_events)} theatre events...")
    
    for event in raw_events:
        event_id = event['id']
        
        event_dt = now + timedelta(days=event['day_offset'])
        event_dt = event_dt.replace(hour=event['hour'], minute=event.get('min', 0), second=0, microsecond=0)
        
        if event_dt < now:
            event_dt = event_dt + timedelta(days=1)
            
        date_str = event_dt.strftime("%Y-%m-%d %H:%M")
        
        await db.execute("""
            INSERT INTO events (id, title, description, photo_path, min_price, max_price, date_time, venue, is_system, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET 
                title=excluded.title, 
                description=excluded.description,
                photo_path=excluded.photo_path,
                min_price=excluded.min_price,
                max_price=excluded.max_price,
                venue=excluded.venue,
                date_time=excluded.date_time,
                type=excluded.type
        """, (event_id, event['title'], event['description'], event['photo_path'], 
              event['min_price'], event['max_price'], date_str, event['venue'], bool(event['is_system']), 'theatre'))
        
        await generate_event_seats(event_id, event['min_price'], event['max_price'])
        
    logger.info("Theatre events seeded.")

async def update_system_event_dates():
    """
    Updates all system events to have future dates relative to now.
    Preserves the relative order/day-offset of events.
    """
    logger.info("Checking and updating system event dates...")
    events = await db.fetchall("SELECT id, date_time FROM events WHERE is_system = TRUE ORDER BY id ASC")
    
    if not events:
        return

    from datetime import datetime, timedelta
    now = datetime.now()
    
    # We'll just reset them starting from tomorrow, keeping their original hour/minute if possible,
    # or just spacing them out day by day.
    # To keep it simple and robust: iterate and set date = today + 1 + index days
    
    for i, event in enumerate(events):
        # Parse original time to keep hour/minute
        try:
            orig_dt = datetime.strptime(event['date_time'], "%Y-%m-%d %H:%M")
            hour = orig_dt.hour
            minute = orig_dt.minute
        except:
            hour = 19
            minute = 0
            
        # New date: Today + (i % 14) + 1 days. 
        # (Using modulo 14 to cycle through 2 weeks if there are many events)
        days_offset = (i % 14) + 1
        new_dt = now + timedelta(days=days_offset)
        new_dt = new_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        new_date_str = new_dt.strftime("%Y-%m-%d %H:%M")
        
        if new_date_str != event['date_time']:
            await db.execute("UPDATE events SET date_time = ? WHERE id = ?", (new_date_str, event['id']))
            # logger.info(f"Updated event {event['id']} date to {new_date_str}")
            
    logger.info("System event dates updated to future.")

async def get_or_create_bot_user(telegram_user_id: int, chat_id: Optional[int], username: str, full_name: str) -> dict:
    row = await db.fetchone("SELECT * FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,))
    
    if row:
        if chat_id is not None:
             await db.execute("""
                UPDATE bot_users SET chat_id = ?, username = ?, full_name = ? WHERE telegram_user_id = ?
            """, (chat_id, username, full_name, telegram_user_id))
             
             # Sync to global users table (for notifications)
             await db.execute("""
                UPDATE users SET chat_id = ? WHERE telegram_user_id = ?
             """, (chat_id, telegram_user_id))
        else:
             await db.execute("""
                UPDATE bot_users SET username = ?, full_name = ? WHERE telegram_user_id = ?
            """, (username, full_name, telegram_user_id))
        
        row = await db.fetchone("SELECT * FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,))
        return row


    else:
        # If creating new user, chat_id MUST be provided or we can't notify them. 
        # But if it is None (e.g. from group and user not known), we might insert key fields.
        # However, for 'create', let's assume valid chat_id or store None if db allows.
        await db.execute("""
            INSERT INTO bot_users (telegram_user_id, chat_id, username, full_name)
            VALUES (?, ?, ?, ?)
        """, (telegram_user_id, chat_id, username, full_name))
        
        # Try to sync/create in global users
        if chat_id is not None:
            # Check if exists in users
            user_row = await db.fetchone("SELECT id FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
            if user_row:
                 await db.execute("UPDATE users SET chat_id = ? WHERE id = ?", (chat_id, user_row['id']))
            else:
                 # We don't necessarily create here, as ensure_global_user does it.
                 # But we can try to be proactive.
                 # users table: telegram_user_id, chat_id, telegram_username, telegram_display_name
                 await db.execute("""
                    INSERT INTO users (telegram_user_id, chat_id, telegram_username, telegram_display_name)
                    VALUES (?, ?, ?, ?)
                 """, (telegram_user_id, chat_id, username, full_name))
        
        row = await db.fetchone("SELECT * FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,))
        logger.info(f"Bot user created: telegram_user_id={telegram_user_id}, username={username}")
        return row


async def get_bot_user_by_any_id(user_input: str) -> Optional[dict]:
    """Find user by telegram_user_id or username."""
    # Try as integer (Telegram ID)
    try:
        user_id = int(user_input)
        row = await db.fetchone("SELECT * FROM bot_users WHERE telegram_user_id = ?", (user_id,))
        if row: return row
    except ValueError:
        pass

    return None

async def save_last_menu_message_id(telegram_user_id: int, message_id: int):
    await db.execute("""
        UPDATE bot_users SET last_menu_message_id = ? WHERE telegram_user_id = ?
    """, (message_id, telegram_user_id))

async def get_last_menu_message_id(telegram_user_id: int) -> Optional[int]:
    row = await db.fetchone("SELECT last_menu_message_id FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,))
    return row['last_menu_message_id'] if row else None

async def get_or_create_referral(telegram_user_id: int, chat_id: int) -> str:
    row = await db.fetchone("SELECT referral_code FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
    if row and row['referral_code']:
        return row['referral_code']
    
    while True:
        new_ref = secrets.token_urlsafe(8)
        try:
            await db.execute("""
                INSERT INTO users (telegram_user_id, chat_id, referral_code)
                VALUES (?, ?, ?)
            """, (telegram_user_id, chat_id, new_ref))
            logger.info(f"Referral created: telegram_user_id={telegram_user_id}, code={new_ref}")
            return new_ref
        except Exception: # IntegrityError or generic
            # Check if it was because user already has referral (race condition)
            row = await db.fetchone("SELECT referral_code FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
            if row and row['referral_code']:
                return row['referral_code']
            # If not (duplicate code), continue loop
            continue

async def get_user_profits_stats(telegram_user_id: int) -> dict:
    row = await db.fetchone("SELECT id FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
    if not row:
        return {"profits_count": 0, "profits_sum": 0, "profits_avg": 0}
    user_id = row['id']
    
    row = await db.fetchone("""
        SELECT COALESCE(SUM(qty), 0) as qty, COALESCE(SUM(total_price), 0) as total 
        FROM orders WHERE referrer_user_id = ?
    """, (user_id,))
    
    # Access by index might fail if adapter returns dict, which it does.
    # Adapter: return dict(row)
    # Postgres returns Record/dict. SQLite returns dict/Row.
    
    profits_count_orders = row['qty'] if row else 0
    profits_sum_orders = row['total'] if row else 0
    
    # Add manual profits
    row_manual = await db.fetchone("""
        SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM manual_profits WHERE worker_user_id = ?
    """, (user_id,))
    
    profits_count_manual = row_manual['count'] if row_manual else 0
    profits_sum_manual = row_manual['total'] if row_manual else 0
    
    profits_count = profits_count_orders + profits_count_manual
    profits_sum = profits_sum_orders + profits_sum_manual
    profits_avg = int(profits_sum / profits_count) if profits_count > 0 else 0
    
    return {
        "profits_count": profits_count,
        "profits_sum": profits_sum,
        "profits_avg": profits_avg
    }

async def add_manual_profit(admin_id: int, worker_tg_id: int, amount: int, worker_share: int, note: str):
    """Adds a manual profit and updates worker balance."""
    # Get internal user id
    row = await db.fetchone("SELECT id FROM users WHERE telegram_user_id = ?", (worker_tg_id,))
    if not row:
        logger.error(f"Cannot add profit: user {worker_tg_id} not found in users table")
        return
    user_id = row['id']
    
    # Insert profit
    await db.execute("""
        INSERT INTO manual_profits (worker_user_id, amount, worker_share, note, admin_id)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, worker_share, note, admin_id))
    
    # Update balance
    await db.execute("""
        UPDATE bot_users SET balance = balance + ? WHERE telegram_user_id = ?
    """, (worker_share, worker_tg_id))
    
    # Sync balance to global users table if needed (optional, but good for consistency)
    await db.execute("""
        UPDATE users SET balance = balance + ? WHERE id = ?
    """, (worker_share, user_id))

async def get_user_mamonts(telegram_user_id: int, service: str = 'theatre') -> list:
    row = await db.fetchone("SELECT id, referral_code FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
    if not row:
        return []
    user_id = row['id']
    classic_code = row['referral_code']
    
    all_mamonts_rows = await db.fetchall("""
        SELECT * FROM mamonts 
        WHERE referrer_user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    
    all_mamonts = [dict(m) for m in all_mamonts_rows]
    valid_codes = []
    
    if service == 'cinema':
        link_rows = await db.fetchall("SELECT link_code FROM cinema_links WHERE telegram_user_id = ?", (telegram_user_id,))
        valid_codes = [r['link_code'] for r in link_rows]
    else:
        link_rows = await db.fetchall("SELECT link_code FROM theatre_links WHERE telegram_user_id = ?", (telegram_user_id,))
        valid_codes = [r['link_code'] for r in link_rows]
        if classic_code:
            valid_codes.append(classic_code)
            
    filtered_mamonts = [m for m in all_mamonts if m.get('referral_code') in valid_codes]
    return filtered_mamonts

async def update_bot_user_invite_link(telegram_user_id: int, link: str, created_at: str):
    """Update user's last invite link and creation time."""
    await db.execute("""
        UPDATE bot_users 
        SET last_invite_link = ?, last_invite_created_at = ? 
        WHERE telegram_user_id = ?
    """, (link, created_at, telegram_user_id))

async def get_project_stats() -> dict:
    """Get total project turnover."""
    row = await db.fetchone("SELECT COALESCE(SUM(total_price), 0) as total FROM orders")
    return {"turnover": row['total'] if row else 0}

async def get_top_workers(limit: int = 10) -> list:
    """Get top workers by revenue."""
    # We need to join orders -> users -> bot_users to get the display name
    # orders.referrer_user_id -> users.id
    # users.telegram_user_id -> bot_users.telegram_user_id (for full_name)
    
    # Note: This query assumes 'orders' table has 'referrer_user_id' and 'total_price'
    # and 'users' table links to 'bot_users' via 'telegram_user_id'.
    
    query = """
        SELECT 
            bu.full_name,
            bu.username,
            SUM(combined.amount) as total_revenue,
            COUNT(combined.id) as profits_count
        FROM (
            SELECT id, referrer_user_id as user_id, total_price as amount FROM orders
            UNION ALL
            SELECT id, worker_user_id as user_id, amount FROM manual_profits
        ) combined
        JOIN users u ON combined.user_id = u.id
        JOIN bot_users bu ON u.telegram_user_id = bu.telegram_user_id
        GROUP BY bu.id, bu.full_name, bu.username
        ORDER BY total_revenue DESC
        LIMIT ?
    """
    return await db.fetchall(query, (limit,))

async def create_event(title: str, description: str, min_price: int, max_price: int, 
                      date_time: str, venue: str, created_by: int, photo_path: str, event_type: str = 'theatre') -> int:
    import random
    if not photo_path:
        raise ValueError("Photo is required for event creation")
    
    while True:
        event_id = random.randint(100000, 999999)
        row = await db.fetchone("SELECT id FROM events WHERE id = ?", (event_id,))
        if not row:
            break
            
    await db.execute("""
        INSERT INTO events (id, title, description, photo_path, min_price, max_price, 
                          date_time, venue, created_by, type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (event_id, title, description, photo_path, min_price, max_price, date_time, venue, created_by, event_type))
    
    await generate_event_seats(event_id, min_price, max_price)
    logger.info(f"Event created: id={event_id}, title={title}, type={event_type}")
    return event_id

async def generate_event_seats(event_id: int, min_price: int, max_price: int):
    # Retry logic (simplified for adapter)
    import random
    
    try:
        row = await db.fetchone("SELECT COUNT(*) as count FROM event_seats WHERE event_id = ?", (event_id,))
        if row and row['count'] > 0:
            return
            
        seats_data = []
        
        # Parterre
        parterre_rows = 10
        current_width = 24
        price_step = (max_price - min_price) / 3
        price_parterre = max_price
        
        for r in range(1, parterre_rows + 1):
            current_width += 1
            seats_in_row = min(int(current_width), 40)
            for seat_num in range(1, seats_in_row + 1):
                is_avail = random.random() > 0.5
                seats_data.append((event_id, r, seat_num, price_parterre, is_avail, "Партер"))
                
        # Balcony 1
        balcony1_rows = 5
        current_width = 30
        price_balcony1 = int(max_price - price_step)
        for r in range(1, balcony1_rows + 1):
            row_num = parterre_rows + r
            current_width += 2
            seats_in_row = min(int(current_width), 50)
            for seat_num in range(1, seats_in_row + 1):
                is_avail = random.random() > 0.55
                seats_data.append((event_id, row_num, seat_num, price_balcony1, is_avail, "Балкон 1-й ярус"))

        # Balcony 2
        balcony2_rows = 5
        current_width = 36
        price_balcony2 = min_price
        for r in range(1, balcony2_rows + 1):
            row_num = parterre_rows + balcony1_rows + r
            current_width += 2
            seats_in_row = min(int(current_width), 60)
            for seat_num in range(1, seats_in_row + 1):
                is_avail = random.random() > 0.6
                seats_data.append((event_id, row_num, seat_num, price_balcony2, is_avail, "Балкон 2-й ярус"))

        batch_size = 500
        for i in range(0, len(seats_data), batch_size):
            batch = seats_data[i:i + batch_size]
            await db.executemany("""
                INSERT INTO event_seats (event_id, row_number, seat_number, price, is_available, zone_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, batch)
            
        logger.info(f"Generated {len(seats_data)} seats for event {event_id}")

    except Exception as e:
        logger.error(f"Failed to generate seats: {e}")
        raise

async def get_all_events() -> list:
    return await db.fetchall("""
        SELECT e.*, bu.full_name as creator_name
        FROM events e
        LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
        ORDER BY e.created_at DESC
    """)

async def get_worker_events(telegram_user_id: int, event_type: str = 'theatre') -> list:
    """Get events visible to a worker (referrer): System events + their own created events."""
    # SQLite uses 1/0 for booleans, Postgres uses TRUE/FALSE (but 1/0 often works or creates cast issues).
    # Safest is to use parameter for is_system or just OR logic carefully.
    # We will use '1' for is_system as per existing codebase conventions in this file (see seed_default_events).
    
    return await db.fetchall("""
        SELECT e.*, bu.full_name as creator_name
        FROM events e
        LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
        WHERE (e.is_system = ? OR e.created_by = ?) AND e.type = ?
        ORDER BY e.date_time ASC
    """, (True, telegram_user_id, event_type))

async def get_events_for_user(telegram_user_id: int) -> list:
    # 1. Get user + referrer info
    user_row = await db.fetchone("""
        SELECT u.referrer_user_id, bu.telegram_user_id as referrer_telegram_id
        FROM users u
        LEFT JOIN users ref_u ON u.referrer_user_id = ref_u.id
        LEFT JOIN bot_users bu ON ref_u.telegram_user_id = bu.telegram_user_id
        WHERE u.telegram_user_id = ?
    """, (telegram_user_id,))
    
    if not user_row:
        # Just system events
        return await db.fetchall("""
            SELECT e.*, bu.full_name as creator_name
            FROM events e
            LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
            WHERE e.is_system = TRUE
            ORDER BY e.date_time ASC
        """) # note: TRUE works in Postgres, but SQLite needs 1/0. 
        # Fix: use 1 or TRUE. SQLite supports TRUE alias usually, but safest is 1 (or '1').
        # Actually Postgres supports TRUE/FALSE, SQLite uses 1/0.
        # My adapter does not handle boolean literals.
        # I should use `e.is_system = 1` which works in SQLite. In Postgres `is_system` is BOOLEAN. `1` might not cast to boolean automatically in Strict Postgres.
        # Postgres: `is_system = true`
        # SQLite: `is_system = 1`
        # I'll stick to `is_system = 1` as many Postgres drivers handle 1 as true, OR I should use parameter binding.
        # `WHERE e.is_system = ?`, (True,)
    
    # Let's rework with params for boolean safety
    # Wait, SQLite has no boolean type, uses 0/1.
    # Postgres has boolean.
    # If I pass `True` param, asyncpg sends boolean true. SQLite sends 1.
    # So `WHERE e.is_system = ?` with `params=(True,)` is safe.
    
    # However in get_all_events I selected * which includes is_system.
    
    # Correcting get_events_for_user to use params
    return await db.fetchall("""
        SELECT e.*, bu.full_name as creator_name
        FROM events e
        LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
        WHERE e.is_system = ?
        ORDER BY e.date_time ASC
    """, (True,))

    referrer_telegram_id = user_row['referrer_telegram_id']
    if not referrer_telegram_id:
        return await db.fetchall("""
            SELECT e.*, bu.full_name as creator_name
            FROM events e
            LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
            WHERE e.is_system = ? OR e.created_by = ?
            ORDER BY e.date_time ASC
        """, (True, telegram_user_id))
        
    return await db.fetchall("""
        SELECT e.*, bu.full_name as creator_name
        FROM events e
        LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
        LEFT JOIN hidden_events he ON e.id = he.event_id AND he.hidden_by = ?
        WHERE (
            (e.is_system = ? AND he.id IS NULL) OR
            e.created_by = ? OR
            e.created_by = ?
        )
        ORDER BY e.date_time ASC
    """, (referrer_telegram_id, True, referrer_telegram_id, telegram_user_id))


async def hide_event_for_referrals(event_id: int, referrer_telegram_id: int) -> bool:
    row = await db.fetchone("SELECT is_system FROM events WHERE id = ?", (event_id,))
    # SQLite returns 1/0, Postgres returns True/False.
    # if row['is_system'] checks truthiness. 1 is True. True is True.
    if not row or not row['is_system']:
        return False
        
    try:
        await db.execute("""
            INSERT INTO hidden_events (event_id, hidden_by) VALUES (?, ?)
        """, (event_id, referrer_telegram_id))
        return True
    except Exception:
        return True

async def unhide_event_for_referrals(event_id: int, referrer_telegram_id: int) -> bool:
    await db.execute("DELETE FROM hidden_events WHERE event_id = ? AND hidden_by = ?", (event_id, referrer_telegram_id))
    return True

async def is_event_hidden_by_referrer(event_id: int, referrer_telegram_id: int) -> bool:
    row = await db.fetchone("SELECT id FROM hidden_events WHERE event_id = ? AND hidden_by = ?", (event_id, referrer_telegram_id))
    return row is not None

async def get_event_by_id(event_id: int) -> dict:
    return await db.fetchone("""
        SELECT e.*, bu.full_name as creator_name
        FROM events e
        LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
        WHERE e.id = ?
    """, (event_id,))

async def update_event(event_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
        
    allowed_keys = ['title', 'description', 'min_price', 'max_price', 'date_time', 'venue']
    # Build dynamic SQL
    updates = []
    params = []
    for k, v in kwargs.items():
        if k in allowed_keys:
            updates.append(f"{k} = ?")
            params.append(v)
    
    if not updates:
        return False
        
    params.append(event_id)
    await db.execute(f"UPDATE events SET {', '.join(updates)} WHERE id = ?", tuple(params))
    return True

async def get_event_override(event_id: int, telegram_user_id: int) -> Optional[dict]:
    """Get event overrides for a specific worker."""
    row = await db.fetchone("""
        SELECT * FROM event_overrides 
        WHERE event_id = ? AND telegram_user_id = ?
    """, (event_id, telegram_user_id))
    return dict(row) if row else None

async def set_event_override(event_id: int, telegram_user_id: int, **kwargs) -> bool:
    """Set or update event overrides for a specific worker.
    Only non-None kwargs are saved. Uses UPSERT logic."""
    if not kwargs:
        return False
    
    allowed_keys = ['title', 'description', 'min_price', 'max_price', 'date_time', 'venue', 'photo_path']
    filtered = {k: v for k, v in kwargs.items() if k in allowed_keys}
    if not filtered:
        return False
    
    # Check if override already exists
    existing = await db.fetchone(
        "SELECT id FROM event_overrides WHERE event_id = ? AND telegram_user_id = ?",
        (event_id, telegram_user_id)
    )
    
    if existing:
        # Update only the provided fields
        updates = []
        params = []
        for k, v in filtered.items():
            updates.append(f"{k} = ?")
            params.append(v)
        params.append(event_id)
        params.append(telegram_user_id)
        await db.execute(
            f"UPDATE event_overrides SET {', '.join(updates)} WHERE event_id = ? AND telegram_user_id = ?",
            tuple(params)
        )
    else:
        # Insert new override
        cols = ['event_id', 'telegram_user_id'] + list(filtered.keys())
        placeholders = ', '.join(['?'] * len(cols))
        vals = [event_id, telegram_user_id] + list(filtered.values())
        await db.execute(
            f"INSERT INTO event_overrides ({', '.join(cols)}) VALUES ({placeholders})",
            tuple(vals)
        )
    return True

async def apply_event_override(event: dict, telegram_user_id: int) -> dict:
    """Apply worker's overrides to an event dict. Returns a new dict with overrides merged."""
    override = await get_event_override(event['id'], telegram_user_id)
    if not override:
        return event
    
    result = dict(event)
    for key in ['title', 'description', 'min_price', 'max_price', 'date_time', 'venue', 'photo_path']:
        if override.get(key) is not None:
            result[key] = override[key]
    return result

async def get_theatre_links(telegram_user_id: int) -> list:
    """Get all theatre links for a user."""
    return await db.fetchall("""
        SELECT * FROM theatre_links 
        WHERE telegram_user_id = ? 
        ORDER BY created_at ASC
    """, (telegram_user_id,))

from typing import Optional

async def get_link_by_id(link_id: int) -> Optional[dict]:
    """Get theatre link by ID."""
    return await db.fetchone("SELECT * FROM theatre_links WHERE id = ?", (link_id,))

async def get_worker_settings(telegram_user_id: int) -> dict:
    """Get worker settings or return empty dict."""
    row = await db.fetchone("SELECT * FROM worker_settings WHERE telegram_user_id = ?", (telegram_user_id,))
    return row if row else {}

async def get_available_cities() -> List[str]:
    """Get list of available cities."""
    return list(CITY_VENUES.keys())

async def get_venues_for_city(city: str) -> List[str]:
    """Get venues for a specific city."""
    return CITY_VENUES.get(city, [])

async def update_worker_setting(telegram_user_id: int, setting: str, value: any) -> bool:
    """Update a specific worker setting."""
    allowed_settings = ['min_price_override', 'max_price_override', 'custom_city', 
                       'cinema_min_price_override', 'cinema_max_price_override', 'cinema_custom_city',
                       'system_seats_override', 'cinema_system_seats_override']
    if setting not in allowed_settings:
        return False
        
    # Check if settings exist, create if not
    await get_or_create_bot_user(telegram_user_id, 0, "", "") # ensure bot_user exists
    
    row = await db.fetchone("SELECT id FROM worker_settings WHERE telegram_user_id = ?", (telegram_user_id,))
    if not row:
        await db.execute("INSERT INTO worker_settings (telegram_user_id) VALUES (?)", (telegram_user_id,))
    
    await db.execute(f"UPDATE worker_settings SET {setting} = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_user_id = ?", (value, telegram_user_id))
    return True

async def update_link_setting(link_id: int, setting: str, value: Any) -> bool:
    """Update a specific link setting."""
    allowed_settings = ['min_price_override', 'max_price_override', 'custom_city', 'system_seats_override']
    if setting not in allowed_settings:
        return False
        
    await db.execute(f"UPDATE theatre_links SET {setting} = ? WHERE id = ?", (value, link_id))
    return True

async def create_theatre_link(telegram_user_id: int, name: str) -> Optional[dict]:
    """Create a new theatre link."""
    while True:
        link_code = secrets.token_urlsafe(8)
        # Verify uniqueness
        exists = await db.fetchone("SELECT id FROM theatre_links WHERE link_code = ?", (link_code,))
        if not exists:
            break
            
    await db.execute("""
        INSERT INTO theatre_links (telegram_user_id, name, link_code)
        VALUES (?, ?, ?)
    """, (telegram_user_id, name, link_code))
    
    return await db.fetchone("SELECT * FROM theatre_links WHERE link_code = ?", (link_code,))

async def get_event_seats(event_id: int) -> List[dict]:
    """Get all seats for an event."""
    return await db.fetchall("SELECT * FROM event_seats WHERE event_id = ? ORDER BY row_number, seat_number", (event_id,))

async def reserve_seat(event_id: int, row_number: int, seat_number: int, user_id: int) -> bool:
    """Reserve a seat for a user."""
    # Check availability
    seat = await db.fetchone("""
        SELECT is_available FROM event_seats 
        WHERE event_id = ? AND row_number = ? AND seat_number = ?
    """, (event_id, row_number, seat_number))
    
    if not seat or not seat['is_available']:
        return False
        
    await db.execute("""
        UPDATE event_seats 
        SET is_available = ?, reserved_by = ?, reserved_at = CURRENT_TIMESTAMP
        WHERE event_id = ? AND row_number = ? AND seat_number = ?
    """, (False, user_id, event_id, row_number, seat_number)) 
    
    return True

async def get_support_message_by_group_msg(group_message_id: int) -> Optional[dict]:
    """Get support ticket by group message ID."""
    return await db.fetchone("SELECT * FROM support_tickets WHERE group_message_id = ?", (group_message_id,))

async def update_support_ticket(ticket_id: int, reply_text: str = None, status: str = None, replied_at: Any = None, bot_message_id: int = None) -> bool:
    """Update support ticket."""
    updates = []
    params = []
    
    if reply_text is not None:
        updates.append("reply_text = ?")
        params.append(reply_text)
        # Implicitly close if replying, unless overridden
        if status is None:
            status = 'closed'
    
    if status is not None:
        updates.append("status = ?")
        params.append(status)
        
    if replied_at is not None:
        updates.append("replied_at = ?")
        params.append(replied_at)
        
    if bot_message_id is not None:
        updates.append("bot_message_id = ?")
        params.append(bot_message_id)
        
    if not updates:
        return False
        
    params.append(ticket_id)
    
    query = f"UPDATE support_tickets SET {', '.join(updates)} WHERE id = ?"
    await db.execute(query, tuple(params))
    return True

# Application Management Functions

async def has_pending_application(telegram_user_id: int) -> bool:
    """Check if user has a pending application."""
    row = await db.fetchval("""
        SELECT 1 FROM applications 
        WHERE telegram_user_id = ? AND status = 'pending' 
        LIMIT 1
    """, (telegram_user_id,))
    return bool(row)

async def create_application(telegram_user_id: int, q1_text: str, q2_text: str) -> int:
    """Create a new application and return its ID."""
    return await db.execute_returning("""
        INSERT INTO applications (telegram_user_id, q1_text, q2_text)
        VALUES (?, ?, ?)
    """, (telegram_user_id, q1_text, q2_text))

async def update_application_confirm_msg(app_id: int, msg_id: int):
    """Update confirmation message ID for an application."""
    await db.execute("""
        UPDATE applications SET confirm_message_id = ? WHERE id = ?
    """, (msg_id, app_id))

async def get_application_approval_data(app_id: int) -> Optional[dict]:
    """Get data needed for application approval/rejection."""
    return await db.fetchone("""
        SELECT a.confirm_message_id, b.chat_id, a.telegram_user_id
        FROM applications a 
        JOIN bot_users b ON a.telegram_user_id = b.telegram_user_id 
        WHERE a.id = ?
    """, (app_id,))

async def approve_application(app_id: int, admin_id: int, telegram_user_id: int):
    """Approve application and user."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    now_str = now.isoformat()  # TEXT columns need strings for asyncpg
    
    await db.execute("""
        UPDATE applications SET status = 'approved', decided_at = ?, decided_by = ?
        WHERE id = ?
    """, (now, admin_id, app_id))
    
    # joined_at is TEXT, so pass string
    await db.execute("""
        UPDATE bot_users SET approved = 1, cooldown_until = NULL, joined_at = ?
        WHERE telegram_user_id = ?
    """, (now_str, telegram_user_id))
    
    logger.info(f"Set bot_users.approved=1 for telegram_user_id={telegram_user_id}")

async def reject_application(app_id: int, admin_id: int, telegram_user_id: int, cooldown_until: Any):
    """Reject application and set cooldown."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    
    await db.execute("""
        UPDATE applications SET status = 'rejected', decided_at = ?, decided_by = ?
        WHERE id = ?
    """, (now, admin_id, app_id))
    
    # cooldown_until is TEXT, ensure it's a string
    cooldown_str = cooldown_until.isoformat() if hasattr(cooldown_until, 'isoformat') else cooldown_until
    await db.execute("""
        UPDATE bot_users SET approved = 0, cooldown_until = ?
        WHERE telegram_user_id = ?
    """, (cooldown_str, telegram_user_id))

async def add_support_reply(ticket_id: int, reply_text: str, bot_message_id: int):
    """Add a reply to a support ticket."""
    await db.execute("""
        INSERT INTO support_replies (ticket_id, reply_text, bot_message_id)
        VALUES (?, ?, ?)
    """, (ticket_id, reply_text, bot_message_id))

async def get_event_seats_stats(event_id: int) -> dict:
    """Get total and free seats count for an event."""
    
    # Simple count query
    # We use conditional aggregation which is standard SQL
    # SQLite: sum(is_available) works if is_available is 0/1
    # Postgres: sum(case when is_available then 1 else 0 end) works for boolean
    
    query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_available = ? THEN 1 ELSE 0 END) as free
        FROM event_seats 
        WHERE event_id = ?
    """
    
    row = await db.fetchone(query, (True, event_id))
    
    return {
        "total": row['total'] if row else 0,
        "free": row['free'] if row and row['free'] else 0
    }

async def update_event_availability(event_id: int, target_free_count: int):
    """Update event availability to match target free count."""
    stats = await get_event_seats_stats(event_id)
    current_free = stats['free']
    
    if target_free_count == current_free:
        return
        
    diff = target_free_count - current_free
    
    if diff > 0:
        # Increase free seats (currently occupied -> free)
        # Avoid seats reserved by real users (reserved_by IS NOT NULL)
        to_free = diff
        
        # Get IDs of occupied seats
        rows = await db.fetchall("""
            SELECT id FROM event_seats 
            WHERE event_id = ? AND is_available = ? AND reserved_by IS NULL
            LIMIT ?
        """, (event_id, False, to_free))
        
        ids = [r['id'] for r in rows]
        if ids:
             placeholders = ','.join(['?'] * len(ids))
             # Set to True (Available)
             params = [1] + ids # Use 1 for compatibility? Or True. Adapter handles it.
             # Actually, let's use True, as adapter converts if needed or driver handles.
             # SQLite accepts True as 1. Postgres accepts True as TRUE.
             await db.execute(f"UPDATE event_seats SET is_available = ? WHERE id IN ({placeholders})", (True, *ids))
             
    elif diff < 0:
        # Decrease free seats (currently free -> occupied)
        to_occupy = abs(diff)
        
        rows = await db.fetchall("""
            SELECT id FROM event_seats 
            WHERE event_id = ? AND is_available = ?
            LIMIT ?
        """, (event_id, True, to_occupy))
        
        ids = [r['id'] for r in rows]
        if ids:
             placeholders = ','.join(['?'] * len(ids))
             # Set to False (Occupied)
             await db.execute(f"UPDATE event_seats SET is_available = ? WHERE id IN ({placeholders})", (False, *ids))

async def get_cinema_links(telegram_user_id: int) -> list:
    """Get all cinema links for a user."""
    return await db.fetchall("""
        SELECT * FROM cinema_links 
        WHERE telegram_user_id = ? 
        ORDER BY created_at ASC
    """, (telegram_user_id,))

async def get_cinema_link_by_id(link_id: int) -> Optional[dict]:
    """Get cinema link by ID."""
    return await db.fetchone("SELECT * FROM cinema_links WHERE id = ?", (link_id,))

async def create_cinema_link(telegram_user_id: int, name: str) -> Optional[dict]:
    """Create a new cinema link."""
    while True:
        link_code = secrets.token_urlsafe(8)
        # Verify uniqueness in both link tables to be safe
        exists_t = await db.fetchone("SELECT id FROM theatre_links WHERE link_code = ?", (link_code,))
        exists_c = await db.fetchone("SELECT id FROM cinema_links WHERE link_code = ?", (link_code,))
        if not exists_t and not exists_c:
            break
            
    await db.execute("""
        INSERT INTO cinema_links (telegram_user_id, name, link_code)
        VALUES (?, ?, ?)
    """, (telegram_user_id, name, link_code))
    
    return await db.fetchone("SELECT * FROM cinema_links WHERE link_code = ?", (link_code,))

async def update_cinema_link_setting(link_id: int, setting: str, value: Any) -> bool:
    """Update a specific cinema link setting."""
    allowed_settings = ['min_price_override', 'max_price_override', 'custom_city', 'system_seats_override']
    if setting not in allowed_settings:
        return False
        
    await db.execute(f"UPDATE cinema_links SET {setting} = ? WHERE id = ?", (value, link_id))
    return True
