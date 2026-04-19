"""
Collection-Aware RAG Agent Base for Athar Islamic QA system.

This module provides:
- IntentLabel: Enum for agent-specific intents
- Pydantic models for agent configuration
- Abstract CollectionAgent class with full RAG pipeline

Phase 1: Core Abstractions for Multi-Agent Collection-Aware RAG system.
This is the canonical base class for v2 agents.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

# Import Citation and AgentInput from canonical location (src/agents/base.py)
# This ensures Pydantic treats all Citation instances as the same type
from src.agents.base import AgentInput, Citation, strip_cot_leakage

# Lazy import to avoid circular imports
# Will be imported inside verify() method when needed


class AgentOutput(BaseModel):
    """Standardized output for all agents."""

    answer: str = Field(description="Agent answer text")
    citations: list[Citation] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_human_review: bool = Field(default=False)


class IntentLabel(str, Enum):
    """
    Agent-specific intents for Islamic knowledge domains.
    Each intent maps to a specific collection and retrieval strategy.
    """

    # Fiqh (Islamic Jurisprudence)
    FiqhHukm = "fiqh_hukm"  # Rulings, halal/haram
    FiqhMasaail = "fiqh_masaail"  # Issues and questions

    # Hadith
    HadithTakhrij = "hadith_takhrij"  # Hadith retrieval
    HadithSanad = "hadith_sanad"  # Chain of transmission
    HadithMatn = "hadith_matn"  # Hadith text analysis

    # Tafsir (Quran Interpretation)
    TafsirAyah = "tafsir_ayah"  # Verse interpretation
    TafsirMaqasid = "tafsir_maqasid"  # Themes and objectives

    # Aqeedah (Islamic Theology)
    AqeedahTawhid = "aqeedah_tawhid"  # Monotheism
    AqeedahIman = "aqeedah_iman"  # Faith concepts

    # Seerah (Prophet Biography)
    SeerahEvent = "seerah_event"  # Historical events
    SeerahMilad = "seerah_milad"  # Birth and life phases

    # Usul Fiqh (Principles of Jurisprudence)
    UsulFiqhIjtihad = "usul_fiqh_ijtihad"  # Ijtihad methodology
    UsulFiqhQiyas = "usul_fiqh_qiyas"  # Analogical reasoning

    # Islamic History
    IslamicHistoryEvent = "islamic_history_event"  # Historical events
    IslamicHistoryDynasty = "islamic_history_dynasty"  # Dynasties and eras

    # Arabic Language
    ArabicGrammar = "arabic_grammar"  # Nahw (syntax)
    ArabicMorphology = "arabic_morphology"  # Sarf (morphology)
    ArabicBalaghah = "arabic_balaghah"  # Rhetoric

    # Tazkiyah (Spiritual Development)
    TazkiyahSuluk = "tazkiyah_suluk"  # Spiritual conduct
    TazkiyahAkhlaq = "tazkiyah_akhlaq"  # Ethics

    # General
    GeneralIslamic = "general_islamic"  # General knowledge
    Unknown = "unknown"


class RetrievalStrategy(BaseModel):
    """
    Configuration for retrieval pipeline.
    Controls dense/sparse weighting, reranking, and thresholds.
    """

    dense_weight: float = Field(default=0.7, ge=0.0, le=1.0, description="Weight for dense (semantic) retrieval")
    sparse_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Weight for sparse (keyword) retrieval")
    top_k: int = Field(default=12, ge=1, le=100, description="Number of candidates to retrieve")
    rerank: bool = Field(default=True, description="Whether to apply reranking")
    score_threshold: float = Field(default=0.65, ge=0.0, le=1.0, description="Minimum score threshold for inclusion")


class VerificationCheck(BaseModel):
    """
    Individual verification check configuration.
    """

    name: str = Field(description="Check identifier")
    fail_policy: str = Field(default="abstain", description="Action on failure: abstain/warn/proceed")
    enabled: bool = Field(default=True, description="Whether check is active")


class VerificationSuite(BaseModel):
    """
    Collection of verification checks with fail-fast behavior.
    """

    checks: list[VerificationCheck] = Field(default_factory=list, description="List of verification checks")
    fail_fast: bool = Field(default=True, description="Stop on first failure if True")


class FallbackPolicy(BaseModel):
    """
    Fallback strategy when primary retrieval fails or is insufficient.
    """

    strategy: str = Field(default="chatbot", description="Strategy: chatbot/human_review/clarify")
    message: str | None = Field(default=None, description="Custom fallback message")


class CollectionAgentConfig(BaseModel):
    """
    Complete configuration for a CollectionAgent.
    """

    collection_name: str = Field(description="Qdrant collection name")
    strategy: RetrievalStrategy = Field(
        default_factory=RetrievalStrategy, description="Retrieval strategy configuration"
    )
    verification_suite: VerificationSuite = Field(
        default_factory=VerificationSuite, description="Verification suite configuration"
    )
    fallback_policy: FallbackPolicy = Field(default_factory=FallbackPolicy, description="Fallback policy configuration")


class VerificationReport(BaseModel):
    """
    Extended verification report with verified passages.
    Extends src.verifiers.base.VerificationReport with passage data.
    """

    is_verified: bool = Field(description="Overall verification status")
    confidence: float = Field(description="Overall confidence score", ge=0.0, le=1.0)
    issues: list[Any] = Field(default_factory=list, description="Verification issues")
    details: dict[str, Any] = Field(default_factory=dict, description="Detailed results")
    verified_passages: list[dict] = Field(default_factory=list, description="Passages that passed verification")

    @classmethod
    def from_passages(
        cls,
        passages: list[dict],
        is_verified: bool = True,
        confidence: float = 1.0,
        issues: list[Any] | None = None,
    ) -> VerificationReport:
        """
        Create a verification report from retrieved passages.

        Args:
            passages: List of passage dictionaries
            is_verified: Whether passages passed verification
            confidence: Confidence score
            issues: List of verification issues

        Returns:
            VerificationReport with verified passages
        """
        return cls(
            is_verified=is_verified,
            confidence=confidence,
            issues=issues or [],
            details={},
            verified_passages=passages,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "is_verified": self.is_verified,
            "confidence": self.confidence,
            "issues": self.issues,
            "details": self.details,
            "verified_passages_count": len(self.verified_passages),
        }


class CollectionAgent(ABC):
    """
    Abstract base class for collection-aware RAG agents.

    Provides the full pipeline:
    1. query_intake    - Normalize and prepare query
    2. classify_intent - Classify to agent-specific intent
    3. retrieve_candidates - Retrieve passages from collection
    4. rerank_candidates - Apply reranking
    5. run_verification - Verify candidates
    6. generate_answer - Generate answer from verified passages
    7. assemble_citations - Build citation references

    Subclasses MUST define:
        - COLLECTION: str (Qdrant collection name)
        - name: str (agent identifier)

    Optional:
        - config: CollectionAgentConfig instance

    Usage:
        class FiqhAgent(CollectionAgent):
            name = "fiqh_agent"
            COLLECTION = "fiqh"

            async def retrieve_candidates(self, query: str) -> list[dict]:
                # Implementation
                ...
    """

    name: str = "collection_agent"
    COLLECTION: str = ""

    def __init__(self, config: CollectionAgentConfig | None = None) -> None:
        """
        Initialize the agent with optional configuration.

        Args:
            config: CollectionAgentConfig instance
        """
        self.config = config or CollectionAgentConfig(
            collection_name=self.COLLECTION,
        )

    @abstractmethod
    def query_intake(self, query: str) -> str:
        """
        Normalize and prepare query for retrieval.

        Args:
            query: Raw user query

        Returns:
            Normalized query string
        """
        ...

    @abstractmethod
    def classify_intent(self, query: str) -> IntentLabel:
        """
        Classify query to agent-specific intent.

        Args:
            query: Normalized query

        Returns:
            IntentLabel enum value
        """
        ...

    @abstractmethod
    async def retrieve_candidates(
        self,
        query: str,
    ) -> list[dict]:
        """
        Retrieve candidate passages from the collection.

        Args:
            query: Normalized query string

        Returns:
            List of passage dictionaries with metadata
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    def assemble_citations(self, passages: list[dict]) -> list[Citation]:
        """
        Build citation references from passages.

        Args:
            passages: List of passage dictionaries

        Returns:
            List of Citation objects
        """
        ...

    # ==========================================
    # Shared Helpers (used by all agents)
    # ==========================================

    @staticmethod
    def _deduplicate_passages(passages: list[dict]) -> list[dict]:
        """
        Remove duplicate passages based on content similarity.

        Uses a hash of the first 200 characters to detect duplicates.
        """
        seen: set[int] = set()
        deduped: list[dict] = []
        for p in passages:
            content_hash = hash(p.get("content", "")[:200])
            if content_hash not in seen:
                seen.add(content_hash)
                deduped.append(p)
        return deduped

    @staticmethod
    def _load_shared_preamble() -> str:
        """
        Load the shared preamble prepended to all agent system prompts.
        Returns empty string on failure (prompt still works without it).
        """
        try:
            with open("prompts/_shared_preamble.txt", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return ""

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Adapter to support the standard agent interface.

        Args:
            input_data: AgentInput containing query, language, and metadata

        Returns:
            AgentOutput with answer, citations, and metadata
        """
        meta = input_data.metadata or {}
        if "language" not in meta:
            meta["language"] = input_data.language

        return await self.run(input_data.query, meta=meta)

    async def run(
        self,
        raw_question: str,
        meta: dict | None = None,
    ) -> AgentOutput:
        """
        Execute the full RAG pipeline end-to-end.
        """
        from src.generation.policies.answer_policy import AnswerMode, AnswerPolicy
        import time

        meta = meta or {}
        language = meta.get("language", "ar")
        timing: dict[str, int] = {}

        # Step 1: Query intake - normalize
        t0 = time.perf_counter()
        normalized = self.query_intake(raw_question)
        timing["intake_ms"] = int((time.perf_counter() - t0) * 1000)

        # Step 2: Classify intent
        t0 = time.perf_counter()
        intent = self.classify_intent(normalized)
        timing["classification_ms"] = int((time.perf_counter() - t0) * 1000)

        # Step 3: Retrieve candidates
        t0 = time.perf_counter()
        candidates = await self.retrieve_candidates(normalized)
        timing["retrieval_ms"] = int((time.perf_counter() - t0) * 1000)

        # Step 4: Rerank + deduplicate candidates
        t0 = time.perf_counter()
        ranked = await self.rerank_candidates(normalized, candidates)
        ranked = self._deduplicate_passages(ranked)
        timing["rerank_ms"] = int((time.perf_counter() - t0) * 1000)

        # Step 5: Run verification
        t0 = time.perf_counter()
        verification = await self.run_verification(normalized, ranked)
        timing["verification_ms"] = int((time.perf_counter() - t0) * 1000)

        # Track filtered evidence
        removed_count = len(candidates) - len(verification.verified_passages)
        if removed_count > 0:
            verification.confidence = min(verification.confidence, 0.90)
            verification.issues.append(
                {
                    "type": "evidence_filtered_out",
                    "removed_count": removed_count,
                    "message": f"تم استبعاد {removed_count} من المقاطع أثناء التصفية والتحقق من الأدلة.",
                }
            )

        # Step 6: Policy gate — determine answer mode
        policy = AnswerPolicy()
        has_evidence = len(verification.verified_passages) > 0

        answer_mode = policy.determine_mode(
            confidence=verification.confidence, verification_passed=verification.is_verified, has_evidence=has_evidence
        )

        if answer_mode == AnswerMode.ABSTAIN:
            abstain_msg = getattr(self, "NO_PASSAGES_MESSAGE", "عذراً، لم أجد في النصوص المتاحة ما يجيب على سؤالك.")
            return AgentOutput(
                answer=abstain_msg,
                citations=[],
                metadata={
                    "intent": intent.value,
                    "sub_intent": intent.value,
                    "collection": self.config.collection_name,
                    "answer_mode": "abstain",
                    "retrieved": len(candidates),
                    "verified": 0,
                    "is_verified": False,
                    "verification_confidence": 0.0 if not has_evidence else verification.confidence,
                    "verification_issues": verification.issues + (["No evidence found"] if not has_evidence else []),
                    "timing": timing,
                },
                confidence=0.0 if not has_evidence else verification.confidence,
                requires_human_review=True,
            )

        if answer_mode == AnswerMode.CLARIFY:
            clarify_msg = "سؤالك يحتمل أكثر من معنى. هل يمكنك توضيح سؤالك بشكل أدق حتى أتمكن من تقديم إجابة دقيقة؟"
            return AgentOutput(
                answer=clarify_msg,
                citations=[],
                metadata={
                    "intent": intent.value,
                    "collection": self.config.collection_name,
                    "answer_mode": "clarify",
                    "retrieved": len(candidates),
                    "verified": len(verification.verified_passages),
                    "is_verified": verification.is_verified,
                    "verification_confidence": verification.confidence,
                    "verification_issues": verification.issues,
                    "timing": timing,
                },
                confidence=verification.confidence,
                requires_human_review=False,
            )

        # Step 7: Generate answer + strip CoT leakage
        t0 = time.perf_counter()
        answer = await self.generate_answer(
            normalized,
            verification.verified_passages,
            language,
        )
        answer = strip_cot_leakage(answer)
        timing["generation_ms"] = int((time.perf_counter() - t0) * 1000)

        # Post-generation Grounding Check (lazy import to avoid circular)
        from src.verifiers.exact_quote import exact_quote_verifier
        from src.verifiers.source_attribution import source_attribution_verifier
        from src.verifiers.groundedness_judge import groundedness_judge

        quote_eval = await exact_quote_verifier.verify(answer, verification.verified_passages)
        if not quote_eval.passed:
            verification.issues.append(
                {
                    "type": "strict_grounding_violation",
                    "message": "Answer contains exact string quotes (verses, hadiths, or excerpts) not strictly grounded in passages.",
                    "details": quote_eval.details,
                }
            )
            verification.confidence = min(verification.confidence, 0.80)

        # Post-generation Source Attribution Check
        source_eval = await source_attribution_verifier.verify(answer, verification.verified_passages)
        if not source_eval.passed:
            verification.issues.append(
                {
                    "type": "source_attribution_violation",
                    "message": "Answer claims sources that are not present in the verified passages.",
                    "details": source_eval.details,
                }
            )
            verification.confidence = min(verification.confidence, 0.85)

        # Post-generation Speculative / Groundedness Check
        groundedness_eval = await groundedness_judge.verify(answer, verification.verified_passages)
        if not groundedness_eval.passed:
            verification.issues.append(
                {
                    "type": "speculative_answer",
                    "message": "Answer adds speculative or ungrounded factual claims beyond the provided evidence.",
                    "details": groundedness_eval.details,
                }
            )
            verification.confidence = min(verification.confidence, 0.70)

        # ==========================================
        # Auto-Healing for Quran (by Source Reference or Text Quote)
        # ==========================================
        invalid_sources = source_eval.details.get("invalid_sources", []) if not source_eval.passed else []
        failed_quotes = quote_eval.details.get("failed_quotes", []) if not quote_eval.passed else []

        if invalid_sources or failed_quotes:
            import asyncio
            from src.infrastructure.database import get_sync_session
            from src.quran.verse_retrieval import VerseRetrievalEngine
            from src.quran.quotation_validator import QuotationValidator

            def fetch_quran_healing():
                new_passages = []
                rem_sources = list(invalid_sources)
                rem_quotes = list(failed_quotes)

                with get_sync_session() as session:
                    engine = VerseRetrievalEngine(session)
                    validator = QuotationValidator(session)
                    
                    # Create a new event loop for this thread to run async Quran methods
                    new_loop = asyncio.new_event_loop()
                    try:
                        asyncio.set_event_loop(new_loop)
                        
                        # 1. Search by reference (e.g. "المائدة: 82")
                        for src in invalid_sources:
                            try:
                                v_info = new_loop.run_until_complete(engine.lookup(str(src), include_translation=False))
                                verses = v_info if isinstance(v_info, list) else [v_info]
                                
                                added = False
                                for v in verses:
                                    new_passages.append({
                                        "id": f"quran_{v['surah_number']}_{v['ayah_number']}",
                                        "text": v["text_uthmani"],
                                        "metadata": {
                                            "book": "القرآن الكريم",
                                            "source": f"سورة {v.get('surah_name_ar', '')}",
                                            "chapter": v.get("surah_name_ar", ""),
                                        }
                                    })
                                    added = True
                                if added and src in rem_sources:
                                    rem_sources.remove(src)
                            except Exception:
                                pass
                                
                        # 2. Search by text quote
                        for q_text in failed_quotes:
                            try:
                                val_res = new_loop.run_until_complete(validator.validate(str(q_text)))
                                if val_res.get("is_quran") and val_res.get("matched_ayah"):
                                    ayah = val_res["matched_ayah"]
                                    new_passages.append({
                                        "id": f"quran_{ayah['surah_number']}_{ayah['ayah_number']}",
                                        "text": ayah["text_uthmani"],
                                        "metadata": {
                                            "book": "القرآن الكريم",
                                            "source": f"سورة {ayah.get('surah_name_ar', ayah.get('surah_name_en', ''))}",
                                            "chapter": ayah.get("surah_name_ar", ayah.get("surah_name_en", "")),
                                        }
                                    })
                                    if q_text in rem_quotes:
                                        rem_quotes.remove(q_text)
                            except Exception:
                                pass
                                
                    finally:
                        new_loop.close()
                return new_passages, rem_sources, rem_quotes

            try:
                new_passages, rem_sources, rem_quotes = await asyncio.to_thread(fetch_quran_healing)
                if new_passages:
                    # Deduplicate before extending
                    existing_texts = {p.get("text", "") for p in verification.verified_passages}
                    added_new = False
                    for np in new_passages:
                        if np["text"] not in existing_texts:
                            verification.verified_passages.append(np)
                            existing_texts.add(np["text"])
                            added_new = True
                            
                    if added_new:
                        # Clean up issues if fully healed
                        if not rem_sources:
                            verification.issues = [i for i in verification.issues if i.get("type") != "source_attribution_violation"]
                        if not rem_quotes:
                            verification.issues = [i for i in verification.issues if i.get("type") != "strict_grounding_violation"]
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("quran_healing_error", error=str(e))

        # Step 8: Assemble citations
        citations = self.assemble_citations(verification.verified_passages)

        # Build metadata with timing breakdown
        output_meta = {
            "intent": intent.value,
            "sub_intent": intent.value,  # Agent-level sub-intent
            "collection": self.config.collection_name,
            "answer_mode": "answer",
            "retrieved": len(candidates),
            "verified": len(verification.verified_passages),
            "is_verified": verification.is_verified,
            "verification_confidence": verification.confidence,
            "verification_issues": verification.issues,
            "timing": timing,
        }

        # Determine if human review is needed
        requires_human_review = len(verification.verified_passages) == 0 or not verification.is_verified

        # Flag high-risk attribution for sensitive domains (e.g., seerah)
        has_source_violation = any(
            isinstance(issue, dict) and issue.get("type") == "source_attribution_violation"
            for issue in verification.issues
        )
        if has_source_violation and intent.value.startswith("seerah"):
            requires_human_review = True

        return AgentOutput(
            answer=answer,
            citations=citations,
            metadata=output_meta,
            confidence=verification.confidence,
            requires_human_review=requires_human_review,
        )

    def __repr__(self) -> str:
        return f"<CollectionAgent: {self.name}, collection={self.config.collection_name}>"
