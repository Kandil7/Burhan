"""
Verification Checks - Canonical verification implementations.

This module re-exports verification checks from the deprecated verifiers module
for backward compatibility. The canonical path is now src/verification/.

For new code, import directly from src.verifiers.base, etc.
"""

# Re-export all verification classes for backward compatibility
from src.verifiers.base import (
    VerificationResult,
    VerificationReport,
    BaseVerifier,
    VerifierPipeline,
    VerifierType,
)

from src.verifiers.exact_quote import ExactQuoteVerifier
from src.verifiers.source_attribution import SourceAttributionVerifier
from src.verifiers.evidence_sufficiency import EvidenceSufficiencyVerifier
from src.verifiers.hadith_grade import HadithGradeVerifier
from src.verifiers.contradiction import ContradictionVerifier
from src.verifiers.school_consistency import SchoolConsistencyVerifier

__all__ = [
    # Base classes
    "VerificationResult",
    "VerificationReport",
    "BaseVerifier",
    "VerifierPipeline",
    "VerifierType",
    # Verifiers
    "ExactQuoteVerifier",
    "SourceAttributionVerifier",
    "EvidenceSufficiencyVerifier",
    "HadithGradeVerifier",
    "ContradictionVerifier",
    "SchoolConsistencyVerifier",
]
