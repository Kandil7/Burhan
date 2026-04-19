# 📂 الملفات 6-10: الوكلاء والأدوات - شرح شامل

## 🕌 مقدمة

هذا الملف يشرح **5 ملفات متبقية** (6-10) في آن واحد لأنها مترابطة:

| الملف | السطور | الوظيفة |
|-------|--------|---------|
| **6** | `src/agents/base.py` | 90 | الفئات الأساسية للوكلاء |
| **7** | `src/agents/chatbot_agent.py` | 160 | وكيل الترحيب |
| **8** | `src/agents/fiqh_agent.py` | 280 | وكيل الفقه (RAG) |
| **9** | `src/tools/base.py` | 70 | فئة الأدوات |
| **10** | `src/tools/zakat_calculator.py` | 350 | حاسبة الزكاة |

---

# الملف 6: `src/agents/base.py` (90 سطر)

## 1️⃣ وظيفة الملف

يعرف **الفئات الأساسية** التي يرث منها كل الوكلاء. يضمن أن كل وكيل يستخدم نفس النموذج للدخل والخرج.

---

## 2️⃣ نظرة عامة

| القسم | الأسطر | المحتوى |
|-------|--------|---------|
| Citation model | 1-20 | نموذج الاقتباس |
| AgentInput | 21-45 | نموذج الدخل |
| AgentOutput | 46-75 | نموذج الخرج |
| BaseAgent | 76-90 | الفئة المجردة |

---

## 3️⃣ شرح سطر بسطر

### الأسطر 1-20: Citation model

```python
class Citation(BaseModel):
    """
    Normalized citation reference.

    Every agent returns citations in this standardized format,
    which are then normalized to [C1], [C2], etc. for display.
    """
    id: str = Field(description="Citation ID: C1, C2, C3, etc.")
    type: str = Field(description="Type: quran, hadith, fatwa, fiqh_book, dua")
    source: str = Field(description="Normalized source name")
    reference: str = Field(description="Specific reference (book, chapter, number)")
    url: Optional[str] = Field(default=None, description="External URL (quran.com, sunnah.com)")
    text_excerpt: Optional[str] = Field(default=None, description="Quoted passage")
```

**شرح كل حقل**:

| الحقل | النوع | الوصف | مثال |
|-------|-------|-------|------|
| `id` | str | معرف الاقتباس | "C1", "C2" |
| `type` | str | نوع المصدر | "quran", "hadith" |
| `source` | str | اسم المصدر | "Quran 2:255" |
| `reference` | str | المرجع التفصيلي | "Surah 2, Ayah 255" |
| `url` | Optional[str] | رابط خارجي | "https://quran.com/2/255" |
| `text_excerpt` | Optional[str] | نص مقتبس | "الله لا إله إلا هو..." |

**مثال كامل**:

```python
Citation(
    id="C1",
    type="quran",
    source="Quran 2:255",
    reference="Surah 2, Ayah 255 - Ayat al-Kursi",
    url="https://quran.com/2/255",
    text_excerpt="اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ..."
)
```

**لماذا مهم**:
- كل الاقتباسات نفس الشكل
- يسهل العرض والتنسيق
- يدعم التحقق من المصادر

---

### الأسطر 21-45: AgentInput

```python
class AgentInput(BaseModel):
    """
    Standardized input for all agents.

    Contains query text, language preference, optional context,
    and metadata from the intent classifier.
    """
    query: str = Field(description="User's question")
    language: str = Field(default="ar", description="Response language: ar or en")
    context: Optional[dict] = Field(
        default=None,
        description="Conversation context (previous queries, user preferences)"
    )
    retrieved_passages: Optional[list] = Field(
        default=None,
        description="Retrieved documents from RAG (if applicable)"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (location, madhhab, session_id)"
    )
```

**شرح كل حقل**:

| الحقل | النوع | افتراضي | الوصف | مثال |
|-------|-------|---------|-------|------|
| `query` | str | مطلوب | سؤال المستخدم | "ما حكم صلاة العيد؟" |
| `language` | str | "ar" | لغة الإجابة | "ar", "en" |
| `context` | Optional[dict] | None | سياق المحادثة | {"prev_query": "..."} |
| `retrieved_passages` | Optional[list] | None | وثائق من RAG | [{"content": "..."}] |
| `metadata` | dict | {} | بيانات إضافية | {"madhhab": "shafii"} |

