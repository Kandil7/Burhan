"""
Synchronous database connection for Quran module.

The Quran module uses synchronous SQLAlchemy
because it doesn't need async I/O (simple queries).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config.settings import settings

# Convert async URL to sync URL
sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")

engine = create_engine(
    sync_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine, class_=Session)


def get_sync_session() -> Session:
    """Get a synchronous database session."""
    return SessionLocal()
