"""
Reciprocal Rank Fusion (RRF) for Retrieval.

RRF combines multiple ranked lists into a single ranked list.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.retrieval.schemas import RetrievalPassage


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion implementation.

    RRF formula: score(d) = sum(1 / (k + rank(d)))
    where k is a constant (typically 60) and rank(d) is the rank of document d in each list.

    Usage:
        rrf = ReciprocalRankFusion(k=60)
        fused = rrf.fuse([list1, list2, list3])
    """

    def __init__(self, k: int = 60):
        """
        Initialize RRF.

        Args:
            k: RRF k parameter (default 60)
        """
        self.k = k

    def fuse(
        self,
        rank_lists: list[list[RetrievalPassage]],
        score_key: str = "score",
    ) -> list[RetrievalPassage]:
        """
        Fuse multiple ranked lists into one.

        Args:
            rank_lists: List of ranked passage lists
            score_key: Key to use for passage identification

        Returns:
            Fused and re-ranked list of passages
        """
        if not rank_lists:
            return []

        if len(rank_lists) == 1:
            return rank_lists[0]

        # Track document scores
        doc_scores: dict[str, float] = defaultdict(float)
        doc_data: dict[str, RetrievalPassage] = {}

        # Process each ranked list
        for rank_list in rank_lists:
            for rank, passage in enumerate(rank_list, 1):
                # Use content hash as unique identifier
                doc_id = self._get_doc_id(passage)

                # Add RRF score
                doc_scores[doc_id] += 1.0 / (self.k + rank)

                # Store passage data (keep first encountered)
                if doc_id not in doc_data:
                    doc_data[doc_id] = passage

        # Sort by fused score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        # Build result with new ranks
        result = []
        for rank, (doc_id, score) in enumerate(sorted_docs, 1):
            passage = doc_data[doc_id]
            # Create new passage with updated rank and score
            fused_passage = RetrievalPassage(
                content=passage.content,
                score=score,
                score_vector=passage.score_vector,
                score_sparse=passage.score_sparse,
                rank=rank,
                collection=passage.collection,
                metadata=passage.metadata,
            )
            result.append(fused_passage)

        return result

    def _get_doc_id(self, passage: RetrievalPassage) -> str:
        """Generate unique document identifier."""
        # Use content hash as ID
        return str(hash(passage.content[:100]))

    def fuse_with_weights(
        self,
        rank_lists: list[list[RetrievalPassage]],
        weights: list[float],
    ) -> list[RetrievalPassage]:
        """
        Fuse ranked lists with custom weights.

        Args:
            rank_lists: List of ranked passage lists
            weights: Weights for each list (must match length)

        Returns:
            Fused and re-ranked list
        """
        if not rank_lists:
            return []

        if len(rank_lists) != len(weights):
            raise ValueError("Number of lists must match number of weights")

        doc_scores: dict[str, float] = defaultdict(float)
        doc_data: dict[str, RetrievalPassage] = {}

        for rank_list, weight in zip(rank_lists, weights):
            for rank, passage in enumerate(rank_list, 1):
                doc_id = self._get_doc_id(passage)
                doc_scores[doc_id] += weight * (1.0 / (self.k + rank))

                if doc_id not in doc_data:
                    doc_data[doc_id] = passage

        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        result = []
        for rank, (doc_id, score) in enumerate(sorted_docs, 1):
            passage = doc_data[doc_id]
            fused_passage = RetrievalPassage(
                content=passage.content,
                score=score,
                score_vector=passage.score_vector,
                score_sparse=passage.score_sparse,
                rank=rank,
                collection=passage.collection,
                metadata=passage.metadata,
            )
            result.append(fused_passage)

        return result


__all__ = ["ReciprocalRankFusion"]
