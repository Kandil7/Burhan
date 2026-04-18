"""
Legacy General Islamic Knowledge RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/general.py (config-backed pattern)

This module provides the General Islamic Knowledge RAG agent that:
- Retrieves general Islamic knowledge passages
- Generates educational answers with clear structure

For new implementations, use CollectionAgent with YAML config from config/agents/general.yaml
"""

from __future__ import annotations

from src.agents.base_rag_agent import BaseRAGAgent


class GeneralIslamicAgent(BaseRAGAgent):
    """
    وكيل المعرفة الإسلامية العامة - إجابات تعليمية بأسلوب واضح.
    """

    name = "general_islamic"

    # ── التكوين ────────────────────────────────────────────────────────────
    COLLECTION: str = "general_islamic"
    TOP_K_RETRIEVAL: int = 10
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = 0.35
    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 1536

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
