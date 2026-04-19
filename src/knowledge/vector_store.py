"""
Qdrant Vector Store Integration for Athar Islamic QA system.

Provides:
- Collection management (fiqh, hadith, tafsir, general, duas)
- Similarity search with metadata filtering
- Hybrid search (semantic + keyword)
- Batch upsert for efficient indexing
- HNSW index configuration

Phase 4: Foundation for all RAG retrieval pipelines.

[DEPRECATED] Moved to src.indexing.vectorstores.qdrant_store
This module is kept for backward compatibility. Please update imports.
"""

# Backward compatibility shim - imports from new location
from src.indexing.vectorstores.qdrant_store import VectorStore, VectorStoreError

__all__ = ["VectorStore", "VectorStoreError"]
