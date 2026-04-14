"""
Intent definitions and routing configuration for Athar Islamic QA system.

Defines the 15 primary intents inspired by the Fanar-Sadiq architecture,
along with Quran sub-intents, agent routing, and keyword patterns for
fast-path classification before LLM or embedding-based routing.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional


class Intent(str, Enum):
    """
    Supported query intents for Athar Islamic QA system.

    Based on a hybrid query classifier similar to Fanar-Sadiq, with
    specialized handlers for fiqh, Quran, hadith, dua, calculators,
    and general Islamic knowledge.[web:2][web:27]
    """

    # Core intents
    FIQH = "fiqh"
    QURAN = "quran"
    ISLAMIC_KNOWLEDGE = "islamic_knowledge"
    # GREETING = "greeting"
    # ZAKAT = "zakat"
    # INHERITANCE = "inheritance"
    # DUA = "dua"
    # HIJRI_CALENDAR = "hijri_calendar"
    # PRAYER_TIMES = "prayer_times"

    # Specialized knowledge agents
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

    Used by the Quran router to direct to appropriate pipelines:

    - verse_lookup: Exact verse retrieval (e.g., 2:255, Ayat al-Kursi)
    - interpretation: Tafsir and meaning
    - analytics: NL2SQL-like statistics (count, length, position, etc.)
    - quotation_validation: Verify if text is actually a Quran verse
    """

    VERSE_LOOKUP = "verse_lookup"
    INTERPRETATION = "interpretation"
    ANALYTICS = "analytics"
    QUOTATION_VALIDATION = "quotation_validation"


# ============================================================================
# Intent descriptions for LLM classifier prompt
# ============================================================================

INTENT_DESCRIPTIONS: Dict[Intent, str] = {
    Intent.FIQH: (
        "Islamic jurisprudence (halal/haram, worship, transactions, "
        "rulings, fiqh questions)"
    ),
    Intent.QURAN: "Quranic verses, surahs, tafsir, or Quran statistics",
    Intent.ISLAMIC_KNOWLEDGE: (
        "General Islamic knowledge (history, biography, theology, concepts)"
    ),
    # Intent.GREETING: (
    #     "Greetings, salutations, polite phrases "
    #     "(As-salamu alaykum, Ramadan Kareem, etc.)"
    # ),
    # Intent.ZAKAT: "Calculate zakat on wealth, gold, silver, trade goods, livestock",
    # Intent.INHERITANCE: (
    #     "Calculate inheritance distribution (fara'id, mirath, estate division)"
    # ),
    # Intent.DUA: (
    #     "Request specific duas or adhkar (supplications, remembrance, "
    #     "Hisn al-Muslim)"
    # ),
    # Intent.HIJRI_CALENDAR: (
    #     "Hijri dates, Ramadan dates, Eid dates, Islamic calendar conversion"
    # ),
    # Intent.PRAYER_TIMES: "Prayer times or qibla direction for a location",

    # Specialized intents
    Intent.HADITH: "Hadith retrieval, authentication, sanad, and matn (Prophetic traditions)",
    Intent.TAFSIR: (
        "Quran interpretation and exegesis (Ibn Kathir, Al-Jalalayn, Al-Qurtubi, etc.)"
    ),
    Intent.AQEEDAH: (
        "Islamic creed and theology (Tawhid, faith, beliefs, theological questions)"
    ),
    Intent.SEERAH: (
        "Prophet Muhammad's biography and life events (Seerah, prophetic history)"
    ),
    Intent.USUL_FIQH: (
        "Principles of Islamic jurisprudence (methodology, sources of Islamic law)"
    ),
    Intent.ISLAMIC_HISTORY: (
        "Islamic history and civilization (historical events, figures, culture)"
    ),
    Intent.ARABIC_LANGUAGE: (
        "Arabic language: grammar (nahw), morphology (sarf), rhetoric (balaghah), "
        "literature, poetry, dictionaries"
    ),
}


# ============================================================================
# Intent → Agent/Tool routing
# ============================================================================

