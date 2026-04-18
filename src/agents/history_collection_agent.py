"""
Legacy History Collection Agent - DEPRECATED.

Migrated to: src/agents/collection/history.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.history_collection_agent is DEPRECATED. Use src.agents.collection.history instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.collection.history import HistoryCollectionAgent

__all__ = ["HistoryCollectionAgent"]
