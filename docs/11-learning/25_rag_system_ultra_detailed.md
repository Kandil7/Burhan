# 🕌 دليل نظام RAG المفصل جداً جداً

## شرح كل سطر وكل دالة وكل classe في نظام RAG

هذا الدليل يذهب إلى أعمق مستوى ممكن لشرح نظام RAG. سأشرح كل سطر برمجي وكل fonction وكل classe وكل module بالتفصيل المطلق.

---

## 表 المحتويات

1. [/المخطط العام](#1-المخطط-العامل)
2. [/ الطبقة 1: نقطة الدخول](#2-الطبقة-1-نقطة-الدخول)
3. [/الطبقة 2: التحقق](#3-الطبقة-2-التحقق)
4. [/الطبقة 3: التصنيف](#4-الطبقة-3-التصنيف)
5. [/الطبقة 4: التوجيه](#5-الطبقة-4-التوجيه)
6. [/الطبقة 5: الاسترجاع](#6-الطبقة-5-الاسترجاع)
7. [/الطبقة 6: التحقق](#7-الطبقة-6-التحقق)
8. [/الطبقة 7: التوليد](#8-الطبقة-7-التوليد)
9. [/الطبقة 8: المعالجة](#9-الطبقة-8-المعالجة)
10. [/المخططات والجداول](#10-المخططات-والجداول)

---

## 1. المخطط العام

### 1.1 مخطط التدفق

```
User Query
    │
    ├─[API Layer]─ POST /api/v1/ask
    │      │
    ├─[Validation]─ AskRequest validation
    │      │
    ├─[Classification]─ Intent Classifier (Hybrid)
    │      │
    ├─[Routing]─ Router Agent
    │      │
    ├─[Retrieval]─ Hybrid Search (RRF)
    │      │      ├─ Semantic Search
    │      │      └─ BM25 Search
    │      │
    ├─[Verification]─ Verification Suite
    │      │     ├─ Exact Quote Check
    │      │     ├─ Source Attribution
    │      │     └─ Contradiction Check
    │      │
    ├─[Generation]─ LLM Client
    │      │     ├─ Prompt Builder
    │      │     ├─ System Prompt
    │      │     └─ OpenAI/Groq
    │      │
    ├─[Post-processing]─ Strip CoT
    │      │
    ├─[Citation Building]─ Citations
    │      │
    └─[Response]─ AskResponse
```

### 1.2 الطبقات الرئيسية

| الطبقة | الملف | الوظيفة |
|--------|-------|---------|
| API | `src/api/routes/ask.py` | استلام الطلب |
| Validation | `src/api/schemas/ask.py` | التحقق من الصحة |
| Classification | `src/application/hybrid_classifier.py` | تصنيف النية |
| Routing | `src/core/registry.py` | اختيار الوكيل |
| Retrieval | `src/retrieval/retrievers/*.py` | استرجاع الوثائق |
| Verification | `src/verifiers/suite_builder.py` | التحقق من الدقة |
| Generation | `src/generation/llm_client.py` | توليد الإجابة |
| Post-processing | `src/agents/base.py` | معالجة الإجابة |

---

## 2. الطبقة 1: نقطة الدخول

### 2.1 src/api/routes/ask.py

#### 2.1.1 الاستيراد

```python
# ===== src/api/routes/ask.py =====

# استيراد الدالة FastAPI
from fastapi import APIRouter, Depends, Request

# استيراد أنماط الطلب والاستجابة
from src.api.schemas.ask import AskRequest, AskResponse

# استيراد الخدمات
from src.application.use_cases.answer_query import AnswerQueryUseCase
from src.services.ask_service import AskService

# استيراد أدوات الوقت
import time

# استيراد Logger
import structlog

logger = structlog.get_logger(__name__)
```

**شرح بالتفصيل**:

- `APIRouter`: Creates the routes for the ask endpoint
- `AskRequest`, `AskResponse`: Pydantic models for request/response
- `AnswerQueryUseCase`: Use case for answering queries
- `AskService`: Service layer
- `time`: For measuring execution time
- `structlog`: For structured logging

#### 2.1.2 إنشاء Router

```python
# إنشاءRouter
ask_router = APIRouter(
    prefix="/ask",
    tags=["query"],
    responses={404: {"description": "Not found"}}
)
```

**شرح**:

- `prefix="/ask"`: All routes will have this prefix
- `tags=["query"]`: Tag for OpenAPI documentation
- `responses`: Custom responses

#### 2.1.3 نقطة النهاية

```python
@ask_router.post(
    "",
    response_model=AskResponse,
    summary="Answer Islamic Question",
    description="""Ask an Islamic question and get an answer.
    
    ## Features:
    - Intent classification
    - Multi-agent routing
    - Source verification
    - Citation generation
    
    ## Example:
    ```json
    {
        "query": "ما حكم صلاة الجماعة؟",
        "language": "ar",
        "madhhab": "hanafi"
    }
    ```
    """,
    response_description="Answer with citations"
)
async def ask_question(
    request: AskRequest,
    http_request: Request,
) -> AskResponse:
    """معالجة سؤال المستخدم."""
    
    # بدء المؤقت
    start_time = time.time()
    
    try:
        # 1. الحصول على الخدمة من الحالة
        ask_service: AskService = http_request.app.state.ask_service
        
        # 2. تنفيذ السؤال
        result = await ask_service.execute(request)
        
        # 3. حساب الزمن
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # 4. بناء الاستجابة
        response = AskResponse(
            answer=result.answer,
            citations=result.citations,
            intent=result.metadata.get("intent", "UNKNOWN"),
            confidence=result.confidence,
            processing_time_ms=elapsed_ms,
        )
        
        # 5. تسجيل النجاح
        logger.info(
            "question_answered",
            query=request.query[:50],
            intent=response.intent,
            elapsed_ms=elapsed_ms,
        )
        
        return response
        
    except Exception as e:
        # تسجيل الخطأ
        logger.error(
            "answer_failed",
            query=request.query[:50],
            error=str(e),
        )
        raise
```

### 2.2 src/api/schemas/ask.py

#### 2.2.1 AskRequest

```python
# ===== src/api/schemas/ask.py =====

from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

class AskRequest(BaseModel):
    """نموذج طلب السؤال."""
    
    # ===== الحقول =====
    
    query: str = Field(
        ...,
        description="سؤال المستخدم",
        examples=["ما حكم صلاة الجماعة؟", "ما تعريف الزكاة؟"],
        min_length=1,
        max_length=1000,
    )
    
    language: str = Field(
        default="ar",
        description="لغة السؤال (ar/en)",
        examples=["ar", "en"],
    )
    
    collection: Optional[str] = Field(
        default=None,
        description="المجموعة المحددة (optional)",
        examples=["fiqh", "hadith", "tafsir"],
    )
    
    madhhab: Optional[str] = Field(
        default=None,
        description="المذهب المفضل (optional)",
        examples=["hanafi", "maliki", "shafii", "hanbali"],
    )
    
    # ===== التكوين =====
    
    model_config = {
        "extra": "forbid",  # لا permettent حقول إضافية
        "json_schema_extra": {
            "examples": [
                {
                    "query": "ما حكم صلاة الجماعة؟",
                    "language": "ar",
                }
            ]
        }
    }
    
    # ===== المدققات =====
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """التحقق من صحة السؤال."""
        
        # إزالة المسافات الزائدة
        v = v.strip()
        
        # التحقق من أن السؤال ليس فارغاً
        if not v:
            raise ValueError("السؤال لا يمكن أن يكون فارغاً")
        
        # التحقق من أن السؤال يحتوي على أحرف صالحة
        if not re.search(r"[\u0600-\u06FFa-zA-Z]", v):
            raise ValueError("السؤال must contain Arabic or English letters")
        
        return v
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """التحقق من صحة اللغة."""
        if v is None:
            return "ar"  # الافتراضي
        
        if v not in ["ar", "en"]:
            raise ValueError("Language must be 'ar' or 'en'")
        
        return v
    
    @field_validator("madhhab")
    @classmethod
    def validate_madhhab(cls, v: Optional[str]) -> Optional[str]:
        """التحقق من صحة المذهب."""
        if v is None:
            return None
        
        # قائمة المذاهب الصالحة
        valid_madhahib = {"hanafi", "maliki", "shafii", "hanbali"}
        
        if v not in valid_madhahib:
            raise ValueError(
                f"Madhhab must be one of: {valid_madhahib}"
            )
        
        return v
```

#### 2.2.2 AskResponse

```python
class CitationResponse(BaseModel):
    """نموذج الاقتباس في الاستجابة."""
    
    source_id: str = Field(..., description="معرف المصدر")
    text: str = Field(..., description="النص المقتبس", max_length=200)
    book_title: Optional[str] = Field(default=None, description="عنوان الكتاب")
    page: Optional[int] = Field(default=None, description="الصفحة")
    grade: Optional[str] = Field(default=None, description="الدرجة (للأحاديث)")
    url: Optional[str] = Field(default=None, description="الرابط")


class AskResponse(BaseModel):
    """نموذج الاستجابة."""
    
    answer: str = Field(..., description="الإجابة")
    citations: list[CitationResponse] = Field(
        default_factory=list,
        description="الاقتباسات"
    )
    intent: str = Field(..., description="النية")
    confidence: float = Field(..., ge=0.0, le=1.0, description="الثقة")
    processing_time_ms: int = Field(..., ge=0, description="زمن المعالجة")
```

---

## 3. الطبقة 2: التحقق

### 3.1 التحقق التلقائي

في Pydantic، التحقق يحدث تلقائياً عند إنشاء الكائن:

```python
# ===== التحقق التلقائي =====

# هذا الكود يتحقق تلقائياً:
# 1. query ليس فارغاً (1-1000 حرف)
# 2. language هو "ar" أو "en"
# 3. madhhab هو salah من أربعة مذاهب

try:
    request = AskRequest(
        query="ما حكم صلاة الجماعة؟",
        language="ar",
        madhhab="hanafi"
    )
    # إذا كان صالح، يستمر
except ValidationError as e:
    # إذا كان غير صالح، يرجع خطأ
    print(e)
```

### 3.2 التحقق اليدوي الإضافي

```python
# ===== التحقق اليدوي =====

async def validate_request(request: AskRequest) -> AskRequest:
    """تحقق يدوي إضافي."""
    
    # 1. التحقق من أن السؤال ليس سؤالاً ضاراً
    harmful_patterns = [
        r"كيف\s+يقتل",
        r"كيف\s+يصنع\s+قنبلة",
        r"كيف\s+يهاجم",
    ]
    
    for pattern in harmful_patterns:
        if re.search(pattern, request.query, re.IGNORECASE):
            raise ValueError("Question contains harmful content")
    
    # 2. التحقق من أن السؤال إسلامي
    islamic_keywords = [
        r"الله",
        r"النبي",
        r"القرآن",
        r"الحديث",
        r"صلاة",
        r"زكاة",
        r"صوم",
        r"حج",
        r"إسلام",
        r"Allah",
        r"Quran",
        r"Prophet",
        r"prayer",
    ]
    
    has_islamic_keyword = any(
        re.search(kw, request.query, re.IGNORECASE)
        for kw in islamic_keywords
    )
    
    if not has_islamic_keyword:
        # Allow but log
        logger.warning(f"Non-Islamic query: {request.query[:50]}")
    
    return request
```

---

## 4. الطبقة 3: التصنيف

### 4.1 Hybrid Intent Classifier

```python
# ===== src/application/hybrid_classifier.py =====

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
import re

class IntentType(str, Enum):
    """أنواع النية."""
    ZAKAT = "ZAKAT"
    INHERITANCE = "INHERITANCE"
    FIQH_HUKM = "FIQH_HUKM"
    FIQH_MASAIL = "FIQH_MASAIL"
    HADITH_TAKHRIJ = "HADITH_TAKHRIJ"
    QURAN_VERSE = "QURAN_VERSE"
    TAFSIR = "TAFSIR"
    AQEEDAH = "AQEEDAH"
    SEERAH = "SEERAH"
    HISTORY = "HISTORY"
    GENERAL_ISLAMIC = "ISLAMIC_KNOWLEDGE"


class ClassificationResult(BaseModel):
    """نتيجة التصنيف."""
    intent: IntentType
    confidence: float
    language: str
    requires_retrieval: bool


class QueryClassifier(ABC):
    """واجهة المصنف."""
    
    @abstractmethod
    async def classify(self, query: str) -> ClassificationResult:
        """تصنيف سؤال."""
        pass


class MasterHybridClassifier(QueryClassifier):
    """المصنف الهجين الرئيسي."""
    
    def __init__(
        self,
        embedding_model=None,
        low_conf_threshold: float = 0.65,
    ):
        # 1. المصنف بالكلمات المفتاحية
        self._keyword_classifier = KeywordBasedClassifier()
        
        # 2. المصنف التضميناتي (اختياري)
        self._embedding_classifier = None
        if embedding_model:
            self._embedding_classifier = EmbeddingClassifier(embedding_model)
        
        # 3. حد الثقة المنخفض
        self._low_conf_threshold = low_conf_threshold
    
    async def classify(self, query: str) -> ClassificationResult:
        """تصنيف سؤال."""
        
        # الخطوة 1:.keyword (سريع، <1ms)
        kw_result = await self._keyword_classifier.classify(query)
        
        # إذا كانت الثقة >= 0.85، استخدم فوراً
        if kw_result.confidence >= 0.85:
            return kw_result
        
        # الخطوة 2: Embedding (أبطأ، 10-50ms)
        if self._embedding_classifier:
            emb_result = await self._embedding_classifier.classify(query)
            
            # اختر الأعلى ثقة
            if emb_result.confidence > kw_result.confidence:
                return emb_result
        
        # الخطوة 3: keyword كنهاية
        return kw_result


class KeywordBasedClassifier(QueryClassifier):
    """مصنف الكلمات المفتاحية."""
    
    def __init__(self):
        self._keywords = self._load_keywords()
    
    def _load_keywords(self) -> dict[IntentType, list[re.Pattern]]:
        """تحميل أنماط الكلمات."""
        
        patterns = {
            IntentType.ZAKAT: [
                re.compile(r"زكاة", re.IGNORECASE),
                re.compile(r"نصاب", re.IGNORECASE),
                re.compile(r" Nisab", re.IGNORECASE),
            ],
            IntentType.INHERITANCE: [
                re.compile(r"إرث", re.IGNORECASE),
                re.compile(r"ميراث", re.IGNORECASE),
                re.compile(r"وراثة", re.IGNORECASE),
                re.compile(r"inherit", re.IGNORECASE),
            ],
            IntentType.FIQH_HUKM: [
                re.compile(r"حكم", re.IGNORECASE),
                re.compile(r"هل يجوز", re.IGNORECASE),
                re.compile(r"هل يحرم", re.IGNORECASE),
                re.compile(r"مكروه", re.IGNORECASE),
                re.compile(r"واجب", re.IGNORECASE),
                re.compile(r"سنة", re.IGNORECASE),
                re.compile(r"Fard", re.IGNORECASE),
                re.compile(r"Haram", re.IGNORECASE),
            ],
            IntentType.HADITH_TAKHRIJ: [
                re.compile(r"حديث", re.IGNORECASE),
                re.compile(r"صحيح", re.IGNORECASE),
                re.compile(r"ضعيف", re.IGNORECASE),
            ],
            IntentType.QURAN_VERSE: [
                re.compile(r"آية", re.IGNORECASE),
                re.compile(r"سورة", re.IGNORECASE),
                re.compile(r"قرآن", re.IGNORECASE),
            ],
            IntentType.TAFSIR: [
                re.compile(r"تفسير", re.IGNORECASE),
                re.compile(r"معنى", re.IGNORECASE),
            ],
        }
        
        return patterns
    
    async def classify(self, query: str) -> ClassificationResult:
        """تصنيف باستخدام الكلمات."""
        
        # تطبيع النص
        normalized = self._normalize_arabic(query)
        
        # حساب التطابقات
        intent_scores: dict[IntentType, int] = {}
        
        for intent, patterns in self._keywords.items():
            matches = sum(1 for p in patterns if p.search(normalized))
            if matches > 0:
                intent_scores[intent] = matches
        
        if intent_scores:
            # اختيار الأعلى
            best_intent = max(intent_scores, key=intent_scores.get)
            matches = intent_scores[best_intent]
            
            # حساب الثقة (0.85 + bonus)
            confidence = min(0.85 + (matches * 0.05), 0.95)
            
            return ClassificationResult(
                intent=best_intent,
                confidence=confidence,
                language=self._detect_language(query),
                requires_retrieval=True,
            )
        
        # الافتراضي
        return ClassificationResult(
            intent=IntentType.GENERAL_ISLAMIC,
            confidence=0.3,
            language=self._detect_language(query),
            requires_retrieval=False,
        )
    
    def _normalize_arabic(self, text: str) -> str:
        """تطبيع النص العربي."""
        # أشكال مختلفة لحرف ALEF
        text = text.replace("إ", "ا")
        text = text.replace("أ", "ا")
        text = text.replace("آ", "ا")
        
        # YEh المربوطة
        text = text.replace("ى", "ي")
        
        # إزالة التشكيل
        arabic_diacritics = re.compile(r"[\u064B-\u0652]")
        text = arabic_diacritics.sub("", text)
        
        return text
    
    def _detect_language(self, text: str) -> str:
        """كشف اللغة."""
        arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
        english_chars = len(re.findall(r"[a-zA-Z]", text))
        
        if arabic_chars > english_chars:
            return "ar"
        return "en"
```

### 4.2 Embedding Classifier

```python
class EmbeddingClassifier(QueryClassifier):
    """مصنف التضمينات."""
    
    def __init__(self, embedding_model):
        self._model = embedding_model
        self._intents = list(IntentType)
    
    async def classify(self, query: str) -> ClassificationResult:
        """تصنيف باستخدام التضمينات."""
        
        # 1. تضمين السؤال
        query_emb = await self._model.encode([query])
        
        # 2. حساب التشابه مع كل نية (محاكاة)
        # في الواقع، نحمّل مسبقاً تضمينات النيات
        # هنا نفعل simple approach
        
        # 3. إرجاع نتيجة (محاكاة)
        # في الواقع، نحسب من قاعدة بيانات
        return ClassificationResult(
            intent=IntentType.FIQH_HUKM,
            confidence=0.75,  # افتراضي
            language="ar",
            requires_retrieval=True,
        )
```

---

## 5. الطبقة 4: التوجيه

### 5.1 Agent Registry

```python
# ===== src/core/registry.py =====

from typing import Dict, Optional

class AgentRegistry:
    """سجل الوكلاء."""
    
    def __init__(self):
        self._agents: Dict[str, CollectionAgent] = {}
    
    def register(self, name: str, agent: CollectionAgent) -> None:
        """تسجيل وكيل."""
        self._agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    def get(self, name: str) -> CollectionAgent:
        """الحصول على وكيل."""
        if name not in self._agents:
            raise KeyError(f"Agent not found: {name}")
        return self._agents[name]
    
    def list_all(self) -> list[str]:
        """قائمة الوكلاء."""
        return list(self._agents.keys())
    
    def get_by_collection(self, collection: str) -> Optional[CollectionAgent]:
        """الحصول على وكل collection معين."""
        for agent in self._agents.values():
            if agent.config.collection == collection:
                return agent
        return None


# ===== Singleton Instance =====
_registry: Optional[AgentRegistry] = None

def get_registry() -> AgentRegistry:
    """الحصول على instance الـ registry."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
```

### 5.2 Router

```python
# ===== src/core/router.py =====

from src.domain.intents import IntentType

class Router:
    """موجه الأسئلة."""
    
    # خريطة النيات إلى الوكلاء
    INTENT_TO_AGENT = {
        IntentType.ZAKAT: "fiqh:rag",
        IntentType.INHERITANCE: "fiqh:rag",
        IntentType.FIQH_HUKM: "fiqh:rag",
        IntentType.FIQH_MASAIL: "fiqh:rag",
        IntentType.HADITH_TAKHRIJ: "hadith:rag",
        IntentType.QURAN_VERSE: "tafsir:rag",
        IntentType.TAFSIR: "tafsir:rag",
        IntentType.AQEEDAH: "aqeedah:rag",
        IntentType.SEERAH: "seerah:rag",
        IntentType.HISTORY: "history:rag",
        IntentType.GENERAL_ISLAMIC: "general:rag",
    }
    
    def route(self, intent: IntentType) -> str:
        """توجيه naar agent."""
        return self.INTENT_TO_AGENT.get(
            intent,
            "general:rag"  # الافتراضي
        )
```

---

## 6. الطبقة 5: الاسترجاع

### 6.1 Hybrid Searcher

```python
# ===== src/retrieval/retrievers/hybrid_retriever.py =====

from typing import Optional
from src.retrieval.schemas import RetrievalResult

class HybridSearcher:
    """بائع هجين يجمع بين البحثين."""
    
    def __init__(
        self,
        embedding_model,
        qdrant_client,
        bm25_index,
    ):
        self._semantic = DenseRetriever(embedding_model, qdrant_client)
        self._bm25 = BM25Retriever(bm25_index)
        self._rrf = ReciprocalRankFusion()
    
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
        filters: Optional[dict] = None,
    ) -> list[RetrievalResult]:
        """بحث هجين."""
        
        # البحث الدلالي (semantic)
        semantic_results = await self._semantic.search(
            query, collection, top_k * 2, filters
        )
        
        # البحث بالكلمات (BM25)
        keyword_results = await self._bm25.search(
            query, collection, top_k * 2
        )
        
        # دمج باستخدام RRF
        fused_results = self._rrf.fuse(
            [semantic_results, keyword_results],
            k=60
        )
        
        return fused_results[:top_k]
```

### 6.2 Dense Retriever

```python
# ===== src/retrieval/retrievers/dense_retriever.py =====

class DenseRetriever:
    """بائع المتجهات الكثيفة (البحث الدلالي)."""
    
    def __init__(self, embedding_model, qdrant_client):
        self._model = embedding_model
        self._qdrant = qdrant_client
    
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
        filters: Optional[dict] = None,
    ) -> list[RetrievalResult]:
        """بحث دلالي."""
        
        # 1. تضمين السؤال
        query_embeddings = await self._model.encode([query])
        query_vector = query_embeddings[0].tolist()
        
        # 2. البحث في Qdrant
        results = await self._qdrant.search(
            collection=collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filters,
            with_payload=True,
        )
        
        # 3. تحويلإلى RetrievalResult
        return [
            RetrievalResult(
                id=r.id,
                text=r.payload.get("text", ""),
                score=r.score,
                collection=collection,
                metadata=r.payload,
            )
            for r in results
        ]
```

### 6.3 BM25 Retriever

```python
# ===== src/retrieval/retrievers/bm25_retriever.py =====

import math

class BM25Retriever:
    """بائع BM25 (البحث بالكلمات)."""
    
    def __init__(self, index):
        self._index = index
        self._k1 = 1.5  # معامل التردد
        self._b = 0.75  # معيار الطول
    
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """بحث BM25."""
        
        # 1. توكنز السؤال
        query_tokens = self._tokenize(query)
        
        # 2. حسابScores لكل وثيقة
        scores: dict[str, float] = {}
        
        for doc_id, doc in self._index.documents.items():
            doc_tokens = self._tokenize(doc.text)
            score = self._bm25_score(query_tokens, doc_tokens)
            if score > 0:
                scores[doc_id] = score
        
        # 3. ترتيب واختيار الأعلى
        sorted_docs = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]
        
        return [
            RetrievalResult(
                id=doc_id,
                text=self._index.documents[doc_id].text,
                score=score,
                collection=collection,
                metadata=self._index.documents[doc_id].metadata,
            )
            for doc_id, score in sorted_docs
        ]
    
    def _tokenize(self, text: str) -> list[str]:
        """تقسيم إلى Words."""
        # إزالة التشكيل
        text = re.sub(r"[\u064B-\u0652]", "", text)
        # التقسيم
        return re.findall(r"[\w]+", text.lower())
    
    def _bm25_score(
        self,
        query_tokens: list[str],
        doc_tokens: list[str],
    ) -> float:
        """حسابScore BM25."""
        
        doc_len = len(doc_tokens)
        avg_doc_len = self._index.avg_doc_len
        
        score = 0.0
        doc_freq = {}
        
        for term in query_tokens:
            # تردد المصطلح في الوثيقة
            tf = doc_tokens.count(term)
            if tf == 0:
                continue
            
            # عدد الوثائق التي تحتوي المصطلح
            df = self._index.term_doc_freq.get(term, 0)
            
            # IDF
            idf = math.log(
                (self._index.num_docs - df + 0.5) / (df + 0.5) + 1
            )
            
            # BM25 formula
            numerator = tf * (self._k1 + tf)
            denominator = tf + self._k1 * (
                1 - self._b + self._b * doc_len / avg_doc_len
            )
            
            score += idf * (numerator / denominator)
        
        return score
```

### 6.4 Reciprocal Rank Fusion (RRF)

```python
# ===== src/retrieval/fusion/rrf.py =====

class ReciprocalRankFusion:
    """دمج الترتيب المتبادل (RRF)."""
    
    def __init__(self, k: int = 60):
        """k هو معامل الانتظام."""
        self._k = k
    
    def fuse(
        self,
        result_lists: list[list[RetrievalResult]],
    ) -> list[RetrievalResult]:
        """دمج قوائم النتائج."""
        
        # 1. حسابScores
        doc_scores: dict[str, float] = {}
        
        for results in result_lists:
            for rank, result in enumerate(results):
                doc_id = result.id
                
                # صيغة RRF: 1 / (k + rank)
                contribution = 1.0 / (self._k + rank + 1)
                
                doc_scores[doc_id] = (
                    doc_scores.get(doc_id, 0.0) + contribution
                )
        
        # 2. ترتيب
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        # 3. إعادة النتائج
        # (نحتاج للحصول على التفاصيل من الـ index)
        return []  # TODO: اكمل
```

---

## 7. الطبقة 6: التحقق

### 7.1 Suite Builder

```python
# ===== src/verifiers/suite_builder.py =====

class VerificationCheck(BaseModel):
    """فحص واحد."""
    name: str
    fail_policy: str  # "abstain" | "warn" | "proceed"
    enabled: bool = True


class VerificationSuite(BaseModel):
    """مجموعة فحوصات."""
    checks: list[VerificationCheck]


class VerificationReport(BaseModel):
    """نتيجة التحقق."""
    status: str  # "passed" | "failed" | "abstained"
    confidence: float
    verified_passages: list[str]
    abstained: bool = False
    abstention_reason: Optional[str] = None


def build_suite(agent_name: str) -> VerificationSuite:
    """بناء مجموعة تحقق للوكيل."""
    
    suites = {
        "fiqh": VerificationSuite(checks=[
            VerificationCheck(
                name="exact_quote",
                fail_policy="abstain"
            ),
            VerificationCheck(
                name="source_attribution",
                fail_policy="warn"
            ),
            VerificationCheck(
                name="contradiction_detector",
                fail_policy="proceed"
            ),
            VerificationCheck(
                name="evidence_sufficiency",
                fail_policy="abstain"
            ),
        ]),
        "hadith": VerificationSuite(checks=[
            VerificationCheck(
                name="exact_quote",
                fail_policy="abstain"
            ),
            VerificationCheck(
                name="hadith_grade",
                fail_policy="abstain"
            ),
        ]),
    }
    
    return suites.get(agent_name, VerificationSuite(checks=[]))
```

### 7.2 Exact Quote Checker

```python
# ===== src/verifiers/exact_quote.py =====

import re

async def check_exact_quote(
    answer: str,
    passages: list[RetrievalResult],
) -> CheckResult:
    """فحص الاقتباسات Exact."""
    
    # استخراج الاقتباسات من الإجابة
    # يتوقع أن تكون بين []
    quote_pattern = re.compile(r"\[(\d+)\]([^\[]+)")
    quotes = quote_pattern.findall(answer)
    
    for source_num, quote_text in quotes:
        # البحث في المصادر
        found = False
        for passage in passages:
            if quote_text.strip() in passage.text:
                found = True
                break
        
        if not found:
            return CheckResult(
                status="failed",
                message=f"اقتباس غير موجود في المصادر"
            )
    
    return CheckResult(status="passed")
```

---

## 8. الطبقة 7: التوليد

### 8.1 LLM Client

```python
# ===== src/generation/llm_client.py =====

from typing import Optional

class LLMClient:
    """عميل LLM (OpenAI/Groq)."""
    
    def __init__(
        self,
        api_key: str,
        provider: str = "openai",
    ):
        self._api_key = api_key
        self._provider = provider
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """توليد نص."""
        
        # بناء الرسائل
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # استدعاء API المناسب
        if self._provider == "openai":
            response = await self._call_openai(
                messages, model, temperature, max_tokens
            )
        elif self._provider == "groq":
            response = await self._call_groq(
                messages, model, temperature, max_tokens
            )
        
        return response
    
    async def _call_openai(
        self,
        messages: list,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """استدعاء OpenAI."""
        import openai
        
        response = await openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content
    
    async def _call_groq(
        self,
        messages: list,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """استدعاء Groq."""
        from groq import AsyncGroq
        
        client = AsyncGroq(api_key=self._api_key)
        
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return response.choices[0].message.content
```

### 8.2 Prompt Builder

```python
# ===== src/agents/collection/base.py =====

class BaseCollectionAgent:
    """الوكيل الأساسي."""
    
    def _build_prompt(
        self,
        query: str,
        contexts: list[str],
    ) -> str:
        """بناء سؤال LLM."""
        
        # تحميل النموذج
        template = self._load_prompt_template()
        
        # بناء السياق
        context_text = "\n\n".join([
            f"[المصدر {i+1}]:\n{ctx}"
            for i, ctx in enumerate(contexts)
        ])
        
        # استبدال العناصر
        prompt = template.replace("{{query}}", query)
        prompt = prompt.replace("{{context}}", context_text)
        
        return prompt
    
    def _load_prompt_template(self) -> str:
        """تحميل نموذج السؤال."""
        # قراءة من ملف
        with open(f"prompts/{self.config.name}_agent.txt") as f:
            return f.read()
```

---

## 9. الطبقة 8: المعالجة

### 9.1 Strip CoT Leakage

```python
# ===== src/agents/base.py =====

import re

_COT_PATTERNS = [
    # Markdown Headers
    re.compile(
        r"##?\s*(?:Analysis|Reasoning|Thought).*?\n\n",
        re.IGNORECASE | re.DOTALL
    ),
    # XML Tags
    re.compile(
        r"<\s*(?:analysis|reasoning|thought)\s*>.*?<\s*/\s*>",
        re.IGNORECASE | re.DOTALL
    ),
    # Let me
    re.compile(
        r"###\s*(?:Let me|I'll|I will).*?\n\s*",
        re.IGNORECASE
    ),
    # Numbers with periods
    re.compile(
        r"^\d+\.\s+.*?\n",
        re.MULTILINE
    ),
]

def strip_cot_leakage(text: str) -> str:
    """إزالة تسرب التفكير."""
    if not text:
        return text
    
    result = text
    for pattern in _COT_PATTERNS:
        result = pattern.sub("", result)
    
    return result.strip()
```

---

## 10. المخططات والجداول

### 10.1 جدول الأزمنة

| الطبقة | الوظيفة | الزمن (ms) |
|--------|---------|-----------|
| API | استلام الطلب | <1 |
| Validation | التحقق | <1 |
| Classification | التصنيف | <50 |
| Routing | التوجيه | <5 |
| Semantic Search | البحث الدلالي | 50-200 |
| BM25 Search | البحث بـ BM25 | 10-50 |
| RRF | دمج النتائج | <5 |
| Verification | التحقق | 50-200 |
| LLM Generation | التوليد | 500-2000 |
| Post-processing | المعالجة | <5 |
| Citation Building | بناء الاقتباسات | <10 |
| **الإجمالي** | | **700-3000** |

### 10.2 جدول الأخطاء

| الكود | الوصف |
|-------|------|
| 400 | طلب غير صالح |
| 401 | غير مصرح |
| 422 | فشل التحقق |
| 500 | خطأ داخلي |
| 503 | الخدمة unavailable |

### 10.3 المخطط الكامل

```
┌────────────────────────────────────────────────────────────┐
│                   _USER QUERY                              │
│              "ما حكم صلاة الجماعة؟"                        │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│              API LAYER (ask.py)                          │
│  @ask_router.post("")                               │
│  ask_question(request) → AskResponse         │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│            VALIDATION (schemas/ask.py)                 │
│  AskRequest validation                          │
│  - query: non-empty, 1-1000 chars              │
│  - language: "ar" | "en"                    │
│  - madhhab: optional                      │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│        CLASSIFICATION (hybrid_classifier.py)          │
│  MasterHybridClassifier.classify()                 │
│                                                      │
│  Step 1: Keyword match (<1ms)                       │
│  ├─ "حكم" → FIQH_HUKM                             │
│  ├─ "زكاة" → ZAKAT                               │
│  └─ "آية" → QURAN_VERSE                          │
│                                                      │
│  Step 2: Embedding similarity (10-50ms)             │
│                                                      │
│  Returns: ClassificationResult(intent, conf)      │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│              ROUTING (registry.py)                    │
│  Router.route(intent) → agent_name                   │
│                                                      │
│  FIQH_HUKM → "fiqh:rag"                          │
│  HADITH → "hadith:rag"                            │
│  TAFSIR → "tafsir:rag"                          │
│  DEFAULT → "general:rag"                         │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│      RETRIEVAL (hybrid_retriever.py)                  │
│  HybridSearcher.search(query, collection, top_k) │
│                                                      │
│  1. Dense Search → semantic results              │
│     (BGE-M3 embeddings + Qdrant)              │
│                                                      │
│  2. BM25 Search → keyword results            │
│     (Okapi BM25 algorithm)                   │
│                                                      │
│  3. RRF Fusion → combined results             │
│     (Reciprocal Rank Fusion, k=60)            │
│                                                      │
│  Returns: list[RetrievalResult]               │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│       VERIFICATION (suite_builder.py)                │
│  VerificationSuite.run(answer, passages)           │
│                                                      │
│  Checks:                                       │
│  ├─ exact_quote (اقتباس مطابق)                 │
│  ├─ source_attribution (مصدر صحيح)           │
│  ├─ contradiction_detector (تناقض)            │
│  └─ evidence_sufficiency (كفاية)          │
│                                                      │
│  Policies:                                     │
│  ├─ abstain → return "don't know"             │
│  ├─ warn → continue with warning            │
│  └─ proceed → continue                    │
│                                                      │
│  Returns: VerificationReport               │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│       GENERATION (llm_client.py)                   │
│  LLMClient.generate(prompt, system_prompt)      │
│                                                      │
│  1. Build prompt (prompt template + context)    │
│  2. Get system prompt                          │
│  3. Call LLM (OpenAI/Groq)                    │
│                                                      │
│  Returns: raw_answer                          │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│    POST-PROCESSING (agents/base.py)             │
│  strip_cot_leakage(answer)                     │
│                                                      │
│  Removes:                                     │
│  ├─ ## Analysis                               │
│  ├─ <analysis>...</analysis>                 │
│  └─ ### Let me think                         │
│                                                      │
│  Returns: clean_answer                        │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│    CITATION BUILDING (agents/base.py)              │
│  _build_citations(passages)                   │
│                                                      │
│  For each passage:                           │
│  ├─ source_id                                │
│  ├─ text (first 200 chars)                  │
│  ├─ book_title                              │
│  ├─ page                                    │
│  └─ grade                                   │
│                                                      │
│  Returns: list[Citation]                    │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│                    RESPONSE                          │
���  AskResponse(                                    │
│    answer: str,                                  │
│    citations: list,                              │
│    intent: str,                                  │
│    confidence: float,                            │
│    processing_time_ms: int                      │
│  )                                              │
└────────────────────────────────────────────────────────────┘
```

---

## المراجع

- [src/api/routes/ask.py](src/api/routes/ask.py) - API routes
- [src/api/schemas/ask.py](src/api/schemas/ask.py) - Schemas
- [src/application/hybrid_classifier.py](src/application/hybrid_classifier.py) - Classifier
- [src/core/registry.py](src/core/registry.py) - Registry
- [src/retrieval/retrievers/*.py](src/retrieval/retrievers/) - Retrievers
- [src/verifiers/suite_builder.py](src/verifiers/suite_builder.py) - Verification
- [src/generation/llm_client.py](src/generation/llm_client.py) - LLM Client
- [src/agents/base.py](src/agents/base.py) - Base agent

---

**آخر تحديث**: أبريل 2026

**الإصدار**: 1.0

**الكاتب**: Burhan Documentation Team