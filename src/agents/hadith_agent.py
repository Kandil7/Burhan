"""
Hadith RAG Agent for Athar Islamic QA system.

إعادة الهيكلة: يرث الآن من BaseRAGAgent لإزالة ~180 سطر من الكود المكرر
يوفر فقط: COLLECTION, SYSTEM_PROMPT, USER_PROMPT, وخصائص التكوين
يقوم BaseRAGAgent بكل عمل الاسترجاع والتوليد تلقائياً
"""

from src.agents.base_rag_agent import BaseRAGAgent


class HadithAgent(BaseRAGAgent):
    """
    وكيل الحديث النبوي - عرض الأحاديث مع المصدر والدرجة.

    temperature: 0.1 (حتمي)
    """

    name = "hadith_agent"

    # === التكوين الأساسي (مطلوب من BaseRAGAgent) ===
    COLLECTION: str = "hadith_passages"
    TOP_K_RETRIEVAL: int = 10
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = 0.6
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 2048

    # === نصوص التوليد (مطلوب من BaseRAGAgent) ===
    SYSTEM_PROMPT: str = """أنت متخصص في علم الحديث ورواياته.

المهم:
- اعرض الأحاديث من النصوص المسترجاعة فقط
- لا تختلق أي أحاديث أو معلومات
- اذكر السند والمتن إذا كانا متاحين
- اذكر درجة الحديث (صحيح، حسن، ضعيف) إذا كانت متوفرة
- اذكر مصدر الحديث (صحيح البخاري، مسلم، إلخ)
- استخدم المراجع [C1]، [C2] لكل حديث
- إذا لم توجد أحاديث كافية، قل ذلك صراحة
- أضف تنبيهاً بضرورة الرجوع لأهل العلم"""

    USER_PROMPT: str = """السؤال: {query}

اللغة المطلوبة: {language}

الأحاديث المسترجاعة:
{passages}

اعرض الأحاديث المناسبة مع ذكر المصدر والدرجة."""
