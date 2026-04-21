# Shim for backward compatibility - re-exports from src.verification.base
from src.verification.base import (
    BaseVerifier,
    CheckResult,
    VerificationReport,
    VerificationStatus,
    VerifierType,
)

__all__ = [
    "BaseVerifier",
    "CheckResult",
    "VerificationReport",
    "VerificationStatus",
    "VerifierType",
]
