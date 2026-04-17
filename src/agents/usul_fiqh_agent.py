"""
Usul al-Fiqh (Principles of Islamic Jurisprudence) RAG Agent for Athar Islamic QA system.

Retrieves from usul_fiqh_passages collection.
Inherits full RAG pipeline from BaseRAGAgent.
"""

from src.agents.base_rag_agent import BaseRAGAgent
from src.config.constants import LLMConfig, RetrievalConfig


class UsulFiqhAgent(BaseRAGAgent):
    """
    وكيل أصول الفقه - قواعد الاستنباط والاجتهاد.

    Uses usul_fiqh_passages collection (classical usul al-fiqh books,
    principles of jurisprudence, qiyas, ijma, etc.)
    """

    name = "usul_fiqh"

    # ── التكوين ────────────────────────────────────────────────────────────
    COLLECTION: str = "usul_fiqh_passages"
    TOP_K_RETRIEVAL: int = 10
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = 0.55
    TEMPERATURE: float = 0.15
    MAX_TOKENS: int = 1792

    NO_PASSAGES_MESSAGE: str = (
        "لم أجد نصوصاً أصولية كافية في قاعدة البيانات. "
        "يُنصح بإعادة صياغة السؤال بأصول فقهية أدق، "
        "أو الرجوع إلى مصادر أصول الفقه المعتمدة."
    )

    # ── نصوص التوليد ──────────────────────────────────────────────────────
    SYSTEM_PROMPT: str = """أنت متخصص في أصول الفقه وقواعد الاستنباط.

التعليمات:
- استند **حصراً** إلى النصوص الأصولية المُقدَّمة، ولا تستحضر معلومات خارجها.
- استخدم مراجع المصادر [C1]، [C2]، ... بعد كل قاعدة أو قول مستمدة منه.
- وضّح الدليل من القرآن أو السنة أو الإجماع أو القياس إن وُجد في النصوص.
- اذكر أقوال الأصوليين (الشافعي، الأمدي، الغزالي، ابن رشد...) مع مصادرها.
- وضّح كيفية تطبيق القاعدة على المسألة إن أمكن.
- إذا كانت النصوص غير كافية، صرّح بذلك."""

    USER_PROMPT: str = """السؤال الأصولي: {query}

اللغة المطلوبة: {language}

النصوص الأصولية المسترجعة ({num_passages} مقطع):
{passages}

قدم الإجابة الأصولية مع الاستشهاد بالمصادر."""
