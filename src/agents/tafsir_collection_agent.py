"""
Tafsir Collection-Aware RAG Agent for Athar Islamic QA system.

This module provides the TafsirCollectionAgent with:
- Full RAG pipeline: query_intake → classify_intent → retrieve → rerank → verify → generate → cite
- Arabic text normalization
- Tafsir-specific intent classification (TafsirAyah, TafsirMaqasid)
- Verification suite integration

Phase 6: Skeleton Agents for Other Domains - Tafsir Collection Agent.
"""

from __future__ import annotations

import re
from typing import Any

from src.agents.base import AgentInput, AgentOutput, Citation
from src.agents.collection_agent import (
    CollectionAgent,
    CollectionAgentConfig,
    IntentLabel,
    VerificationReport,
)
from src.retrieval.strategies import get_strategy_for_agent
from src.verifiers.suite_builder import build_verification_suite_for


# =============================================================================
# Arabic Text Normalization
# =============================================================================

# Regex patterns for Arabic text normalization
_ALEF_PATTERN = re.compile(r"[إأآا]")
_YA_PATTERN = re.compile(r"[ىئ]")
_TA_MARBUTA = re.compile(r"ة")
_EXTRA_SPACES = re.compile(r"\s+")


def _normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for consistent retrieval.

    Args:
        text: Arabic text to normalize

    Returns:
        Normalized Arabic text
    """
    # Unify alef variants
    text = _ALEF_PATTERN.sub("ا", text)
    # Unify ya variants
    text = _YA_PATTERN.sub("ي", text)
    # Normalize ta marbuta
    text = _TA_MARBUTA.sub("ه", text)
    # Remove extra whitespace
    text = _EXTRA_SPACES.sub(" ", text).strip()
    return text


# =============================================================================
# Tafsir Intent Classification Keywords
# =============================================================================

# Keywords for TafsirAyah intent (verse interpretation)
_TAFSIR_AYAH_KEYWORDS = [
    "آية",
    "القرآن",
    "الكريم",
    "القرءان",
    "تفسير",
    "فسير",
    "معنى",
    "بيان",
    "بيان",
    "البيان",
    "محكم",
    "متشابه",
    "ناسخ",
    "منسوخ",
    "محل",
    "مكي",
    "مدني",
    "سورة",
    "اية",
    "ايات",
    "يأيها",
    "الصلوات",
    "الرحمن",
]

# Keywords for TafsirMaqasid intent (themes and objectives)
_TAFSIR_MAQASID_KEYWORDS = [
    "مقصد",
    "مقاصد",
    "الحكمة",
    "الغرض",
    "الهدف",
    "الاهداف",
    "عبر",
    "عظة",
    "درس",
    "موعظة",
    "تشريع",
    "احكام",
    "حكم",
    "BCL",
    "BCL",
    "BCL",
    "BCL",
]


# =============================================================================
# Tafsir Collection Agent
# =============================================================================


class TafsirCollectionAgent(CollectionAgent):
    """
    Collection-Aware RAG Agent for Tafsir (Quran Interpretation).

    Provides full RAG pipeline with:
    - Arabic text normalization
    - Tafsir-specific intent classification (TafsirAyah, TafsirMaqasid)
    - Hybrid retrieval with reranking
    - Verification suite integration
    - Citation assembly

    Configuration (class-level):
        TOP_K_RETRIEVAL: Number of candidates to retrieve (default: 40)
        TOP_K_RERANK: Number of candidates after reranking (default: 5)
        SCORE_THRESHOLD: Minimum score for inclusion (default: 0.15)
        TEMPERATURE: LLM generation temperature (default: 0.15)
        MAX_TOKENS: Maximum tokens in response (default: 2048)
    """

    name = "tafsir_agent"
    COLLECTION = "quran"

    # Configuration overrides
    TOP_K_RETRIEVAL = 40
    TOP_K_RERANK = 5
    SCORE_THRESHOLD = 0.15
    TEMPERATURE = 0.15
    MAX_TOKENS = 2048

    # Fallback message for no passages
    NO_PASSAGES_MESSAGE = "لم أجد نصوص تفسيرية كافية للإجابة على سؤالك."

    # System prompt - Arabic
    SYSTEM_PROMPT = """أنت مساعد إسلامي متخصص في تفسير القرآن الكريم.

التعليمات:
- استند حصراً إلى النصوص التفسيرية المُقدَّمة
- استخدم مراجع المصادر [C1]، [C2]، ... بعد كل جملة
-اذكر اسم التفسير إن وُجد (الطبري، الكشاف، الميزان، إلخ)
-اذكر رقم الآية والسورة إن توفر
-إذا كانت هناك روايات متعددة للتفسير، اعرضها
-إذا كانت النصوص غير كافية، أقرّ بذلك بوضوح
- قدّم الإجابة باللغة المطلوبة (العربية أو الإنجليزية)"""

    # User prompt template
    USER_PROMPT = """السؤال: {query}

النصوص المسترجعة:
{passages}

عدد النصوص: {num_passages}

