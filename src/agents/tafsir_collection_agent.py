"""
Legacy Tafsir Collection Agent - DEPRECATED.

Migrated to: src/agents/collection/tafsir.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.tafsir_collection_agent is DEPRECATED. Use src.agents.collection.tafsir instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.collection.tafsir import TafsirCollectionAgent

__all__ = ["TafsirCollectionAgent"]
