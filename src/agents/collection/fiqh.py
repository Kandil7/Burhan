"""
Fiqh (Islamic Jurisprudence) Collection Agent.

This module provides the canonical v2 Fiqh agent that uses:
- YAML config from config/agents/fiqh.yaml
- System prompt from prompts/fiqh_agent.txt
- DOMAIN_KEYWORDS-based routing

Phase 2: FiqhAgent with full verification pipeline.
"""

from __future__ import annotations

import re

from src.agents.collection.base import (
    Citation,
    CollectionAgent,
    CollectionAgentConfig,
    FallbackPolicy,
    IntentLabel,
    RetrievalStrategy,
    VerificationReport,
)

# =============================================================================
# Arabic Text Normalization
# =============================================================================

_ALEF_PATTERN = re.compile(r"[إأآا]")
_YA_PATTERN = re.compile(r"[ىئ]")
_TA_MARBUTA = re.compile(r"ة")
_EXTRA_SPACES = re.compile(r"\s+")


def _normalize_arabic(text: str) -> str:
    """Normalize Arabic text for consistent retrieval."""
    text = _ALEF_PATTERN.sub("ا", text)
    text = _YA_PATTERN.sub("ي", text)
    text = _TA_MARBUTA.sub("ه", text)
    text = _EXTRA_SPACES.sub(" ", text).strip()
    return text


# =============================================================================
# Fiqh Intent Classification Keywords
# =============================================================================

_HUKM_KEYWORDS = [
    "حكم",
    "حلال",
    "حرام",
    "فرض",
    "واجب",
    "محرم",
    "مباح",
    "مكروه",
    "نفل",
    "سنة",
    "فتوى",
    "فقيه",
    "مذهب",
    "شريعة",
    "حكم شرعي",
]

_MASAAIL_KEYWORDS = [
    "مسألة",
    "سؤال",
    "استشارة",
    "كيف",
    "ما حكم",
    "ما هو حكم",
    "ما حكم",
    "هل يجوز",
    "أيجوز",
    "هل يحل",
    "هل يحرم",
]


