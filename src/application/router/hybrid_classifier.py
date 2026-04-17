# Hybrid Classifier Module
"""Hybrid classifier combining multiple classification approaches."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


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
    ):
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

        # Collect results from all classifiers
        results = []
        for classifier in self.classifiers:
            try:
                result = await classifier.classify(query)
                results.append(result)
            except Exception:
                continue

        if not results:
            return ClassificationResult(
                category="general_islamic",
                confidence=0.5,
                method="fallback",
                details={},
            )

        # Combine results using weighted voting
        category_scores: Dict[str, float] = {}

        for result in results:
            category = result.get("category", "general_islamic")
            confidence = result.get("confidence", 0.5)
            weight = self.weights.get(category, 1.0)

            if category not in category_scores:
                category_scores[category] = 0.0
            category_scores[category] += confidence * weight

        # Get best category
        if not category_scores:
            best_category = "general_islamic"
            best_confidence = 0.5
        else:
            best_category = max(category_scores, key=category_scores.get)
            # Normalize confidence
            total = sum(category_scores.values())
            best_confidence = category_scores[best_category] / total if total > 0 else 0.5

        return ClassificationResult(
            category=best_category,
            confidence=min(best_confidence, 1.0),
            method="hybrid",
            details={
                "all_categories": category_scores,
                "classifier_count": len(results),
            },
        )

    def add_classifier(self, classifier: Any, weight: float = 1.0) -> None:
        """Add a classifier to the ensemble."""
        self.classifiers.append(classifier)
        # Use category as weight key
        self.weights[classifier.__class__.__name__] = weight


# Default hybrid classifier instance
hybrid_classifier = HybridClassifier()
