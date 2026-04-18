"""
Legacy Tafsir (Quran Interpretation) RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/tafsir.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.tafsir_agent is DEPRECATED. Use src.agents.collection.tafsir (config-backed) instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.legacy.tafsir_agent import TafsirAgent

__all__ = ["TafsirAgent"]
