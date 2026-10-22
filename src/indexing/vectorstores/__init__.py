"""Vectorstores module for Burhan Islamic QA system.

The designed multi-store factory (FAISS and Chroma branches) was deleted in
hardening Phase 7; the Qdrant store is what the live tree uses.
"""

from src.indexing.vectorstores.qdrant_store import VectorStore, VectorStoreError

__all__ = [
    "VectorStore",
    "VectorStoreError",
]
