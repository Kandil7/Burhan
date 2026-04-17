"""
Fiqh Collection-Aware RAG Agent for Athar Islamic QA system.

This module provides the FiqhCollectionAgent with:
- Full RAG pipeline: query_intake → classify_intent → retrieve → rerank → verify → generate → cite
- Arabic text normalization
- Fiqh-specific intent classification
- Verification suite integration

Phase 2: FiqhAgent with full verification pipeline.
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

    - Unify different forms of alef (أ, إ, آ, ا) to ا
    - Unify different forms of ya (ى, ي, ئ) to ي
    - Normalize ta marbuta (ة) to ه
    - Remove extra whitespace

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
# Fiqh Intent Classification Keywords
# =============================================================================

# Keywords for FiqhHukm intent (rulings, halal/haram)
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

# Keywords for FiqhMasaail intent (questions, issues)
_MASAAIL_KEYWORDS = [
    "مسألة",
    "سؤال",
    "استشارة",
    "كيف",
    "ما حكم",
    "ما هو حكم",
    "ما حكم",
    "هل يجوز",
    "هل يجوز",
    "أيجوز",
    "هل يحل",
    "هل يحرم",
]


# =============================================================================
# Fiqh Collection Agent
# =============================================================================


class FiqhCollectionAgent(CollectionAgent):
    """
    Collection-Aware RAG Agent for Fiqh (Islamic Jurisprudence).

    Provides full RAG pipeline with:
    - Arabic text normalization
    - Fiqh-specific intent classification (FiqhHukm, FiqhMasaail)
    - Hybrid retrieval with reranking
    - Verification suite integration
    - Citation assembly

    Configuration (class-level):
        TOP_K_RETRIEVAL: Number of candidates to retrieve (default: 80)
        TOP_K_RERANK: Number of candidates after reranking (default: 5)
        SCORE_THRESHOLD: Minimum score for inclusion (default: 0.65)
        TEMPERATURE: LLM generation temperature (default: 0.15)
        MAX_TOKENS: Maximum tokens in response (default: 2048)
    """

    name = "fiqh_agent"
    COLLECTION = "fiqh"

    # Configuration overrides
    TOP_K_RETRIEVAL = 80
    TOP_K_RERANK = 5
    SCORE_THRESHOLD = 0.65
    TEMPERATURE = 0.15
    MAX_TOKENS = 2048

    # Fallback message for no passages
    NO_PASSAGES_MESSAGE = "لم أجد نصوصاً فقهية كافية للإجابة على سؤالك."

    # System prompt - Arabic
    SYSTEM_PROMPT = """أنت مساعد إسلامي متخصص في الفقه الإسلامي.
    
