"""
Legacy Fiqh Collection Agent - DEPRECATED.

Migrated to: src/agents/collection/fiqh.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.fiqh_collection_agent is DEPRECATED. Use src.agents.collection.fiqh instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.collection.fiqh import FiqhCollectionAgent

__all__ = ["FiqhCollectionAgent"]
