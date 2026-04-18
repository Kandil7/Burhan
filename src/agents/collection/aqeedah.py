"""
Aqeedah (Islamic Theology) Collection Agent.

Uses YAML config from config/agents/aqeedah.yaml
"""

from __future__ import annotations

from src.agents.collection.base import (
    Citation,
    CollectionAgent,
    CollectionAgentConfig,
    FallbackPolicy,
    IntentLabel,
    RetrievalStrategy,
    VerificationReport,
)


def _normalize_arabic(text: str) -> str:
    import re

    text = re.compile(r"[إأآا]").sub("ا", text)
    text = re.compile(r"[ىئ]").sub("ي", text)
    text = re.compile(r"ة").sub("ه", text)
    text = re.compile(r"\s+").sub(" ", text).strip()
    return text


_AQEEDAH_TAWHID_KEYWORDS = ["توحيد", "الله", "أسماء", "صفات", "ربوبية", "ألوهيت"]
_AQEEDAH_IMAN_KEYWORDS = ["إيمان", "القرآن", "الملائكة", "الكتب", "الرسل", "اليوم الآخر"]


class AqeedahCollectionAgent(CollectionAgent):
    """Aqeedah (Islamic Theology) Collection Agent."""

    name = "aqeedah"
    COLLECTION = "aqeedah_passages"

    DEFAULT_STRATEGY = RetrievalStrategy(
        dense_weight=0.6,
        sparse_weight=0.4,
        top_k=10,
        rerank=True,
        score_threshold=0.15,
    )

    NO_PASSAGES_MESSAGE = "لم أجد نصوصاً في العقيدة الإسلامية مرتبطة بهذا السؤال."

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
        for keyword in _AQEEDAH_TAWHID_KEYWORDS:
            if keyword in query:
                return IntentLabel.AqeedaTawhid
        for keyword in _AQEEDAH_IMAN_KEYWORDS:
            if keyword in query:
                return IntentLabel.AqeedaIman
        return IntentLabel.AqeedaTawhid

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
            with open("prompts/aqeedah_agent.txt", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return """أنت متخصص في العقيدة الإسلامية (علم التوحيد).
استند حصراً إلى النصوص العقدية.
اذكر الدليل من القرآن والسنة.
Use مراجع المصادر [C1]، [C2]."""

    def _build_user_prompt(self, query: str, passages: str, language: str) -> str:
        return f"""السؤال العقدي: {query}
اللغة المطلوبة: {language}
النصوص العقدية:
{passages}
قدم الإجابة العقدية مع الاستشهاد."""

    def __repr__(self) -> str:
        return f"<AqeedahCollectionAgent: {self.name}, collection={self.COLLECTION}>"