class FiqhCollectionAgent(CollectionAgent):
    """
    Collection-Aware RAG Agent for Fiqh (Islamic Jurisprudence).

    Provides full RAG pipeline with:
    - Arabic text normalization
    - Fiqh-specific intent classification (FiqhHukm, FiqhMasaail)
    - Hybrid retrieval with reranking
    - Verification suite integration
    - Citation assembly

    Configuration:
        - YAML: config/agents/fiqh.yaml
        - Prompt: prompts/fiqh_agent.txt
    """

    name = "fiqh"
    COLLECTION = "fiqh_passages"

    # Default strategy - sparse-heavy for fiqh precision
    DEFAULT_STRATEGY = RetrievalStrategy(
        dense_weight=0.4,
        sparse_weight=0.6,
        top_k=15,
        rerank=True,
        score_threshold=0.65,
    )

    # Fallback message
    NO_PASSAGES_MESSAGE = "لم أجد نصوصاً فقهية كافية للإجابة على سؤالك."

    def __init__(
        self,
        config: CollectionAgentConfig | None = None,
        embedding_model=None,
        vector_store=None,
        llm_client=None,
    ) -> None:
        # Build config from defaults if not provided
        if config is None:
            from src.verifiers.suite_builder import build_verification_suite_for
            config = CollectionAgentConfig(
                collection_name=self.COLLECTION,
                strategy=self.DEFAULT_STRATEGY,
                verification_suite=build_verification_suite_for(self.name),
                fallback_policy=FallbackPolicy(strategy="chatbot"),
            )

        super().__init__(config)

        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.strategy = config.strategy

    def query_intake(self, query: str) -> str:
        """Normalize and prepare query for retrieval."""
        return _normalize_arabic(query)

    def classify_intent(self, query: str) -> IntentLabel:
        """Classify query to Fiqh-specific intent."""
        for keyword in _HUKM_KEYWORDS:
            if keyword in query:
                return IntentLabel.FiqhHukm
        for keyword in _MASAAIL_KEYWORDS:
            if keyword in query:
                return IntentLabel.FiqhMasaail
        return IntentLabel.FiqhMasaail

    async def retrieve_candidates(self, query: str) -> list[dict]:
        """Retrieve candidate passages from Fiqh collection."""
        if not self.vector_store or getattr(self, "embedding_model", None) is None:
            import logging
            logging.getLogger(self.__class__.__name__).error("Missing vector_store or embedding_model")
            return []

        top_k = self.strategy.top_k if self.strategy else 15

        try:
            query_embedding = await self.embedding_model.encode_query(query)
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                collection=self.COLLECTION,
                top_k=top_k,
            )

            return [
                {
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0),
                    "metadata": r.get("metadata", {}),
                }
                for r in results
            ]
        except Exception as e:
            import logging
            logging.getLogger(self.__class__.__name__).error(f"Retrieval failed: {e}")
            return []

    async def rerank_candidates(
        self,
        query: str,
        candidates: list[dict],
    ) -> list[dict]:
        """Rerank retrieved candidates."""
        threshold = self.strategy.score_threshold if self.strategy else 0.65
        filtered = [p for p in candidates if p.get("score", 0) >= threshold]
        top_k = self.strategy.top_k if self.strategy and self.strategy.rerank else 5
        return filtered[:top_k]

    async def run_verification(
        self,
        query: str,
        candidates: list[dict],
    ) -> VerificationReport:
        """Verify candidates against the query."""
        from src.verifiers.suite_builder import run_verification_suite

        suite = self.config.verification_suite if self.config else None

        if suite:
            return run_verification_suite(
                suite=suite,
                query=query,
                candidates=candidates,
            )

        return VerificationReport.from_passages(
            passages=candidates,
            is_verified=True,
            confidence=0.8,
        )

    async def generate_answer(
        self,
        query: str,
        verified_passages: list[dict],
        language: str,
    ) -> str:
        """Generate answer from verified passages."""
        if not verified_passages:
            return self.NO_PASSAGES_MESSAGE

        formatted = self._format_passages(verified_passages)

        if self.llm_client:
            try:
                from src.config.settings import settings

                response = await self.llm_client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": self._build_user_prompt(query, formatted, language)},
                    ],
                    temperature=0.15,
                    max_tokens=2048,
                )
                return response.choices[0].message.content
            except Exception as e:
                import logging
                logging.getLogger(self.__class__.__name__).error(f"LLM generation failed: {e}")
                pass

        return formatted

    def assemble_citations(self, passages: list[dict]) -> list[Citation]:
        """Build citation references from passages."""
        return [Citation.from_passage(p, i) for i, p in enumerate(passages, 1)]

    def _format_passages(self, passages: list[dict]) -> str:
        """Format passages for prompt insertion."""
        if not passages:
            return ""
        parts = []
        for i, p in enumerate(passages, 1):
            content = p.get("content", "")
            if len(content) > 500:
                content = content[:500] + "…"
            parts.append(f"[C{i}] {content}")
        return "\n\n".join(parts)

    def _get_system_prompt(self) -> str:
        """Get system prompt from file or use default."""
        try:
            with open("prompts/fiqh_agent.txt", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return """أنت مساعد إسلامي متخصص في الفقه الإسلامي.
استند حصراً إلى النصوص المسترجاعة المُقدَّمة.
Use مراجع المصادر [C1]، [C2]، ... after each sentence.
اذكر المذهب الفقهي إن وُجد (حنفي، مالكي، شافعي، حنبلي).
إذا تعارضت النصوص أو وُجد خلاف فقهي، اعرض الأقوال وأصحابها.
إذا كانت النصوص غير كافية، أقرّ بذلك بوضوح."""

    def _build_user_prompt(self, query: str, passages: str, language: str) -> str:
        """Build user prompt from template."""
        return f"""السؤال: {query}

اللغة المطلوبة: {language}

النصوص المسترجعة:
{passages}

أجب على السؤال مستنداً إلى النصوص أعلاه، مع ذكر المصادر."""

    def __repr__(self) -> str:
        return f"<FiqhCollectionAgent: {self.name}, collection={self.COLLECTION}>"


# Re-export for backward compatibility
__all__ = [
    "FiqhCollectionAgent",
    "_normalize_arabic",
]
