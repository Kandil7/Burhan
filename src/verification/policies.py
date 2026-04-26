# Verification Policies Module
"""Policies for controlling verification behavior."""

from typing import Dict, List, Set
from enum import Enum
from .schemas import VerifierType


class VerificationLevel(str, Enum):
    """Levels of verification rigor."""

    MINIMAL = "minimal"  # Basic checks only
    STANDARD = "standard"  # Standard verification
    STRICT = "strict"  # Maximum verification
    DISABLED = "disabled"  # No verification


class VerificationPolicy:
    """Policy for controlling verification behavior."""

    def __init__(self, level: VerificationLevel = VerificationLevel.STANDARD):
        self.level = level
        self._enabled_verifiers: Dict[VerifierType, bool] = self._get_defaults()

    def _get_defaults(self) -> Dict[VerifierType, bool]:
        """Get default enabled verifiers for each level."""
        defaults = {
            VerificationLevel.MINIMAL: {
                VerifierType.EXACT_QUOTE: True,
                VerifierType.SOURCE_ATTRIBUTION: False,
                VerifierType.EVIDENCE_SUFFICIENCY: False,
                VerifierType.CONTRADICTION: False,
                VerifierType.SCHOOL_CONSISTENCY: False,
                VerifierType.TEMPORAL_CONSISTENCY: False,
                VerifierType.HADITH_GRADE: True,
                VerifierType.GROUNDEDNESS: False,
            },
            VerificationLevel.STANDARD: {
                VerifierType.EXACT_QUOTE: True,
                VerifierType.SOURCE_ATTRIBUTION: True,
                VerifierType.EVIDENCE_SUFFICIENCY: True,
                VerifierType.CONTRADICTION: True,
                VerifierType.SCHOOL_CONSISTENCY: True,
                VerifierType.TEMPORAL_CONSISTENCY: False,
                VerifierType.HADITH_GRADE: True,
                VerifierType.GROUNDEDNESS: True,
            },
            VerificationLevel.STRICT: {
                VerifierType.EXACT_QUOTE: True,
                VerifierType.SOURCE_ATTRIBUTION: True,
                VerifierType.EVIDENCE_SUFFICIENCY: True,
                VerifierType.CONTRADICTION: True,
                VerifierType.SCHOOL_CONSISTENCY: True,
                VerifierType.TEMPORAL_CONSISTENCY: True,
                VerifierType.HADITH_GRADE: True,
                VerifierType.GROUNDEDNESS: True,
            },
            VerificationLevel.DISABLED: {v: False for v in VerifierType},
        }
        return defaults.get(self.level, {})

    def is_enabled(self, verifier_type: VerifierType) -> bool:
        """Check if a verifier is enabled."""
        return self._enabled_verifiers.get(verifier_type, False)

    def enable_verifier(self, verifier_type: VerifierType) -> None:
        """Enable a specific verifier."""
        self._enabled_verifiers[verifier_type] = True

    def disable_verifier(self, verifier_type: VerifierType) -> None:
        """Disable a specific verifier."""
        self._enabled_verifiers[verifier_type] = False

    def set_level(self, level: VerificationLevel) -> None:
        """Set verification level."""
        self.level = level
        self._enabled_verifiers = self._get_defaults()

    def get_enabled_types(self) -> List[VerifierType]:
        """Get list of enabled verifier types."""
        return [v for v, enabled in self._enabled_verifiers.items() if enabled]


# Default policy instance
verification_policy = VerificationPolicy()
