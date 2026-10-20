"""
Hybrid Intent Classifier - Backward Compatibility Module.

This module re-exports the canonical classifier from classifier_factory.py
for backward compatibility with existing code.

DEPRECATED: Import directly from src.application.router.classifier_factory instead.
"""

# Re-export keyword-based classifier from canonical module
from src.application.router.classifier_factory import (
    INTENT_KEYWORDS,
    ClassifierFactory,
    HybridIntentClassifier,
    KeywordBasedClassifier,
    MasterHybridClassifier,
    QueryClassifier,
    classifier_factory,
    detect_language,
    normalize_arabic,
)

# Language detection utility (define locally for backward compat)
from src.application.router.classifier_factory import detect_language as detect_language_util

# Import EmbeddingClassifier from its own module
from src.application.router.embedding_classifier import EmbeddingClassifier

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
    "INTENT_KEYWORDS",
]
