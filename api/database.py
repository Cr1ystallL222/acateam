
from data.db import db, logger

async def ensure_schema():
    """Ensures that the database schema is up to date."""
    logger.info(f"Checking database schema in {db.mode} mode...")

    if db.mode == "sqlite":
        await _ensure_sqlite_schema()
    else:
        await _ensure_postgres_schema()
        
    # Seed default events if table is empty (for both modes)
    # Check if events table exists first (it should)
    try:
        row = await db.fetchone("SELECT COUNT(*) as count FROM events")
        if row and row['count'] == 0:
            await seed_default_events()
    except Exception as e:
        logger.error(f"Failed to check/seed events: {e}")

async def _ensure_postgres_schema():
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

    # Bot Users
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

    # Event Seats
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

    # Hidden Events
    await db.execute("""
        CREATE TABLE IF NOT EXISTS hidden_events (
            id SERIAL PRIMARY KEY,
            event_id INTEGER NOT NULL REFERENCES events(id),
            hidden_by BIGINT NOT NULL REFERENCES bot_users(telegram_user_id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, hidden_by)
        )
    """)

    # Worker Settings
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
    
    # Theatre Links
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

    # Applications
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

    # Support Tickets
    await db.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            telegram_user_id BIGINT,
            message TEXT NOT NULL,
            reply_text TEXT,
            status TEXT DEFAULT 'open',
            group_message_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            replied_at TIMESTAMP,
            attachment_path TEXT,
            mamont_id TEXT,
            user_read BOOLEAN DEFAULT FALSE
        )
    """)
    
    # Migrations
    try:
        await db.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS telegram_user_id BIGINT")
    except Exception as e:
        logger.info(f"Migration note (telegram_user_id): {e}")

    try:
        await db.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS attachment_path TEXT")
    except Exception as e:
        logger.info(f"Migration note (attachment_path): {e}")

    try:
        await db.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS mamont_id TEXT")
    except Exception as e:
        logger.info(f"Migration note (mamont_id): {e}")

    try:
        await db.execute("ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS user_read BOOLEAN DEFAULT FALSE")
    except Exception as e:
        logger.info(f"Migration note (user_read): {e}")
    
    logger.info("Postgres schema initialized.")

async def _ensure_sqlite_schema():
    await db.execute("PRAGMA journal_mode = WAL")
    await db.execute("PRAGMA busy_timeout = 30000")

    # ... (rest of sqlite tables) ...

    # Users
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
            balance INTEGER DEFAULT 0,
            FOREIGN KEY(referrer_user_id) REFERENCES users(id)
        )
    """)

    # Bot Users
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
    
    # Registration Sessions
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

    # Events
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

    # Event Seats
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

    # Hidden Events
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

    # Worker Settings
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

    # Theatre Links
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

    # Applications
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

    # Visits
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

    # Orders
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
    
    # Mamonts (visitor tracking)
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(referrer_user_id) REFERENCES users(id)
        )
    """)

    # Deposits
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

    # Support Tickets
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
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Migrations (Generic wrapper for SQLite only)
    async def add_column_if_missing(table, column, definition):
        try:
            # Simple check
            await db.execute(f"SELECT {column} FROM {table} LIMIT 1")
        except Exception:
            logger.info(f"Migrating: Adding {column} to {table}...")
            try:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            except Exception as e:
                logger.error(f"Migration error for {table}.{column}: {e}")

    await add_column_if_missing("users", "referrer_user_id", "INTEGER REFERENCES users(id)")
    await add_column_if_missing("users", "telegram_username", "TEXT")
    await add_column_if_missing("users", "balance", "INTEGER DEFAULT 0")
    await add_column_if_missing("event_seats", "zone_name", "TEXT") 
    
    await add_column_if_missing("support_tickets", "attachment_path", "TEXT")
    await add_column_if_missing("support_tickets", "mamont_id", "TEXT")
    await add_column_if_missing("support_tickets", "user_read", "BOOLEAN DEFAULT FALSE") 

async def seed_default_events():
    """Insert default events if the events table is empty."""
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
    # We need to replicate generate_event_seats logic here briefly or import it
    # Since importing from bots.database causes circular import potentially (bots.database imports data.db)
    # I will inline the seat generation logic to keep api/database.py self-contained
    
    import random
    
    for event in default_events:
        event_id = event['id']
        min_price = event['min_price']
        max_price = event['max_price']
        
        # Check seats
        row = await db.fetchone("SELECT COUNT(*) as count FROM event_seats WHERE event_id = ?", (event_id,))
        if row and row['count'] > 0:
            continue

        seats_data = []
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