**مثال كامل**:

```python
AgentInput(
    query="ما حكم صلاة العيد؟",
    language="ar",
    context=None,
    retrieved_passages=[
        {"content": "صلاة العيد سنة مؤكدة...", "source": "موطأ مالك"},
        {"content": "كان النبي يصلي العيد...", "source": "صحيح البخاري"}
    ],
    metadata={
        "madhhab": "shafii",
        "location": "Riyadh",
        "session_id": "abc123"
    }
)
```

---

### الأسطر 46-75: AgentOutput

```python
class AgentOutput(BaseModel):
    """
    Standardized output for all agents.

    Contains answer, citations, and metadata for response assembly.
    """
    answer: str = Field(description="Agent's answer text")
    citations: list[Citation] = Field(
        default_factory=list,
        description="List of citations with structured references"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Metadata (agent name, processing time, madhhab, etc.)"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the answer (0.0-1.0)"
    )
    requires_human_review: bool = Field(
        default=False,
        description="Flag if this response needs scholarly review"
    )
```

**شرح كل حقل**:

| الحقل | النوع | افتراضي | الوصف | مثال |
|-------|-------|---------|-------|------|
| `answer` | str | مطلوب | الإجابة | "صلاة العيد سنة مؤكدة..." |
| `citations` | list[Citation] | [] | قائمة المصادر | [Citation(...), Citation(...)] |
| `metadata` | dict | {} | بيانات إضافية | {"agent": "fiqh_agent"} |
| `confidence` | float | 1.0 | درجة الثقة | 0.89 (0-1) |
| `requires_human_review` | bool | False | يحتاج مراجعة؟ | True إذا مصادر ضعيفة |

**مثال كامل**:

```python
AgentOutput(
    answer="صلاة العيد سنة مؤكدة عند الجمهور...\n\n[C1] [C2]",
    citations=[
        Citation(id="C1", type="quran", source="Quran 2:255", ...),
        Citation(id="C2", type="hadith", source="Sahih Bukhari", ...)
    ],
    metadata={
        "agent": "fiqh_agent",
        "processing_time": 1.23,
        "madhhab": "shafii",
        "retrieved_count": 15,
        "used_count": 5
    },
    confidence=0.89,
    requires_human_review=False
)
```

---

### الأسطر 76-90: BaseAgent

```python
class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Agents handle queries requiring knowledge retrieval, reasoning,
    or text generation. Examples: FiqhAgent, QuranAgent, GeneralIslamicAgent.
    """

    name: str = "base_agent"

    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        """
        Execute agent logic and return result.
        """
        pass

    async def __call__(self, **kwargs) -> AgentOutput:
        """Allow agent to be called directly like a function."""
        input_data = AgentInput(**kwargs)
        return await self.execute(input_data)

    def __repr__(self) -> str:
        return f"<Agent: {self.name}>"
```

**شرح**:

| العنصر | الوصف |
|--------|-------|
| `ABC` | Abstract Base Class (لا يمكن إنشاء نسخة مباشرة) |
| `name` | اسم الوكيل (يحدد في الوراثة) |
| `execute()` | دالة مجردة (يجب تطبيقها في الوراثة) |
| `__call__()` | يسمح بالاستدعاء المباشر |
| `__repr__()` | تمثيل نصي |

**مثال وراثة**:

```python
class FiqhAgent(BaseAgent):
    name = "fiqh_agent"  # يحدد الاسم

    async def execute(self, input: AgentInput) -> AgentOutput:
        # يطبق المنطق هنا
        return AgentOutput(answer="...", citations=[...])
```

**لماذا Abstract؟**:
- يجبر المطورين على تطبيق `execute()`
- يضمن واجهة موحدة لكل الوكلاء
- يمنع إنشاء `BaseAgent()` مباشرة

---

## 5️⃣ الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً؟

1. **Citation** نموذج موحد لكل المصادر
2. **AgentInput** دخل موحد لكل الوكلاء
3. **AgentOutput** خرج موحد لكل الوكلاء
4. **BaseAgent** يجبر على تطبيق `execute()`

