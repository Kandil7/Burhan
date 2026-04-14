"""
Intent definitions and routing configuration for Athar Islamic QA system.

Defines the 9 primary intents based on Fanar-Sadiq architecture,
along with Quran sub-intents and keyword patterns for fast-path classification.
"""

from enum import Enum


class Intent(str, Enum):
    """
    Supported query intents for Athar Islamic QA system.

    Based on Fanar-Sadiq hybrid query classifier with 15 primary intents.
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

    # NEW: Specialized agents
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
    # NEW intents
    Intent.HADITH: "Hadith retrieval, authentication, sanad, and matn (Prophetic traditions)",
    Intent.TAFSIR: "Quran interpretation and exegesis (Ibn Kathir, Al-Jalalayn, Al-Qurtubi)",
    Intent.AQEEDAH: "Islamic creed and theology (Tawhid, faith, beliefs, theological questions)",
    Intent.SEERAH: "Prophet Muhammad's biography and life events (Seerah, prophetic history)",
    Intent.USUL_FIQH: "Principles of Islamic jurisprudence (methodology, sources of Islamic law)",
    Intent.ISLAMIC_HISTORY: "Islamic history and civilization (historical events, figures, culture)",
    Intent.ARABIC_LANGUAGE: (
        "Arabic language: grammar (nahw), morphology (sarf), rhetoric (balaghah), "
        "literature, poetry, dictionaries"
    ),
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
    # Active specialized agents
    Intent.HADITH: "hadith_agent",
    Intent.SEERAH: "seerah_agent",
    # NOTE: tafsir, aqeedah, usul_fiqh, islamic_history, arabic_language agents
    # were deleted as orphan files. These intents will fall back to general_islamic_agent.
    Intent.TAFSIR: "general_islamic_agent",
    Intent.AQEEDAH: "general_islamic_agent",
    Intent.USUL_FIQH: "general_islamic_agent",
    Intent.ISLAMIC_HISTORY: "general_islamic_agent",
    Intent.ARABIC_LANGUAGE: "general_islamic_agent",
}


# ==========================================
# Keyword patterns for fast-path classification
# ==========================================
# These patterns are checked first before LLM classification.
# If a pattern matches with high confidence (>=0.90), we skip LLM call.
# NOTE: Order matters - more specific intents should come before broad ones.
KEYWORD_PATTERNS = {
    # Specific intents (checked first)
    Intent.ZAKAT: [
        "زكاة",
        "zakat",
        "نصاب",
        "zakat calculator",
    ],
    Intent.INHERITANCE: [
        "ميراث",
        "inheritance",
        "تركة",
        "فرائض",
        "عصبة",
        "توزيع الميراث",
    ],
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
    Intent.PRAYER_TIMES: [
        "prayer times",
        "مواقيت الصلاة",
        "وقت الصلاة",
        "وقت صلاة",
        "qibla",
        "قبلة",
    ],
    Intent.HIJRI_CALENDAR: [
        "هجري",
        "hijri",
        "رمضان",
        "eid",
        "عيد",
        "hijri date",
        "متى رمضان",
    ],
    Intent.DUA: [
        "دعاء",
        "dua",
        "أذكار",
        "adhkar",
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


# ==========================================
# Helper functions
# ==========================================
def get_intent_description(intent: Intent) -> str:
    """Get description for an intent."""
    return INTENT_DESCRIPTIONS.get(intent, "Unknown intent")


def get_agent_for_intent(intent: Intent) -> str | None:
    """Get the agent/tool name for an intent."""
    return INTENT_ROUTING.get(intent)


def is_quran_intent(intent: Intent) -> bool:
    """Check if intent is related to Quran."""
    return intent == Intent.QURAN
