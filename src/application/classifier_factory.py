"""
Intent Classifier Factory for Athar Islamic QA System.

Returns the correct IntentClassifier implementation based on settings.
Coordinates between Keyword, Hybrid (Master), and LLM-based classifiers.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Any

from src.application.interfaces import IntentClassifier
from src.application.router.hybrid_classifier import MasterHybridClassifier
from src.domain.models import ClassificationResult

logger = logging.getLogger(__name__)


# ============================================================================
# Fallback Chain Classifier
# ============================================================================

class FallbackChainClassifier(IntentClassifier):
    """
    Tries primary classifier first, falls back to secondary on any error.
    Useful for LLM -> Hybrid fallback patterns.
    """
    def __init__(self, primary: IntentClassifier, fallback: IntentClassifier):
        self._primary = primary
        self._fallback = fallback

    async def classify(self, query: str) -> ClassificationResult:
        try:
            return await self._primary.classify(query)
        except Exception as e:
            logger.warning(f"Primary classifier failed, using fallback: {e}")
            return await self._fallback.classify(query)

    async def close(self) -> None:
        if hasattr(self._primary, "close"):
            await self._primary.close()
        if hasattr(self._fallback, "close"):
            await self._fallback.close()


# ============================================================================
# Build Classifier Factory Function
# ============================================================================

def build_classifier(embedding_model: Any = None) -> IntentClassifier:
    """
    Constructs and returns an IntentClassifier based on application settings.
    
    Args:
        embedding_model: Optional BGE-M3 model for semantic classification.
    """
    from src.config.settings import settings
    
    backend = settings.classifier_backend
    logger.info(f"Building classifier with backend: {backend}, embedding_model_present: {embedding_model is not None}")

    # 1. Base Master Hybrid Classifier (Keyword + Semantic) - Always available
    master_hybrid = MasterHybridClassifier(
        embedding_model=embedding_model,
        low_conf_threshold=settings.low_conf_threshold
    )

    if backend == "hybrid":
        return master_hybrid

    # 2. LLM Classifier (requires API keys)
    if backend in ("llm", "chain"):
        try:
            from src.infrastructure.llm.llm_classifier import LLMIntentClassifier
            from src.infrastructure.llm.openai_client import build_openai_client

            client = build_openai_client()
            llm_classifier = LLMIntentClassifier(
                client=client,
                model=settings.openai_model,
                temperature=settings.classifier_llm_temperature,
                max_tokens=settings.classifier_llm_max_tokens,
                raise_on_error=(backend == "chain")
            )

            if backend == "chain":
                return FallbackChainClassifier(
                    primary=llm_classifier,
                    fallback=master_hybrid
                )
            
            return llm_classifier

        except (ImportError, ValueError) as e:
            logger.error(f"Failed to initialize LLM classifier: {e}. Falling back to Hybrid.")
            return master_hybrid

    # Default fallback
    return master_hybrid

__all__ = ["build_classifier", "FallbackChainClassifier"]
