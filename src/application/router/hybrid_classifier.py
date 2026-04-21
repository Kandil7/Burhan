"""
Hybrid Intent Classifier - Backward Compatibility Module.

This module re-exports the canonical classifier from classifier_factory.py
for backward compatibility with existing code.

DEPRECATED: Import directly from src.application.router.classifier_factory instead.
"""

# Re-export all from the canonical module
from src.application.router.classifier_factory import (
    KeywordBasedClassifier,
    EmbeddingClassifier,
    MasterHybridClassifier,
    HybridIntentClassifier,
    ClassifierFactory,
    normalize_arabic,
    detect_language,
    INTENT_KEYWORDS,
    classifier_factory,
    QueryClassifier,
)

# Utility functions that were in this module
from src.application.router.classifier_factory import (
    _detect_language as detect_language_util,
    _classify_quran_subintent as classify_quran_subintent,
    _infer_requires_retrieval as infer_requires_retrieval,
)

__all__ = [
    # Core classes
    "QueryClassifier",
    "KeywordBasedClassifier",
    "EmbeddingClassifier",
    "MasterHybridClassifier",
    "HybridIntentClassifier",
    "ClassifierFactory",
    "classifier_factory",
    # Utilities
    "normalize_arabic",
    "detect_language",
    "detect_language_util",
    "classify_quran_subintent",
    "infer_requires_retrieval",
    "INTENT_KEYWORDS",
]
