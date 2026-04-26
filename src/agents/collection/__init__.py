"""
Collection Agents - Canonical v2 Agents.

This package contains the config-backed CollectionAgent implementations.
These are the canonical agents for Burhan v2 architecture.
"""

from src.agents.collection.aqeedah import AqeedahCollectionAgent
from src.agents.collection.base import (
    CollectionAgent,
    CollectionAgentConfig,
    FallbackPolicy,
    RetrievalStrategy,
    VerificationCheck,
    VerificationReport,
    VerificationSuite,
)

# Import domain agents
from src.agents.collection.fiqh import FiqhCollectionAgent
from src.agents.collection.general import GeneralCollectionAgent
from src.agents.collection.hadith import HadithCollectionAgent
from src.agents.collection.history import HistoryCollectionAgent
from src.agents.collection.language import LanguageCollectionAgent
from src.agents.collection.seerah import SeerahCollectionAgent
from src.agents.collection.tafsir import TafsirCollectionAgent
from src.agents.collection.tazkiyah import TazkiyahCollectionAgent
from src.agents.collection.usul_fiqh import UsulFiqhCollectionAgent

__all__ = [
    # Base classes
    "CollectionAgent",
    "CollectionAgentConfig",
    "RetrievalStrategy",
    "VerificationSuite",
    "VerificationCheck",
    "FallbackPolicy",
    "VerificationReport",
    # Domain agents
    "FiqhCollectionAgent",
    "HadithCollectionAgent",
    "TafsirCollectionAgent",
    "AqeedahCollectionAgent",
    "SeerahCollectionAgent",
    "UsulFiqhCollectionAgent",
    "HistoryCollectionAgent",
    "LanguageCollectionAgent",
    "TazkiyahCollectionAgent",
    "GeneralCollectionAgent",
]
