
from typing import Optional, List
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

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

    # Worker settings
    await db.execute("""
        CREATE TABLE IF NOT EXISTS worker_settings (
            id SERIAL PRIMARY KEY,
            telegram_user_id BIGINT UNIQUE NOT NULL REFERENCES bot_users(telegram_user_id),
            min_price_override INTEGER DEFAULT NULL,
            max_price_override INTEGER DEFAULT NULL,
            custom_city TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            replied_at TIMESTAMP
        )
    """)

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
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # SQLite Migrations
    async def add_column_if_missing(table, column, definition):
        try:
            await db.execute(f"SELECT {column} FROM {table} LIMIT 1")
        except Exception:
            logger.info(f"Migrating: Adding {column} to {table}...")
            try:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            except Exception as e:
                logger.error(f"Migration error: {e}")

    await add_column_if_missing("bot_users", "joined_at", "TEXT")
    await add_column_if_missing("bot_users", "balance", "INTEGER DEFAULT 0")
    await add_column_if_missing("bot_users", "last_menu_message_id", "INTEGER")
    await add_column_if_missing("applications", "confirm_message_id", "INTEGER")
    await add_column_if_missing("event_seats", "zone_name", "TEXT")
    await add_column_if_missing("worker_settings", "max_price_override", "INTEGER DEFAULT NULL")
    await add_column_if_missing("deposits", "requisites", "TEXT")
    await add_column_if_missing("deposits", "bank_name", "TEXT")
    await add_column_if_missing("deposits", "exact_amount", "INTEGER")
    await add_column_if_missing("deposits", "group_message_id", "INTEGER")
    await add_column_if_missing("deposits", "expires_at", "TIMESTAMP")