التعليمات:
- استند حصراً إلى النصوص المسترجاعة المُقدَّمة
- استخدم مراجع المصادر [C1]، [C2]، ... بعد كل جملة
- اذكر المذهب الفقهي إن وُجد (حنفي، مالكي، شافعي، حنبلي)
- إذا تعارضت النصوص أو وُجد خلاف فقهي، اعرض الأقوال وأصحابها
- إذا كانت النصوص غير كافية، أقرّ بذلك بوضوح
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
        Initialize the Fiqh Collection Agent.

        Args:
            config: Optional CollectionAgentConfig (if None, built from strategy)
            embedding_model: Optional embedding model for query encoding
            vector_store: Optional vector store for retrieval
            llm_client: Optional LLM client for answer generation
        """
        # Build config from strategy if not provided
        if config is None:
            strategy = get_strategy_for_agent("fiqh_agent")
            verification_suite = build_verification_suite_for("fiqh_agent")
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

        Applies Arabic text normalization:
        - Unifies alef variants
        - Unifies ya variants
        - Normalizes ta marbuta
        - Removes extra whitespace

        Args:
            query: Raw user query

        Returns:
            Normalized query string
        """
        normalized = _normalize_arabic(query)

        # Log for debugging
        if normalized != query:
            # Could add logging here if needed
            pass

        return normalized

    # -------------------------------------------------------------------------
    # Intent Classification - Fiqh-specific
    # -------------------------------------------------------------------------

    def classify_intent(self, query: str) -> IntentLabel:
        """
        Classify query to Fiqh-specific intent.

        Uses keyword matching to determine:
        - FiqhHukm: for ruling questions (حكم, حلال, حرام, etc.)
        - FiqhMasaail: for general questions (مسألة, سؤال, etc.)
        - Unknown: if no keywords match

        Args:
            query: Normalized query string

        Returns:
            IntentLabel enum value
        """
        # Check for ruling keywords first (higher priority)
        for keyword in _HUKM_KEYWORDS:
            if keyword in query:
                return IntentLabel.FiqhHukm

        # Check for masaail keywords
        for keyword in _MASAAIL_KEYWORDS:
            if keyword in query:
                return IntentLabel.FiqhMasaail

        # Default to masaail for general questions
        return IntentLabel.FiqhMasaail

    # -------------------------------------------------------------------------
    # Retrieval - Hybrid Search
    # -------------------------------------------------------------------------

    async def retrieve_candidates(
        self,
        query: str,
    ) -> list[dict]:
        """
        Retrieve candidate passages from Fiqh collection.

        Uses vector store with hybrid search if available.
        Falls back to empty list if no vector store.

        Args:
            query: Normalized query string

        Returns:
            List of passage dictionaries with content, metadata, score
        """
        if not self.vector_store:
            return []

        top_k = self.strategy.top_k if self.strategy else self.TOP_K_RETRIEVAL

        try:
            # Try to use hybrid search if available
            # This assumes vector_store has a search method
            results = await self.vector_store.search(
                query=query,
                collection=self.COLLECTION,
                top_k=top_k,
            )

            # Convert to passage dict format if needed
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
            # Fallback to empty list on error
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

        If strategy.rerank is enabled, applies reranking logic.
        Otherwise returns top_k candidates as-is.

        Args:
            query: Original query
            candidates: List of candidate passages

        Returns:
            Reranked list of passage dictionaries
        """
        # Get threshold from strategy
        threshold = self.strategy.score_threshold if self.strategy else self.SCORE_THRESHOLD

        # Filter by score threshold
        filtered = [p for p in candidates if p.get("score", 0) >= threshold]

        # Get top_k from strategy or use default
        top_k = self.strategy.top_k if self.strategy and self.strategy.rerank else self.TOP_K_RERANK

        # Return top_k candidates
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

        Uses the verification suite configured for Fiqh agent:
        - quote_validator (abstain on failure)
        - source_attributor (warn on failure)
        - contradiction_detector (proceed on failure)
        - evidence_sufficiency (abstain on failure)

        Args:
            query: Original query
            candidates: List of candidate passages

        Returns:
            VerificationReport with verified passages
        """
        # Import here to avoid circular imports
        from src.verifiers.suite_builder import run_verification_suite

        # Get verification suite from config
        suite = self.config.verification_suite if self.config else None

        if suite:
            return run_verification_suite(
                suite=suite,
                query=query,
                candidates=candidates,
            )

        # Fallback: return all candidates as verified
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

        If no passages available, returns NO_PASSAGES_MESSAGE.
        Otherwise builds prompt and calls LLM if available.

        Args:
            query: Original query
            verified_passages: List of verified passage dictionaries
            language: Output language code (ar/en)

        Returns:
            Generated answer string
        """
        if not verified_passages:
            return self.NO_PASSAGES_MESSAGE

        # Format passages for prompt
        formatted = self._format_passages(verified_passages)

        # Build user prompt
        user_prompt = self.USER_PROMPT.format(
            query=query,
            language=language,
            passages=formatted,
            num_passages=len(verified_passages),
        )

        # Use LLM if available
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
                # Fallback to formatted passages
                pass

        # Fallback: return formatted passages
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

        Adds '…' on truncation if content > 500 chars.

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
        return f"<FiqhCollectionAgent: {self.name}, collection={self.COLLECTION}>"