---

# الملف 7: `src/agents/chatbot_agent.py` (160 سطر)

## 1️⃣ وظيفة الملف

وكيل بسيط للترحيب والتحيات. **لا يستخدم LLM** بل قوالب جاهزة (templates).

---

## 2️⃣ نظرة عامة

| القسم | الأسطر | المحتوى |
|-------|--------|---------|
| Imports | 1-15 | مكتبات |
| Greeting templates | 16-50 | قوالب الترحيب |
| Small talk templates | 51-80 | قوالب الحديث |
| execute() | 81-130 | الدالة الرئيسية |
| Helpers | 131-160 | دوال مساعدة |

---

## 3️⃣ شرح سطر بسطر

### الأسطر 16-50: Greeting templates

```python
GREETINGS_AR = [
    {"text": "وعليكم السلام ورحمة الله وبركاته", "translation": "And upon you be peace..."},
    {"text": "أهلاً وسهلاً", "translation": "Welcome"},
    {"text": "حياك الله", "translation": "May Allah greet you"},
]

GREETINGS_EN = [
    {"text": "Wa alaikum assalam wa rahmatullahi wa barakatuh", "translation": None},
    {"text": "Welcome! How can I help you today?", "translation": None},
    {"text": "Assalamu alaikum! May Allah bless you", "translation": "Peace be upon you"},
]

RAMADAN_GREETINGS = [
    {"text": "رمضان مبارك! تقبل الله منا ومنكم", "translation": "Ramadan Mubarak!..."},
    {"text": "Ramadan Kareem! May this blessed month...", "translation": None},
]

EID_GREETINGS = [
    {"text": "عيد مبارك! تقبل الله منا ومنكم صالح الأعمال", "translation": "Eid Mubarak!..."},
    {"text": "Eid Mubarak! May Allah bless you and your family", "translation": None},
]
```

**شرح**:

| القائمة | الاستخدام | أمثلة |
|---------|-----------|-------|
| `GREETINGS_AR` | تحيات عربية | "وعليكم السلام" |
| `GREETINGS_EN` | تحيات إنجليزية | "Wa alaikum assalam" |
| `RAMADAN_GREETINGS` | رمضان | "رمضان مبارك" |
| `EID_GREETINGS` | العيد | "عيد مبارك" |

**لماذا قائمة؟**:
- يختار عشوائياً (random.choice)
- يعطي تنوع في الردود
- يمنع التكرار

---

### الأسطر 81-130: execute()

```python
    async def execute(self, input: AgentInput) -> AgentOutput:
        """Generate appropriate greeting or small talk response."""
        query = input.query.lower()
        language = input.language or self._detect_language(input.query)

        # Check for special occasions
        is_ramadan = input.metadata.get("is_ramadan", False)
        is_eid = input.metadata.get("is_eid", False)

        # Determine response type
        if self._is_greeting(query):
            if is_ramadan:
                response = random.choice(RAMADAN_GREETINGS)
            elif is_eid:
                response = random.choice(EID_GREETINGS)
            elif language == "ar":
                response = random.choice(GREETINGS_AR)
            else:
                response = random.choice(GREETINGS_EN)

            answer = response["text"]
            if response.get("translation"):
                answer += f"\n\n({response['translation']})"

        elif self._is_small_talk(query):
            intent = self._classify_small_talk(query)
            templates = SMALL_TALK_AR if language == "ar" else SMALL_TALK_EN
            response = random.choice(templates.get(intent, [{"text": "..."}]))
            answer = response["text"]
            if response.get("translation"):
                answer += f"\n\n({response['translation']})"

        else:
            # Fallback for unrecognized input
            answer = (
                "أعتذر، لم أفهم سؤالك بشكل كامل. يرجى السؤال عن:\n"
                "- أحكام فقهية\n"
                "- آيات قرآنية\n"
                "- زكاة أو ميراث\n"
                "- أذكار وأدعية"
            )

        return AgentOutput(
            answer=answer,
            citations=[],
            metadata={
                "agent": self.name,
                "language": language,
                "response_type": "greeting" if self._is_greeting(query) else "small_talk",
            },
            confidence=0.95
        )
```

**شرح التدفق**:

