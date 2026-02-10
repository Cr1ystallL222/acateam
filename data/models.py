"""
Shared SQLAlchemy models for PostgreSQL.

These models are used by both api/ and bots/ via the shared data layer.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "shared_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(String, unique=True, nullable=False, index=True)

    def __repr__(self):
        return f"<User(id={self.id}, tg_id={self.tg_id})>"
