
<div align="center">

# 🎬 Afisha Cinema

**Современная платформа бронирования кинобилетов**  
*с интеграцией Telegram и реферальной системой*

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-black?style=for-the-badge&logo=next.js&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

</div>

---

## 📖 О проекте

**Afisha Cinema** — это fullstack-приложение для бронирования билетов в кино. Проект демонстрирует бесшовную интеграцию между веб-интерфейсом и Telegram-ботами.

**Ключевые особенности:**
*   🔐 **Авторизация через Telegram** — без паролей и SMS.
*   🎟 **Покупка билетов** — удобный выбор фильмов и мест.
*   🤝 **Реферальная система** — приглашайте друзей и получайте бонусы.
*   🤖 **Умные боты** — уведомления о бронировании и рефералах.

---

## 📦 Структура проекта

```graphql
.
├── 📂 api          # Backend (FastAPI, JSON API)
├── 📂 web          # Frontend (Next.js 14, React)
├── 📂 bots         # Telegram-боты (Main + Auth)
└── 📂 data         # База данных SQLite (shared)
```

---

## 🧱 Архитектура и Связи

| Компонент | Технология | Порт/URL | Описание |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js | `http://localhost:3000` | Веб-интерфейс пользователя |
| **Backend** | FastAPI | `http://127.0.0.1:8000` | REST API для данных и логики |
| **Database** | SQLite | `./data/app.db` | Общее хранилище данных |
| **Bots** | Aiogram 3 | *Polling* | Взаимодействие с пользователем в TG |

---

## ⚙️ Настройка окружения

1.  **Создайте файл `.env`** в корне проекта:

    ```bash
    cp .env.example .env
    ```

2.  **Заполните переменные:**

    | Переменная | Описание |
    | :--- | :--- |
    | `BOT_TOKEN` | Токен основного бота (уведомления, рефералы) |
    | `AUTH_BOT_TOKEN` | Токен бота авторизации (логин) |
    | `AUTH_BOT_USERNAME` | Username бота авторизации (без @) |
    | `SITE_URL` | Адрес фронтенда (default: `http://localhost:3000`) |
    | `DB_PATH` | Путь к БД (default: `./data/app.db`) |

---

## ▶️ Запуск проекта

Для работы системы необходимо запустить **4 процесса** (в отдельных терминалах):

### 1️⃣ Backend API
```powershell
uvicorn api.main:app --reload --port 8000
```

### 2️⃣ Frontend
```powershell
cd web
npm install  # только первый раз
npm run dev
```

### 3️⃣ Main Bot (Referrals & Notifications)
```powershell
python bots/bot.py
```

### 4️⃣ Auth Bot (Login Flow)
```powershell
python bots/auth_bot.py
```

---

## 🔌 API Эндпоинты

Все запросы к API проксируются через Next.js (`/api/*` -> `http://127.0.0.1:8000/api/*`).

| Метод | Эндпоинт | Описание |
| :--- | :--- | :--- |
| `GET` | `/api/movies` | Список доступных фильмов |
| `GET` | `/api/me` | Профиль текущего пользователя |
| `GET` | `/api/referral/track` | Трекинг реферальных ссылок (`?ref=...`) |
| `POST` | `/api/auth/telegram/start` | Инициализация входа через Telegram |
| `POST` | `/api/orders/pay` | Создание и оплата заказа |

> **Примечание:** Полная документация API доступна по адресу `http://127.0.0.1:8000/docs` (Swagger UI) при запущенном бэкенде.

---

## 🛠 Технологический стек

### Backend
*   **FastAPI** — быстрый асинхронный фреймворк.
*   **aiosqlite** — асинхронная работа с SQLite.
*   **Pydantic** — валидация данных.

### Frontend
*   **Next.js 14** (App Router).
*   **React** & **Hooks**.
*   **TailwindCSS** (предположительно, или модульный CSS).
*   **Framer Motion** — анимации.

### Telegram Bots
*   **Aiogram 3.x** — современный фреймворк для ботов.

---

## ✅ Проверка работоспособности

1.  **API:** Откройте `http://127.0.0.1:8000/`. Ответ: `{"status": "ok"}`.
2.  **Web:** Откройте `http://localhost:3000`. Должна загрузиться главная страница.
3.  **Логин:** Нажмите "Войти" на сайте -> переброс в бота -> подтверждение -> вход выполнен.
4.  **Рефералы:** Зайдите по ссылке вида `http://localhost:3000/?ref=YOUR_ID`. Бот должен прислать уведомление о переходе.

---

<div align="center">
  <sub>Developed by Cr1ystallL222</sub>
</div>