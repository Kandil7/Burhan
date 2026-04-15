"""
General Islamic Knowledge RAG Agent for Athar Islamic QA system.

إعادة الهيكلة: يرث الآن من BaseRAGAgent لإزالة ~220 سطر من الكود المكرر
يوفر فقط: COLLECTION, SYSTEM_PROMPT, USER_PROMPT, وخصائص التكوين
يقوم BaseRAGAgent بكل عمل الاسترجاع والتوليد تلقائياً
"""
from __future__ import annotations

from src.agents.base_rag_agent import BaseRAGAgent


class GeneralIslamicAgent(BaseRAGAgent):
    """
    وكيل المعرفة الإسلامية العامة - إجابات تعليمية بأسلوب واضح.

    """

    name = "general_islamic"          # حُذفت "_agent" لتطابق RouterAgent

    # ── التكوين الأساسي ────────────────────────────────────────────────────
    COLLECTION:        str   = "general_islamic"
    TOP_K_RETRIEVAL:   int   = 10
    TOP_K_RERANK:      int   = 5
    SCORE_THRESHOLD: float = 0.35 
    TEMPERATURE:       float = 0.3
    MAX_TOKENS:        int   = 1536

    # ── Fix #1: أجبر على وجود embedding_model عند البناء ─────────────────
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if getattr(self, "embedding_model", None) is None:
            raise ValueError(
                f"{self.__class__.__name__} requires 'embedding_model' — "
                "pass it to the constructor or register it in the DI container."
            )

    # ── نصوص التوليد ──────────────────────────────────────────────────────
    SYSTEM_PROMPT: str = """أنت معلم إسلامي متخصص يُجيب بأسلوب تعليمي واضح.

التعليمات:
- استند **حصراً** إلى المصادر المُقدَّمة، لا تستحضر معلومات خارجها.
- استخدم مراجع المصادر [C1]، [C2]... بعد كل جملة مستمدة منها.
- أضف السياق التاريخي أو الفقهي عند الاقتضاء.
- إذا تعارضت المصادر، اذكر الخلاف بأمانة.
- إذا كانت المصادر المُقدَّمة غير كافية للإجابة، قل:
  "لم أجد في المصادر المتاحة ما يُجيب على هذا السؤال بدقة."
  ولا تُكمل بمعلومات من خارجها."""

    USER_PROMPT: str = """السؤال: {query}

اللغة المطلوبة: {language}

المصادر المتاحة ({num_passages} مقطع):
{passages}

قدم إجابة تعليمية مُنظَّمة مبنية على المصادر أعلاه."""