INTENT_ROUTING: Dict[Intent, str] = {
    Intent.FIQH: "fiqh_agent",
    Intent.QURAN: "quran_agent",
    Intent.ISLAMIC_KNOWLEDGE: "general_islamic_agent",
    # Intent.GREETING: "chatbot_agent",
    # Intent.ZAKAT: "zakat_tool",
    # Intent.INHERITANCE: "inheritance_tool",
    # Intent.DUA: "dua_tool",
    # Intent.HIJRI_CALENDAR: "hijri_tool",
    # Intent.PRAYER_TIMES: "prayer_tool",

    # Active specialized agents
    Intent.HADITH: "hadith_agent",
    Intent.SEERAH: "seerah_agent",

    # These intents currently fall back to general_islamic_agent.
    # Dedicated agents were removed as orphans but the intents are kept
    # so the classifier can still be precise at the semantic level.
    Intent.TAFSIR: "general_islamic_agent",
    Intent.AQEEDAH: "general_islamic_agent",
    Intent.USUL_FIQH: "general_islamic_agent",
    Intent.ISLAMIC_HISTORY: "general_islamic_agent",
    Intent.ARABIC_LANGUAGE: "general_islamic_agent",
}


# ============================================================================
# Keyword patterns for fast-path classification
# These are checked before LLM/embedding routing.
# Order matters: more specific intents first.
# ============================================================================

KEYWORD_PATTERNS: Dict[Intent, List[str]] = {
    # Specific intents (checked first)
    # Intent.ZAKAT: [
    #     "زكاة",
    #     "zakat",
    #     "نصاب",
    #     "zakat calculator",
    # ],
    # Intent.INHERITANCE: [
    #     "ميراث",
    #     "inheritance",
    #     "تركة",
    #     "فرائض",
    #     "عصبة",
    #     "توزيع الميراث",
    # ],
    Intent.QURAN: [
        "آية",
        "سورة",
        "قرآن",
        "ayah",
        "surah",
        "quran",
        "كم عدد آيات",
        "أطول سورة",
    ],
    # Intent.PRAYER_TIMES: [
    #     "prayer times",
    #     "مواقيت الصلاة",
    #     "وقت الصلاة",
    #     "وقت صلاة",
    #     "qibla",
    #     "قبلة",
    # ],
    # Intent.HIJRI_CALENDAR: [
    #     "هجري",
    #     "hijri",
    #     "رمضان",
    #     "eid",
    #     "عيد",
    #     "hijri date",
    #     "متى رمضان",
    # ],
    # Intent.DUA: [
    #     "دعاء",
    #     "dua",
    #     "أذكار",
    #     "adhkar",
    #     "استغفار",
    #     "دعاء الصباح",
    #     "hisn al-muslim",
    # ],
    # Intent.GREETING: [
    #     "سلام",
    #     "السلام عليكم",
    #     "hello",
    #     "hi",
    #     "مرحبا",
    #     "assalamu alaikum",
    #     "ramadan kareem",
    #     "عيد مبارك",
    # ],
    Intent.HADITH: [
        "حديث",
        "hadith",
        "سند",
        "متن",
        "رواه",
        "صحيح",
        "ضعيف",
        "الإسناد",
    ],
    Intent.TAFSIR: [
        "تفسير",
        "tafsir",
        "معنى الآية",
        "شرح الآية",
        "تفسير ابن كثير",
    ],
    Intent.AQEEDAH: [
        "عقيدة",
        "توحيد",
        "aqeedah",
        "tawhid",
        "أركان الإيمان",
    ],
    Intent.SEERAH: [
        "سيرة",
        "seerah",
        "prophet biography",
        "حياة النبي",
        "السيرة النبوية",
    ],
    Intent.USUL_FIQH: [
        "أصول الفقه",
        "usul al-fiqh",
        "الاجتهاد",
        "القياس",
        "الإجماع",
        "مصادر التشريع",
    ],
    Intent.ISLAMIC_HISTORY: [
        "تاريخ إسلامي",
        "islamic history",
        "الدولة الأموية",
        "الدولة العباسية",
        "الخلفاء الراشدين",
    ],
    Intent.ARABIC_LANGUAGE: [
        "نحو",
        "صرف",
        "بلاغة",
        "arabic grammar",
        "معنى كلمة",
        "قاموس",
    ],

    # Broad intents (checked last)
    Intent.FIQH: [
        "ما حكم",
        "هل يجوز",
        "هل هو حلال",
        "هل هو حرام",
        "fiqh",
        "halal",
        "haram",
        "Islamic law",
    ],
    Intent.ISLAMIC_KNOWLEDGE: [
        "شرح",
        "معلومات عن",
        "explain",
    ],
}


# ============================================================================
# Helper functions
# ============================================================================

def get_intent_description(intent: Intent) -> str:
    """Return human-readable description for a given intent."""
    return INTENT_DESCRIPTIONS.get(intent, "Unknown intent")


def get_agent_for_intent(intent: Intent) -> Optional[str]:
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