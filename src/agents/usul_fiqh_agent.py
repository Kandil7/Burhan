"""
Legacy Usul al-Fiqh RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/usul_fiqh.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.usul_fiqh_agent is DEPRECATED. Use src.agents.collection.usul_fiqh (config-backed) instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.legacy.usul_fiqh_agent import UsulFiqhAgent

__all__ = ["UsulFiqhAgent"]
