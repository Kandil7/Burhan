"""
Intent Router for Athar Islamic QA System.

Routes queries to agents based on intent classification.
Uses the canonical KeywordBasedClassifier from classifier_factory.py.

This is a simplified router that delegates classification to the hybrid classifier.
For production, use the full MasterHybridClassifier via build_classifier().
"""

from __future__ import annotations

from src.domain.intents import Intent
from src.application.router.classifier_factory import (
    KeywordBasedClassifier,
    normalize_arabic,
)


# Intent to agent mapping
INTENT_TO_AGENT: dict[Intent, str] = {
    Intent.FIQH: "fiqh",
    Intent.QURAN: "tafsir",
    Intent.HADITH: "hadith",
    Intent.SEERAH: "seerah",
    Intent.TAFSIR: "tafsir",
    Intent.AQEEDAH: "aqeedah",
    Intent.USUL_FIQH: "usul_fiqh",
    Intent.ISLAMIC_HISTORY: "history",
    Intent.ARABIC_LANGUAGE: "language",
    Intent.ISLAMIC_TAZKIYAH: "tazkiyah",
    Intent.ISLAMIC_KNOWLEDGE: "general",
    Intent.GREETING: "chatbot",
    Intent.ZAKAT: "chatbot",
    Intent.INHERITANCE: "chatbot",
    Intent.DUAS: "chatbot",
    Intent.PRAYER_TIMES: "chatbot",
    Intent.HIJRI_CALENDAR: "chatbot",
}


class IntentRouter:
    """
    Routes queries to agents based on intent classification.

    Uses KeywordBasedClassifier for fast, accurate keyword-based classification.
    This is the v2 canonical routing component.
    """

    def __init__(self):
        """Initialize the intent router with keyword classifier."""
        self._classifier = KeywordBasedClassifier()
        self._routing_enabled = True

    async def classify(self, query: str) -> Intent:
        """
        Classify query to intent using keyword-based classification.

        Args:
            query: User query string

        Returns:
            Intent: The classified intent
        """
        if not query or not query.strip():
            return Intent.ISLAMIC_KNOWLEDGE

        result = await self._classifier.classify(query)
        return result.intent

    def route_to_agent(self, intent: Intent) -> str:
        """
        Get agent name for an intent.

        Args:
            intent: The intent to route

        Returns:
            str: Agent name
        """
        return INTENT_TO_AGENT.get(intent, "general")

    async def route(self, query: str) -> tuple[Intent, str]:
        """
        Full routing: classify query and get agent.

        Args:
            query: User query string

        Returns:
            tuple: (intent, agent_name)
        """
        intent = await self.classify(query)
        agent = self.route_to_agent(intent)
        return intent, agent


# Global singleton instance
_router: IntentRouter | None = None


def get_intent_router() -> IntentRouter:
    """Get the global intent router instance."""
    global _router
    if _router is None:
        _router = IntentRouter()
    return _router


__all__ = [
    "IntentRouter",
    "get_intent_router",
    "INTENT_TO_AGENT",
]
