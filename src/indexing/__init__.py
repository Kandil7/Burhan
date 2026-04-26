"""Indexing layer for Burhan Islamic QA system.

This module contains indexing-related components:
- embeddings: Embedding model and cache
- vectorstores: Vector store implementations
- metadata: Title and metadata loaders
- lexical: BM25 and other lexical search
- pipelines: Indexing pipelines
"""

from src.indexing.embeddings.embedding_model import EmbeddingModel
from src.indexing.embeddings.embedding_cache import EmbeddingCache
from src.indexing.vectorstores.base import VectorStoreBase
from src.indexing.vectorstores.qdrant_store import VectorStore
from src.indexing.vectorstores.factory import get_vector_store
from src.indexing.metadata.title_loader import TitleLoader

__all__ = [
    "EmbeddingModel",
    "EmbeddingCache",
    "VectorStoreBase",
    "VectorStore",
    "get_vector_store",
    "TitleLoader",
]
