import asyncio
import logging
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

from data.db import db
from bots.database import seed_default_events, generate_event_seats

logging.basicConfig(level=logging.INFO)

# Театральные системные события (из web/app/(landing)/page.tsx)
THEATRE_EVENTS = [
    {'id': 100001, 'title': 'Фестиваль науки в КГИК', 'description': 'Фестиваль науки в КГИК', 'venue': 'Краснодарский государственный институт культуры', 'photo_path': '/images/026ce21a706b9829d72e7db9f1df3012-jpg.jpeg', 'min_price': 0, 'max_price': 500, 'hour': 11, 'min': 0, 'day_offset': 0},
    {'id': 100002, 'title': '«Миры М.А. Булгакова». К 135-летию со дня рождения...', 'description': 'Выставка к юбилею М.А. Булгакова', 'venue': 'Школа-лицей при музее Сталинградская битва', 'photo_path': '/images/0e8052455655d9aaca6315f378362cdf-jpg.jpeg', 'min_price': 350, 'max_price': 800, 'hour': 12, 'min': 0, 'day_offset': 1},
    {'id': 100003, 'title': 'Квиз «Знатоки родного края»', 'description': 'Квиз «Знатоки родного края»', 'venue': 'Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы', 'photo_path': '/images/1-jpeg.jpeg', 'min_price': 250, 'max_price': 600, 'hour': 14, 'min': 0, 'day_offset': 0},
    {'id': 100004, 'title': 'Спектакль «На всякого мудреца...»', 'description': 'Спектакль «На всякого мудреца довольно простоты»', 'venue': 'Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова', 'photo_path': '/images/1572446586138e701da3254e277dd9f0-jpg.jpeg', 'min_price': 400, 'max_price': 1200, 'hour': 18, 'min': 30, 'day_offset': 0},
    {'id': 100005, 'title': 'Диво дивное — слово русское!', 'description': 'Диво дивное — слово русское!', 'venue': 'Краснодарская краевая детская библиотека им.братьев Игнатовых', 'photo_path': '/images/1f189852c5966a3eb983a78acd54b701-jpg.jpeg', 'min_price': 0, 'max_price': 300, 'hour': 11, 'min': 0, 'day_offset': 1},
    {'id': 100006, 'title': 'День кубанского кобзаря', 'description': 'День кубанского кобзаря', 'venue': 'Краснодарская краевая юношеская библиотека им. И.Ф. Вараввы', 'photo_path': '/images/26c35e1eecc195b202a606f9728060bb-jpg.jpeg', 'min_price': 0, 'max_price': 300, 'hour': 14, 'min': 0, 'day_offset': 1},
    {'id': 100007, 'title': 'Спектакль «Доктор Айболит»', 'description': 'Спектакль «Доктор Айболит»', 'venue': 'Пашковский городской дом культуры г. Краснодара', 'photo_path': '/images/30807229e5a58543550454e83002cc48-jpg.jpeg', 'min_price': 600, 'max_price': 1500, 'hour': 14, 'min': 0, 'day_offset': 2},
    {'id': 100008, 'title': 'Спектакль «Сквозь огонь войны»', 'description': 'Спектакль «Сквозь огонь войны»', 'venue': 'Театр защитников Отечества', 'photo_path': '/images/3609ed8fe59c2b5c3508e1cd7b4b9874-jpg.jpeg', 'min_price': 500, 'max_price': 1200, 'hour': 17, 'min': 0, 'day_offset': 3},
    {'id': 100009, 'title': 'Опера «Царская невеста»', 'description': 'Опера «Царская невеста»', 'venue': 'Краснодарское творческое объединение «Премьера» им. Л.Г. Гатова', 'photo_path': '/images/377fe330d6a08a6b09438ffdcacde5a6-jpeg.jpeg', 'min_price': 400, 'max_price': 1000, 'hour': 17, 'min': 0, 'day_offset': 4},
    {'id': 100010, 'title': 'Спектакль «В стране дорожных знаков»', 'description': 'Спектакль «В стране дорожных знаков»', 'venue': 'Краснодарский краевой театр кукол', 'photo_path': '/images/7a79eb8caca34affc0db16180a1cabbe-jpg.jpeg', 'min_price': 350, 'max_price': 800, 'hour': 11, 'min': 0, 'day_offset': 5},
    {'id': 100011, 'title': 'Концерт «Овеяна славой родная Кубань»', 'description': 'Концерт «Овеяна славой родная Кубань»', 'venue': 'Центральный концертный зал', 'photo_path': '/images/7b558d68b9e52db8b7fda34f1c9e13cd-jpg.jpeg', 'min_price': 300, 'max_price': 800, 'hour': 14, 'min': 0, 'day_offset': 5},
    {'id': 100012, 'title': 'Спектакль «Двойник»', 'description': 'Спектакль «Двойник»', 'venue': 'Краснодарский академический театр драмы им. М.Горького', 'photo_path': '/images/7c70a2ae3e90ccde8884e252621f4664-jpg.jpeg', 'min_price': 500, 'max_price': 1500, 'hour': 18, 'min': 30, 'day_offset': 7},
    {'id': 100013, 'title': 'Концерт «Песни Победы вместе поем»', 'description': 'Концерт «Песни Победы вместе поем»', 'venue': 'Центральный концертный зал', 'photo_path': '/images/8fb891bcdc9fa96dad8b2eb96b59c0b6-jpg.jpeg', 'min_price': 300, 'max_price': 700, 'hour': 15, 'min': 0, 'day_offset': 6},
    {'id': 100014, 'title': 'Концерт «Маленький принц»', 'description': 'Концерт «Маленький принц»', 'venue': 'Краснодарская филармония им. Г.Ф. Пономаренко', 'photo_path': '/images/ba61bc932f041a3a8f03979c52b20272-jpg.jpeg', 'min_price': 400, 'max_price': 1000, 'hour': 17, 'min': 0, 'day_offset': 6},
    {'id': 100015, 'title': 'Спектакль «Ромео и Джульетта»', 'description': 'Спектакль «Ромео и Джульетта»', 'venue': 'Краснодарский академический театр драмы им. М.Горького', 'photo_path': '/images/c02ad07ab42247ef32be54b05d5599b9-jpg.jpeg', 'min_price': 500, 'max_price': 1500, 'hour': 19, 'min': 0, 'day_offset': 8},
]

