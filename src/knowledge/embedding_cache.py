"""
Embedding Cache for Athar Islamic QA system.

Redis-based caching for embedding vectors with connection pooling.
- TTL: 7 days
- Reduces redundant embedding generation
- Significant speedup for repeated queries
- Async Redis client to avoid blocking event loop

Phase 6 Refactoring:
- Converted from sync redis to redis.asyncio to prevent event loop blocking
- Proper async/await throughout
"""
import json
import pickle
from typing import Optional

import numpy as np
import redis.asyncio as redis  # Phase 6: Async Redis client

from src.config.settings import settings
from src.infrastructure.redis import get_redis
from src.config.logging_config import get_logger

logger = get_logger()


class EmbeddingCache:
    """
    Async Redis-based cache for embedding vectors with connection pooling.
    
    Phase 6 Refactoring: All methods are now async to use redis.asyncio
    
    Key format: "embedding:{sha256_hash}"
    Value: Serialized numpy array
    TTL: 7 days (604800 seconds)

    Usage:
        cache = EmbeddingCache()
        await cache.set("hash123", embedding_array)
        embedding = await cache.get("hash123")
    """

    TTL = 604800  # 7 days in seconds
    KEY_PREFIX = "embedding:"

    def __init__(self, max_connections: int = 10):
        """Initialize cache with async Redis connection pool and local dict fallback."""
        self._redis = None
        self._local_cache = {}  # Fallback when Redis unavailable
        self._redis_available = True  # Track Redis availability
        self._hits = 0
        self._misses = 0

        # Initialize async Redis connection pool (reused across requests)
        try:
            self._redis_pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                max_connections=max_connections,
                decode_responses=False,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            self._redis = redis.Redis(connection_pool=self._redis_pool)
            logger.info("embedding_cache.redis_pool_created", max_connections=max_connections)
        except Exception as e:
            logger.warning("embedding_cache.redis_pool_failed", error=str(e))
            self._redis = None
            self._redis_pool = None
            self._redis_available = False

    async def get(self, text_hash: str) -> Optional[np.ndarray]:
        """
        Get embedding from cache (with async Redis + local fallback).
        Uses connection pool for efficiency.
        """
        # Try local cache first
        if text_hash in self._local_cache:
            self._hits += 1
            logger.debug("embedding_cache.local_hit", hash=text_hash[:8])
            return self._local_cache[text_hash]

        if not self._redis_available or not self._redis:
            self._misses += 1
            return None

        try:
            key = f"{self.KEY_PREFIX}{text_hash}"
            data = await self._redis.get(key)  # Phase 6: Async call

            if data is None:
                self._misses += 1
                return None

            # Deserialize numpy array
            embedding = pickle.loads(data)
            # Store in local cache
            self._local_cache[text_hash] = embedding
            self._hits += 1

            logger.debug("embedding_cache.hit", hash=text_hash[:8])
            return embedding

        except Exception as e:
            logger.warning("embedding_cache.get_failed", error=str(e))
            self._redis_available = False
            self._misses += 1
            return None

    async def set(self, text_hash: str, embedding: np.ndarray, ttl: Optional[int] = None) -> bool:
        """
        Set embedding in cache (with async Redis connection pool).
        """
        # Always store in local cache
        self._local_cache[text_hash] = embedding

        if not self._redis_available or not self._redis:
            return True

        try:
            key = f"{self.KEY_PREFIX}{text_hash}"
            serialized = pickle.dumps(embedding)

            await self._redis.setex(key, ttl or self.TTL, serialized)  # Phase 6: Async call

            logger.debug("embedding_cache.set", hash=text_hash[:8], ttl=ttl or self.TTL)
            return True

        except Exception as e:
            logger.warning("embedding_cache.set_failed", error=str(e))
            self._redis_available = False
            return True  # Still succeeded locally

    async def clear(self) -> bool:
        """
        Clear all cached embeddings using async Redis.

        Returns:
            True if cleared successfully
        """
        if not self._redis_available or not self._redis:
            return False

        try:
            # Delete all embedding keys
            keys = await self._redis.keys(f"{self.KEY_PREFIX}*")  # Phase 6: Async call
            if keys:
                await self._redis.delete(*keys)

            logger.info("embedding_cache.cleared", count=len(keys))
            return True

        except Exception as e:
            logger.warning("embedding_cache.clear_error", error=str(e))
            return False
    
    def stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with hits, misses, hit rate
        """
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 3),
            "ttl_seconds": self.TTL,
        }
