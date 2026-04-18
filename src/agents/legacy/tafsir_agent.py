"""
Legacy Tafsir (Quran Interpretation) RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/tafsir.py (config-backed pattern)

This module provides the Tafsir RAG agent that:
- Retrieves tafsir passages from tafsir_passages collection
- Generates answers with multiple tafsir perspectives

For new implementations, use CollectionAgent with YAML config from config/agents/tafsir.yaml
"""

from src.agents.base_rag_agent import BaseRAGAgent
from src.config.constants import LLMConfig, RetrievalConfig


class TafsirAgent(BaseRAGAgent):
    """
    وكيل تفسير القرآن الكريم - تفسير آيات القرآن ومعانيها.

    Uses tafsir_passages collection (multiple tafsir books:
    Ibn Kathir, Al-Jalalayn, Al-Qurtubi, etc.)
    """

    name = "tafsir"

    # ── التكوين ────────────────────────────────────────────────────────────
    COLLECTION: str = "tafsir_passages"
    TOP_K_RETRIEVAL: int = RetrievalConfig.TOP_K_TAFSIR
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = RetrievalConfig.SEMANTIC_SCORE_THRESHOLD
    TEMPERATURE: float = LLMConfig.TAFSIR_TEMPERATURE
    MAX_TOKENS: int = LLMConfig.DEFAULT_MAX_TOKENS

    NO_PASSAGES_MESSAGE: str = (
        "لم أجد تفسيراً للآية المطلوبة في قاعدة البيانات. "
        "يُنصح بالتحقق من صحة الآية أو صياغة السؤال بشكل مختلف، "
        "أو الرجوع إلى كتب التفسير المعتمدة."
    )

    # ── نصوص التوليد ──────────────────────────────────────────────────────
    SYSTEM_PROMPT: str = """أنت متخصص في تفسير القرآن الكريم وعلومه.

التعليمات:
- استند **حصراً** إلى النصوص التفسيرية المُقدَّمة، ولا تستحضر معلومات خارجها.
- استخدم مراجع المصادر [C1]، [C2]، ... بعد كل جملة مستمدة منها.
- اذكر اسم المفسر والمصدر التفسيري إن وُجد في النصوص (ابن كثير، الجلالين، القرطبي، إلخ).
- اعرض التفسير بأسلوب واضح مع ذكر المعنى الإجمالي للآية.
- إذا تعددت التفاسير لنفس الآية، اعرض الأقوال المختلفة مع مصادرها.
- إذا كانت النصوص غير كافية، صرّح بذلك ولا تُخمن."""

    USER_PROMPT: str = """السؤال: {query}

اللغة المطلوبة: {language}

النصوص التفسيرية المسترجعة ({num_passages} مقطع):
{passages}

قدم التفسير المناسب مع ذكر المصدر."""
