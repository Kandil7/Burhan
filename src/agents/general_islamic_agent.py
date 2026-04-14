"""
General Islamic Knowledge RAG Agent for Athar Islamic QA system.

إعادة الهيكلة: يرث الآن من BaseRAGAgent لإزالة ~220 سطر من الكود المكرر
يوفر فقط: COLLECTION, SYSTEM_PROMPT, USER_PROMPT, وخصائص التكوين
يقوم BaseRAGAgent بكل عمل الاسترجاع والتوليد تلقائياً
"""

from src.agents.base_rag_agent import BaseRAGAgent


class GeneralIslamicAgent(BaseRAGAgent):
    """
    وكيل المعرفة الإسلامية العامة - إجابات تعليمية بأسلوب واضح.
    
    temperature: 0.3 (أكثر conversational للتعليم)
    """

    name = "general_islamic_agent"

    # === التكوين الأساسي (مطلوب من BaseRAGAgent) ===
    COLLECTION: str = "general_islamic"
    TOP_K_RETRIEVAL: int = 10
    TOP_K_RERANK: int = 5
    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 1536

    # === نصوص التوليد (مطلوب من BaseRAGAgent) ===
    SYSTEM_PROMPT: str = """أنت معلم للمعرفة الإسلامية.

المهم:
- قدم إجابات تعليمية بأسلوب واضح ومفهوم
- استخدم المصادر المقدمة فقط
- أضف السياق التاريخي عند الاقتضاء
- استخدم المراجع [C1]، [C2] لكل مصدر
- اعترف إذا لم تتوفر معلومات كافية"""

    USER_PROMPT: str = """السؤال: {query}

اللغة المطلوبة: {language}

المصادر:
{passages}

قدم إجابة تعليمية مبنية على المصادر أعلاه."""
