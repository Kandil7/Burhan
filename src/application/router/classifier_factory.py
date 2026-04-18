# Classifier Factory Module
"""
High-Precision Keyword-Based Classifier for Athar.
Uses robust Arabic normalization and tiered matching.
"""

import re
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from src.domain.models import ClassificationResult
from src.domain.intents import Intent, QuranSubIntent

class QueryClassifier(ABC):
    """Abstract base class for query classifiers."""

    @abstractmethod
    async def classify(self, query: str) -> ClassificationResult:
        """Classify a query."""
        pass


def _normalize_arabic(text: str) -> str:
    """Robust Arabic text normalization for keyword matching."""
    if not text: return ""
    # Strip diacritics
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    # Unify Alef variants
    text = re.sub(r"[إأآٱ]", "ا", text)
    # Unify Ta-Marbuta and Ya (careful: might over-match, but better for keywords)
    text = text.replace("ة", "ه").replace("ى", "ي")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


class KeywordBasedClassifier(QueryClassifier):
    """
    Enhanced Keyword-based query classifier with robust normalization.
    """

    def __init__(self):
        # Priority mapping: More specific/unique terms first
        # We pre-normalize keywords for performance
        self.keywords: Dict[Intent, List[str]] = {
            Intent.FIQH: [
                "حكم", "يجوز", "حلال", "حرام", "فتوى", "واجب", "سنة", "مستحب", "مكروه",
                "صلاة", "صوم", "زكاة", "حج", "طهارة", "وضوء", "جنابة", "عمرة", "طلاق",
                "نكاح", "بيع", "ربا", "معاملات", "عبادات", "فقه"
            ],
            Intent.HADITH: [
                "حديث", "رواه", "اخرجه", "اسناد", "سند", "متن", "صحيح", "ضعيف", "حسن",
                "بخاري", "مسلم", "ترمذي", "نسائي", "ابن ماجه", "ابو داود"
            ],
            Intent.TAFSIR: [
                "تفسير", "معنى", "بيان", "تاويل", "ابن كثير", "جلالين", "قرطبي", "طبري",
                "تفسير الايه", "شرح الايه"
            ],
            Intent.QURAN: [
                "آية", "سورة", "قرآن", "مصحف", "تلاوة", "تجويد"
            ],
            Intent.AQEEDAH: [
                "عقيدة", "توحيد", "ايمان", "شرك", "كفر", "نفاق", "اسماء الله", "صفات الله",
                "يوم الاخر", "ملائكة", "قدر", "قضاء"
            ],
            Intent.SEERAH: [
                "سيرة", "غزوة", "هجرة", "صحابة", "خلفاء", "نبوية", "مكة", "مدينة", "بدر", "أحد",
                "الخندق", "فتح مكة", "تبوك", "المتخلفين", "النبي", "الرسول", "محمد صلى الله عليه وسلم"
            ],
            Intent.USUL_FIQH: [
                "اصول الفقه", "استنباط", "قياس", "اجماع", "اجتهاد", "قاعدة فقهية"
            ],
            Intent.ISLAMIC_HISTORY: [
                "تاريخ", "دولة", "خلافة", "فتح", "معركة", "حضارة", "اموي", "عباسي", "عثماني"
            ],
            Intent.ARABIC_LANGUAGE: [
                "نحو", "صرف", "بلاغة", "اعراب", "كلمة", "معنى كلمة", "لغة", "عربي"
            ],
            Intent.GREETING: [
                "سلام", "السلام", "مرحبا", "أهلا"
            ],
            Intent.ZAKAT: ["حساب الزكاة", "زكاة المال", "نصاب"],
            Intent.INHERITANCE: ["ميراث", "فرائض", "تقسيم", "ورثة"],
        }
        
        # Pre-normalize everything in the registry
        self._norm_keywords = {
            intent: [_normalize_arabic(kw) for kw in kws]
            for intent, kws in self.keywords.items()
        }

    async def classify(self, query: str) -> ClassificationResult:
        """Classify based on keyword density and priority."""
        if not query or not query.strip():
            return ClassificationResult(
                intent=Intent.ISLAMIC_KNOWLEDGE, confidence=0.0, language="ar", 
                reasoning="Empty query.", requires_retrieval=True, method="keyword"
            )

        norm_query = _normalize_arabic(query)
        
        # Count matches per intent
        matches: Dict[Intent, int] = {}
        for intent, patterns in self._norm_keywords.items():
            count = 0
            for p in patterns:
                # Use word boundaries or check if contained
                # For Arabic, simple 'in' is often best due to suffixes
                if p in norm_query:
                    count += 1
            if count > 0:
                matches[intent] = count

        if not matches:
            # RETURN ZERO CONFIDENCE so MasterHybrid switches to Tier 2 (Embedding)
            return ClassificationResult(
                intent=Intent.ISLAMIC_KNOWLEDGE,
                confidence=0.0,
                language="ar",
                reasoning="No keywords matched.",
                requires_retrieval=True,
                method="keyword",
            )

        # Pick highest match count
        best_intent = max(matches, key=matches.get)
        
        # Boost confidence based on match count
        # 1 match = 0.7, 2 matches = 0.85, 3+ = 0.95
        count = matches[best_intent]
        confidence = 0.7 if count == 1 else (0.85 if count == 2 else 0.95)

        return ClassificationResult(
            intent=best_intent,
            confidence=confidence,
            language="ar",
            reasoning=f"Matched {count} keywords for {best_intent.value}.",
            requires_retrieval=True,
            method="keyword",
        )


class ClassifierFactory:
    """Factory for creating query classifiers."""

    @staticmethod
    def create(
        classifier_type: str = "keyword",
        **kwargs,
    ) -> QueryClassifier:
        """Create a classifier instance."""
        return KeywordBasedClassifier()

    @staticmethod
    def create_default() -> QueryClassifier:
        """Create the default classifier."""
        return KeywordBasedClassifier()


# Default factory instance
classifier_factory = ClassifierFactory()
