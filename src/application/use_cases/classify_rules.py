"""
Keyword-based intent classification rules.

This module contains the keyword rules for each intent domain.
Used by ClassifyQueryUseCase for fast, deterministic classification.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class IntentRule:
    """Represents a classification rule for an intent."""

    intent: str
    keywords: List[str]
    confidence: float
    agent: str
    collections: List[str]


# All classification rules in priority order
INTENT_RULES: List[IntentRule] = [
    # Tazkiyah / Spirituality (highest priority)
    IntentRule(
        intent="islamic_tazkiyah",
        keywords=[
            "ابن القيم",
            "مدارج السالكين",
            "منازل السائرين",
            "الذوق",
            "الوجد",
            "الفناء",
            "الجمع",
            "تزكية",
            "تصوف",
            "سلوك",
            "قلب",
        ],
        confidence=0.9,
        agent="tazkiyah_agent",
        collections=["spirituality_passages"],
    ),
    # Fiqh
    IntentRule(
        intent="islamic_fiqh",
        keywords=[
            "ما حكم",
            "هل يجوز",
            "هل هو حلال",
            "هل هو حرام",
            "حكم",
            "فتوى",
            "فتوه",
            "فقه",
            "صلاة",
            "صوم",
            "زكاة",
            "حج",
        ],
        confidence=0.85,
        agent="fiqh_agent",
        collections=["fiqh_passages"],
    ),
    # Hadith
    IntentRule(
        intent="islamic_hadith",
        keywords=[
            "حديث",
            "الحديث",
            "سند",
            "إسناد",
            "اسناد",
            "متن",
            "رواه",
            "رواية",
            "روايه",
            "صحيح البخاري",
            "صحيح مسلم",
            "ضعيف",
            "موضوع",
            "حسن",
        ],
        confidence=0.85,
        agent="hadith_agent",
        collections=["hadith_passages"],
    ),
    # Quran / Tafsir
    IntentRule(
        intent="islamic_tafsir",
        keywords=[
            "آية",
            "ايه",
            "سورة",
            "سوره",
            "القرآن",
            "القران",
            "قرآن",
            "quran",
            "ayah",
            "surah",
            "تفسير",
            "معنى الآية",
        ],
        confidence=0.8,
        agent="tafsir_agent",
        collections=["quran_tafsir_passages"],
    ),
    # Aqeedah
    IntentRule(
        intent="islamic_aqeedah",
        keywords=[
            "عقيدة",
            "عقيده",
            "توحيد",
            "tawhid",
            "أركان الإيمان",
            "اركان الايمان",
            "الإيمان بالله",
            "الايمان بالله",
            "أسماء الله",
            "اسماء الله الحسنى",
        ],
        confidence=0.8,
        agent="aqeedah_agent",
        collections=["aqeedah_passages"],
    ),
    # Seerah
    IntentRule(
        intent="islamic_seerah",
        keywords=[
            "سيرة",
            "سيره",
            "السيرة النبوية",
            "السيره النبويه",
            "غزوة",
            "غزوه",
            "حياة النبي",
            "حياه النبي",
            "prophet biography",
            "النبي",
            "الرسول",
            "هدي",
            "السنة النبوية",
        ],
        confidence=0.8,
        agent="seerah_agent",
        collections=["seerah_passages"],
    ),
    # Arabic Language
    IntentRule(
        intent="islamic_language",
        keywords=[
            "نحو",
            "صرف",
            "بلاغة",
            "بلاغه",
            "إعراب",
            "اعراب",
            "معنى كلمة",
            "معنى كلمه",
            "arabic grammar",
            "arabic morphology",
        ],
        confidence=0.8,
        agent="language_agent",
        collections=["language_passages"],
    ),
    # Usul Fiqh
    IntentRule(
        intent="islamic_usul_fiqh",
        keywords=[
            "أصول الفقه",
            "اصول الفقه",
            "usul al-fiqh",
            "الاجتهاد",
            "القياس",
            "الإجماع",
            "الاجماع",
            "مصادر التشريع",
            "مصادر الاحكام",
        ],
        confidence=0.8,
        agent="usul_fiqh_agent",
        collections=["usul_fiqh_passages"],
    ),
    # Islamic History
    IntentRule(
        intent="islamic_history",
        keywords=[
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
        ],
        confidence=0.75,
        agent="history_agent",
        collections=["history_passages"],
    ),
]


def classify_by_keywords(query: str) -> Tuple[str, float, str, List[str]]:
    """
    Classify query using keyword rules.

    Args:
        query: User query string

    Returns:
        Tuple of (intent, confidence, agent, collections)
    """
    for rule in INTENT_RULES:
        if any(kw in query for kw in rule.keywords):
            return (
                rule.intent,
                rule.confidence,
                rule.agent,
                rule.collections,
            )

    # Fallback to general Islamic
    return (
        "general_islamic",
        0.6,
        "general_islamic_agent",
        ["quran", "sahih_bukhari", "fiqh_islami"],
    )


__all__ = [
    "IntentRule",
    "INTENT_RULES",
    "classify_by_keywords",
]
