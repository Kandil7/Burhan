"""
Legacy Seerah Collection Agent - DEPRECATED.

Migrated to: src/agents/collection/seerah.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.seerah_collection_agent is DEPRECATED. Use src.agents.collection.seerah instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.collection.seerah import SeerahCollectionAgent

__all__ = ["SeerahCollectionAgent"]
