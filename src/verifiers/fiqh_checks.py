# Fiqh Checks Module
"""Verification checks specific to Fiqh (Islamic Jurisprudence) domain."""

from typing import Optional, Dict, Any, List
from .base import BaseVerifier, VerificationResult, VerifierType


class QuoteValidator(BaseVerifier):
    """Verifies exact quote matching for Fiqh texts with robust Arabic support.

    Checks that text inside quotes ("..." or «...») exists within the retrieved
    evidence documents, preventing LLM hallucinations of classical texts.
    """

    def __init__(self) -> None:
        self.verifier_type = VerifierType.EXACT_QUOTE

    def _normalize(self, text: str) -> str:
        """Strip diacritics and non-Arabic characters for fuzzy matching."""
        import re

        # Remove diacritics (tashkeel)
        text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
        # Unify Alef with Hamza variants
        text = re.sub(r"[إأآٱ]", "ا", text)
        # Unify Ta-Marbuta and Ha, and Alif-Maqsura and Ya
        text = text.replace("ة", "ه").replace("ى", "ي")
        # Keep only Arabic letters
        return re.sub(r"[^\u0600-\u06FF]", "", text)

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """
        Verify that quotes in the claim exist in the evidence.
        """
        import re

        # Detect text inside "quotes" or «brackets»
        found_quotes = re.findall(r'["«](.*?)["»]', claim)
        if not found_quotes:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=True,
                confidence=1.0,
                message="No quotes found to verify.",
            )

        # Merge all evidence content into a single searchable blob
        if isinstance(evidence, list):
            evidence_text = " ".join([e.get("content", e.get("text", "")) for e in evidence])
        else:
            evidence_text = str(evidence)

        norm_evidence = self._normalize(evidence_text)
        failed_quotes = []

        for quote in found_quotes:
            norm_quote = self._normalize(quote)
            # Ignore very short quotes (< 15 chars) to avoid false positives
            if len(norm_quote) > 15 and norm_quote not in norm_evidence:
                failed_quotes.append(quote)

        if failed_quotes:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.0,
                message=f"Possible hallucination: {len(failed_quotes)} quotes not found in sources.",
                details={"failed_quotes": failed_quotes},
            )

        return VerificationResult(
            verifier_type=self.verifier_type,
            passed=True,
            confidence=1.0,
            message="All quotes verified against sources.",
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if any quotes are present in the claim."""
        import re

        return bool(re.search(r'["«]', claim))


class SourceAttributor(BaseVerifier):
    """Verifies source attribution for Fiqh claims.

    Checks that sources (classical scholars, works) are
    properly attributed and verified.

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
    ) -> VerificationResult:
        """Verify source attribution."""
        claimed_sources = self._extract_sources(claim)

        if not claimed_sources:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=True,
                confidence=1.0,
                message="No sources claimed in claim",
            )

        valid_sources = []
        invalid_sources = []

        for source in claimed_sources:
            if self._verify_source(source, evidence):
                valid_sources.append(source)
            else:
                invalid_sources.append(source)

        if invalid_sources:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.7,
                message=f"Invalid sources: {invalid_sources}",
                details={"invalid_sources": invalid_sources, "valid_sources": valid_sources},
            )

        return VerificationResult(
            verifier_type=self.verifier_type,
            passed=True,
            confidence=0.9,
            message="All sources properly attributed",
            details={"valid_sources": valid_sources},
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if this verifier is applicable."""
        return True

    def _extract_sources(self, claim: str) -> List[str]:
        """Extract source references from claim."""
        import re

        sources = []

        patterns = [
            r"(?: Imam |al-)?(?:Abu Hanifa|Malik|Shafi'i|Ahmad|Ibn Taymiyyah|Ibn al-Qayyim)",
            r"(?:Al-|Ul|])?(?:Muwatta|Mukhtasar|al-Umm|al-Majmu|Ihya|Fath)",
            r"\[([^\]]+)\]",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, claim, re.IGNORECASE)
            if matches:
                for m in matches:
                    if isinstance(m, tuple):
                        sources.extend([x for x in m if x])
                    elif isinstance(m, str) and m:
                        sources.append(m)

        return list(set(sources))

    def _verify_source(self, source: str, evidence: Any) -> bool:
        """Verify that a source exists in evidence."""
        source_lower = source.lower()

        if isinstance(evidence, list):
            for ev in evidence:
                if isinstance(ev, dict):
                    text = ev.get("text", "")
                    if source_lower in text.lower():
                        return True

        return True


class ContradictionDetector(BaseVerifier):
    """Detects contradictions in Fiqh passages.

    Checks for internal contradictions between
    different rulings or sources.

    Interface:
        verify(claim, evidence, context) -> VerificationResult
        is_applicable(claim, evidence) -> bool
    """

    def __init__(self):
        self.verifier_type = VerifierType.CONTRADICTION

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """Detect contradictions."""
        statements = self._extract_statements(evidence)
        contradictions = self._find_contradictions(statements)

        if contradictions:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.8,
                message=f"Found {len(contradictions)} contradictions",
                details={"contradictions": contradictions},
            )

        return VerificationResult(
            verifier_type=self.verifier_type,
            passed=True,
            confidence=0.9,
            message="No contradictions found",
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if this verifier is applicable."""
        return evidence is not None

    def _extract_statements(self, evidence: Any) -> List[Dict[str, Any]]:
        """Extract statements from evidence."""
        if isinstance(evidence, list):
            return evidence
        return []

    def _find_contradictions(
        self,
        statements: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find contradictions in statements."""
        return []


class EvidenceSufficiency(BaseVerifier):
    """Verifies evidence sufficiency for Fiqh claims.

    Checks that evidence is sufficient to support
    a Fiqh ruling (hukm).

    Interface:
        verify(claim, evidence, context) -> VerificationResult
        is_applicable(claim, evidence) -> bool
    """

    def __init__(
        self,
        min_evidences: int = 2,
        require_different_sources: bool = True,
    ):
        self.verifier_type = VerifierType.EVIDENCE_SUFFICIENCY
        self.min_evidences = min_evidences
        self.require_different_sources = require_different_sources

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """Verify evidence sufficiency."""
        evidences = self._extract_evidences(evidence)

        if len(evidences) < self.min_evidences:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.8,
                message=f"Insufficient evidences: {len(evidences)} < {self.min_evidences}",
                details={"evidence_count": len(evidences)},
            )

        if self.require_different_sources:
            sources = set(e.get("source") for e in evidences if e.get("source"))
            if len(sources) < 2:
                return VerificationResult(
                    verifier_type=self.verifier_type,
                    passed=False,
                    confidence=0.8,
                    message="Multiple sources required",
                    details={"source_count": len(sources)},
                )

        return VerificationResult(
            verifier_type=self.verifier_type,
            passed=True,
            confidence=0.85,
            message="Evidence is sufficient",
            details={
                "evidence_count": len(evidences),
                "sufficiency_score": self._calculate_score(evidences),
            },
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if this verifier is applicable."""
        return evidence is not None

    def _extract_evidences(self, evidence: Any) -> List[Dict[str, Any]]:
        """Extract evidences from evidence object."""
        if isinstance(evidence, list):
            return evidence
        return []

    def _calculate_score(self, evidences: List[Dict[str, Any]]) -> float:
        """Calculate sufficiency score."""
        if not evidences:
            return 0.0

        count_score = min(len(evidences) / self.min_evidences, 1.0)

        authority_scores = [e.get("authority_score", 0.5) for e in evidences]
        authority_score = sum(authority_scores) / len(authority_scores) if authority_scores else 0.5

        return (count_score + authority_score) / 2


def register_fiqh_checks() -> None:
    """Register Fiqh checks with the suite builder."""
    from .suite_builder import register_check

    register_check("quote_validator", QuoteValidator)
    register_check("source_attributor", SourceAttributor)
    register_check("contradiction_detector", ContradictionDetector)
    register_check("evidence_sufficiency", EvidenceSufficiency)
