"""
Router Agent for Athar Islamic QA system.

Thin orchestration layer between the HTTP/LangGraph entry point
and the IntentClassifier.

Responsibilities:
1. Call the classifier (injected via DI — swappable implementation)
2. Apply confidence gating (low-confidence queries → fallback intent)
3. Build the final route string via _build_route()
4. Return a RoutingDecision with agent metadata

Does NOT perform I/O — pure coordination logic.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.domain.intents import INTENT_ROUTING, Intent, QuranSubIntent
from src.domain.models import ClassificationResult
from src.application.interfaces import IntentClassifier, Router
from src.application.models import RoutingDecision

logger = logging.getLogger(__name__)


# ============================================================================
# Route construction
# ============================================================================


def _build_route(
    intent: Intent,
    sub: Optional[QuranSubIntent],
) -> str:
    """
    Translate intent (+ optional Quran sub-intent) into a concrete route string.

    Route strings are consumed by the orchestration layer (LangGraph / FastAPI)
    to dispatch to the correct agent or tool.
    """
    if intent is Intent.QURAN and sub is not None:
        _quran_routes = {
            QuranSubIntent.VERSE_LOOKUP: "quran:verse_lookup",
            QuranSubIntent.ANALYTICS: "quran:nl2sql",
            QuranSubIntent.QUOTATION_VALIDATION: "quran:quote_validation",
            QuranSubIntent.INTERPRETATION: "quran:interpretation_rag",
        }
        return _quran_routes.get(sub, "quran:interpretation_rag")

    return INTENT_ROUTING[intent]


def _build_agent_metadata(result: ClassificationResult) -> Dict[str, Any]:
    """
    Build optional metadata dictionary passed alongside the RoutingDecision.

    Downstream agents can use this for system-prompt tuning,
    retrieval filter selection, or response formatting hints.
    """
    meta: Dict[str, Any] = {
        "language": result.language,
        "requires_retrieval": result.requires_retrieval,
        "confidence": result.confidence,
        "classification_method": result.method,
    }
    if result.quran_subintent:
        meta["quran_subintent"] = result.quran_subintent.value
    if result.subquestions:
        meta["subquestions"] = result.subquestions
    return meta


# ============================================================================
# RouterAgent
# ============================================================================


class RouterAgent(Router):
    """
    Thin orchestration layer between the HTTP/LangGraph entry point
    and the IntentClassifier.

    Responsibilities:
    1. Call the classifier (injected via DI — swappable implementation)
    2. Apply confidence gating (low-confidence queries → fallback intent)
    3. Build the final route string via _build_route()
    4. Return a RoutingDecision with agent metadata

    Does NOT perform I/O — pure coordination logic.
    """

    DEFAULT_CONF_THRESHOLD = 0.55
    DEFAULT_FALLBACK_INTENT = Intent.ISLAMIC_KNOWLEDGE

    def __init__(
        self,
        classifier: IntentClassifier,
        conf_threshold: float = DEFAULT_CONF_THRESHOLD,
        fallback_intent: Intent = DEFAULT_FALLBACK_INTENT,
    ) -> None:
        """
        Initialize the router with a classifier.

        Args:
            classifier: IntentClassifier implementation (e.g., HybridIntentClassifier)
            conf_threshold: Minimum confidence threshold (default: 0.55)
            fallback_intent: Intent to use when confidence is below threshold
        """
        self._classifier = classifier
        self._conf_threshold = conf_threshold
        self._fallback_intent = fallback_intent

    async def route(self, query: str) -> RoutingDecision:
        """
        Classify query and resolve to a RoutingDecision.

        If confidence is below the threshold, the intent is overridden
        with fallback_intent (default: ISLAMIC_KNOWLEDGE) and a warning
        is logged.
        """
        result: ClassificationResult = await self._classifier.classify(query)

        if result.confidence < self._conf_threshold:
            logger.warning(
                "router.low_confidence",
                extra={
                    "original_intent": result.intent.value,
                    "confidence": result.confidence,
                    "fallback": self._fallback_intent.value,
                },
            )
            result = ClassificationResult(
                intent=self._fallback_intent,
                confidence=result.confidence,
                language=result.language,
                reasoning=(
                    f"Low confidence ({result.confidence:.2f}) on "
                    f"'{result.intent.value}' → overridden to "
                    f"'{self._fallback_intent.value}'"
                ),
                requires_retrieval=True,
                method=result.method,
                quran_subintent=None,
                subquestions=result.subquestions,
            )

        route = _build_route(result.intent, result.quran_subintent)
        metadata = _build_agent_metadata(result)

        logger.info(
            "router.decision",
            extra={
                "intent": result.intent.value,
                "route": route,
                "confidence": result.confidence,
                "method": result.method,
                "language": result.language,
            },
        )

        return RoutingDecision(
            result=result,
            route=route,
            agent_metadata=metadata,
        )

    async def close(self) -> None:
        """Clean up classifier resources."""
        if hasattr(self._classifier, "close"):
            await self._classifier.close()
