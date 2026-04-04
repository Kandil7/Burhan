"""
Redis client for Athar Islamic QA system.

Provides async Redis connection for caching, session management,
and rate limiting.
"""
from typing import Optional
import redis.asyncio as redis

from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger()

# Global Redis client
redis_client: Optional[redis.Redis] = None


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


async def cache_get(key: str) -> Optional[str]:
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
