"""
Embedding Cache for Athar Islamic QA system.

Redis-based caching for embedding vectors with connection pooling.
- TTL: 7 days (configurable)
- Reduces redundant embedding generation
- Significant speedup for repeated queries
- Async Redis client to avoid blocking event loop
- Local dict fallback for resilience

Phase 9 Enhancement:
- Added query cache for LLM responses
- Enhanced stats tracking
- TTL from settings

Phase 6 Refactoring:
- Converted from sync redis to redis.asyncio to prevent event loop blocking
- Proper async/await throughout
"""

import hashlib
import pickle
from typing import Any

import numpy as np
import redis.asyncio as redis

from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()


# ==========================================
# Embedding Cache
# ==========================================


class EmbeddingCache:
    """
    Async Redis-based cache for embedding vectors with connection pooling.

    Phase 6 Refactoring: All methods are now async to use redis.asyncio
    Phase 9 Enhancement: TTL from settings, enhanced stats

    Key format: "embedding:{sha256_hash}"
    Value: Serialized numpy array
    TTL: 7 days (604800 seconds) - configurable via settings

    Usage:
        cache = EmbeddingCache()
        await cache.set("hash123", embedding_array)
        embedding = await cache.get("hash123")
    """

    KEY_PREFIX = "embedding:"

    def __init__(
        self,
        max_connections: int = 10,
        ttl: int | None = None,
    ):
        """Initialize cache with async Redis connection pool and local dict fallback."""
        self.ttl = ttl or settings.embedding_cache_ttl
        self._redis = None
        self._redis_pool = None
        self._local_cache: dict[str, np.ndarray] = {}  # Fallback when Redis unavailable
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
            logger.info(
                "embedding_cache.redis_pool_created",
                max_connections=max_connections,
                ttl=self.ttl,
            )
        except Exception as e:
            logger.warning("embedding_cache.redis_pool_failed", error=str(e))
            self._redis = None
            self._redis_pool = None
            self._redis_available = False

    async def get(self, text_hash: str) -> np.ndarray | None:
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

    async def set(
        self,
        text_hash: str,
        embedding: np.ndarray,
        ttl: int | None = None,
    ) -> bool:
        """
        Set embedding in cache (with async Redis connection pool).
        """
        # Always store in local cache
        self._local_cache[text_hash] = embedding

        # Limit local cache size
        if len(self._local_cache) > 1000:
            # Remove oldest entries
            keys_to_remove = list(self._local_cache.keys())[:100]
            for key in keys_to_remove:
                del self._local_cache[key]

        if not self._redis_available or not self._redis:
            return True

        try:
            key = f"{self.KEY_PREFIX}{text_hash}"
            serialized = pickle.dumps(embedding)

            await self._redis.setex(key, ttl or self.ttl, serialized)

            logger.debug("embedding_cache.set", hash=text_hash[:8], ttl=ttl or self.ttl)
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
            keys = await self._redis.keys(f"{self.KEY_PREFIX}*")
            if keys:
                await self._redis.delete(*keys)

            # Clear local cache
            self._local_cache.clear()

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
            "ttl_seconds": self.ttl,
            "local_cache_size": len(self._local_cache),
        }


# ==========================================
# Query Cache (for LLM responses)
# ==========================================


