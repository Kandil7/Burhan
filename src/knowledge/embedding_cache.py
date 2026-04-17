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

[DEPRECATED] Moved to src.indexing.embeddings.embedding_cache
This module is kept for backward compatibility. Please update imports.
"""

# Backward compatibility shim - imports from new location
from src.indexing.embeddings.embedding_cache import EmbeddingCache, QueryCache

__all__ = ["EmbeddingCache", "QueryCache"]
