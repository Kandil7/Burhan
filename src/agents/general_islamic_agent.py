"""
Legacy General Islamic Knowledge RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/general.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.general_islamic_agent is DEPRECATED. Use src.agents.collection.general (config-backed) instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.legacy.general_islamic_agent import GeneralIslamicAgent

__all__ = ["GeneralIslamicAgent"]
