import asyncio
import random

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
import sqlite3
import aiohttp
import logging
import requests

bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)                                # Устанавливаем уровень логирования

# Создаем кнопки
button_registr = KeyboardButton(text="Регистрация в телеграм боте")
button_exchange_rates = KeyboardButton(text="Курс валют")
button_tips = KeyboardButton(text="Советы по экономии")
button_finances = KeyboardButton(text="Личные финансы")

# Создаем Reply-клавиатуру с кнопками
keyboards = ReplyKeyboardMarkup(keyboard=[
    [button_registr, button_exchange_rates],
    [button_tips, button_finances]
    ], resize_keyboard=True)

conn = sqlite3.connect('user.db')                                     # Подключаемся к базе данных
cursor = conn.cursor()                                                # Создаем курсор

# Создаем таблицу пользователей в базе данных (3 поля категории, 3 поля расхода)
cursor.execute('''                                                     
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    name TEXT,
    category1 TEXT,
    category2 TEXT,
    category3 TEXT,
    expenses1 REAL,
    expenses2 REAL,
    expenses3 REAL
    )
''')

conn.commit()                                                          # Сохраняем изменения в базе данных

# Классы состояний для категорий и расходов
class FinancesForm(StatesGroup):                                       # Создаем класс состояний для категорий и расходов
    category1 = State()
    expenses1 = State()
    category2 = State()
    expenses2 = State()
    category3 = State()
    expenses3 = State()



# Асинхронная Функция обработки команды /start
@dp.message(Command('start'))
async def send_start(message: Message):
    await message.answer("Привет! Я ваш личный финансовый помощник. Выберите одну из опций в меню:", reply_markup=keyboards)  # Отображаем клавиатуру с кнопками при команде /start

# Асинхронная функция обработки команды "Регистрация в телеграм боте"
@dp.message(F.text == "Регистрация в телеграм боте")                                                                    # Функция "Регистрация в телеграм боте"
async def registration(message: Message):                                                                               # создаем асинхронную функцию registration
    telegram_id = message.from_user.id                                                                                  # сохраняем id пользователя в переменную telegram_id который оотправил сообщение
    name = message.from_user.full_name                                                                                  # сохраняем полное имя пользователя
    cursor.execute('''SELECT * FROM users WHERE telegram_id = ?''', (telegram_id,))                     # проверяем есть ли такой пользователь с таким id в базе данных
    user = cursor.fetchone()                                                                                            # если есть, то получаем его данные
    if user:
        await message.answer("Вы уже зарегистрированы!")                                                                # если пользователь есть, то выводим сообщение
    else:
        cursor.execute('''INSERT INTO users (telegram_id, name) VALUES (?, ?)''', (telegram_id, name))  # если пользователь нет, то создаем его
        conn.commit()                                                                                                   # сохраняем изменения
        await message.answer("Вы успешно зарегистрированы!")                                                            # выводим сообщение

# Асинхронная функция обработки команды "Курс валют"
@dp.message(F.text == "Курс валют")
async def exchange_rates(message: Message):                                                                             # функция обработки команды "Курс валют" exchange_rates
    url = "https://v6.exchangerate-api.com/v6/09edf8b2bb246e1f801cbfba/latest/USD"                                      # URL для получения данных о курсе валют USD c сайта ExchangeRate-API
    try:                                                                                                                # конструкция try-except для обработки исключений
        response = requests.get(url)                                                                                    # отправляем GET-запрос по адресу URL с данными о курсе валют
        data = response.json()                                                                                          # сохраняем данные о курсе валют
        if response.status_code != 200:                                                                                 # если код ответа не 200
            await message.answer("Не удалось получить данные о курсе валют!")                                           # выводим сообщение
            return                                                                                                      # выходим из функции
        usd_to_rub = data['conversion_rates']['RUB']                                                                    # сохраняем данные о USD в RUB
        eur_to_usd = data['conversion_rates']['EUR']                                                                    # сохраняем данные о EUR в USD
        euro_to_rub = eur_to_usd * usd_to_rub                                                                           # переводим о EUR в RUB

        await message.answer(f"1 USD - {usd_to_rub:.2f}  RUB\n"                                                         # выводим цену 1 USD в RUB (.2f округляет до 2 знаков после запяты)
                             f"1 EUR - {euro_to_rub:.2f}  RUB")                                                         # выводим цену 1 EUR в RUB (.2f округляет до 2 знаков после запяты)


    except:
        await message.answer("Произошла ошибка")                                                                        # выводим сообщение о ошибке

