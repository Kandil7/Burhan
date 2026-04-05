"""
Database connection management for Athar Islamic QA system.

Provides async SQLAlchemy engine and session management for PostgreSQL.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import declarative_base

from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger()

# ==========================================
# Engine and Session
# ==========================================
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before use
    echo=settings.debug,  # Log SQL in development
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for ORM models
Base = declarative_base()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database connection and create tables.
    
    Phase 1: Verify connection
    Phase 2+: Run migrations, create tables
    """
    try:
        async with engine.begin() as conn:
            # Phase 1: Just verify connection
            await conn.execute("SELECT 1")
            logger.info("database.connected", url=settings.database_url)
            
            # Phase 2: Create tables from models
            # await conn.run_sync(Base.metadata.create_all)
            
    except Exception as e:
        logger.error("database.connection_error", error=str(e))
        raise


async def close_db():
    """Close database connection."""
    await engine.dispose()
    logger.info("database.disconnected")
