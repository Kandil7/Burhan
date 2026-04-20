# Multi-Collection Retriever Module
"""Retrieval across multiple collections."""

from typing import List, Optional, Dict, Any
import asyncio


class MultiCollectionRetriever:
    """Retriever that queries multiple collections."""

    def __init__(self, retrievers: Optional[Dict[str, Any]] = None):
        self.retrievers: Dict[str, Any] = retrievers or {}

    async def retrieve(
        self,
        query: str,
        collections: List[str],
        top_k: int = 10,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve from multiple collections.

        Returns:
            Dict mapping collection_id to list of results
        """
        results: Dict[str, List[Dict[str, Any]]] = {}

        # Build tasks for collections that have retrievers
        tasks = []
        ordered_ids: List[str] = []

        for collection_id in collections:
            retriever = self.retrievers.get(collection_id)
            if retriever is not None:
                tasks.append(retriever.retrieve(query, top_k))
                ordered_ids.append(collection_id)
            else:
                # collection بدون retriever مسجّل → نتائج فارغة
                results[collection_id] = []

        if tasks:
            retrieved_lists = await asyncio.gather(*tasks, return_exceptions=True)
            for coll_id, res in zip(ordered_ids, retrieved_lists):
                if isinstance(res, Exception):
                    # TODO: log error هنا لو حابب
                    results[coll_id] = []
                else:
                    results[coll_id] = res

        return results

    def register_retriever(self, collection_id: str, retriever: Any) -> None:
        """Register a retriever for a collection."""
        self.retrievers[collection_id] = retriever

    def get_retriever(self, collection_id: str) -> Optional[Any]:
        """Get the retriever for a specific collection."""
        return self.retrievers.get(collection_id)