المطلوب: أجب على السؤال مستنداً إلى النصوص أعلاه، مع ذكر المصادر."""

    def __init__(
        self,
        config: CollectionAgentConfig | None = None,
        embedding_model=None,
        vector_store=None,
        llm_client=None,
    ) -> None:
        """
        Initialize the Tafsir Collection Agent.

        Args:
            config: Optional CollectionAgentConfig
            embedding_model: Optional embedding model
            vector_store: Optional vector store
            llm_client: Optional LLM client
        """
        # Build config from strategy if not provided
        if config is None:
            strategy = get_strategy_for_agent("tafsir_agent")
            verification_suite = build_verification_suite_for("tafsir_agent")
            config = CollectionAgentConfig(
                collection_name=self.COLLECTION,
                strategy=strategy,
                verification_suite=verification_suite,
            )

        super().__init__(config)

        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm_client = llm_client

        # Store strategy for easy access
        self.strategy = config.strategy

    # -------------------------------------------------------------------------
    # Query Intake - Arabic Normalization
    # -------------------------------------------------------------------------

    def query_intake(self, query: str) -> str:
        """
        Normalize and prepare query for retrieval.

        Args:
            query: Raw user query

        Returns:
            Normalized query string
        """
        normalized = _normalize_arabic(query)
        return normalized

    # -------------------------------------------------------------------------
    # Intent Classification - Tafsir-specific
    # -------------------------------------------------------------------------

    def classify_intent(self, query: str) -> IntentLabel:
        """
        Classify query to Tafsir-specific intent.

        Uses keyword matching to determine:
        - TafsirAyah: for verse interpretation (آية, تفسير, etc.)
        - TafsirMaqasid: for themes and objectives (مقصد, الحكمة, etc.)
        - Unknown: if no keywords match

        Args:
            query: Normalized query string

        Returns:
            IntentLabel enum value
        """
        # Check for maqasid keywords first (higher priority)
        for keyword in _TAFSIR_MAQASID_KEYWORDS:
            if keyword in query:
                return IntentLabel.TafsirMaqasid

        # Check for ayah keywords
        for keyword in _TAFSIR_AYAH_KEYWORDS:
            if keyword in query:
                return IntentLabel.TafsirAyah

        # Default to TafsirAyah for general tafsir queries
        return IntentLabel.TafsirAyah

    # -------------------------------------------------------------------------
    # Retrieval - Hybrid Search
    # -------------------------------------------------------------------------

    async def retrieve_candidates(
        self,
        query: str,
    ) -> list[dict]:
        """
        Retrieve candidate passages from Tafsir collection.

        Args:
            query: Normalized query string

        Returns:
            List of passage dictionaries with content, metadata, score
        """
        if not self.vector_store:
            return []

        top_k = self.strategy.top_k if self.strategy else self.TOP_K_RETRIEVAL

        try:
            results = await self.vector_store.search(
                query=query,
                collection=self.COLLECTION,
                top_k=top_k,
            )

            candidates = []
            for r in results:
                passage = {
                    "content": r.get("content", ""),
                    "score": r.get("score", 0.0),
                    "metadata": r.get("metadata", {}),
                }
                candidates.append(passage)

            return candidates

        except Exception:
            return []

    # -------------------------------------------------------------------------
    # Reranking
    # -------------------------------------------------------------------------

    async def rerank_candidates(
        self,
        query: str,
        candidates: list[dict],
    ) -> list[dict]:
        """
        Rerank retrieved candidates.

        Args:
            query: Original query
            candidates: List of candidate passages

        Returns:
            Reranked list of passage dictionaries
        """
        threshold = self.strategy.score_threshold if self.strategy else self.SCORE_THRESHOLD

        filtered = [p for p in candidates if p.get("score", 0) >= threshold]

        top_k = self.strategy.top_k if self.strategy and self.strategy.rerank else self.TOP_K_RERANK

        return filtered[:top_k]

    # -------------------------------------------------------------------------
    # Verification
    # -------------------------------------------------------------------------

    async def run_verification(
        self,
        query: str,
        candidates: list[dict],
    ) -> VerificationReport:
        """
        Verify candidates against the query.

        Args:
            query: Original query
            candidates: List of candidate passages

        Returns:
            VerificationReport with verified passages
        """
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

    # -------------------------------------------------------------------------
    # Answer Generation
    # -------------------------------------------------------------------------

    async def generate_answer(
        self,
        query: str,
        verified_passages: list[dict],
        language: str,
    ) -> str:
        """
        Generate answer from verified passages.

        Args:
            query: Original query
            verified_passages: List of verified passage dictionaries
            language: Output language code (ar/en)

        Returns:
            Generated answer string
        """
        if not verified_passages:
            return self.NO_PASSAGES_MESSAGE

        formatted = self._format_passages(verified_passages)

        user_prompt = self.USER_PROMPT.format(
            query=query,
            language=language,
            passages=formatted,
            num_passages=len(verified_passages),
        )

        if self.llm_client:
            try:
                from src.config.settings import settings

                response = await self.llm_client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.TEMPERATURE,
                    max_tokens=self.MAX_TOKENS,
                )
                return response.choices[0].message.content
            except Exception:
                pass

        return formatted

    # -------------------------------------------------------------------------
    # Citation Assembly
    # -------------------------------------------------------------------------

    def assemble_citations(self, passages: list[dict]) -> list[Citation]:
        """
        Build citation references from passages.

        Args:
            passages: List of passage dictionaries

        Returns:
            List of Citation objects
        """
        return [Citation.from_passage(p, i) for i, p in enumerate(passages, 1)]

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _format_passages(self, passages: list[dict]) -> str:
        """
        Format passages for prompt insertion.

        Args:
            passages: List of passage dictionaries

        Returns:
            Formatted string with [C1], [C2], etc.
        """
        if not passages:
            return ""

        parts = []
        for i, p in enumerate(passages, 1):
            content = p.get("content", "")
            if len(content) > 500:
                content = content[:500] + "…"
            parts.append(f"[C{i}] {content}")

        return "\n\n".join(parts)

    def __repr__(self) -> str:
        return f"<TafsirCollectionAgent: {self.name}, collection={self.COLLECTION}>"
