"""
Hierarchical Retriever for Athar Islamic QA system.

DEPRECATED: This module has been moved to src.retrieval.retrievers.hierarchical_retriever.
Please update imports to use the new location.

This file is kept for backward compatibility during migration.
"""

import warnings

# Re-export from new location for backward compatibility
from src.retrieval.retrievers.hierarchical_retriever import HierarchicalRetriever as _HierarchicalRetriever

# Emit deprecation warning when module is imported
warnings.warn(
    "src.knowledge.hierarchical_retriever is deprecated. Use src.retrieval.retrievers.hierarchical_retriever instead.",
    DeprecationWarning,
    stacklevel=2,
)

# For backward compatibility
HierarchicalRetriever = _HierarchicalRetriever

__all__ = ["HierarchicalRetriever"]
