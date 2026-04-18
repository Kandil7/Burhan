"""
Legacy Agents - DEPRECATED.

This package contains the deprecated legacy agents. They are kept for
backward compatibility during the v2 migration.

Migration Status:
- FiqhAgent -> src/agents/collection/fiqh (config-backed)
- HadithAgent -> src/agents/collection/hadith (config-backed)
- SeerahAgent -> src/agents/collection/seerah (config-backed)
- TafsirAgent -> src/agents/collection/tafsir (config-backed)
- AqeedahAgent -> src/agents/collection/aqeedah (config-backed)
- HistoryAgent -> src/agents/collection/history (config-backed)
- LanguageAgent -> src/agents/collection/language (config-backed)
- TazkiyahAgent -> src/agents/collection/tazkiyah (config-backed)
- UsulFiqhAgent -> src/agents/collection/usul_fiqh (config-backed)
- GeneralIslamicAgent -> src/agents/collection/general (config-backed)
- BaseRAGAgent -> src/agents/collection/base (config-backed)
"""

import warnings

# Show deprecation warning when importing from legacy
warnings.filterwarnings("default", category=DeprecationWarning, module="src.agents.legacy")

from src.agents.legacy.base_rag_agent import BaseRAGAgent
from src.agents.legacy.fiqh_agent import FiqhAgent
from src.agents.legacy.hadith_agent import HadithAgent
from src.agents.legacy.seerah_agent import SeerahAgent
from src.agents.legacy.tafsir_agent import TafsirAgent
from src.agents.legacy.aqeedah_agent import AqeedahAgent
from src.agents.legacy.history_agent import HistoryAgent
from src.agents.legacy.language_agent import LanguageAgent
from src.agents.legacy.tazkiyah_agent import TazkiyahAgent
from src.agents.legacy.usul_fiqh_agent import UsulFiqhAgent
from src.agents.legacy.general_islamic_agent import GeneralIslamicAgent

__all__ = [
    "BaseRAGAgent",
    "FiqhAgent",
    "HadithAgent",
    "SeerahAgent",
    "TafsirAgent",
    "AqeedahAgent",
    "HistoryAgent",
    "LanguageAgent",
    "TazkiyahAgent",
    "UsulFiqhAgent",
    "GeneralIslamicAgent",
]
