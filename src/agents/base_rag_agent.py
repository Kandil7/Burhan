"""
Legacy Base RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/base.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.base_rag_agent is DEPRECATED. Use src.agents.collection.base (config-backed) instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.legacy.base_rag_agent import BaseRAGAgent

__all__ = ["BaseRAGAgent"]
