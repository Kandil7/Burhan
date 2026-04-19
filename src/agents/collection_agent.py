"""
Alias for retrieval strategy (legacy v1 path re-export).

This module exists for backward compatibility. The canonical location
is now src.agents.collection.base.RetrievalStrategy
"""

from src.agents.collection.base import (
    RetrievalStrategy,
    VerificationCheck,
    VerificationReport,
    VerificationSuite,
)

__all__ = [
    "RetrievalStrategy",
    "VerificationCheck",
    "VerificationSuite",
    "VerificationReport",
]
