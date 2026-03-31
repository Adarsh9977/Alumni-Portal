# database.py - Database configuration and session management

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Cloud Ready Database Configuration
# Uses PostgreSQL in production (Vercel) and SQLite for local development
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or "sqlite:////tmp/alumni_portal.db"

# Fix for Heroku/Vercel Postgres URLs (postgres:// -> postgresql://)
if DATABASE_URL and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)

# Only use check_same_thread for SQLite
engine_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {"connect_timeout": 3}

engine = create_engine(DATABASE_URL, connect_args=engine_args)

# Create a configured session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Ensures the session is closed after the request is complete.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
