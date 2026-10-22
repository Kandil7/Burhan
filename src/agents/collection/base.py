"""
One-release shim (hardening Phase 5).

The ten collection agent classes and their base class were replaced by the
spec-driven src.agents.pipeline.RAGPipeline. The configuration models moved
to src.agents.config_models; the verification types re-export from
src.verification. Import from those homes in new code; this shim disappears
after the next release.
"""

from __future__ import annotations

from src.agents.config_models import (
    CollectionAgentConfig as CollectionAgentConfig,
)
from src.agents.config_models import (
    FallbackPolicy as FallbackPolicy,
)
from src.agents.config_models import (
    RetrievalStrategy as RetrievalStrategy,
)
from src.verification import (
    VerificationCheck as VerificationCheck,
)
from src.verification import (
    VerificationReport as VerificationReport,
)
from src.verification import (
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
