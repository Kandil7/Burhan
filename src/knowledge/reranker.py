"""
Cross-encoder reranker for improved retrieval quality.

Uses LLM-based reranking to improve retrieval precision
by re-scoring passages based on relevance to the query.

Phase 9: Added cross-encoder reranker.

Usage:
    reranker = CrossEncoderReranker(llm_client)
    reranked = await reranker.rerank(query, passages, top_k=5)
"""

from __future__ import annotations

from typing import Any

from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()


class RerankResult:
    """Reranked passage result."""

    def __init__(
        self,
        content: str,
        source: str,
        score: float,
        original_score: float,
        rank: int,
        metadata: dict | None = None,
    ):
        self.content = content
        self.source = source
        self.score = score
        self.original_score = original_score
        self.rank = rank
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "source": self.source,
            "rerank_score": self.score,
            "original_score": self.original_score,
            "rank": self.rank,
            "metadata": self.metadata,
        }


class CrossEncoderReranker:
    """
    Rerank retrieval results using LLM.

    Phase 9: Added LLM-based reranking.

    Args:
        llm_client: LLM client for scoring
        model: Model name
    """

    def __init__(
        self,
        llm_client: "LLMClient | None" = None,
        model: str | None = None,
    ):
        self.llm_client = llm_client
        self.model = model or settings.llm_model

    async def rerank(
        self,
        query: str,
        passages: list[dict[str, Any]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Rerank passages based on relevance to query.

        Args:
            query: Original query
            passages: Retrieved passages
            top_k: Number of results to return

        Returns:
            Reranked passages with scores
        """
        if not passages:
            return []

        if not self.llm_client:
            # Fall back to original scoring
            return passages[:top_k]

        try:
            # Build reranking prompt
            rerank_prompt = self._build_rerank_prompt(query, passages)

            # Get LLM to score each passage
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """أنت نموذج ترتيب متخصص في تقييم相关性 النصوص 
                        Given a query and passages, rank them by relevance from 1-10.
                        Return in format: [score1, score2, ...]""",
                    },
                    {
                        "role": "user",
                        "content": rerank_prompt,
                    },
                ],
                temperature=0.1,
                max_tokens=200,
            )

            # Parse scores
            scores = self._parse_scores(response.choices[0].message.content)

            # Apply scores to passages
            reranked = []
            for i, (passage, score) in enumerate(zip(passages, scores)):
                result = passage.copy()
                result["rerank_score"] = score
                result["rerank_rank"] = i + 1
                reranked.append(result)

            # Sort by rerank score
            reranked.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

            logger.info(
                "rerank.complete",
                query=query[:30],
                original_count=len(passages),
                reranked_count=len(reranked),
            )

            return reranked[:top_k]

        except Exception as e:
            logger.warning("rerank.failed", error=str(e))
            return passages[:top_k]

    def _build_rerank_prompt(
        self,
        query: str,
        passages: list[dict[str, Any]],
    ) -> str:
        """Build reranking prompt."""
        prompt = f"Query: {query}\n\n"

        for i, passage in enumerate(passages[:10], 1):  # Limit to 10
            content = passage.get("content", "")[:200]
            source = passage.get("source", "unknown")
            prompt += f"[{i}] Source: {source}\nContent: {content}\n\n"

        prompt += "Rate each passage 1-10 for relevance to the query. Return as comma-separated scores:"

        return prompt

    def _parse_scores(self, response: str) -> list[float]:
        """Parse scores from LLM response."""
        import re

        # Try to extract numbers
        numbers = re.findall(r"[\d.]+", response)

        if not numbers:
            return []

        scores = []
        for n in numbers:
            try:
                score = float(n)
                if 0 <= score <= 10:
                    scores.append(score / 10)  # Normalize to 0-1
            except ValueError:
                continue

        return scores


# ==========================================
# Simple Reranker (fallback)
# ==========================================


class SimpleReranker:
    """
    Simple reranker using keyword overlap.

    Fallback when LLM is not available.
    """

    def __init__(self):
        pass

    async def rerank(
        self,
        query: str,
        passages: list[dict[str, Any]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Rerank by keyword overlap."""
        import re

        # Extract query keywords
        query_keywords = set(re.findall(r"[\u0600-\u06FF]+", query.lower()))

        # Score each passage
        scored = []
        for passage in passages:
            content_keywords = set(re.findall(r"[\u0600-\u06FF]+", passage.get("content", "").lower()))

            # Calculate overlap
            overlap = len(query_keywords & content_keywords)
            score = overlap / max(len(query_keywords), 1)

            result = passage.copy()
            result["simple_rerank_score"] = score
            scored.append(result)

        # Sort by score
        scored.sort(key=lambda x: x.get("simple_rerank_score", 0), reverse=True)

        return scored[:top_k]


# ==========================================
# Hybrid Reranker
# ==========================================


class HybridReranker:
    """
    Hybrid reranker combining LLM and keyword scores.

    Combines deep relevance understanding with keyword matching.
    """

    def __init__(
        self,
        llm_client: "LLMClient | None" = None,
        use_llm: bool = True,
    ):
        self.llm_reranker = CrossEncoderReranker(llm_client) if use_llm else None
        self.simple_reranker = SimpleReranker()

    async def rerank(
        self,
        query: str,
        passages: list[dict[str, Any]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Rerank with hybrid approach."""
        if not passages:
            return []

        # Get simple scores first
        simple_reranked = await self.simple_reranker.rerank(query, passages, top_k=top_k * 2)

        if self.llm_reranker:
            # Use LLM reranker if available
            llm_reranked = await self.llm_reranker.rerank(query, passages, top_k=top_k * 2)

            # Combine scores
            reranked = []
            for p1, p2 in zip(simple_reranked, llm_reranked):
                combined = p1.copy()
                simple_score = p1.get("simple_rerank_score", 0)
                llm_score = p2.get("rerank_score", 0)
                combined["hybrid_score"] = (simple_score * 0.3) + (llm_score * 0.7)
                reranked.append(combined)

            # Sort by combined score
            reranked.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)
            return reranked[:top_k]

        return simple_reranked[:top_k]
