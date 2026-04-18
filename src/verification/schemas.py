"""
Verification Schemas for Athar Islamic QA system.

Defines the canonical schemas for the verification layer.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    """Verification status values."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ABSTAINED = "abstained"


class CheckResult(BaseModel):
    """Result of a single verification check."""

    check_name: str = Field(description="Name of the check")
    status: VerificationStatus = Field(description="Check status")
    message: str | None = Field(default=None, description="Status message")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Check confidence")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class VerificationReport(BaseModel):
    """
    Complete verification report for a query and passages.

    This is the canonical format for verification results.
    """

    query: str = Field(description="Original query")
    is_verified: bool = Field(description="Overall verification status")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence")
    status: VerificationStatus = Field(description="Overall status")
    issues: list[str] = Field(default_factory=list, description="List of issues found")
    check_results: list[CheckResult] = Field(default_factory=list, description="Individual check results")
    verified_passages: list[dict[str, Any]] = Field(
        default_factory=list, description="Passages that passed verification"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "query": self.query,
            "is_verified": self.is_verified,
            "confidence": self.confidence,
            "status": self.status.value,
            "issues": self.issues,
            "check_results": [
                {
                    "check_name": r.check_name,
                    "status": r.status.value,
                    "message": r.message,
                    "confidence": r.confidence,
                }
                for r in self.check_results
            ],
            "verified_passages_count": len(self.verified_passages),
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


__all__ = [
    "VerificationStatus",
    "CheckResult",
    "VerificationReport",
    "AbstentionReason",
    "Abstention",
]
