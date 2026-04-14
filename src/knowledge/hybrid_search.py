"""
Hybrid Search for Athar Islamic QA system.

Combines semantic search (embeddings) with keyword search (BM25)
for better retrieval of Islamic texts.

Enhanced with faceted search support:
- Filter by author, era, book, collection
- Filter by time period (death year range)
- Filter by category/madhhab
- Multi-facet filtering

Phase 6 Refactoring:
- Uses shared EraClassifier from utils instead of duplicate _classify_era method
"""
import re
from typing import Any

import numpy as np

from src.config.logging_config import get_logger
from src.knowledge.vector_store import VectorStore
from src.utils.era_classifier import EraClassifier  # Phase 6: Shared utility

logger = get_logger()


class HybridSearcher:
    """
    Hybrid search combining semantic and keyword matching.

    Process:
    1. Semantic search → top-k1 results
    2. Keyword search (BM25-like) → top-k2 results
    3. Reciprocal rank fusion
    4. Return merged results

    Usage:
        searcher = HybridSearcher(vector_store)
        results = await searcher.search(query, query_embedding, "fiqh_passages")
    """

    def __init__(self, vector_store: VectorStore, k: int = 60):
        """
        Initialize hybrid searcher.

        Args:
            vector_store: Vector store instance
            k: Reciprocal rank fusion parameter (default: 60)
        """
        self.vector_store = vector_store
        self.k = k

    async def search(
        self,
        query: str,
        query_embedding: np.ndarray,
        collection: str,
        top_k: int = 10
    ) -> list[dict]:
        """
        Hybrid search combining semantic and keyword results.

        Args:
            query: Original query text (for keyword search)
            query_embedding: Query embedding (for semantic search)
            collection: Collection name
            top_k: Number of results to return

        Returns:
            Merged and ranked results
        """
        # Step 1: Semantic search
        semantic_results = await self.vector_store.search(
            collection,
            query_embedding,
            top_k=top_k * 2  # Get more for fusion
        )

        # Step 2: Keyword search (on semantic results)
        keyword_scores = self._keyword_search(query, semantic_results)

        # Step 3: Reciprocal rank fusion
        fused_results = self._reciprocal_rank_fusion(
            semantic_results,
            keyword_scores,
            top_k
        )

        logger.info(
            "hybrid_search.complete",
            query=query[:50],
            semantic_count=len(semantic_results),
            keyword_count=len(keyword_scores),
            final_count=len(fused_results)
        )

        return fused_results

    async def search_with_facets(
        self,
        query: str,
        query_embedding: np.ndarray,
        collection: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict]:
        """
        Hybrid search with metadata facet filtering.

        Supports filters:
        - author: str or list[str] - Filter by author name
        - author_death_min: int - Minimum death year (Hijri)
        - author_death_max: int - Maximum death year (Hijri)
        - book_id: int or list[int] - Filter by book ID
        - category: str or list[str] - Filter by category
        - collection_subset: list[str] - Filter to specific collections
        - era: str or list[str] - Filter by scholarly era

        Args:
            query: Original query text
            query_embedding: Query embedding
            collection: Collection name
            top_k: Number of results to return
            filters: Dict of filter criteria

        Returns:
            Filtered and ranked results
        """
        # Step 1: Get more results for filtering
        expanded_k = top_k * 5 if filters else top_k * 2

        # Step 2: Semantic search
        semantic_results = await self.vector_store.search(
            collection,
            query_embedding,
            top_k=expanded_k
        )

        # Step 3: Apply facet filters
        if filters:
            semantic_results = self._apply_filters(semantic_results, filters)
            logger.info(
                "hybrid_search.facets_applied",
                filters=list(filters.keys()),
                results_before=expanded_k,
                results_after=len(semantic_results),
            )

        # Step 4: Keyword search on filtered results
        keyword_scores = self._keyword_search(query, semantic_results)

        # Step 5: Reciprocal rank fusion
        fused_results = self._reciprocal_rank_fusion(
            semantic_results,
            keyword_scores,
            top_k
        )

        logger.info(
            "hybrid_search.faceted_complete",
            query=query[:50],
            filters=list(filters.keys()) if filters else None,
            final_count=len(fused_results)
        )

        return fused_results

    def _apply_filters(
        self,
        results: list[dict],
        filters: dict[str, Any]
    ) -> list[dict]:
        """Apply metadata filters to search results."""
        filtered = []

        for result in results:
            match = True

            # Author filter
            if "author" in filters:
                author_filter = filters["author"]
                if isinstance(author_filter, list):
                    if result.get("author") not in author_filter:
                        match = False
                elif result.get("author") != author_filter:
                    match = False

            # Death year range filter
            if match and "author_death_min" in filters:
                death_year = result.get("author_death")
                if death_year is None or death_year < filters["author_death_min"]:
                    match = False

            if match and "author_death_max" in filters:
                death_year = result.get("author_death")
                if death_year is None or death_year > filters["author_death_max"]:
                    match = False

            # Book ID filter
            if match and "book_id" in filters:
                book_filter = filters["book_id"]
                if isinstance(book_filter, list):
                    if result.get("book_id") not in book_filter:
                        match = False
                elif result.get("book_id") != book_filter:
                    match = False

            # Category filter
            if match and "category" in filters:
                cat_filter = filters["category"]
                if isinstance(cat_filter, list):
                    if result.get("category") not in cat_filter:
                        match = False
                elif result.get("category") != cat_filter:
                    match = False

            # Collection filter
            if match and "collection_subset" in filters:
                if result.get("collection") not in filters["collection_subset"]:
                    match = False

            # Era filter
            if match and "era" in filters:
                era_filter = filters["era"]
                death_year = result.get("author_death")
                if death_year:
                    era = EraClassifier.classify(death_year)  # Phase 6: Shared utility
                    if isinstance(era_filter, list):
                        if era not in era_filter:
                            match = False
                    elif era != era_filter:
                        match = False
                else:
                    match = False  # No death year, can't classify era

            if match:
                filtered.append(result)

        return filtered

    def _keyword_search(
        self,
        query: str,
        results: list[dict]
    ) -> dict[int, float]:
        """
        Score results by keyword matching.

        Simple BM25-like scoring based on term frequency.

        Args:
            query: Query text
            results: Semantic search results

        Returns:
            Dict of {result_id: keyword_score}
        """
        # Extract Arabic keywords from query
        keywords = self._extract_keywords(query)

        if not keywords:
            return {}

        scores = {}
        for result in results:
            content = result.get("content", "").lower()
            score = 0.0

            for keyword in keywords:
                if keyword in content:
                    # Count occurrences
                    count = content.count(keyword)
                    # TF-IDF-like score
                    score += count / (len(content) / 1000)

            if score > 0:
                scores[result["id"]] = score

        return scores

    def _reciprocal_rank_fusion(
        self,
        semantic_results: list[dict],
        keyword_scores: dict[int, float],
        top_k: int
    ) -> list[dict]:
        """
        Combine semantic and keyword results using reciprocal rank fusion.

        Formula: score = 1 / (k + rank_semantic) + 1 / (k + rank_keyword)

        Args:
            semantic_results: Ranked semantic results
            keyword_scores: Keyword scores by ID
            top_k: Number of final results

        Returns:
            Fused and ranked results
        """
        # Build rank maps
        semantic_ranks = {r["id"]: i for i, r in enumerate(semantic_results)}
        keyword_ranks = {id_: i for i, (id_, _) in enumerate(
            sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        )}

        # Calculate fused scores
        all_ids = set(semantic_ranks.keys()) | set(keyword_ranks.keys())
        fused_scores = {}

        for id_ in all_ids:
            score = 0.0

            # Semantic component
            if id_ in semantic_ranks:
                score += 1.0 / (self.k + semantic_ranks[id_])

            # Keyword component
            if id_ in keyword_ranks:
                score += 1.0 / (self.k + keyword_ranks[id_])

            if score > 0:
                fused_scores[id_] = score

        # Sort by fused score
        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)

        # Build final results
        id_to_result = {r["id"]: r for r in semantic_results}
        final_results = []

        for id_ in sorted_ids[:top_k]:
            result = id_to_result.get(id_, {})
            result["hybrid_score"] = fused_scores[id_]
            final_results.append(result)

        return final_results

    def _extract_keywords(self, text: str) -> list[str]:
        """
        Extract keywords from Arabic/Islamic text.

        Removes stop words and short words.

        Args:
            text: Input text

        Returns:
            List of keywords
        """
        # Arabic stop words
        stop_words = {
            "في", "من", "على", "إلى", "عن", "هذا", "هذه", "الذي", "التي",
            "هو", "هي", "هم", "نحن", "أنا", "أنت", "ما", "لا", "قد",
            "و", "أو", "ثم", "لكن", "إذا", "إن", "أن", "هل",
        }

        # Split into words
        words = re.findall(r'[\u0600-\u06FF]+', text)

        # Filter stop words and short words
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords
