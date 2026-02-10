import aiosqlite
import secrets
from typing import Optional
from .config import DB_PATH, logger

async def ensure_bot_schema():
    """Create bot-specific tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Enable WAL mode for better concurrency
        await db.execute("PRAGMA journal_mode = WAL")
        await db.execute("PRAGMA busy_timeout = 30000")  # 30 seconds timeout
        
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
        
        # Hidden events table - for referrers who hide system events from their referrals
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
        
        # Worker settings table - for customization per worker (referrer)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS worker_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER UNIQUE NOT NULL,
                
                -- Price settings (min and max price for seats)
                min_price_override INTEGER DEFAULT NULL,
                max_price_override INTEGER DEFAULT NULL,
                
                -- City customization
                custom_city TEXT DEFAULT NULL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY(telegram_user_id) REFERENCES bot_users(telegram_user_id)
            )
        """)
        
        # Theatre links table - multiple referral links per user with individual settings
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
        
        # Add new columns to event_seats
        await add_column_if_missing("event_seats", "zone_name", "TEXT")
        # Add new columns to registration_sessions
        await add_column_if_missing("registration_sessions", "visitor_id", "TEXT")
        await add_column_if_missing("registration_sessions", "intent", "TEXT")
        # Add max_price_override to worker_settings
        await add_column_if_missing("worker_settings", "max_price_override", "INTEGER DEFAULT NULL")

        # Deposits table (for top-up system)
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
        
        # Deposits table migrations
        await add_column_if_missing("deposits", "requisites", "TEXT")
        await add_column_if_missing("deposits", "bank_name", "TEXT")
        await add_column_if_missing("deposits", "exact_amount", "INTEGER")
        await add_column_if_missing("deposits", "group_message_id", "INTEGER")
        await add_column_if_missing("deposits", "expires_at", "TIMESTAMP")

        await db.commit()
    
    # Seed default events if table is empty
    await seed_default_events()
    
    logger.info("Bot schema OK")

