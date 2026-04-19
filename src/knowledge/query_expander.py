"""
Query expansion with Islamic synonyms for better retrieval.

DEPRECATED: This module has been moved to src.retrieval.expanders.query_expander.
Please update imports to use the new location.

This file is kept for backward compatibility during migration.
"""

import warnings

# Re-export from new location for backward compatibility
from src.retrieval.expanders.query_expander import QueryExpander as _QueryExpander
from src.retrieval.expanders.query_expander import RetrievalQueryExpander as _RetrievalQueryExpander

# Emit deprecation warning when module is imported
warnings.warn(
    "src.knowledge.query_expander is deprecated. Use src.retrieval.expanders.query_expander instead.",
    DeprecationWarning,
    stacklevel=2,
)

# For backward compatibility
QueryExpander = _QueryExpander
RetrievalQueryExpander = _RetrievalQueryExpander

__all__ = ["QueryExpander", "RetrievalQueryExpander"]
