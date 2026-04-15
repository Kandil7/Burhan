"""
Base RAG Agent for Athar Islamic QA system.

Phase 6 Refactoring:
- filters/hierarchical extracted from AgentInput.metadata (fixes silent bug)
- Citation.from_passage() replaces CitationNormalizer.enrich_citations()
- Double-normalization removed
"""
from __future__ import annotations

import re
from typing import Any

from src.agents.base import AgentInput, AgentOutput, BaseAgent, Citation
from src.config.logging_config import get_logger
from src.config.settings import settings
from src.core.citation import CitationNormalizer
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
        USER_PROMPT:   str  — with {query}, {language}, {context}

    Optional overrides:
        TOP_K_RETRIEVAL, TOP_K_RERANK, SCORE_THRESHOLD,
        TEMPERATURE, MAX_TOKENS, FALLBACK_MESSAGE
    """

    COLLECTION:          str   = ""
    SYSTEM_PROMPT:       str   = ""
    USER_PROMPT:         str   = ""
    TOP_K_RETRIEVAL:     int   = 12
    TOP_K_RERANK:        int   = 5
    SCORE_THRESHOLD:     float = 0.65
    TEMPERATURE:         float = 0.15
    MAX_TOKENS:          int   = 2048
    FALLBACK_MESSAGE:    str   = "النموذج غير متاح حالياً."
    NO_PASSAGES_MESSAGE: str   = "لا توجد نصوص كافية للإجابة."

    def __init__(
        self,
        embedding_model=None,
        vector_store=None,
        llm_client=None,
    ) -> None:
        self.embedding_model        = embedding_model
        self.vector_store           = vector_store
        self.llm_client             = llm_client
        self.hybrid_searcher        = HybridSearcher(vector_store) if vector_store else None
        self.hierarchical_retriever = HierarchicalRetriever()
        self.title_loader           = TitleLoader()
        self.hadith_grader          = HadithAuthenticityGrader()
        self.book_weighter          = BookImportanceWeighter()

    # ── Public API ────────────────────────────────────────────────────────────

    async def execute(self, input: AgentInput) -> AgentOutput:
        """
        RAG pipeline — filters and hierarchical flag read from input.metadata.

        query_router embeds them via build_agent_input():
            metadata={"filters": {...}, "hierarchical": True/False}
        """
        if not self.embedding_model:
            return AgentOutput(
                answer=self.FALLBACK_MESSAGE,
                metadata={"error": "embedding_model not injected"},
                confidence=0.0,
                requires_human_review=True,
            )

        # ── Extract routing params from metadata ──────────────────────────────
        filters:      dict[str, Any] | None = input.metadata.get("filters")
        hierarchical: bool                  = bool(input.metadata.get("hierarchical", False))

        try:
            query_embedding = await self.embedding_model.encode_query(input.query)

            # ── Retrieval ─────────────────────────────────────────────────────
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

            # ── Score filter ──────────────────────────────────────────────────
            good_passages = [
                p for p in retrieved_passages
                if p.get("score", 0) >= self.SCORE_THRESHOLD
            ][: self.TOP_K_RERANK]

            # ── Enrich ────────────────────────────────────────────────────────
            if good_passages:
                good_passages = self.title_loader.enrich_passages(good_passages)
                good_passages = self.hadith_grader.enrich_passages_with_authenticity(good_passages)
                good_passages = self.book_weighter.weight_passages_by_importance(good_passages)

            # ── Format ────────────────────────────────────────────────────────
            formatted_context = self._format_passages(good_passages)

            # ── Generate + strip thinking ─────────────────────────────────────
            raw_answer   = await self._generate(input.query, formatted_context, input.language)
            clean_answer = _strip_thinking(raw_answer)

            # ── Normalize inline citations [C1]… in answer text ───────────────
            normalizer   = CitationNormalizer()
            norm_answer  = normalizer.normalize(clean_answer)

            # ── Build typed Citation objects from passage metadata ────────────
            citations: list[Citation] = [
                Citation.from_passage(p, i)
                for i, p in enumerate(good_passages, 1)
            ]

            confidence = self._calculate_confidence(good_passages)

            return AgentOutput(
                answer=norm_answer,
                citations=citations,
                metadata={
                    "retrieved":  len(retrieved_passages),
                    "used":       len(good_passages),
                    "collection": self.COLLECTION,
                },
                confidence=confidence,
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

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _format_passages(self, passages: list[dict]) -> str:
        if not passages:
            return ""
        return "\n\n".join(
            f"[C{i}] {p.get('content', '')[:500]}"
            for i, p in enumerate(passages, 1)
        )

    async def _generate(self, query: str, context: str, language: str) -> str:
        if not context:
            return self.NO_PASSAGES_MESSAGE
        if not self.llm_client:
            return context[:300]
        try:
            response = await self.llm_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user",   "content": self.USER_PROMPT.format(
                        query=query, language=language, context=context,
                    )},
                ],
                temperature=self.TEMPERATURE,
                max_tokens=self.MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"{self.name}.generation_failed", error=str(e))
            return self.FALLBACK_MESSAGE

    def _calculate_confidence(self, passages: list[dict]) -> float:
        if not passages:
            return 0.0
        scores = [p.get("score", 0.0) for p in passages[:5]]
        return min(1.0, sum(scores) / len(scores))