async def seed_theatre_events():
    """Восстановить театральные системные события в БД."""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    
    # Сначала удалим старые театральные системные события (если есть)
    await db.execute("DELETE FROM hidden_events WHERE event_id IN (SELECT id FROM events WHERE is_system = TRUE AND type = 'theatre')")
    await db.execute("DELETE FROM event_seats WHERE event_id IN (SELECT id FROM events WHERE is_system = TRUE AND type = 'theatre')")
    await db.execute("DELETE FROM events WHERE is_system = TRUE AND type = 'theatre'")
    
    logging.info(f"Seeding {len(THEATRE_EVENTS)} theatre events...")
    
    for event in THEATRE_EVENTS:
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
        """, (event['id'], event['title'], event['description'], event['photo_path'], 
              event['min_price'], event['max_price'], date_str, event['venue'], True, 'theatre'))
        
        await generate_event_seats(event['id'], event['min_price'], event['max_price'])
    
    logging.info("Theatre events seeded.")

async def main():
    await db.connect()
    
    try:
        # 1. Генерируем дефолтные события Кино (удаляет только cinema, НЕ трогает theatre)
        logging.info("Re-seeding cinema events...")
        await seed_default_events()
        
        # 2. Восстанавливаем театральные системные события
        logging.info("Seeding theatre events...")
        await seed_theatre_events()
        
        logging.info("Done! Both cinema and theatre events are now in the database.")

    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
