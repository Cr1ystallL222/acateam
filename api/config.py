import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Import the robust notification function - used by services
# Using simple import string for now to avoid circular deps if needed
# from api.telegram_notify import send_telegram_message 

# Load env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("AUTH_BOT_USERNAME", "PlaceHolderAuthBot")

# Absolute path to database
DB_PATH = PROJECT_ROOT / "data" / "app.db"

MOVIES = [
    {"title": "Dune: Part Two", "sessions": ["12:00", "15:00"]},
    {"title": "Inception", "sessions": ["19:00", "21:30"]},
    {"title": "The Matrix", "sessions": ["10:00", "22:00"]},
]
