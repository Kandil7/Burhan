# Sparse Retriever Module
"""Sparse (keyword-based) retrieval."""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod


class BaseSparseRetriever(ABC):
    """Abstract base class for sparse retrievers."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve documents using sparse (keyword) methods."""
        pass


class SparseRetriever(BaseSparseRetriever):
    """Sparse retriever implementation using BM25 or similar."""

    def __init__(self, index_path: Optional[str] = None):
        self.index_path = index_path

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve documents using sparse methods."""
        # Placeholder - implement actual sparse retrieval
        raise NotImplementedError("Sparse retriever not yet implemented")


# Factory function
def create_sparse_retriever(index_path: str) -> SparseRetriever:
    """Create a sparse retriever with the given index path."""
    return SparseRetriever(index_path=index_path)
