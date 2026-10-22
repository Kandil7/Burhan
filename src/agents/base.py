"""
Base types for Burhan agents.

This module provides core types that were expected to be migrated from v1
but were never implemented. Re-exports from canonical locations.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

# One-release shims: these models moved to src.domain.models (Phase 2).
# Import from the domain home in new code; these aliases disappear after the
# next release.
from src.domain.models import AgentOutput as AgentOutput
from src.domain.models import Citation as Citation
from src.domain.models import VerificationReport as VerificationReport

# ============================================================================
# Agent Input
# ============================================================================


class AgentInput(BaseModel):
    """Standard input for agents."""

    query: str = Field(description="User query")
    language: str = Field(default="ar", description="Query language (ar/en)")
    collection: str | None = Field(default=None, description="Target collection")
    metadata: dict = Field(default_factory=dict)

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
    re.compile(
        r"<\s*(analysis|reasoning|thought|think)\s*>.*?(?:</\s*(?:analysis|reasoning|thought|think)\s*>)?\s*",
        re.IGNORECASE | re.DOTALL,
    ),
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
