# Hybrid Classifier Module
"""Hybrid classifier combining multiple classification approaches."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ClassificationResult:
    """Result from hybrid classifier."""

    category: str
    confidence: float
    method: str
    details: Dict[str, Any]


class HybridClassifier:
    """Combines multiple classification methods."""

    def __init__(
        self,
        classifiers: Optional[List[Any]] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        """Initialize hybrid classifier with optional classifiers and weights."""
        self.classifiers = classifiers or []
        self.weights = weights or {}

    async def classify(self, query: str) -> ClassificationResult:
        """Classify using ensemble of classifiers."""
        if not self.classifiers:
            return ClassificationResult(
                category="general_islamic",
                confidence=0.5,
                method="default",
                details={},
            )

        weighted_results: list[tuple[Any, dict]] = []
        for classifier in self.classifiers:
            try:
                result = await classifier.classify(query)
                weighted_results.append((classifier, result))
            except Exception:
                continue

        if not weighted_results:
            return ClassificationResult(
                category="general_islamic",
                confidence=0.5,
                method="fallback",
                details={},
            )

        category_scores: Dict[str, float] = {}
        for classifier, result in weighted_results:
            category = result.get("category", "general_islamic")
            confidence = result.get("confidence", 0.5)
            classifier_key = classifier.__class__.__name__
            # Prefer classifier weight, with optional category fallback.
            weight = self.weights.get(classifier_key, self.weights.get(category, 1.0))

            if category not in category_scores:
                category_scores[category] = 0.0
            category_scores[category] += confidence * weight

        if not category_scores:
            return ClassificationResult(
                category="general_islamic",
                confidence=0.5,
                method="fallback",
                details={},
            )

        best_category = max(category_scores, key=category_scores.get)
        total = sum(category_scores.values())
        best_confidence = category_scores[best_category] / total if total > 0 else 0.5

        return ClassificationResult(
            category=best_category,
            confidence=min(best_confidence, 1.0),
            method="hybrid",
            details={
                "all_categories": category_scores,
                "classifier_count": len(weighted_results),
            },
        )

    def add_classifier(self, classifier: Any, weight: float = 1.0) -> None:
        """Add a classifier to the ensemble."""
        self.classifiers.append(classifier)
        self.weights[classifier.__class__.__name__] = weight


# Default hybrid classifier instance
hybrid_classifier = HybridClassifier()
