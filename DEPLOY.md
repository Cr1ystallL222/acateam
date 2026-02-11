# Деплой: VPS + Render + Vercel

## Архитектура

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  VPS        │     │  Render      │     │  Vercel      │
│  Боты       │────▶│  API + БД    │◀────│  Фронтенд    │
│  (polling)  │     │  (PostgreSQL)│     │  (Next.js)   │
└─────────────┘     └──────────────┘     └──────────────┘
```

---

## 1. БД — Render PostgreSQL

1. **Render Dashboard** → New → PostgreSQL
2. Скопировать **Internal Database URL** (для API на том же Render)
3. Скопировать **External Database URL** (для ботов на VPS)
   ```
   # Для API (internal, быстрее):
   DATABASE_URL=postgresql://user:pass@dpg-xxx.internal:5432/dbname

   # Для ботов на VPS (external):
   DATABASE_URL=postgresql://user:pass@dpg-xxx.oregon-postgres.render.com:5432/dbname
   ```

> ⚠️ Бесплатная PostgreSQL на Render удаляется через 90 дней. Платная — от $7/мес.

---

## 2. API — Render Web Service

1. **Render Dashboard** → New → Web Service
2. Подключить GitHub репозиторий
3. Настройки:
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables**:
   ```
   DATABASE_URL=postgresql://user:pass@dpg-xxx.internal:5432/dbname
   BOT_TOKEN=токен_основного_бота
   MAIN_BOT_TOKEN=токен_основного_бота
   AUTH_BOT_TOKEN=токен_авт_бота
   TOPUP_GROUP_ID=-100xxxxxxxxx
   SUPPORT_CHAT_ID=-100xxxxxxxxx
   ```

### Проверка
- `GET https://your-api.onrender.com/health` → `{"status": "ok"}`
- Логи: `"Connected to PostgreSQL"` и `"API DB connected."`

---

## 3. Боты — VPS

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/your/repo.git && cd repo

# Установить зависимости
pip install -r requirements.txt

# Настроить .env
cp .env.example .env
nano .env
```

### .env на VPS

```bash
# ВАЖНО: использовать External URL (не internal!)
DATABASE_URL=postgresql://user:pass@dpg-xxx.oregon-postgres.render.com:5432/dbname

BOT_TOKEN=токен_основного_бота
MAIN_BOT_TOKEN=токен_основного_бота
AUTH_BOT_TOKEN=токен_авт_бота
BOT_USERNAME=имя_авт_бота
ADMIN_IDS=123456789,987654321
SITE_URL=https://your-domain.vercel.app
TOPUP_GROUP_ID=-100xxxxxxxxx
SUPPORT_CHAT_ID=-100xxxxxxxxx
```

### Запуск через systemd

**Основной бот** — `/etc/systemd/system/main-bot.service`:
```ini
[Unit]
Description=Main Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/repo
ExecStart=/home/ubuntu/repo/venv/bin/python -m bots.bot
Restart=always
RestartSec=5
EnvironmentFile=/home/ubuntu/repo/.env

[Install]
WantedBy=multi-user.target
```

**Авторизационный бот** — `/etc/systemd/system/auth-bot.service`:
```ini
[Unit]
Description=Auth Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/repo
ExecStart=/home/ubuntu/repo/venv/bin/python -m bots.auth_bot
Restart=always
RestartSec=5
EnvironmentFile=/home/ubuntu/repo/.env

[Install]
WantedBy=multi-user.target
```

```bash
# Активировать и запустить
sudo systemctl daemon-reload
sudo systemctl enable main-bot auth-bot
sudo systemctl start main-bot auth-bot

# Проверить статус
sudo systemctl status main-bot
sudo systemctl status auth-bot

# Логи
journalctl -u main-bot -f
journalctl -u auth-bot -f
```

---

## 4. Фронтенд — Vercel

1. **Vercel Dashboard** → Import Git Repository
2. **Root Directory**: `web/`
3. **Framework**: Next.js (авто)
4. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://your-api.onrender.com
   ```

### CORS

В `api/main.py` указать домен Vercel:
```python
allow_origins=["https://your-domain.vercel.app", "http://localhost:3000"]
```

---

## 5. Чеклист

- [ ] Render PostgreSQL создан
- [ ] API на Render запущен с **Internal** DATABASE_URL
- [ ] Боты на VPS запущены с **External** DATABASE_URL
- [ ] CORS в `api/main.py` включает домен Vercel
- [ ] `SITE_URL` в `.env` на VPS = домен Vercel
- [ ] Фронтенд на Vercel видит API (`NEXT_PUBLIC_API_URL`)





DATABASE_URL	(Internal URL из Render PostgreSQL)
BOT_TOKEN	
MAIN_BOT_TOKEN	
AUTH_BOT_TOKEN	
BOT_USERNAME	
TOPUP_GROUP_ID	
SUPPORT_CHAT_ID	
ADMIN_IDS	
SITE_URL	