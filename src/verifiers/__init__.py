"""
Verifiers Module - DEPRECATED.

This module is DEPRECATED. The canonical verification layer is now src/verification/.

Migration path:
- src/verification/base.py - BaseVerifier, VerifierPipeline
- src/verification/schemas.py - VerificationReport, CheckResult, VerifierType
- src/verification/checks/*.py - Individual verifiers
- src/verification/suite_builder.py - build_verification_suite_for, run_verification_suite
"""

import warnings

warnings.warn(
    "src.verifiers is DEPRECATED. Use src.verification instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new canonical location
from src.verification.schemas import VerificationReport
from src.verification.pipeline import VerifierPipeline

# These moved to suite_builder in verification/
try:
    from src.verification.suite_builder import build_verification_suite_for, run_verification_suite
except ImportError:
    build_verification_suite_for = None
    run_verification_suite = None

__all__ = [
    "VerificationReport",
    "VerifierPipeline",
    "build_verification_suite_for",
    "run_verification_suite",
]
