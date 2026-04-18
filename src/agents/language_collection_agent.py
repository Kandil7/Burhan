"""
Legacy Language Collection Agent - DEPRECATED.

Migrated to: src/agents/collection/language.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.language_collection_agent is DEPRECATED. Use src.agents.collection.language instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.collection.language import LanguageCollectionAgent

__all__ = ["LanguageCollectionAgent"]
