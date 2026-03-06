import os
import sys
import logging
import warnings
from pathlib import Path
from dotenv import load_dotenv

# Suppress Pydantic warnings about aiogram models
warnings.filterwarnings("ignore", message=".*model_custom_emoji_id.*conflict with protected namespace.*")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main_bot")

# Configuration
MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN") or os.getenv("BOT_TOKEN")
APPLICATIONS_CHAT_ID = os.getenv("APPLICATIONS_CHAT_ID")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
LOG_CHAT_ID = os.getenv("LOG_CHAT_ID") or os.getenv("APPLICATIONS_CHAT_ID")
SITE_URL = os.getenv("SITE_URL", "http://localhost:3000").rstrip('/')
CINEMA_SITE_URL = os.getenv("CINEMA_SITE_URL", "http://localhost:3001").rstrip('/')
ESCORT_BOT_USERNAME = os.getenv("ESCORT_BOT_USERNAME", "CrystallGirls_bot")
WELCOME_STICKER_ID = os.getenv("WELCOME_STICKER_ID", "CAACAgIAAxkBAAEVndxpfLWe_kV-422Fi4qGKJLHsd5efwACu4wAAuMy4UtXVa5yYy5AOTgE")
WELCOME_IMAGE_PATH = os.getenv("WELCOME_IMAGE_PATH", "")

# New profile & theatre config
WELCOME_PHOTO_PATH = os.getenv("WELCOME_PHOTO_PATH", "bots/images/wealcom.jpg")
THEATRE_PHOTO_PATH = os.getenv("THEATRE_PHOTO_PATH", "bots/images/Teatre.jpg")
THEATRE_GUIDE_URL = os.getenv("THEATRE_GUIDE_URL", "https://telegra.ph/Manual-po-rabote-s-botom-ACA-Team-02-15")
CINEMA_PHOTO_PATH = os.getenv("CINEMA_PHOTO_PATH", "bots/images/Cinema.jpg")
CINEMA_GUIDE_URL = os.getenv("CINEMA_GUIDE_URL", "https://telegra.ph/Manual-po-rabote-s-botom-ACA-Team-02-15")
TOPUP_GROUP_ID = os.getenv("TOPUP_GROUP_ID")
WORKERS_CHAT_ID = os.getenv("WORKERS_CHAT_ID")
PROFITS_CHANNEL_ID = os.getenv("PROFITS_CHANNEL_ID")
PROFIT_COMMAND_CHAT_ID = os.getenv("PROFIT_COMMAND_CHAT_ID")
SYSTEM_CHAT_ID = os.getenv("SYSTEM_CHAT_ID") or PROFIT_COMMAND_CHAT_ID

# Absolute path to database
DB_PATH = PROJECT_ROOT / "data" / "app.db"

if not MAIN_BOT_TOKEN:
    logger.error("MAIN_BOT_TOKEN is missing! Please update .env")
    sys.exit(1)

if not APPLICATIONS_CHAT_ID:
    logger.warning("APPLICATIONS_CHAT_ID is not set - applications won't be sent to group")
else:
    logger.info(f"Applications will be sent to chat: {APPLICATIONS_CHAT_ID}")

# Path helpers
def get_welcome_image_path():
    if WELCOME_IMAGE_PATH:
        p = Path(WELCOME_IMAGE_PATH)
        if p.is_absolute():
            return p
        return PROJECT_ROOT / p
    return PROJECT_ROOT / "bots" / "welcom.jpg"

def get_profile_photo_path():
    p = Path(WELCOME_PHOTO_PATH)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p

def get_theatre_photo_path():
    p = Path(THEATRE_PHOTO_PATH)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p

def get_cinema_photo_path():
    p = Path(CINEMA_PHOTO_PATH)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p

RESOLVED_IMAGE_PATH = get_welcome_image_path()
PROFILE_PHOTO_PATH = get_profile_photo_path()
THEATRE_PHOTO_RESOLVED = get_theatre_photo_path()
CINEMA_PHOTO_RESOLVED = get_cinema_photo_path()
