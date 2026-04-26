# 📂 الملف 3: `src/core/router.py` - مصنف النية الهجين (250 سطر)

## 1️⃣ وظيفة الملف

هذا الملف يحتوي على **HybridQueryClassifier** - العقل الذي **يفهم نية المستخدم** من السؤال. يستخدم 3 مستويات:
1. **Keyword matching** (سريع)
2. **LLM classification** (دقيق)
3. **Embedding similarity** (fallback)

---

## 2️⃣ نظرة عامة

| القسم | الأسطر | المحتوى |
|-------|--------|---------|
| Imports | 1-20 | مكتبات أساسية |
| RouterResult | 21-40 | نتيجة التصنيف |
| HybridQueryClassifier | 41-250 | المصنف الرئيسي |
| Tier 1: Keyword | 150-180 | مطابقة الكلمات |
| Tier 2: LLM | 181-230 | تصنيف بـ LLM |
| Tier 3: Embedding | 231-245 | fallback |
| Language detection | 246-250 | كشف اللغة |

---

## 3️⃣ شرح سطر بسطر

### الأسطر 1-20: Imports

```python
import json
from typing import Optional

from pydantic import BaseModel, Field

from src.config.intents import (
    Intent,
    INTENT_DESCRIPTIONS,
    KEYWORD_PATTERNS,
)
from src.config.settings import settings
from src.config.logging_config import get_logger

logger = get_logger()
```

**شرح**:
- `json`: لتحليل استجابة LLM
- `BaseModel, Field`: لنمذجة البيانات
- `Intent`: أنواع النية
- `INTENT_DESCRIPTIONS`: أوصاف النيات للـ prompt
- `KEYWORD_PATTERNS**: كلمات مفتاحية
- `settings**: إعدادات التطبيق
- `logger**: تسجيل الأحداث

---

### الأسطر 21-45: RouterResult

```python
class RouterResult(BaseModel):
    """Result from intent classification."""
    
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    method: str = Field(description="Classification method: keyword, llm, or embedding")
    language: str = Field(default="ar", description="Detected language: ar or en")
    requires_retrieval: bool = Field(
        default=True,
        description="Whether this query needs document retrieval (RAG)"
    )
    sub_intent: Optional[str] = Field(
        default=None,
        description="Sub-intent for Quran queries (verse_lookup, interpretation, etc.)"
    )
    reason: str = Field(default="", description="Reasoning for classification")
```

**شرح كل حقل**:

| الحقل | النوع | الوصف | مثال |
|-------|-------|-------|------|
| `intent` | Intent | النية المصنفة | Intent.FIQH |
| `confidence` | float | درجة الثقة | 0.92 |
| `method` | str | طريقة التصنيف | "keyword", "llm", "embedding" |
| `language` | str | اللغة المكتشفة | "ar", "en" |
| `requires_retrieval` | bool | هل يحتاج RAG؟ | True, False |
| `sub_intent` | Optional[str] | نية فرعية للقرآن | "verse_lookup" |
| `reason` | str | سبب التصنيف | "Keyword match: 'ما حكم'" |

**مثال نتيجة**:
```python
RouterResult(
    intent=Intent.FIQH,
    confidence=0.92,
    method="keyword",
    language="ar",
    requires_retrieval=True,
    sub_intent=None,
    reason="Keyword match: 'ما حكم'"
)
```

---

### الأسطر 46-70: فئة HybridQueryClassifier

```python
class HybridQueryClassifier:
    """
    Three-tier hybrid intent classifier.

    Tier 1: Keyword matching (fast path, confidence >= 0.90)
    Tier 2: LLM classification (primary path, confidence >= threshold)
    Tier 3: Embedding similarity (fallback when LLM confidence is low)
    """

    CONFIDENCE_THRESHOLD = 0.75
