"""
Embedding-based Intent Classifier for Athar Islamic QA system.

Phase 5 Upgrade: Uses BGE-M3 embeddings to find semantic similarity
between the user query and intent 'anchors' (descriptions).
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Tuple, Any

from src.domain.intents import Intent, INTENT_DESCRIPTIONS
from src.domain.models import ClassificationResult
from src.application.interfaces import IntentClassifier
from src.config.logging_config import get_logger

logger = get_logger()


class EmbeddingClassifier(IntentClassifier):
    """
    Phase 5 Classifier using semantic vector similarity.
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
            # Use the descriptive text as the semantic center for the intent
            emb = await self.model.encode_query(desc)
            self._anchor_embeddings[intent] = np.array(emb)

    async def classify(self, query: str) -> ClassificationResult:
        """
        Classify query by finding the intent anchor with highest cosine similarity.
        """
        if not query or not query.strip():
            return self._build_unknown_result("Empty query")

        await self._ensure_anchors()

        # 1. Encode user query
        query_emb = np.array(await self.model.encode_query(query))
        
        # 2. Calculate similarities
        scores: List[Tuple[Intent, float]] = []
        for intent, anchor_emb in self._anchor_embeddings.items():
            # Cosine similarity
            dot = np.dot(query_emb, anchor_emb)
            norm = np.linalg.norm(query_emb) * np.linalg.norm(anchor_emb)
            score = dot / norm if norm > 0 else 0.0
            scores.append((intent, float(score)))

        # 3. Rank and return
        scores.sort(key=lambda x: x[1], reverse=True)
        best_intent, best_score = scores[0]

        # Log top 3 for debugging
        logger.debug(
            "embedding_classifier.ranked",
            top_3=[{"intent": i.value, "score": round(s, 4)} for i, s in scores[:3]]
        )

        # Scale semantic score [0.3-0.8] to confidence [0.4-0.95]
        confidence = min(0.95, max(0.4, (best_score - 0.3) * 2))
        
        return ClassificationResult(
            intent=best_intent,
            confidence=round(confidence, 4),
            language="ar", # Detection could be injected here
            reasoning=f"Semantic similarity match ({best_score:.3f}) using BGE-M3",
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

    async def close(self) -> None:
        """Clean up resources."""
        pass