async def seed_default_events():
    """Insert default events if the events table is empty."""
    # Data is retained from original file
    default_events = [
        {'id': 100001, 'title': 'Фестиваль науки в КГИК', 'description': 'Краснодарский государственный институт культуры приглашает на фестиваль науки. Увлекательные эксперименты, мастер-классы и лекции.', 'venue': 'Краснодарский государственный институт культуры', 'date_time': '2026-02-06 11:00', 'photo_path': '/images/7c70a2ae3e90ccde8884e252621f4664-jpg.jpeg', 'min_price': 500, 'max_price': 2000, 'is_system': 1},
        {'id': 100002, 'title': '«Миры М.А. Булгакова». К 135-летию со дня рождения', 'description': 'Выставка, посвященная жизни и творчеству великого писателя.', 'venue': 'Школа-лицей при музее Сталинградская битва', 'date_time': '2026-03-13 12:00', 'photo_path': '/images/ef8aff0f5d4d637224a0e87b97675ceb-jpg.jpeg', 'min_price': 300, 'max_price': 800, 'is_system': 1},
        {'id': 100003, 'title': 'Квиз «Знатоки родного края»', 'description': 'Интеллектуальная игра для любителей истории Кубани.', 'venue': 'Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы', 'date_time': '2026-02-04 14:00', 'photo_path': '/images/3609ed8fe59c2b5c3508e1cd7b4b9874-jpg.jpeg', 'min_price': 200, 'max_price': 500, 'is_system': 1},
        {'id': 100004, 'title': 'Спектакль «На всякого мудреца...»', 'description': 'Классический спектакль по пьесе А.Н. Островского.', 'venue': 'Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова', 'date_time': '2026-02-04 18:30', 'photo_path': '/images/ba61bc932f041a3a8f03979c52b20272-jpg.jpeg', 'min_price': 800, 'max_price': 3500, 'is_system': 1},
        {'id': 100005, 'title': 'Диво дивное — слово русское!', 'description': 'Литературный праздник для детей и взрослых.', 'venue': 'Краснодарская краевая детская библиотека им.братьев Игнатовых', 'date_time': '2026-02-05 11:00', 'photo_path': '/images/026ce21a706b9829d72e7db9f1df3012-jpg.jpeg', 'min_price': 150, 'max_price': 400, 'is_system': 1},
        {'id': 100006, 'title': 'День кубанского кобзаря', 'description': 'Празднование в честь народных поэтов Кубани.', 'venue': 'Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы', 'date_time': '2026-02-05 14:00', 'photo_path': '/images/1f189852c5966a3eb983a78acd54b701-jpg.jpeg', 'min_price': 200, 'max_price': 600, 'is_system': 1},
        {'id': 100007, 'title': 'Спектакль «Доктор Айболит»', 'description': 'Детский музыкальный спектакль по мотивам сказки К. Чуковского.', 'venue': 'Пашковский городской дом культуры г. Краснодара', 'date_time': '2026-02-07 14:00', 'photo_path': '/images/7a79eb8caca34affc0db16180a1cabbe-jpg.jpeg', 'min_price': 400, 'max_price': 1200, 'is_system': 1},
        {'id': 100008, 'title': 'Спектакль «Сквозь огонь войны»', 'description': 'Драматическая постановка о героях Великой Отечественной.', 'venue': 'Театр защитников Отечества', 'date_time': '2026-02-08 17:00', 'photo_path': '/images/f16886979b66cfad60fd2df83def6f17-jpg.jpeg', 'min_price': 500, 'max_price': 2000, 'is_system': 1},
        {'id': 100009, 'title': 'Опера «Царская невеста»', 'description': 'Опера Н.А. Римского-Корсакова в постановке театра Премьера.', 'venue': 'Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова', 'date_time': '2026-02-10 17:00', 'photo_path': '/images/c02ad07ab42247ef32be54b05d5599b9-jpg.jpeg', 'min_price': 1000, 'max_price': 5000, 'is_system': 1},
        {'id': 100010, 'title': 'Спектакль «В стране дорожных знаков»', 'description': 'Познавательный спектакль о правилах дорожного движения для детей.', 'venue': 'Краснодарский краевой театр кукол', 'date_time': '2026-02-12 11:00', 'photo_path': '/images/8fb891bcdc9fa96dad8b2eb96b59c0b6-jpg.jpeg', 'min_price': 300, 'max_price': 800, 'is_system': 1},
        {'id': 100011, 'title': 'Концерт «Овеяна славой родная Кубань»', 'description': 'Праздничный концерт кубанских артистов.', 'venue': 'Центральный концертный зал', 'date_time': '2026-02-12 14:00', 'photo_path': '/images/30807229e5a58543550454e83002cc48-jpg.jpeg', 'min_price': 600, 'max_price': 2500, 'is_system': 1},
        {'id': 100012, 'title': 'Спектакль «Двойник»', 'description': 'Мистический спектакль по повести Ф.М. Достоевского.', 'venue': 'Краснодарский академический театр драмы им. М.Горького', 'date_time': '2026-02-15 18:30', 'photo_path': '/images/7b558d68b9e52db8b7fda34f1c9e13cd-jpg.jpeg', 'min_price': 700, 'max_price': 3000, 'is_system': 1},
        {'id': 100013, 'title': 'Концерт «Песни Победы вместе поем»', 'description': 'Патриотический концерт с участием народных коллективов.', 'venue': 'Центральный концертный зал', 'date_time': '2026-02-14 15:00', 'photo_path': '/images/377fe330d6a08a6b09438ffdcacde5a6-jpeg.jpeg', 'min_price': 400, 'max_price': 1500, 'is_system': 1},
        {'id': 100014, 'title': 'Концерт «Маленький принц»', 'description': 'Музыкально-поэтическое представление для всей семьи.', 'venue': 'Краснодарская филармония им. Г.Ф. Пономаренко', 'date_time': '2026-02-14 17:00', 'photo_path': '/images/eee6882fc7dbf38e0b0a91316c613588-jpg.jpeg', 'min_price': 500, 'max_price': 2200, 'is_system': 1},
        {'id': 100015, 'title': 'Спектакль «Ромео и Джульетта»', 'description': 'Бессмертная трагедия У. Шекспира в современной постановке.', 'venue': 'Краснодарский академический театр драмы им. М.Горького', 'date_time': '2026-02-17 19:00', 'photo_path': '/images/fe9ffccbd3facaf5a096422d8e8b353c-jpg.jpeg', 'min_price': 800, 'max_price': 4000, 'is_system': 1}
    ]
    
    logger.info("Seeding default events...")
    
    for event in default_events:
        await db.execute("""
            INSERT INTO events (id, title, description, photo_path, min_price, max_price, date_time, venue, is_system)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event['id'], event['title'], event['description'], event['photo_path'], 
              event['min_price'], event['max_price'], event['date_time'], event['venue'], bool(event['is_system'])))
    
    # Generate seats for each event
    for event in default_events:
         await generate_event_seats(event['id'], event['min_price'], event['max_price'])

async def get_or_create_bot_user(telegram_user_id: int, chat_id: int, username: str, full_name: str) -> dict:
    row = await db.fetchone("SELECT * FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,))
    
    if row:
        await db.execute("""
            UPDATE bot_users SET chat_id = ?, username = ?, full_name = ? WHERE telegram_user_id = ?
        """, (chat_id, username, full_name, telegram_user_id))
        
        row = await db.fetchone("SELECT * FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,))
        return row
    else:
        await db.execute("""
            INSERT INTO bot_users (telegram_user_id, chat_id, username, full_name)
            VALUES (?, ?, ?, ?)
        """, (telegram_user_id, chat_id, username, full_name))
        
        row = await db.fetchone("SELECT * FROM bot_users WHERE telegram_user_id = ?", (telegram_user_id,))
        logger.info(f"Bot user created: telegram_user_id={telegram_user_id}, username={username}")
        return row

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
    
    profits_count = row['qty'] if row else 0
    profits_sum = row['total'] if row else 0
    profits_avg = int(profits_sum / profits_count) if profits_count > 0 else 0
    
    return {
        "profits_count": profits_count,
        "profits_sum": profits_sum,
        "profits_avg": profits_avg
    }

async def get_user_mamonts(telegram_user_id: int) -> list:
    row = await db.fetchone("SELECT id FROM users WHERE telegram_user_id = ?", (telegram_user_id,))
    if not row:
        return []
    user_id = row['id']
    
    return await db.fetchall("""
        SELECT * FROM mamonts 
        WHERE referrer_user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))

