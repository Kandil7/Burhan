"""
BM25 Retrieval for Athar Islamic QA System.

DEPRECATED: This module has been moved to src.retrieval.retrievers.bm25_retriever.
Please update imports to use the new location.

This file is kept for backward compatibility during migration.
"""

import warnings

# Re-export from new location for backward compatibility
from src.retrieval.retrievers.bm25_retriever import BM25 as _BM25
from src.retrieval.retrievers.bm25_retriever import BM25Retriever as _BM25Retriever

# Emit deprecation warning when module is imported
warnings.warn(
    "src.knowledge.bm25_retriever is deprecated. Use src.retrieval.retrievers.bm25_retriever instead.",
    DeprecationWarning,
    stacklevel=2,
)

# For backward compatibility
BM25 = _BM25
BM25Retriever = _BM25Retriever

__all__ = ["BM25", "BM25Retriever"]
