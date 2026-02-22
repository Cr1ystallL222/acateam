from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import logger
from api.database import ensure_schema
from api.utils import global_exception_handler
from api.routes import auth, movies, orders, referral, events, topup, support, coupons
from data.db import db

# Disable redirect_slashes to prevent 307 redirects that lose cookies
app = FastAPI(redirect_slashes=False)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Exception Handler
app.add_exception_handler(Exception, global_exception_handler)

# Register Routes
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(orders.router)
app.include_router(referral.router)
app.include_router(events.router)
app.include_router(topup.router)
app.include_router(support.router)
app.include_router(coupons.router)
from api.routes import logging
app.include_router(logging.router)

from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
project_root = Path(__file__).parent.parent
uploads_dir = project_root / "data" / "uploads"
logger.info(f"Mounting uploads dir: {uploads_dir} (Exists: {uploads_dir.exists()})")
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

@app.on_event("startup")
async def startup():
    await db.connect()
    logger.info("API DB connected.")
    await ensure_schema()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "API is running. Frontend at http://localhost:3000"}
