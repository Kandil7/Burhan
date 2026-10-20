"""
Domain intents and classifications for Burhan Islamic QA system.

This module defines:
- Intent enum: Supported query intents
- QuranSubIntent: Sub-intents for Quran queries
- INTENT_DESCRIPTIONS: Human-readable descriptions for LLM prompts
- INTENT_ROUTING: Intent → agent/tool routing table
- INTENT_PRIORITY: Priority scores for resolving keyword conflicts
- KEYWORD_PATTERNS: Fast-path keyword matching patterns
"""

from __future__ import annotations

import re
from enum import Enum


class Intent(str, Enum):
    """
    Supported query intents for Burhan Islamic QA system.
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
    ISLAMIC_TAZKIYAH = "islamic_tazkiyah"  # ⬅ جديد
    # Additional intents for specific tools and queries
    ZAKAT = "zakat"
    INHERITANCE = "inheritance"
    GREETING = "greeting"
    DUAS = "duas"
    PRAYER_TIMES = "prayer_times"
    HIJRI_CALENDAR = "hijri_calendar"


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


INTENT_DESCRIPTIONS: dict[Intent, str] = {
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
    Intent.ISLAMIC_TAZKIYAH: (  # ⬅ جديد
        "Tazkiyah and spiritual development (tasawwuf, suluk, hearts, manners, Ibn al-Qayyim, Madarij al-Salikin)"
    ),
    # Additional intents for specific tools
    Intent.ZAKAT: ("Zakat calculation and rulings (zakat al-fitr, niacin, wealth)"),
    Intent.INHERITANCE: ("Islamic inheritance distribution and rulings"),
    Intent.GREETING: ("Greetings and salam exchanges"),
    Intent.DUAS: ("Islamic supplications and duas"),
    Intent.PRAYER_TIMES: ("Prayer times calculation and schedules"),
    Intent.HIJRI_CALENDAR: ("Hijri calendar conversion and dates"),
}


# ============================================================================
# Intent → agent/tool routing table (Epic 6 - Collection-aware)
# ============================================================================


INTENT_ROUTING: dict[Intent, str] = {
    Intent.FIQH: "fiqh_agent",
    Intent.QURAN: "tafsir_agent",  # Tafsir handles Quran interpretation
    Intent.ISLAMIC_KNOWLEDGE: "general_islamic_agent",
    Intent.HADITH: "hadith_agent",
    Intent.SEERAH: "seerah_agent",
    Intent.TAFSIR: "tafsir_agent",  # Dedicated tafsir agent (Epic 6)
    Intent.AQEEDAH: "aqeedah_agent",  # Dedicated aqeedah agent (Epic 6)
    Intent.USUL_FIQH: "usul_fiqh_agent",  # Dedicated usul_fiqh agent (Epic 6)
    Intent.ISLAMIC_HISTORY: "history_agent",  # Dedicated history agent (Epic 6)
    Intent.ARABIC_LANGUAGE: "language_agent",  # Dedicated language agent (Epic 6)
    Intent.ISLAMIC_TAZKIYAH: "tazkiyah_agent",  # ⬅ جديد
    # Tool intents route to their concrete tool names, which the registry
    # registers in src/core/registry.py. A generic "tool_agent" never existed.
    Intent.ZAKAT: "zakat_tool",
    Intent.INHERITANCE: "inheritance_tool",
    Intent.GREETING: "chatbot_agent",
    Intent.DUAS: "dua_tool",
    Intent.PRAYER_TIMES: "prayer_tool",
    Intent.HIJRI_CALENDAR: "hijri_tool",
}


# ============================================================================
# Priority scores — higher = more specific.
# Used by the keyword classifier only to break ties when two intents match
# the same number of keywords. Keyword count decides first.
# Note: More specific intents should have HIGHER priority.
# ============================================================================


INTENT_PRIORITY: dict[Intent, int] = {
    Intent.TAFSIR: 10,  # Most specific Quran intent (tafsir > general quran)
    Intent.QURAN: 9,  # General Quran intent
    Intent.HADITH: 9,
    Intent.SEERAH: 8,
    Intent.AQEEDAH: 8,
    Intent.USUL_FIQH: 8,
    Intent.ISLAMIC_TAZKIYAH: 8,  # ⬅ جديد
    Intent.ARABIC_LANGUAGE: 7,
    Intent.ISLAMIC_HISTORY: 6,
    # Tool intents that name a concrete request. They outrank FIQH when the
    # match count ties, so "وقت صلاة المغرب" resolves to prayer times while
    # "ما حكم صيام رمضان؟" stays FIQH on a higher keyword count.
    Intent.PRAYER_TIMES: 6,
    Intent.HIJRI_CALENDAR: 6,
    Intent.ZAKAT: 6,
    Intent.INHERITANCE: 6,
    Intent.DUAS: 6,
    Intent.FIQH: 5,
    Intent.GREETING: 9,  # A greeting is unambiguous and must win outright
    Intent.ISLAMIC_KNOWLEDGE: 1,  # most general — matched last
}


# ============================================================================
# Arabic Text Normalization
# ============================================================================

_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
_LATIN_RE = re.compile(r"[a-zA-Z]")


def normalize_arabic(text: str) -> str:
    """Robust Arabic text normalization for keyword matching."""
    if not text:
        return ""
    # Strip diacritics (tashkeel)
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    # Unify Alef variants
    text = re.sub(r"[إأآٱ]", "ا", text)
    # Unify Ta-Marbuta and Ya
    text = text.replace("ة", "ه").replace("ى", "ي")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def detect_language(text: str) -> str:
    """Detect whether text is primarily Arabic, English, or mixed.

    Text counts as "mixed" when both scripts appear in meaningful
    proportion. A single Latin product name inside an Arabic question does
    not make the whole query mixed.
    """
    ar = len(_ARABIC_RE.findall(text))
    en = len(_LATIN_RE.findall(text))
    if ar == 0 and en == 0:
        return "ar"  # default for empty / numeric queries
    if ar == 0:
        return "en"
    if en == 0:
        return "ar"
    minority = min(ar, en)
    majority = max(ar, en)
    if minority / majority >= 0.2:
        return "mixed"
    return "ar" if ar > en else "en"


# ============================================================================
# Keyword patterns for fast-path classification.
# This is the SINGLE SOURCE OF TRUTH for classification keywords.
# ============================================================================

KEYWORD_PATTERNS: dict[Intent, list[str]] = {
    Intent.FIQH: [
        "صلاة",
        "صلاه",
        "صوم",
        "صيام",
        "زكاة",
        "زكاه",
        "حج",
        "عمرة",
        "طهارة",
        "طهاره",
        "وضوء",
        "غسل",
        "جنابة",
        "حكم",
        "يجوز",
        "حلال",
        "حرام",
        "فتوى",
        "واجب",
        "سنة",
        "مستحب",
        "مكروه",
        "مباح",
        "نفل",
        "قربة",
        "بيع",
        "شراء",
        "ربا",
        "قرض",
        "إجارة",
        "شركة",
        "وكالة",
        "رهن",
        "شفعة",
        "طلاق",
        "نكاح",
        "زواج",
        "عدة",
        "متعة",
        "نفقة",
        "حدود",
        "قذف",
        "سرقة",
        "عبادات",
        "معاملات",
        "فقه",
        "مذهب",
        "حنفية",
        "مالكية",
        "شافعيه",
        "حنبلية",
        # English jurisprudence terms
        "halal",
        "haram",
        "fiqh",
        "ruling",
        "permissible",
        "forbidden",
        "islamic law",
    ],
    Intent.HADITH: [
        "حديث",
        "الحديث",
        "رواه",
        "اخرجه",
        "اسناد",
        "سند",
        "متن",
        "صحيح",
        "ضعيف",
        "حسن",
        "موضوع",
        "كذب",
        "شاذ",
        "منكر",
        "مختلف فيه",
        "بخاري",
        "مسلم",
        "ترمذي",
        "نسائي",
        "ابن ماجه",
        "ابو داود",
        "الدارمي",
        "البلاذري",
        "البيهقي",
        "ابن حيان",
        "ابن خزيمة",
        "الطبراني",
        # English hadith terms
        "hadith",
        "sanad",
        "isnad",
        "narration",
        "narrated",
    ],
    Intent.TAFSIR: [
        "تفسير",
        "تاويل",
        "الاية",
        "الايه",
        "ابن كثير",
        "جلالين",
        "قرطبي",
        "طبري",
        "السمعاني",
        "البيضاوي",
        "الزاملي",
        "الكاشف",
        "المنار",
        "الفيومي",
        # English exegesis terms
        "tafsir",
        "exegesis",
    ],
    Intent.QURAN: [
        "آية",
        "اية",
        "سورة",
        "سوره",
        "قرآن",
        "القرآن",
        "القران",
        "مصحف",
        "تلاوة",
        "تجويد",
        "ايات",
        "الايات",
        "ختمة",
        "حفظ",
        "قوله",
        "قوله تعالى",
        "كتاب الله",
        # English Quran terms
        "quran",
        "quranic",
        "surah",
        "ayah",
        "verse",
    ],
    Intent.AQEEDAH: [
        "عقيدة",
        "عقيده",
        "توحيد",
        "شرك",
        "كفر",
        "نفاق",
        "إيمان",
        "ايمان",
        "اسماء الله",
        "صفات الله",
        "يوم الاخر",
        "ملائكة",
        "قدر",
        "قضاء",
        "جنة",
        "نار",
        "جحيم",
        "عذاب",
        "ثواب",
        "الأسماء الحسنى",
        "التوحيد",
        "المعرفة",
        "الإله",
        "الرب",
        "الألوهية",
    ],
    Intent.SEERAH: [
        "سيرة",
        "سيره",
        "السيرة",
        "السيرة النبوية",
        "السيره النبويه",
        "النبي",
        "الرسول",
        "محمد",
        "صلى الله عليه وسلم",
        "صلي الله عليه",
        "غزوة",
        "غزوه",
        "غزوات",
        "هجرة",
        "هجره",
        "الهجرة النبوية",
        "بدر",
        "أحد",
        "الخندق",
        "فتح مكة",
        "تبوك",
        "خيبر",
        "طائف",
        "صحابة",
        "الصحابة",
        "خلفاء",
        "أبي بكر",
        "عمر",
        "عثمان",
        "علي",
        "خالد",
        "عمر بن الخطاب",
        "ابي بكر",
        "مكة",
        "المدينة",
        "المدينه",
        "مكة المكرمة",
        "طيبة",
        "ولادة",
        "بعثة",
        "وفاة",
        "هدي",
        "السنة",
        "السنه",
        "السنة النبوية",
        "السنه النبويه",
        "تطبيق",
        "اقتداء",
        "قدوة",
        "أخلاق",
        "خُلُق",
        "خُلق",
        "character",
        "morals",
        "behavior",
        "نبوية",
        "نبوي",
        "القديم",
        "حياة",
        "سيرة نبوية",
        "عبر",
        "دروس",
    ],
    Intent.USUL_FIQH: [
        "أصول الفقه",
        "اصول الفقه",
        "أصول",
        "اجتهاد",
        "قياس",
        "استنباط",
        "اجماع",
        "قاعدة فقهية",
        "القياس",
        "الاستنباط",
        "الاجماع",
        "التراجيح",
        "الاولويات",
        "المصالح",
        "المرسلات",
    ],
    Intent.ISLAMIC_HISTORY: [
        "تاريخ",
        "دولة",
        "خلافة",
        "فتح",
        "معركة",
        "حضارة",
        "اموي",
        "عباسي",
        "عثماني",
        "فاطمي",
        "سلجوقي",
        "مملوكي",
        "الخلافة",
        "الفتوحات",
        "الحروب",
        "المرحلة",
        "العهد",
    ],
    Intent.ARABIC_LANGUAGE: [
        "نحو",
        "صرف",
        "بلاغة",
        "بلاغه",
        "إعراب",
        "اعراب",
        "لغة",
        "عربي",
        "كلمة",
        "معنى كلمة",
        "المعنى",
        "المرادف",
        "الاضداد",
        "صفة",
        "اسم",
        "فعل",
        "حرف",
        "مصدر",
        "مشتق",
        "بناء",
        "مرفوع",
        "منصوب",
        "مجرور",
        "مفعول",
    ],
    Intent.ISLAMIC_TAZKIYAH: [
        "تزكية",
        "تزكيه",
        "تربية",
        "تربيه",
        "سلوك",
        "السلوك",
        "تصوف",
        "تصوّف",
        "روحانية",
        "قلوب",
        "قلب",
        "مقامات",
        "منازل",
        "مدارج",
        "سالكين",
        "عابد",
        "زاهد",
        "ابن القيم",
        "الغزالي",
        "ابن عربي",
        "الجيلاني",
    ],
    Intent.GREETING: ["سلام", "السلام", "مرحبا", "أهلا", "حياك", "الله يبارك"],
    Intent.ZAKAT: ["زكاة", "زكاه", "حساب الزكاة", "زكاة المال", "نصاب", "فطر"],
    Intent.INHERITANCE: ["ميراث", "فرائض", "تقسيم", "ورثة", "إرث", "تركة"],
    Intent.DUAS: ["دعاء", "ادعية", "الدعاء", "تضرع", "طلب", "إجابة"],
    Intent.PRAYER_TIMES: ["مواقيت", "وقت", "وقت الصلاة"],
    Intent.HIJRI_CALENDAR: ["هجري", "ميلادي", "التقويم", "الشهر", "السنة الهجرية", "رمضان"],
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


def all_intents() -> list[Intent]:
    """Convenience: return list of all supported intents."""
    return list(Intent)


def all_quran_sub_intents() -> list[QuranSubIntent]:
    """Convenience: return list of supported Quran sub-intents."""
    return list(QuranSubIntent)


# ============================================================================
# Quran sub-intent and retrieval heuristics
# ============================================================================

# Ordered most-specific first. The first pattern that matches wins.
_QURAN_SUBINTENT_PATTERNS: list[tuple[QuranSubIntent, list[str]]] = [
    (
        QuranSubIntent.QUOTATION_VALIDATION,
        ["هل هذه آية", "تصحيح", "تحقق", "صحة الآية", "is this a verse", "verify verse"],
    ),
    (
        QuranSubIntent.ANALYTICS,
        [
            "كم عدد",
            "عدد آيات",
            "عدد كلمات",
            "اطول سورة",
            "أطول سورة",
            "اقصر سورة",
            "أقصر سورة",
            "how many",
            "verse count",
            "طول السورة",
        ],
    ),
    (
        QuranSubIntent.VERSE_LOOKUP,
        [
            "اقرأ",
            "اكتب",
            "آية الكرسي",
            "اية الكرسي",
            "نص الآية",
            "ما نص",
            "read verse",
            "verse text",
        ],
    ),
    (
        QuranSubIntent.INTERPRETATION,
        ["تفسير", "معنى", "يفسر", "tafsir", "meaning of", "explain verse"],
    ),
]

# Sub-intents whose answers come from databases or LLM knowledge, not RAG.
_NON_RETRIEVAL_SUBINTENTS = {
    QuranSubIntent.VERSE_LOOKUP,
    QuranSubIntent.ANALYTICS,
    QuranSubIntent.QUOTATION_VALIDATION,
}


def classify_quran_subintent(query: str) -> tuple[QuranSubIntent, float]:
    """Classify a Quran query into a sub-intent.

    Returns:
        Tuple of sub-intent and a confidence in the range 0.0 to 1.0.
    """
    normalized = normalize_arabic(query or "")
    for sub_intent, patterns in _QURAN_SUBINTENT_PATTERNS:
        for pattern in patterns:
            if normalize_arabic(pattern) in normalized:
                return sub_intent, 0.8
    return QuranSubIntent.INTERPRETATION, 0.4


def infer_requires_retrieval(
    intent: Intent,
    sub_intent: QuranSubIntent | None = None,
) -> bool:
    """Decide whether answering the query needs document retrieval.

    Greetings never need retrieval. Quran lookup, analytics, and quotation
    validation are answered from structured sources instead of RAG.
    """
    if intent == Intent.GREETING:
        return False
    if intent == Intent.QURAN and sub_intent in _NON_RETRIEVAL_SUBINTENTS:
        return False
    return True


# Route suffix for each Quran sub-intent. RouterAgent composes these into
# "quran:<suffix>" routes documented on RoutingDecision.
QURAN_SUBINTENT_ROUTES: dict[QuranSubIntent, str] = {
    QuranSubIntent.VERSE_LOOKUP: "quran:verse_lookup",
    QuranSubIntent.ANALYTICS: "quran:nl2sql",
    QuranSubIntent.INTERPRETATION: "quran:interpretation_rag",
    QuranSubIntent.QUOTATION_VALIDATION: "quran:quote_validation",
}

DEFAULT_QURAN_ROUTE = "quran:interpretation_rag"
