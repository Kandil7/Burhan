"""
Legacy Hadith Collection Agent - DEPRECATED.

Migrated to: src/agents/collection/hadith.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.hadith_collection_agent is DEPRECATED. Use src.agents.collection.hadith instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.collection.hadith import HadithCollectionAgent

__all__ = ["HadithCollectionAgent"]
