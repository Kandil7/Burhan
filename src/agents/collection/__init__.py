"""
One-release shim (hardening Phase 5).

The collection agent classes are gone; one RAGPipeline in src.agents.pipeline
covers them all, configured by config/agents/*.yaml. The configuration models
re-export here so the legacy import paths keep working until the next
release.
"""

from __future__ import annotations

from src.agents.collection.base import (
    CollectionAgentConfig as CollectionAgentConfig,
)
from src.agents.collection.base import (
    FallbackPolicy as FallbackPolicy,
)
from src.agents.collection.base import (
    RetrievalStrategy as RetrievalStrategy,
)
from src.agents.collection.base import (
    VerificationCheck as VerificationCheck,
)
from src.agents.collection.base import (
    VerificationReport as VerificationReport,
)
from src.agents.collection.base import (
    VerificationSuite as VerificationSuite,
)

__all__ = [
    "CollectionAgentConfig",
    "FallbackPolicy",
    "RetrievalStrategy",
    "VerificationCheck",
    "VerificationReport",
    "VerificationSuite",
]
