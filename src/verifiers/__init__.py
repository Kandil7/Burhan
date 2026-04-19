"""
Verifiers Module - DEPRECATED.

This module is DEPRECATED. The canonical verification layer is now in src/verification/.

Migration:
- src/verifiers/base.py -> src/verification/base.py
- src/verifiers/suite_builder.py -> src/verification/suite_builder.py
- src/verifiers/fiqh_checks.py -> src/verification/checks/fiqh_checks.py
- src/verifiers/exact_quote.py -> src/verification/checks/exact_quote.py
- src/verifiers/hadith_grade.py -> src/verification/checks/hadith_grade.py
- src/verifiers/source_attribution.py -> src/verification/checks/source_attribution.py
- src/verifiers/contradiction.py -> src/verification/checks/contradiction.py
- src/verifiers/evidence_sufficiency.py -> src/verification/checks/evidence_sufficiency.py
- src/verifiers/policies.py -> src/verification/policies.py
"""

import warnings

warnings.warn(
    "src.verifiers is DEPRECATED. Use src.verification instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location
from src.verifiers.base import VerificationReport
from src.verifiers.suite_builder import build_verification_suite_for, run_verification_suite

__all__ = ["VerificationReport", "build_verification_suite_for", "run_verification_suite"]
