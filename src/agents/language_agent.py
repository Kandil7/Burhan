"""
Legacy Arabic Language RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/language.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.language_agent is DEPRECATED. Use src.agents.collection.language (config-backed) instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.legacy.language_agent import LanguageAgent

__all__ = ["LanguageAgent"]
