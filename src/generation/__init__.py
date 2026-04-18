"""
Generation module for Athar Islamic QA system.

This module handles the generation of responses based on verified evidence.
It ensures generation only consumes output from the verification layer.

Components:
- composers: Answer, citation, clarification, abstention composers
- prompts: Domain-specific prompt templates
- policies: Generation policies (formatting, risk, answer)
- schemas: Generation data models
- prompt_loader: Loads prompts from files
"""

from src.generation.schemas import (
    AnswerRequest,
    AnswerResponse,
    GenerationConfig,
    PromptTemplate,
)

from src.generation.composers.answer_composer import AnswerComposer
from src.generation.composers.citation_composer import CitationComposer
from src.generation.composers.clarification_composer import ClarificationComposer

__all__ = [
    # Schemas
    "AnswerRequest",
    "AnswerResponse",
    "GenerationConfig",
    "PromptTemplate",
    # Composers
    "AnswerComposer",
    "CitationComposer",
    "ClarificationComposer",
]
