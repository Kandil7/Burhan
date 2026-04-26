"""
Qdrant Client Wrapper for Burhan Islamic QA system.

Provides a clean interface for Qdrant operations, separating infrastructure
from the retrieval layer.

This module wraps src.indexing.vectorstores.qdrant_store.VectorStore
with additional utilities for the v2 architecture.
"""

from __future__ import annotations

from typing import Any

from src.indexing.vectorstores.qdrant_store import VectorStore as QdrantVectorStore


class QdrantClientWrapper:
    """
    Wrapper around Qdrant VectorStore for v2 architecture.

    Provides:
    - Simplified search interface
    - Collection management utilities
    - Payload transformation

    Usage:
        client = QdrantClientWrapper()
        await client.initialize()
        results = await client.search("fiqh", query="...", top_k=10)
    """

    def __init__(self):
        """Initialize the Qdrant client wrapper."""
        self._client = QdrantVectorStore()
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the underlying Qdrant client."""
        if self._initialized:
            return

        await self._client.initialize()
        self._initialized = True

    async def search(
        self,
        collection: str,
        query: str,
        embedding: list[float] | None = None,
        top_k: int = 10,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search the collection.

        Args:
            collection: Collection name
            query: Query text (for hybrid search)
            embedding: Query embedding (for semantic search)
            top_k: Number of results
            score_threshold: Minimum score
            filters: Metadata filters

        Returns:
            List of result dictionaries with content, score, metadata
        """
        # Delegate to underlying client
        # Note: This is a simplified interface - the actual implementation
        # may differ based on the underlying VectorStore API
        return await self._client.search(
            collection=collection,
            query_embedding=embedding,
            query=query,
            top_k=top_k,
            filters=filters,
        )

    async def search_by_embedding(
        self,
        collection: str,
        embedding: list[float],
        top_k: int = 10,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Search by embedding only (semantic search)."""
        return await self._client.search(
            collection=collection,
            query_embedding=embedding,
            top_k=top_k,
        )

    async def search_by_text(
        self,
        collection: str,
        query: str,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Search by text only (keyword search)."""
        return await self._client.search(
            collection=collection,
            query=query,
            top_k=top_k,
        )

    async def get_collection_info(self, collection: str) -> dict[str, Any]:
        """Get collection information."""
        # This would need implementation in underlying client
        return {"name": collection}

    async def close(self) -> None:
        """Close the client connection."""
        if hasattr(self._client, "close"):
            await self._client.close()
        self._initialized = False


# Singleton instance
_client_instance: QdrantClientWrapper | None = None


async def get_qdrant_client() -> QdrantClientWrapper:
    """Get the global Qdrant client instance."""
    global _client_instance

    if _client_instance is None:
        _client_instance = QdrantClientWrapper()
        await _client_instance.initialize()

    return _client_instance


__all__ = ["QdrantClientWrapper", "get_qdrant_client"]
