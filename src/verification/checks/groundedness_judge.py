# Groundedness Judge Module
"""Judge for overall groundedness of responses."""

from typing import Optional, Dict, Any, List
from ..schemas import CheckResult, VerificationStatus, VerifierType
from ..base import BaseVerifier
from dataclasses import dataclass
from enum import Enum


class GroundednessLevel(str, Enum):
    """Levels of groundedness."""

    FULL = "full"
    PARTIAL = "partial"
    UNGROUNDED = "ungrounded"


@dataclass
class GroundednessScore:
    """Score for groundedness assessment."""

    level: GroundednessLevel
    score: float  # 0-1
    supported_claims: int
    unsupported_claims: int
    evidence_count: int


class GroundednessJudge(BaseVerifier):
    """Judges overall groundedness of a response."""

    def __init__(
        self,
        min_evidence_ratio: float = 0.8,
    ):
        self.verifier_type = VerifierType.GROUNDEDNESS
        self.min_evidence_ratio = min_evidence_ratio

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> CheckResult:
        """Judge groundedness of claim."""
        # Extract claims from response
        claims = self._extract_claims(claim)

        # Extract evidences
        evidences = self._extract_evidences(evidence)

        if not claims:
            return CheckResult(
                check_name=self.verifier_type.value,
                passed=True,
                confidence=1.0,
                message="No claims to verify",
            )

        # Count supported vs unsupported claims
        supported = 0
        unsupported = 0

        for c in claims:
            if self._is_supported(c, evidences):
                supported += 1
            else:
                unsupported += 1

        # Calculate groundedness
        evidence_ratio = supported / len(claims) if claims else 0

        if evidence_ratio >= self.min_evidence_ratio:
            level = GroundednessLevel.FULL
            passed = True
            message = "Response is fully grounded"
        elif evidence_ratio >= 0.5:
            level = GroundednessLevel.PARTIAL
            passed = True
            message = "Response is partially grounded"
        else:
            level = GroundednessLevel.UNGROUNDED
            passed = False
            message = "Response is not sufficiently grounded"

        return CheckResult(
            check_name=self.verifier_type.value,
            passed=passed,
            confidence=0.85,
            message=message,
            details={
                "level": level.value,
                "supported_claims": supported,
                "unsupported_claims": unsupported,
                "evidence_count": len(evidences),
                "groundedness_ratio": evidence_ratio,
            },
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if this verifier is applicable."""
        return evidence is not None

    def _extract_claims(self, text: str) -> List[str]:
        """Extract claims from text."""
        # Placeholder - would implement actual claim extraction
        # Split by sentence endings
        import re

        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_evidences(self, evidence: Any) -> List[Dict[str, Any]]:
        """Extract evidences from evidence object."""
        # Placeholder - would implement actual extraction
        if isinstance(evidence, list):
            return evidence
        return []

    def _is_supported(
        self,
        claim: str,
        evidences: List[Dict[str, Any]],
    ) -> bool:
        """Check if a claim is supported by evidence."""
        # Placeholder - would implement actual support detection
        # For now, assume all claims are supported if there's evidence
        return len(evidences) > 0


# Default judge instance
groundedness_judge = GroundednessJudge()
