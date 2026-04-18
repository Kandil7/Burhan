"""
Legacy Collection Agent Base - DEPRECATED.

Migrated to: src/agents/collection/base.py (config-backed pattern)
"""

import warnings

warnings.warn(
    "src.agents.collection_agent is DEPRECATED. Use src.agents.collection.base instead.",
    DeprecationWarning,
    stacklevel=2,
)

from src.agents.collection.base import (
    CollectionAgent,
    CollectionAgentConfig,
    IntentLabel,
    RetrievalStrategy,
    VerificationSuite,
    VerificationCheck,
    FallbackPolicy,
    VerificationReport,
)

__all__ = [
    "CollectionAgent",
    "CollectionAgentConfig",
    "IntentLabel",
    "RetrievalStrategy",
    "VerificationSuite",
    "VerificationCheck",
    "FallbackPolicy",
    "VerificationReport",
]
