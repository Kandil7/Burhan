# 🕌 دليل نظام RAG الكامل والشامل

## شرح كل خطوة في منطق نظام الاسترجاع والتوليد

هذا الدليل يشرح بالتفصيل المطلق كل خطوة في نظام RAG الخاص بمشروع Burhan، بدءاً من استلام سؤال المستخدم وحتى إرسال الإجابة النهائية.，我将详细解释每个组件、每个函数以及它们如何协同工作。

---

## 表 المحتويات

1. [/مقدمة إلى نظام RAG](#1-مقدمة-إلى-نظام-rag)
2. [/الخطوة الأولى: دخول الطلب](#2-الخطوة-الأولى-دخول-الطلب)
3. [/الخطوة الثانية: التحقق من صحة الطلب](#3-الخطوة-الثانية-التحقق-من-صحة-الطلب)
4. [/الخطوة الثالثة: تصنيف النية](#4-الخطوة-الثالثة-تصنيف-النية)
5. [/الخطوة الرابعة: التوجيه واختيار الوكيل](#5-الخطوة-الرابعة-التوجيه-واختيار-الوكيل)
6. [/الخطوة الخامسة: استرجاع الوثائق](#6-الخطوة-الخامسة-استرجاع-الوثائق)
7. [/الخطوة السادسة: التحقق من الدقة](#7-الخطوة-السادسة-التحقق-من-الدقة)
8. [/الخطوة السابعة: توليد الإجابة](#8-الخطوة-السابعة-توليد-الإجابة)
9. [/الخطوة الثامنة: معالجة الإجابة](#9-الخطوة-الثامنة-معالجة-الإجابة)
10. [/الخطوة التاسعة: بناء الاقتباسات](#10-الخطوة-التاسعة-بناء-الاقتباسات)
11. [/الخطوة العاشرة: إرسال الاستجابة](#11-الخطوة-العاشرة-إرسال-الاستجابة)
12. [/ملخص التدفق الكامل](#12-ملخص-التدفق-الكامل)

---

## 1. مقدمة إلى نظام RAG

### 1.1 ما هو نظام RAG؟

نظام RAG (الاسترجاع والتوليد المحسّن) هو مزيج من تقنيتين:

| التقنية | الوظيفة | مثال |
|---------|---------|------|
| **الاسترجاع (Retrieval)** | البحث في قاعدة البيانات | البحث عن وثائق ذات صلة |
| **التوليد (Generation)** | إنشاء النص | استخدام LLM للتوليد |

### 1.2 لماذا نستخدم RAG؟

```
WITHOUT RAG:
المستخدم: ما حكم صلاة الجماعة؟
LLM: لا أعرف، سأخمن... (قد يكذب!)

WITH RAG:
المستخدم: ما حكم صلاة الجماعة؟
    ↓
RETRIEVE: ابحث في الموسوعة الفقهية
    ↓
GET: "صلاة الجماعة فرض عين على القادر"
    ↓
GENERATE: أضف المصدر وولّد إجابة دقيقة
    ↓
الإجابة: "صلاة الجماعة فرض عين على كل ذكر بالغ قادر..."
```

### 1.3 نظام RAG في Burhan

يستخدم Burhan نسخة محسنة من RAG تتضمن:

- **بحث هجين**: دمج البحث الدلالي والبحث بالكلمات
- **التحقق**: التأكد من دقة الاقتباسات
- **طبقة متعددة**: وكلاء متخصصون لكل مجال

---

## 2. الخطوة الأولى: دخول الطلب

### 2.1 نظرة عامة

الخطوة الأولى هي استلام سؤال المستخدم وتحويله إلى форма طلب مفهوم.

### 2.2 نقطة النهاية

الطلب يدخل من خلال:

```python
# في src/api/routes/ask.py
@ask_router.post("", response_model=AskResponse)
async def ask_question(request: AskRequest) -> AskResponse:
```

### 2.3 عنوان النهاية

```
POST /api/v1/ask
```

أو في الإصدار الجديد:

```
POST /ask
```

### 2.4 نموذج الطلب

```python
# في src/api/schemas/ask.py
class AskRequest(BaseModel):
    """نموذج طلب السؤال."""
    query: str = Field(..., description="سؤال المستخدم")
    language: str = Field(default="ar", description="لغة السؤال")
    collection: str | None = Field(default=None, description="المجموعة المحددة")
    madhhab: str | None = Field(default=None, description="المذهب المفضل")
```

### 2.5 مثال على طلب

```json
{
    "query": "ما حكم صلاة الجماعة في الإسلام؟",
    "language": "ar",
    "madhhab": "hanafi"
}
```

### 2.6 ما يحدث داخلياً

عند دخول الطلب:

```python
async def ask_question(request: AskRequest) -> AskResponse:
    """معالجة سؤال المستخدم."""
    
    # 1. بدء المؤقت
    start_time = time.time()
    
    # 2. التحقق من صحة الطلب (تلقائي بواسطة Pydantic)
    # إذا كان غير صالح، يرجع خطأ فوراً
    
    # 3. تسجيل الطلب
    logger.info(f"استلام سؤال: {request.query}")
    
    # 4. متابعة المعالجة...
```

### 2.7 معالجة الأخطاء

إذا كان الطلب غير صالح:

```python
# مثال على خطأ
{
    "detail": [
        {
            "loc": ["body", "query"],
            "msg": "Field required",
            "type": "missing"
        }
    ]
}
```

---

## 3. الخطوة الثانية: التحقق من صحة الطلب

### 3.1 نظرة عامة

الخطوة الثانية هي التأكد من أن البيانات المقدمة صالحة ومحددة.

### 3.2 التحقق التلقائي

Pydantic يقوم بالتحقق تلقائياً:

```python
class AskRequest(BaseModel):
    """نموذج طلب مع قواعد التحقق."""
    
    query: str = Field(
        ...,  # مطلوب
        min_length=1,  # 최소 1 حرف
        max_length=1000,  # الحد الأقصى 1000 حرف
        description="سؤال المستخدم"
    )
    
    language: str = Field(
        default="ar",  # الافتراضي
        pattern="^(ar|en)$",  # فقط Arabic أو English
        description="لغة السؤال"
    )
    
    collection: str | None = Field(
        default=None,  # اختياري
        description="المجموعة المحددة"
    )
    
    madhhab: str | None = Field(
        default=None,
        pattern="^(hanafi|maliki|shafii|hanbali)$",
        description="المذهب المفضل"
    )
    
    model_config = {
        "extra": "forbid"  #不允许 حقول إضافية
    }
```

### 3.3 قواعد التحقق التفصيلية

| الحقل | النوع | القاعدة | رسالة الخطأ |
|------|------|---------|-------------|
| `query` | مطلوب | 1-1000 حرف | "Field required" |
| `language` | اختياري | "ar" أو "en" فقط | "string should match pattern" |
| `madhhab` | اختياري | salah من أربعة مذاهب | "string should match pattern" |

### 3.4 التحقق اليدوي (اختياري)

بالإضافة إلى التحقق التلقائي:

```python
async def validate_request(request: AskRequest) -> bool:
    """تحقق يدوي إضافي."""
    
    # التحقق من أن السؤال ليس فارغاً بعد إزالة ��لمسافات
    if not request.query.strip():
        raise ValueError("السؤال لا يمكن أن يكون فارغاً")
    
    # التحقق من أن السؤال يحتوي على أحرف عربية أو إنجليزية
    if not re.search(r"[\u0600-\u06FFa-zA-Z]", request.query):
        raise ValueError("السؤال يجب أن يحتوي على أحرف عربية أو إنجليزية")
    
    return True
```

### 3.5 ما بعد التحقق الناجح

بعد نجاح التحقق:

```python
# إنشاء كائن الطلب النهائي
valid_request = AskRequest(
    query="ما حكم صلاة الجماعة؟",
    language="ar",
    madhhab="hanafi"
)

# تحويل إلى AgentInput
agent_input = AgentInput(
    query=valid_request.query,
    language=valid_request.language,
    metadata={"madhhab": valid_request.madhhab}
)
```

---

## 4. الثالثة: الخطوة تصنيف النية

### 4.1 نظرة عامة

الخطوة الثالثة هي تحديد نوع سؤال المستخدم (النية)，以便 توجيهه إلى الوكيل الصحيح.

### 4.2 التصنيف الهجين (Hybrid Classification)

نظام Burhan يستخدم تصنيفاً هجيناً يجمع بين طريقتين:

```python
# في src/application/hybrid_classifier.py
class MasterHybridClassifier:
    """مصنف النية الهجين."""
    
    async def classify(self, query: str) -> ClassificationResult:
        """تصنيف النية."""
        
        # الخطوة 1: البحث بالكلمات المفتاحية (سريع)
        kw_result = await self._keyword_classifier.classify(query)
        
        # إذا كانت الثقة عالية بما يكفي، استخدم النتيجة فوراً
        if kw_result.confidence >= 0.85:
            return kw_result
        
        # الخطوة 2: البحث بالم embeddings (أدق لكن أبطأ)
        if self._embedding_classifier:
            emb_result = await self._embedding_classifier.classify(query)
            
            # اختر النتيجة الأعلى ثقة
            if emb_result.confidence > kw_result.confidence:
                return emb_result
        
        # الخطوة 3: استخدم keyword كنهاية أخيرة
        return kw_result
```

### 4.3 المصنف الأول: الكلمات المفتاحية

```python
# في src/application/classifier_factory.py
class KeywordBasedClassifier:
    """مصنف الكلمات المفتاحية."""
    
    def __init__(self):
        self._keywords = KEYWORD_PATTERNS
    
    async def classify(self, query: str) -> ClassificationResult:
        """تصنيف باستخدام الكلمات المفتاحية."""
        
        # 1. تطبيع النص
        normalized = self._normalize_arabic(query)
        
        # 2. البحث عن التطابقات
        for intent, patterns in self._keywords.items():
            matches = sum(1 for p in patterns if p.search(normalized))
            
            if matches >= 2:  # الحد الأدنى
                confidence = min(0.85 + (matches * 0.05), 0.95)
                return ClassificationResult(
                    intent=intent,
                    confidence=confidence,
                    requires_retrieval=True,
                )
        
        # 3. الافتراضي
        return ClassificationResult(
            intent="ISLAMIC_KNOWLEDGE",
            confidence=0.3,
            requires_retrieval=False,
        )
```

### 4.4 أنماط الكلمات المفتاحية

```python
# في src/domain/intents.py
KEYWORD_PATTERNS = {
    # فقه - أحكام
    "FIQH_HUKM": [
        r"حكم",
        r"��ل يجوز",
        r"هل يحرم",
        r"مكروه",
        r"واجب",
        r"سنة",
        r"Fard",
        r"Haram",
        r"Makruh",
        r"Mustahabb",
    ],
    
    # زكاة
    "ZAKAT": [
        r"زكاة",
        r"نصاب",
        r" Nisab",
        r"الزكاة",
    ],
    
    # إرث
    "INHERITANCE": [
        r"إرث",
        r"ميراث",
        r"وراثة",
        r" inherit",
    ],
    
    # حديث
    "HADITH_TAKHRIJ": [
        r"حديث",
        r"صحيح",
        r"ضعيف",
        r"الحديث",
    ],
    
    # قرآن
    "QURAN_VERSE": [
        r"آية",
        r"سورة",
        r"قرآن",
        r"القرآن",
    ],
    
    # تفسير
    "TAFSIR": [
        r"تفسير",
        r"معنى",
        r"فسير",
    ],
    
    # عقيدة
    "AQEEDAH": [
        r"عقيدة",
        r"إيمان",
        r"توحيد",
    ],
    
    # سيرة
    "SEERAH": [
        r"سيرة",
        r"النبي",
        r"رسول",
    ],
}
```

### 4.5 المصنف الثاني: التضمينات (Embeddings)

```python
# في src/application/embedding_classifier.py
class EmbeddingClassifier:
    """مصنف التضمينات."""
    
    def __init__(self, embedding_model):
        self._model = embedding_model
        self._intent_embeddings = self._load_intent_embeddings()
    
    async def classify(self, query: str) -> ClassificationResult:
        """تصنيف باستخدام التضمينات."""
        
        # 1. تحويل السؤال إلى متجه
        query_embedding = await self._model.encode([query])
        
        # 2. حساب التشابه مع كل نية
        similarities = []
        for intent, intent_emb in self._intent_embeddings.items():
            similarity = cosine_similarity(query_embedding, intent_emb)
            similarities.append((intent, similarity))
        
        # 3. اختيار الأعلى تشابهاً
        best = max(similarities, key=lambda x: x[1])
        
        return ClassificationResult(
            intent=best[0],
            confidence=best[1],
            requires_retrieval=best[1] > 0.5,
        )
```

### 4.6 مستويات الأولوية

الأولويات من 1 (الأعلى) إلى 10 (الأدنى):

```python
# في src/domain/intents.py
INTENT_PRIORITIES = {
    "ZAKAT": 1,           # الأعلى - قضايا مالية مهمة
    "INHERITANCE": 2,      # إرث - قضايا قانونية مهمة
    "FIQH_HUKM": 3,       # أحكام - فقه أساسي
    "FIQH_MASAIL": 4,       # مسائل - فقه
    "HADITH_TAKHRIJ": 5,   # حديث - مصادر مهمة
    "QURAN_VERSE": 6,       # آيات - مصادر مهمة
    "TAFSIR": 7,           # تفسير - قرآن
    "AQEEDAH": 8,         # عقيدة - أساسيات
    "SEERAH": 9,          # سيرة - تاريخ
    "GENERAL_ISLAMIC": 10,   # عام - افتراضي
}
```

### 4.7 النيات الفرعية للقرآن

4 subtypes للقرآن specifically:

```python
QuranSubIntent = Enum("QuranSubIntent", {
    "VERSE_LOOKUP": "استعلام عن آية محددة",
    "ANALYTICS": "إحصاءات قرآنية",
    "INTERPRETATION": "تفسير آية",
    "QUOTATION_VALIDATION": "تحقق من اقتباس قرآني",
})
```

### 4.8 مخرجات التصنيف

```python
class ClassificationResult:
    """نتيجة التصنيف."""
    intent: IntentType              # نوع النية
    confidence: float            # 0.0 - 1.0
    language: str              # "ar" أو "en"
    requires_retrieval: bool   # هل يحتاج استرجاع؟
    sub_intent: QuranSubIntent | None = None
```

### 4.9 مثال على تصنيف

**الإدخال**: "ما حكم صلاة الجمعة؟"

**المخرجات**:

```python
{
    "intent": "FIQH_HUKM",
    "confidence": 0.92,
    "language": "ar",
    "requires_retrieval": True
}
```

---

## 5. الرابعة: التوجيه واختيار الوكيل

### 5.1 نظرة عامة

الخطوة الرابعة هي توجيه السؤال إلى الوكيل المناسب based on the intent classification.

### 5.2 سجل الوكلاء

```python
# في src/core/registry.py
class AgentRegistry:
    """سجل الوكلاء."""
    
    def __init__(self):
        self._agents: dict[str, CollectionAgent] = {}
    
    def register(self, name: str, agent: CollectionAgent) -> None:
        """تسجيل وكيل."""
        self._agents[name] = agent
    
    def get(self, name: str) -> CollectionAgent:
        """الحصول على وكيل."""
        if name not in self._agents:
            raise KeyError(f"الوكيل غير موجود: {name}")
        return self._agents[name]
    
    def list_all(self) -> list[str]:
        """قائمة جميع الوكلاء."""
        return list(self._agents.keys())
```

### 5.3 تسجيل الوكلاء

عند بدء التطبيق (في lifespan):

```python
# في src/api/lifespan.py
async def lifespan(app: FastAPI):
    """بدء التطبيق."""
    
    registry = get_registry()
    
    # تحميل التكوينات
    config_manager = get_config_manager()
    
    # تسجيل الوكلاء
    # FiQH
    fiqh_config = config_manager.get_agent_config("fiqh")
    registry.register("fiqh:rag", FiQHCollectionAgent(fiqh_config))
    
    # Hadith
    hadith_config = config_manager.get_agent_config("hadith")
    registry.register("hadith:rag", HadithCollectionAgent(hadith_config))
    
    # Tafsir
    tafsir_config = config_manager.get_agent_config("tafsir")
    registry.register("tafsir:rag", TafsirCollectionAgent(tafsir_config))
    
    # Aqeedah
    aqeedah_config = config_manager.get_agent_config("aqeedah")
    registry.register("aqeedah:rag", AqeedahCollectionAgent(aqeedah_config))
    
    # ... المزيد من الوكلاء
```

### 5.4 خريطة التوجيه

```python
# في src/core/router.py
INTENT_TO_AGENT = {
    # FiQH
    "FIQH_HUKM": "fiqh:rag",
    "FIQH_MASAIL": "fiqh:rag",
    
    # Hadith
    "HADITH_TAKHRIJ": "hadith:rag",
    
    # Quran/Tafsir
    "QURAN_VERSE": "tafsir:rag",
    "TAFSIR": "tafsir:rag",
    
    # Aqeedah
    "AQEEDAH": "aqeedah:rag",
    
    # Seerah
    "SEERAH": "seerah:rag",
    
    # History
    "HISTORY": "history:rag",
    
    # General
    "ISLAMIC_KNOWLEDGE": "general:rag",
}
```

### 5.5 التوجيه

```python
# في src/application/use_cases/answer_query.py
class AnswerQueryUseCase:
    """حالة استخدام الإجابة على السؤال."""
    
    def __init__(self, agent_registry, router):
        self.agents = agent_registry
        self.router = router
    
    async def execute(self, input: AnswerQueryInput) -> AnswerQueryOutput:
        """تنفيذ."""
        
        # 1. تصنيف النية
        classification = await self.router.route(input.query)
        
        # 2. تحديد الوكيل
        agent_name = self._get_agent_for_intent(classification.intent)
        
        # 3. الحصول على الوكيل
        agent = self.agents.get(agent_name)
        
        # 4. تحويل الإدخال
        agent_input = AgentInput(
            query=input.query,
            language=input.language,
            metadata=input.metadata,
        )
        
        # 5. تنفيذ الوكيل
        result = await agent.execute(agent_input)
        
        # 6. إخراج
        return AnswerQueryOutput(
            answer=result.answer,
            citations=result.citations,
            intent=classification.intent.value,
            confidence=result.confidence,
            processing_time_ms=elapsed,
        )
```

### 5.6 اختيار الوكيل

```python
def _get_agent_for_intent(intent: IntentType) -> str:
    """الحصول على اسم الوكيل للنية."""
    return INTENT_TO_AGENT.get(intent, "general:rag")
```

---

## 6. الخامسة: الخطوة استرجاع الوثائق

### 6.1 نظرة عامة

الخطوة الخامسة هي البحث في قاعدة البيانات عن الوثائق ذات الصلة بالسؤال.

### 6.2 البحث الهجين (Hybrid Search)

نظام Burhan يجمع بين طريقتين للبحث:

```python
# في src/retrieval/retrievers/hybrid_retriever.py
class HybridSearcher:
    """بائع هجين."""
    
    def __init__(self, embedding_model, qdrant_client):
        self._semantic = DenseRetriever(embedding_model, qdrant_client)
        self._bm25 = BM25Retriever()
        self._rrf = ReciprocalRankFusion()
    
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        """بحث هجين."""
        
        # البحث الدلالي
        semantic_results = await self._semantic.search(
            query, collection, top_k
        )
        
        # البحث بـ BM25
        keyword_results = await self._bm25.search(
            query, collection, top_k
        )
        
        # دمج النتائج
        fused = self._rrf.fuse(
            [semantic_results, keyword_results],
            k=60
        )
        
        return fused[:top_k]
```

### 6.3 البحث الدلالي (Semantic Search)

```python
# في src/retrieval/retrievers/dense_retriever.py
class DenseRetriever:
    """بائع المتجهات الكثيفة."""
    
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int,
    ) -> list[RetrievalResult]:
        """بحث دلالي."""
        
        # 1. تحويل السؤال إلى متجه
        query_vector = await self._embedding_model.encode([query])
        
        # 2. البحث في Qdrant
        results = await self._qdrant.search(
            collection=collection,
            query_vector=query_vector[0].tolist(),
            limit=top_k,
            with_payload=True,
        )
        
        # 3. تحويل النتائج
        return [self._to_result(r) for r in results]
```

### 6.4 البحث بـ BM25

```python
# في src/retrieval/retrievers/bm25_retriever.py
class BM25Retriever:
    """بائع BM25."""
    
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int,
    ) -> list[RetrievalResult]:
        """بحث بالكلمات المفتاحية."""
        
        # 1. فهرسة السؤال
        query_tokens = self._tokenize(query)
        
        # 2. حسابScores
        scores = self._index.score(query_tokens)
        
        # 3. ترتيب النتائج
        top_results = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        return [self._to_result(doc_id, score) for doc_id, score in top_results]
```

### 6.5 دمج النتائج (Reciprocal Rank Fusion)

```python
# في src/retrieval/fusion/rrf.py
class ReciprocalRankFusion:
    """دمج الترتيب المتبادل."""
    
    def fuse(
        self,
        result_lists: list[list[RetrievalResult]],
        k: int = 60,
    ) -> list[RetrievalResult]:
        """دمج النتائج."""
        
        scores = {}
        
        for results in result_lists:
            for rank, result in enumerate(results):
                doc_id = result.id
                
                # صيغة RRF
                score = 1.0 / (k + rank + 1)
                scores[doc_id] = scores.get(doc_id, 0) + score
        
        # ترتيب بالنتيجة النهائية
        sorted_docs = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [self._get_result(doc_id) for doc_id, _ in sorted_docs]
```

### 6.6 استراتيجية الاسترجاع

كل وكيل له استراتيجية خاصة:

```python
# في src/retrieval/strategies.py
RETRIEVAL_MATRIX = {
    "fiqh_agent": RetrievalStrategy(
        collection="fiqh_passages",
        top_k=15,
        filters={
            "type": "fiqh",
            "source": "trusted",
        },
        rerank=True,
    ),
    
    "hadith_agent": RetrievalStrategy(
        collection="hadith_passages",
        top_k=10,
        filters={
            "grade$in": ["sahih", "hasan"],
        },
        rerank=True,
    ),
    
    "tafsir_agent": RetrievalStrategy(
        collection="tafsir_passages",
        top_k=10,
        filters={"type": "tafsir"},
        rerank=True,
    ),
    
    # الافتراضي
    "default": RetrievalStrategy(
        collection="default",
        top_k=10,
        filters=None,
        rerank=False,
    ),
}

def get_strategy(agent_name: str) -> RetrievalStrategy:
    """الحصول على استراتيجية الوكيل."""
    return RETRIEVAL_MATRIX.get(agent_name, RETRIEVAL_MATRIX["default"])
```

### 6.7 نموذج النتيجة

```python
class RetrievalResult(BaseModel):
    """نتيجة الاسترجاع."""
    id: str                        # معرف الوثيقة
    text: str                      # نص الوثيقة
    score: float                   # الدرجة
    collection: str               # المجموعة
    metadata: dict               # البيانات الوصفية
    
    # حقول إضافية
    book_title: str | None        # عنوان الكتاب
    author: str | None         # المؤلف
    page: int | None          # الصفحة
    grade: str | None        # الدرجة (للأحاديث)
    chapter: str | None      # الفصل
```

### 6.8 مثال على استرجاع

**الإدخال**: "ما حكم صلاة الجماعة؟"

**المخرجات**:

```python
[
    {
        "id": "fiqh_passage_001",
        "text": "صلاة الجماعة فرض عين على كل ذكر بالغ قادر خلافاً للعلماء.\n"
                "قال ابن المنذر: أجمع العلماء على أن صلاة الجماعة.vast"
                "هي الفرض العين.",
        "score": 0.92,
        "collection": "fiqh_passages",
        "metadata": {
            "book_title": "الموسوعة الفقهية",
            "author": "الشيخ عبد الرحمن السديس",
            "page": 150,
            "chapter": "صلاة الجماعة"
        }
    },
    {
        "id": "fiqh_passage_002",
        "text": "ويستحب التكبير في أول صلاة العيد...",
        "score": 0.85,
        "collection": "fiqh_passages",
        "metadata": {
            "book_title": "تحديد فروع الإيمان",
            "author": "ابن حزم",
            "page": 78
        }
    },
]
```

---

## 7. السادسة: الخطوة التحقق من الدقة

### 7.1 نظرة عامة

الخطوة السادسة هي التأكد من أن المعلومات المسترجعة دقيقة وموثقة.

### 7.2 مجموعة التحقق

لكل وكيل مجموعة تحقق خاصة:

```python
# في src/verifiers/suite_builder.py
def build_suite(agent_name: str) -> VerificationSuite:
    """بناء مجموعة التحقق للوكيل."""
    
    suites = {
        "fiqh": VerificationSuite(
            checks=[
                # 1. التحقق من الاقتباس الدقيق
                VerificationCheck(
                    name="exact_quote",
                    fail_policy="abstain",
                    enabled=True,
                ),
                # 2. التحقق من المصدر
                VerificationCheck(
                    name="source_attribution",
                    fail_policy="warn",
                    enabled=True,
                ),
                # 3. التحقق من التناقضات
                VerificationCheck(
                    name="contradiction_detector",
                    fail_policy="proceed",
                    enabled=True,
                ),
                # 4. التحقق من كفاية الأد��ة
                VerificationCheck(
                    name="evidence_sufficiency",
                    fail_policy="abstain",
                    enabled=True,
                ),
            ]
        ),
        
        "hadith": VerificationSuite(
            checks=[
                VerificationCheck(name="exact_quote", fail_policy="abstain"),
                VerificationCheck(name="hadith_grade", fail_policy="abstain"),
                VerificationCheck(name="sanad_verification", fail_policy="warn"),
            ]
        ),
    }
    
    return suites.get(agent_name, VerificationSuite(checks=[]))
```

### 7.3 فحوصات التحقق

#### 7.3.1 التحقق من الاقتباس الدقيق

```python
# في src/verifiers/exact_quote.py
async def check_exact_quote(
    answer: str,
    passages: list[RetrievalResult],
) -> CheckResult:
    """التحقق من أن الاقتباسات دقيقة."""
    
    # استخراج الاقتباسات من الإجابة
    quotes = extract_quotes(answer)
    
    for quote in quotes:
        # البحث في المصادر
        match = find_in_passages(quote, passages)
        
        if not match:
            return CheckResult(
                status="failed",
                message=f"اقتباس غير موجود: {quote[:50]}..."
            )
        
        # التحقق من التطابق Exact
        if not is_exact_match(quote, match.text):
            return CheckResult(
                status="warning",
                message="الاقتباس غير حرفي"
            )
    
    return CheckResult(status="passed")
```

#### 7.3.2 التحقق من المصدر

```python
# في src/verifiers/source_attribution.py
async def check_source_attribution(
    answer: str,
    passages: list[RetrievalResult],
) -> CheckResult:
    """التحقق من صحة المصادر."""
    
    # استخراج أسماء المصادر
    mentioned_sources = extract_sources(answer)
    
    for source in mentioned_sources:
        # البحث في المصادر
        valid = any(
            source.lower() in p.metadata.get("book_title", "").lower()
            for p in passages
        )
        
        if not valid:
            return CheckResult(
                status="warning",
                message=f"مصدر غير موجود: {source}"
            )
    
    return CheckResult(status="passed")
```

#### 7.3.3 التحقق من درجة الحديث

```python
# في src/verifiers/hadith_grade.py
async def check_hadith_grade(
    answer: str,
    passages: list[RetrievalResult],
) -> CheckResult:
    """التحقق من صحة الأحاديث."""
    
    # استخراج الأحاديث
    ahadith = extract_ahadith(answer)
    
    for hadith_text in ahadith:
        # البحث عن الدرجة
        grade = get_grade_from_passages(hadith_text, passages)
        
        if grade == "mawdu":
            return CheckResult(
                status="failed",
                message="يشير إلى حديث موضوع (مكذوب)"
            )
        
        if grade == "daif":
            return CheckResult(
                status="warning",
                message="يشير إلى حديث ضعيف"
            )
    
    return CheckResult(status="passed")
```

### 7.4 سياسات الفشل

| السياسة | الإجراء |
|---------|----------|
| `abstain` | التوقف وإرجاع "لا أعرف" |
| `warn` | إكمال مع تحذير |
| `proceed` | إكمال بدون توقف |

### 7.5 تقرير التحقق

```python
class VerificationReport(BaseModel):
    """تقرير التحقق."""
    status: str                # "passed" | "failed" | "abstained"
    confidence: float          # 0.0 - 1.0
    verified_passages: list[str] # المقاطع المحققة
    abstained: bool          # هل توقف؟
    abstention_reason: str | None  # سبب التوقف
    
    checks_passed: int       # عدد الفحوصات الناجحة
    checks_failed: int        # عدد الفحوصات الفاشلة
    warnings: list[str]      # التحذيرات
```

### 7.6 مثال على تحقق

**الإدخال**: الإجابة + 2 مقطع

**المخرجات**:

```python
{
    "status": "passed",
    "confidence": 0.95,
    "verified_passages": [
        "fiqh_passage_001",
        "fiqh_passage_002"
    ],
    "abstained": False,
    "checks_passed": 3,
    "checks_failed": 0,
    "warnings": []
}
```

---

## 8. السابعة: الخطوة توليد الإجابة

### 8.1 نظرة عامة

الخطوة السابعة هي توليد إجابة باستخدام نموذج اللغة الكبير (LLM).

### 8.2 عميل LLM

```python
# في src/generation/llm_client.py
class LLMClient:
    """عميل LLM."""
    
    def __init__(self, api_key: str, provider: str = "openai"):
        self._api_key = api_key
        self._provider = provider
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
    ) -> str:
        """توليد إجابة."""
        
        # بناء الرسالة
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
        
        # استدعاء API
        if self._provider == "openai":
            response = await openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000,
            )
        
        elif self._provider == "groq":
            response = await groq.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
        
        return response.choices[0].message.content
```

### 8.3 تحميل المطالبات

```python
# في src/generation/prompt_loader.py
def load_prompt(template_name: str) -> str:
    """تحميل نموذج المذكرة."""
    path = f"prompts/{template_name}.txt"
    
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def list_prompts() -> list[str]:
    """قائمة النماذج المتاحة."""
    return os.listdir("prompts/")
```

### 8.4 بناء السؤال

```python
# في src/agents/collection/base.py
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
        f"[المصدر {i+1}]: {ctx}"
        for i, ctx in enumerate(contexts)
    ])
    
    # استبدال العناصر
    prompt = template.replace("{{query}}", query)
    prompt = prompt.replace("{{context}}", context_text)
    prompt = prompt.replace("{{language}}", self.config.language)
    
    return prompt
```

### 8.5 نموذج المذكرة

```
# سؤال المستخدم
{{query}}

# المصادر
{{context}}

# التعليمات
- أجب باللغة {{language}}
- استخدم المصادر المذكورة فقط
- اذكر رقم المصدر لكل معلومة
- إذا لم تجد إجابة، قل "لا أعرف"
```

### 8.6 سؤال النظام

```python
def _get_system_prompt(self) -> str:
    """_BUILD سؤال النظام."""
    
    prompts = {
        "fiqh": """أنت عالم إسلامي متخصص في الفقه الإسلامي.
            - أجب باللغة العربية فصيحى
            - استخدم المذاهب الأربعة
            - اذكر المصادر بوضوح
            - تجنب الآراء الشاذة""",
        
        "hadith": """أنت عالم حديث متخصص.
            -اذكر درجة الحديث (صحيح، حسن، ضعيف)
            -اذكر اسم الراوي
            -تجنب الأحاديث الضعيفة بدون سياق""",
        
        "tafsir": """أنت مفسر قرآن متخصص.
            - أفسروا الآية بوضوح
            - اذكروا أسباب النزول
            - استخدموا التفاسير المعتمدة""",
    }
    
    return prompts.get(self.config.name, "")
```

### 8.7 توليد الإجابة

```python
# في CollectionAgent.execute()
async def generate(
    self,
    query: str,
    passages: list[RetrievalResult],
) -> str:
    """توليد الإجابة."""
    
    # 1. استخراج النصوص
    contexts = [p.text for p in passages]
    
    # 2. بناء السؤال
    prompt = self._build_prompt(query, contexts)
    
    # 3. الحصول على سؤال النظام
    system_prompt = self._get_system_prompt()
    
    # 4. توليد
    raw_answer = await self._llm_client.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        model=self.config.llm_model,
        temperature=self.config.temperature,
    )
    
    return raw_answer
```

### 8.8 مثال على توليد

**الإدخال**:
- السؤال: "ما حكم صلاة الجماعة؟"
- السياق: مقطع من الموسوعة الفقهية

**المخرجات**:
```
صلاة الجماعة واجبة على كل ذكر بالغ قادر بإجماع المذاهب الأربعة.

قال الشيخ ابن عثيمين في "الشرح الممتع": "صلاة الجماعة فرض عين على الرجل القادر عليها، وهي أفضل من صلى منفرداً بسبع وعشرين درجة".

المصادر:
- صحيح البخاري، كتاب الجماعة
- الموسوعة الفقهية، ج 3، ص 150
```

---

## 9. الخطوة الثامنة: معالجة الإجابة

### 9.1 نظرة عامة

الخطوة الثامنة هي تنظيف الإجابة من تسرب التفكير الداخلي.

### 9.2 إزالة تسرب Thought Chain

```python
# في src/agents/base.py
_COT_PATTERNS = [
    # Markdown Headers
    re.compile(
        r"##?\s*(Analysis|Reasoning|Thought).*?\n\n",
        re.IGNORECASE | re.DOTALL
    ),
    # XML Tags
    re.compile(
        r"<\s*(analysis|reasoning|thought)\s*>.*?<\s*/\s*>",
        re.IGNORECASE | re.DOTALL
    ),
    # Let me / I'll
    re.compile(
        r"###\s*(?:Let me|I'll|I will).*?\n\s*",
        re.IGNORECASE
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

### 9.3 ما يتم إزالته

| النوع | قبل | بعد |
|-------|------|------|
| Markdown | ## Analysis<br>النتيجة | (محذوف) |
| XML | \<analysis\>...\<\/analysis\> | (محذوف) |
| Let me | ### Let me think | (محذوف) |

### 9.4 مثال على المعالجة

**قبل**:

```
## Analysis
سأبحث في المصادر...

صلاة الجماعة واجبة على كل ذكر قادر...

### Let me verify
نعم، هذا صحيح بناءً على صحيح البخاري...
```

**بعد**:

```
صلاة الجماعة واجبة على كل ذكر قادر...
```

---

## 10. التاسعة: الخطوة بناء الاقتباسات

### 10.1 نظرة عامة

الخطوة العاشرة هي بناء قائمة الاقتباسات للإجابة.

### 10.2 نموذج الاقتباس

```python
class Citation(BaseModel):
    """اقتباس."""
    source_id: str           # معرف المصدر
    text: str             # النص المقتبس
    book_title: str | None  # عنوان الكتاب
    page: int | None      # الصفحة
    grade: str | None    # الدرجة (للأحاديث)
    url: str | None     # الرابط
    metadata: dict      # البيانات الوصفية
```

### 10.3 بناء الاقتباسات

```python
def _build_citations(
    self,
    passages: list[RetrievalResult],
) -> list[Citation]:
    """بناء الاقتباسات."""
    
    citations = []
    
    for passage in passages[:self.config.max_citations]:
        citation = Citation(
            source_id=passage.id,
            text=passage.text[:200],  # أول 200 حرف
            book_title=passage.metadata.get("book_title"),
            page=passage.metadata.get("page"),
            grade=passage.metadata.get("grade"),
            url=passage.metadata.get("url"),
            metadata=passage.metadata,
        )
        citations.append(citation)
    
    return citations
```

### 10.4 نموذج الاستجابة

```python
class CitationResponse(BaseModel):
    """نموذج الاقتباس في الاستجابة."""
    source_id: str
    text: str
    book_title: str | None
    page: int | None
    grade: str | None
    url: str | None
```

---

## 11. العاشرة: الخطوة إرسال الاستجابة

### 11.1 نظرة عامة

الخطوة الأخيرة هي إرسال الاستجابة للمستخدم.

### 11.2 نموذج الاستجابة

```python
class AskResponse(BaseModel):
    """نموذج الاستجابة."""
    answer: str                       # الإجابة
    citations: list[CitationResponse]  # الاقتباسات
    intent: str                     # النية
    confidence: float               # الثقة
    processing_time_ms: int         # زمن المعالجة
```

### 11.3 حساب الزمن

```python
async def ask_question(request: AskRequest) -> AskResponse:
    """معالجة السؤال."""
    
    start_time = time.time()
    
    # ... معالجة ...
    
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    return AskResponse(
        answer=result.answer,
        citations=citations,
        intent=result.metadata.get("intent"),
        confidence=result.confidence,
        processing_time_ms=elapsed_ms,
    )
```

### 11.4 مثال على استجابة

```json
{
    "answer": "صلاة الجماعة واجبة على كل ذكر بالغ قادر بإجماع المذاهب الأربعة. قال الشيخ ابن عثيمين: 'صلاة الجماعة فرض عين على الرجل القادر'.",
    "citations": [
        {
            "source_id": "fiqh_passage_001",
            "text": "صلاة الجماعة فرض عين على كل ذكر بالغ قادر...",
            "book_title": "الموسوعة ��لفقهية",
            "page": 150
        },
        {
            "source_id": "hadith_passage_001",
            "text": "من صلى جماعة فكأنما صلى في五金...",
            "book_title": "صحيح البخاري",
            "page": 580,
            "grade": "sahih"
        }
    ],
    "intent": "FIQH_HUKM",
    "confidence": 0.95,
    "processing_time_ms": 1250
}
```

---

## 12. ملخص التدفق الكامل

### 12.1 نظرة عامة

```
المستخدم → API → التحقق → تصنيف → توجيه → استرجاع → تحقق → توليد → معالجة → اقتباسات → استجابة
```

### 12.2 الزمن الكلي (تقديري)

| الخطوة | الزمن |
|---------|--------|
| استلام الطلب | <1 مللي ثانية |
| التحقق من الصحة | <1 مللي ثانية |
| تصنيف النية | <50 مللي ثانية |
| التوجيه | <5 مللي ثانية |
| استرجاع الوثائق | 100-500 مللي ثانية |
| التحقق | 50-200 مللي ثانية |
| توليد الإجابة | 500-2000 مللي ثانية |
| معالجة الإجابة | <5 مللي ثانية |
| بناء الاقتباسات | <10 مللي ثانية |
| **الإجمالي** | **700-3000 مللي ثانية** |

### 12.3 المخططات

```
┌─────────────────────────────────────────────┐
│         POST /api/v1/ask                    │
│         {query, language, madhhab}          │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Pydantic Validation                 │
│         التحقق من صحة البيانات              │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Hybrid Intent Classifier           │
│         (keyword + embedding)               │
│         ←FiQH, Hadith, Tafsir, etc.         │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Router                              │
│         توجيه إلى الوكيل المناسب           │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Hybrid Search (RRF)                │
│         (semantic + BM25)                   │
│         ←Qdrant + Okapi BM25                │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Verification Suite                 │
│         (quote, source, contradiction)      │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         LLM Generation                     │
│         (GPT-4 or Groq)                    │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Post-processing                    │
│         (strip CoT leakage)               │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Citation Building                  │
│         (sources + metadata)              │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         AskResponse                        │
│         (answer, citations, metrics)       │
└─────────────────────────────────────────────┘
```

---

## المراجع

- [01_project_overview.md](01_project_overview.md) - نظرة عامة
- [02_folder_structure.md](02_folder_structure.md) - بنية المجلدات
- [18_src_modules_complete_guide.md](18_src_modules_complete_guide.md) - دليل الوحدات
- [22_complete_src_reference.md](22_complete_src_reference.md) - مرجع كامل
- [23_detailed_execution_steps.md](23_detailed_execution_steps.md) - خطوات التنفيذ

---

**آخر تحديث**: أبريل 2026

**الإصدار**: 1.0

**الكاتب**: فريق توثيق Burhan