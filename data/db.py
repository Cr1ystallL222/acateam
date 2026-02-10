"""
Shared database engine and session factory for PostgreSQL (Render).

Requires DATABASE_URL environment variable in production.
In local development, set ENV=local to fall back to SQLite.
"""

import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
ENV = os.getenv("ENV", "production")

# Render gives postgres:// but SQLAlchemy 2.x needs postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    if ENV == "local":
        # Local development fallback — SQLite in data/app.db
        _db_path = os.path.join(os.path.dirname(__file__), "app.db")
        DATABASE_URL = f"sqlite:///{_db_path}"
    else:
        print(
            "FATAL: DATABASE_URL is not set. "
            "Set DATABASE_URL for production or set ENV=local for local SQLite fallback.",
            file=sys.stderr,
        )
        sys.exit(1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
