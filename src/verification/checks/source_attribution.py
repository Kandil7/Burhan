# Source Attribution Verifier Module
"""Verifier for source attribution validation."""

from typing import Optional, Dict, Any, List
from ..schemas import CheckResult, VerificationStatus, VerifierType
from ..base import BaseVerifier


class SourceAttributionVerifier(BaseVerifier):
    """Verifies that sources are properly attributed.

    Supports:
    - Quran verification
    - Hadith verification
    - General source attribution

    Interface:
        verify(claim, evidence, context) -> VerificationResult
        is_applicable(claim, evidence) -> bool
    """

    def __init__(self):
        self.verifier_type = VerifierType.SOURCE_ATTRIBUTION

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> CheckResult:
        """Verify source attribution.

        Args:
            claim: The claim/response containing source attributions
            evidence: Evidence passages to verify against
            context: Additional context (sources, etc.)

        Returns:
            VerificationResult with attribution verification status
        """
        # Extract claimed sources from claim
        claimed_sources = self._extract_sources(claim)

        if not claimed_sources:
            return CheckResult(
                check_name=self.verifier_type.value,
                passed=True,
                confidence=1.0,
                message="No sources claimed in claim",
            )

        # Get evidence sources from context
        evidence_sources = context.get("sources", []) if context else []

        # Verify each source against evidence
        valid_sources = []
        invalid_sources = []

        for source in claimed_sources:
            if self._verify_source(source, evidence, evidence_sources):
                valid_sources.append(source)
            else:
                invalid_sources.append(source)

        if invalid_sources:
            return CheckResult(
                check_name=self.verifier_type.value,
                passed=False,
                confidence=0.7,
                message=f"Invalid sources: {invalid_sources}",
                details={"invalid_sources": invalid_sources, "valid_sources": valid_sources},
            )

        return CheckResult(
            check_name=self.verifier_type.value,
            passed=True,
            confidence=0.9,
            message="All sources properly attributed",
            details={"valid_sources": valid_sources},
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if this verifier is applicable.

        Args:
            claim: The claim text
            evidence: Evidence passages

        Returns:
            True if claim mentions sources or is a factual statement
        """
        # Check for source patterns
        source_patterns = [
            r"(?:Sahih |Al-)?(?:Bukhari|Muslim|Abu Dawud)",
            r"(?:Quran|Qur'an|Al-Quran)",
            r"\[([^\]]+)\]",
            r"\d+:\d+",  # Verse references like 2:255
        ]

        import re

        for pattern in source_patterns:
            if re.search(pattern, claim, re.IGNORECASE):
                return True

        return True  # Always applicable for factual claims

    def _extract_sources(self, claim: str) -> List[str]:
        """Extract source references from claim.

        Args:
            claim: The claim text

        Returns:
            List of extracted source references
        """
        import re

        sources = []

        # Patterns for different source types
        patterns = [
            # Hadith collections
            r"(?:Sahih |Al-)?(?:Bukhari|Muslim|Abu Dawud|Nasai|Ibn Majah|Tirmidhi)",
            # Quran references
            r"(?:Quran|Qur'an|Al-Quran)[\s:]*(\d+:\d+)?",
            # Bracketed citations
            r"\[([^\]]+)\]",
            # General book references
            r"(?:book|chapter|verse)[\s:]*(\d+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, claim, re.IGNORECASE)
            if matches:
                # Handle both single string matches and tuple groups
                for m in matches:
                    if isinstance(m, tuple):
                        sources.extend([x for x in m if x])
                    elif isinstance(m, str) and m:
                        sources.append(m)

        return list(set(sources))

    def _verify_source(
        self,
        source: str,
        evidence: Any,
        evidence_sources: List[str],
    ) -> bool:
        """Verify that a source exists in the evidence.

        Args:
            source: Source reference to verify
            evidence: Evidence passages
            evidence_sources: Known sources from evidence

        Returns:
            True if source is verified
        """
        # Check against known evidence sources
        source_lower = source.lower()

        # If it's a citation marker like [C1], match against it
        if source_lower.startswith("c") and source_lower[1:].isdigit():
            # In our system citations are like C0, C1, etc.
            # Assuming evidence might have this embedded implicitly if it's just index-based
            # But let's check text and metadata
            pass

        for ev_source in evidence_sources:
            if source_lower in ev_source.lower():
                return True

        # Check if source is mentioned in evidence texts or metadata
        if isinstance(evidence, list):
            for i, ev in enumerate(evidence):
                # Auto-approve C-style indexing if numeric matches position
                # E.g. [C1] matches evidence index 0 (if 1-based)
                if source_lower == f"c{i + 1}":
                    return True
                if source_lower == f"c{i}":
                    return True

                if isinstance(ev, dict):
                    text = ev.get("text", "")
                    if source_lower in text.lower():
                        return True

                    # Check metadata
                    metadata = ev.get("metadata", {})
                    if isinstance(metadata, dict):
                        for key in ["book", "source", "author", "id", "chapter"]:
                            val = metadata.get(key)
                            if val and isinstance(val, str) and source_lower.replace("al-", "").strip() in val.lower():
                                return True

        return False


# Default verifier instance
source_attribution_verifier = SourceAttributionVerifier()
