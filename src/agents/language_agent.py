"""
Arabic Language RAG Agent for Athar Islamic QA system.

Retrieves from language_passages collection.
Inherits full RAG pipeline from BaseRAGAgent.
"""

from src.agents.base_rag_agent import BaseRAGAgent
from src.config.constants import LLMConfig, RetrievalConfig


class LanguageAgent(BaseRAGAgent):
    """
    وكيل اللغة العربية - النحو والصرف والبلاغة والمعاجم.

    Uses language_passages collection (Arabic grammar books,
    dictionaries, morphology, rhetoric, poetry, etc.)
    """

    name = "language"

    # ── التكوين ────────────────────────────────────────────────────────────
    COLLECTION: str = "language_passages"
    TOP_K_RETRIEVAL: int = 10
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = 0.45
    TEMPERATURE: float = 0.2
    MAX_TOKENS: int = 1536

    NO_PASSAGES_MESSAGE: str = (
        "لم أجد معلومات لغوية كافية في قاعدة البيانات. "
        "يُنصح بإعادة صياغة السؤال أو التحقق من الكلمة، "
        "أو الرجوع إلى المعاجم العربية المعتمدة."
    )

    # ── نصوص التوليد ──────────────────────────────────────────────────────
    SYSTEM_PROMPT: str = """أنت متخصص في اللغة العربية وعلومها (النحو، الصرف، البلاغة، المعاجم).

التعليمات:
- استند **حصراً** إلى النصوص اللغوية المُقدَّمة، ولا تستحضر معلومات خارجها.
- استخدم مراجع المصادر [C1]، [C2]، ... بعد كل معلومة مستمدة منها.
- وضّح القواعد النحوية والصرفية بذكر الدليل من النصوص المعاصرة.
- اعرض معاني الكلمات والسياق الذي استُخدمت فيه.
- إذا كانت الكلمة متعددة المعاني، اذكر كل معنى مع مثال.
- إذا كانت النصوص غير كافية، صرّح بذلك."""

    USER_PROMPT: str = """السؤال اللغوي: {query}

اللغة المطلوبة: {language}

النصوص اللغوية المسترجعة ({num_passages} مقطع):
{passages}

قدم الإجابة اللغوية مع الاستشهاد بالمصادر."""
