"""
Legacy Tazkiyah (Spiritual Development) RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/tazkiyah.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.tazkiyah_agent is DEPRECATED. Use src.agents.collection.tazkiyah (config-backed) instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.legacy.tazkiyah_agent import TazkiyahAgent

__all__ = ["TazkiyahAgent"]