class QueryCache:
    """
    Redis-backed query cache for LLM responses.

    Phase 9: Added for caching LLM responses to reduce costs and improve latency.

    Key format: "query:{sha256_hash}"
    Value: JSON serialized response

    Usage:
        cache = QueryCache()
        await cache.initialize()

        result = await cache.get("query_hash", params)
        if result is None:
            result = await generate_response(...)
            await cache.set("query_hash", result)
    """

    KEY_PREFIX = "query:"

    def __init__(
        self,
        max_connections: int = 10,
        ttl: int | None = None,
    ):
        """Initialize cache with async Redis connection pool."""
        self.ttl = ttl or settings.llm_cache_ttl
        self._redis = None
        self._redis_pool = None
        self._initialized = False
        self._hits = 0
        self._misses = 0
        self._local_cache: dict[str, dict] = {}  # In-memory fallback

        # Initialize async Redis connection pool
        try:
            self._redis_pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                max_connections=max_connections,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            self._redis = redis.Redis(connection_pool=self._redis_pool)
            self._initialized = True
            logger.info(
                "query_cache.redis_pool_created",
                max_connections=max_connections,
                ttl=self.ttl,
            )
        except Exception as e:
            logger.warning("query_cache.redis_pool_failed", error=str(e))
            self._redis = None
            self._redis_pool = None

    async def initialize(self) -> None:
        """Initialize the cache."""
        if self._initialized:
            return
        # Re-initialize if not done in __init__
        if not self._redis_pool:
            self.__init__()

    def _make_key(self, query: str, params: dict | None = None) -> str:
        """Generate cache key from query and parameters."""
        import json

        params_str = json.dumps(params or {}, sort_keys=True)
        key = hashlib.sha256(f"{query}:{params_str}".encode()).hexdigest()
        return f"{self.KEY_PREFIX}{key[:32]}"

    async def get(
        self,
        query: str,
        params: dict | None = None,
    ) -> dict | None:
        """
        Get cached query result.

        Args:
            query: Original query text
            params: Additional parameters for differentiation

        Returns:
            Cached result or None
        """
        # Try local cache first
        key = self._make_key(query, params)
        if key in self._local_cache:
            self._hits += 1
            logger.debug("query_cache.local_hit", key=key[:16])
            return self._local_cache[key]

        if not self._redis or not self._initialized:
            self._misses += 1
            return None

        try:
            cached = await self._redis.get(key)
            if cached:
                import json

                result = json.loads(cached)
                self._local_cache[key] = result
                self._hits += 1
                logger.debug("query_cache.hit", key=key[:16])
                return result

            self._misses += 1
            return None

        except Exception as e:
            logger.warning("query_cache.get_error", error=str(e))
            self._misses += 1
            return None

    async def set(
        self,
        query: str,
        result: dict,
        params: dict | None = None,
    ) -> bool:
        """
        Cache query result.

        Args:
            query: Original query text
            result: Result to cache
            params: Additional parameters
        """
        key = self._make_key(query, params)

        # Always store in local cache
        self._local_cache[key] = result

        # Limit local cache size
        if len(self._local_cache) > 500:
            keys_to_remove = list(self._local_cache.keys())[:50]
            for k in keys_to_remove:
                del self._local_cache[k]

        if not self._redis or not self._initialized:
            return True

        try:
            import json

            await self._redis.setex(key, self.ttl, json.dumps(result))
            logger.debug("query_cache.set", key=key[:16])
            return True

        except Exception as e:
            logger.warning("query_cache.set_error", error=str(e))
            return True

    async def invalidate(
        self,
        query: str,
        params: dict | None = None,
    ) -> bool:
        """Invalidate a cached query."""
        key = self._make_key(query, params)

        # Remove from local cache
        if key in self._local_cache:
            del self._local_cache[key]

        if not self._redis or not self._initialized:
            return False

        try:
            deleted = await self._redis.delete(key)
            logger.debug("query_cache.invalidated", key=key[:16], deleted=deleted)
            return bool(deleted)

        except Exception as e:
            logger.warning("query_cache.invalidate_error", error=str(e))
            return False

    async def clear(self) -> bool:
        """Clear all cached queries."""
        self._local_cache.clear()

        if not self._redis or not self._initialized:
            return False

        try:
            keys = await self._redis.keys(f"{self.KEY_PREFIX}*")
            if keys:
                await self._redis.delete(*keys)

            logger.info("query_cache.cleared", count=len(keys))
            return True

        except Exception as e:
            logger.warning("query_cache.clear_error", error=str(e))
            return False

    def stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 3),
            "ttl_seconds": self.ttl,
            "local_cache_size": len(self._local_cache),
        }
