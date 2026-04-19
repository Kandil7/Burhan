"""
Hadith Collection Agent.

This module provides the canonical v2 Hadith agent that uses:
- YAML config from config/agents/hadith.yaml
- System prompt from prompts/hadith_agent.txt
- DOMAIN_KEYWORDS-based routing

Special handling:
- Hadith grade verification (sahih, hasan, daif, mawdu)
- Exact text preservation (no hallucination)
- Sanad (chain) and Matn (text) extraction
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
from src.agents.base import strip_cot_leakage

# =============================================================================
# Arabic Text Normalization
# =============================================================================

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


# =============================================================================
# Hadith Intent Classification Keywords
# =============================================================================

_TAKHRIJ_KEYWORDS = ["حديث", "راوي", "مروي", "أخرج", "صحيح", "ضعيف", "مسلم", "بخاري"]
_SANAD_KEYWORDS = ["إسناد", "سند", "راوي", "الحديث"]
_MATN_KEYWORDS = ["متن", "الحديث", "قوله", "فعل"]


class HadithCollectionAgent(CollectionAgent):
    """
    Collection-Aware RAG Agent for Hadith (Prophetic traditions).

    Provides:
    - Exact text preservation (critical for hadith)
    - Hadith grade verification
    - Sanad and Matn extraction
    """

    name = "hadith"
    COLLECTION = "hadith_passages"

    # Default strategy - sparse-heavy for precise matching
    DEFAULT_STRATEGY = RetrievalStrategy(
        dense_weight=0.3,
        sparse_weight=0.7,
        top_k=10,
        rerank=True,
        score_threshold=0.50,
    )

    NO_PASSAGES_MESSAGE = "لم أجد أحاديث نبوية مرتبطة بهذا السؤال."

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
        """Normalize and prepare query for retrieval."""
        return _normalize_arabic(query)

    def classify_intent(self, query: str) -> IntentLabel:
        """Classify query to Hadith-specific intent."""
        for keyword in _TAKHRIJ_KEYWORDS:
            if keyword in query:
                return IntentLabel.HadithTakhrij
        for keyword in _SANAD_KEYWORDS:
            if keyword in query:
                return IntentLabel.HadithSanad
        for keyword in _MATN_KEYWORDS:
            if keyword in query:
                return IntentLabel.HadithMatn
        return IntentLabel.HadithTakhrij

    async def retrieve_candidates(self, query: str) -> list[dict]:
        """Retrieve candidate passages from Hadith collection."""
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

    async def rerank_candidates(self, query: str, candidates: list[dict]) -> list[dict]:
        """Rerank retrieved candidates."""
        threshold = self.strategy.score_threshold if self.strategy else 0.50
        filtered = [p for p in candidates if p.get("score", 0) >= threshold]
        # Deduplicate by content prefix
        filtered = self._deduplicate_passages(filtered)
        top_k = self.strategy.top_k if self.strategy and self.strategy.rerank else 5
        return filtered[:top_k]

    async def run_verification(self, query: str, candidates: list[dict]) -> VerificationReport:
        """Verify candidates with hadith-specific checks."""
        from src.verifiers.suite_builder import run_verification_suite

        suite = self.config.verification_suite if self.config else None

        if suite:
            return run_verification_suite(suite=suite, query=query, candidates=candidates)

        return VerificationReport.from_passages(
            passages=candidates,
            is_verified=True,
            confidence=0.8,
        )

    async def generate_answer(self, query: str, verified_passages: list[dict], language: str) -> str:
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
                    temperature=0.1,  # Low temperature for exact text preservation
                    max_tokens=1024,
                )
                raw_answer = response.choices[0].message.content
                return strip_cot_leakage(raw_answer)
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
        """Get system prompt from file with shared preamble."""
        preamble = self._load_shared_preamble()
        try:
            with open("prompts/hadith_agent.txt", encoding="utf-8") as f:
                agent_prompt = f.read()
        except FileNotFoundError:
            agent_prompt = """أنت متخصص في علم الحديث النبوي ورواياته.
تحذير مطلق: لا تختلق أي حديث أو إسناد.
استند حصراً إلى النصوص المسترجاعة.
اعرض الأحاديث حرفياً كما وردت.
اذكر درجة الحديث (صحيح، حسن، ضعيف، موضوع) إن وُجدت.
Use مراجع المصادر [C1]، [C2]، ... after each hadith."""
        if preamble:
            return f"{preamble}\n\n{agent_prompt}"
        return agent_prompt

    def _build_user_prompt(self, query: str, passages: str, language: str) -> str:
        """Build user prompt from template."""
        return f"""السؤال: {query}

اللغة المطلوبة: {language}

الأحاديث المسترجعة:
{passages}

اعرض الأحاديث المناسبة مع ذكر المصدر والدرجة."""

    def __repr__(self) -> str:
        return f"<HadithCollectionAgent: {self.name}, collection={self.COLLECTION}>"
