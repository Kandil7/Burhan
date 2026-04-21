"""
Scholarly Reranker for Athar Islamic QA system.

This module provides advanced reranking logic that combines:
1. Semantic relevance (vector score)
2. Lexical relevance (BM25 score)
3. Scholarly authority (BookImportanceWeighter)
4. Intent-aware contextual boosting

Phase 10: Dynamic Scholarly Reranking.
"""

from __future__ import annotations

import logging
from typing import Any

from src.domain.intents import Intent
from src.retrieval.ranking.book_weighter import BookImportanceWeighter

logger = logging.getLogger(__name__)


class ScholarlyReranker:
    """
    Reranks candidates based on scholarly authority and intent.
    """

    def __init__(self, book_weighter: BookImportanceWeighter | None = None):
        self.book_weighter = book_weighter or BookImportanceWeighter()

    async def rerank(
        self,
        query: str,
        candidates: list[dict],
        intent: Intent = Intent.ISLAMIC_KNOWLEDGE,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Apply scholarly reranking to candidates.

        Args:
            query: Original query
            candidates: List of candidate passages with scores and metadata
            intent: Detected intent of the query
            top_k: Number of results to return

        Returns:
            Reranked list of top candidates
        """
        if not candidates:
            return []

        scored_candidates = []

        # 1. Intent-based Category Boosting
        category_boosts = self._get_intent_category_boosts(intent)

        # 2. Extract Madhhab from query if exists
        target_madhhab = self._extract_target_madhhab(query)

        for cand in candidates:
            metadata = cand.get("metadata", {})
            book_id = metadata.get("book_id")
            category = metadata.get("category", "").lower()

            # Base score (semantic/lexical)
            base_score = cand.get("score", 0.0)

            # Scholarly Importance (Static)
            importance_weight = 0.5
            if book_id:
                importance_weight = self.book_weighter.get_importance_score(int(book_id))

            # Intent-based Boosting (Dynamic)
            intent_boost = 1.0
            for cat_key, boost in category_boosts.items():
                if cat_key in category:
                    intent_boost = max(intent_boost, boost)

            # Madhhab Boosting (Specific)
            madhhab_boost = 1.0
            if target_madhhab and target_madhhab in category:
                madhhab_boost = 1.3  # Significant boost for requested school

            # Composite Scholarly Score
            # Formula: (Base * 0.4) + (Importance * 0.3) + (IntentBoost * 0.3) * MadhhabBoost
            scholarly_score = ((base_score * 0.4) + (importance_weight * 0.3) + (intent_boost * 0.3)) * madhhab_boost

            # Update candidate
            new_cand = cand.copy()
            new_cand["scholarly_score"] = scholarly_score
            new_cand["importance_weight"] = importance_weight
            new_cand["intent_boost"] = intent_boost

            scored_candidates.append(new_cand)

        # Sort by scholarly score
        scored_candidates.sort(key=lambda x: x.get("scholarly_score", 0), reverse=True)

        logger.info(
            "scholarly_reranker.complete",
            intent=intent,
            count=len(scored_candidates),
            top_score=scored_candidates[0]["scholarly_score"] if scored_candidates else 0,
        )

        return scored_candidates[:top_k]

    def _get_intent_category_boosts(self, intent: Intent) -> dict[str, float]:
        """Returns category boosting factors based on intent."""
        # Mapping intent to categories that should be boosted
        boosts = {
            Intent.FIQH: {"فقه": 1.2, "صحيح": 1.1, "حديث": 1.05},
            Intent.HADITH: {"حديث": 1.2, "صحيح": 1.15, "سنن": 1.1},
            Intent.TAFSIR: {"تفسير": 1.25, "قرآن": 1.1},
            Intent.SEERAH: {"سيرة": 1.25, "تاريخ": 1.1},
            Intent.AQEEDAH: {"عقيدة": 1.2, "توحيد": 1.2},
            Intent.ARABIC_LANGUAGE: {"لغة": 1.2, "نحو": 1.2},
        }
        return boosts.get(intent, {})

    def _extract_target_madhhab(self, query: str) -> str | None:
        """Simple extraction of requested Madhhab from query."""
        madhahib = {
            "حنفي": "حنفي",
            "مالكي": "مالكي",
            "شافعي": "شافعي",
            "حنبلي": "حنبلي",
            "hanafi": "حنفي",
            "maliki": "مالكي",
            "shafi": "شافعي",
            "hanbali": "حنبلي",
        }
        for key, val in madhahib.items():
            if key in query.lower():
                return val
        return None
