from __future__ import annotations

from typing import Any

from src.domain.intents import Intent


class IntentRouter:
    """
    Routes queries to agents based on intent classification.

    This is the canonical routing component for the v2 architecture.
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
        Intent.ISLAMIC_TAZKIYAH: "tazkiyah",          # ⬅ جديد
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
        """
        query_lower = query.lower()

        # Check for greeting
        greeting_keywords = ["سلام", "مرحبا", "hello", "assalam", "اهلا"]
        if any(kw in query_lower for kw in greeting_keywords):
            return Intent.GREETING

        # Check for fiqh
        fiqh_keywords = ["حكم", "حلال", "حرام", "فرض", "فتوى", "فتوه", "فقه"]
        if any(kw in query_lower for kw in fiqh_keywords):
            return Intent.FIQH

        # Check for hadith
        hadith_keywords = ["حديث", "الحديث", "صحيح", "ضعيف", "سنن", "بخاري", "مسلم"]
        if any(kw in query_lower for kw in hadith_keywords):
            return Intent.HADITH

        # Check for tafsir
        tafsir_keywords = ["آية", "ايه", "تفسير", "قرآن", "القرآن", "القران", "سورة", "سوره"]
        if any(kw in query_lower for kw in tafsir_keywords):
            return Intent.TAFSIR

        # Check for aqeedah
        aqeedah_keywords = ["توحيد", "عقيدة", "عقيده", "إيمان", "ايمان", "الإيمان بالله", "الايمان بالله"]
        if any(kw in query_lower for kw in aqeedah_keywords):
            return Intent.AQEEDAH

        # Check for tazkiyah / spirituality
        tazkiyah_keywords = [
            "تزكية",
            "تزكيه",
            "تربية إيمانية",
            "تربيه ايمانية",
            "السلوك",
            "السلوك إلى الله",
            "التصوف",
            "التصوّف",
            "الأحوال القلبية",
            "احوال قلبيه",
            "مقامات السالكين",
            "منازل السائرين",
            "مدارج السالكين",
            "ابن القيم",
            "ابن تيمية",
            "الذوق",
            "الوجد",
            "الفناء",
            "الجمع",
        ]
        if any(kw in query_lower for kw in tazkiyah_keywords):
            return Intent.ISLAMIC_TAZKIYAH

        # Check for seerah
        seerah_keywords = ["سيرة", "سيره", "نبوية", "رسول", "النبي", "السيرة النبوية", "السيره النبويه"]
        if any(kw in query_lower for kw in seerah_keywords):
            return Intent.SEERAH

        # Check for usul_fiqh
        usul_keywords = ["أصول الفقه", "اصول الفقه", "أصول", "اجتهاد", "قياس", "استنباط"]
        if any(kw in query_lower for kw in usul_keywords):
            return Intent.USUL_FIQH

        # Check for history
        history_keywords = ["تاريخ", "خلافة", "دولة", "حكم"]
        if any(kw in query_lower for kw in history_keywords):
            return Intent.ISLAMIC_HISTORY

        # Check for language
        lang_keywords = ["نحو", "صرف", "بلاغة", "بلاغه", "إعراب", "اعراب"]
        if any(kw in query_lower for kw in lang_keywords):
            return Intent.ARABIC_LANGUAGE

        # Default to general Islamic knowledge
        return Intent.ISLAMIC_KNOWLEDGE

    def route_to_agent(self, intent: Intent) -> str:
        """Get agent name for intent."""
        return self.INTENT_TO_AGENT.get(intent, "general")

    async def route(self, query: str) -> tuple[Intent, str]:
        """Full routing: classify and get agent."""
        intent = await self.classify(query)
        agent = self.route_to_agent(intent)
        return intent, agent


_router: IntentRouter | None = None


def get_intent_router() -> IntentRouter:
    """Get the global intent router instance."""
    global _router
    if _router is None:
        _router = IntentRouter()
    return _router