"""
Hybrid Search for Athar Islamic QA system.

Combines semantic search (embeddings) with keyword search (BM25)
for better retrieval of Islamic texts.

Phase 4: Improves retrieval accuracy for fiqh and hadith queries.
"""
import re
from typing import Optional

import numpy as np

from src.knowledge.vector_store import VectorStore
from src.config.logging_config import get_logger

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
