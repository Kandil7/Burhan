"""
Legacy Hadith RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/hadith.py (config-backed pattern)

This module provides the Hadith RAG agent that:
- Retrieves hadith passages from hadith_passages collection
- Applies hadith grade verification
- Generates answers with source attribution

For new implementations, use CollectionAgent with YAML config from config/agents/hadith.yaml
"""

from src.agents.base_rag_agent import BaseRAGAgent
from src.config.constants import LLMConfig, RetrievalConfig


class HadithAgent(BaseRAGAgent):
    """
    وكيل الحديث النبوي - عرض الأحاديث مع المصدر والدرجة.
    temperature: 0.1 (حتمي — أدنى من FiqhAgent لأن النصوص يجب أن تُنقل حرفياً)
    """

    name = "hadith"

    # ── التكوين ──────────────────────────────────────────────────────────
    COLLECTION: str = "hadith_passages"
    TOP_K_RETRIEVAL: int = RetrievalConfig.TOP_K_HADITH
    TOP_K_RERANK: int = 5
    SCORE_THRESHOLD: float = RetrievalConfig.HYBRID_SCORE_THRESHOLD  # 0.50
    TEMPERATURE: float = LLMConfig.DEFAULT_TEMPERATURE
    MAX_TOKENS: int = LLMConfig.DEFAULT_MAX_TOKENS

    NO_PASSAGES_MESSAGE: str = (
        "لم أجد أحاديث نبوية مرتبطة بهذا السؤال في قاعدة البيانات. "
        "يُنصح بإعادة صياغة السؤال بمصطلحات حديثية أدق (ذكر راوٍ، موضوع، أو كتاب مصدر)، "
        "أو الرجوع مباشرةً لكتب السنة النبوية."
    )

    SYSTEM_PROMPT: str = """أنت متخصص في علم الحديث النبوي ورواياته.

تحذير مطلق — يجب الالتزام به بصرامة:
لا تختلق أبداً أي حديث أو جزء من حديث أو إسناد.
إذا لم يكن الحديث موجوداً حرفياً في النصوص المسترجاعة، لا تذكره ولا تُلمّح إليه.
نسبة كلام زائف إلى النبي ﷺ كبيرة من الكبائر.

التعليمات:
- اعرض الأحاديث **حرفياً** كما وردت في النصوص المسترجاعة فقط، دون أي تعديل أو اختصار.
-اذكر السند والمتن إذا كانا متاحَين في النص.
- اذكر درجة الحديث (صحيح، حسن، ضعيف، موضوع) إذا وردت في النص.
- اذكر مصدر الحديث (صحيح البخاري، مسلم، سنن أبي داود... إلخ) من النص مباشرةً.
- استخدم مراجع المصادر [C1]، [C2]، ... بعد كل حديث.
- إذا تعددت الروايات لنفس المعنى، اعرضها جميعاً مع مصادرها.
- إذا كانت النصوص غير كافية للإجابة، أقرّ بذلك صراحةً ولا تُكمِّل من عندك.
- أضف في النهاية: "يُنصح بالرجوع لأهل العلم للتحقق من صحة الاستدلال بهذه الأحاديث"."""

    USER_PROMPT: str = """السؤال: {query}

اللغة المطلوبة: {language}

الأحاديث المسترجاعة ({num_passages} مقطع):
{passages}

اعرض الأحاديث المناسبة من النصوص أعلاه مع ذكر المصدر والدرجة."""
