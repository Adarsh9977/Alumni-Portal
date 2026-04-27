import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set to a PostgreSQL connection string")

# Fix postgres URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# REMOVE pg8000
if "postgresql+pg8000" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+pg8000", "postgresql")

if not DATABASE_URL.startswith("postgresql://"):
    raise RuntimeError("DATABASE_URL must use PostgreSQL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()