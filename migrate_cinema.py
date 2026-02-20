import asyncio
import logging
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

from data.db import db
from bots.database import seed_default_events

logging.basicConfig(level=logging.INFO)

async def main():
    await db.connect()
    
    try:
        # 1. Заново генерируем дефолтные события (они получат type='cinema')
        logging.info("Re-seeding cinema events...")
        await seed_default_events()
        
        # 2. Переименовываем старые системные события (ID >= 100) обратно в театр
        logging.info("Re-migrating old theatre events...")
        await db.execute("""
            UPDATE events 
            SET type = 'theatre' 
            WHERE is_system = 1 AND type = 'cinema' AND id >= 100 AND (
                title LIKE '%Спектакль%' OR 
                title LIKE '%Комедия%' OR 
                title LIKE '%Балет%' OR 
                title LIKE '%Мюзикл%' OR 
                title LIKE '%Шоу%' OR
                title LIKE '%Миры М.А.%' OR
                title LIKE '%Классика%'
            )
        """)
        
        logging.info("Done!")

    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