async def seed_default_events():
    """Insert default events if the events table is empty."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Check if events exist
        async with db.execute("SELECT COUNT(*) FROM events") as cursor:
            count = (await cursor.fetchone())[0]
            if count > 0:
                logger.info(f"Events table has {count} events, skipping seed")
                return
        
        logger.info("Seeding default events...")
        
        # Default events with images from public/images
        default_events = [
            {
                'id': 100001,
                'title': 'Фестиваль науки в КГИК',
                'description': 'Краснодарский государственный институт культуры приглашает на фестиваль науки. Увлекательные эксперименты, мастер-классы и лекции.',
                'venue': 'Краснодарский государственный институт культуры',
                'date_time': '2026-02-06 11:00',
                'photo_path': '/images/7c70a2ae3e90ccde8884e252621f4664-jpg.jpeg',
                'min_price': 500,
                'max_price': 2000,
                'is_system': 1
            },
            {
                'id': 100002,
                'title': '«Миры М.А. Булгакова». К 135-летию со дня рождения',
                'description': 'Выставка, посвященная жизни и творчеству великого писателя.',
                'venue': 'Школа-лицей при музее Сталинградская битва',
                'date_time': '2026-03-13 12:00',
                'photo_path': '/images/ef8aff0f5d4d637224a0e87b97675ceb-jpg.jpeg',
                'min_price': 300,
                'max_price': 800,
                'is_system': 1
            },
            {
                'id': 100003,
                'title': 'Квиз «Знатоки родного края»',
                'description': 'Интеллектуальная игра для любителей истории Кубани.',
                'venue': 'Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы',
                'date_time': '2026-02-04 14:00',
                'photo_path': '/images/3609ed8fe59c2b5c3508e1cd7b4b9874-jpg.jpeg',
                'min_price': 200,
                'max_price': 500,
                'is_system': 1
            },
            {
                'id': 100004,
                'title': 'Спектакль «На всякого мудреца...»',
                'description': 'Классический спектакль по пьесе А.Н. Островского.',
                'venue': 'Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова',
                'date_time': '2026-02-04 18:30',
                'photo_path': '/images/ba61bc932f041a3a8f03979c52b20272-jpg.jpeg',
                'min_price': 800,
                'max_price': 3500,
                'is_system': 1
            },
            {
                'id': 100005,
                'title': 'Диво дивное — слово русское!',
                'description': 'Литературный праздник для детей и взрослых.',
                'venue': 'Краснодарская краевая детская библиотека им.братьев Игнатовых',
                'date_time': '2026-02-05 11:00',
                'photo_path': '/images/026ce21a706b9829d72e7db9f1df3012-jpg.jpeg',
                'min_price': 150,
                'max_price': 400,
                'is_system': 1
            },
            {
                'id': 100006,
                'title': 'День кубанского кобзаря',
                'description': 'Празднование в честь народных поэтов Кубани.',
                'venue': 'Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы',
                'date_time': '2026-02-05 14:00',
                'photo_path': '/images/1f189852c5966a3eb983a78acd54b701-jpg.jpeg',
                'min_price': 200,
                'max_price': 600,
                'is_system': 1
            },
            {
                'id': 100007,
                'title': 'Спектакль «Доктор Айболит»',
                'description': 'Детский музыкальный спектакль по мотивам сказки К. Чуковского.',
                'venue': 'Пашковский городской дом культуры г. Краснодара',
                'date_time': '2026-02-07 14:00',
                'photo_path': '/images/7a79eb8caca34affc0db16180a1cabbe-jpg.jpeg',
                'min_price': 400,
                'max_price': 1200,
                'is_system': 1
            },
            {
                'id': 100008,
                'title': 'Спектакль «Сквозь огонь войны»',
                'description': 'Драматическая постановка о героях Великой Отечественной.',
                'venue': 'Театр защитников Отечества',
                'date_time': '2026-02-08 17:00',
                'photo_path': '/images/f16886979b66cfad60fd2df83def6f17-jpg.jpeg',
                'min_price': 500,
                'max_price': 2000,
                'is_system': 1
            },
            {
                'id': 100009,
                'title': 'Опера «Царская невеста»',
                'description': 'Опера Н.А. Римского-Корсакова в постановке театра Премьера.',
                'venue': 'Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова',
                'date_time': '2026-02-10 17:00',
                'photo_path': '/images/c02ad07ab42247ef32be54b05d5599b9-jpg.jpeg',
                'min_price': 1000,
                'max_price': 5000,
                'is_system': 1
            },
            {
                'id': 100010,
                'title': 'Спектакль «В стране дорожных знаков»',
                'description': 'Познавательный спектакль о правилах дорожного движения для детей.',
                'venue': 'Краснодарский краевой театр кукол',
                'date_time': '2026-02-12 11:00',
                'photo_path': '/images/8fb891bcdc9fa96dad8b2eb96b59c0b6-jpg.jpeg',
                'min_price': 300,
                'max_price': 800,
                'is_system': 1
            },
            {
                'id': 100011,
                'title': 'Концерт «Овеяна славой родная Кубань»',
                'description': 'Праздничный концерт кубанских артистов.',
                'venue': 'Центральный концертный зал',
                'date_time': '2026-02-12 14:00',
                'photo_path': '/images/30807229e5a58543550454e83002cc48-jpg.jpeg',
                'min_price': 600,
                'max_price': 2500,
                'is_system': 1
            },
            {
                'id': 100012,
                'title': 'Спектакль «Двойник»',
                'description': 'Мистический спектакль по повести Ф.М. Достоевского.',
                'venue': 'Краснодарский академический театр драмы им. М.Горького',
                'date_time': '2026-02-15 18:30',
                'photo_path': '/images/7b558d68b9e52db8b7fda34f1c9e13cd-jpg.jpeg',
                'min_price': 700,
                'max_price': 3000,
                'is_system': 1
            },
            {
                'id': 100013,
                'title': 'Концерт «Песни Победы вместе поем»',
                'description': 'Патриотический концерт с участием народных коллективов.',
                'venue': 'Центральный концертный зал',
                'date_time': '2026-02-14 15:00',
                'photo_path': '/images/377fe330d6a08a6b09438ffdcacde5a6-jpeg.jpeg',
                'min_price': 400,
                'max_price': 1500,
                'is_system': 1
            },
            {
                'id': 100014,
                'title': 'Концерт «Маленький принц»',
                'description': 'Музыкально-поэтическое представление для всей семьи.',
                'venue': 'Краснодарская филармония им. Г.Ф. Пономаренко',
                'date_time': '2026-02-14 17:00',
                'photo_path': '/images/eee6882fc7dbf38e0b0a91316c613588-jpg.jpeg',
                'min_price': 500,
                'max_price': 2200,
                'is_system': 1
            },
            {
                'id': 100015,
                'title': 'Спектакль «Ромео и Джульетта»',
                'description': 'Бессмертная трагедия У. Шекспира в современной постановке.',
                'venue': 'Краснодарский академический театр драмы им. М.Горького',
                'date_time': '2026-02-17 19:00',
                'photo_path': '/images/fe9ffccbd3facaf5a096422d8e8b353c-jpg.jpeg',
                'min_price': 800,
                'max_price': 4000,
                'is_system': 1
            }
        ]
        
        for event in default_events:
            await db.execute("""
                INSERT INTO events (id, title, description, photo_path, min_price, max_price, date_time, venue, is_system)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (event['id'], event['title'], event['description'], event['photo_path'], 
                  event['min_price'], event['max_price'], event['date_time'], event['venue'], event['is_system']))
        
        await db.commit()
        logger.info(f"Seeded {len(default_events)} default events")
        
        # Generate seats for each event
        for event in default_events:
            await generate_event_seats(event['id'], event['min_price'], event['max_price'])

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

