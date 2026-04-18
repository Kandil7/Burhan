"""
Legacy Seerah (Prophet Biography) RAG Agent - DEPRECATED.

Migrated to: src/agents/collection/seerah.py (config-backed pattern)

This module provides the Seerah RAG agent that:
- Retrieves prophet biography passages from seerah_passages collection
- Generates answers with historical context

For new implementations, use CollectionAgent with YAML config from config/agents/seerah.yaml
"""

from src.agents.base_rag_agent import BaseRAGAgent


class SeerahAgent(BaseRAGAgent):
    """Seerah Retrieval Agent — Prophet biography questions."""

    name = "seerah"
    COLLECTION = "seerah_passages"
    SCORE_THRESHOLD: float = 0.50

    TEMPERATURE = 0.2  # slightly higher for narrative tone vs fiqh precision

    SYSTEM_PROMPT = """\
أنت مساعد إسلامي متخصص في السيرة النبوية.

قواعد الإجابة:
- استند فقط إلى النصوص المسترجعة، ولا تضف معلومات من خارجها.
- استشهد بكل مصدر بالرمز [C1]، [C2]، وهكذا.
- اعرض الأحداث بترتيب زمني عند الإمكان.
- إن كانت النصوص غير كافية، صرّح بذلك صراحةً.

هيكل الإجابة:
١. الإجابة المباشرة
٢. التفاصيل من النصوص مع الاستشهادات
٣. السياق التاريخي إن وُجد في النصوص"""

    USER_PROMPT = """\
السؤال: {query}

اللغة المطلوبة: {language}

نصوص السيرة النبوية المسترجعة ({num_passages} مقطع):
{passages}

أجب وفق القواعد أعلاه، ولا تتجاوز ما في النصوص."""
