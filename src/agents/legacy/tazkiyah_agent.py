"""
Legacy Tazkiyah (Spiritual Development/Ethics) RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/tazkiyah.py (config-backed pattern)

This module provides the Tazkiyah RAG agent that:
- Retrieves spiritual development passages from tazkiyah_passages collection
- Generates answers with ethical and spiritual guidance

For new implementations, use CollectionAgent with YAML config from config/agents/tazkiyah.yaml
"""

from src.agents.base_rag_agent import BaseRAGAgent
from src.config.constants import LLMConfig, RetrievalConfig


class TazkiyahAgent(BaseRAGAgent):
    """
    وكيل التزكية والتربية الروحية - الأخلاق والتطور الروحي.

    Uses tazkiyah_passages collection (Islamic spirituality,
    ethics, self-purification, Sufism, Ibn Qayyim, Al-Ghazali, etc.)
    """

    name = "tazkiyah"

    # ── التكوين ────────────────────────────────────────────────────────────
    COLLECTION: str = "tazkiyah_passages"
    TOP_K_RETRIEVAL: int = 10
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = 0.45
    TEMPERATURE: float = 0.25
    MAX_TOKENS: int = 1792

    NO_PASSAGES_MESSAGE: str = (
        "لم أجد نصوصاً كافية في موضوع التزكية والأخلاق. "
        "يُنصح بإعادة صياغة السؤال بالتركيز على جانب معين من الأخلاق أو التزكية، "
        "أو الرجوع إلى مصادر التربية الروحية الإسلامية."
    )

    # ── نصوص التوليد ──────────────────────────────────────────────────────
    SYSTEM_PROMPT: str = """أنت متخصص في التزكية الإسلامية والأخلاق والتربية الروحية.

التعليمات:
- استند **حصراً** إلى النصوص التزكية والأخلاقية المُقدَّمة، ولا تستحضر معلومات خارجها.
- استخدم مراجع المصادر [C1]، [C2]، ... بعد كل معلومة مستمدة منها.
- وضّح الأبعاد الروحية والأخلاقية للموضوع.
- اعرض النصوص الواردة في الآيات القرآنية والأحاديث النبوية إن وُجدت.
- قدّم النصائح العملية المبنية على النصوص المتاحة.
- إذا تعددت الآراء في المسألة الأخلاقية، اعرضها بأمانة."""

    USER_PROMPT: str = """السؤال في التزكية والأخلاق: {query}

اللغة المطلوبة: {language}

النصوص التزكية المسترجعة ({num_passages} مقطع):
{passages}

قدم الإجابة مع الاستشهاد بالمصادر."""
