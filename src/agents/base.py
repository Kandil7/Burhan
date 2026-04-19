"""
Base types for Athar agents.

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
    re.compile(r"##?\s*(Analysis|Reasoning|Thought|Chain of Thought).*?\\n\\n", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\\s*(analysis|reasoning|thought)\\s*>\\s*", re.IGNORECASE),
    re.compile(r"###\\s*(?:Let me|I'll|I will).*?\\n\\s*", re.IGNORECASE),
]


def strip_cot_leakage(text: str) -> str:
    """Remove chain-of-thought leakage from generated text.

    Strips patterns like:
    - "## Analysis\n...", "## Reasoning\n..."
    - <analysis>...</analysis>
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
]
