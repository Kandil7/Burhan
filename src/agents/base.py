"""
Base types for Burhan agents.

This module provides core types that were expected to be migrated from v1
but were never implemented. Re-exports from canonical locations.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

# ============================================================================
# Citation - Re-export from domain
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
    def from_passage(cls, passage, index: int = 1) -> "Citation":
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


# ============================================================================
# Agent Input/Output
# ============================================================================


class AgentInput(BaseModel):
    """Standard input for agents."""

    query: str = Field(description="User query")
    language: str = Field(default="ar", description="Query language (ar/en)")
    collection: str | None = Field(default=None, description="Target collection")
    metadata: dict = Field(default_factory=dict)

    model_config = {"extra": "allow"}


class AgentOutput(BaseModel):
    """Standard output for agents."""

    answer: str = Field(description="Agent answer text")
    citations: list[Citation] = Field(default_factory=list)
    citation_chunks: list[dict[str, Any]] = Field(default_factory=list)  
    metadata: dict = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_human_review: bool = Field(default=False)

    model_config = {"extra": "allow"}

class BaseAgent:
    """Base class for agents (placeholder)."""

    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute the agent."""
        raise NotImplementedError


# ============================================================================
# Utility Functions
# ============================================================================

# Chain-of-thought markers to strip
_COT_PATTERNS = [
    re.compile(r"##?\s*(Analysis|Reasoning|Thought|Chain of Thought).*?\n\n", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*(analysis|reasoning|thought|think)\s*>.*?(?:</\s*(?:analysis|reasoning|thought|think)\s*>)?\s*", re.IGNORECASE | re.DOTALL),
    re.compile(r"^.*?<\/\s*(?:analysis|reasoning|thought|think)\s*>\s*", re.IGNORECASE | re.DOTALL),
    re.compile(r"###\s*(?:Let me|I'll|I will).*?\n\s*", re.IGNORECASE),
]


def strip_cot_leakage(text: str) -> str:
    """Remove chain-of-thought leakage from generated text.

    Strips patterns like:
    - "## Analysis\n...", "## Reasoning\n..."
    - <analysis>...</analysis>, <think>...</think>
    - "### Let me...\n"
    """
    if not text:
        return text

    result = text
    for pattern in _COT_PATTERNS:
        result = pattern.sub("", result)

    return result.strip()


__all__ = [
    "Citation",
    "AgentInput",
    "AgentOutput",
    "BaseAgent",
    "strip_cot_leakage",
    "VerificationReport",
]


# ============================================================================
# Verification Report
# ============================================================================


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
    ) -> "VerificationReport":
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
