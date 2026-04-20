"""
Use case for classifying user queries in Athar Islamic QA system.

This module provides:
- QueryIntent: high-level domain intents
- ClassifyQueryInput / ClassifyQueryOutput dataclasses
- ClassifyQueryUseCase: lightweight keyword-based classifier

NOTE:
This is a fast, deterministic classifier that can be used:
- as a first-pass router
- or as a fallback when LLM-based classification is unavailable.

It is designed to be consistent with src.domain.intents.Intent and routing.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class QueryIntent(str, Enum):
    """Query intent types."""

    ISLAMIC_FIQH = "islamic_fiqh"
    ISLAMIC_HADITH = "islamic_hadith"
    ISLAMIC_TAFSIR = "islamic_tafsir"
    ISLAMIC_AQEEDAH = "islamic_aqeedah"
    ISLAMIC_SEERAH = "islamic_seerah"
    ISLAMIC_HISTORY = "islamic_history"
    ISLAMIC_LANGUAGE = "islamic_language"
    ISLAMIC_TAZKIYAH = "islamic_tazkiyah"
    ISLAMIC_USUL_FIQH = "islamic_usul_fiqh"
    GENERAL_ISLAMIC = "general_islamic"
    TOOL = "tool"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass
class ClassifyQueryInput:
    """Input for classify query use case."""

    query: str
    language: str = "en"
    # optional room for future metadata
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ClassifyQueryOutput:
    """Output for classify query use case."""

    intent: QueryIntent
    confidence: float
    suggested_agent: str
    suggested_collections: List[str]
    requires_clarification: bool
    clarification_options: Optional[List[str]] = None


class ClassifyQueryUseCase:
    """
    Use case for classifying user queries.

    Steps (current lightweight implementation):
    1. Fast keyword-based rules per domain
    2. Special-case rules for tazkiyah / spirituality (Ibn al-Qayyim, Madarij)
    3. Fallback to GENERAL_ISLAMIC
    """

    def __init__(self) -> None:
        # could inject config / logger here if needed
        pass

    async def execute(self, input: ClassifyQueryInput) -> ClassifyQueryOutput:
        q: str = input.query
        q_norm = q.lower()

        # ================================
        # 1) Tazkiyah / spirituality rules
        # ================================
        # ابن القيم + مدارج السالكين + الذوق/الوجد/الفناء/الجمع → تزكية / spiritual
        if (
            any(kw in q for kw in ["ابن القيم", "مدارج السالكين", "منازل السائرين"])
            or any(kw in q for kw in ["الذوق", "الوجد", "الفناء", "الجمع"])
        ):
            return ClassifyQueryOutput(
                intent=QueryIntent.ISLAMIC_TAZKIYAH,
                confidence=0.9,
                suggested_agent="tazkiyah_agent",
                suggested_collections=["spirituality_passages"],
                requires_clarification=False,
                clarification_options=None,
            )

        # ================================
        # 2) Fiqh rules
        # ================================
        if any(
            kw in q
            for kw in [
                "ما حكم",
                "هل يجوز",
                "هل هو حلال",
                "هل هو حرام",
                "حكم",
                "فتوى",
                "فتوه",
            ]
        ):
            return ClassifyQueryOutput(
                intent=QueryIntent.ISLAMIC_FIQH,
                confidence=0.85,
                suggested_agent="fiqh_agent",
                suggested_collections=["fiqh_passages"],
                requires_clarification=False,
                clarification_options=None,
            )

        # ================================
        # 3) Hadith rules
        # ================================
        if any(
            kw in q
            for kw in [
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
            ]
        ):
            return ClassifyQueryOutput(
                intent=QueryIntent.ISLAMIC_HADITH,
                confidence=0.85,
                suggested_agent="hadith_agent",
                suggested_collections=["hadith_passages"],
                requires_clarification=False,
                clarification_options=None,
            )

        # ================================
        # 4) Quran / Tafsir rules
        # ================================
        if any(
            kw in q
            for kw in [
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
            ]
        ):
            # التفريق بين تفسير و lookup ممكن لاحقاً
            return ClassifyQueryOutput(
                intent=QueryIntent.ISLAMIC_TAFSIR,
                confidence=0.8,
                suggested_agent="tafsir_agent",
                suggested_collections=["quran_tafsir_passages"],
                requires_clarification=False,
                clarification_options=None,
            )

        # ================================
        # 5) Aqeedah rules
        # ================================
        if any(
            kw in q
            for kw in [
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
            ]
        ):
            return ClassifyQueryOutput(
                intent=QueryIntent.ISLAMIC_AQEEDAH,
                confidence=0.8,
                suggested_agent="aqeedah_agent",
                suggested_collections=["aqeedah_passages"],
                requires_clarification=False,
                clarification_options=None,
            )

        # ================================
        # 6) Seerah rules
        # ================================
        if any(
            kw in q
            for kw in [
                "سيرة",
                "سيره",
                "السيرة النبوية",
                "السيره النبويه",
                "غزوة",
                "غزوه",
                "حياة النبي",
                "حياه النبي",
                "prophet biography",
            ]
        ):
            return ClassifyQueryOutput(
                intent=QueryIntent.ISLAMIC_SEERAH,
                confidence=0.8,
                suggested_agent="seerah_agent",
                suggested_collections=["seerah_passages"],
                requires_clarification=False,
                clarification_options=None,
            )

        # ================================
        # 7) Arabic language rules
        # ================================
        if any(
            kw in q
            for kw in [
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
            ]
        ):
            return ClassifyQueryOutput(
                intent=QueryIntent.ISLAMIC_LANGUAGE,
                confidence=0.8,
                suggested_agent="language_agent",
                suggested_collections=["language_passages"],
                requires_clarification=False,
                clarification_options=None,
            )

        # ================================
        # 8) Usul Fiqh rules
        # ================================
        if any(
            kw in q
            for kw in [
                "أصول الفقه",
                "اصول الفقه",
                "usul al-fiqh",
                "الاجتهاد",
                "القياس",
                "الإجماع",
                "الاجماع",
                "مصادر التشريع",
                "مصادر الاحكام",
            ]
        ):
            return ClassifyQueryOutput(
                intent=QueryIntent.ISLAMIC_USUL_FIQH,
                confidence=0.8,
                suggested_agent="usul_fiqh_agent",
                suggested_collections=["usul_fiqh_passages"],
                requires_clarification=False,
                clarification_options=None,
            )

        # ================================
        # 9) History rules
        # ================================
        if any(
            kw in q
            for kw in [
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
            ]
        ):
            return ClassifyQueryOutput(
                intent=QueryIntent.ISLAMIC_HISTORY,
                confidence=0.75,
                suggested_agent="history_agent",
                suggested_collections=["history_passages"],
                requires_clarification=False,
                clarification_options=None,
            )

        # ================================
        # 10) Fallback: general Islamic
        # ================================
        return ClassifyQueryOutput(
            intent=QueryIntent.GENERAL_ISLAMIC,
            confidence=0.6,
            suggested_agent="general_islamic_agent",
            suggested_collections=["quran", "sahih_bukhari", "fiqh_islami"],
            requires_clarification=False,
            clarification_options=None,
        )


# Default use case instance
classify_query_use_case = ClassifyQueryUseCase()