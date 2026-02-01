from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import aiosqlite

from ..config import DB_PATH, APPLICATIONS_CHAT_ID, RESOLVED_IMAGE_PATH, logger
from ..loader import bot, dp

# FSM States
class ApplicationForm(StatesGroup):
    waiting_q1 = State()
    waiting_q2 = State()

@dp.callback_query(F.data == "continue")
async def cb_continue(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    msg_id = data.get("welcome_msg_id")
    
    question_text = (
        "<b>📝 Вопрос 1/2</b>\n\n"
        "Есть ли у вас опыт в данной сфере?\n\n"
        "<i>Напишите ваш ответ сообщением.</i>"
    )
    
    if msg_id:
        try:
            await callback.message.edit_caption(caption=question_text, parse_mode="HTML")
        except:
            await callback.message.answer(question_text, parse_mode="HTML")
    else:
        await callback.message.answer(question_text, parse_mode="HTML")
    
    await state.set_state(ApplicationForm.waiting_q1)

@dp.message(ApplicationForm.waiting_q1)
async def process_q1(message: types.Message, state: FSMContext):
    await state.update_data(q1_answer=message.text)
    
    await message.answer(
        "<b>📝 Вопрос 2/2</b>\n\n"
        "Откуда узнали о нас?\n\n"
        "<i>Напишите ваш ответ сообщением.</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(ApplicationForm.waiting_q2)

@dp.message(ApplicationForm.waiting_q2)
async def process_q2(message: types.Message, state: FSMContext):
    data = await state.get_data()
    q1 = data.get("q1_answer", "")
    q2 = message.text
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or ""
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO applications (telegram_user_id, q1_text, q2_text)
            VALUES (?, ?, ?)
        """, (user_id, q1, q2))
        app_id = cursor.lastrowid
        await db.commit()
    
    logger.info(f"Application created: id={app_id}, telegram_user_id={user_id}")
    
    if APPLICATIONS_CHAT_ID:
        app_text = (
            f"<b>📨 Новая заявка #{app_id}</b>\n\n"
            f"<b>От:</b> {full_name}\n"
            f"<b>Username:</b> @{username if username else 'нет'}\n"
            f"<b>ID:</b> <code>{user_id}</code>\n\n"
            f"<b>Вопрос 1:</b> Есть ли у вас опыт?\n"
            f"<i>{q1}</i>\n\n"
            f"<b>Вопрос 2:</b> Откуда узнали о нас?\n"
            f"<i>{q2}</i>"
        )
        
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"approve:{user_id}:{app_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{user_id}:{app_id}")
            ]
        ])
        
        try:
            await bot.send_message(APPLICATIONS_CHAT_ID, app_text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            logger.error(f"Failed to send to applications chat: {e}")
    
    confirm_msg = await message.answer(
        "<b>✅ Заявка отправлена!</b>\n\n"
        "Ваша заявка принята на рассмотрение.\n"
        "Мы уведомим вас о решении в ближайшее время.\n\n"
        "<i>Обычно это занимает до 24 часов.</i>",
        parse_mode="HTML"
    )
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE applications SET confirm_message_id = ? WHERE id = ?", (confirm_msg.message_id, app_id))
        await db.commit()
    
    await state.clear()
