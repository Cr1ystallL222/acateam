from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from .config import MAIN_BOT_TOKEN

# Initialize Bot and Dispatcher with FSM storage
bot = Bot(token=MAIN_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
