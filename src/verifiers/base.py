# Verifiers Base Module
"""Base classes for the verification framework."""

from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class VerifierType(str, Enum):
    """Types of verifiers."""

    EXACT_QUOTE = "exact_quote"
    SOURCE_ATTRIBUTION = "source_attribution"
    EVIDENCE_SUFFICIENCY = "evidence_sufficiency"
    CONTRADICTION = "contradiction"
    SCHOOL_CONSISTENCY = "school_consistency"
    TEMPORAL_CONSISTENCY = "temporal_consistency"
    HADITH_GRADE = "hadith_grade"
    GROUNDEDNESS = "groundedness"


@dataclass
class VerificationResult:
    """Result of a verification check.

    Attributes:
        verifier_type: The type of verifier that produced this result
        passed: Whether the verification passed
        confidence: Confidence score (0.0-1.0)
        message: Human-readable message
        details: Additional details from the verifier
    """

    verifier_type: VerifierType
    passed: bool
    confidence: float
    message: str
    details: Optional[Dict[str, Any]] = None

    @property
    def is_verified(self) -> bool:
        """Whether the claim is verified (passed with sufficient confidence)."""
        return self.passed and self.confidence >= 0.7

    @property
    def issues(self) -> List[str]:
        """Get list of issues if verification failed."""
        if self.passed:
            return []
        return [self.message]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "is_verified": self.is_verified,
            "confidence": self.confidence,
            "issues": self.issues,
            "details": self.details or {},
            "verifier_type": self.verifier_type.value,
            "passed": self.passed,
            "message": self.message,
        }

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"VerificationResult({self.verifier_type.value}: {status}, confidence={self.confidence})"


@dataclass
class VerificationReport:
    """Aggregated verification report from multiple verifiers.

    Attributes:
        is_verified: Overall verification status
        confidence: Overall confidence score (0.0-1.0)
        issues: List of all verification issues
        details: Detailed results from each verifier
    """

    is_verified: bool
    confidence: float
    issues: List[str]
    details: Dict[str, Any]
    verifier_results: List[VerificationResult] = None

    def __post_init__(self):
        if self.verifier_results is None:
            self.verifier_results = []

    @classmethod
    def from_results(
        cls,
        results: List[VerificationResult],
        min_confidence: float = 0.7,
    ) -> "VerificationReport":
        """Create a report from a list of verification results.

        Args:
            results: List of VerificationResult objects
            min_confidence: Minimum confidence threshold for verification

        Returns:
            VerificationReport with aggregated results
        """
        all_issues = []
        details = {}

        for result in results:
            all_issues.extend(result.issues)
            details[result.verifier_type.value] = result.to_dict()

        # Overall verification is pass if no issues and sufficient confidence
        avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0.0
        is_verified = len(all_issues) == 0 and avg_confidence >= min_confidence

        return cls(
            is_verified=is_verified,
            confidence=round(avg_confidence, 3),
            issues=all_issues,
            details=details,
            verifier_results=results,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "is_verified": self.is_verified,
            "confidence": self.confidence,
            "issues": self.issues,
            "details": self.details,
        }


class BaseVerifier(ABC):
    """Abstract base class for all verifiers."""

    def __init__(self):
        self.verifier_type: VerifierType

    @abstractmethod
    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """Verify a claim against evidence."""
        pass

    @abstractmethod
    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if this verifier is applicable to the claim/evidence."""
        pass


class VerifierPipeline:
    """Pipeline that runs multiple verifiers."""

    def __init__(self):
        self.verifiers: List[BaseVerifier] = []

    def add_verifier(self, verifier: BaseVerifier) -> None:
        """Add a verifier to the pipeline."""
        self.verifiers.append(verifier)

    async def verify_all(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[VerificationResult]:
        """Run all applicable verifiers."""
        results = []
        for verifier in self.verifiers:
            if verifier.is_applicable(claim, evidence):
                result = await verifier.verify(claim, evidence, context)
                results.append(result)
        return results

    def get_results_summary(self, results: List[VerificationResult]) -> Dict[str, Any]:
        """Summarize verification results."""
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0.0

        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "average_confidence": avg_confidence,
            "all_passed": failed == 0,
        }
