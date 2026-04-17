"""
Islamic History RAG Agent for Athar Islamic QA system.

Retrieves from history_passages collection.
Inherits full RAG pipeline from BaseRAGAgent.
"""

from src.agents.base_rag_agent import BaseRAGAgent
from src.config.constants import LLMConfig, RetrievalConfig


class HistoryAgent(BaseRAGAgent):
    """
    وكيل التاريخ الإسلامي - تاريخ الحضارة الإسلامية والأحداث.

    Uses history_passages collection (Islamic history books,
    chronicles, biographies of companions, etc.)
    """

    name = "history"

    # ── التكوين ────────────────────────────────────────────────────────────
    COLLECTION: str = "history_passages"
    TOP_K_RETRIEVAL: int = 12
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = 0.50
    TEMPERATURE: float = 0.25
    MAX_TOKENS: int = 2048

    NO_PASSAGES_MESSAGE: str = (
        "لم أجد معلومات تاريخية كافية في قاعدة البيانات. "
        "يُنصح بإعادة صياغة السؤال أو التركيز على فترة أو شخصية محددة، "
        "أو الرجوع إلى كتب التاريخ الإسلامي المعتمدة."
    )

    # ── نصوص التوليد ──────────────────────────────────────────────────────
    SYSTEM_PROMPT: str = """أنت متخصص في التاريخ الإسلامي والحضارة الإسلامية.

التعليمات:
- استند **حصراً** إلى النصوص التاريخية المُقدَّمة، ولا تستحضر معلومات خارجها.
- استخدم مراجع المصادر [C1]، [C2]، ... بعد كل معلومة مستمدة منها.
- قدّم المعلومات بأسلوب سردي واضح مع الترتيب الزمني عند الإمكان.
- اذكر الفترة الزمنية والشخصيات والأماكن المذكورة في النصوص.
- إذا تعارضت الروايات التاريخية، اعرض الروايات المختلفة.
- إذا كانت النصوص غير كافية، صرّح بذلك."""

    USER_PROMPT: str = """السؤال التاريخي: {query}

اللغة المطلوبة: {language}

النصوص التاريخية المسترجعة ({num_passages} مقطع):
{passages}

قدم الإجابة التاريخية مع الاستشهاد بالمصادر."""
