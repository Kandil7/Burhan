"""
General Islamic Knowledge Collection Agent.

Uses YAML config from config/agents/general.yaml

This is the fallback agent for questions that don't match specific domains.
"""

from __future__ import annotations

from src.agents.collection.base import Citation
from src.agents.collection.base import (
    CollectionAgent,
    CollectionAgentConfig,
    IntentLabel,
    RetrievalStrategy,
    VerificationSuite,
    FallbackPolicy,
    VerificationReport,
)


def _normalize_arabic(text: str) -> str:
    import re

    text = re.compile(r"[إأآا]").sub("ا", text)
    text = re.compile(r"[ىئ]").sub("ي", text)
    text = re.compile(r"ة").sub("ه", text)
    text = re.compile(r"\s+").sub(" ", text).strip()
    return text


class GeneralCollectionAgent(CollectionAgent):
    """General Islamic Knowledge Collection Agent (Fallback)."""

    name = "general"
    COLLECTION = "general_islamic"

    DEFAULT_STRATEGY = RetrievalStrategy(
        dense_weight=0.7,
        sparse_weight=0.3,
        top_k=10,
        rerank=True,
        score_threshold=0.35,
    )

    NO_PASSAGES_MESSAGE = "لم أجد في المصادر المتاحة ما يُجيب على هذا السؤال بدقة."

    def __init__(
        self,
        config: CollectionAgentConfig | None = None,
        embedding_model=None,
        vector_store=None,
        llm_client=None,
    ) -> None:
        if config is None:
            config = CollectionAgentConfig(
                collection_name=self.COLLECTION,
                strategy=self.DEFAULT_STRATEGY,
                verification_suite=VerificationSuite(checks=[], fail_fast=False),
                fallback_policy=FallbackPolicy(strategy="chatbot"),
            )

        super().__init__(config)

        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.strategy = config.strategy

    def query_intake(self, query: str) -> str:
        return _normalize_arabic(query)

    def classify_intent(self, query: str) -> IntentLabel:
        return IntentLabel.GeneralIslamic

    async def retrieve_candidates(self, query: str) -> list[dict]:
        if not self.vector_store or getattr(self, "embedding_model", None) is None:
            import logging
            logging.getLogger(self.__class__.__name__).error("Missing vector_store or embedding_model")
            return []
        top_k = self.strategy.top_k if self.strategy else 10
        try:
            query_embedding = await self.embedding_model.encode_query(query)
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                collection=self.COLLECTION,
                top_k=top_k,
            )
            return [
                {"content": r.get("content", ""), "score": r.get("score", 0.0), "metadata": r.get("metadata", {})}
                for r in results
            ]
        except Exception as e:
            import logging
            logging.getLogger(self.__class__.__name__).error(f"Retrieval failed: {e}")
            return []

    async def rerank_candidates(self, query: str, candidates: list[dict]) -> list[dict]:
        threshold = self.strategy.score_threshold if self.strategy else 0.35
        filtered = [p for p in candidates if p.get("score", 0) >= threshold]
        top_k = self.strategy.top_k if self.strategy and self.strategy.rerank else 5
        return filtered[:top_k]

    async def run_verification(self, query: str, candidates: list[dict]) -> VerificationReport:
        return VerificationReport.from_passages(passages=candidates, is_verified=True, confidence=0.8)

    async def generate_answer(self, query: str, verified_passages: list[dict], language: str) -> str:
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
                    temperature=0.3,
                    max_tokens=1536,
                )
                return response.choices[0].message.content
            except Exception as e:
                import logging
                logging.getLogger(self.__class__.__name__).error(f"LLM generation failed: {e}")
                pass
        return formatted

    def assemble_citations(self, passages: list[dict]) -> list[Citation]:
        return [Citation.from_passage(p, i) for i, p in enumerate(passages, 1)]

    def _format_passages(self, passages: list[dict]) -> str:
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
        try:
            with open("prompts/general_agent.txt", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return """أنت معلم إسلامي متخصص.
استند حصراً إلى المصادر المُقدَّمة.
Use مراجع المصادر [C1]، [C2].
أضف السياق التاريخي أو الفقهي عند الاقتضاء.
إذا كانت المصادر غير كافية، قل ذلك بوضوح."""

    def _build_user_prompt(self, query: str, passages: str, language: str) -> str:
        return f"""السؤال: {query}
اللغة المطلوبة: {language}
المصادر المتاحة:
{passages}
قدم إجابة تعليمية مُنظَّمة."""

    def __repr__(self) -> str:
        return f"<GeneralCollectionAgent: {self.name}, collection={self.COLLECTION}>"