```
Input: AgentInput(query="السلام عليكم", language="ar")
    ↓
1. query.lower() = "السلام عليكم"
2. language = "ar"
3. is_ramadan = False, is_eid = False
4. _is_greeting("السلام عليكم") → True (يجد "سلام")
5. language == "ar" → True
6. response = random.choice(GREETINGS_AR)
   → {"text": "وعليكم السلام ورحمة الله وبركاته", ...}
7. answer = "وعليكم السلام ورحمة الله وبركاته"
8. translation موجود → يضيفه
9. يرجع AgentOutput(answer="وعليكم السلام...\n\n(And upon you...)")
```

**لماذا random.choice؟**:
- تنوع في الردود
- يمنع الملل
- محاكاة المحادثة الحقيقية

---

### الأسطر 131-160: Helper functions

```python
    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting."""
        greeting_keywords = [
            "سلام", "السلام", "مرحبا", "اهلا", "هلا",
            "hello", "hi", "hey", "greetings", "assalam",
            "ramadan", "eid", "رمضان", "عيد"
        ]
        return any(keyword in query.lower() for keyword in greeting_keywords)

    def _is_small_talk(self, query: str) -> bool:
        """Check if query is small talk."""
        small_talk_keywords = [
            "كيف حالك", "كيفك", "شلونك", "عامل",
            "how are you", "how do you do",
            "شكراً", "شكرا", "ممنون", "جزاك",
            "thank", "thanks", "jazak"
        ]
        return any(keyword in query.lower() for keyword in small_talk_keywords)

    def _classify_small_talk(self, query: str) -> Optional[str]:
        """Classify small talk intent."""
        if any(k in query for k in ["كيف حالك", "كيفك", "how are you"]):
            return "how_are_you"
        elif any(k in query for k in ["شكر", "thank", "جزاك"]):
            return "thank_you"
        return None

    def _detect_language(self, query: str) -> str:
        """Detect if query is Arabic or English."""
        arabic_chars = sum(1 for c in query if '\u0600' <= c <= '\u06FF')
        total_chars = len(query.replace(" ", ""))
        if total_chars == 0:
            return "ar"
        return "ar" if (arabic_chars / total_chars) > 0.3 else "en"
```

**شرح**:

```python
# _is_greeting()
_is_greeting("السلام عليكم")  # True (يجد "سلام")
_is_greeting("hello world")   # True (يجد "hello")
_is_greeting("ما حكم الصلاة؟") # False

# _is_small_talk()
_is_small_talk("كيف حالك؟")   # True (يجد "كيف حالك")
_is_small_talk("شكراً جزيلاً") # True (يجد "شكر")
_is_small_talk("ما حكم الزكاة؟") # False

# _classify_small_talk()
_classify_small_talk("كيف حالك؟")   # "how_are_you"
_classify_small_talk("شكراً")       # "thank_you"
_classify_small_talk("ما هذا؟")     # None

# _detect_language()
_detect_language("السلام عليكم")    # "ar" (100% عربي)
_detect_language("hello мир")       # "en" (أقل من 30% عربي)
_detect_language("مرحبا hello")     # "ar" (أكثر من 30% عربي)
```

---

## 5️⃣ الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً؟

1. **Template-based** - لا يستخدم LLM
2. **Random choice** للتنوع
3. **Language detection** يختار القالب المناسب
4. **Fallback** يعطي رسالة خطأ واضحة

---

# الملف 8: `src/agents/fiqh_agent.py` (280 سطر)

## 1️⃣ وظيفة الملف

وكيل الفقه يستخدم **RAG كامل**:
1. يسترجع وثائق من Qdrant
2. يولد إجابة بـ LLM
5. يطبع الاقتباسات

---

## 2️⃣ نظرة عامة

| القسم | الأسطر | المحتوى |
|-------|--------|---------|
| Imports | 1-20 | مكتبات |
| Constants | 21-30 | ثوابت من config |
| Prompts | 31-50 | System و User prompts |
| __init__() | 51-80 | التهيئة |
| _initialize() | 81-120 | تهيئة كسولة |
| execute() | 121-200 | الدالة الرئيسية |
| _format_passages() | 201-220 | تنسيق الوثائق |
| _generate_with_llm() | 221-260 | توليد بـ LLM |
| _generate_answer_from_passages() | 261-280 | fallback بدون LLM |

