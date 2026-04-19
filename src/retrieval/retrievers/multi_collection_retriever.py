# Multi-Collection Retriever Module
"""Retrieval across multiple collections."""

from typing import List, Optional, Dict, Any


class MultiCollectionRetriever:
    """Retriever that queries multiple collections."""

    def __init__(self, retrievers: Optional[Dict[str, Any]] = None):
        self.retrievers = retrievers or {}

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
        results = {}

        for collection_id in collections:
            if collection_id in self.retrievers:
                retriever = self.retrievers[collection_id]
                results[collection_id] = await retriever.retrieve(query, top_k)
            else:
                results[collection_id] = []

        return results

    def register_retriever(self, collection_id: str, retriever: Any) -> None:
        """Register a retriever for a collection."""
        self.retrievers[collection_id] = retriever

    def get_retriever(self, collection_id: str) -> Optional[Any]:
        """Get the retriever for a specific collection."""
        return self.retrievers.get(collection_id)
