"""
Book Importance Weighter for Athar Islamic QA system.

DEPRECATED: This module has been moved to src.retrieval.ranking.book_weighter.
Please update imports to use the new location.

This file is kept for backward compatibility during migration.
"""

import warnings

# Re-export from new location for backward compatibility
from src.retrieval.ranking.book_weighter import BookImportanceWeighter as _BookImportanceWeighter

# Emit deprecation warning when module is imported
warnings.warn(
    "src.knowledge.book_weighter is deprecated. Use src.retrieval.ranking.book_weighter instead.",
    DeprecationWarning,
    stacklevel=2,
)

# For backward compatibility
BookImportanceWeighter = _BookImportanceWeighter

__all__ = ["BookImportanceWeighter"]
