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
from typing import Dict, List


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


INTENT_ROUTING: Dict[Intent, str] = {
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
    # Additional intents route to tools or appropriate agents
    Intent.ZAKAT: "tool_agent",  # Zakat calculator tool
    Intent.INHERITANCE: "tool_agent",  # Inheritance calculator tool
    Intent.GREETING: "chatbot_agent",  # Greeting responses
    Intent.DUAS: "general_islamic_agent",  # Duas retrieval
    Intent.PRAYER_TIMES: "tool_agent",  # Prayer times tool
    Intent.HIJRI_CALENDAR: "tool_agent",  # Hijri calendar tool
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
    Intent.ISLAMIC_TAZKIYAH: 8,  # ⬅ جديد
    Intent.ARABIC_LANGUAGE: 7,
    Intent.ISLAMIC_HISTORY: 6,
    Intent.FIQH: 5,
    Intent.ZAKAT: 5,
    Intent.INHERITANCE: 5,
    Intent.PRAYER_TIMES: 4,
    Intent.HIJRI_CALENDAR: 4,
    Intent.DUAS: 4,
    Intent.GREETING: 3,
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
    """Detect whether text is primarily Arabic, English, or mixed."""
    ar = len(_ARABIC_RE.findall(text))
    en = len(_LATIN_RE.findall(text))
    if ar == 0 and en == 0:
        return "ar"  # default for empty / numeric queries
    if ar > en:
        return "ar"
    if en > ar:
        return "en"
    return "mixed"


# ============================================================================
# Keyword patterns for fast-path classification.
# This is the SINGLE SOURCE OF TRUTH for classification keywords.
# ============================================================================

KEYWORD_PATTERNS: Dict[Intent, List[str]] = {
    Intent.FIQH: [
        "صلاة", "صلاه", "صوم", "صيام", "زكاة", "زكاه", "حج", "عمرة",
        "طهارة", "طهاره", "وضوء", "غسل", "جنابة",
        "حكم", "يجوز", "حلال", "حرام", "فتوى",
        "واجب", "سنة", "مستحب", "مكروه", "مباح", "نفل", "قربة",
        "بيع", "شراء", "ربا", "قرض", "إجارة", "شركة", "وكالة", "رهن", "شفعة",
        "طلاق", "نكاح", "زواج", "عدة", "متعة", "نفقة", "حدود", "قذف", "سرقة",
        "عبادات", "معاملات", "فقه", "مذهب",
        "حنفية", "مالكية", "شافعيه", "حنبلية",
    ],
    Intent.HADITH: [
        "حديث", "الحديث", "رواه", "اخرجه", "اسناد", "سند", "متن",
        "صحيح", "ضعيف", "حسن", "موضوع", "كذب", "شاذ", "منكر", "مختلف فيه",
        "بخاري", "مسلم", "ترمذي", "نسائي", "ابن ماجه", "ابو داود",
        "الدارمي", "البلاذري", "البيهقي", "ابن حيان", "ابن خزيمة", "الطبراني",
    ],
    Intent.TAFSIR: [
        "تفسير", "معنى", "بيان", "تاويل", "الاية", "الايه",
        "ابن كثير", "جلالين", "قرطبي", "طبري",
        "السمعاني", "البيضاوي", "الزاملي", "الكاشف", "المنار", "الفيومي",
    ],
    Intent.QURAN: [
        "آية", "اية", "سورة", "سوره", "قرآن", "القرآن", "القران",
        "مصحف", "تلاوة", "تجويد", "ايات", "الايات", "ختمة", "حفظ",
    ],
    Intent.AQEEDAH: [
        "عقيدة", "عقيده", "توحيد", "شرك", "كفر", "نفاق",
        "إيمان", "ايمان", "اسماء الله", "صفات الله", "يوم الاخر",
        "ملائكة", "قدر", "قضاء", "جنة", "نار", "جحيم", "عذاب", "ثواب",
        "الأسماء الحسنى", "التوحيد", "المعرفة", "الإله", "الرب", "الألوهية",
    ],
    Intent.SEERAH: [
        "سيرة", "سيره", "السيرة", "السيرة النبوية", "السيره النبويه",
        "النبي", "الرسول", "محمد", "صلى الله عليه وسلم", "صلي الله عليه",
        "غزوة", "غزوه", "غزوات", "هجرة", "هجره", "الهجرة النبوية",
        "بدر", "أحد", "الخندق", "فتح مكة", "تبوك", "خيبر", "طائف",
        "صحابة", "الصحابة", "خلفاء",
        "أبي بكر", "عمر", "عثمان", "علي", "خالد", "عمر بن الخطاب", "ابي بكر",
        "مكة", "المدينة", "المدينه", "مكة المكرمة", "طيبة",
        "ولادة", "بعثة", "وفاة",
        "هدي", "السنة", "السنه", "السنة النبوية", "السنه النبويه",
        "تطبيق", "اقتداء", "قدوة", "أخلاق", "خُلُق", "خُلق",
        "character", "morals", "behavior",
        "نبوية", "نبوي", "القديم", "حياة", "سيرة نبوية", "عبر", "دروس",
    ],
    Intent.USUL_FIQH: [
        "أصول الفقه", "اصول الفقه", "أصول",
        "اجتهاد", "قياس", "استنباط", "اجماع",
        "قاعدة فقهية", "القياس", "الاستنباط", "الاجماع",
        "التراجيح", "الاولويات", "المصالح", "المرسلات",
    ],
    Intent.ISLAMIC_HISTORY: [
        "تاريخ", "دولة", "خلافة", "فتح", "معركة", "حضارة",
        "اموي", "عباسي", "عثماني", "فاطمي", "سلجوقي", "مملوكي",
        "الخلافة", "الفتوحات", "الحروب", "المرحلة", "العهد",
    ],
    Intent.ARABIC_LANGUAGE: [
        "نحو", "صرف", "بلاغة", "بلاغه", "إعراب", "اعراب",
        "لغة", "عربي", "كلمة", "معنى كلمة",
        "المعنى", "المرادف", "الاضداد",
        "صفة", "اسم", "فعل", "حرف", "مصدر", "مشتق",
        "بناء", "مرفوع", "منصوب", "مجرور", "مفعول",
    ],
    Intent.ISLAMIC_TAZKIYAH: [
        "تزكية", "تزكيه", "تربية", "تربيه",
        "سلوك", "السلوك", "تصوف", "تصوّف",
        "روحانية", "قلوب", "قلب",
        "مقامات", "منازل", "مدارج", "سالكين",
        "عابد", "زاهد", "ابن القيم", "الغزالي", "ابن عربي", "الجيلاني",
    ],
    Intent.GREETING: ["سلام", "السلام", "مرحبا", "أهلا", "حياك", "الله يبارك"],
    Intent.ZAKAT: ["زكاة", "زكاه", "حساب الزكاة", "زكاة المال", "نصاب", "فطر"],
    Intent.INHERITANCE: ["ميراث", "فرائض", "تقسيم", "ورثة", "إرث", "تركة"],
    Intent.DUAS: ["دعاء", "ادعية", "الدعاء", "تضرع", "طلب", "إجابة"],
    Intent.PRAYER_TIMES: ["مواقيت", "الصلاة", "الاذان", "اقامة", "وقت"],
    Intent.HIJRI_CALENDAR: ["هجري", "ميلادي", "التقويم", "الشهر", "السنة الهجرية"],
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
