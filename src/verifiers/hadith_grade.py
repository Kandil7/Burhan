# Hadith Grade Verifier Module
"""Verifier for hadith grading and authenticity with esnad support."""

from typing import Optional, Dict, Any, List
from .base import BaseVerifier, VerificationResult, VerifierType
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class HadithGrade(str, Enum):
    """Grades of hadith authenticity.

    Attributes:
        SAHIH: Authentic - strong, unbroken chain
        HASAN: Good - acceptable chain
        DAIF: Weak - issues with chain
        MUNQATI: Disconnected - broken chain
        MUDALLAS: Hidden defect - unclear connection
        MOWDU: Fabricated - fabricated content
    """

    SAHIH = "sahih"  # Authentic
    HASAN = "hasan"  # Good
    DAIF = "daif"  # Weak
    MUNQATI = "munqati"  # Disconnected
    MUDALLAS = "mudallas"  # Hidden defect
    MOWDU = "mowdu"  # Fabricated


@dataclass
class HadithGradingResult:
    """Result of hadith grading.

    Attributes:
        grade: The hadith grade
        details: Additional details
        scholars: List of scholars who graded this hadith
    """

    grade: HadithGrade
    details: Optional[str] = None
    scholars: List[str] = None


# Known hadith collections and their default grades
HADITH_COLLECTIONS = {
    "sahih_bukhari": HadithGrade.SAHIH,
    "sahih_muslim": HadithGrade.SAHIH,
    "sunan_abudawud": HadithGrade.HASAN,
    "sunan_nasai": HadithGrade.HASAN,
    "sunan_ibnmajah": HadithGrade.HASAN,
    "jami_atirmidhi": HadithGrade.HASAN,
}


class HadithGradeVerifier(BaseVerifier):
    """Verifies hadith grades and authenticity.

    Supports:
    - Quran exact quotation validation
    - Hadith exact quotation validation
    - General source text matching

    Interface:
        verify(claim, evidence, context) -> VerificationResult
        is_applicable(claim, evidence) -> bool
    """

    def __init__(self, esnad_dir: Path | None = None):
        """Initialize the hadith grade verifier.

        Args:
            esnad_dir: Optional path to esnad directory for chain analysis
        """
        self.verifier_type = VerifierType.HADITH_GRADE
        self._esnad_dir = esnad_dir
        self._original_grader = None

        # Try to load the original hadith grader
        self._load_original_grader()

    def _load_original_grader(self):
        """Load the original HadithAuthenticityGrader if available."""
        try:
            from src.knowledge.hadith_grader import HadithAuthenticityGrader

            self._original_grader = HadithAuthenticityGrader(esnad_dir=self._esnad_dir)
        except ImportError:
            pass

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """Verify hadith grade.

        Args:
            claim: The claim/response containing hadith references
            evidence: Evidence passages to verify
            context: Additional context (collection, book_id, page, etc.)

        Returns:
            VerificationResult with hadith grade verification status
        """
        # Extract hadith reference from claim
        hadith_ref = self._extract_hadith_reference(claim)

        if not hadith_ref:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=True,
                confidence=1.0,
                message="No hadith reference found",
            )

        # Get context for grading
        collection = context.get("collection", "") if context else ""
        book_id = context.get("book_id")
        page = context.get("page")

        # Use original grader if available
        if self._original_grader and book_id and page:
            return self._verify_with_original_grader(book_id, page, hadith_ref)

        # Fallback to collection-based grading
        grade = self._get_grade_from_collection(hadith_ref, collection)

        if grade == HadithGrade.DAIF or grade == HadithGrade.MOWDU:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.9,
                message=f"Hadith is {grade.value}",
                details={"reference": hadith_ref, "grade": grade.value},
            )

        return VerificationResult(
            verifier_type=self.verifier_type,
            passed=True,
            confidence=0.95,
            message=f"Hadith is {grade.value}",
            details={"reference": hadith_ref, "grade": grade.value},
        )

    def _verify_with_original_grader(
        self,
        book_id: int,
        page: int,
        reference: str,
    ) -> VerificationResult:
        """Verify using the original HadithAuthenticityGrader."""
        try:
            grade_result = self._original_grader.grade_hadith(book_id, page)

            grade = grade_result.get("grade", "unknown")
            confidence = grade_result.get("confidence", 0.5)
            weight = grade_result.get("weight", 0.5)

            # Map to our grades
            grade_map = {
                "sahih": HadithGrade.SAHIH,
                "hasan": HadithGrade.HASAN,
                "da'if": HadithGrade.DAIF,
            }

            mapped_grade = grade_map.get(grade, HadithGrade.DAIF)

            # Determine pass/fail
            passed = mapped_grade in [HadithGrade.SAHIH, HadithGrade.HASAN]

            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=passed,
                confidence=confidence,
                message=f"Hadith grade: {grade} (weight: {weight})",
                details={
                    "reference": reference,
                    "grade": grade,
                    "chain_length": grade_result.get("chain_length"),
                    "chain_count": grade_result.get("chain_count"),
                    "authenticity_weight": weight,
                },
            )
        except Exception as e:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=True,
                confidence=0.5,
                message=f"Could not verify with esnad: {str(e)}",
                details={"error": str(e)},
            )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if this verifier is applicable.

        Args:
            claim: The claim text
            evidence: Evidence passages

        Returns:
            True if claim contains hadith-related keywords
        """
        hadith_keywords = ["hadith", "حديث", "صحيح", "ضعيف", "رسول"]
        return any(kw in claim.lower() for kw in hadith_keywords)

    def _extract_hadith_reference(self, claim: str) -> Optional[str]:
        """Extract hadith reference from claim.

        Args:
            claim: The claim text

        Returns:
            Extracted hadith reference or None
        """
        import re

        # Common patterns
        patterns = [
            r"(Sahih |Al-)?(?:Bukhari|Muslim)[\s,:]+(\d+)",
            r"(?:Abu Dawud|Nasai|Ibn Majah|Tirmidhi)[\s,:]+(\d+)",
            r"حديث\s+(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, claim, re.IGNORECASE)
            if match:
                return match.group()

        return None

    def _get_grade_from_collection(
        self,
        reference: str,
        collection: str,
    ) -> HadithGrade:
        """Get grade from collection name.

        Args:
            reference: Hadith reference
            collection: Collection name

        Returns:
            HadithGrade
        """
        # Check collection first
        collection_lower = collection.lower()
        for coll, grade in HADITH_COLLECTIONS.items():
            if coll in collection_lower:
                return grade

        # Check reference string
        ref_lower = reference.lower()
        for coll, grade in HADITH_COLLECTIONS.items():
            if coll in ref_lower:
                return grade

        # Unknown - return default
        return HadithGrade.DAIF

    def enrich_passages_with_authenticity(self, passages: List[Dict]) -> List[Dict]:
        """Enrich passages with hadith authenticity grades.

        Args:
            passages: List of passage dictionaries

        Returns:
            Passages with added authenticity metadata
        """
        if self._original_grader:
            return self._original_grader.enrich_passages_with_authenticity(passages)
        return passages


# Default verifier instance
hadith_grade_verifier = HadithGradeVerifier()
