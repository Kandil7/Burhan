"""
Legacy Fiqh RAG Agent - DEPRECATED.

This module is DEPRECATED. Use src/agents/collection/fiqh.py instead.

This file is kept for backward compatibility during migration.
Migrate to config-backed CollectionAgent pattern.
"""

import warnings

warnings.warn(
    "src.agents.fiqh_agent is DEPRECATED. Use src.agents.collection.fiqh (config-backed) instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from legacy location
from src.agents.legacy.fiqh_agent import FiqhAgent

__all__ = ["FiqhAgent"]
