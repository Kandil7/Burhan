"""
Legacy Base RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/base.py (config-backed pattern)

This module provides the base RAG agent that all legacy agents inherit from.
It implements the full RAG pipeline: retrieve → score → enrich → generate → cite.

For new implementations, use CollectionAgent with YAML configs from config/agents/
"""

from __future__ import annotations

import re
from typing import Any

from src.agents.base import AgentInput, AgentOutput, BaseAgent, Citation
from src.config.logging_config import get_logger
from src.config.settings import settings
from src.knowledge.book_weighter import BookImportanceWeighter
from src.knowledge.hadith_grader import HadithAuthenticityGrader
from src.knowledge.hierarchical_retriever import HierarchicalRetriever
from src.knowledge.hybrid_search import HybridSearcher
from src.knowledge.title_loader import TitleLoader

logger = get_logger()

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _strip_thinking(text: str) -> str:
    return _THINK_RE.sub("", text).strip()


class BaseRAGAgent(BaseAgent):
    """
    Base class for all RAG-based agents.

    Subclasses MUST define:
        COLLECTION:    str  — Qdrant collection name
        SYSTEM_PROMPT: str  — system prompt (Arabic)
        USER_PROMPT:   str  — template with at minimum {query}, {language}, {passages}
                              optional: {num_passages}

    Optional class-level overrides:
        TOP_K_RETRIEVAL, TOP_K_RERANK, SCORE_THRESHOLD,
        TEMPERATURE, MAX_TOKENS, FALLBACK_MESSAGE
    """

    COLLECTION: str = ""
    SYSTEM_PROMPT: str = ""
    USER_PROMPT: str = ""
    TOP_K_RETRIEVAL: int = 12
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = 0.65  #  — canonical name used in execute()
    TEMPERATURE: float = 0.15
    MAX_TOKENS: int = 2048
    FALLBACK_MESSAGE: str = "النموذج غير متاح حالياً."
    NO_PASSAGES_MESSAGE: str = "لا توجد نصوص كافية للإجابة."

    def __init__(
        self,
        embedding_model=None,
        vector_store=None,
        llm_client=None,
    ) -> None:
        super().__init__()  # Initialize parent class
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.hybrid_searcher = HybridSearcher(vector_store) if vector_store else None
        self.hierarchical_retriever = HierarchicalRetriever()
        self.title_loader = TitleLoader()
        self.hadith_grader = HadithAuthenticityGrader()
        self.book_weighter = BookImportanceWeighter()

    # ── Public API ──────────────────────────────────────────────────────────

    async def execute(self, input: AgentInput) -> AgentOutput:
        if not self.embedding_model:
            return AgentOutput(
                answer=self.FALLBACK_MESSAGE,
                metadata={"error": "embedding_model not injected"},
                confidence=0.0,
                requires_human_review=True,
            )

        #  — guard against None metadata
        meta: dict[str, Any] = input.metadata or {}
        filters: dict[str, Any] | None = meta.get("filters")
        hierarchical: bool = bool(meta.get("hierarchical", False))

        try:
            query_embedding = await self.embedding_model.encode_query(input.query)

            # ── Retrieval ───────────────────────────────────────────────────
            retrieved_passages: list[dict] = []

            if self.hybrid_searcher:
                if hierarchical:
                    expanded = await self.hybrid_searcher.search_with_facets(
                        query=input.query,
                        query_embedding=query_embedding,
                        collection=self.COLLECTION,
                        top_k=self.TOP_K_RETRIEVAL * 3,
                        filters=filters,
                    )
                    hier = self.hierarchical_retriever.retrieve_hierarchical(
                        passages=expanded,
                        top_k_books=3,
                        top_k_pages_per_book=self.TOP_K_RERANK,
                    )
                    retrieved_passages = self.hierarchical_retriever.get_flat_passages(
                        hier, max_passages=self.TOP_K_RERANK
                    )
                elif filters:
                    retrieved_passages = await self.hybrid_searcher.search_with_facets(
                        query=input.query,
                        query_embedding=query_embedding,
                        collection=self.COLLECTION,
                        top_k=self.TOP_K_RETRIEVAL,
                        filters=filters,
                    )
                else:
                    retrieved_passages = await self.hybrid_searcher.search(
                        query=input.query,
                        query_embedding=query_embedding,
                        collection=self.COLLECTION,
                        top_k=self.TOP_K_RETRIEVAL,
                    )

            #  — uses self.SCORE_THRESHOLD (subclasses override THIS name)
            good_passages = [p for p in retrieved_passages if p.get("score", 0) >= self.SCORE_THRESHOLD][
                : self.TOP_K_RERANK
            ]

            # ── Enrich ──────────────────────────────────────────────────────
            if good_passages:
                good_passages = self.title_loader.enrich_passages(good_passages)
                good_passages = self.hadith_grader.enrich_passages_with_authenticity(good_passages)
                good_passages = self.book_weighter.weight_passages_by_importance(good_passages)

            # ── Generate ────────────────────────────────────────────────────
            raw_answer = await self._generate(input.query, good_passages, input.language)
            clean_answer = _strip_thinking(raw_answer)

            #  — Citation.from_passage() only; CitationNormalizer removed
            citations: list[Citation] = [Citation.from_passage(p, i) for i, p in enumerate(good_passages, 1)]

            return AgentOutput(
                answer=clean_answer,
                citations=citations,
                metadata={
                    "retrieved": len(retrieved_passages),
                    "used": len(good_passages),
                    "collection": self.COLLECTION,
                },
                confidence=self._calculate_confidence(good_passages),
                requires_human_review=len(good_passages) == 0,
            )

        except Exception as e:
            logger.error(f"{self.name}.execution_failed", error=str(e), exc_info=True)
            return AgentOutput(
                answer=self.FALLBACK_MESSAGE,
                confidence=0.0,
                metadata={"error": str(e)},
                requires_human_review=True,
            )

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _format_passages(self, passages: list[dict]) -> str:
        """— adds '…' on truncation."""
        if not passages:
            return ""
        parts = []
        for i, p in enumerate(passages, 1):
            content = p.get("content", "")
            if len(content) > 500:
                content = content[:500] + "…"
            parts.append(f"[C{i}] {content}")
        return "\n\n".join(parts)

    def _build_user_prompt(
        self,
        query: str,
        passages: list[dict],
        language: str,
    ) -> str:
        """
         + #6 — virtual method subclasses can override.
        Passes ALL known format variables so any USER_PROMPT template works.
        """
        formatted = self._format_passages(passages)
        fmt_vars = {
            "query": query,
            "language": language,
            "context": formatted,  # legacy alias
            "passages": formatted,  # GeneralIslamicAgent style
            "num_passages": len(passages),  #
        }
        try:
            return self.USER_PROMPT.format(**fmt_vars)
        except KeyError as e:
            logger.error(f"{self.name}.prompt_format_error", missing_key=str(e))
            return self.USER_PROMPT.format_map(_SafeDict(fmt_vars))

    async def _generate(self, query: str, passages: list[dict], language: str) -> str:
        """— accepts passages list, not pre-formatted string."""
        if not passages:
            return self.NO_PASSAGES_MESSAGE
        if not self.llm_client:
            return self._format_passages(passages)[:300]
        try:
            user_content = self._build_user_prompt(query, passages, language)
            response = await self.llm_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"{self.name}.generation_failed", error=str(e))
            return self.FALLBACK_MESSAGE

    def _calculate_confidence(self, passages: list[dict]) -> float:
        """— prefers score_vector (pure semantic) over hybrid score."""
        if not passages:
            return 0.0
        scores = [p.get("score_vector") or p.get("score", 0.0) for p in passages[:5]]
        return round(min(1.0, sum(scores) / len(scores)), 4)


class _SafeDict(dict):
    """Returns '{key}' for missing keys instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"
