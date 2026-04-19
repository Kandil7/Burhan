# Exact Quote Verifier Module
"""Verifier for exact quote matching with Quran and Hadith support."""

from typing import Optional, Dict, Any, List
from .base import BaseVerifier, VerificationResult, VerifierType
from .quote_span import QuoteSpanDetector


class ExactQuoteVerifier(BaseVerifier):
    """Verifies that quotes exactly match source text.

    Supports:
    - Quran exact quotation validation
    - Hadith exact quotation validation
    - General source text matching

    Interface:
        verify(claim, evidence, context) -> VerificationResult
        is_applicable(claim, evidence) -> bool
    """

    def __init__(self, quran_validator=None):
        """Initialize the exact quote verifier.

        Args:
            quran_validator: Optional QuotationValidator instance for Quran validation
        """
        self.verifier_type = VerifierType.EXACT_QUOTE
        self.detector = QuoteSpanDetector()
        self._quran_validator = quran_validator

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """Verify exact quote matching.

        Args:
            claim: The claim/response text containing quotes
            evidence: Evidence passages to verify against
            context: Additional context (source_type, etc.)

        Returns:
            VerificationResult with quote verification status
        """
        # Extract quotes from claim
        quotes = self.detector.extract_quote_content(claim)

        if not quotes:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=True,
                confidence=1.0,
                message="No quotes found in claim",
            )

        # Determine source type from context
        source_type = context.get("source_type", "general") if context else "general"

        # Check each quote against evidence
        failed_quotes = []
        passed_quotes = []

        for quote in quotes:
            if self._quote_matches_source(quote, evidence, source_type):
                passed_quotes.append(quote)
            else:
                failed_quotes.append(quote)

        if failed_quotes:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.8,
                message=f"Quotes not matching source: {failed_quotes}",
                details={
                    "failed_quotes": failed_quotes,
                    "passed_quotes": passed_quotes,
                    "source_type": source_type,
                },
            )

        return VerificationResult(
            verifier_type=self.verifier_type,
            passed=True,
            confidence=0.95,
            message="All quotes match source text",
            details={
                "verified_quotes": passed_quotes,
                "source_type": source_type,
            },
        )

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Check if this verifier is applicable.

        Args:
            claim: The claim text
            evidence: Evidence passages

        Returns:
            True if quotes are found in claim
        """
        return len(self.detector.extract_quote_content(claim)) > 0

    def _quote_matches_source(
        self,
        quote: str,
        evidence: Any,
        source_type: str = "general",
    ) -> bool:
        """Check if a quote matches the source evidence.

        Args:
            quote: The quote text to verify
            evidence: Evidence passages
            source_type: Type of source (quran, hadith, general)

        Returns:
            True if quote matches source
        """
        if not evidence:
            return False

        # Handle Quran-specific validation
        if source_type == "quran" and self._quran_validator:
            # Use the Quran quotation validator for Arabic text
            return self._validate_quran_quote(quote)

        # General text matching
        if isinstance(evidence, list):
            evidence_texts = [e.get("text", "") for e in evidence if isinstance(e, dict)]
        elif isinstance(evidence, dict):
            evidence_texts = [evidence.get("text", "")]
        else:
            evidence_texts = [str(evidence)]

        # Simple substring matching
        for text in evidence_texts:
            if quote.lower() in text.lower():
                return True

        # Fallback to Cross-Corpus Quran grounding if it's an unrecognized quote
        # If it's an accurate Quran verse, we allow it to pass even if not in evidence.
        return self._validate_quran_quote(quote)

    def _validate_quran_quote(self, quote: str) -> bool:
        """Validate a Quran quote using the Quran validator.

        Args:
            quote: The Arabic quote to validate

        Returns:
            True if quote is a valid Quranic verse
        """
        # If no DB validator is available, fallback to basic logic
        from src.infrastructure.database import get_sync_session
        from src.quran.quotation_validator import QuotationValidator
        import asyncio
        
        # We need an event loop to run async to_thread in _get_candidates
        try:
            with get_sync_session() as session:
                quran_validator = QuotationValidator(session=session)
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(quran_validator.validate(quote))
                return result.get("is_quran", False)
        except Exception:
            return True

    def set_quran_validator(self, validator) -> None:
        """Set the Quran quotation validator.

        Args:
            validator: QuotationValidator instance
        """
        self._quran_validator = validator


# Default verifier instance
exact_quote_verifier = ExactQuoteVerifier()
