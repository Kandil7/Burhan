"""
Verification module - first-class verification layer for Athar.
"""

from src.verification.schemas import (
    VerificationStatus,
    VerifierType,
    CheckResult,
    VerificationReport,
    AbstentionReason,
    Abstention,
    VerificationCheck,
    VerificationSuite,
)
from src.verification.trace import VerificationStep, VerificationTrace, generate_trace_id
from src.verification.base import BaseVerifier, VerifierPipeline
from src.verification.suite_builder import (
    build_verification_suite_for,
    run_verification_suite,
    register_all_checks,
)

__all__ = [
    # Schemas
    "VerificationStatus",
    "VerifierType",
    "CheckResult",
    "VerificationReport",
    "AbstentionReason",
    "Abstention",
    "VerificationCheck",
    "VerificationSuite",
    # Tracing
    "VerificationStep",
    "VerificationTrace",
    "generate_trace_id",
    # Base Logic
    "BaseVerifier",
    "VerifierPipeline",
    # Suite Management
    "build_verification_suite_for",
    "run_verification_suite",
    "register_all_checks",
]
