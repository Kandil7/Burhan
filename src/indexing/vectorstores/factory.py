"""
Vector Store Factory.

Creates vector store instances based on configuration.
Supports Qdrant (default) and other backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from src.config.logging_config import get_logger
from src.config.settings import settings

if TYPE_CHECKING:
    from src.indexing.vectorstores.base import VectorStoreBase

logger = get_logger()


class VectorStoreFactory:
    """
    Factory for creating vector store instances.

    Supports:
    - Qdrant (default, production-ready)
    - Chroma (placeholder, not yet implemented)
    - FAISS (placeholder, not yet implemented)

    Usage:
        # Get default Qdrant store
        store = VectorStoreFactory.get_vector_store()

        # Get specific store type
        store = VectorStoreFactory.get_vector_store(store_type="qdrant")
    """

    _instance: Any = None

    @classmethod
    def get_vector_store(
        cls,
        store_type: str | None = None,
    ) -> VectorStoreBase:
        """
        Get a vector store instance.

        Args:
            store_type: Type of vector store ("qdrant", "chroma", "faiss")
                       If None, uses settings.vector_store_type or default

        Returns:
            Vector store instance

        Raises:
            ValueError: If store type is unknown or not implemented
        """
        store_type = str(store_type or getattr(settings, "vector_store_type", "qdrant")).lower()

        # Return cached instance if already created
        if cls._instance is not None:
            return cast(VectorStoreBase, cls._instance)

        if store_type == "qdrant":
            from src.indexing.vectorstores.qdrant_store import VectorStore

            cls._instance = VectorStore()
            logger.info("vectorstore.factory.created", store_type="qdrant")
            return cast(VectorStoreBase, cls._instance)

        elif store_type == "chroma":
            # Dead scaffolding: chroma_store.py does not exist yet (Known Gaps).
            from src.indexing.vectorstores import chroma_store  # type: ignore

            cls._instance = chroma_store.ChromaVectorStore()
            logger.info("vectorstore.factory.created", store_type="chroma")
            return cast(VectorStoreBase, cls._instance)

        elif store_type == "faiss":
            # FAISS placeholder - would import FAISSVectorStore when implemented
            raise ValueError("FAISS vector store is not yet implemented. Use 'qdrant' or 'chroma' instead.")

        else:
            raise ValueError(f"Unknown vector store type: {store_type}. Supported: qdrant, chroma, faiss")

    @classmethod
    async def initialize_vector_store(cls) -> VectorStoreBase:
        """
        Get and initialize the vector store.

        Returns:
            Initialized vector store instance
        """
        store = cls.get_vector_store()
        await store.initialize()
        return store

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the cached instance.
        Useful for testing or when changing configuration.
        """
        cls._instance = None
        logger.info("vectorstore.factory.reset")

    @classmethod
    def get_available_stores(cls) -> list[str]:
        """
        Get list of available (implemented) vector stores.

        Returns:
            List of store type names
        """
        return ["qdrant", "chroma"]


# Convenience function for quick access
def get_vector_store() -> VectorStoreBase:
    """Get the default vector store instance."""
    return VectorStoreFactory.get_vector_store()


async def initialize_vector_store() -> VectorStoreBase:
    """Initialize and return the default vector store."""
    return await VectorStoreFactory.initialize_vector_store()
