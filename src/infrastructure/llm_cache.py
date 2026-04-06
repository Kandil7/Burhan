"""
LLM response caching for Athar Islamic QA System.

Provides Redis-based caching for LLM responses to reduce costs and improve latency.
"""

import json
import hashlib
from typing import Optional
import redis.asyncio as redis

from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger()


class LLMResponseCache:
    """
    Redis-based cache for LLM responses.

    Uses SHA256 hash of prompt as cache key.
    TTL configurable (default 1 hour).
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self._redis: Optional[redis.Redis] = None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=False,  # Binary for faster processing
            )
        return self._redis

    def _generate_cache_key(self, prompt: str, model: str, temperature: float) -> str:
        """Generate cache key from prompt and parameters."""
        # Create deterministic hash
        content = f"{model}:{temperature}:{prompt}"
        hash_obj = hashlib.sha256(content.encode("utf-8"))
        return f"llm:response:{hash_obj.hexdigest()[:32]}"

    async def get(self, prompt: str, model: str, temperature: float = 0.1) -> Optional[str]:
        """
        Get cached LLM response.

        Args:
            prompt: The prompt that was sent to LLM
            model: The model used
            temperature: Temperature parameter

        Returns:
            Cached response or None if not found
        """
        try:
            redis_client = await self._get_redis()
            cache_key = self._generate_cache_key(prompt, model, temperature)

            cached = await redis_client.get(cache_key)

            if cached:
                logger.info("cache.hit", key=cache_key[:16])
                return cached.decode("utf-8")

            logger.info("cache.miss", key=cache_key[:16])
            return None

        except Exception as e:
            logger.error("cache.get_error", error=str(e))
            return None

    async def set(self, prompt: str, response: str, model: str, temperature: float = 0.1) -> bool:
        """
        Cache LLM response.

        Args:
            prompt: The prompt sent to LLM
            response: The LLM response to cache
            model: The model used
            temperature: Temperature parameter

        Returns:
            True if cached successfully
        """
        try:
            redis_client = await self._get_redis()
            cache_key = self._generate_cache_key(prompt, model, temperature)

            await redis_client.setex(cache_key, self.ttl, response.encode("utf-8"))

            logger.info("cache.set", key=cache_key[:16], ttl=self.ttl)
            return True

        except Exception as e:
            logger.error("cache.set_error", error=str(e))
            return False

    async def delete(self, prompt: str, model: str, temperature: float = 0.1) -> bool:
        """Delete cached response."""
        try:
            redis_client = await self._get_redis()
            cache_key = self._generate_cache_key(prompt, model, temperature)
            await redis_client.delete(cache_key)
            return True
        except Exception as e:
            logger.error("cache.delete_error", error=str(e))
            return False

    async def clear_all(self) -> bool:
        """Clear all LLM response cache."""
        try:
            redis_client = await self._get_redis()
            keys = await redis_client.keys("llm:response:*")
            if keys:
                await redis_client.delete(*keys)
            logger.info("cache.cleared", count=len(keys))
            return True
        except Exception as e:
            logger.error("cache.clear_error", error=str(e))
            return False

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Global cache instance
_llm_cache: Optional[LLMResponseCache] = None


async def get_llm_cache() -> LLMResponseCache:
    """Get global LLM cache instance."""
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = LLMResponseCache()
    return _llm_cache


# ==========================================
# Cached LLM generation helper
# ==========================================


async def generate_with_cache(
    llm_client,
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.1,
    max_tokens: int = 2048,
    use_cache: bool = True,
) -> str:
    """
    Generate text using LLM with caching.

    Args:
        llm_client: OpenAI-compatible client
        prompt: User prompt
        system_prompt: Optional system prompt
        model: Model name
        temperature: Temperature
        max_tokens: Max tokens
        use_cache: Whether to use caching

    Returns:
        Generated text
    """
    # Check cache first
    if use_cache:
        cache = await get_llm_cache()
        cached_response = await cache.get(prompt, model, temperature)
        if cached_response:
            return cached_response

    # Generate new response
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = await llm_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    result = response.choices[0].message.content

    # Cache the response
    if use_cache and result:
        cache = await get_llm_cache()
        await cache.set(prompt, result, model, temperature)

    return result
