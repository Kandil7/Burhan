"""
Legacy Aqeedah Collection Agent - DEPRECATED.

Migrated to: src/agents/collection/aqeedah.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.aqeedah_collection_agent is DEPRECATED. Use src.agents.collection.aqeedah instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.collection.aqeedah import AqeedahCollectionAgent

__all__ = ["AqeedahCollectionAgent"]
