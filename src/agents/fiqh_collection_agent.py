"""
Legacy Fiqh Collection Agent - DEPRECATED.

Migrated to: src/agents/collection/fiqh.py (config-backed pattern)

This module re-exports from the new location for backward compatibility.
"""

import warnings

warnings.warn(
    "src.agents.fiqh_collection_agent is DEPRECATED. Use src.agents.collection.fiqh instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.collection.fiqh import FiqhCollectionAgent
from src.agents.collection.fiqh import _normalize_arabic

__all__ = ["FiqhCollectionAgent", "_normalize_arabic"]
