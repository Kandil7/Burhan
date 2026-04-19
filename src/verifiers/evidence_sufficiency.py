# Evidence Sufficiency Verifier Module
"""Verifier for evidence sufficiency assessment."""

from typing import Optional, Dict, Any, List
from .base import BaseVerifier, VerificationResult, VerifierType
from dataclasses import dataclass


@dataclass
class SufficiencyCriteria:
    """Criteria for evidence sufficiency."""

    min_evidences: int = 2
    min_authority_score: float = 0.7
    require_multiple_sources: bool = True


class EvidenceSufficiencyVerifier(BaseVerifier):
    """Verifies that evidence is sufficient to support a claim."""

    def __init__(
        self,
        criteria: Optional[SufficiencyCriteria] = None,
    ):
        self.verifier_type = VerifierType.EVIDENCE_SUFFICIENCY
        self.criteria = criteria or SufficiencyCriteria()

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """Verify evidence sufficiency."""
        evidences = self._extract_evidences(evidence)

        # Check minimum number of evidences
        if len(evidences) < self.criteria.min_evidences:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.8,
                message=f"Insufficient evidences: {len(evidences)} < {self.criteria.min_evidences}",
                details={"evidence_count": len(evidences)},
            )

        # Check authority scores
        authority_scores = [e.get("authority_score", 0.5) for e in evidences]
        avg_authority = sum(authority_scores) / len(authority_scores)

        if avg_authority < self.criteria.min_authority_score:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.8,
                message=f"Authority score too low: {avg_authority:.2f}",
                details={"avg_authority": avg_authority},
            )

        # Check multiple sources if required
        if self.criteria.require_multiple_sources:
            sources = set(e.get("source_id") for e in evidences)
            if len(sources) < 2:
                return VerificationResult(
                    verifier_type=self.verifier_type,
                    passed=False,
                    confidence=0.8,
                    message="Multiple sources required",
                    details={"source_count": len(sources)},
                )

        sufficiency_score = self._calculate_sufficiency_score(evidences)

        return VerificationResult(
            verifier_type=self.verifier_type,
            passed=True,
            confidence=0.85,
            message="Evidence is sufficient",
            details={
                "evidence_count": len(evidences),
                "avg_authority": avg_authority,
                "sufficiency_score": sufficiency_score,
            },
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if this verifier is applicable."""
        return evidence is not None

    def _extract_evidences(self, evidence: Any) -> List[Dict[str, Any]]:
        """Extract evidences from evidence object."""
        # Placeholder - would implement actual extraction
        if isinstance(evidence, list):
            return evidence
        return []

    def _calculate_sufficiency_score(
        self,
        evidences: List[Dict[str, Any]],
    ) -> float:
        """Calculate a sufficiency score."""
        if not evidences:
            return 0.0

        count_score = min(len(evidences) / self.criteria.min_evidences, 1.0)

        authority_scores = [e.get("authority_score", 0.5) for e in evidences]
        authority_score = sum(authority_scores) / len(authority_scores)

        return (count_score + authority_score) / 2


# Default verifier instance
evidence_sufficiency_verifier = EvidenceSufficiencyVerifier()
