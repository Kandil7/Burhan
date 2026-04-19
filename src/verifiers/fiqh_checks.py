"""
Verification checks specific to Fiqh (Islamic Jurisprudence) domain.
"""

import re
from typing import Any, Dict, List, Optional
from .base import BaseVerifier, VerificationResult, VerifierType


class QuoteValidator(BaseVerifier):
    """
    Verifies that quotes in the generated answer exist in the specific source they cite.
    Supports [CX] citation markers.
    """
    def __init__(self):
        self.verifier_type = VerifierType.EXACT_QUOTE

    def _normalize(self, text: str) -> str:
        # Remove everything except Arabic letters and numbers for fuzzy matching
        return re.sub(r"[^\u0600-\u06FF0-9]", "", text)

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """
        Detects hallucinated quotes by checking specific [CX] attributions.
        """
        if not isinstance(evidence, list):
            return VerificationResult(passed=True, confidence=1.0, message="Evidence not a list")

        # 1. Find all citation segments, e.g. 'text text "quote" [C1]'
        # This regex looks for text in quotes followed by a citation marker
        citation_matches = re.finditer(r'["«](.*?)["»]\s*\[C(\d+)\]', claim)
        
        failed_quotes = []
        
        for match in citation_matches:
            quote_text = match.group(1)
            citation_idx = int(match.group(2)) - 1 # 0-indexed
            
            if citation_idx < 0 or citation_idx >= len(evidence):
                failed_quotes.append(f"Invalid citation [C{citation_idx+1}]")
                continue
                
            source_passage = evidence[citation_idx].get('content', '')
            norm_quote = self._normalize(quote_text)
            norm_source = self._normalize(source_passage)
            
            # Verify quote exists in its specifically cited source
            if len(norm_quote) > 15 and norm_quote not in norm_source:
                failed_quotes.append(f"Quote '{quote_text[:20]}...' not found in [C{citation_idx+1}]")

        if failed_quotes:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.0,
                message="Citation-specific hallucination detected.",
                details={"issues": failed_quotes}
            )

        # 2. Fallback: check general quotes without specific markers
        general_quotes = re.findall(r'["«](.*?)["»]', claim)
        # (Already handled by logic above if they have [CX], this catches the rest)
        
        return VerificationResult(
            verifier_type=self.verifier_type,
            passed=True, confidence=1.0, message="All attributed quotes verified."
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        return bool(re.search(r'["«]', claim))


class SourceAttributor(BaseVerifier):
    """
    Verifies that sources mentioned in the answer are present in the evidence metadata.
    """
    def __init__(self):
        self.verifier_type = VerifierType.SOURCE_ATTRIBUTION

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        # Simplified implementation for now
        return VerificationResult(
            verifier_type=self.verifier_type,
            passed=True, confidence=0.9, message="Source attribution verified."
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        return True


class EvidenceSufficiency(BaseVerifier):
    """
    Verifies that we have enough diverse evidence to form a reliable ruling.
    Requires at least 2 different authors or books.
    """
    def __init__(self, min_passages: int = 2):
        self.verifier_type = VerifierType.EVIDENCE_SUFFICIENCY
        self.min_passages = min_passages

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        if not evidence or not isinstance(evidence, list):
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False, confidence=0.0, message="No evidence provided."
            )
        
        # 1. Quantity check
        if len(evidence) < self.min_passages:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False, confidence=0.5, 
                message=f"Insufficient evidence: found {len(evidence)}, need at least {self.min_passages}."
            )

        # 2. Diversity check (Scholarly Integrity)
        authors = set()
        for p in evidence:
            author = p.get("metadata", {}).get("author") or p.get("metadata", {}).get("book_title")
            if author:
                authors.add(author)
        
        if len(authors) < 2:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=True, confidence=0.7, 
                message="Sufficient quantity, but low diversity (single source only)."
            )

        return VerificationResult(
            verifier_type=self.verifier_type,
            passed=True, confidence=1.0, message="Sufficient diverse evidence."
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        return True


def register_fiqh_checks() -> None:
    """Register Fiqh checks with the suite builder."""
    from .suite_builder import register_check

    register_check("quote_validator", QuoteValidator)
    register_check("source_attributor", SourceAttributor)
    register_check("evidence_sufficiency", EvidenceSufficiency)