```

**شرح**:
- `CONFIDENCE_THRESHOLD = 0.75`: الحد الأدنى للثقة
- إذا كانت الثقة < 0.75، ينتقل للمستوى التالي

---

### الأسطر 71-140: LLM Classifier Prompt

```python
    LLM_CLASSIFIER_PROMPT = """You are an expert intent classifier for an Islamic QA system called Burhan.

Your task is to classify the user's query into exactly ONE intent from the list below.

Available Intents:
{intent_descriptions}

Rules:
- Return ONLY valid JSON with these exact fields:
  - intent: one of the valid intents above (lowercase, with underscores)
  - confidence: float between 0.0 and 1.0 (your confidence in this classification)
  - language: "ar" if the query is mostly Arabic script, "en" otherwise
  - requires_retrieval: true if answering requires retrieving documents (fatwas, hadith, etc.), false otherwise
  - sub_intent: null unless intent is "quran", then use one of:
    - "verse_lookup" (user wants a specific verse/surah text)
    - "interpretation" (user asks for meaning/tafsir)
    - "analytics" (user asks for statistics: count, length, etc.)
    - "quotation_validation" (user asks if some text is a Quran verse)
  - reason: brief explanation of why you chose this intent
  - sub_questions: array of sub-questions if the query is compound (can be empty [])

Examples:

Query: "ما حكم ترك صلاة الجمعة عمداً؟"
Output:
{{"intent":"fiqh","confidence":0.95,"language":"ar","requires_retrieval":true,"sub_intent":null,"reason":"Asking legal ruling about Friday prayer obligation","sub_questions":[]}}

Query: "كم عدد آيات سورة البقرة؟"
Output:
{{"intent":"quran","confidence":0.98,"language":"ar","requires_retrieval":false,"sub_intent":"analytics","reason":"Asking for count of verses in Surah Al-Baqarah","sub_questions":[]}}

Query: "How do I calculate zakat on my savings?"
Output:
{{"intent":"zakat","confidence":0.93,"language":"en","requires_retrieval":false,"sub_intent":null,"reason":"User wants to calculate zakat amount","sub_questions":[]}}

Query: "Is it permissible to trade cryptocurrency?"
Output:
{{"intent":"fiqh","confidence":0.88,"language":"en","requires_retrieval":true,"sub_intent":null,"reason":"Asking legal ruling on cryptocurrency trading","sub_questions":[]}}

Now classify this query. Return ONLY valid JSON, no explanations.

Query: {query}"""
```

**شرح**:
- **System prompt** للـ LLM
- يصف كل نية
- يعطي أمثلة
- يطلب JSON فقط

**لماذا مهم**:
- بدون هذا الـ prompt، LLM لا يعرف كيف يصنف
- الأمثلة تساعد LLM على فهم المطلوب

---

### الأسطر 141-200: دالة classify() الرئيسية

```python
    async def classify(self, query: str) -> RouterResult:
        """
        Classify user query using three-tier approach.
        """
        if not query or not query.strip():
            return RouterResult(
                intent=Intent.GREETING,
                confidence=0.5,
                method="fallback",
                reason="Empty query, defaulting to greeting"
            )

        # ==========================================
        # Tier 1: Keyword matching (fast path)
        # ==========================================
        keyword_result = self._keyword_match(query)
        if keyword_result and keyword_result.confidence >= 0.90:
            logger.info(
                "router.keyword_match",
                intent=keyword_result.intent.value,
                confidence=keyword_result.confidence,
                method="keyword"
            )
            return keyword_result

        # ==========================================
        # Tier 2: LLM classification (primary)
        # ==========================================
        if self.llm_client:
            try:
                llm_result = await self._llm_classify(query)
                if llm_result.confidence >= self.CONFIDENCE_THRESHOLD:
                    logger.info(
                        "router.llm_classify",
                        intent=llm_result.intent.value,
                        confidence=llm_result.confidence,
                        method="llm"
                    )
                    return llm_result
            except Exception as e:
                logger.error("router.llm_error", error=str(e))

        # ==========================================
        # Tier 3: Embedding fallback (backup)
        # ==========================================
        if self.embed_client and settings.router_fallback_enabled:
            try:
                embed_result = await self._embedding_classify(query)
                logger.info(
                    "router.embedding_classify",
                    intent=embed_result.intent.value,
                    confidence=embed_result.confidence,
                    method="embedding"
                )
                return embed_result
            except Exception as e:
                logger.error("router.embedding_error", error=str(e))

        # ==========================================
        # Default fallback
        # ==========================================
        logger.warning(
            "router.default_fallback",
            query=query[:100],
            default_intent=Intent.ISLAMIC_KNOWLEDGE.value
        )

        return RouterResult(
            intent=Intent.ISLAMIC_KNOWLEDGE,
            confidence=0.5,
            method="fallback",
            language=self._detect_language(query),
            reason="No classifier matched with sufficient confidence, defaulting to general knowledge"
        )
