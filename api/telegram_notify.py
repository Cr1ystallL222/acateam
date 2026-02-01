import httpx
import logging
import asyncio
import os
import time
from dotenv import load_dotenv
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telegram_notify")

# Load env variables from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def send_telegram_message(chat_id: int, text: str, max_retries: int = 3):
    """
    Sends a message to Telegram with retries and exponential backoff.
    """
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing! Cannot send notification.")
        return

    logger.info(f"Attempting to send Telegram message to chat_id={chat_id}, text_length={len(text)}")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    
    # Explicit timeouts
    timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10.0)
    
    for attempt in range(1, max_retries + 1):
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                
            elapsed = time.time() - start_time
            
            if resp.status_code == 200:
                logger.info(f"[Attempt {attempt}] Telegram notify success: sent to {chat_id} in {elapsed:.2f}s")
                return
            else:
                logger.error(f"[Attempt {attempt}] Telegram notify failed: {resp.status_code} {resp.text}")
                # We don't necessarily retry on 4xx errors (client errors), only validation etc.
                # But for 5xx or specific telegram errors we might. 
                # For now, let's treat non-200 as failure, but maybe only retry on network/server errors?
                # User asked for retries on ConnectTimeout/ReadTimeout/RequestError. 
                # Responses from API usually mean connectivity was fine.
                if 400 <= resp.status_code < 500:
                    # Client error, likely invalid chat_id or token, no need to retry
                    logger.error(f"Client error {resp.status_code}, not retrying")
                    return
        
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RequestError) as e:
            logger.warning(f"[Attempt {attempt}] Telegram notify network error: {type(e).__name__} {e}")
        except Exception as e:
            logger.error(f"[Attempt {attempt}] Telegram notify unexpected error: {type(e).__name__} {e}")
            # Don't retry on unknown logic errors unless sure
        
        # Backoff logic if we haven't returned yet
        if attempt < max_retries:
            sleep_time = 0
            if attempt == 1:
                sleep_time = 1
            elif attempt == 2:
                sleep_time = 3
            else:
                sleep_time = 3 # Cap at 3 or increase further
                
            logger.info(f"Retrying in {sleep_time}s...")
            await asyncio.sleep(sleep_time)
            
    logger.error(f"Failed to send telegram message to {chat_id} after {max_retries} attempts.")
