"""
Redis client for Burhan Islamic QA system.

Provides async Redis connection for caching, session management,
and rate limiting.

Phase 9 Enhancement:
- Added RedisManager class for better connection management
- Added connection pool management
- Added health check and reconnection
"""

from __future__ import annotations

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()


# ==========================================
# Redis Manager Class
# ==========================================


class RedisManager:
    """
    Redis manager with connection pooling.

    Phase 9: Enhanced with connection management.

    Usage:
        manager = RedisManager(url=settings.redis_url)
        await manager.initialize()

        client = await manager.get_client()
        await client.set("key", "value")

        await manager.close()
    """

    def __init__(
        self,
        url: str | None = None,
        max_connections: int = 10,
        decode_responses: bool = True,
    ):
        self.url = url or settings.redis_url
        self.max_connections = max_connections
        self.decode_responses = decode_responses

        self._pool: ConnectionPool | None = None
        self._client: redis.Redis | None = None
        self._initialized = False
        self._available = True

    async def initialize(self) -> None:
        """Initialize Redis connection pool."""
        if self._initialized:
            return

        try:
            self._pool = ConnectionPool.from_url(
                self.url,
                max_connections=self.max_connections,
                decode_responses=self.decode_responses,
                health_check_interval=30,
            )
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            await self._client.ping()

            self._initialized = True
            self._available = True
            logger.info("redis.initialized", url=self.url)

        except Exception as e:
            logger.error("redis.init_error", error=str(e))
            self._available = False
            self._initialized = True  # Mark as initialized but not available

    async def get_client(self) -> redis.Redis | None:
        """Get Redis client."""
        if not self._initialized:
            await self.initialize()
        return self._client

    async def ping(self) -> bool:
        """Ping Redis server."""
        if not self._client:
            return False

        try:
            await self._client.ping()
            self._available = True
            return True
        except Exception as e:
            logger.warning("redis.ping_error", error=str(e))
            self._available = False
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

        if self._pool:
            await self._pool.disconnect()
            self._pool = None

        self._initialized = False
        self._available = False
        logger.info("redis.closed")

    @property
    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self._available

    @property
    def is_initialized(self) -> bool:
        """Check if Redis is initialized."""
        return self._initialized


# ==========================================
# Legacy Functions (backward compatibility)
# ==========================================

# Global Redis client
redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """
    Get or create Redis client instance.

    Usage:
        redis = await get_redis()
        await redis.set("key", "value", ex=3600)
        value = await redis.get("key")
    """
    global redis_client

    if redis_client is None:
        redis_client = redis.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
            health_check_interval=30,
        )

    return redis_client


async def init_redis():
    """
    Initialize Redis connection.

    Phase 1: Verify connection
    Phase 2+: Test connection health
    """
    try:
        client = await get_redis()
        await client.ping()
        logger.info("redis.connected", url=settings.redis_url)

    except Exception as e:
        logger.error("redis.connection_error", error=str(e))
        # Don't raise - Redis is optional in Phase 1
        logger.warning("redis.running_without_redis")


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("redis.disconnected")


async def cache_get(key: str) -> str | None:
    """
    Get value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None
    """
    try:
        client = await get_redis()
        value = await client.get(key)
        if value:
            logger.debug("cache.hit", key=key)
        return value
    except Exception as e:
        logger.error("cache.get_error", key=key, error=str(e))
        return None


async def cache_set(key: str, value: str, ttl: int = 3600):
    """
    Set value in cache with TTL.

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default: 1 hour)
    """
    try:
        client = await get_redis()
        await client.setex(key, ttl, value)
        logger.debug("cache.set", key=key, ttl=ttl)
    except Exception as e:
        logger.error("cache.set_error", key=key, error=str(e))


async def cache_delete(key: str):
    """
    Delete value from cache.

    Args:
        key: Cache key
    """
    try:
        client = await get_redis()
        await client.delete(key)
        logger.debug("cache.delete", key=key)
    except Exception as e:
        logger.error("cache.delete_error", key=key, error=str(e))
