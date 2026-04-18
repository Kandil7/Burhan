"""
Legacy Hadith RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/hadith.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.hadith_agent is DEPRECATED. Use src.agents.collection.hadith (config-backed) instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.legacy.hadith_agent import HadithAgent

__all__ = ["HadithAgent"]
