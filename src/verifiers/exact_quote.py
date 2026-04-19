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
        """Verify that every quote in *claim* is grounded in *evidence*.

        Args:
            claim:    The answer text that may contain quoted passages.
            evidence: List of passage dicts (must have a ``content`` key).
            context:  Optional dict; ``source_type`` key accepted.

        Returns:
            VerificationResult — passed=False + failed_quotes list when any
            quote is ungrounded, so the auto-healing layer can act on it.
        """
        quotes = self.detector.extract_quote_content(claim)

        if not quotes:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=True,
                confidence=1.0,
                message="No quotes found in claim",
            )

        source_type = (
            context.get("source_type", "general") if context else "general"
        )

        failed_quotes: List[str] = []
        passed_quotes: List[str] = []

        for quote in quotes:
            if await self._quote_in_evidence(quote, evidence):
                passed_quotes.append(quote)
            else:
                failed_quotes.append(quote)

        if failed_quotes:
            return VerificationResult(
                verifier_type=self.verifier_type,
                passed=False,
                confidence=0.8,
                message=f"Quotes not found in evidence: {failed_quotes}",
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

    def is_applicable(self, claim: str, evidence: Any) -> bool:
        """Return True if *claim* contains any quoted segments."""
        return len(self.detector.extract_quote_content(claim)) > 0

    # ── Core matching ────────────────────────────────────────────────────────

    async def _quote_in_evidence(
        self,
        quote: str,
        evidence: Any,
    ) -> bool:
        """Return True only if *quote* is found verbatim in evidence passages.

        Intentionally does NOT fall back to Quran corpus validation.
        Ungrounded Quranic quotes are handled by the auto-healing layer
        in CollectionAgent after this verifier flags them as failed.
        """
        if not evidence:
            return False

        # Normalise evidence to list[dict] with a ``content`` key
        passages: List[str] = []
        if isinstance(evidence, list):
            for e in evidence:
                if isinstance(e, dict):
                    # Use ``content`` (canonical field); fall back to ``text``
                    passages.append(e.get("content", e.get("text", "")))
                else:
                    passages.append(str(e))
        elif isinstance(evidence, dict):
            passages = [evidence.get("content", evidence.get("text", ""))]
        else:
            passages = [str(evidence)]

        quote_norm = self._normalize(quote)
        for text in passages:
            if quote_norm in self._normalize(text):
                return True

        return False

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
                    validator = (
                        self._quran_validator
                        or QuotationValidator(session=session)
                    )
                    new_loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(new_loop)
                        result = new_loop.run_until_complete(
                            validator.validate(quote)
                        )
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