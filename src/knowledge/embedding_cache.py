"""
Embedding Cache for Athar Islamic QA system.

Redis-based caching for embedding vectors.
- TTL: 7 days
- Reduces redundant embedding generation
- Significant speedup for repeated queries

Phase 4: Optimization layer for RAG pipelines.
"""
import json
import pickle
from typing import Optional

import numpy as np

from src.config.settings import settings
from src.infrastructure.redis import get_redis
from src.config.logging_config import get_logger

logger = get_logger()


class EmbeddingCache:
    """
    Redis-based cache for embedding vectors.
    
    Key format: "embedding:{sha256_hash}"
    Value: Serialized numpy array
    TTL: 7 days (604800 seconds)
    
    Usage:
        cache = EmbeddingCache()
        cache.set("hash123", embedding_array)
        embedding = cache.get("hash123")
    """
    
    TTL = 604800  # 7 days in seconds
    KEY_PREFIX = "embedding:"
    
    def __init__(self):
        """Initialize cache."""
        self._redis = None
        self._hits = 0
        self._misses = 0
    
    async def _get_redis(self):
        """Get Redis connection."""
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis
    
    def get(self, text_hash: str) -> Optional[np.ndarray]:
        """
        Get embedding from cache.
        
        Args:
            text_hash: SHA-256 hash of text
            
        Returns:
            Embedding array or None if not cached
        """
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Running in async context, create sync connection
                import redis
                r = redis.from_url(settings.redis_url, decode_responses=False)
            else:
                # Running in sync context
                import redis
                r = redis.from_url(settings.redis_url, decode_responses=False)
            
            key = f"{self.KEY_PREFIX}{text_hash}"
            data = r.get(key)
            
            if data is None:
                self._misses += 1
                return None
            
            # Deserialize numpy array
            embedding = pickle.loads(data)
            self._hits += 1
            
            logger.debug("embedding_cache.hit", hash=text_hash[:8])
            return embedding
            
        except Exception as e:
            logger.warning("embedding_cache.get_error", error=str(e))
            self._misses += 1
            return None
    
    def set(self, text_hash: str, embedding: np.ndarray, ttl: Optional[int] = None) -> bool:
        """
        Set embedding in cache.
        
        Args:
            text_hash: SHA-256 hash of text
            embedding: Embedding array to cache
            ttl: Time to live in seconds (default: 7 days)
            
        Returns:
            True if cached successfully
        """
        try:
            import redis
            r = redis.from_url(settings.redis_url, decode_responses=False)
            
            key = f"{self.KEY_PREFIX}{text_hash}"
            serialized = pickle.dumps(embedding)
            
            r.setex(key, ttl or self.TTL, serialized)
            
            logger.debug("embedding_cache.set", hash=text_hash[:8], ttl=ttl or self.TTL)
            return True
            
        except Exception as e:
            logger.warning("embedding_cache.set_error", error=str(e))
            return False
    
    def clear(self) -> bool:
        """
        Clear all cached embeddings.
        
        Returns:
            True if cleared successfully
        """
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            
            # Delete all embedding keys
            keys = r.keys(f"{self.KEY_PREFIX}*")
            if keys:
                r.delete(*keys)
            
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
