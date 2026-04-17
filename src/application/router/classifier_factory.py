# Classifier Factory Module
"""Factory for creating query classifiers."""

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class QueryClassifier(ABC):
    """Abstract base class for query classifiers."""

    @abstractmethod
    async def classify(self, query: str) -> Dict[str, Any]:
        """Classify a query."""
        pass


class KeywordBasedClassifier(QueryClassifier):
    """Keyword-based query classifier."""

    def __init__(self):
        self.keywords: Dict[str, list[str]] = {
            "fiqh": ["fiqh", "jurisprudence", "حكم", "فتوى", "صلاة", "صوم"],
            "hadith": ["hadith", "حديث", "sunnah", "صحيح", "ضعيف"],
            "tafsir": ["tafsir", "تفسير", "قرآن", "آية", "سورة"],
            "aqeedah": ["aqeedah", "عقيدة", "توحيد", "إيمان"],
            "seerah": ["seerah", "سيرة", "نبوية", "صحابة"],
            "history": ["history", "تاريخ", "خلافة"],
            "tool": ["calculate", "zakat", "inheritance", "prayer times"],
        }

    async def classify(self, query: str) -> Dict[str, Any]:
        """Classify based on keywords."""
        query_lower = query.lower()

        scores = {}
        for category, keywords in self.keywords.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[category] = score

        if not scores:
            return {
                "category": "general_islamic",
                "confidence": 0.5,
                "keywords_found": [],
            }

        top_category = max(scores, key=scores.get)
        confidence = min(scores[top_category] / 3, 1.0)

        return {
            "category": top_category,
            "confidence": confidence,
            "keywords_found": [k for k in self.keywords[top_category] if k in query_lower],
        }


class LLMBasedClassifier(QueryClassifier):
    """LLM-based query classifier."""

    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client

    async def classify(self, query: str) -> Dict[str, Any]:
        """Classify using LLM."""
        # Placeholder - would use LLM for classification
        raise NotImplementedError("LLM classifier not yet implemented")


class ClassifierFactory:
    """Factory for creating query classifiers."""

    @staticmethod
    def create(
        classifier_type: str = "keyword",
        **kwargs,
    ) -> QueryClassifier:
        """Create a classifier instance."""
        if classifier_type == "keyword":
            return KeywordBasedClassifier()
        elif classifier_type == "llm":
            return LLMBasedClassifier(kwargs.get("llm_client"))
        else:
            raise ValueError(f"Unknown classifier type: {classifier_type}")

    @staticmethod
    def create_default() -> QueryClassifier:
        """Create the default classifier."""
        return ClassifierFactory.create("keyword")


# Default factory instance
classifier_factory = ClassifierFactory()
