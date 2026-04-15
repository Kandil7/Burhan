"""
Fiqh RAG Agent for Athar Islamic QA system.

Fixes v2:
  - Bug #1: name = "fiqh" (no _agent suffix)
  - Bug #2: __init__ validates embedding_model at construction time
  - Bug #3: SYSTEM_PROMPT fully in Arabic — no mixed language
  - Bug #4: NO_PASSAGES_MESSAGE guides user to rephrase fiqh query
"""
from src.agents.base_rag_agent import BaseRAGAgent
from src.config.constants import LLMConfig, RetrievalConfig


class FiqhAgent(BaseRAGAgent):
    """
    وكيل الفقه الإسلامي - إجابات مبنية على النصوص المسترجاعة فقط.

    Uses usul_fiqh collection (50,240 vectors in Qdrant).
    """

    name = "fiqh"   # Fix #1 — consistent with RouterAgent

    # ── التكوين ────────────────────────────────────────────────────────────
    COLLECTION:      str   = "usul_fiqh"
    TOP_K_RETRIEVAL: int   = RetrievalConfig.TOP_K_FIQH
    TOP_K_RERANK:    int   = 5
    SCORE_THRESHOLD: float = RetrievalConfig.SEMANTIC_SCORE_THRESHOLD
    TEMPERATURE:     float = LLMConfig.FIQH_TEMPERATURE
    MAX_TOKENS:      int   = LLMConfig.DEFAULT_MAX_TOKENS

    # Fix #4 — رسالة مخصصة لسياق الفقه
    NO_PASSAGES_MESSAGE: str = (
        "لم أجد نصوصاً فقهية كافية للإجابة على هذا السؤال تحديداً. "
        "يُنصح بإعادة صياغة السؤال بمصطلحات فقهية أدق، "
        "أو استشارة عالم متخصص للحالات الخاصة."
    )

    # Fix #2 — تحقق من الـ embedding_model عند البناء
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if getattr(self, "embedding_model", None) is None:
            raise ValueError(
                "FiqhAgent requires 'embedding_model' — "
                "pass it to the constructor or register it in the DI container."
            )

    # ── نصوص التوليد ──────────────────────────────────────────────────────
    # Fix #3 — SYSTEM_PROMPT بالعربية الكاملة بدون خلط لغوي
    SYSTEM_PROMPT: str = """أنت مساعد إسلامي متخصص في الفقه الإسلامي.

التعليمات:
- استند **حصراً** إلى النصوص المسترجاعة المُقدَّمة، ولا تستحضر معلومات خارجها.
- استخدم مراجع المصادر [C1]، [C2]، ... بعد كل جملة مستمدة منها.
- اذكر المذهب الفقهي إن وُجد في النصوص (حنفي، مالكي، شافعي، حنبلي).
- إذا تعارضت النصوص أو وُجد خلاف فقهي، اعرض الأقوال وأصحابها.
- إذا كانت النصوص المقدمة غير كافية للإجابة بدقة، أقرّ بذلك صراحةً دون افتراض.
- أضف في النهاية: "يُنصح باستشارة عالم متخصص للحالات الخاصة" عند الاقتضاء."""

    USER_PROMPT: str = """السؤال الفقهي: {query}

اللغة المطلوبة: {language}

النصوص المسترجاعة ({num_passages} مقطع):
{passages}

أجب بناءً على النصوص أعلاه مع الالتزام بالتعليمات."""