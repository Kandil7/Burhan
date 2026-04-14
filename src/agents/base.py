"""
Base Agent abstraction for Athar Islamic QA system.

All agents (Fiqh, Quran, General Islamic, etc.) inherit from BaseAgent
and implement the execute() method with standardized input/output.
"""
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """
    Normalized citation reference.

    Every agent returns citations in this standardized format,
    which are then normalized to [C1], [C2], etc. for display.
    """
    id: str = Field(description="Citation ID: C1, C2, C3, etc.")
    type: str = Field(description="Type: quran, hadith, fatwa, fiqh_book, dua")
    source: str = Field(description="Normalized source name")
    reference: str = Field(description="Specific reference (book, chapter, number)")
    url: str | None = Field(default=None, description="External URL (quran.com, sunnah.com)")
    text_excerpt: str | None = Field(default=None, description="Quoted passage")


class AgentInput(BaseModel):
    """
    Standardized input for all agents.

    Contains query text, language preference, optional context,
    and metadata from the intent classifier.
    """
    query: str = Field(description="User's question")
    language: str = Field(default="ar", description="Response language: ar or en")
    context: dict | None = Field(
        default=None,
        description="Conversation context (previous queries, user preferences)"
    )
    retrieved_passages: list | None = Field(
        default=None,
        description="Retrieved documents from RAG (if applicable)"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (location, madhhab, session_id)"
    )


class AgentOutput(BaseModel):
    """
    Standardized output for all agents.

    Contains answer, citations, and metadata for response assembly.
    """
    answer: str = Field(description="Agent's answer text")
    citations: list[Citation] = Field(
        default_factory=list,
        description="List of citations with structured references"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Metadata (agent name, processing time, madhhab, etc.)"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the answer (0.0-1.0)"
    )
    requires_human_review: bool = Field(
        default=False,
        description="Flag if this response needs scholarly review"
    )


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Agents handle queries requiring knowledge retrieval, reasoning,
    or text generation. Examples: FiqhAgent, QuranAgent, GeneralIslamicAgent.

    Usage:
        class FiqhAgent(BaseAgent):
            name = "fiqh_agent"

            async def execute(self, input: AgentInput) -> AgentOutput:
                # Implementation
                return AgentOutput(answer="...", citations=[...])

        agent = FiqhAgent()
        result = await agent.execute(AgentInput(query="ما حكم الصلاة؟"))
    """

    name: str = "base_agent"

    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        """
        Execute agent logic and return result.

        Args:
            input: Standardized agent input with query and metadata

        Returns:
            AgentOutput with answer, citations, and metadata
        """
        pass

    async def __call__(self, **kwargs) -> AgentOutput:
        """Allow agent to be called directly like a function."""
        input_data = AgentInput(**kwargs)
        return await self.execute(input_data)

    def __repr__(self) -> str:
        return f"<Agent: {self.name}>"
