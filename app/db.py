from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

from .config import settings

# Get database URL with fallback
database_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# Configure engine for PostgreSQL with proper connection pooling
engine = create_engine(
    database_url, 
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Set to True for SQL query logging in development
)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
