"""
Legacy UsulFiqh Collection Agent - DEPRECATED.

Migrated to: src/agents/collection/usul_fiqh.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.usul_fiqh_collection_agent is DEPRECATED. Use src.agents.collection.usul_fiqh instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.collection.usul_fiqh import UsulFiqhCollectionAgent

__all__ = ["UsulFiqhCollectionAgent"]
