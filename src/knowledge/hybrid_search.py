"""
Hybrid Search for Athar Islamic QA system.

DEPRECATED: This module has been moved to src.retrieval.retrievers.hybrid_retriever.
Please update imports to use the new location.

This file is kept for backward compatibility during migration.
"""

import warnings

# Re-export from new location for backward compatibility
from src.retrieval.retrievers.hybrid_retriever import HybridSearcher as _HybridSearcher

# Emit deprecation warning when module is imported
warnings.warn(
    "src.knowledge.hybrid_search is deprecated. Use src.retrieval.retrievers.hybrid_retriever instead.",
    DeprecationWarning,
    stacklevel=2,
)

# For backward compatibility, provide the HybridSearcher from new location
HybridSearcher = _HybridSearcher

# Also keep the original module-level code for imports that might reference it
__all__ = ["HybridSearcher"]
