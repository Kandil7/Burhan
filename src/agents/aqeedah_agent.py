"""
Legacy Aqeedah (Islamic Creed/Theology) RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/aqeedah.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.aqeedah_agent is DEPRECATED. Use src.agents.collection.aqeedah (config-backed) instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.legacy.aqeedah_agent import AqeedahAgent

__all__ = ["AqeedahAgent"]
