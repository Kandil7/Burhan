"""
Fiqh RAG Agent for Athar Islamic QA system.

إعادة الهيكلة: يرث الآن من BaseRAGAgent لإزالة ~240 سطر من الكود المكرر
يوفر فقط: COLLECTION, SYSTEM_PROMPT, USER_PROMPT, وخصائص التكوين
يقوم BaseRAGAgent بكل عمل الاسترجاع والتوليد تلقائياً
"""

from src.agents.base_rag_agent import BaseRAGAgent
from src.config.constants import LLMConfig, RetrievalConfig


class FiqhAgent(BaseRAGAgent):
    """
    وكيل الفقه الإسلامي - إجابات مبنية على النصوص المسترجاعة فقط.

   _temperature: 0.1 (حتمي جداً)
    """

    name = "fiqh_agent"

    # === التكوين الأساسي (مطلوب من BaseRAGAgent) ===
    COLLECTION: str = "fiqh_passages"
    TOP_K_RETRIEVAL: int = RetrievalConfig.TOP_K_FIQH
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = RetrievalConfig.SEMANTIC_SCORE_THRESHOLD
    TEMPERATURE: float = LLMConfig.FIQH_TEMPERATURE
    MAX_TOKENS: int = LLMConfig.DEFAULT_MAX_TOKENS

    # === نصوص التوليد (مطلوب من BaseRAGAgent) ===
    SYSTEM_PROMPT: str = """أنت مساعد إسلامي متخصص في الفقه الإسلامي.

المهم:
- أجب بناءً ONLY على النصوص المسترجاعة المقدمة
- لا تختلق أي معلومات غير موجودة في النصوص
- استخدم المراجع [C1]، [C2]، إلخ لكل مصدر تستشهد به
- إذا لم تكن هناك نص sufficiently يجيب على السؤال، قل ذلك صراحة
- أضف تنبيه باستشارة عالم متخصص للحالات الخاصة
- اذكر المذهب الإسلامي إن وُجد في النصوص"""

    USER_PROMPT: str = """السؤال: {query}

اللغة المطلوبة: {language}

النصوص المسترجاعة:
{passages}

أجب بناءً على النصوص أعلاه مع الالتزام بالتعليمات."""
