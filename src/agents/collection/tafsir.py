"""
Tafsir (Quran Interpretation) Collection Agent.

Uses YAML config from config/agents/tafsir.yaml
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

_ALEF_PATTERN = re.compile(r"[إأآا]")
_YA_PATTERN = re.compile(r"[ىئ]")
_TA_MARBUTA = re.compile(r"ة")
_EXTRA_SPACES = re.compile(r"\s+")


def _normalize_arabic(text: str) -> str:
    """Normalize Arabic text."""
    text = _ALEF_PATTERN.sub("ا", text)
    text = _YA_PATTERN.sub("ي", text)
    text = _TA_MARBUTA.sub("ه", text)
    text = _EXTRA_SPACES.sub(" ", text).strip()
    return text


_TAFSIR_AYAH_KEYWORDS = ["آية", "القرآن", "تفسير", "الايات", "سورة", "المصحف"]
_TAFSIR_MAQSAD_KEYWORDS = ["معنى", "الغرض", "الهدف", "ال寓意"]


class TafsirCollectionAgent(CollectionAgent):
    """Tafsir (Quran Interpretation) Collection Agent."""

    name = "tafsir"
    COLLECTION = "tafsir_passages"

    DEFAULT_STRATEGY = RetrievalStrategy(
        dense_weight=0.7,
        sparse_weight=0.3,
        top_k=12,
        rerank=True,
        score_threshold=0.15,
    )

    NO_PASSAGES_MESSAGE = "لم أجد تفسيراً للآية المطلوبة."

    def __init__(
        self,
        config: CollectionAgentConfig | None = None,
        embedding_model=None,
        vector_store=None,
        llm_client=None,
    ) -> None:
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
        return _normalize_arabic(query)

    def classify_intent(self, query: str) -> IntentLabel:
        for keyword in _TAFSIR_MAQSAD_KEYWORDS:
            if keyword in query:
                return IntentLabel.TafsirMaqasid
        for keyword in _TAFSIR_AYAH_KEYWORDS:
            if keyword in query:
                return IntentLabel.TafsirAyah
        return IntentLabel.TafsirAyah

    async def retrieve_candidates(self, query: str) -> list[dict]:
        if not self.vector_store or getattr(self, "embedding_model", None) is None:
            import logging
            logging.getLogger(self.__class__.__name__).error("Missing vector_store or embedding_model")
            return []
        top_k = self.strategy.top_k if self.strategy else 12
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
        threshold = self.strategy.score_threshold if self.strategy else 0.15
        filtered = [p for p in candidates if p.get("score", 0) >= threshold]
        top_k = self.strategy.top_k if self.strategy and self.strategy.rerank else 5
        return filtered[:top_k]

    async def run_verification(self, query: str, candidates: list[dict]) -> VerificationReport:
        from src.verifiers.suite_builder import run_verification_suite

        suite = self.config.verification_suite if self.config else None
        if suite:
            return run_verification_suite(suite=suite, query=query, candidates=candidates)
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
                    temperature=0.2,
                    max_tokens=2048,
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
            with open("prompts/tafsir_agent.txt", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return """أنت متخصص في تفسير القرآن الكريم.
استند حصراً إلى النصوص التفسيرية.
اذكر اسم المفسر والمصدر.
Use مراجع المصادر [C1]، [C2]."""

    def _build_user_prompt(self, query: str, passages: str, language: str) -> str:
        return f"""السؤال: {query}
اللغة المطلوبة: {language}
النصوص التفسيرية:
{passages}
قدم التفسير مع ذكر المصدر."""

    def __repr__(self) -> str:
        return f"<TafsirCollectionAgent: {self.name}, collection={self.COLLECTION}>"
