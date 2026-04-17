"""
Aqeedah (Islamic Creed/Theology) RAG Agent for Athar Islamic QA system.

Retrieves from aqeedah_passages collection.
Inherits full RAG pipeline from BaseRAGAgent.
"""

from src.agents.base_rag_agent import BaseRAGAgent
from src.config.constants import LLMConfig, RetrievalConfig


class AqeedahAgent(BaseRAGAgent):
    """
    وكيل العقيدة الإسلامية - الإيمان والتوحيد والعقائد.

    Uses aqeedah_passages collection (classical aqeedah books:
    Ibn Taymiyyah, Al-Ghazali, Al-Ashari, Al-Maturidi, etc.)
    """

    name = "aqeedah"

    # ── التكوين ────────────────────────────────────────────────────────────
    COLLECTION: str = "aqeedah_passages"
    TOP_K_RETRIEVAL: int = RetrievalConfig.TOP_K_AQEEDAH
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = RetrievalConfig.SEMANTIC_SCORE_THRESHOLD
    TEMPERATURE: float = LLMConfig.AQEEDAH_TEMPERATURE
    MAX_TOKENS: int = LLMConfig.DEFAULT_MAX_TOKENS

    NO_PASSAGES_MESSAGE: str = (
        "لم أجد نصوصاً في العقيدة الإسلامية مرتبطة بهذا السؤال. "
        "يُنصح بإعادة صياغة السؤال بمصطلحات عقدية أدق، "
        "أو الرجوع إلى مصادر العقيدة الإسلامية المعتمدة."
    )

    # ── نصوص التوليد ──────────────────────────────────────────────────────
    SYSTEM_PROMPT: str = """أنت متخصص في العقيدة الإسلامية (علم التوحيد).

التعليمات:
- استند **حصراً** إلى النصوص العقدية المُقدَّمة، ولا تستحضر معلومات خارجها.
- استخدم مراجع المصادر [C1]، [C2]، ... بعد كل جملة مستمدة منها.
- اذكر الدليل من القرآن والسنة إن وُجد في النصوص.
- اعرض أقوال أهل العلم في المسألة العقدية مع مصدرها.
- إذا تعددت المذاهب العقدية (أشعرية، ماتريدية، سلفية)، اعرض كل قول بأمانة.
- إذا كانت النصوص غير كافية أو غابت الأدلة، صرّح بذلك."""

    USER_PROMPT: str = """السؤال العقدي: {query}

اللغة المطلوبة: {language}

النصوص العقدية المسترجعة ({num_passages} مقطع):
{passages}

قدم الإجابة العقدية مع الاستشهاد بالمصادر."""
