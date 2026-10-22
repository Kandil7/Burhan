"""Indexing layer for Burhan Islamic QA system.

This module contains the indexing components the live tree uses:
- embeddings: embedding model and cache
- vectorstores: the Qdrant store

The designed extras (metadata catalogs, lexical indexes, the FAISS/Chroma
factory, and the analysis pipelines) were deleted in hardening Phase 7;
see docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md.
"""

from src.indexing.embeddings.embedding_cache import EmbeddingCache
from src.indexing.embeddings.embedding_model import EmbeddingModel
from src.indexing.vectorstores.qdrant_store import VectorStore

__all__ = [
    "EmbeddingModel",
    "EmbeddingCache",
    "VectorStore",
]
