"""
Legacy v1 path re-exports for backward compatibility.

This module exists for backward compatibility. The canonical location
is now src.agents.collection

DEPRECATED: Use src.agents.collection instead.
"""

import warnings

from src.agents.collection.base import (
    CollectionAgent,
    CollectionAgentConfig,
    FallbackPolicy,
    RetrievalStrategy,
    VerificationCheck,
    VerificationReport,
    VerificationSuite,
)

# Emit deprecation warning when this module is imported
warnings.warn(
    "src.agents.collection_agent is deprecated. Use src.agents.collection instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    # Base classes
    "CollectionAgent",
    "CollectionAgentConfig",
    "RetrievalStrategy",
    "VerificationSuite",
    "VerificationCheck",
    "FallbackPolicy",
    "VerificationReport",
]