async def create_event(title: str, description: str, min_price: int, max_price: int, 
                      date_time: str, venue: str, created_by: int, photo_path: str) -> int:
    """Create new event and return event_id. Photo is required."""
    if not photo_path:
        raise ValueError("Photo is required for event creation")
    
    import random
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Generate unique random ID
        while True:
            event_id = random.randint(100000, 999999)  # 6-digit random ID
            
            # Check if ID already exists
            async with db.execute("SELECT id FROM events WHERE id = ?", (event_id,)) as cursor:
                if not await cursor.fetchone():
                    break
        
        # Insert with specific ID
        await db.execute("""
            INSERT INTO events (id, title, description, photo_path, min_price, max_price, 
                              date_time, venue, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, title, description, photo_path, min_price, max_price, date_time, venue, created_by))
        
        await db.commit()
        
        # Generate seats for the event
        await generate_event_seats(event_id, min_price, max_price)
        
        logger.info(f"Event created: id={event_id}, title={title}, by={created_by}, photo={photo_path}")
        return event_id

async def generate_event_seats(event_id: int, min_price: int, max_price: int):
    """Generate professional theater seat layout with Parterre and Balconies."""
    import asyncio
    import random
    import math
    
    # Retry logic for database lock
    for attempt in range(5):
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute("PRAGMA busy_timeout = 60000")
                await db.execute("PRAGMA synchronous = NORMAL")
                
                # Check existence
                async with db.execute("SELECT COUNT(*) FROM event_seats WHERE event_id = ?", (event_id,)) as cursor:
                    if (await cursor.fetchone())[0] > 0:
                        logger.info(f"Seats already exist for event {event_id}")
                        return
                
                seats_data = []
                
                # --- Theater Configuration ---
                # Zone 1: Parterre (Партер) - Red tones
                # Rows 1-10
                parterre_rows = 10
                parterre_start_width = 24
                
                # Zone 2: Balcony 1 (Балкон 1-й ярус) - Gray tones
                # Rows 11-15 (Gap after Parterre)
                balcony1_rows = 5
                balcony1_start_width = 30
                
                # Zone 3: Balcony 2 (Балкон 2-й ярус) - Dark tones
                # Rows 16-20 (Gap after Balcony 1)
                balcony2_rows = 5
                balcony2_start_width = 36
                
                total_rows = parterre_rows + balcony1_rows + balcony2_rows
                
                # Setup Prices
                price_step = (max_price - min_price) / 3
                price_parterre = max_price
                price_balcony1 = int(max_price - price_step)
                price_balcony2 = min_price
                
                # --- GENERATION ---
                
                # 1. Parterre Generation
                current_width = parterre_start_width
                for r in range(1, parterre_rows + 1):
                    row_num = r
                    current_width += 1 # Gentle growth
                    count = int(current_width)
                    seats_in_row = min(count, 40)
                    
                    for seat_num in range(1, seats_in_row + 1):
                        is_available = 1 if random.random() > 0.5 else 0
                        seats_data.append((event_id, row_num, seat_num, price_parterre, is_available, "Партер"))

                # 2. Balcony 1 Generation
                current_width = balcony1_start_width
                for r in range(1, balcony1_rows + 1):
                    row_num = parterre_rows + r
                    current_width += 2 # Faster growth
                    count = int(current_width)
                    seats_in_row = min(count, 50)
                    
                    for seat_num in range(1, seats_in_row + 1):
                        is_available = 1 if random.random() > 0.55 else 0
                        seats_data.append((event_id, row_num, seat_num, price_balcony1, is_available, "Балкон 1-й ярус"))

                # 3. Balcony 2 Generation
                current_width = balcony2_start_width
                for r in range(1, balcony2_rows + 1):
                    row_num = parterre_rows + balcony1_rows + r
                    current_width += 2
                    count = int(current_width)
                    seats_in_row = min(count, 60)
                    
                    for seat_num in range(1, seats_in_row + 1):
                        is_available = 1 if random.random() > 0.6 else 0
                        seats_data.append((event_id, row_num, seat_num, price_balcony2, is_available, "Балкон 2-й ярус"))
                
                # Bulk insert
                batch_size = 500
                for i in range(0, len(seats_data), batch_size):
                    batch = seats_data[i:i + batch_size]
                    await db.executemany("""
                        INSERT INTO event_seats (event_id, row_number, seat_number, price, is_available, zone_name)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, batch)
                
                await db.commit()
                logger.info(f"Generated {len(seats_data)} theater seats for event {event_id}")
                return

        except Exception as e:
            if "database is locked" in str(e).lower() and attempt < 4:
                wait_time = attempt + 1
                logger.warning(f"Database locked, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            else:
                logger.error(f"Failed to generate seats: {e}")
                if attempt == 4:
                    return
                    logger.error(f"Giving up on seat generation for event {event_id}")
                    return
                raise

async def get_all_events() -> list:
    """Get all events (system + user created)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("""
            SELECT e.*, bu.full_name as creator_name
            FROM events e
            LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
            ORDER BY e.created_at DESC
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_events_for_user(telegram_user_id: int) -> list:
    """Get events visible to specific user based on referral hierarchy."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Check if user exists in users table
        async with db.execute("""
            SELECT u.referrer_user_id, bu.telegram_user_id as referrer_telegram_id
            FROM users u
            LEFT JOIN users ref_u ON u.referrer_user_id = ref_u.id
            LEFT JOIN bot_users bu ON ref_u.telegram_user_id = bu.telegram_user_id
            WHERE u.telegram_user_id = ?
        """, (telegram_user_id,)) as cursor:
            user_row = await cursor.fetchone()
        
        # If user doesn't exist in users table, just show system events
        if not user_row:
            async with db.execute("""
                SELECT e.*, bu.full_name as creator_name
                FROM events e
                LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
                WHERE e.is_system = 1
                ORDER BY e.date_time ASC
            """, ()) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        
        referrer_telegram_id = user_row['referrer_telegram_id'] if user_row else None
        
        # If user has no referrer, show all system events + their own events
        if not referrer_telegram_id:
            async with db.execute("""
                SELECT e.*, bu.full_name as creator_name
                FROM events e
                LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
                WHERE e.is_system = 1 OR e.created_by = ?
                ORDER BY e.date_time ASC
            """, (telegram_user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        
        # User has referrer - show events based on referrer's settings
        # 1. System events that referrer hasn't hidden
        # 2. Events created by referrer
        # 3. User's own events
        async with db.execute("""
            SELECT e.*, bu.full_name as creator_name
            FROM events e
            LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
            LEFT JOIN hidden_events he ON e.id = he.event_id AND he.hidden_by = ?
            WHERE (
                (e.is_system = 1 AND he.id IS NULL) OR  -- System events not hidden by referrer
                e.created_by = ? OR                      -- Events created by referrer
                e.created_by = ?                         -- User's own events
            )
            ORDER BY e.date_time ASC
        """, (referrer_telegram_id, referrer_telegram_id, telegram_user_id)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def hide_event_for_referrals(event_id: int, referrer_telegram_id: int) -> bool:
    """Hide system event for all referrals of specific referrer."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if event is system event
        async with db.execute("SELECT is_system FROM events WHERE id = ?", (event_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or not row[0]:
                return False  # Can only hide system events
        
        # Add to hidden events
        try:
            await db.execute("""
                INSERT INTO hidden_events (event_id, hidden_by)
                VALUES (?, ?)
            """, (event_id, referrer_telegram_id))
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            # Already hidden
            return True

async def unhide_event_for_referrals(event_id: int, referrer_telegram_id: int) -> bool:
    """Unhide system event for all referrals of specific referrer."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            DELETE FROM hidden_events 
            WHERE event_id = ? AND hidden_by = ?
        """, (event_id, referrer_telegram_id))
        await db.commit()
        return True

async def is_event_hidden_by_referrer(event_id: int, referrer_telegram_id: int) -> bool:
    """Check if event is hidden by referrer."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT id FROM hidden_events 
            WHERE event_id = ? AND hidden_by = ?
        """, (event_id, referrer_telegram_id)) as cursor:
            return await cursor.fetchone() is not None

async def get_event_by_id(event_id: int) -> dict:
    """Get event details by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("""
            SELECT e.*, bu.full_name as creator_name
            FROM events e
            LEFT JOIN bot_users bu ON e.created_by = bu.telegram_user_id
            WHERE e.id = ?
        """, (event_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_event(event_id: int, **kwargs) -> bool:
    """Update event fields."""
    if not kwargs:
        return False
    
    allowed_keys = ['title', 'description', 'min_price', 'max_price', 'date_time', 'venue']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_keys:
            updates.append(f"{key} = ?")
            values.append(value)
    
    if not updates:
        return False
    
    values.append(event_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"""
            UPDATE events SET {', '.join(updates)} WHERE id = ?
        """, values)
        await db.commit()
        logger.info(f"Event updated: id={event_id}, fields={list(kwargs.keys())}")
        return True

async def get_event_seats(event_id: int) -> list:
    """Get all seats for an event."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("""
            SELECT * FROM event_seats 
            WHERE event_id = ? 
            ORDER BY row_number, seat_number
        """, (event_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def reserve_seat(event_id: int, row_number: int, seat_number: int, user_id: int) -> bool:
    """Reserve a seat for user. Returns True if successful."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if seat is available
        async with db.execute("""
            SELECT is_available FROM event_seats 
            WHERE event_id = ? AND row_number = ? AND seat_number = ? AND is_available = 1
        """, (event_id, row_number, seat_number)) as cursor:
            if not await cursor.fetchone():
                return False
        
        # Reserve the seat
        await db.execute("""
            UPDATE event_seats 
            SET is_available = 0, reserved_by = ?, reserved_at = CURRENT_TIMESTAMP
            WHERE event_id = ? AND row_number = ? AND seat_number = ?
        """, (user_id, event_id, row_number, seat_number))
        
        await db.commit()
        return True

async def create_system_events():
    """Create default system events."""
    import asyncio
    
    # Wait a bit to let other processes finish
    await asyncio.sleep(2)
    
    # Retry logic for database lock
    for attempt in range(10):  # Увеличиваем количество попыток
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                # Enable WAL mode and set timeouts
                await db.execute("PRAGMA journal_mode = WAL")
                await db.execute("PRAGMA busy_timeout = 60000")  # 60 seconds
                await db.execute("PRAGMA synchronous = NORMAL")  # Faster writes
                
                # Check if events table exists
                async with db.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='events'
                """) as cursor:
                    table_exists = await cursor.fetchone()
                
                if not table_exists:
                    logger.warning("Events table doesn't exist yet, skipping system events creation")
                    return
                
                # Check if system events already exist
                async with db.execute("SELECT COUNT(*) FROM events WHERE is_system = 1") as cursor:
                    count = (await cursor.fetchone())[0]
                    if count > 0:
                        logger.info(f"System events already exist ({count} events)")
                        return
                
                logger.info("Creating system events...")
                
                system_events = [
                    {
                        "title": "Гамлет",
                        "description": "Классическая трагедия Шекспира в современной постановке",
                        "min_price": 2000,
                        "max_price": 6500,
                        "date_time": "2026-02-15 19:00",
                        "venue": "Театр Драмы им. Горького - Основная сцена"
                    },
                    {
                        "title": "Ромео и Джульетта", 
                        "description": "Вечная история любви в новом прочтении",
                        "min_price": 1800,
                        "max_price": 5500,
                        "date_time": "2026-02-20 19:30",
                        "venue": "Театр Драмы им. Горького - Малая сцена"
                    },
                    {
                        "title": "Вишневый сад",
                        "description": "Пьеса А.П. Чехова о прощании с прошлым",
                        "min_price": 2200,
                        "max_price": 7000,
                        "date_time": "2026-02-25 18:00", 
                        "venue": "Театр Драмы им. Горького - Основная сцена"
                    }
                ]
                
                for i, event_data in enumerate(system_events):
                    logger.info(f"Creating system event {i+1}/{len(system_events)}: {event_data['title']}")
                    
                    cursor = await db.execute("""
                        INSERT INTO events (title, description, min_price, max_price, 
                                          date_time, venue, is_system, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, 1, NULL)
                    """, (event_data["title"], event_data["description"], 
                          event_data["min_price"], event_data["max_price"],
                          event_data["date_time"], event_data["venue"]))
                    
                    event_id = cursor.lastrowid
                    await db.commit()  # Commit after each event
                    
                    # Generate seats for this event
                    await generate_event_seats(event_id, event_data["min_price"], event_data["max_price"])
                
                logger.info("System events created successfully")
                return  # Success, exit retry loop
                
        except Exception as e:
            error_msg = str(e).lower()
            if ("database is locked" in error_msg or "database disk image is malformed" in error_msg) and attempt < 9:
                wait_time = min(attempt + 1, 5)  # Max 5 seconds wait
                logger.warning(f"Database issue, retrying in {wait_time} seconds... (attempt {attempt + 1}/10): {e}")
                await asyncio.sleep(wait_time)
                continue
            else:
                logger.error(f"Failed to create system events after {attempt + 1} attempts: {e}")
                if attempt == 9:  # Last attempt
                    logger.error("Giving up on system events creation. They can be created later manually.")
                    return
                raise


# ============================================================================
# Worker Settings Functions
# ============================================================================

# Available min price options
MIN_PRICE_OPTIONS = [2500, 2700, 3000, 3500]

# Available max price options (for seat pricing)
MAX_PRICE_OPTIONS = [5000, 7000, 10000, 15000]

# City venues database - theaters and cultural centers by city
CITY_VENUES = {
    "Краснодар": [
        "Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы",
        "Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова",
        "Краснодарский государственный институт культуры",
        "Краснодарская краевая детская библиотека им.братьев Игнатовых",
        "Краснодарский академический театр драмы им. М.Горького",
        "Краснодарский краевой театр кукол",
        "Краснодарская филармония им. Г.Ф. Пономаренко",
        "Центральный концертный зал",
        "Пашковский городской дом культуры г. Краснодара",
        "Театр защитников Отечества",
    ],
    "Москва": [
        "Большой театр России",
        "Московский художественный театр им. А.П. Чехова",
        "Театр им. Евг. Вахтангова",
        "Малый театр России",
        "Российский академический молодёжный театр (РАМТ)",
        "Московский театр Олега Табакова",
        "Театр «Современник»",
        "Московский государственный театр Ленком",
        "Театр Наций",
        "Московская государственная филармония",
    ],
    "Санкт-Петербург": [
        "Мариинский театр",
        "Александринский театр",
        "Большой драматический театр им. Г.А. Товстоногова",
        "Михайловский театр",
        "Театр музыкальной комедии",
        "Санкт-Петербургский академический театр комедии",
        "Молодёжный театр на Фонтанке",
        "Театр «Балтийский дом»",
        "Санкт-Петербургская филармония им. Д.Д. Шостаковича",
        "Эрмитажный театр",
    ],
    "Новосибирск": [
        "Новосибирский академический театр оперы и балета",
        "Новосибирский академический молодёжный театр «Глобус»",
        "Новосибирский государственный драматический театр «Красный факел»",
        "Новосибирская государственная филармония",
        "Новосибирский музыкальный театр",
        "Дом культуры им. Октябрьской революции",
        "Городской дом культуры железнодорожников",
    ],
    "Екатеринбург": [
        "Екатеринбургский государственный академический театр оперы и балета",
        "Свердловский государственный академический театр драмы",
        "Свердловский государственный академический театр музыкальной комедии",
        "Екатеринбургский театр юного зрителя",
        "Свердловская государственная филармония",
        "Коляда-Театр",
        "Дом актёра им. Н.Ф. Стромилова",
    ],
    "Казань": [
        "Татарский академический государственный театр оперы и балета им. М. Джалиля",
        "Казанский академический русский большой драматический театр им. В.И. Качалова",
        "Татарский государственный академический театр им. Г. Камала",
        "Казанский государственный театр юного зрителя",
        "Государственная филармония Республики Татарстан",
        "Казанский государственный театр кукол «Экият»",
    ],
    "Нижний Новгород": [
        "Нижегородский государственный академический театр драмы им. М. Горького",
        "Нижегородский государственный академический театр оперы и балета им. А.С. Пушкина",
        "Нижегородский театр юного зрителя",
        "Нижегородская государственная филармония им. М. Ростроповича",
        "Театр «Комедiя»",
        "Нижегородский театр кукол",
    ],
    "Пермь": [
        "Пермский академический театр оперы и балета им. П.И. Чайковского",
        "Пермский академический Театр-Театр",
        "Пермский академический театр драмы",
        "Пермский театр юного зрителя",
        "Пермская краевая филармония",
        "Пермский театр кукол",
    ],
    "Самара": [
        "Самарский академический театр оперы и балета",
        "Самарский академический театр драмы им. М. Горького",
        "Самарский академический театр детей и молодёжи «СамАрт»",
        "Самарская государственная филармония",
        "Самарский театр юного зрителя «СамАрт»",
    ],
    "Ростов-на-Дону": [
        "Ростовский государственный музыкальный театр",
        "Ростовский академический театр драмы им. М. Горького",
        "Ростовский молодёжный академический театр",
        "Ростовская государственная филармония",
        "Ростовский театр кукол",
    ],
    "Воронеж": [
        "Воронежский государственный театр оперы и балета",
        "Воронежский академический театр драмы им. А. Кольцова",
        "Воронежский Камерный театр",
        "Воронежская государственная филармония",
        "Воронежский государственный театр юного зрителя",
    ],
    "Волгоград": [
        "Волгоградский музыкальный театр",
        "Волгоградский областной драматический театр им. М. Горького", 
        "Волгоградский молодёжный театр",
        "Волгоградская областная филармония",
        "Школа-лицей при музее Сталинградская битва",
    ],
}


async def get_worker_settings(telegram_user_id: int) -> dict:
    """Get worker settings or return defaults."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("""
            SELECT * FROM worker_settings WHERE telegram_user_id = ?
        """, (telegram_user_id,)) as cursor:
            row = await cursor.fetchone()
            
        if row:
            return dict(row)
        
        # Return defaults
        return {
            'telegram_user_id': telegram_user_id,
            'min_price_override': None,
            'max_price_override': None,
            'custom_city': None,
        }


async def update_worker_setting(telegram_user_id: int, key: str, value) -> bool:
    """Update a specific worker setting."""
    allowed_keys = ['min_price_override', 'max_price_override', 'custom_city']
    if key not in allowed_keys:
        logger.error(f"Invalid setting key: {key}")
        return False
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if settings exist for user
        async with db.execute("""
            SELECT id FROM worker_settings WHERE telegram_user_id = ?
        """, (telegram_user_id,)) as cursor:
            exists = await cursor.fetchone()
        
        if exists:
            # Update existing
            await db.execute(f"""
                UPDATE worker_settings 
                SET {key} = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE telegram_user_id = ?
            """, (value, telegram_user_id))
        else:
            # Insert new
            await db.execute(f"""
                INSERT INTO worker_settings (telegram_user_id, {key})
                VALUES (?, ?)
            """, (telegram_user_id, value))
        
        await db.commit()
        logger.info(f"Worker setting updated: {telegram_user_id}.{key} = {value}")
        return True


def get_venues_for_city(city: str) -> list:
    """Get list of venues for a city. Returns default (Krasnodar) if city not found."""
    # Try exact match
    if city in CITY_VENUES:
        return CITY_VENUES[city]
    
    # Try case-insensitive match
    city_lower = city.lower()
    for city_name, venues in CITY_VENUES.items():
        if city_name.lower() == city_lower:
            return venues
    
    # Return Krasnodar as default
    return CITY_VENUES.get("Краснодар", [])


def get_available_cities() -> list:
    """Get list of all available cities."""
    return list(CITY_VENUES.keys())


# ============================================================================
# Deposits (Top-Up System)
# ============================================================================

async def create_deposit(user_id: int, amount: int) -> dict:
    """Create a new deposit request."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            INSERT INTO deposits (user_id, amount, status)
            VALUES (?, ?, 'pending')
        """, (user_id, amount))
        deposit_id = cursor.lastrowid
        await db.commit()
        
        async with db.execute("SELECT * FROM deposits WHERE id = ?", (deposit_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_deposit_by_id(deposit_id: int) -> dict:
    """Get deposit by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM deposits WHERE id = ?", (deposit_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_deposit(deposit_id: int, **kwargs) -> bool:
    """Update deposit fields."""
    if not kwargs:
        return False
    
    allowed_keys = ['status', 'requisites', 'bank_name', 'exact_amount', 'group_message_id', 'expires_at']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_keys:
            updates.append(f"{key} = ?")
            values.append(value)
    
    if not updates:
        return False
    
    values.append(deposit_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"""
            UPDATE deposits SET {', '.join(updates)} WHERE id = ?
        """, values)
        await db.commit()
        return True


async def get_deposit_by_message_id(group_message_id: int) -> dict:
    """Get deposit by group message ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM deposits WHERE group_message_id = ?", (group_message_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_user_pending_deposit(user_id: int) -> dict:
    """Get user's pending deposit if exists."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM deposits 
            WHERE user_id = ? AND status IN ('pending', 'awaiting_requisites', 'requisites_sent')
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


# ============================================================================
# Support Chat System
# ============================================================================

async def ensure_support_table():
    """Create support_tickets table if not exists."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                telegram_user_id INTEGER,
                message TEXT NOT NULL,
                group_message_id INTEGER,
                reply_text TEXT,
                replied_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        await db.commit()


async def create_support_message(user_id: int, telegram_user_id: int, message: str, group_message_id: int = None) -> dict:
    """Create a new support message."""
    await ensure_support_table()
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            INSERT INTO support_tickets (user_id, telegram_user_id, message, group_message_id)
            VALUES (?, ?, ?, ?)
        """, (user_id, telegram_user_id, message, group_message_id))
        ticket_id = cursor.lastrowid
        await db.commit()
        
        async with db.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_support_message_by_group_msg(group_message_id: int) -> dict:
    """Get support ticket by group message ID."""
    await ensure_support_table()
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM support_tickets WHERE group_message_id = ?", (group_message_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_support_ticket(ticket_id: int, **kwargs) -> bool:
    """Update support ticket fields."""
    if not kwargs:
        return False
    
    allowed_keys = ['reply_text', 'replied_at', 'group_message_id']
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if key in allowed_keys:
            updates.append(f"{key} = ?")
            values.append(value)
    
    if not updates:
        return False
    
    values.append(ticket_id)
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"""
            UPDATE support_tickets SET {', '.join(updates)} WHERE id = ?
        """, values)
        await db.commit()
        return True