```

**شرح التدفق**:

```
query: "ما حكم صلاة العيد؟"
    ↓
1. هل query فارغ؟ → لا
    ↓
2. Tier 1: Keyword match
   - _keyword_match("ما حكم صلاة العيد؟")
   - يجد "ما حكم" في KEYWORD_PATTERNS[FIQH]
   - يرجع RouterResult(confidence=0.92)
   - 0.92 >= 0.90 → ✅ يرجع النتيجة
    ↓
RouterResult(intent=FIQH, confidence=0.92, method="keyword")
```

**لماذا 3 tiers؟**:

| Tier | السرعة | الدقة | التكلفة |
|------|--------|-------|---------|
| Keyword | microseconds | 70% | مجاني |
| LLM | milliseconds | 90% | مكلف |
| Embedding | milliseconds | 80% | متوسط |

---

### الأسطر 201-230: دالة _keyword_match()

```python
    def _keyword_match(self, query: str) -> Optional[RouterResult]:
        """
        Fast keyword-based intent detection.
        """
        query_lower = query.lower()
        language = self._detect_language(query)

        for intent, patterns in KEYWORD_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in query_lower:
                    return RouterResult(
                        intent=intent,
                        confidence=0.92,
                        method="keyword",
                        language=language,
                        requires_retrieval=intent in [
                            Intent.FIQH,
                            Intent.ISLAMIC_KNOWLEDGE,
                            Intent.QURAN,
                        ],
                        reason=f"Keyword match: '{pattern}'"
                    )

        return None
```

**شرح**:

```python
query = "ما حكم صلاة العيد؟"
query_lower = "ما حكم صلاة العيد؟"

