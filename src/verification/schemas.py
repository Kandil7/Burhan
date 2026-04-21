"""
Verification Schemas for Athar Islamic QA system.

Defines the canonical schemas for the verification layer.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    """Verification status values."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ABSTAINED = "abstained"
    WARNING = "warning"


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


class VerificationCheck(BaseModel):
    """Individual verification check configuration."""

    name: str = Field(description="Check identifier")
    fail_policy: str = Field(
        default="abstain",
        description="Action on failure: abstain/warn/proceed",
    )
    enabled: bool = Field(default=True, description="Whether check is active")


class VerificationSuite(BaseModel):
    """Collection of verification checks with fail-fast behavior."""

    checks: list[VerificationCheck] = Field(default_factory=list, description="List of verification checks")
    fail_fast: bool = Field(default=True, description="Stop on first failure if True")


class CheckResult(BaseModel):
    """Result of a single verification check."""

    check_name: str = Field(description="Name of the check")
    status: VerificationStatus = Field(default=VerificationStatus.PASSED, description="Check status")
    passed: bool = Field(default=True, description="Whether the check passed")
    message: str | None = Field(default=None, description="Status message")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Check confidence")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def __init__(self, **data):
        # Handle backward compatibility: accept passed=True/False for status
        if "passed" in data and "status" not in data:
            data["status"] = VerificationStatus.PASSED if data.get("passed", True) else VerificationStatus.FAILED
        super().__init__(**data)


class VerificationReport(BaseModel):
    """
    Complete verification report for a query and passages.

    This is the canonical format for verification results.
    """

    is_verified: bool = Field(description="Overall verification status")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence")
    status: VerificationStatus = Field(default=VerificationStatus.PASSED, description="Overall status")
    issues: list[Any] = Field(default_factory=list, description="List of issues found")
    check_results: dict[str, Any] = Field(default_factory=dict, description="Individual check results as dict")
    verified_passages: list[dict[str, Any]] = Field(
        default_factory=list, description="Passages that passed verification"
    )
    details: dict[str, Any] = Field(default_factory=dict, description="Aggregated details")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def from_passages(
        cls,
        passages: list[dict],
        is_verified: bool = True,
        confidence: float = 1.0,
        issues: list[Any] | None = None,
    ) -> VerificationReport:
        return cls(
            is_verified=is_verified,
            confidence=confidence,
            issues=issues or [],
            status=VerificationStatus.PASSED if is_verified else VerificationStatus.FAILED,
            verified_passages=passages,
        )

    @classmethod
    def from_results(
        cls,
        results: list[CheckResult],
    ) -> VerificationReport:
        """Create a VerificationReport from a list of CheckResults.

        Args:
            results: List of check results from verification checks.

        Returns:
            Aggregated VerificationReport.
        """
        if not results:
            return cls(
                is_verified=False,
                confidence=0.0,
                status=VerificationStatus.ABSTAINED,
                issues=["No verification checks were performed"],
            )

        # Aggregate results
        is_verified = all(r.status == VerificationStatus.PASSED for r in results)
        avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0.0

        # Collect verified passages from all checks
        verified_passages: list[dict[str, Any]] = []
        issues: list[Any] = []

        for r in results:
            if r.passages:
                verified_passages.extend(r.passages)
            if r.issues:
                issues.extend(r.issues)

        # Determine overall status
        if any(r.status == VerificationStatus.FAILED for r in results):
            status = VerificationStatus.FAILED
        elif any(r.status == VerificationStatus.WARNING for r in results):
            status = VerificationStatus.WARNING
        else:
            status = VerificationStatus.PASSED

        return cls(
            is_verified=is_verified,
            confidence=avg_confidence,
            status=status,
            issues=issues,
            check_results={r.check_name: r.model_dump() for r in results},
            verified_passages=verified_passages,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "is_verified": self.is_verified,
            "confidence": self.confidence,
            "status": self.status.value,
            "issues": self.issues,
            "verified_passages_count": len(self.verified_passages),
            "details": self.details,
            "metadata": self.metadata,
        }


class AbstentionReason(str, Enum):
    """Reasons for abstention."""

    LOW_CONFIDENCE = "low_confidence"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    SENSITIVE_TOPIC = "sensitive_topic"
    CONTRADICTORY_SOURCES = "contradictory_sources"
    GRADE_RESTRICTION = "grade_restriction"
    OTHER = "other"


class Abstention(BaseModel):
    """Abstention decision when verification fails."""

    reason: AbstentionReason = Field(description="Reason for abstention")
    message: str = Field(description="Abstention message")
    fallback_agent: str | None = Field(default=None, description="Suggested fallback")
    requires_human_review: bool = Field(default=True, description="Requires human review")


# Alias for backward compatibility
VerificationResult = CheckResult

__all__ = [
    "VerificationStatus",
    "VerifierType",
    "VerificationCheck",
    "VerificationSuite",
    "CheckResult",
    "VerificationResult",  # Alias
    "VerificationReport",
    "AbstentionReason",
    "Abstention",
]
