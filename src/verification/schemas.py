"""
Verification Schemas for Burhan Islamic QA system.

Defines the canonical schemas for the verification layer.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional, List, Dict

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

    checks: List[VerificationCheck] = Field(
        default_factory=list, description="List of verification checks"
    )
    fail_fast: bool = Field(
        default=True, description="Stop on first failure if True"
    )


class CheckResult(BaseModel):
    """Result of a single verification check."""

    check_name: str = Field(description="Name of the check")
    status: VerificationStatus = Field(description="Check status")
    passed: bool = Field(default=True, description="Whether the check passed")
    message: Optional[str] = Field(default=None, description="Status message")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Check confidence")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VerificationReport(BaseModel):
    """
    Complete verification report for a query and passages.

    This is the canonical format for verification results.
    """

    query: Optional[str] = Field(default=None, description="Original query")
    is_verified: bool = Field(description="Overall verification status")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence")
    status: VerificationStatus = Field(default=VerificationStatus.PASSED, description="Overall status")
    issues: List[Any] = Field(default_factory=list, description="List of issues found")
    check_results: Dict[str, Any] = Field(default_factory=dict, description="Individual check results as dict")
    verified_passages: List[Dict[str, Any]] = Field(
        default_factory=list, description="Passages that passed verification"
    )
    details: Dict[str, Any] = Field(default_factory=dict, description="Aggregated details")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def from_passages(
        cls,
        passages: List[dict],
        is_verified: bool = True,
        confidence: float = 1.0,
        issues: Optional[List[Any]] = None,
    ) -> VerificationReport:
        return cls(
            is_verified=is_verified,
            confidence=confidence,
            issues=issues or [],
            status=VerificationStatus.PASSED if is_verified else VerificationStatus.FAILED,
            verified_passages=passages,
        )

    def to_dict(self) -> Dict[str, Any]:
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
    fallback_agent: Optional[str] = Field(default=None, description="Suggested fallback")
    requires_human_review: bool = Field(default=True, description="Requires human review")


__all__ = [
    "VerificationStatus",
    "VerifierType",
    "VerificationCheck",
    "VerificationSuite",
    "CheckResult",
    "VerificationReport",
    "AbstentionReason",
    "Abstention",
]