async def get_user_by_telegram_id(telegram_user_id: int) -> dict:
    """Get user by telegram_user_id."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_user_id = ?", (telegram_user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


# ============================================================================
# Theatre Links System
# ============================================================================

async def create_theatre_link(telegram_user_id: int, name: str) -> dict:
    """Create a new theatre link with unique 8-digit code. Retries on collision."""
    import random
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        max_retries = 10
        
        for attempt in range(max_retries):
            # Generate 8-digit numeric code
            link_code = str(random.randint(10000000, 99999999))
            
            try:
                await db.execute("""
                    INSERT INTO theatre_links (telegram_user_id, name, link_code)
                    VALUES (?, ?, ?)
                """, (telegram_user_id, name, link_code))
                await db.commit()
                
                # Return created record
                async with db.execute(
                    "SELECT * FROM theatre_links WHERE link_code = ?", (link_code,)
                ) as cursor:
                    row = await cursor.fetchone()
                    logger.info(f"Theatre link created: user={telegram_user_id}, name={name}, code={link_code}")
                    return dict(row) if row else None
                    
            except aiosqlite.IntegrityError:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to generate unique link_code after {max_retries} attempts")
                    raise Exception("Failed to generate unique link_code")
                continue
    
    return None


async def get_theatre_links(telegram_user_id: int) -> list:
    """Get all theatre links for user, ordered by creation date."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute("""
            SELECT * FROM theatre_links 
            WHERE telegram_user_id = ? 
            ORDER BY created_at ASC
        """, (telegram_user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_link_by_code(link_code: str) -> dict:
    """Get theatre link by public code (for cl= parameter)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute(
            "SELECT * FROM theatre_links WHERE link_code = ?", (link_code,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_link_by_id(link_id: int) -> dict:
    """Get theatre link by internal ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        async with db.execute(
            "SELECT * FROM theatre_links WHERE id = ?", (link_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_link_setting(link_id: int, key: str, value) -> bool:
    """Update a specific theatre link setting. Only allowed keys."""
    allowed_keys = ['name', 'custom_city', 'min_price_override', 'max_price_override']
    
    if key not in allowed_keys:
        logger.error(f"Invalid link setting key: {key}")
        return False
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"""
            UPDATE theatre_links 
            SET {key} = ?
            WHERE id = ?
        """, (value, link_id))
        await db.commit()
        logger.info(f"Theatre link setting updated: link_id={link_id}, {key}={value}")
        return True


async def delete_theatre_link(link_id: int) -> bool:
    """Delete a theatre link by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM theatre_links WHERE id = ?", (link_id,))
        await db.commit()
        logger.info(f"Theatre link deleted: id={link_id}")
        return True