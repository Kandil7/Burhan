"""
Intent Router for Athar Islamic QA system.

Routes user queries to appropriate agents based on intent classification.
"""

from __future__ import annotations

from typing import Any

from src.domain.intents import Intent


class IntentRouter:
    """
    Routes queries to agents based on intent classification.

    This is the canonical routing component for the v2 architecture.

    Usage:
        router = IntentRouter()
        intent = await router.classify("ما حكم الصيام في رمضان؟")
        agent = router.route_to_agent(intent)
    """

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
        Intent.ISLAMIC_KNOWLEDGE: "general",
        Intent.GREETING: "chatbot",
    }

    def __init__(self):
        """Initialize the intent router."""
        self._routing_enabled = True

    async def classify(self, query: str) -> Intent:
        """
        Classify query to intent.

        Note: This is a simplified implementation. The actual classification
        should use the hybrid classifier from classifier_factory.py.

        Args:
            query: User query

        Returns:
            Intent enum value
        """
        # Simplified keyword-based routing
        # In production, this would call the classifier
        query_lower = query.lower()

        # Check for greeting
        greeting_keywords = ["سلام", "مرحبا", "hello", "assalam", "اهلا"]
        if any(kw in query_lower for kw in greeting_keywords):
            return Intent.GREETING

        # Check for fiqh
        fiqh_keywords = ["حكم", "حلال", "حرام", "فرض", "فتوى", "فقه"]
        if any(kw in query_lower for kw in fiqh_keywords):
            return Intent.FIQH

        # Check for hadith
        hadith_keywords = ["حديث", "صحيح", "ضعيف", "سنن", "بخاري", "مسلم"]
        if any(kw in query_lower for kw in hadith_keywords):
            return Intent.HADITH

        # Check for tafsir
        tafsir_keywords = ["آية", "تفسير", "قرآن", "سورة"]
        if any(kw in query_lower for kw in tafsir_keywords):
            return Intent.TAFSIR

        # Check for aqeedah
        aqeedah_keywords = ["توحيد", "عقيدة", "إيمان", "الله"]
        if any(kw in query_lower for kw in aqeedah_keywords):
            return Intent.AQEEDAH

        # Check for seerah
        seerah_keywords = ["سيرة", "نبوية", "رسول", "النبي"]
        if any(kw in query_lower for kw in seerah_keywords):
            return Intent.SEERAH

        # Check for usul_fiqh
        usul_keywords = ["أصول", "اجتهاد", "قياس", "استنباط"]
        if any(kw in query_lower for kw in usul_keywords):
            return Intent.USUL_FIQH

        # Check for history
        history_keywords = ["تاريخ", "خلافة", "دولة", "حكم"]
        if any(kw in query_lower for kw in history_keywords):
            return Intent.ISLAMIC_HISTORY

        # Check for language
        lang_keywords = ["نحو", "صرف", "بلاغة", "إعراب"]
        if any(kw in query_lower for kw in lang_keywords):
            return Intent.ARABIC_LANGUAGE

        # Default to general Islamic knowledge
        return Intent.ISLAMIC_KNOWLEDGE

    def route_to_agent(self, intent: Intent) -> str:
        """
        Get agent name for intent.

        Args:
            intent: Classified intent

        Returns:
            Agent name string
        """
        return self.INTENT_TO_AGENT.get(intent, "general")

    async def route(self, query: str) -> tuple[Intent, str]:
        """
        Full routing: classify and get agent.

        Args:
            query: User query

        Returns:
            Tuple of (Intent, agent_name)
        """
        intent = await self.classify(query)
        agent = self.route_to_agent(intent)
        return intent, agent


# Singleton instance
_router: IntentRouter | None = None


def get_intent_router() -> IntentRouter:
    """Get the global intent router instance."""
    global _router
    if _router is None:
        _router = IntentRouter()
    return _router


__all__ = ["IntentRouter", "get_intent_router"]
