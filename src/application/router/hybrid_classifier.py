"""
Master Hybrid Intent Classifier for Athar Islamic QA system.

Orchestrates multiple classification tiers:
1. Keyword Fast-Path (High priority matches like "حكم", "ميراث")
2. Embedding Classifier (Phase 5 - Semantic similarity via BGE-M3)
3. Fallback
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple, Any

from src.domain.intents import (
    INTENT_PRIORITY,
    KEYWORD_PATTERNS,
    Intent,
    QuranSubIntent,
)
from src.domain.models import ClassificationResult
from src.application.interfaces import IntentClassifier
from src.application.router.classifier_factory import KeywordBasedClassifier
from src.application.router.embedding_classifier import EmbeddingClassifier
from src.config.logging_config import get_logger

logger = get_logger()


class MasterHybridClassifier(IntentClassifier):
    """
    Consolidated Hybrid Classifier combining Keyword and Semantic tiers.
    """

    def __init__(
        self,
        embedding_model: Any = None,
        low_conf_threshold: float = 0.65
    ) -> None:
        """
        Initialize the multi-tier classifier.
        """
        self._low_conf = low_conf_threshold
        self._keyword_classifier = KeywordBasedClassifier()
        self._embedding_classifier = None
        if embedding_model:
            self._embedding_classifier = EmbeddingClassifier(embedding_model)

    async def classify(self, query: str) -> ClassificationResult:
        """
        Run classification tiers in order.
        """
        logger.info("hybrid_classifier.classify_start", query=query[:50])
        if not query or not query.strip():
            return await self._keyword_classifier.classify("")

        # ── Tier 1: Keyword Fast-Path ────────────────────────────────────
        kw_result = await self._keyword_classifier.classify(query)
        logger.debug("hybrid_classifier.keyword_result", intent=kw_result.intent.value, confidence=kw_result.confidence)
        
        # If keyword match is VERY strong (2+ keywords), return immediately
        if kw_result.confidence >= 0.85:
            logger.info("hybrid_classifier.keyword_win", intent=kw_result.intent.value)
            return kw_result

        # ── Tier 2: Semantic (Embedding) ─────────────────────────────────
        # If keyword was weak or missing, try Embedding
        logger.debug("hybrid_classifier.trying_embedding", present=self._embedding_classifier is not None)
        if self._embedding_classifier:
            try:
                emb_result = await self._embedding_classifier.classify(query)
                logger.info("hybrid_classifier.embedding_result", intent=emb_result.intent.value, confidence=emb_result.confidence)
                
                # If we had NO keywords, embedding result is our best bet
                if kw_result.confidence == 0.0:
                    logger.info("hybrid_classifier.embedding_only_win", intent=emb_result.intent.value)
                    return emb_result
                
                # If embedding result is strong, it can override weak keyword
                if emb_result.confidence >= 0.65:
                    logger.info("hybrid_classifier.embedding_override_win", intent=emb_result.intent.value)
                    return emb_result
                    
                # If both are weak, pick the highest confidence
                if emb_result.confidence > kw_result.confidence:
                    logger.info("hybrid_classifier.embedding_higher_win", intent=emb_result.intent.value)
                    return emb_result
            except Exception as e:
                logger.error("hybrid_classifier.embedding_failed", error=str(e), exc_info=True)

        # ── Tier 3: Return Keyword Result (even if weak/default) ──────────
        logger.info("hybrid_classifier.fallback_to_keyword", intent=kw_result.intent.value)
        return kw_result

    async def close(self) -> None:
        """Clean up resources."""
        if self._embedding_classifier:
            await self._embedding_classifier.close()
