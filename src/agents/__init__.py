"""
Agents Module for Burhan Islamic QA system.

This module contains all AI agents for the system.

Submodules:
- base: Base types (Citation, AgentInput, AgentOutput)
- collection: Collection-aware RAG agents (v2 architecture)
- chatbot_agent: Main chatbot agent
"""

from src.agents.base import (
    AgentInput,
    AgentOutput,
    Citation,
)
from src.agents.collection import (
    AqeedahCollectionAgent,
    CollectionAgent,
    CollectionAgentConfig,
    FiqhCollectionAgent,
    HadithCollectionAgent,
    IntentLabel,
    SeerahCollectionAgent,
    TafsirCollectionAgent,
)

__all__ = [
    # Base types
    "AgentInput",
    "AgentOutput",
    "Citation",
    # Collection agents
    "CollectionAgent",
    "CollectionAgentConfig",
    "FiqhCollectionAgent",
    "HadithCollectionAgent",
    "TafsirCollectionAgent",
    "AqeedahCollectionAgent",
    "SeerahCollectionAgent",
    "IntentLabel",
]
