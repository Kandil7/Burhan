"""
Domain value objects for Burhan Islamic QA system.

This module is the single home for the models the layers share:

- ClassificationResult: value object produced by the intent classifier
- RoutingDecision: classification plus a resolved route
- Citation: source quote carried in agent answers
- AgentOutput: standard output for agents
- VerificationReport: verification summary attached to an answer
- VerificationStatus: status values for verification checks
- RetrievalResult: one retrieved row with its score

The former homes re-export these names with explicit aliases and lose those
shims after one release (docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md,
Phase 2). API DTOs in src/api/schemas keep their own models on purpose: the
26-path HTTP contract is frozen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.domain.intents import Intent, QuranSubIntent


@dataclass(frozen=True)
class ClassificationResult:
    """
    Pure domain value object produced by the intent classifier.

    Does NOT contain routing information — that is an application concern
    decided by RouterAgent based on this result.

    Attributes:
        intent: The classified primary intent
        confidence: Confidence score (0.0 - 1.0)
        language: Detected language ("ar" | "en" | "mixed")
        reasoning: Human-readable explanation of classification
        requires_retrieval: Whether this query needs document retrieval (RAG)
        method: Classification method used ("keyword" | "llm" | "embedding" | "fallback")
        quran_subintent: Optional sub-intent for Quran queries
        scores: Optional dictionary of intent scores for debugging
        subquestions: List of sub-questions if query is compound
    """

    intent: Intent
    confidence: float  # 0.0 – 1.0
    language: str  # "ar" | "en" | "mixed"
    reasoning: str
    requires_retrieval: bool
    method: str  # "keyword" | "llm" | "embedding" | "fallback"
    quran_subintent: QuranSubIntent | None = None
    scores: dict[str, float] | None = field(default=None)
    subquestions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate classification result after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if self.language not in ("ar", "en", "mixed"):
            raise ValueError(f"Language must be 'ar', 'en', or 'mixed', got {self.language}")
        if self.method not in ("keyword", "llm", "embedding", "fallback"):
            raise ValueError(f"Invalid method: {self.method}")


# ============================================================================
# Routing
# ============================================================================


@dataclass(frozen=True)
class RoutingDecision:
    """
    Application-level result: wraps ClassificationResult with a resolved
    route string and optional metadata for downstream agents.

    Route examples:
      "fiqh_agent"
      "hadith_agent"
      "quran:verse_lookup"
      "quran:nl2sql"
      "quran:interpretation_rag"
      "quran:quote_validation"

    Attributes:
        result: The underlying ClassificationResult
        route: Resolved route string for agent/tool dispatch
        agent_metadata: Optional metadata for downstream agents
    """

    result: ClassificationResult
    route: str
    agent_metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Agent types
# ============================================================================


class Citation(BaseModel):
    """Source citation for agent answers."""

    source_id: str = Field(description="Source document ID")
    text: str = Field(description="Quoted text from source")
    book_title: str | None = Field(default=None, description="Book title")
    page: int | None = Field(default=None, description="Page number")
    grade: str | None = Field(default=None, description="Hadith grade (sahih, hasan, daif)")
    url: str | None = Field(default=None, description="Source URL")
    metadata: dict = Field(default_factory=dict)

    model_config = {"extra": "allow"}

    @classmethod
    def from_passage(cls, passage: Any, index: int = 1) -> Citation:
        """Create Citation from RetrievalPassage.

        Args:
            passage: RetrievalPassage object or dict
            index: Citation number (e.g., 1 for [C1])

        Returns:
            Citation instance
        """
        # Handle different passage formats
        if isinstance(passage, dict):
            text = passage.get("content") or passage.get("text", str(passage))
            metadata = passage.get("metadata", {}) or {}
        else:
            text = getattr(passage, "content", getattr(passage, "text", str(passage)))
            metadata = getattr(passage, "metadata", {}) or {}

        # Build source_id like "C1", "C2", etc.
        source_id = f"C{index}"

        return cls(
            source_id=source_id,
            text=text[:200] if text else "",  # First 200 chars
            book_title=metadata.get("book_title"),
            page=metadata.get("page_number"),
            grade=metadata.get("grade"),
            url=metadata.get("url"),
            metadata=metadata,
        )


class AgentOutput(BaseModel):
    """Standard output for agents."""

    answer: str = Field(description="Agent answer text")
    citations: list[Citation] = Field(default_factory=list)
    citation_chunks: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_human_review: bool = Field(default=False)

    model_config = {"extra": "allow"}


class VerificationReport(BaseModel):
    """Results from verification."""

    status: str = Field(default="passed", description="passed/failed/abstained")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    verified_passages: list[str] = Field(default_factory=list)
    abstained: bool = Field(default=False)
    abstention_reason: str | None = Field(default=None)
    metadata: dict = Field(default_factory=dict)

    model_config = {"extra": "allow"}

    @classmethod
    def from_passages(
        cls,
        passages: list,
        is_verified: bool = True,
        confidence: float = 0.8,
    ) -> VerificationReport:
        """Create VerificationReport from list of passages.

        Args:
            passages: List of RetrievalPassage objects
            is_verified: Whether verification passed
            confidence: Confidence score

        Returns:
            VerificationReport instance
        """
        if not passages:
            return cls(
                status="abstained",
                confidence=0.0,
                abstention_reason="No passages provided",
                abstained=True,
            )

        verified = [getattr(p, "text", str(p))[:100] for p in passages]

        return cls(
            status="passed" if is_verified else "failed",
            confidence=confidence,
            verified_passages=verified,
            abstained=False,
        )


# ============================================================================
# Verification
# ============================================================================


class VerificationStatus(str, Enum):
    """Verification status values."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ABSTAINED = "abstained"
    WARNING = "warning"


# ============================================================================
# Retrieval
# ============================================================================


class RetrievalResult:
    """Structured retrieval result with metadata."""

    def __init__(
        self,
        content: str,
        source: str,
        score: float,
        metadata: dict | None = None,
    ):
        self.content = content
        self.source = source
        self.score = score
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "source": self.source,
            "score": self.score,
            "metadata": self.metadata,
        }
