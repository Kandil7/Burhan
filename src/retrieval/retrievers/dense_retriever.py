# Dense Retriever Module
"""Dense (embedding-based) retrieval."""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod


class BaseDenseRetriever(ABC):
    """Abstract base class for dense retrievers."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve documents using dense embeddings."""
        raise NotImplementedError


class DenseRetriever(BaseDenseRetriever):
    """Dense retriever implementation using embeddings."""

    def __init__(
        self,
        collection: str,
        embedding_model: Any,
        vector_store: Any,
    ):
        self.collection = collection
        self.embedding_model = embedding_model
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve documents using dense embeddings."""
        # 1) Embed query
        query_embedding = await self.embedding_model.encode_query(query)

        # 2) Search in the configured collection
        results = await self.vector_store.search(
            collection=self.collection,
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )

        # 3) Ensure collection metadata exists
        for r in results:
            meta = r.get("metadata", {}) or {}
            meta.setdefault("collection", self.collection)
            r["metadata"] = meta

        return results


# Factory function
def create_dense_retriever(
    collection: str,
    embedding_model: Any,
    vector_store: Any,
) -> DenseRetriever:
    """Create a dense retriever for a specific collection."""
    return DenseRetriever(
        collection=collection,
        embedding_model=embedding_model,
        vector_store=vector_store,
    )