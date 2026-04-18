"""
Base Agent abstraction for Athar Islamic QA system.

DEPRECATED: Use src/agents/collection/base.py for the v2 config-backed architecture.
Migration: All agents should inherit from CollectionAgent instead of BaseAgent.

This module provides backward compatibility through __getattr__ for lazy deprecation warnings.
"""

from __future__ import annotations

import re

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel, Field


# Lazy deprecation handler - only warns when actually accessed
def __getattr__(name: str):
    """Lazy deprecation handler - warns only when deprecated items are accessed."""
    deprecated_items = {
        "BaseAgent": "src.agents.collection.base.CollectionAgent",
        "AgentInput": "src.agents.collection.base.AgentInput (not yet exported, use src.agents.base.AgentInput)",
        "AgentOutput": "src.agents.collection.base.AgentOutput (not yet exported, use src.agents.base.AgentOutput)",
        "Citation": "src.agents.base.Citation (still valid)",
    }

    if name in deprecated_items:
        import warnings

        new_path = deprecated_items[name]
        warnings.warn(
            f"src.agents.base.{name} is deprecated. Use {new_path} instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    # Raise AttributeError for unknown items to maintain normal Python behavior
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class Citation(BaseModel):
    """
    Normalized citation reference.
    Returned by every agent — mapped to CitationResponse at the API layer.
    """

    id: str = Field(description="Citation ID: C1, C2, C3, …")
    type: str = Field(description="quran | hadith | fatwa | fiqh_book | dua")
    source: str = Field(description="Normalized source name")
    reference: str = Field(description="Book / chapter / hadith number")
    url: str | None = Field(default=None, description="External URL")
    text_excerpt: str | None = Field(default=None, description="Quoted passage (≤ 300 chars)")

    @classmethod
    def from_passage(cls, passage: dict, index: int) -> Citation:
        meta = passage.get("metadata", {})

        # Infer type from collection or explicit metadata field
        collection = meta.get("collection", "")
        source_type = meta.get("source_type") or (
            "hadith"
            if "hadith" in collection
            else "quran"
            if "quran" in collection
            else "seerah"
            if "seerah" in collection
            else "tafsir"
            if "tafsir" in collection
            else "aqeedah"
            if "aqeedah" in collection
            else "fiqh_book"
        )

        author = meta.get("author", "")
        death_year = meta.get("author_death", "")
        page = meta.get("page_number", "")

        # Filter sentinel death year values (99999 = unknown/living)
        death_year_valid = ""
        if death_year:
            try:
                dy = int(death_year)
                if 0 < dy < 1500:
                    death_year_valid = str(dy)
            except (ValueError, TypeError):
                pass

        ref_parts = filter(
            None,
            [
                author,
                f"ت {death_year_valid} هـ" if death_year_valid else "",
                f"ص{page}" if page else "",
            ],
        )

        # Clean text excerpt: strip HTML, normalize whitespace
        raw_excerpt = passage.get("content", "")
        text_excerpt = _clean_text_excerpt(raw_excerpt) or None

        return cls(
            id=f"C{index}",
            type=source_type,
            source=meta.get("book_title") or meta.get("author") or "مصدر إسلامي",
            reference=" — ".join(ref_parts),
            url=None,
            text_excerpt=text_excerpt,
        )


# ============================================================================
# Shared Utilities
# ============================================================================

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MULTI_SPACE_RE = re.compile(r"\s+")


def _clean_text_excerpt(raw: str, max_chars: int = 300) -> str:
    """Clean text excerpt: strip HTML, normalize whitespace, truncate."""
    text = _HTML_TAG_RE.sub("", raw)
    text = text.replace("\r", "\n")
    text = _MULTI_SPACE_RE.sub(" ", text).strip()
    return text[:max_chars]


_COT_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_COT_PREAMBLE_RE = re.compile(
    r"^(Okay|Let me|I need to|First,|Looking at|I notice|I should|The user).*?\n\n",
    re.DOTALL,
)


def strip_cot_leakage(answer: str) -> str:
    """Strip LLM chain-of-thought leakage from generated answer.

    Removes:
    - <think>...</think> blocks
    - English preamble lines ("Okay, the user is asking...")
    """
    # Strip <think> blocks
    answer = _COT_THINK_RE.sub("", answer).strip()
    # Strip English reasoning preamble
    answer = _COT_PREAMBLE_RE.sub("", answer).strip()
    return answer


class AgentInput(BaseModel):
    """Standardized input for all agents."""

    query: str = Field(description="User's question")
    language: str = Field(default="ar", description="ar | en")
    context: dict | None = Field(default=None)
    retrieved_passages: list | None = Field(default=None)
    metadata: dict = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """Standardized output for all agents."""

    answer: str = Field(description="Agent answer text")
    citations: list[Citation] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_human_review: bool = Field(default=False)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    DEPRECATED: Use CollectionAgent from src/agents/collection/base.py instead.

    Usage:
        class FiqhAgent(BaseAgent):
            name = "fiqh_agent"

            async def execute(self, input: AgentInput) -> AgentOutput:
                return AgentOutput(answer="...", citations=[...])
    """

    # ClassVar — excluded from Pydantic field scanning
    name: ClassVar[str] = "base_agent"

    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute agent logic and return standardized result."""
        ...

    async def __call__(self, input: AgentInput | None = None, **kwargs) -> AgentOutput:
        """
        Allow agent to be called directly.

        Accepts either a pre-built AgentInput or raw kwargs:
            await agent(AgentInput(query="…"))
            await agent(query="…", language="ar")
        """
        if input is None:
            input = AgentInput(**kwargs)
        return await self.execute(input)

    def __repr__(self) -> str:
        return f"<Agent: {self.name}>"


# Backward compatibility - allow direct import of deprecated classes
# These will trigger the deprecation warning via __getattr__
__all__ = [
    "Citation",
    "AgentInput",
    "AgentOutput",
    "BaseAgent",
    "strip_cot_leakage",
    "_clean_text_excerpt",
]
