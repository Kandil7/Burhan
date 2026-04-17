"""
Collection-Aware RAG Agent for Athar Islamic QA system.

This module provides:
- IntentLabel: Enum for agent-specific intents
- Pydantic models for agent configuration
- Abstract CollectionAgent class with full RAG pipeline

Phase 1: Core Abstractions for Multi-Agent Collection-Aware RAG system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.agents.base import AgentOutput, Citation


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
    issues: list[str] = Field(default_factory=list, description="Verification issues")
    details: dict[str, Any] = Field(default_factory=dict, description="Detailed results")
    verified_passages: list[dict] = Field(default_factory=list, description="Passages that passed verification")

    @classmethod
    def from_passages(
        cls,
        passages: list[dict],
        is_verified: bool = True,
        confidence: float = 1.0,
        issues: list[str] | None = None,
    ) -> "VerificationReport":
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
        - name: ClassVar[str] (agent identifier)

    Optional:
        - config: CollectionAgentConfig instance

    Usage:
        class FiqhCollectionAgent(CollectionAgent):
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

    async def run(
        self,
        raw_question: str,
        meta: dict | None = None,
    ) -> AgentOutput:
        """
        Execute the full RAG pipeline end-to-end.

        Pipeline steps:
        1. Normalize query (query_intake)
        2. Classify intent (classify_intent)
        3. Retrieve candidates (retrieve_candidates)
        4. Rerank candidates (rerank_candidates)
        5. Verify candidates (run_verification)
        6. Generate answer (generate_answer)
        7. Assemble citations (assemble_citations)

        Args:
            raw_question: Raw user question
            meta: Optional metadata (language, filters, etc.)

        Returns:
            AgentOutput with answer, citations, and metadata
        """
        meta = meta or {}
        language = meta.get("language", "ar")

        # Step 1: Query intake - normalize
        normalized = self.query_intake(raw_question)

        # Step 2: Classify intent
        intent = self.classify_intent(normalized)

        # Step 3: Retrieve candidates
        candidates = await self.retrieve_candidates(normalized)

        # Step 4: Rerank candidates
        ranked = await self.rerank_candidates(normalized, candidates)

        # Step 5: Run verification
        verification = await self.run_verification(normalized, ranked)

        # Step 6: Generate answer
        answer = await self.generate_answer(
            normalized,
            verification.verified_passages,
            language,
        )

        # Step 7: Assemble citations
        citations = self.assemble_citations(verification.verified_passages)

        # Build metadata
        output_meta = {
            "intent": intent.value,
            "collection": self.config.collection_name,
            "retrieved": len(candidates),
            "verified": len(verification.verified_passages),
            "is_verified": verification.is_verified,
            "verification_confidence": verification.confidence,
            "verification_issues": verification.issues,
        }

        # Determine if human review is needed
        requires_human_review = len(verification.verified_passages) == 0 or not verification.is_verified

        return AgentOutput(
            answer=answer,
            citations=citations,
            metadata=output_meta,
            confidence=verification.confidence,
            requires_human_review=requires_human_review,
        )

    def __repr__(self) -> str:
        return f"<CollectionAgent: {self.name}, collection={self.config.collection_name}>"