# iteration 1: intent=FIQH, patterns=["حكم", "ما حكم", ...]
#   pattern = "حكم" → ليس في query
#   pattern = "ما حكم" → ✅ في query!
#   → يرجع RouterResult(intent=FIQH, confidence=0.92)
```

**لماذا confidence=0.92؟**:
- لأنه سريع لكن ليس دقيقاً دائماً
- "ما حكم" قد تكون في سؤال غير فقه (نادر)

---

### الأسطر 231-280: دالة _llm_classify()

```python
    async def _llm_classify(self, query: str) -> RouterResult:
        """
        LLM-based intent classification.
        """
        try:
            # Build prompt with intent descriptions
            intent_descriptions = "\n".join(
                f"- {k.value}: {v}" for k, v in INTENT_DESCRIPTIONS.items()
            )

            prompt = self.LLM_CLASSIFIER_PROMPT.format(
                intent_descriptions=intent_descriptions,
                query=query
            )

            # Call LLM
            response = await self.llm_client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert intent classifier. Return ONLY valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Deterministic
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            result = json.loads(content)

            # Validate and normalize
            intent = Intent(result.get("intent", Intent.ISLAMIC_KNOWLEDGE))
            confidence = float(result.get("confidence", 0.8))
            language = result.get("language", self._detect_language(query))
            requires_retrieval = result.get("requires_retrieval", True)
            sub_intent = result.get("sub_intent")
            reason = result.get("reason", "LLM classification")

            return RouterResult(
                intent=intent,
                confidence=confidence,
                method="llm",
                language=language,
                requires_retrieval=requires_retrieval,
                sub_intent=sub_intent,
                reason=reason
            )

        except json.JSONDecodeError as e:
            logger.error("router.llm_json_error", error=str(e))
            raise ValueError(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            logger.error("router.llm_error", error=str(e))
            raise
```

**شرح**:

```
1. يبني prompt:
   - يضيف أوصاف النيات
   - يضيف السؤال
    ↓
2. يرسل لـ LLM:
   - model: qwen/qwen3-32b
   - temperature: 0.0 (دقيق جداً)
   - response_format: json_object
    ↓
3. يستلم JSON:
   {"intent": "fiqh", "confidence": 0.95, ...}
    ↓
4. يحلل JSON:
   - json.loads(content)
    ↓
5. يرجع RouterResult
```

**لماذا temperature=0.0؟**:
- نريد إجابة **دقيقة ومتسقة**
- نفس السؤال → نفس الإجابة دائماً

---

### الأسطر 281-295: دالة _detect_language()

```python
    def _detect_language(self, query: str) -> str:
        """
        Detect if query is Arabic or English.
        Uses Unicode range detection for Arabic script.
        """
        arabic_chars = sum(
            1 for char in query
            if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F'
        )

        total_chars = len(query.replace(" ", ""))
        if total_chars == 0:
            return "ar"

        arabic_ratio = arabic_chars / total_chars
        return "ar" if arabic_ratio > 0.3 else "en"
```

**شرح**:

```python
query = "ما حكم صلاة العيد؟"

# حساب الحروف العربية:
# '\u0600' <= 'م' <= '\u06FF' → ✅
# '\u0600' <= 'ا' <= '\u06FF' → ✅
# ...
arabic_chars = 15

total_chars = 15 (بدون مسافات)

arabic_ratio = 15 / 15 = 1.0
1.0 > 0.3 → يرجع "ar"
```

**لماذا 0.3؟**:
- إذا كان 30% من النص عربي، نعتبره عربي
- يسمح بكلمات إنجليزية في نص عربي

---

## 🏗️ التحديثات في الإصدار v2 - نظام التوجيه الجديد

### ما الجديد؟
مع الإصدار v2، انتقل التوجيه من `src/core/router.py` إلى **نظام تصريحي** جديد:

```
src/application/routing/
├── intent_router.py    ← router هجين جديد (v2)
├── planner.py          ← مخطط الاستجابة
└── executor.py        ← منفذ الاستجابة
```

### الفرق بين v1 و v2

| الجانب | v1 (Legacy) | v2 (Config-Backed) |
|--------|-------------|-------------------|
| **التوجيه** | `src/core/router.py` | `src/application/routing/intent_router.py` |
| **التصنيف** | HybridQueryClassifier (3 tiers) | IntentRouter + decision tree |
| **التكوين** | كود صلب | YAML config |
| **الـ Prompts** | strings في الكود | ملفات منفصلة |

### مثال على التوجيه في v2

```python
from src.application.routing import IntentRouter

router = IntentRouter()
result = await router.route("ما حكم الزكاة؟")
# result.agent = "fiqh"
# result.confidence = 0.95
# result.strategy = "semantic"
```

### للمزيد من التفاصيل
- راجع: [`V2_MIGRATION_NOTES.md`](../../8-development/refactoring/V2_MIGRATION_NOTES.md)
- راجع: [`02_folder_structure.md`](02_folder_structure.md) - المعمارية الجديدة

---

## 5️⃣ الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً؟

1. **3 tiers**: Keyword → LLM → Embedding
2. **Keyword سريع** (microseconds) لكن أقل دقة
3. **LLM دقيق** لكن مكلف (يحتاج API call)
4. **Embedding fallback** عندما يفشل الاثنين

### 📝 تمرين صغير

1. ما هو `CONFIDENCE_THRESHOLD`؟
2. لماذا keyword confidence=0.92؟
3. ماذا يحدث إذا فشل الـ 3 tiers؟

### 🔜 الخطوة التالية

اقرأ الملف 4: `src/core/registry.py`

---

*(يتبع شرح الملفات 4-10 بنفس التفصيل...)*

---

**📖 الدليل الكامل:** [`docs/mentoring/`](docs/mentoring/)
