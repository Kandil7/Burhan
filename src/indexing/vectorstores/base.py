"""
Base VectorStore Abstract Class.

Defines the interface that all vector store implementations must follow.
This allows for swappable backends (Qdrant, Chroma, FAISS, etc.).
"""

from __future__ import annotations

import abc
from typing import Any

import numpy as np

from src.config.logging_config import get_logger

logger = get_logger()


class VectorStoreBaseError(Exception):
    """Base exception for vector store errors."""

    pass


class VectorStoreBase(abc.ABC):
    """
    Abstract base class for vector store implementations.

    All vector stores must implement these methods:
    - initialize()
    - upsert()
    - search()
    - delete_collection()
    - list_collections()
    - get_collection_stats()

    Example:
        class MyVectorStore(VectorStoreBase):
            async def initialize(self) -> None:
                ...

            async def upsert(...) -> int:
                ...
    """

    # Default collections for Islamic texts
    DEFAULT_COLLECTIONS: dict[str, dict[str, Any]] = {
        "fiqh_passages": {"dimension": 1024, "description": "Fiqh books and fatwas"},
        "hadith_passages": {"dimension": 1024, "description": "Hadith collections"},
        "quran_tafsir": {"dimension": 1024, "description": "Tafsir passages"},
        "general_islamic": {"dimension": 1024, "description": "General Islamic knowledge"},
        "duas_adhkar": {"dimension": 1024, "description": "Duas and adhkar"},
        "aqeedah_passages": {"dimension": 1024, "description": "Aqeedah and creed"},
        "seerah_passages": {"dimension": 1024, "description": "Prophet biography"},
        "islamic_history_passages": {"dimension": 1024, "description": "Islamic history"},
        "arabic_language_passages": {"dimension": 1024, "description": "Arabic language"},
        "spirituality_passages": {"dimension": 1024, "description": "Spirituality and ethics"},
        "usul_fiqh": {"dimension": 1024, "description": "Principles of jurisprudence"},
    }

    @abc.abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the vector store and create default collections.

        Raises:
            VectorStoreBaseError: If initialization fails
        """
        pass

    @abc.abstractmethod
    async def upsert(
        self,
        collection: str,
        documents: list[dict],
        embeddings: np.ndarray,
    ) -> int:
        """
        Upsert documents with embeddings to collection.

        Args:
            collection: Collection name
            documents: List of document dicts with 'content' and optional 'metadata'
            embeddings: Numpy array of embeddings (N x dimension)

        Returns:
            Number of documents upserted

        Raises:
            VectorStoreBaseError: If upsert fails
        """
        pass

    @abc.abstractmethod
    async def search(
        self,
        collection: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        Search for similar documents.

        Args:
            collection: Collection name
            query_embedding: Query embedding vector
            top_k: Number of results
            filters: Optional metadata filters

        Returns:
            List of result dicts with 'id', 'score', 'content', 'metadata'

        Raises:
            VectorStoreBaseError: If search fails
        """
        pass

    @abc.abstractmethod
    async def ensure_collection(self, name: str, dimension: int = 1024) -> None:
        """
        Ensure a collection exists, create if not.

        Args:
            name: Collection name
            dimension: Vector dimension

        Raises:
            VectorStoreBaseError: If operation fails
        """
        pass

    @abc.abstractmethod
    def delete_collection(self, collection: str) -> bool:
        """
        Delete a collection.

        Args:
            collection: Collection name

        Returns:
            True if deleted successfully, False otherwise
        """
        pass

    @abc.abstractmethod
    def list_collections(self) -> list[str]:
        """
        List all collection names.

        Returns:
            List of collection names
        """
        pass

    @abc.abstractmethod
    def get_collection_stats(self, collection: str) -> dict:
        """
        Get collection statistics.

        Args:
            collection: Collection name

        Returns:
            Dict with 'collection', 'vectors_count', 'status'
        """
        pass

    # ── Optional methods ─────────────────────────────────────────────────────

    async def search_with_score_threshold(
        self,
        collection: str,
        query_embedding: np.ndarray,
        top_k: int = 10,
        score_threshold: float = 0.7,
    ) -> list[dict]:
        """
        Search with minimum score threshold.
        Default implementation filters results after search.

        Args:
            collection: Collection name
            query_embedding: Query embedding
            top_k: Max results
            score_threshold: Minimum similarity score

        Returns:
            Filtered results above threshold
        """
        results = await self.search(collection, query_embedding, top_k=top_k * 2)
        filtered = [r for r in results if r["score"] >= score_threshold]
        return filtered[:top_k]

    async def close(self) -> None:
        """
        Close any open connections.
        Default implementation does nothing.
        Override if cleanup is needed.
        """
        pass

    def get_stats(self) -> dict:
        """
        Get overall vector store statistics.
        Default implementation returns basic info.
        Override for detailed stats.
        """
        return {
            "type": self.__class__.__name__,
            "collections": self.list_collections(),
        }