---

## 3️⃣ شرح مختصر (للإيجاز)

### Pipeline الرئيسية

```
execute()
    ↓
1. _initialize()              ← تهيئة Embedding, VectorStore, LLM
    ↓
2. embedding_model.encode()   ← تحويل السؤال لمتجه
    ↓
3. hybrid_searcher.search()   ← بحث في Qdrant (top 15)
    ↓
4. filter by score threshold  ← تصفية (threshold: 0.15)
    ↓
5. _format_passages()         ← تنسيق للـ LLM
    ↓
6. _generate_with_llm()       ← توليد إجابة بـ Groq
    ↓
7. citation_normalizer        ← تحويل المصادر لـ [C1], [C2]
    ↓
8. _add_disclaimer()          ← إضافة تنويه
    ↓
AgentOutput(answer, citations, confidence)
```

---

# الملف 9: `src/tools/base.py` (70 سطر)

## 1️⃣ وظيفة الملف

يعرف **الفئة الأساسية** لكل الأدوات الحتمية.

---

## 2️⃣ شرح مختصر

```python
class ToolInput(BaseModel):
    query: str
    metadata: dict  # معاملات خاصة (location, assets, ...)

class ToolOutput(BaseModel):
    result: dict    # نتيجة الحساب
    success: bool   # نجاح أم خطأ
    error: str      # رسالة الخطأ
    metadata: dict  # بيانات إضافية

class BaseTool(ABC):
    name: str = "base_tool"
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolOutput:
        pass
```

**الفرق بين Agent و Tool**:

| الوجه | Agent | Tool |
|-------|-------|------|
| LLM | ✅ يستخدم | ❌ لا يستخدم |
| RAG | ✅ يحتاج | ❌ لا يحتاج |
| Deterministic | ❌ إجابة مختلفة | ✅ نفس الإجابة |
| مثال | FiqhAgent | ZakatCalculator |

---

# الملف 10: `src/tools/zakat_calculator.py` (350 سطر)

## 1️⃣ وظيفة الملف

يحسب **الزكاة** بدقة حسب الشريعة الإسلامية.

---

## 2️⃣ أهم المحتويات

### ZakatType enum (7 أنواع)

```python
class ZakatType(str, Enum):
    WEALTH = "wealth"        # المال
    GOLD = "gold"            # الذهب
    SILVER = "silver"        # الفضة
    TRADE_GOODS = "trade_goods"  # عروض التجارة
    STOCKS = "stocks"        # الأسهم
    LIVESTOCK = "livestock"  # الماشية
    CROPS = "crops"          # الزروع
```

### Madhhab enum (4 مذاهب)

```python
class Madhhab(str, Enum):
    HANAFI = "hanafi"
    MALIKI = "maliki"
    SHAFII = "shafii"
    HANBILI = "hanbali"
```

### calculate() method

```python
def calculate(self, assets: ZakatAssets, debts: float = 0.0, madhhab: Madhhab = Madhhab.GENERAL) -> ZakatResult:
    # 1. حساب النصاب
    nisab_gold = 85 * gold_price      # 85 جرام ذهب
    nisab_silver = 595 * silver_price # 595 جرام فضة
    nisab_effective = min(nisab_gold, nisab_silver)  # الأدنى (أفضل للفقراء)
    
    # 2. حساب الأصول
    total_assets = cash + gold_value + silver_value + ...
    
    # 3. خصم الديون
    zakatable_wealth = total_assets - debts
    
    # 4. مقارنة بالنصاب
    is_zakatable = zakatable_wealth >= nisab_effective
    
    # 5. حساب الزكاة
    if is_zakatable:
        zakat_amount = zakatable_wealth * 0.025  # 2.5%
    
    return ZakatResult(...)
```

### Livestock zakat (hadith rates)

