"""Vectorstores module for Athar Islamic QA system."""

from src.indexing.vectorstores.base import VectorStoreBase, VectorStoreBaseError
from src.indexing.vectorstores.qdrant_store import VectorStore, VectorStoreError
from src.indexing.vectorstores.chroma_store import ChromaVectorStore, ChromaStoreError
from src.indexing.vectorstores.factory import (
    VectorStoreFactory,
    get_vector_store,
    initialize_vector_store,
)

__all__ = [
    "VectorStoreBase",
    "VectorStoreBaseError",
    "VectorStore",
    "VectorStoreError",
    "ChromaVectorStore",
    "ChromaStoreError",
    "VectorStoreFactory",
    "get_vector_store",
    "initialize_vector_store",
]
