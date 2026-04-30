"""
Domain layer for Burhan Islamic QA system.

This module contains domain value objects and business logic:
- citations: Citation domain models
- collections: Collection constants
- decisions: Decision domain models
- evidence: Evidence domain models
- intents: Intent enums and routing
- models: Generic domain models
"""

from src.config.constants import CollectionNames
from src.domain.citations import Citation, CitationChain, SourceAttribution
from src.domain.decisions import (
    AgentDecision,
    CollectionDecision,
    Decision,
    DecisionType,
    ResponseMode,
    ResponseModeDecision,
)
from src.domain.evidence import (
    Evidence,
    EvidenceSet,
    EvidenceType,
    GroundednessLevel,
    VerificationStatus,
)
from src.domain.intents import Intent, IntentLabel, QuranSubIntent
from src.domain.models import ClassificationResult

__all__ = [
    # Citations
    "Citation",
    "CitationChain",
    "SourceAttribution",
    # Collections (from config.constants)
    "CollectionNames",
    # Decisions
    "Decision",
    "DecisionType",
    "AgentDecision",
    "CollectionDecision",
    "ResponseMode",
    "ResponseModeDecision",
    # Evidence
    "Evidence",
    "EvidenceSet",
    "EvidenceType",
    "GroundednessLevel",
    "VerificationStatus",
    # Intents
    "Intent",
    "IntentLabel",
    "QuranSubIntent",
    # Models
    "ClassificationResult",
]
