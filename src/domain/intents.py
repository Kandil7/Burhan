"""
Domain intents and classifications for Athar Islamic QA system.

This module defines:
- Intent enum: Supported query intents
- QuranSubIntent: Sub-intents for Quran queries
- INTENT_DESCRIPTIONS: Human-readable descriptions for LLM prompts
- INTENT_ROUTING: Intent → agent/tool routing table
- INTENT_PRIORITY: Priority scores for resolving keyword conflicts
- KEYWORD_PATTERNS: Fast-path keyword matching patterns
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List


class Intent(str, Enum):
    """
    Supported query intents for Athar Islamic QA system.
    """

    FIQH = "fiqh"
    QURAN = "quran"
    ISLAMIC_KNOWLEDGE = "islamic_knowledge"
    HADITH = "hadith"
    TAFSIR = "tafsir"
    AQEEDAH = "aqeedah"
    SEERAH = "seerah"
    USUL_FIQH = "usul_fiqh"
    ISLAMIC_HISTORY = "islamic_history"
    ARABIC_LANGUAGE = "arabic_language"


class QuranSubIntent(str, Enum):
    """
    Sub-intents for Quran queries.

    - verse_lookup: exact verse / surah text retrieval
    - interpretation: tafsir and meaning (RAG)
    - analytics: NL2SQL statistics (count, length, position)
    - quotation_validation: verify whether a text is a real Quran verse
    """

    VERSE_LOOKUP = "verse_lookup"
    INTERPRETATION = "interpretation"
    ANALYTICS = "analytics"
    QUOTATION_VALIDATION = "quotation_validation"


# ============================================================================
# Human-readable descriptions used in LLM classifier prompts
# ============================================================================

INTENT_DESCRIPTIONS: Dict[Intent, str] = {
    Intent.FIQH: ("Islamic jurisprudence (halal/haram, worship, transactions, rulings, fiqh questions)"),
    Intent.QURAN: ("Quranic verses, surahs, tafsir, Quran statistics, or verse lookup"),
    Intent.ISLAMIC_KNOWLEDGE: (
        "General Islamic knowledge (history, biography, theology, concepts) that does not fit a more specific intent"
    ),
    Intent.HADITH: ("Hadith retrieval, authentication, sanad, and matn (Prophetic traditions)"),
    Intent.TAFSIR: ("Quran interpretation and exegesis (Ibn Kathir, Al-Jalalayn, Al-Qurtubi, etc.)"),
    Intent.AQEEDAH: ("Islamic creed and theology (Tawhid, faith, beliefs, theological questions)"),
    Intent.SEERAH: ("Prophet Muhammad's biography and life events (Seerah, prophetic history)"),
    Intent.USUL_FIQH: ("Principles of Islamic jurisprudence (methodology, sources of Islamic law, ijtihad, qiyas)"),
    Intent.ISLAMIC_HISTORY: ("Islamic history and civilization (historical events, figures, dynasties, culture)"),
    Intent.ARABIC_LANGUAGE: (
        "Arabic language: grammar (nahw), morphology (sarf), rhetoric (balaghah), literature, poetry, dictionaries"
    ),
}


# ============================================================================
# Intent → agent/tool routing table
# ============================================================================

INTENT_ROUTING: Dict[Intent, str] = {
    Intent.FIQH: "fiqh_agent",
    Intent.QURAN: "quran_agent",  # further refined by QuranSubIntent
    Intent.ISLAMIC_KNOWLEDGE: "general_islamic_agent",
    Intent.HADITH: "hadith_agent",
    Intent.SEERAH: "seerah_agent",
    # The intents below currently share general_islamic_agent.
    # Dedicated agents will be added in later phases.
    Intent.TAFSIR: "general_islamic_agent",
    Intent.AQEEDAH: "general_islamic_agent",
    Intent.USUL_FIQH: "general_islamic_agent",
    Intent.ISLAMIC_HISTORY: "general_islamic_agent",
    Intent.ARABIC_LANGUAGE: "general_islamic_agent",
}


# ============================================================================
# Priority scores — higher = more specific.
# Used by HybridIntentClassifier to resolve keyword conflicts.
# Note: More specific intents should have HIGHER priority.
# ============================================================================

INTENT_PRIORITY: Dict[Intent, int] = {
    Intent.TAFSIR: 10,  # Most specific Quran intent (tafsir > general quran)
    Intent.QURAN: 9,  # General Quran intent
    Intent.HADITH: 9,
    Intent.SEERAH: 8,
    Intent.AQEEDAH: 8,
    Intent.USUL_FIQH: 8,
    Intent.ARABIC_LANGUAGE: 7,
    Intent.ISLAMIC_HISTORY: 6,
    Intent.FIQH: 5,
    Intent.ISLAMIC_KNOWLEDGE: 1,  # most general — matched last
}


# ============================================================================
# Keyword patterns for fast-path classification.
# NOTE: more specific intents are listed first.
# Keywords are intentionally un-normalised here; normalisation is applied
# at match time inside HybridIntentClassifier._fast_path().
# ============================================================================

KEYWORD_PATTERNS: Dict[Intent, List[str]] = {
    Intent.QURAN: [
        "آية",
        "ايه",
        "سورة",
        "سوره",
        "قرآن",
        "القرآن",
        "القران",
        "ayah",
        "surah",
        "quran",
        "كم عدد آيات",
        "كم عدد ايات",
        "أطول سورة",
        "اطول سوره",
        "آيات سورة",
        "ايات سوره",
        "مكية",
        "مدنية",
    ],
    Intent.HADITH: [
        "حديث",
        "الحديث",
        "hadith",
        "سند",
        "إسناد",
        "اسناد",
        "متن",
        "رواه",
        "رواية",
        "صحيح البخاري",
        "صحيح مسلم",
        "ضعيف",
        "موضوع",
        "حسن",
        "الإسناد",
        "الاسناد",
    ],
    Intent.TAFSIR: [
        "تفسير",
        "tafsir",
        "معنى الآية",
        "معنى الايه",
        "شرح الآية",
        "شرح الايه",
        "تفسير ابن كثير",
        "تفسير الجلالين",
        "تفسير القرطبي",
        "interpretation of verse",
    ],
    Intent.AQEEDAH: [
        "عقيدة",
        "عقيده",
        "aqeedah",
        "توحيد",
        "tawhid",
        "أركان الإيمان",
        "اركان الايمان",
        "الإيمان بالله",
        "الايمان بالله",
        "أسماء الله",
        "اسماء الله الحسنى",
    ],
    Intent.SEERAH: [
        "سيرة",
        "سيره",
        "seerah",
        "sirah",
        "prophet biography",
        "حياة النبي",
        "حياه النبي",
        "السيرة النبوية",
        "السيره النبويه",
        "غزوة",
        "غزوه",
    ],
    Intent.USUL_FIQH: [
        "أصول الفقه",
        "اصول الفقه",
        "usul al-fiqh",
        "الاجتهاد",
        "الاجتهاد",
        "القياس",
        "الإجماع",
        "الاجماع",
        "مصادر التشريع",
        "مصادر الاحكام",
        "النسخ في القرآن",
    ],
    Intent.ISLAMIC_HISTORY: [
        "تاريخ إسلامي",
        "تاريخ اسلامي",
        "islamic history",
        "الدولة الأموية",
        "الدوله الامويه",
        "الدولة العباسية",
        "الدوله العباسيه",
        "الخلفاء الراشدين",
        "الخلفاء الراشدون",
        "الفتوحات الإسلامية",
        "الفتوحاتIslam",
    ],
    Intent.ARABIC_LANGUAGE: [
        "نحو",
        "صرف",
        "بلاغة",
        "بلاغه",
        "arabic grammar",
        "arabic morphology",
        "معنى كلمة",
        "معنى كلمه",
        "قاموس",
        "لسان العرب",
        "إعراب",
        "اعراب",
    ],
    Intent.FIQH: [
        "ما حكم",
        "هل يجوز",
        "هل يجوز",
        "هل هو حلال",
        "هل هو حرام",
        "حكم",
        "فتوى",
        "فتوه",
        "fiqh",
        "halal",
        "haram",
        "islamic law",
        "يحرم",
        "يحل",
        "مباح",
        "مكروه",
    ],
    Intent.ISLAMIC_KNOWLEDGE: [
        "شرح",
        "explain",
        "معلومات عن",
        "اخبرني عن",
        "ما هو",
        "ما هي",
        "من هو",
        "من هي",
        "what is",
        "who is",
        "tell me about",
    ],
}


# ============================================================================
# Helper functions
# ============================================================================


def get_intent_description(intent: Intent) -> str:
    """Return human-readable description for a given intent."""
    return INTENT_DESCRIPTIONS.get(intent, "Unknown intent")


def get_agent_for_intent(intent: Intent) -> str | None:
    """Return the agent/tool name for a given intent, if defined."""
    return INTENT_ROUTING.get(intent)


def is_quran_intent(intent: Intent) -> bool:
    """Return True if the intent is specifically Quran-related."""
    return intent == Intent.QURAN


def all_intents() -> List[Intent]:
    """Convenience: return list of all supported intents."""
    return list(Intent)


def all_quran_sub_intents() -> List[QuranSubIntent]:
    """Convenience: return list of supported Quran sub-intents."""
    return list(QuranSubIntent)
