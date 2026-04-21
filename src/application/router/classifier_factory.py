"""
Intent Classification Module for Athar Islamic QA System.

This module provides the canonical intent classification system:
1. KeywordBasedClassifier - Fast keyword matching for clear signals
2. MasterHybridClassifier - Combines keyword + embedding tiers
3. ClassifierFactory - Factory for creating classifiers

All classification code should use these implementations.

Note: EmbeddingClassifier is in src/application/router/embedding_classifier.py
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.application.interfaces import IntentClassifier
from src.config.logging_config import get_logger
from src.domain.intents import Intent, INTENT_DESCRIPTIONS
from src.domain.models import ClassificationResult

logger = get_logger()


# ============================================================================
# Arabic Text Normalization
# ============================================================================


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


# ============================================================================
# Language Detection
# ============================================================================

_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
_LATIN_RE = re.compile(r"[a-zA-Z]")


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
# Intent Keywords Registry
# ============================================================================

# Comprehensive keyword registry for each intent
# Keywords are ordered by specificity - more specific first
INTENT_KEYWORDS: Dict[Intent, List[str]] = {
    Intent.FIQH: [
        # Core Fiqh terms
        "حكم",
        "يجوز",
        "حلال",
        "حرام",
        "فتوى",
        "واجب",
        "سنة",
        "مستحب",
        "مكروه",
        "حرام",
        "مباح",
        "نفل",
        "قربة",
        # Worship
        "صلاة",
        "صوم",
        "زكاة",
        "حج",
        "عمرة",
        "طهارة",
        "وضوء",
        "جنابة",
        "غسل",
        # Transactions
        "بيع",
        "شراء",
        "ربا",
        "قرض",
        "إجارة",
        "شركة",
        "وكالة",
        "رهن",
        "شفعة",
        # Family
        "طلاق",
        "نكاح",
        "زواج",
        "عدة",
        "متعة",
        "نفقة",
        "حدود",
        "قذف",
        "سرقة",
        # General
        "عبادات",
        "معاملات",
        "فقه",
        "مذهب",
        "حنفية",
        "مالكية",
        "شافعيه",
        "حنبلية",
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
    ],
    Intent.TAFSIR: [
        "تفسير",
        "معنى",
        "بيان",
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
        # Core seerah terms - highest priority
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
        # Battles
        "بدر",
        "أحد",
        "الخندق",
        "فتح مكة",
        "تبوك",
        "خيبر",
        "طائف",
        # Companions
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
        "الصحابة",
        # Life events
        "مكة",
        "المدينة",
        "المدينه",
        "مكة المكرمة",
        "طيبة",
        "ولادة",
        "بعثة",
        "هجرة",
        "وفاة",
        "غزوة",
        "السنة",
        # Character & behavior (Prophetic traditions)
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
        # General seerah
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
        "مصدر",
        "اعراب",
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
        "تصوف",
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
    Intent.PRAYER_TIMES: ["مواقيت", "الصلاة", "الاذان", "اقامة", "وقت"],
    Intent.HIJRI_CALENDAR: ["هجري", "ميلادي", "التقويم", "الشهر", "السنة الهجرية"],
}


# ============================================================================
# Query Classifier Abstract Base Class
# ============================================================================


class QueryClassifier(ABC):
    """Abstract base class for query classifiers."""

    @abstractmethod
    async def classify(self, query: str) -> ClassificationResult:
        """Classify a query."""
        pass


# ============================================================================
# Keyword-Based Classifier
# ============================================================================


class KeywordBasedClassifier(QueryClassifier):
    """
    High-precision keyword-based query classifier.

    Uses robust Arabic normalization and match counting for classification.
    """

    def __init__(self, keywords: Optional[Dict[Intent, List[str]]] = None):
        """
        Initialize the classifier with keywords.

        Args:
            keywords: Optional custom keywords dict. Uses INTENT_KEYWORDS if not provided.
        """
        self.keywords = keywords or INTENT_KEYWORDS
        # Pre-normalize keywords for performance
        self._norm_keywords: Dict[Intent, List[str]] = {
            intent: [normalize_arabic(kw) for kw in kws] for intent, kws in self.keywords.items()
        }

    async def classify(self, query: str) -> ClassificationResult:
        """Classify based on keyword density and priority."""
        if not query or not query.strip():
            return ClassificationResult(
                intent=Intent.ISLAMIC_KNOWLEDGE,
                confidence=0.0,
                language="ar",
                reasoning="Empty query.",
                requires_retrieval=True,
                method="keyword",
            )

        norm_query = normalize_arabic(query)

        # Count matches per intent
        matches: Dict[Intent, int] = {}
        for intent, patterns in self._norm_keywords.items():
            count = sum(1 for p in patterns if p in norm_query)
            if count > 0:
                matches[intent] = count

        if not matches:
            # Return zero confidence so hybrid classifier can try next tier
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
        count = matches[best_intent]

        # Confidence based on match count
        confidence = 0.7 if count == 1 else (0.85 if count == 2 else 0.95)

        return ClassificationResult(
            intent=best_intent,
            confidence=confidence,
            language="ar",
            reasoning=f"Matched {count} keywords for {best_intent.value}.",
            requires_retrieval=True,
            method="keyword",
        )


# ============================================================================
# Embedding-Based Classifier
# ============================================================================


class EmbeddingClassifier(QueryClassifier):
    """
    Semantic classifier using embedding similarity.

    Phase 5: Uses BGE-M3 embeddings to find semantic similarity
    between the user query and intent descriptions.
    """

    def __init__(self, embedding_model: Any, threshold: float = 0.45):
        """
        Initialize with an embedding model.

        Args:
            embedding_model: Instance of EmbeddingModel (e.g., BGE-M3 wrapper)
            threshold: Minimum similarity score for a valid classification
        """
        self.model = embedding_model
        self.threshold = threshold
        self._anchor_embeddings: Dict[Intent, np.ndarray] = {}

    async def _ensure_anchors(self) -> None:
        """Lazily encode intent descriptions as vector anchors."""
        if self._anchor_embeddings:
            return

        logger.info("embedding_classifier.indexing_anchors")
        for intent, desc in INTENT_DESCRIPTIONS.items():
            emb = await self.model.encode_query(desc)
            self._anchor_embeddings[intent] = np.array(emb)

    async def classify(self, query: str) -> ClassificationResult:
        """Classify query by finding the intent anchor with highest cosine similarity."""
        if not query or not query.strip():
            return self._build_unknown_result("Empty query")

        await self._ensure_anchors()

        # Encode user query
        query_emb = np.array(await self.model.encode_query(query))

        # Calculate cosine similarities
        scores: List[Tuple[Intent, float]] = []
        for intent, anchor_emb in self._anchor_embeddings.items():
            dot = np.dot(query_emb, anchor_emb)
            norm = np.linalg.norm(query_emb) * np.linalg.norm(anchor_emb)
            score = dot / norm if norm > 0 else 0.0
            scores.append((intent, float(score)))

        # Rank and return
        scores.sort(key=lambda x: x[1], reverse=True)
        best_intent, best_score = scores[0]

        logger.debug(
            "embedding_classifier.ranked", top_3=[{"intent": i.value, "score": round(s, 4)} for i, s in scores[:3]]
        )

        # Scale semantic score to confidence
        confidence = min(0.95, max(0.4, (best_score - 0.3) * 2))

        return ClassificationResult(
            intent=best_intent,
            confidence=round(confidence, 4),
            language="ar",
            reasoning=f"Semantic similarity match ({best_score:.3f}) using embeddings",
            requires_retrieval=True,
            method="embedding",
        )

    def _build_unknown_result(self, reason: str) -> ClassificationResult:
        return ClassificationResult(
            intent=Intent.ISLAMIC_KNOWLEDGE,
            confidence=0.5,
            language="ar",
            reasoning=reason,
            requires_retrieval=True,
            method="embedding",
        )


# ============================================================================
# Hybrid Classifier
# ============================================================================


class MasterHybridClassifier(IntentClassifier):
    """
    Consolidated Hybrid Classifier combining Keyword and Semantic tiers.

    Tier 1: Keyword fast-path (always runs first)
    Tier 2: Embedding fallback (when no keywords matched)
    """

    def __init__(self, embedding_model: Any = None, low_conf_threshold: float = 0.65) -> None:
        """
        Initialize the multi-tier classifier.

        Args:
            embedding_model: Optional embedding model for semantic classification
            low_conf_threshold: Threshold for low confidence detection
        """
        self._low_conf = low_conf_threshold
        self._keyword_classifier = KeywordBasedClassifier()
        self._embedding_classifier = None
        if embedding_model:
            self._embedding_classifier = EmbeddingClassifier(embedding_model)

    async def classify(self, query: str) -> ClassificationResult:
        """Run classification tiers in order."""
        logger.info("hybrid_classifier.classify_start", query=query[:50])

        if not query or not query.strip():
            return await self._keyword_classifier.classify("")

        # Tier 1: Keyword Fast-Path
        kw_result = await self._keyword_classifier.classify(query)
        logger.debug("hybrid_classifier.keyword_result", intent=kw_result.intent.value, confidence=kw_result.confidence)

        # If keyword match exists, use it
        if kw_result.confidence > 0.0:
            logger.info("hybrid_classifier.keyword_win", intent=kw_result.intent.value)
            return kw_result

        # Tier 2: Embedding Fallback
        if self._embedding_classifier:
            try:
                emb_result = await self._embedding_classifier.classify(query)
                logger.info(
                    "hybrid_classifier.embedding_result",
                    intent=emb_result.intent.value,
                    confidence=emb_result.confidence,
                )
                return emb_result
            except Exception as e:
                logger.error("hybrid_classifier.embedding_failed", error=str(e))

        # Fallback
        logger.info("hybrid_classifier.fallback_to_default")
        return kw_result

    async def close(self) -> None:
        """Clean up resources."""
        if self._embedding_classifier:
            await self._embedding_classifier.close()


# ============================================================================
# Classifier Factory
# ============================================================================


class ClassifierFactory:
    """Factory for creating query classifiers."""

    @staticmethod
    def create_keyword() -> KeywordBasedClassifier:
        """Create a keyword-based classifier."""
        return KeywordBasedClassifier()

    @staticmethod
    def create_hybrid(embedding_model: Any = None) -> MasterHybridClassifier:
        """Create a hybrid classifier with optional embedding support."""
        return MasterHybridClassifier(embedding_model=embedding_model)

    @staticmethod
    def create_default() -> KeywordBasedClassifier:
        """Create the default classifier (keyword-based)."""
        return KeywordBasedClassifier()


# Default factory instance
classifier_factory = ClassifierFactory()

# Backward compatibility aliases
HybridIntentClassifier = MasterHybridClassifier


__all__ = [
    # Core classes
    "QueryClassifier",
    "KeywordBasedClassifier",
    "EmbeddingClassifier",
    "MasterHybridClassifier",
    "HybridIntentClassifier",
    "ClassifierFactory",
    # Utilities
    "normalize_arabic",
    "detect_language",
    "INTENT_KEYWORDS",
    # Backward compatibility
    "classifier_factory",
]
