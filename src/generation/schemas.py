"""
Generation Schemas for Athar Islamic QA system.

Defines schemas for the generation layer.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AnswerStyle(str, Enum):
    """Answer style types."""

    FORMAL = "formal"  # Academic/formal style
    CASUAL = "casual"  # Conversational style
    EDUCATIONAL = "educational"  # Teaching style
    NARRATIVE = "narrative"  # Story-telling style


class GenerationRequest(BaseModel):
    """Request for answer generation."""

    query: str = Field(description="User query")
    language: str = Field(default="ar", description="Output language (ar/en)")
    passages: list[dict[str, Any]] = Field(
        default_factory=list, description="Verified passages to generate answer from"
    )
    style: AnswerStyle = Field(default=AnswerStyle.FORMAL, description="Answer style")
    max_length: int = Field(default=2048, description="Max tokens")
    temperature: float = Field(default=0.2, description="LLM temperature")


class GeneratedAnswer(BaseModel):
    """Generated answer with metadata."""

    answer: str = Field(description="Generated answer text")
    citations: list[dict[str, Any]] = Field(default_factory=list, description="Citations from passages")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    style: AnswerStyle = Field(description="Style used")
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptTemplate(BaseModel):
    """Prompt template configuration."""

    name: str = Field(description="Template name")
    system_prompt: str = Field(description="System prompt")
    user_template: str = Field(description="User prompt template with {placeholders}")
    required_variables: list[str] = Field(default_factory=list, description="Required template variables")


__all__ = [
    "AnswerStyle",
    "GenerationRequest",
    "GeneratedAnswer",
    "PromptTemplate",
]
