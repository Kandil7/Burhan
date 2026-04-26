# Verifier Pipeline Module
"""Pipeline for running multiple verifiers."""

from typing import List, Optional, Dict, Any
from .schemas import CheckResult, VerificationReport, VerificationStatus, VerifierType
from .base import BaseVerifier
from .policies import VerificationPolicy, VerificationLevel

# Alias for backward compatibility
VerificationResult = CheckResult


class VerifierPipeline:
    """Pipeline that orchestrates multiple verifiers.

    Supports:
    - Quran verification
    - Hadith verification
    - Chained verification

    Interface:
        verify_claim(claim, evidence, context) -> Dict[str, Any>
        register_verifier(verifier_type, verifier) -> None
    """

    def __init__(self, policy: Optional[VerificationPolicy] = None):
        self.verifiers: Dict[VerifierType, BaseVerifier] = {}
        self.policy = policy or VerificationPolicy()

    def register_verifier(
        self,
        verifier_type: VerifierType,
        verifier: BaseVerifier,
    ) -> None:
        """Register a verifier.

        Args:
            verifier_type: Type of verifier to register
            verifier: Verifier instance
        """
        self.verifiers[verifier_type] = verifier

    async def verify_claim(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Verify a claim using all applicable verifiers.

        Args:
            claim: The claim/response to verify
            evidence: Evidence passages
            context: Additional context

        Returns:
            Dict with verification results and summary

        The returned dict contains:
            - results: List of VerificationResult objects
            - summary: Summary with total, passed, failed, confidence
            - report: VerificationReport with aggregated results
        """
        results = []
        enabled_types = self.policy.get_enabled_types()

        for verifier_type, verifier in self.verifiers.items():
            # Skip disabled verifiers
            if verifier_type not in enabled_types:
                continue

            if verifier.is_applicable(claim, evidence):
                result = await verifier.verify(claim, evidence, context)
                results.append(result)

        # Create aggregated report
        report = VerificationReport.from_results(results)

        # Get summary
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0.0

        return {
            "results": results,
            "report": report,
            "summary": {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "average_confidence": round(avg_confidence, 3),
                "all_passed": failed == 0,
            },
            "is_verified": report.is_verified,
            "confidence": report.confidence,
            "issues": report.issues,
        }

    async def verify_claim_chain(
        self,
        claims: List[str],
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Verify multiple claims in sequence.

        Args:
            claims: List of claims to verify
            evidence: Evidence passages
            context: Additional context

        Returns:
            List of verification results for each claim
        """
        results = []

        for claim in claims:
            result = await self.verify_claim(claim, evidence, context)
            results.append(result)

        return results

    def get_enabled_verifiers(self) -> List[VerifierType]:
        """Get list of enabled verifier types."""
        return [v for v in self.verifiers.keys() if self.policy.is_enabled(v)]

    def set_policy(self, policy: VerificationPolicy) -> None:
        """Set verification policy.

        Args:
            policy: VerificationPolicy to use
        """
        self.policy = policy

    def set_verification_level(self, level: VerificationLevel) -> None:
        """Set verification level.

        Args:
            level: VerificationLevel (MINIMAL, STANDARD, STRICT, DISABLED)
        """
        self.policy.set_level(level)


# Factory function for creating pipeline
def create_verification_pipeline(
    level: VerificationLevel = VerificationLevel.STANDARD,
) -> VerifierPipeline:
    """Create a verification pipeline with default verifiers.

    Args:
        level: Verification level to use

    Returns:
        Configured VerifierPipeline
    """
    from .checks.exact_quote import exact_quote_verifier
    from .checks.hadith_grade import hadith_grade_verifier
    from .checks.source_attribution import source_attribution_verifier
    from .checks.evidence_sufficiency import evidence_sufficiency_verifier
    from .checks.contradiction import contradiction_verifier
    from .checks.school_consistency import school_consistency_verifier
    from .checks.temporal_consistency import temporal_consistency_verifier
    from .checks.groundedness_judge import groundedness_judge

    pipeline = VerifierPipeline(policy=VerificationPolicy(level=level))

    # Register all verifiers
    pipeline.register_verifier(VerifierType.EXACT_QUOTE, exact_quote_verifier)
    pipeline.register_verifier(VerifierType.HADITH_GRADE, hadith_grade_verifier)
    pipeline.register_verifier(VerifierType.SOURCE_ATTRIBUTION, source_attribution_verifier)
    pipeline.register_verifier(VerifierType.EVIDENCE_SUFFICIENCY, evidence_sufficiency_verifier)
    pipeline.register_verifier(VerifierType.CONTRADICTION, contradiction_verifier)
    pipeline.register_verifier(VerifierType.SCHOOL_CONSISTENCY, school_consistency_verifier)
    pipeline.register_verifier(VerifierType.TEMPORAL_CONSISTENCY, temporal_consistency_verifier)
    pipeline.register_verifier(VerifierType.GROUNDEDNESS, groundedness_judge)

    return pipeline


# Default pipeline instance
verifier_pipeline = create_verification_pipeline()
