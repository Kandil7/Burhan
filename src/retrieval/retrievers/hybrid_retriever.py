"""Hybrid retrieval adapters for one or more collections.

The previous version of this module imported classes that no longer exist,
used undefined names, and built a global retriever at import time. It is
replaced by an explicit adapter over the current HybridSearcher API.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from src.retrieval.retrievers.hybrid_searcher import HybridSearcher
from src.retrieval.retrievers.multi_collection_retriever import MultiCollectionRetriever

__all__ = ["CollectionHybridRetriever", "build_multi_collection_retriever"]


class CollectionHybridRetriever:
    """Expose :class:`HybridSearcher` as a single-collection retriever.

    Usage:
        retriever = CollectionHybridRetriever(
            collection="fiqh_passages",
            vector_store=vector_store,
            embedding_model=embedding_model,
        )
        results = await retriever.retrieve("زكاة المال", top_k=10)
    """

    def __init__(
        self,
        collection: str,
        vector_store: Any,
        embedding_model: Any,
        k: int = 60,
    ) -> None:
        self.collection = collection
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.searcher = HybridSearcher(vector_store, k=k)

    async def retrieve(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Embed the query and run hybrid search on this collection."""
        query_embedding = await self.embedding_model.encode_query(query)
        return await self.searcher.search(
            query=query,
            query_embedding=query_embedding,
            collection=self.collection,
            top_k=top_k,
        )


def build_multi_collection_retriever(
    collections: Iterable[str],
    vector_store: Any,
    embedding_model: Any,
    k: int = 60,
) -> MultiCollectionRetriever:
    """Build a :class:`MultiCollectionRetriever` with one adapter per collection."""
    multi = MultiCollectionRetriever()
    for collection in collections:
        multi.register_retriever(
            collection,
            CollectionHybridRetriever(
                collection=collection,
                vector_store=vector_store,
                embedding_model=embedding_model,
                k=k,
            ),
        )
    return multi
