# Deployment Guide

This repository is structured for deployment on **Render** (API, Worker, DB) and **Vercel** (Frontend).

## 1. Database (Render PostgreSQL)

1. Create a **New PostgreSQL** on Render.
2. Copy the **Internal URL** (starts with `postgres://...`).
3. This is your `DATABASE_URL`.

---

## 2. API (Render Web Service)

1. Create a **New Web Service** connected to this repo.
2. **Settings**:
   - **Name**: `afisha-api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r api/requirements.txt && pip install -e .`
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
3. **Environment Variables**:
   - `DATABASE_URL`: (Paste from DB step)
   - `PYTHON_VERSION`: `3.11.0` (Recommended)

---

## 3. Telegram Bot (Render Background Worker)

1. Create a **New Background Worker** connected to this repo.
2. **Settings**:
   - **Name**: `afisha-bot`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r bots/requirements.txt && pip install -e .`
   - **Start Command**: `python bots/bot.py`
3. **Environment Variables**:
   - `DATABASE_URL`: (Paste from DB step)
   - `BOT_TOKEN`: (Your Telegram Bot Token)
   - `PYTHON_VERSION`: `3.11.0` (Recommended)

---

## 4. Frontend (Vercel)

1. Import project in Vercel.
2. **Settings**:
   - **Root Directory**: `web`
   - **Framework Preset**: `Next.js`
3. **Environment Variables**:
   - `NEXT_PUBLIC_API_URL`: `https://<YOUR-RENDER-API-URL>.onrender.com`

---

## 5. Local Development

1. Set `ENV=local` in your `.env` file to use local SQLite fallback (`data/app.db`).
2. Run `start.ps1` to launch everything.

> [!IMPORTANT]
> The `.env` file is NOT committed. You must manually add environment variables in the Render/Vercel dashboards.