```python
def calculate_livestock_zakat(self, camels=0, cows=0, goats=0, sheep=0) -> dict:
    # Rates from Sahih Bukhari:
    # Camels:
    #   1-4:    No zakat
    #   5-9:    1 sheep
    #   10-14:  2 sheep
    #   25-35:  1 bint makhad (1-year she-camel)
    #   ...
    
    # Cows:
    #   1-29:   No zakat
    #   30-39:  1 tabi' (1-year)
    #   40-59:  1 musinnah (2-year)
    #   ...
    
    # Goats/Sheep:
    #   1-39:   No zakat
    #   40-120: 1 sheep
    #   121-200: 2 sheep
    #   ...
```

### Crops zakat

```python
def calculate_crops_zakat(self, total_value: float, irrigation_type: str = "irrigated") -> dict:
    if irrigation_type == "natural":  # مطري
        rate = 0.10  # 10%
    else:  # مروى
        rate = 0.05  # 5%
    
    return total_value * rate
```

**لماذا مختلف؟**:
- القرآن 6:141: "وَآتُوا حَقَّهُ يَوْمَ حَصَادِهِ"
- الحديث: "ما سقت السماء فالعشر، وما سقي بالنضح فنصف العشر"

---

## 5️⃣ الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً؟

1. **BaseAgent** و **BaseTool** يضمنان واجهة موحدة
2. **ChatbotAgent** template-based (بدون LLM)
3. **FiqhAgent** RAG كامل (retrieve → generate → cite)
4. **ZakatCalculator** حتمية (نفس الدخل → نفس الخرج)
5. **Livestock و Crops** rates من الحديث والقرآن

### 📝 تمرين شامل

1. ارسم diagram للفرق بين Agent و Tool
2. تتبع سؤال من البداية للنهاية
3. اكتب Agent جديد: `FatwaAgent`
4. اكتب Tool جديد: `QiblaFinderTool`

---

## 🏗️ التحديثات في الإصدار v2 - الوكلاء والأدوات

### ما الجديد؟
مع الإصدار v2، تم إعادة هيكلة الوكلاء والأدوات:

```
src/agents/
├── collection/           ← NEW! 10 وكلاء بمعمارية CollectionAgent
│   ├── base.py           ← CollectionAgent الأساسي
│   ├── fiqh.py          ← وكيل الفقه (config-backed)
│   ├── hadith.py        ← وكيل الحديث
│   ├── tafsir.py        ← وكيل التفسير
│   ├── aqeedah.py       ← وكيل العقيدة
│   ├── seerah.py        ← وكيل السيرة
│   ├── usul_fiqh.py     ← وكيل أصول الفقه
│   ├── history.py       ← وكيل التاريخ
│   ├── language.py      ← وكيل اللغة العربية
│   ├── tazkiyah.py      ← وكيل التربية الروحية
│   └── general.py       ← وكيل العام
├── legacy/               ← DEPRECATED! الوكلاء القدامى
├── base.py              ← DEPRECATED! (base.py القديم)
└── ... (individual agents) ← DEPRECATED!

src/tools/
└── (لا تغيير - الأدوات الحتمية تبقى كما هي)
```

### الفرق بين v1 و v2

| الجانب | v1 (Legacy) | v2 (Config-Backed) |
|--------|-------------|-------------------|
| **الفئة الأساسية** | `BaseAgent` | `CollectionAgent` |
| **التكوين** | كود Python | YAML files |
| **الـ Prompts** | strings في الكود | ملفات .txt منفصلة |
| **عدد الوكلاء** | 13 وكيل | 10 وكلاء collection + legacy |

### مثال على CollectionAgent في v2

```python
from src.agents.collection import FiqhAgent

# إنشاء الوكيل من التكوين
agent = FiqhAgent()

# أو من التكوين المخصص
agent = FiqhAgent(
    config_path="config/agents/fiqh.yaml",
    prompt_path="prompts/fiqh/"
)
```

### لماذا لم تتغير الأدوات؟
- الأدوات (Tools) هي **حتمية** deterministic
- لا تحتاج LLM أو RAG
- `ZakatCalculator`, `InheritanceCalculator` تبقى كما هي

### للمزيد من التفاصيل
- راجع: [`V2_MIGRATION_NOTES.md`](../../8-development/refactoring/V2_MIGRATION_NOTES.md)
- راجع: [`02_folder_structure.md`](02_folder_structure.md)

---

**📖 الدليل الكامل:** [`docs/mentoring/`](docs/mentoring/)
