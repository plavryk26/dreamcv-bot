# dreamcv_bot MVP (aiogram + OpenAI + сохранение)

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging
import openai
import json
import os
from datetime import datetime

API_TOKEN = '7118757045:AAEM0f4WjBD4j7Ra18PhzvOtmyQO4Xzq4QQ'
OPENAI_API_KEY = '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'
openai.api_key = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

DATA_FILE = 'user_data.json'

def save_user_content(user_id, content_type, content):
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}

    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = []

    data[user_id_str].append({
        "type": content_type,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "content": content
    })

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(
    KeyboardButton("✏️ Создать резюме"),
    KeyboardButton("📄 Сопроводительное письмо"),
    KeyboardButton("🎓 Подготовка к собеседованию")
)

class CoverLetterState(StatesGroup):
    waiting_for_job_text = State()
    waiting_for_name = State()
    waiting_for_experience = State()
    waiting_for_skills = State()

class ResumeState(StatesGroup):
    waiting_for_name = State()
    waiting_for_contacts = State()
    waiting_for_goal = State()
    waiting_for_education = State()
    waiting_for_experience = State()
    waiting_for_skills = State()
    waiting_for_extra = State()

@dp.message_handler(CommandStart())
async def send_welcome(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в DreamCV!\n\n"
        "Я помогу вам создать резюме, сопроводительное письмо и подготовиться к собеседованию.\n\n"
        "Что вы хотите сделать?",
        reply_markup=main_menu
    )

@dp.message_handler(commands=['history'])
async def show_history(message: types.Message):
    user_id = str(message.from_user.id)
    if not os.path.exists(DATA_FILE):
        await message.answer("У вас пока нет сохранённых документов.")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if user_id not in data or not data[user_id]:
        await message.answer("У вас пока нет сохранённых документов.")
        return

    reply = "📂 Ваши сохранённые материалы:\n\n"
    for i, item in enumerate(data[user_id], start=1):
        reply += f"{i}. [{item['type'].capitalize()} | {item['created']}]\n{item['content'][:200]}...\n\n"

    await message.answer(reply)

@dp.message_handler(lambda message: message.text == "✏️ Создать резюме")
async def create_resume(message: types.Message):
    await message.answer("Отлично! Начнём. Как вас зовут?")
    await ResumeState.waiting_for_name.set()

@dp.message_handler(state=ResumeState.waiting_for_name)
async def resume_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите контактную информацию (телефон, email, город):")
    await ResumeState.waiting_for_contacts.set()

@dp.message_handler(state=ResumeState.waiting_for_contacts)
async def resume_contacts(message: types.Message, state: FSMContext):
    await state.update_data(contacts=message.text)
    await message.answer("Цель резюме: на какую должность вы претендуете?")
    await ResumeState.waiting_for_goal.set()

@dp.message_handler(state=ResumeState.waiting_for_goal)
async def resume_goal(message: types.Message, state: FSMContext):
    await state.update_data(goal=message.text)
    await message.answer("Опишите ваше образование:")
    await ResumeState.waiting_for_education.set()

@dp.message_handler(state=ResumeState.waiting_for_education)
async def resume_education(message: types.Message, state: FSMContext):
    await state.update_data(education=message.text)
    await message.answer("Опишите ваш опыт работы:")
    await ResumeState.waiting_for_experience.set()

@dp.message_handler(state=ResumeState.waiting_for_experience)
async def resume_experience(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await message.answer("Укажите ключевые навыки:")
    await ResumeState.waiting_for_skills.set()

@dp.message_handler(state=ResumeState.waiting_for_skills)
async def resume_skills(message: types.Message, state: FSMContext):
    await state.update_data(skills=message.text)
    await message.answer("Дополнительная информация (языки, хобби и т.д.):")
    await ResumeState.waiting_for_extra.set()

@dp.message_handler(state=ResumeState.waiting_for_extra)
async def resume_extra(message: types.Message, state: FSMContext):
    await state.update_data(extra=message.text)
    data = await state.get_data()
    prompt = f"""
Составь профессиональное резюме на русском языке по следующим данным:

Имя: {data['name']}
Контакты: {data['contacts']}
Цель: {data['goal']}
Образование: {data['education']}
Опыт: {data['experience']}
Навыки: {data['skills']}
Дополнительно: {data['extra']}

Резюме должно быть структурированным, с заголовками и лаконичным изложением. Без лишней воды. Под формат Word или PDF.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    resume = response.choices[0].message.content.strip()
    save_user_content(message.from_user.id, "resume", resume)
    await message.answer("Ваше сгенерированное резюме:\n\n" + resume)
    await state.finish()

@dp.message_handler(lambda message: message.text == "📄 Сопроводительное письмо")
async def start_cover_letter(message: types.Message):
    await message.answer("Для какой вакансии нужно сопроводительное письмо? Отправьте ссылку или текст описания.")
    await CoverLetterState.waiting_for_job_text.set()

@dp.message_handler(state=CoverLetterState.waiting_for_job_text)
async def process_job_text(message: types.Message, state: FSMContext):
    await state.update_data(job_text=message.text)
    await message.answer("Как вас зовут? (Имя и фамилия)")
    await CoverLetterState.waiting_for_name.set()

@dp.message_handler(state=CoverLetterState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Опишите ваш опыт в 1-2 предложениях")
    await CoverLetterState.waiting_for_experience.set()

@dp.message_handler(state=CoverLetterState.waiting_for_experience)
async def process_experience(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await message.answer("Какие ключевые навыки у вас есть?")
    await CoverLetterState.waiting_for_skills.set()

@dp.message_handler(state=CoverLetterState.waiting_for_skills)
async def process_skills(message: types.Message, state: FSMContext):
    await state.update_data(skills=message.text)
    data = await state.get_data()
    prompt = f"""
Выступи в роли карьерного консультанта.
Создай вежливое и персонализированное сопроводительное письмо на русском языке по следующему описанию вакансии:

Описание вакансии:
{data['job_text']}

Информация о кандидате:
Имя: {data['name']}
Опыт: {data['experience']}
Навыки: {data['skills']}

Сделай письмо кратким (до 200 слов), без воды, с акцентом на мотивацию и релевантные навыки.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    reply = response.choices[0].message.content.strip()
    save_user_content(message.from_user.id, "cover_letter", reply)
    await message.answer("Вот ваше сопроводительное письмо:\n\n" + reply)
    await state.finish()

@dp.message_handler(lambda message: message.text == "🎓 Подготовка к собеседованию")
async def interview_prep(message: types.Message):
    await message.answer("DreamCV задаст вам несколько типовых вопросов для тренировки. Готовы? Отпишите \"Готов\" или \"Нет\".")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
