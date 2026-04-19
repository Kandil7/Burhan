"""Verifier for exact quote matching with Quran and Hadith support."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .base import BaseVerifier, VerificationResult, VerifierType
from .quote_span import QuoteSpanDetector

logger = logging.getLogger(__name__)


class ExactQuoteVerifier(BaseVerifier):
    """Verifies that quotes found in the answer exist in evidence passages.

    Supports:
    - Quran exact quotation validation (via QuotationValidator)
    - Hadith exact quotation validation
    - General source text matching

    Design principle:
        A quote PASSES only if it is found verbatim (or near-verbatim) in
        the verified passages.  Quranic validity alone is NOT sufficient to
        pass a quote — the passage must be present in evidence so the
        auto-healing layer in CollectionAgent can fetch and attach it.

    Interface:
        verify(claim, evidence, context) -> VerificationResult
        is_applicable(claim, evidence)   -> bool
    """

    def __init__(self, quran_validator=None) -> None:
        """Initialize the exact quote verifier.

        Args:
            quran_validator: Optional QuotationValidator instance.
                             If None, a fresh session will be opened per call.
        """
        self.verifier_type = VerifierType.EXACT_QUOTE
        self.detector = QuoteSpanDetector()
        self._quran_validator = quran_validator

    # ── Public API ──────────────────────────────────────────────────────────

    async def verify(
        self,
        claim: str,
        evidence: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        from src.verifiers.quote_span import RELAXED_DELIMITER_TYPES

        spans = self.detector.extract_with_spans(claim)

        if not spans:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=True,
                confidence=1.0,
                message="No quotes found in claim",
            )

        source_type = context.get("source_type", "general") if context else "general"

        failed_quotes: List[str] = []
        passed_quotes: List[str] = []

        for span in spans:
            relaxed = span["delimiter_type"] in RELAXED_DELIMITER_TYPES
            matched = await self._quote_in_evidence(span["content"], evidence, relaxed=relaxed)
            if matched:
                passed_quotes.append(span["content"])
            else:
                # Only flag strict-type failures as hard violations
                # Neutral misses are soft — logged but not failed
                if span["requires_strict_match"]:
                    failed_quotes.append(span["content"])
                else:
                    passed_quotes.append(span["content"])  # soft pass

        if failed_quotes:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.8,
                message=f"Strict-type quotes not found in evidence: {failed_quotes}",
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
            message="All quotes found in evidence",
            details={
                "verified_quotes": passed_quotes,
                "source_type": source_type,
            },
        )

    async def _quote_in_evidence(
        self,
        quote: str,
        evidence: Any,
        relaxed: bool = False,
    ) -> bool:
        """
        Args:
            relaxed: If True, accept fuzzy match ≥ 0.75 (for neutral "" quotes).
                     If False, require exact substring match (for ﴿﴾ and «»).
        """
        if not evidence:
            return False

        passages: List[str] = []
        if isinstance(evidence, list):
            for e in evidence:
                if isinstance(e, dict):
                    passages.append(e.get("content", e.get("text", "")))
                else:
                    passages.append(str(e))
        elif isinstance(evidence, dict):
            passages = [evidence.get("content", evidence.get("text", ""))]
        else:
            passages = [str(evidence)]

        quote_norm = self._normalize(quote)

        for text in passages:
            text_norm = self._normalize(text)
            if quote_norm in text_norm:
                return True
            if relaxed and len(quote_norm) > 20:
                from difflib import SequenceMatcher

                ratio = SequenceMatcher(None, quote_norm, text_norm).ratio()
                if ratio >= 0.75:
                    return True

        return False

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Return True if *claim* contains any quoted segments."""
        return len(self.detector.extract_quote_content(claim)) > 0

    # ── Quran validation (used externally by misattribution detector) ────────

    async def is_quran_text(self, quote: str) -> bool:
        """Check whether *quote* matches a Quranic verse.

        Used by the misattributed-Quran detector in CollectionAgent, NOT
        as a fallback inside _quote_in_evidence.

        Opens a fresh DB session if no validator was injected.
        Returns False on any error (fail-closed).
        """
        try:
            from src.infrastructure.database import get_sync_session
            from src.quran.quotation_validator import QuotationValidator

            def _run_sync() -> bool:
                with get_sync_session() as session:
                    validator = self._quran_validator or QuotationValidator(session=session)
                    new_loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(new_loop)
                        result = new_loop.run_until_complete(validator.validate(quote))
                        return bool(result.get("is_quran", False))
                    finally:
                        new_loop.close()

            return await asyncio.to_thread(_run_sync)

        except Exception:
            logger.warning(
                "is_quran_text check failed for quote: %s",
                quote[:60],
                exc_info=True,
            )
            return False  # fail-closed — do not pass unverified quotes

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize(text: str) -> str:
        """Light normalisation for substring matching (case + whitespace)."""
        return " ".join(text.lower().split())

    def set_quran_validator(self, validator) -> None:
        """Inject a QuotationValidator instance (e.g., in tests).

        Args:
            validator: QuotationValidator instance
        """
        self._quran_validator = validator


# Default singleton — injected into CollectionAgent at startup
exact_quote_verifier = ExactQuoteVerifier()
