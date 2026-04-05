"""
Intent definitions and routing configuration for Athar Islamic QA system.

Defines the 9 primary intents based on Fanar-Sadiq architecture,
along with Quran sub-intents and keyword patterns for fast-path classification.
"""

from enum import Enum
from typing import Optional


class Intent(str, Enum):
    """
    Supported query intents for Athar Islamic QA system.

    Based on Fanar-Sadiq hybrid query classifier with 9 primary intents.
    """

    FIQH = "fiqh"
    QURAN = "quran"
    ISLAMIC_KNOWLEDGE = "islamic_knowledge"
    GREETING = "greeting"
    ZAKAT = "zakat"
    INHERITANCE = "inheritance"
    DUA = "dua"
    HIJRI_CALENDAR = "hijri_calendar"
    PRAYER_TIMES = "prayer_times"


class QuranSubIntent(str, Enum):
    """
    Sub-intents for Quran queries.

    Used by Quran router to direct to appropriate pipeline:
    - verse_lookup: Exact verse retrieval (2:255, Ayat al-Kursi, etc.)
    - interpretation: Tafsir and meaning
    - analytics: NL2SQL for statistics (count, length, etc.)
    - quotation_validation: Verify if text is actually a Quran verse
    """

    VERSE_LOOKUP = "verse_lookup"
    INTERPRETATION = "interpretation"
    ANALYTICS = "analytics"
    QUOTATION_VALIDATION = "quotation_validation"


# ==========================================
# Intent descriptions for LLM classifier prompt
# ==========================================
INTENT_DESCRIPTIONS = {
    Intent.FIQH: "Islamic jurisprudence (halal/haram, worship, transactions, rulings, fiqh questions)",
    Intent.QURAN: "Quranic verses, surahs, tafsir, or Quran statistics",
    Intent.ISLAMIC_KNOWLEDGE: "General Islamic knowledge (history, biography, theology, concepts)",
    Intent.GREETING: "Greetings, salutations, polite phrases (As-salamu alaykum, Ramadan Kareem, etc.)",
    Intent.ZAKAT: "Calculate zakat on wealth, gold, silver, trade goods, livestock",
    Intent.INHERITANCE: "Calculate inheritance distribution (fara'id, mirath, estate division)",
    Intent.DUA: "Request specific duas or adhkar (supplications, remembrance, Hisn al-Muslim)",
    Intent.HIJRI_CALENDAR: "Hijri dates, Ramadan dates, Eid dates, Islamic calendar conversion",
    Intent.PRAYER_TIMES: "Prayer times or qibla direction for a location",
}


# ==========================================
# Intent to Agent/Tool mapping
# ==========================================
INTENT_ROUTING = {
    Intent.FIQH: "fiqh_agent",
    Intent.QURAN: "quran_agent",
    Intent.ISLAMIC_KNOWLEDGE: "general_islamic_agent",
    Intent.GREETING: "chatbot_agent",
    Intent.ZAKAT: "zakat_tool",
    Intent.INHERITANCE: "inheritance_tool",
    Intent.DUA: "dua_tool",
    Intent.HIJRI_CALENDAR: "hijri_tool",
    Intent.PRAYER_TIMES: "prayer_tool",
}


# ==========================================
# Keyword patterns for fast-path classification
# ==========================================
# These patterns are checked first before LLM classification.
# If a pattern matches with high confidence (>=0.90), we skip LLM call.
KEYWORD_PATTERNS = {
    Intent.FIQH: [
        "حكم",
        "fiqh",
        "halal",
        "haram",
        "Islamic law",
        "ما حكم",
        "هل يجوز",
        "هل هو حلال",
        "هل هو حرام",
    ],
    Intent.ISLAMIC_KNOWLEDGE: [
        "من هو",
        "ما هو",
        "ما هي",
        "who is",
        "what is",
        "explain",
        "شرح",
        "معلومات عن",
    ],
    Intent.ZAKAT: [
        "زكاة",
        "zakat",
        "زكاة المال",
        "نصاب",
        "زكاة الذهب",
        "zakat calculator",
    ],
    Intent.INHERITANCE: [
        "ميراث",
        "inheritance",
        "تركة",
        "فرائض",
        "عصبة",
        "inheritance calculator",
        "توزيع الميراث",
    ],
    Intent.QURAN: [
        "آية",
        "سورة",
        "قرآن",
        "ayah",
        "surah",
        "quran",
        "تفسير",
        "كم عدد آيات",
        "أطول سورة",
    ],
    Intent.PRAYER_TIMES: [
        "prayer times",
        "مواقيت الصلاة",
        "وقت الصلاة",
        "qibla direction",
        "قبلة",
    ],
    Intent.HIJRI_CALENDAR: [
        "هجري",
        "hijri",
        "رمضان",
        "eid",
        "عيد",
        "تاريخ",
        "hijri date",
        "متى رمضان",
    ],
    Intent.DUA: [
        "دعاء",
        "dua",
        "ذكر",
        "adhkar",
        "أذكار",
        "استغفار",
        "دعاء الصباح",
        "hisn al-muslim",
    ],
    Intent.GREETING: [
        "سلام",
        "السلام عليكم",
        "hello",
        "hi",
        "مرحبا",
        "assalamu alaikum",
        "ramadan kareem",
        "عيد مبارك",
    ],
}


# ==========================================
# Helper functions
# ==========================================
def get_intent_description(intent: Intent) -> str:
    """Get description for an intent."""
    return INTENT_DESCRIPTIONS.get(intent, "Unknown intent")


def get_agent_for_intent(intent: Intent) -> Optional[str]:
    """Get the agent/tool name for an intent."""
    return INTENT_ROUTING.get(intent)


def is_quran_intent(intent: Intent) -> bool:
    """Check if intent is related to Quran."""
    return intent == Intent.QURAN
