🎬 Afisha Cinema

Современная платформа бронирования кино с авторизацией через Telegram и реферальной системой.

Проект состоит из бэкенда (FastAPI), фронтенда (Next.js), Telegram-ботов и общей базы данных SQLite.

📦 Структура проекта
/api     — Backend (FastAPI, JSON API)
/web     — Frontend (Next.js, React)
/bots    — Telegram-боты (основной + бот авторизации)
/data    — База данных SQLite

🧱 Архитектура

Frontend: Next.js
URL: http://localhost:3000

Backend API: FastAPI
URL: http://127.0.0.1:8000

Database: SQLite
Файл: data/app.db
Используется всеми компонентами проекта

⚙️ Настройка окружения

Скопируйте файл окружения и заполните переменные:

cp .env.example .env

Обязательные переменные
Переменная	Описание
BOT_TOKEN	Токен основного Telegram-бота (реферальные ссылки)
AUTH_BOT_TOKEN	Токен бота авторизации
AUTH_BOT_USERNAME	Username бота авторизации (без @)
SITE_URL	URL фронтенда (по умолчанию http://localhost:3000)
DB_PATH	Путь к базе данных (./data/app.db)
▶️ Запуск проекта

Проект требует 4 параллельно запущенных процесса
(каждый — в отдельном терминале).

1️⃣ Backend API (порт 8000)
cd d:\Codes\4\112\nehuy\3
uvicorn api.main:app --reload --port 8000

2️⃣ Frontend (порт 3000)
cd d:\Codes\4\112\nehuy\3\web
npm install   # только при первом запуске
npm run dev

3️⃣ Основной Telegram-бот (рефералы)
cd d:\Codes\4\112\nehuy\3
python bots/bot.py

4️⃣ Telegram-бот авторизации
cd d:\Codes\4\112\nehuy\3
python bots/auth_bot.py

🔌 API эндпоинты

Все эндпоинты доступны по префиксу /api/*.

Метод	Endpoint	Описание
GET	/api/movies	Получить список фильмов
GET	/api/me	Информация о текущем пользователе
GET	/api/referral/track?ref=XXX	Отслеживание реферального перехода
POST	/api/register/draft	Начало регистрации
POST	/api/register/verify	Подтверждение кода регистрации
POST	/api/auth/telegram/start	Запуск Telegram-авторизации
POST	/api/auth/telegram/verify	Проверка кода авторизации
POST	/api/orders/pay	Оплата заказа
🔁 Прокси Frontend → Backend

Next.js проксирует запросы /api/* на FastAPI через next.config.ts:

rewrites: [
  {
    source: "/api/:path*",
    destination: "http://127.0.0.1:8000/api/:path*",
  },
]


Это позволяет фронтенду работать с API без CORS и хардкода URL.

✅ Проверка работы

После запуска всех компонентов:

API доступен

curl http://127.0.0.1:8000/


Ожидаемый ответ:

{ "status": "ok" }


Список фильмов

curl http://127.0.0.1:8000/api/movies


Фронтенд

Откройте: http://localhost:3000

Должен отобразиться интерфейс киноафиши

Реферальная система

Перейдите по ссылке:

http://localhost:3000/?ref=XXXX


В Telegram должно прийти уведомление

🛠 Технологический стек

Backend

FastAPI

aiosqlite

httpx

Frontend

Next.js 14

React

Framer Motion

Bots

aiogram 3.x

Database

SQLite

📌 Примечания

База данных общая для API, фронтенда и ботов

Авторизация и регистрация происходят через Telegram

Проект рассчитан на локальную разработку (dev-режим)