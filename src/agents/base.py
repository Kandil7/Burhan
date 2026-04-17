"""
Base Agent abstraction for Athar Islamic QA system.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """
    Normalized citation reference.
    Returned by every agent — mapped to CitationResponse at the API layer.
    """
    id:           str      = Field(description="Citation ID: C1, C2, C3, …")
    type:         str      = Field(description="quran | hadith | fatwa | fiqh_book | dua")
    source:       str      = Field(description="Normalized source name")
    reference:    str      = Field(description="Book / chapter / hadith number")
    url:          str | None = Field(default=None,  description="External URL")
    text_excerpt: str | None = Field(default=None,  description="Quoted passage (≤ 300 chars)")

    @classmethod
    def from_passage(cls, passage: dict, index: int) -> "Citation":
        meta = passage.get("metadata", {})

        # Infer type from collection or explicit metadata field
        collection  = meta.get("collection", "")
        source_type = meta.get("source_type") or (
            "hadith"    if "hadith"  in collection else
            "quran"     if "quran"   in collection else
            "seerah"    if "seerah"  in collection else
            "fiqh_book"
        )

        author     = meta.get("author", "")
        death_year = meta.get("author_death", "")
        page       = meta.get("page_number", "")

        ref_parts = filter(None, [
            author,
            f"ت {death_year} هـ" if death_year else "",
            f"ص{page}"           if page       else "",
        ])

        return cls(
            id=f"C{index}",
            type=source_type,                                          # ✅
            source=meta.get("book_title") or meta.get("author") or "مصدر إسلامي",
            reference=" — ".join(ref_parts),
            url=None,
            text_excerpt=passage.get("content", "")[:300] or None,
        )



class AgentInput(BaseModel):
    """Standardized input for all agents."""
    query:              str        = Field(description="User's question")
    language:           str        = Field(default="ar", description="ar | en")
    context:            dict | None = Field(default=None)
    retrieved_passages: list | None = Field(default=None)
    metadata:           dict       = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """Standardized output for all agents."""
    answer:               str           = Field(description="Agent answer text")
    citations:            list[Citation] = Field(default_factory=list)
    metadata:             dict           = Field(default_factory=dict)
    confidence:           float          = Field(default=1.0, ge=0.0, le=1.0)
    requires_human_review: bool          = Field(default=False)


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

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