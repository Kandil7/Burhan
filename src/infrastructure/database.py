"""
Async database utilities for Athar Islamic QA System.

Provides both async and sync database access with proper thread pool execution
for sync operations to avoid blocking the event loop.
"""

import asyncio
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Index, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()

# Create base class for models
Base = declarative_base()


# ==========================================
# Sync Database (for queries that need it)
# ==========================================


def get_sync_database_url() -> str:
    """Convert async URL to sync URL."""
    return settings.database_url.replace("+asyncpg", "+psycopg2")


# Create sync engine with connection pooling
sync_engine = create_engine(
    get_sync_database_url(),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    poolclass=NullPool if settings.is_production else None,
)

# Session factory
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine, class_=Session)


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """
    Get a synchronous database session with proper cleanup.

    Usage:
        with get_sync_session() as session:
            result = session.query(Model).all()
    """
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_in_thread(func):
    """
    Decorator/utility to run sync database operations in thread pool.

    Usage:
        async def get_data():
            return await run_in_thread(sync_query)
    """

    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    return wrapper


# ==========================================
# Database Models with Indexes
# ==========================================


class QuranModels:
    """Database models for Quran data."""

    @staticmethod
    def create_tables():
        """Create all tables with indexes."""
        # Import here to avoid circular imports

        Base.metadata.create_all(bind=sync_engine)
        logger.info("database.tables_created")

    @staticmethod
    def create_indexes():
        """Create performance indexes."""
        from src.data.models.quran import Ayah, Surah, Tafsir, Translation

        # Create indexes
        indexes = [
            # Surah indexes
            Index("idx_surah_number", Surah.number),
            # Ayah indexes
            Index("idx_ayah_surah", Ayah.surah_id),
            Index("idx_ayah_surah_number", Ayah.surah_id, Ayah.number_in_surah),
            Index("idx_ayah_juz", Ayah.juz),
            Index("idx_ayah_page", Ayah.page),
            Index(
                "idx_ayah_text_uthmani",
                Ayah.text_uthmani,
                postgresql_using="gin",
                postgresql_ops={"text_uthmani": "gin_trgm_ops"},
            ),
            # Translation indexes
            Index("idx_translation_ayah", Translation.ayah_id),
            Index("idx_translation_language", Translation.language),
            # Tafsir indexes
            Index("idx_tafsir_ayah", Tafsir.ayah_id),
            Index("idx_tafsir_source", Tafsir.source),
        ]

        for index in indexes:
            try:
                index.create(sync_engine)
                logger.info("database.index_created", index=index.name)
            except Exception as e:
                logger.warning("database.index_create_error", index=index.name, error=str(e))


# ==========================================
# Async Database (for high-throughput scenarios)
# ==========================================


class AsyncDatabaseManager:
    """
    Async database manager for high-throughput scenarios.

    Uses asyncpg directly for better performance.
    """

    def __init__(self):
        self._pool: object | None = None

    async def initialize(self):
        """Initialize async connection pool."""
        try:
            from urllib.parse import urlparse

            import asyncpg

            # Parse DATABASE_URL for connection parameters
            parsed = urlparse(settings.database_url)
            self._pool = await asyncpg.create_pool(
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                user=parsed.username or "athar",
                password=parsed.password,
                database=parsed.path.lstrip("/") or "athar_db",
                min_size=5,
                max_size=20,
            )
            logger.info("database.async_pool_initialized")
        except Exception as e:
            logger.error("database.async_pool_error", error=str(e))
            raise

    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("database.async_pool_closed")

    async def fetch(self, query: str, *args):
        """Execute query and fetch results."""
        if not self._pool:
            raise RuntimeError("Database not initialized")

        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Execute query and fetch single row."""
        if not self._pool:
            raise RuntimeError("Database not initialized")

        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        """Execute query without returning results."""
        if not self._pool:
            raise RuntimeError("Database not initialized")

        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)


# Global async database instance
_async_db: AsyncDatabaseManager | None = None


async def get_async_db() -> AsyncDatabaseManager:
    """Get async database manager instance."""
    global _async_db
    if _async_db is None:
        _async_db = AsyncDatabaseManager()
    return _async_db
