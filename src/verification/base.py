"""
Base classes for the verification framework.

This module provides abstract base classes and core data structures
for the verification system, integrated with Pydantic schemas.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.verification.schemas import (
    CheckResult,
    VerificationReport,
    VerificationStatus,
    VerifierType,
)


class BaseVerifier(ABC):
    """Abstract base class for all verifiers."""

    def __init__(self, verifier_type: VerifierType):
        self.verifier_type = verifier_type

    @abstractmethod
    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> CheckResult:
        """
        Verify a claim against evidence.

        Args:
            claim: The text or claim to verify
            evidence: Passages or data to verify against
            context: Optional additional context

        Returns:
            CheckResult containing the verification outcome
        """
        pass

    @abstractmethod
    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """
        Check if this verifier is applicable to the claim/evidence.

        Args:
            claim: The text or claim to verify
            evidence: Passages or data to verify against

        Returns:
            True if this verifier can handle the input
        """
        pass


class VerifierPipeline:
    """Pipeline that runs multiple verifiers and aggregates results."""

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
    ) -> List[CheckResult]:
        """Run all applicable verifiers."""
        results = []
        for verifier in self.verifiers:
            if verifier.is_applicable(claim, evidence):
                result = await verifier.verify(claim, evidence, context)
                results.append(result)
        return results

    def get_results_summary(self, results: List[CheckResult]) -> Dict[str, Any]:
        """Summarize verification results."""
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        avg_confidence = (
            sum(r.confidence for r in results) / len(results) if results else 0.0
        )

        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "average_confidence": round(avg_confidence, 3),
            "all_passed": failed == 0,
        }


__all__ = ["BaseVerifier", "VerifierPipeline", "VerifierType"]
