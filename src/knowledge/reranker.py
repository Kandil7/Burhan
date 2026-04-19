"""
Cross-encoder reranker for improved retrieval quality.

DEPRECATED: This module has been moved to src.retrieval.ranking.reranker.
Please update imports to use the new location.

This file is kept for backward compatibility during migration.
"""

import warnings

# Re-export from new location for backward compatibility
from src.retrieval.ranking.reranker import CrossEncoderReranker as _CrossEncoderReranker
from src.retrieval.ranking.reranker import HybridReranker as _HybridReranker
from src.retrieval.ranking.reranker import RerankResult as _RerankResult
from src.retrieval.ranking.reranker import SimpleReranker as _SimpleReranker

# Emit deprecation warning when module is imported
warnings.warn(
    "src.knowledge.reranker is deprecated. Use src.retrieval.ranking.reranker instead.",
    DeprecationWarning,
    stacklevel=2,
)

# For backward compatibility
CrossEncoderReranker = _CrossEncoderReranker
HybridReranker = _HybridReranker
RerankResult = _RerankResult
SimpleReranker = _SimpleReranker

__all__ = ["CrossEncoderReranker", "HybridReranker", "RerankResult", "SimpleReranker"]
