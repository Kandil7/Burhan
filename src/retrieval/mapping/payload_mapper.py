"""
Payload Mapper for Retrieval Layer.

Maps Qdrant payload to canonical RetrievalPassage format.
"""

from __future__ import annotations

from typing import Any

from src.retrieval.schemas import RetrievalPassage


class PayloadMapper:
    """
    Maps raw Qdrant payloads to canonical RetrievalPassage format.

    Usage:
        mapper = PayloadMapper()
        passage = mapper.from_payload(payload)
    """

    @staticmethod
    def from_payload(
        payload: dict[str, Any],
        score: float = 0.0,
        collection: str = "",
    ) -> RetrievalPassage:
        """
        Convert Qdrant payload to RetrievalPassage.

        Args:
            payload: Raw payload from Qdrant
            score: Retrieval score
            collection: Collection name

        Returns:
            RetrievalPassage instance
        """
        content = payload.get("content", "")

        # Extract metadata, excluding content
        metadata = {k: v for k, v in payload.items() if k != "content"}

        return RetrievalPassage(
            content=content,
            score=score,
            score_vector=payload.get("score_vector"),
            score_sparse=payload.get("score_sparse"),
            rank=0,  # Will be set by reranker
            collection=collection,
            metadata=metadata,
        )

    @staticmethod
    def from_payloads(
        payloads: list[dict[str, Any]],
        scores: list[float],
        collection: str = "",
    ) -> list[RetrievalPassage]:
        """
        Convert multiple payloads to RetrievalPassage list.

        Args:
            payloads: List of payloads
            scores: List of scores (must match payloads length)
            collection: Collection name

        Returns:
            List of RetrievalPassage instances
        """
        if len(payloads) != len(scores):
            raise ValueError("Number of payloads must match number of scores")

        return [PayloadMapper.from_payload(p, s, collection) for p, s in zip(payloads, scores)]

    @staticmethod
    def to_payload(passage: RetrievalPassage) -> dict[str, Any]:
        """
        Convert RetrievalPassage to Qdrant payload.

        Args:
            passage: RetrievalPassage instance

        Returns:
            Qdrant-compatible payload dict
        """
        payload = {"content": passage.content}
        payload.update(passage.metadata)

        if passage.score_vector is not None:
            payload["score_vector"] = passage.score_vector
        if passage.score_sparse is not None:
            payload["score_sparse"] = passage.score_sparse

        return payload


__all__ = ["PayloadMapper"]
