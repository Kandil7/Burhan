"""
Classifier Factory for Athar Islamic QA system.

Returns the correct IntentClassifier based on CLASSIFIER_BACKEND setting.

┌──────────────────────┬───────────────────────────────────────────────────┐
│ CLASSIFIER_BACKEND   │ What you get                                      │
├──────────────────────┼───────────────────────────────────────────────────┤
│ hybrid  (default)    │ HybridIntentClassifier                            │
│                      │ • Zero external dependencies                      │
│                      │ • Keyword fast-path + Jaccard fallback    │
│                      │ • Ideal for dev / offline environments    │
├──────────────────────┼───────────────────────────────────────────────────┤
│ llm                  │ LLMIntentClassifier                           │
│                      │ • Requires OPENAI_API_KEY                 │
│                      │ • Works with any OpenAI-compatible API  │
│                      │ • Silent fallback to ISLAMIC_KNOWLEDGE│
├──────────────────────┼───────────────────────────────────────────────────┤
│ chain                │ FallbackChainClassifier                     │
│                      │ • LLM primary (raises on error)          │
│                      │ • HybridIntentClassifier fallback      │
│                      │ • Best for production: accuracy +     │
│                      │   reliability                      │
└──────────────────────┴───────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.application.hybrid_classifier import HybridIntentClassifier
from src.application.interfaces import IntentClassifier
from src.domain.models import ClassificationResult

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ============================================================================
# FallbackChainClassifier
# ============================================================================


class FallbackChainClassifier(IntentClassifier):
    """
    Tries `primary` first; on any unhandled exception falls back to `secondary`.

    Typical use:  LLMIntentClassifier (primary)  →  HybridIntentClassifier (fallback)

    Guarantees:
    • The primary must be configured with raise_on_error=True so that failures
      propagate here instead of being silently swallowed inside the primary.
    • Fallback is always HybridIntentClassifier — pure in-process, never fails.
    • The returned ClassificationResult.method is preserved from whichever
      classifier succeeded, so downstream logging shows the actual path taken.
    """

    def __init__(
        self,
        primary: IntentClassifier,
        fallback: IntentClassifier,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    async def classify(self, query: str) -> ClassificationResult:
        """Try primary, fall back to secondary on error."""
        try:
            result = await self._primary.classify(query)
            logger.debug(
                "chain_classifier.primary_ok",
                extra={"method": result.method, "intent": result.intent.value},
            )
            return result
        except Exception as exc:
            logger.warning(
                "chain_classifier.primary_failed_using_fallback",
                exc_info=exc,
                extra={"fallback": type(self._fallback).__name__},
            )
            return await self._fallback.classify(query)

    async def close(self) -> None:
        """Clean up both classifiers."""
        if hasattr(self._primary, "close"):
            await self._primary.close()
        if hasattr(self._fallback, "close"):
            await self._fallback.close()


# ============================================================================
# Factory
# ============================================================================


def build_classifier() -> IntentClassifier:
    """
    Returns the correct IntentClassifier based on CLASSIFIER_BACKEND setting.

    LLM infrastructure imports are deferred: openai package is NOT imported
    when backend=hybrid, keeping startup fast and dependency-free.
    """
    from src.config.settings import Settings

    # Get settings instance to check backend
    settings = Settings()
    backend = settings.classifier_backend
    logger.info("classifier_factory.build", extra={"backend": backend.value})

    # ── hybrid ────────────────────────────────────────────────────────────
    if backend.value == "hybrid":
        return HybridIntentClassifier(
            low_conf_threshold=settings.low_conf_threshold,
        )

    # ── llm | chain ─────────────────────────────────────────────────
    if backend.value in ("llm", "chain"):
        try:
            # Deferred import: openai is only required for LLM backends
            from src.infrastructure.llm.llm_classifier import LLMIntentClassifier
            from src.infrastructure.llm.openai_client import build_openai_client

            client = build_openai_client()

            llm = LLMIntentClassifier(
                client=client,
                model=settings.openai_model,  # Use openai_model from settings
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                # raise_on_error=True so FallbackChainClassifier catches the exception
                raise_on_error=(backend.value == "chain"),
            )

            if backend.value == "chain":
                hybrid_fallback = HybridIntentClassifier(
                    low_conf_threshold=settings.low_conf_threshold,
                )
                return FallbackChainClassifier(
                    primary=llm,
                    fallback=hybrid_fallback,
                )

            return llm
        except ImportError as e:
            logger.warning(
                "classifier_factory.openai_not_installed",
                extra={"error": str(e), "falling_back": "hybrid"},
            )
            # Fall back to hybrid if openai not installed
            return HybridIntentClassifier(
                low_conf_threshold=settings.low_conf_threshold,
            )

    raise ValueError(f"Unknown classifier backend: {backend!r}")
