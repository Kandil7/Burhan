"""
Legacy Islamic History RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/history.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.history_agent is DEPRECATED. Use src.agents.collection.history (config-backed) instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.legacy.history_agent import HistoryAgent

__all__ = ["HistoryAgent"]
