# Afisha Cinema Project

A modern cinema booking platform with Telegram authentication and referral system.

## Project Structure

```
/api     — Backend (FastAPI) - JSON API only
/web     — Frontend (Next.js React)
/bots    — Telegram bots (main bot + auth bot)
/data    — SQLite database
```

## Architecture

- **Frontend**: Next.js on `http://localhost:3000`
- **Backend API**: FastAPI on `http://127.0.0.1:8000`
- **Database**: SQLite (`data/app.db`) - shared between all components

## Environment Setup

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Required variables:
- `BOT_TOKEN` - Main Telegram bot token (for referral links)
- `AUTH_BOT_TOKEN` - Auth bot token (for login verification)
- `AUTH_BOT_USERNAME` - Auth bot username (without @)
- `SITE_URL` - Frontend URL (default: http://localhost:3000)
- `DB_PATH` - Database path (default: ./data/app.db)

## Running the Project

Start 4 processes in separate terminals:

### 1. Backend API (port 8000)

```bash
cd d:\Codes\4\112\nehuy\3
uvicorn api.main:app --reload --port 8000
```

### 2. Frontend (port 3000)

```bash
cd d:\Codes\4\112\nehuy\3\web
npm install  # first time only
npm run dev
```

### 3. Main Telegram Bot (referrals)

```bash
cd d:\Codes\4\112\nehuy\3
python bots/bot.py
```

### 4. Auth Telegram Bot (login/registration)

```bash
cd d:\Codes\4\112\nehuy\3
python bots/auth_bot.py
```

## API Endpoints

All API endpoints are under `/api/*`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/movies` | List of movies |
| GET | `/api/me` | Current user info |
| GET | `/api/referral/track?ref=XXX` | Track referral visit |
| POST | `/api/register/draft` | Start registration |
| POST | `/api/register/verify` | Verify code & complete registration |
| POST | `/api/auth/telegram/start` | Start auth session |
| POST | `/api/auth/telegram/verify` | Verify auth code |
| POST | `/api/orders/pay` | Process payment |

## Frontend → API Proxy

Next.js proxies all `/api/*` requests to the backend via rewrites in `next.config.ts`:

```typescript
rewrites: [{
  source: "/api/:path*",
  destination: "http://127.0.0.1:8000/api/:path*",
}]
```

## Verification

After starting all 4 processes:

1. **API Check**: `curl http://127.0.0.1:8000/` → Should return JSON `{"status": "ok", ...}`
2. **API Movies**: `curl http://127.0.0.1:8000/api/movies` → Should return JSON array
3. **Frontend**: Open `http://localhost:3000` → Should show cinema interface
4. **Referral**: Open `http://localhost:3000/?ref=XXXX` → Should trigger Telegram notification

## Tech Stack

- **Backend**: FastAPI, aiosqlite, httpx
- **Frontend**: Next.js 14, React, Framer Motion
- **Bots**: aiogram 3.x
- **Database**: SQLite