# Асинхронная функция обработки команды "Советы по экономии"
@dp.message(F.text == "Советы по экономии")
async def send_tips(message: Message):
    tips = [                                                                                                            # список советов
        "Совет 1: Ведите бюджет и следите за своими расходами.",
        "Совет 2: Откладывайте часть доходов на сбережения.",
        "Совет 3: Покупайте товары по скидкам и распродажам."
    ]
    tip = random.choice(tips)                                                                                           # сохраняем случайный совет из списка советов
    await message.answer(tip)                                                                                           # выводим случайный совет

# Создаём асинхронную функцию для работы с личными финансами
@dp.message(F.text == "Личные финансы")
async def finances(message: Message, state: FSMContext):                                                                # функция  "Личные финансы" finances состояний
    await state.set_state(FinancesForm.category1)                                                                       # устанавливаем новое состояние FinancesForm.category1
    await message.reply("Введите первую категорию расходов:")                                                           # выводим сообщение

#  функция для расходов по первой категории
@dp.message(FinancesForm.category1)
async def finances(message: Message, state: FSMContext):                                                                # функция обработки состояний категорий и расходов
    await state.update_data(category1 = message.text)                                                                   # сохраняем категорию расходов
    await state.set_state(FinancesForm.expenses1)                                                                       # устанавливаем новое состояние FinancesForm.expenses1
    await message.reply("Введите расходы для категории 1:")                                                             # выводим сообщение

# функция обработки состояний категории 2 и расходов
@dp.message(FinancesForm.expenses1)
async def finances(message: Message, state: FSMContext):
    await state.update_data(expenses1 = float(message.text))
    await state.set_state(FinancesForm.category2)
    await message.reply("Введите вторую категорию расходов:")

# функция обработки состояний категории 2 и расходов
@dp.message(FinancesForm.category2)
async def finances(message: Message, state: FSMContext):
    await state.update_data(category2 = message.text)
    await state.set_state(FinancesForm.expenses2)
    await message.reply("Введите расходы для категории 2:")

# функция обработки состояний категории 3 и расходов
@dp.message(FinancesForm.expenses2)
async def finances(message: Message, state: FSMContext):
    await state.update_data(expenses2 = float(message.text))
    await state.set_state(FinancesForm.category3)
    await message.reply("Введите третью категорию расходов:")

# функция обработки состояний категории 3 и расходов
@dp.message(FinancesForm.category3)
async def finances(message: Message, state: FSMContext):
    await state.update_data(category3 = message.text)
    await state.set_state(FinancesForm.expenses3)
    await message.reply("Введите расходы для категории 3:")

# функция Сохраняем изменения. Очищаем состояния. Прописываем сообщение о сохранении категорий и расходов.
@dp.message(FinancesForm.expenses3)
async def finances(message: Message, state: FSMContext):
    data = await state.get_data()                                                                                       # сохраняем всю информацию по состояниям
    telegarm_id = message.from_user.id                                                                                  # сохраняем информацию
    cursor.execute('''UPDATE users SET category1 = ?, expenses1 = ?, category2 = ?, expenses2 = ?, category3 = ?, expenses3 = ? WHERE telegram_id = ?''',
                   (data['category1'], data['expenses1'], data['category2'], data['expenses2'], data['category3'], float(message.text), telegarm_id))
    conn.commit()                                                                                                       # сохраняем изменения
    await state.clear()                                                                                                 # очищаем состояние

    await message.answer("Категории и расходы сохранены!")                                                              # выводим сообщение


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())