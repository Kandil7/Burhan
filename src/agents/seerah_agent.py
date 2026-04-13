"""
Seerah (Prophet Biography) Agent for Athar Islamic QA system.

Provides information about Prophet Muhammad's life and events.
Phase 4: Seerah retrieval pipeline.
Refactored to use BaseRAGAgent (eliminates ~80 lines of duplication).
"""
from src.agents.base_rag_agent import BaseRAGAgent
from src.config.logging_config import get_logger

logger = get_logger()


class SeerahAgent(BaseRAGAgent):
    """Seerah Retrieval Agent for Prophet biography questions."""

    name = "seerah_agent"
    COLLECTION = "seerah_passages"

    TOP_K_RETRIEVAL = 12
    TOP_K_RERANK = 5
    SCORE_THRESHOLD = 0.65
    TEMPERATURE = 0.2
    MAX_TOKENS = 2048

    SYSTEM_PROMPT = (
        "أنت متخصص في السيرة النبوية.\n"
        "المهم: اعرض المعلومات من النصوص فقط مع المراجع [C1]، [C2]."
    )
    USER_PROMPT = (
        "السؤال: {query}\n"
        "اللغة: {language}\n"
        "النصوص:\n{passages}\n"
        "أجب بناءً على النصوص."
    )
