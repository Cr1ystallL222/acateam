import warnings
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from .config import MAIN_BOT_TOKEN

# Suppress Pydantic warnings about aiogram models
warnings.filterwarnings("ignore", message=".*model_custom_emoji_id.*conflict with protected namespace.*")

# Initialize Bot and Dispatcher with FSM storage
bot = Bot(token=MAIN_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
