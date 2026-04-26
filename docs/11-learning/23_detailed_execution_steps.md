# دليل التنفيذ التفصيلي الشامل

## شرح كل خطوة في نظام Burhan من البداية للنهاية

هذا الدليل يشرح بالتفصيل كل خطوة في نظام Burhan الإسلامية، بدءاً من استلام سؤال المستخدم وحتى إرسال الإجابة النهائية.，我将使用阿拉伯语撰写，确保使用正确的阿拉伯标点符号和完整的术语。
  
---

## جدول المحتويات

1. [/مقدمة](#1-مقدمة)
2. [/الخطوة الأولى: استلام الطلب](#2-الخطوة الأولى-استلام-الطلب)
3. [/الخطوة الثانية: التحقق من الصحة](#3-الخطوة الثانية-التحقق من الصحة)
4. [/الخطوة الثالثة: تصنيف النية](#4-الخطوة الثالثة-تصنيف-النية)
5. [/الخطوة الرابعة: التوجيه](#5-الخطوة الرابعة-التوجيه)
6. [/الخطوة الخامسة: استرجاع الوثائق](#6-الخطوة الخامسة-استرجاع-الوثائق)
7. [/الخطوة السادسة: التحقق](#7-الخطوة السادسة-التحقق)
8. [/الخطوة السابعة: توليد الإجابة](#8-الخطوة السابعة-توليد-الإجابة)
9. [/الخطوة الثامنة: معالجة الإجابة](#9-الخطوة الثامنة-معالجة-الإجابة)
10. [/الخطوة التاسعة: بناء الاقتباسات](#10-الخطوة التاسعة-بناء-الاقتباسات)
11. [/الخطوة العاشرة: إرسال الاستجابة](#11-الخطوة العاشرة-إرسال-الاستجابة)
12. [/خلاصة التدفق](#12-خلاصة-التدفق)

---

## 1. مقدمة

نظام Burhan هو نظام سؤال وجواب إسلامي يستخدم تقنيات الذكاء الاصطناعي المتقدمة. يتكون النظام من خطوات متعددة تعمل معاً لتقديم إجابة دقيقة وموثقة للمستخدم.

### نظرة عامة على التدفق

```
المستخدم → API → classify → route → retrieve → verify → generate → respond
```

### المكونات الرئيسية

يتكون النظام من المكونات التالية:

| المكون | الوظيفة |
|--------|---------|
| `src/api/` | نقطة دخول HTTP |
| `src/application/` | منطق الأعمال |
| `src/agents/` | وكلاء الذكاء الاصطناعي |
| `src/retrieval/` | استرجاع الوثائق |
| `src/verifiers/` | التحقق من الدقة |
| `src/generation/` | توليد الإجابات |

---

## 2. الخطوة الأولى: استلام الطلب

### 2.1 الوصف

الخطوة الأولى هي استلام طلب المستخدم من خلال واجهة برمجة التطبيقات (API). يتم إرسال طلب إلى نقطة النهاية `/api/v1/ask`または `/ask`.

### 2.2 الكود

الطلب يصل إلى الدالة التالية في `src/api/routes/ask.py`:

```python
@ask_router.post("", response_model=AskResponse)
async def ask_question(request: AskRequest) -> AskResponse:
```

### 2.3 نموذج الطلب

طلب المستخدم يحتوي على الحقول التالية:

```python
class AskRequest(BaseModel):
    query: str = Field(..., description="سؤال المستخدم")
    language: str = Field(default="ar", description="لغة السؤال")
    collection: str | None = Field(default=None, description="المجموعة المستهدفة")
    madhhab: str | None = Field(default=None, description="المذهب المفضل")
```

### 2.4 مثال على طلب

```json
{
    "query": "ما حكم صلاة الجماعة؟",
    "language": "ar",
    "madhhab": "hanafi"
}
```

### 2.5 ما يحدث داخلياً

عند استلام الطلب:

1. **تحديد الوقت**: يتم تسجيل وقت بدء المعالجة
2. **التحقق من الصحة**: يتم التحقق من البيانات باستخدام Pydantic
3. **إعداد السياق**: يتم إعداد سياق الطلب للخطوات التالية

### 2.6 معالجة الأخطاء

إذا كان الطلب غير صالح:

```python
# مثال على خطأ في التحقق
try:
    request = AskRequest(query="ما حكم الصلاة؟")
except ValidationError as e:
    return {"error": str(e)}
```

---

## 3. الخطوة الثانية: التحقق من الصحة

### 3.1 الوصف

الخطوة الثانية هي التحقق من صحة البيانات المستلمة. يتم ذلك تلقائياً بواسطة Pydantic.

### 3.2 التحقق من صحة النماذج

في `src/api/schemas/ask.py`:

```python
class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    language: str = Field(default="ar", pattern="^(ar|en)$")
    collection: str | None = None
    madhhab: str | None = Field(default=None, pattern="^(hanafi|maliki|shafii|hanbali)$")
    
    model_config = {"extra": "forbid"}
```

### 3.3 قواعد التحقق

| الحقل | القاعدة |
|------|--------|
| `query` | مطلوب، 1-1000 حرف |
| `language` | افتراضي "ar"،要么 "ar" أو "en" |
| `madhhab` | اختياري، salah واحد من أربعة مذاهب |

### 3.4 معالجة الأخطاء

إذا فشل التحقق:

```python
# خطأ في التحقق من الصحة
{
    "detail": [
        {
            "loc": ["query"],
            "msg": "String should have at least 1 character",
            "type": "string_too_short"
        }
    ]
}
```

### 3.5 ما بعد التحقق الناجح

 после успешной проверки:

1. ** إنشاء كائن الطلب**: `AskRequest` объекта создается
2. **تمرير إلى الخدمة**: يتم إرسال الطلب إلى `AskService`

---

## 4. الخطوة الثالثة: تصنيف النية

### 4.1 الوصف

الخطوة الثالثة هي تحديد نوع سؤال المستخدم (نية). هل هو سؤال فقه، حديث، تفسير، تاريخ، إلخ.

### 4.2 التصنيف الهجين

يستخدم النظام تصنيفياً هجيناً يجمع بين طريقتين:

```python
# في src/application/hybrid_classifier.py
class MasterHybridClassifier:
    async def classify(self, query: str) -> ClassificationResult:
        # الخطوة 1: المطابقة بالكلمات المفتاحية
        kw_result = await self._keyword_classifier.classify(query)
        
        if kw_result.confidence >= 0.85:
            return kw_result
        
        # الخطوة 2: البحث بالم embeddings
        emb_result = await self._embedding_classifier.classify(query)
        
        # الخطوة 3: اختيار الأعلى ثقة
        return max(kw_result, emb_result, key=lambda x: x.confidence)
```

### 4.3 مستويات الأولوية

يوجد 10 مستويات من الأولوية:

| المستوى | النية | الأولوية |
|---------|------|----------|
| 1 | ZAKAT | highest |
| 2 | INHERITANCE | high |
| 3 | FIQH_HUKM | high |
| 4 | FIQH_MASAIL | medium-high |
| 5 | HADITH_TAKHRIJ | medium |
| 6 | QURAN_VERSE | medium |
| 7 | TAFSIR | medium |
| 8 | AQEEDAH | medium-low |
| 9 | SEERAH | low |
| 10 | GENERAL_ISLAMIC | lowest |

### 4.4 الكلمات المفتاحية

كل نية لها كلمات مفتاحية محددة:

```python
# في src/domain/intents.py
KEYWORD_PATTERNS = {
    "FIQH_HUKM": [
        r"حكم",
        r"هل يجوز",
        r"هل يحرم",
        r"مكروه",
        r"واجب",
    ],
    "ZAKAT": [
        r"زكاة",
        r"نصاب",
        r" Nisab",
    ],
    # ...
}
```

### 4.5 النيات الفرعية للقرآن

للقرآن 4 نيات فرعية:

```python
QuranSubIntent = Enum(
    "QuranSubIntent",
    {
        "VERSE_LOOKUP": "استعلام عن آية",
        "ANALYTICS": "إحصاءات قرآنية",
        "INTERPRETATION": "تفسير آية",
        "QUOTATION_VALIDATION": "تحقق من اقتباس",
    }
)
```

### 4.6 مخرجات التصنيف

```python
class ClassificationResult:
    intent: IntentType
    confidence: float  # 0.0 - 1.0
    language: str  # "ar" أو "en"
    requires_retrieval: bool
    sub_intent: QuranSubIntent | None = None
```

### 4.7 مثال على تصنيف

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

## 5. الرابعة: التوجيه

### 5.1 الوصف

الخطوة الرابعة هي توجيه السؤال إلى الوكيل المناسب بناءً على تصنيف النية.

### 5.2 سجل الوكلاء

 يتم استخدام `AgentRegistry` para gestionar los agentes:

```python
# في src/core/registry.py
class AgentRegistry:
    def register(self, name: str, agent: CollectionAgent) -> None:
        self._agents[name] = agent
    
    def get(self, name: str) -> CollectionAgent:
        return self._agents[name]
    
    def list_all(self) -> list[str]:
        return list(self._agents.keys())
```

### 5.3 تسجيل الوكلاء

 في `src/api/lifespan.py`:

```python
# تسجيل الوكلاء عند بدء التطبيق
registry.register("fiqh:rag", FiQHCollectionAgent(config_fiqh))
registry.register("hadith:rag", HadithCollectionAgent(config_hadith))
registry.register("tafsir:rag", TafsirCollectionAgent(config_tafsir))
# ... المزيد من الوكلاء
```

### 5.4 خريطة التوجيه

| النية | الوكيل | المجموعة |
|------|-------|----------|
| FIQH_HUKM | fiqh:rag | fiqh_passages |
| FIQH_MASAIL | fiqh:rag | fiqh_passages |
| HADITH_TAKHRIJ | hadith:rag | hadith_passages |
| QURAN_VERSE | tafsir:rag | quran_passages |
| TAFSIR | tafsir:rag | tafsir_passages |
| AQEEDAH | aqeedah:rag | aqeedah_passages |
| SEERAH | seerah:rag | seerah_passages |
| HISTORY | history:rag | history_passages |
| ISLAMIC_KNOWLEDGE | general:rag | general_passages |

### 5.5 ما بعد التوجيه

 بعد التوجيه الناجح:

1. **الحصول على الوكيل**: `registry.get(route)`
2. **إعداد الإدخال**: `AgentInput(query, language, metadata)`
3. **تنفيذ الوكيل**: `agent.execute(input)`

---

## 6. الخطوة الخامسة: استرجاع الوثائق

### 6.1 الوصف

الخطوة الخامسة هي استرجاع الوثائق ذات الصلة من قاعدة بيانات المتجهات (Qdrant).

### 6.2 البحث الهجين

يستخدم النظام بحثاً هجيناً يجمع بين البحث الدلالي وBM25:

```python
# في src/retrieval/retrievers/hybrid_retriever.py
class HybridSearcher:
    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        # البحث الدلالي (بالمتجهات)
        semantic_results = await self._semantic.search(query, collection, top_k)
        
        # البحث بكلمات المفتاح (BM25)
        keyword_results = await self._bm25.search(query, collection, top_k)
        
        # دمج النتائج بـ Reciprocal Rank Fusion
        fused = self._rrf.fuse(semantic_results, keyword_results, k=60)
        
        return fused[:top_k]
```

### 6.3 استراتيجية الاسترجاع

كل وكيل له استراتيجية خاصة:

```python
# في src/retrieval/strategies.py
RETRIEVAL_MATRIX = {
    "fiqh_agent": RetrievalStrategy(
        collection="fiqh_passages",
        top_k=15,
        filters={"type": "fiqh"},
        rerank=True,
    ),
    "hadith_agent": RetrievalStrategy(
        collection="hadith_passages",
        top_k=10,
        filters={"grade": "sahih"},
        rerank=True,
    ),
}
```

### 6.4 البحث الدلالي

البحث الدلالي يستخدم التضمينات (embeddings):

```python
async def semantic_search(query: str, collection: str, top_k: int):
    # 1. تحويل الاستعلام إلى متجه
    query_embedding = await embedding_model.encode([query])
    
    # 2. البحث في Qdrant
    results = await qdrant.search(
        collection=collection,
        query_vector=query_embedding[0].tolist(),
        limit=top_k,
    )
    
    return results
```

### 6.5 البحث بـ BM25

البحث بـ BM25 يستخدم خوارزمية OKapi BM25:

```python
async def bm25_search(query: str, collection: str, top_k: int):
    # 1. بناء فهرس BM25
    # 2. حسابScores للكلمات
    # 3. ترتيب النتائج
    results = bm25_index.rank(query, top_k)
    
    return results
```

### 6.6 دمج النتائج (Reciprocal Rank Fusion)

RRF يدمج نتائج متعددة:

```python
def rrf_fuse(results_list: list[list], k: int = 60) -> list:
    scores = {}
    
    for results in results_list:
        for rank, result in enumerate(results):
            doc_id = result.id
            # صيغة RRF
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
    
    # ترتيب بالنتيجة
    sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    return [get_result(doc_id) for doc_id, _ in sorted_results]
```

### 6.7 نموذج النتيجة

```python
class RetrievalResult(BaseModel):
    id: str  # معرف الوثيقة
    text: str  # نص الوثيقة
    score: float  # الدرجة
    collection: str  # المجموعة
    metadata: dict  # البيانات الوصفية
    book_title: str | None  # عنوان الكتاب
    page: int | None  # الصفحة
    grade: str | None  # درجة الحديث
```

### 6.8 مثال على استرجاع

**الإدخال**: "ما حكم صلاة الجماعة؟"

**المخرجات**:

```python
[
    {
        "id": "fiqh_001",
        "text": "صلاة الجماعة فرض عين على الرجل القادر...",
        "score": 0.92,
        "collection": "fiqh_passages",
        "metadata": {"book": "الموسوعة الفقهية", "page": 150}
    },
    {
        "id": "fiqh_002",
        "text": "ويستحب لها التكبير...",
        "score": 0.85,
        ...
    }
]
```

---

## 7. الخطوة السادسة: التحقق

### 7.1 الوصف

الخطوة السادسة هي التحقق من أن الإجابة ستستند إلى أدلة موثوقة. يتم ذلك بواسطة طبقة التحقق.

### 7.2 بناء مجموعة التحقق

لكل وكيل مجموعة تحقق خاصة:

```python
# في src/verifiers/suite_builder.py
def build_verification_suite_for(agent_name: str) -> VerificationSuite:
    suites = {
        "fiqh": VerificationSuite(checks=[
            VerificationCheck(name="quote_validator", fail_policy="abstain"),
            VerificationCheck(name="source_attributor", fail_policy="warn"),
            VerificationCheck(name="contradiction_detector", fail_policy="proceed"),
            VerificationCheck(name="evidence_sufficiency", fail_policy="abstain"),
        ]),
        "hadith": VerificationSuite(checks=[
            VerificationCheck(name="quote_validator", fail_policy="abstain"),
            VerificationCheck(name="hadith_grade_checker", fail_policy="abstain"),
        ]),
    }
    
    return suites.get(agent_name, VerificationSuite(checks=[]))
```

### 7.3 فحوصات التحقق

#### 7.3.1 التحقق من الاقتباس الدقيق

```python
# في src/verifiers/exact_quote.py
async def check_exact_quote(answer: str, passages: list) -> CheckResult:
    # استخراج الاقتباسات من الإجابة
    quotes = extract_quotes(answer)
    
    for quote in quotes:
        # البحث في المصادر
        match = find_exact_match(quote, passages)
        
        if not match:
            return CheckResult(
                status="failed",
                message=f"اقتباس غير موجود: {quote[:50]}..."
            )
    
    return CheckResult(status="passed")
```

#### 7.3.2 التحقق من المصدر

```python
# في src/verifiers/source_attribution.py
async def check_source_attribution(answer: str, passages: list) -> CheckResult:
    # استخراج أسماء المصادر
    sources = extract_sources(answer)
    
    for source in sources:
        if not validate_source(source, passages):
            return CheckResult(
                status="warning",
                message=f"مصدر غير موثق: {source}"
            )
    
    return CheckResult(status="passed")
```

#### 7.3.3 التحقق من درجة الحديث

```python
# في src/verifiers/hadith_grade.py
async def check_hadith_grade(answer: str, passages: list) -> CheckResult:
    # استخراج الأحاديث المذكورة
    ahadith = extract_ahadith(answer)
    
    for hadith in ahadith:
        # التحقق من الدرجة في المصادر
        grade = get_grade(hadith)
        
        if grade == "daif":
            return CheckResult(
                status="warning",
                message="يشير إلى حديث ضعيف"
            )
    
    return CheckResult(status="passed")
```

#### 7.3.4 التحقق من التناقض

```python
# في src/verifiers/contradiction.py
async def check_contradiction(answer: str, passages: list) -> CheckResult:
    # تحليل المحتوى
    claims = extract_claims(answer)
    
    # التحقق من التناقضات
    for i, claim1 in enumerate(claims):
        for claim2 in claims[i+1:]:
            if is_contradiction(claim1, claim2):
                return CheckResult(
                    status="warning",
                    message="تم اكتشاف تناقض محتمل"
                )
    
    return CheckResult(status="passed")
```

### 7.4 سياسات الفشل

كل فحص له سياسة فشل:

```python
class VerificationCheck(BaseModel):
    name: str  # اسم الفحص
    fail_policy: str  # "abstain" | "warn" | "proceed"
    enabled: bool = True
```

| السياسة | الإجراء |
|---------|----------|
| `abstain` | التوقف وإرجاع "لا أعرف" |
| `warn` | إكمال مع تحذير |
| `proceed` | إكمال بدون توقف |

### 7.5 تقرير التحقق

```python
class VerificationReport(BaseModel):
    status: str  # "passed" | "failed" | "abstained"
    confidence: float  # 0.0 - 1.0
    verified_passages: list[str]  # المقاطع المحققة
    abstained: bool  # هل توقف
    abstention_reason: str | None  # سبب التوقف
```

### 7.6 مثال على تحقق

**الإدخال**:

- الإجابة: "صلاة الجماعة واجبة على كل ذكر..."
- المقاطع: [مقطع من الموسوعة الفقهية]

**المخرجات**:

```python
{
    "status": "passed",
    "confidence": 0.95,
    "verified_passages": ["صلاة الجماعة فرض عين..."],
    "abstained": False
}
```

---

## 8. الخطوة السابعة: توليد الإجابة

### 8.1 الوصف

الخطوة السابعة هي توليد الإجابة باستخدام نموذج اللغة الكبير (LLM).

### 8.2 العميل

```python
# في src/generation/llm_client.py
class LLMClient:
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
    ) -> str:
        # بناء رسالة المحادثة
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        # استدعاء LLM
        response = await openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=2000,
        )
        
        return response.choices[0].message.content
```

### 8.3 تحميل المطالبات

 يتم تحمي�� المطالبات من ملفات نصية:

```python
# في src/generation/prompt_loader.py
def load_prompt(template_name: str) -> str:
    path = f"prompts/{template_name}.txt"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
```

### 8.4 بناء المذكرة

 يتم بناء المذكرة بالسياق:

```python
# في src/agents/collection/base.py
def _build_prompt(self, query: str, contexts: list[str]) -> str:
    # تحميل النموذج
    template = self._load_prompt_template()
    
    # بناء السياق
    context_text = "\n\n".join([
        f"[{i+1}] {ctx}" for i, ctx in enumerate(contexts)
    ])
    
    # استبدال العناصر
    prompt = template.replace("{{query}}", query)
    prompt = prompt.replace("{{context}}", context_text)
    
    return prompt
```

### 8.5 مثال على مذكرة

```
سؤال: ما حكم صلاة الجماعة؟

المصادر:
[1] صلاة الجماعة فرض عين على الرجل القادر، وهي أفضل من صلاة الفرد بسبع وعشرين درجة. (صحيح البخاري)
[2] ويؤمر الرجال بها دون النساء. (الموسوعة الفقهية)

أجب باللغة العربية مع ذكر المصادر.
```

### 8.6 النظام

 يتم إنشاء سؤال النظام أيضاً:

```python
def _get_system_prompt(self) -> str:
    return """أنت عالم إسلامي متخصص في الفقه الإسلامي.
        - أجب باللغة العربية
        - اذكر المصادر بوضوح
        - تجنب المعلومات غير المؤكدة"""
```

### 8.7 توليد الإجابة

```python
async def generate(self, query: str, passages: list) -> str:
    # بناء المذكرة
    prompt = self._build_prompt(query, passages)
    
    # الحصول على نظام السؤال
    system_prompt = self._get_system_prompt()
    
    # توليد الإجابة
    raw_answer = await self._llm_client.generate(
        prompt=prompt,
        system_prompt=system_prompt,
    )
    
    return raw_answer
```

### 8.8 مثال على إجابة

**الإدخال**: سؤال + مقاطع

**المخرجات**:

```
صلاة الجماعة واجبة على كل ذكر بالغ قادر بإجماع المذاهب الأربعة.
قال الشيخ ابن عثيمين: "صلاة الجماعة فرض عين على мужчина قادر".

المصادر:
- صحيح البخاري، كتاب الجماعة
- الموسوعة الفقهية، ج 3، ص 150
```

---

## 9. الخطوة الثامنة: معالجة الإجابة

### 9.1 الوصف

الخطوة الثامنة هي تنظيف الإجابة من تسرب التفكير الداخلي.

### 9.2 إزالة تسرب思维链

قد تحتوي الإجابة على علامات تفكير داخلي:

```python
# في src/agents/base.py
_COT_PATTERNS = [
    re.compile(r"##?\s*(Analysis|Reasoning|Thought).*?\n\n", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*(analysis|reasoning|thought)\s*>\s*", re.IGNORECASE),
    re.compile(r"###\s*(?:Let me|I'll|I will).*?\n\s*", re.IGNORECASE),
]

def strip_cot_leakage(text: str) -> str:
    if not text:
        return text
    
    result = text
    for pattern in _COT_PATTERNS:
        result = pattern.sub("", result)
    
    return result.strip()
```

### 9.3 ما يتم إزالته

| النمط | مثال | الإزالة |
|-------|------|----------|
| Markdown标题 | ## Analysis | إزالة بالكامل |
| XML标签 | `<analysis>...</analysis>` | إزالة بالكامل |
| Markdown标题 | ### Let me think | إزالة بالكامل |

### 9.4 مثال على معالجة

**قبل المعالجة**:

```
## Analysis
سأبحث في المصادر...

صلاة الجماعة واجبة...

### Let me verify
نعم، هذا صحيح...
```

**بعد المعالجة**:

```
صلاة الجماعة واجبة...
```

### 9.5 بعد المعالجة

بعد التنظيف:

1. **التحقق النهائي**: التأكد من سلامة الإجابة
2. **التالي**: بناء الاقتباسات

---

## 10. الخطوة التاسعة: بناء الاقتباسات

### 10.1 الوصف

الخطوة العاشرة هي بناء قائمة الاقتباسات للإجابة.

### 10.2 نموذج الاقتباس

```python
class Citation(BaseModel):
    source_id: str  # معرف المصدر
    text: str  # النص المقتبس
    book_title: str | None  # عنوان الكتاب
    page: int | None  # الصفحة
    grade: str | None  # درجة الحديث
    url: str | None  # الرابط
    metadata: dict  # البيانات الوصفية
```

### 10.3 بناء الاقتباسات

```python
def _build_citations(self, passages: list[RetrievalPassage]) -> list[Citation]:
    citations = []
    
    for passage in passages:
        citation = Citation(
            source_id=passage.id,
            text=passage.text[:200],  # أول 200 حرف
            book_title=passage.metadata.get("book_title"),
            page=passage.metadata.get("page"),
            grade=passage.metadata.get("grade"),
            metadata=passage.metadata,
        )
        citations.append(citation)
    
    return citations
```

### 10.4 نموذج الاستجابة

```python
class CitationResponse(BaseModel):
    source_id: str
    text: str
    book_title: str | None
    page: int | None
    grade: str | None
    url: str | None
```

### 10.5 مثال على اقتباسات

**المدخلات**: مقاطع مسترجعة

**المخرجات**:

```python
[
    {
        "source_id": "fiqh_001",
        "text": "صلاة الجماعة فرض عين على الرجل القادر...",
        "book_title": "الموسوعة الفقهية",
        "page": 150,
        "grade": null
    },
    {
        "source_id": "hadith_001",
        "text": "من صلى جماعة فكأنما صلى في五金...",
        "book_title": "صحيح البخاري",
        "page": 580,
        "grade": "sahih"
    }
]
```

---

## 11. الخطوة العاشرة: إرسال الاستجابة

### 11.1 الوصف

الخطوة الأخيرة هي إرسال الاستجابة للمستخدم.

### 11.2 نموذج الاستجابة

```python
class AskResponse(BaseModel):
    answer: str  # الإجابة
    citations: list[CitationResponse]  # الاقتباسات
    intent: str  # النية
    confidence: float  # الثقة
    processing_time_ms: int  # زمن المعالجة
```

### 11.3 حساب الزمن

```python
async def ask_question(request: AskRequest) -> AskResponse:
    start_time = time.time()
    
    # ... معالجة الطلب ...
    
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
            "source_id": "fiqh_001",
            "text": "صلاة الجماعة فرض عين على الرجل القادر...",
            "book_title": "الموسوعة الفقهية",
            "page": 150
        }
    ],
    "intent": "FIQH_HUKM",
    "confidence": 0.95,
    "processing_time_ms": 1250
}
```

### 11.5 حالة النجاح

```python
# HTTP 200 OK
{
    "answer": "...",
    "citations": [...],
    "intent": "FIQH_HUKM",
    "confidence": 0.95,
    "processing_time_ms": 1250
}
```

### 11.6 حالات الخطأ

| الكود | الوصف |
|-------|------|
| 400 | طلب غير صالح |
| 401 | غير مصرح |
| 422 | فشل التحقق |
| 500 | خطأ داخلي |
| 503 | الخدمة غير متوفرة |

---

## 12. خلاصة التدفق

### ملخص الخطوات

```
الخطوة 1: استلام الطلب (HTTP POST /ask)
    ↓
الخطوة 2: التحقق من الصحة (Pydantic)
    ↓
الخطوة 3: تصنيف النية (Hybrid Classifier)
    ↓
الخطوة 4: التوجيه (Router)
    ↓
الخطوة 5: استرجاع الوثائق (Hybrid Search)
    ↓
الخطوة 6: التحقق (Verification Suite)
    ↓
الخطوة 7: توليد الإجابة (LLM)
    ↓
الخطوة 8: معالجة الإجابة (CoT Removal)
    ↓
الخطوة 9: بناء الاقتباسات (Citations)
    ↓
الخطوة 10: إرسال الاستجابة (HTTP Response)
```

### أوقات المعالجة (تقديرية)

| الخطوة | الزمن |
|---------|--------|
| استلام الطلب | <1 مللي ثانية |
| التحقق من الصحة | <1 مللي ثانية |
| تصنيف النية | <50 ��لل�� ثانية |
| التوجيه | <5 مللي ثانية |
| استرجاع الوثائق | 100-500 مللي ثانية |
| التحقق | 50-200 مللي ثانية |
| توليد الإجابة | 500-2000 مللي ثانية |
| معالجة الإجابة | <5 مللي ثانية |
| بناء الاقتباسات | <10 مللي ثانية |
| **الإجمالي** | **700-3000 مللي ثانية** |

### المسار学习中

للتعلم بشكل أعمق:

1. [/src/api/main.py](src/api/main.py) - نقطة الدخول
2. [/src/api/routes/ask.py](src/api/routes/ask.py) - نقطة النهاية
3. [/src/application/hybrid_classifier.py](src/application/hybrid_classifier.py) - التصنيف
4. [/src/agents/collection/base.py](src/agents/collection/base.py) - الوكيل الأساسي
5. [/src/retrieval/retrievers/hybrid_retriever.py](src/retrieval/retrievers/hybrid_retriever.py) - الاسترجاع
6. [/src/verifiers/suite_builder.py](src/verifiers/suite_builder.py) - التحقق
7. [/src/generation/llm_client.py](src/generation/llm_client.py) - التوليد

---

## المراجع

- [01_project_overview.md](01_project_overview.md) - نظرة عامة
- [02_folder_structure.md](02_folder_structure.md) - بنية المجلدات
- [18_src_modules_complete_guide.md](18_src_modules_complete_guide.md) - دليل الوحدات
- [22_complete_src_reference.md](22_complete_src_reference.md) - مرجع كامل

---

**آخر تحديث**: أبريل 2026

**الإصدار**: 1.0

**الكاتب**: فريق توثيق Burhan