async def create_event(title: str, description: str, min_price: int, max_price: int, 
                      date_time: str, venue: str, created_by: int, photo_path: str) -> int:
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
                          date_time, venue, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (event_id, title, description, photo_path, min_price, max_price, date_time, venue, created_by))
    
    await generate_event_seats(event_id, min_price, max_price)
    logger.info(f"Event created: id={event_id}, title={title}")
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
    allowed_settings = ['min_price_override', 'max_price_override', 'custom_city']
    if setting not in allowed_settings:
        return False
        
    # Check if settings exist, create if not
    await get_or_create_bot_user(telegram_user_id, 0, "", "") # ensure bot_user exists
    
    row = await db.fetchone("SELECT id FROM worker_settings WHERE telegram_user_id = ?", (telegram_user_id,))
    if not row:
        await db.execute("INSERT INTO worker_settings (telegram_user_id) VALUES (?)", (telegram_user_id,))
    
    await db.execute(f"UPDATE worker_settings SET {setting} = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_user_id = ?", (value, telegram_user_id))
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

async def update_support_ticket(ticket_id: int, reply_text: str, replied_at: str) -> bool:
    """Update support ticket with reply."""
    await db.execute("""
        UPDATE support_tickets 
        SET reply_text = ?, replied_at = ?, status = 'closed'
        WHERE id = ?
    """, (reply_text, replied_at, ticket_id))
    return True

# Application Management Functions

async def create_application(telegram_user_id: int, q1_text: str, q2_text: str) -> int:
    """Create a new application and return its ID."""
    if db.is_postgres:
        row = await db.fetchone("""
            INSERT INTO applications (telegram_user_id, q1_text, q2_text)
            VALUES (?, ?, ?)
            RETURNING id
        """, (telegram_user_id, q1_text, q2_text))
        return row['id']
    else:
        # For SQLite, we use cursor.lastrowid
        cursor = await db.execute("""
            INSERT INTO applications (telegram_user_id, q1_text, q2_text)
            VALUES (?, ?, ?)
        """, (telegram_user_id, q1_text, q2_text))
        return cursor.lastrowid

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
    now_iso = datetime.now(timezone.utc).isoformat()
    
    await db.execute("""
        UPDATE applications SET status = 'approved', decided_at = ?, decided_by = ?
        WHERE id = ?
    """, (now_iso, admin_id, app_id))
    
    # Using integer 1 for compatibility with SQLite and Postgres (if column is INTEGER)
    await db.execute("""
        UPDATE bot_users SET approved = 1, cooldown_until = NULL, joined_at = ?
        WHERE telegram_user_id = ?
    """, (now_iso, telegram_user_id))
    
    logger.info(f"Set bot_users.approved=1 for telegram_user_id={telegram_user_id}")

async def reject_application(app_id: int, admin_id: int, telegram_user_id: int, cooldown_iso: str):
    """Reject application and set cooldown."""
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat()
    
    await db.execute("""
        UPDATE applications SET status = 'rejected', decided_at = ?, decided_by = ?
        WHERE id = ?
    """, (now_iso, admin_id, app_id))
    
    await db.execute("""
        UPDATE bot_users SET approved = 0, cooldown_until = ?
        WHERE telegram_user_id = ?
    """, (cooldown_iso, telegram_user_id))
