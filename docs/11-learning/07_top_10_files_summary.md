# 🕌 ملخص شامل - أهم 10 ملفات في Burhan

## 📚 المقدمة

هذا الملف يقدم **ملخص سريع** لأهم 10 ملفات في مشروع Burhan مع روابط للشروحات التفصيلية.

---

## 🎯 أهم 10 ملفات بالترتيب

| الأولوية | الملف | السطور | الوظيفة | الحالة |
|----------|-------|--------|---------|--------|
| **1** | `src/config/settings.py` | 140 | كل إعدادات التطبيق | ✅ مشروح |
| **2** | `src/config/intents.py` | 180 | 16 نوع نية + كلمات مفتاحية | ✅ مشروح |
| **3** | `src/core/router.py` | 250 | تصنيف النية (3-tier) | ✅ مشروح |
| **4** | `src/core/registry.py` | 190 | تسجيل الوكلاء والأدوات | 📝 قريباً |
| **5** | `src/core/citation.py` | 350 | تطبيع الاقتباسات | 📝 قريباً |
| **6** | `src/agents/base.py` | 90 | الفئات الأساسية للوكلاء | 📝 قريباً |
| **7** | `src/agents/chatbot_agent.py` | 160 | وكيل الترحيب (أبسط وكيل) | 📝 قريباً |
| **8** | `src/agents/fiqh_agent.py` | 280 | وكيل الفقه (RAG كامل) | 📝 قريباً |
| **9** | `src/tools/base.py` | 70 | فئة الأدوات الحتمية | 📝 قريباً |
| **10** | `src/tools/zakat_calculator.py` | 350 | حاسبة الزكاة | 📝 قريباً |

---

## 📊 ملخص كل ملف

### 1. `settings.py` (140 سطر)

**الوظيفة:** كل إعدادات التطبيق في مكان واحد

**أهم المحتويات:**
- 37 متغير بيئة
- PostgreSQL, Redis, Qdrant settings
- LLM provider (Groq/OpenAI)
- Embedding model (BAAI/bge-m3)
- Validators للتحقق من الإعدادات

**مثال:**
```python
class Settings(BaseSettings):
    llm_provider: str = "groq"
    groq_model: str = "qwen/qwen3-32b"
    embedding_model: str = "BAAI/bge-m3"
    database_url: str = "postgresql+asyncpg://..."
```

**📖 الشرح التفصيلي:** [`04_top_10_files_deep_explanation.md`](04_top_10_files_deep_explanation.md#الملف-1-srcconfigsettingspy-140-سطر)

---

### 2. `intents.py` (180 سطر)

**الوظيفة:** تعريف 16 نوع نية + كلمات مفتاحية

**أهم المحتويات:**
- `Intent` Enum (16 نوع)
- `QuranSubIntent` Enum (4 أنواع فرعية)
- `INTENT_DESCRIPTIONS` (أوصاف للـ LLM)
- `INTENT_ROUTING` (توجيه للوكلاء)
- `KEYWORD_PATTERNS` (للتصنيف السريع)

**مثال:**
```python
class Intent(str, Enum):
    FIQH = "fiqh"
    QURAN = "quran"
    ZAKAT = "zakat"
    # ... (16 نوع)

INTENT_ROUTING = {
    Intent.FIQH: "fiqh_agent",
    Intent.QURAN: "quran_agent",
    Intent.ZAKAT: "zakat_tool",
}
```

**📖 الشرح التفصيلي:** [`04_top_10_files_deep_explanation.md`](04_top_10_files_deep_explanation.md#الملف-2-srcconfigintentspy-180-سطر)

---

### 3. `router.py` (250 سطر)

**الوظيفة:** تصنيف نية المستخدم (3-tier)

**أهم المحتويات:**
- `RouterResult` (نموذج النتيجة)
- `HybridQueryClassifier` (المصنف الرئيسي)
- Tier 1: Keyword matching (0.92 confidence)
- Tier 2: LLM classification (0.75 threshold)
- Tier 3: Embedding fallback
- Language detection (Arabic/English)

**مثال:**
```python
classifier = HybridQueryClassifier(llm_client=openai_client)
result = await classifier.classify("ما حكم صلاة العيد؟")
# RouterResult(intent=Intent.FIQH, confidence=0.92, method="keyword")
```

**📖 الشرح التفصيلي:** [`05_router_deep_dive.md`](05_router_deep_dive.md)

---

### 4. `registry.py` (190 سطر)

**الوظيفة:** تسجيل الوكلاء والأدوات

**أهم المحتويات:**
- `AgentRegistration` dataclass
- `AgentRegistry` class
- `register_agent()`, `register_tool()`
- `get_for_intent()`
- `initialize_registry()`

**مثال:**
```python
registry = AgentRegistry()
registry.register_tool("zakat_tool", ZakatCalculator())
registry.register_agent("fiqh_agent", FiqhAgent())

agent, is_agent = registry.get_for_intent(Intent.FIQH)
```

**📖 الشرح التفصيلي:** 📝 قريباً

---

### 5. `citation.py` (350 سطر)

**الوظيفة:** تطبيع الاقتباسات من مصادر مختلفة

**أهم المحتويات:**
- `CitationNormalizer` class
- 6 regex patterns (Quran, Hadith, Fatwa, Fiqh books)
- External URLs (quran.com, sunnah.com, islamweb.net)
- Era classification (prophetic → modern)
- Rich metadata enrichment

**مثال:**
```python
normalizer = CitationNormalizer()
text = "قال ابن تيمية في مجموع الفتاوى..."
normalized = normalizer.normalize(text)
# "قال ابن تيمية [C1]..."
citations = normalizer.get_citations()
```

**📖 الشرح التفصيلي:** 📝 قريباً

---

### 6. `base.py (agents)` (90 سطر)

**الوظيفة:** الفئات الأساسية لكل الوكلاء

**أهم المحتويات:**
- `Citation` model
- `AgentInput` model
- `AgentOutput` model
- `BaseAgent` abstract class
- `__call__()` magic method

**مثال:**
```python
class FiqhAgent(BaseAgent):
    name = "fiqh_agent"
    
    async def execute(self, input: AgentInput) -> AgentOutput:
        # Implementation
        return AgentOutput(answer="...", citations=[...])
```

**📖 الشرح التفصيلي:** 📝 قريباً

---

### 7. `chatbot_agent.py` (160 سطر)

**الوظيفة:** وكيل الترحيب والتحيات

**أهم المحتويات:**
- Greeting templates (Arabic/English)
- Ramadan/Eid greetings
- Small talk templates
- _is_greeting(), _is_small_talk()
- Language detection

**مثال:**
```python
agent = ChatbotAgent()
result = await agent.execute(AgentInput(query="السلام عليكم"))
# AgentOutput(answer="وعليكم السلام ورحمة الله وبركاته")
```

**📖 الشرح التفصيلي:** 📝 قريباً

---

### 8. `fiqh_agent.py` (280 سطر)

**الوظيفة:** وكيل الفقه (RAG كامل)

**أهم المحتويات:**
- Lazy initialization
- Retrieve → Generate → Cite pipeline
- Hybrid search integration
- Citation normalization
- Fallback mechanisms
- LLM answer generation
- Template-based fallback

**مثال:**
```python
agent = FiqhAgent()
result = await agent.execute(AgentInput(query="ما حكم صلاة العيد؟"))
# AgentOutput(
#     answer="صلاة العيد سنة مؤكدة...",
#     citations=[Citation(id="C1", type="fiqh_book", ...)],
#     confidence=0.89
# )
```

**📖 الشرح التفصيلي:** 📝 قريباً

---

### 9. `base.py (tools)` (70 سطر)

**الوظيفة:** فئة الأدوات الحتمية

**أهم المحتويات:**
- `ToolInput` model
- `ToolOutput` model
- `BaseTool` abstract class
- الفرق بين Agent و Tool

**مثال:**
```python
class ZakatCalculator(BaseTool):
    name = "zakat_tool"
    
    async def execute(self, **kwargs) -> ToolOutput:
        # Calculate zakat
        return ToolOutput(result={"zakat_amount": 1000.0})
```

**📖 الشرح التفصيلي:** 📝 قريباً

---

### 10. `zakat_calculator.py` (350 سطر)

**الوظيفة:** حاسبة الزكاة (أداة حتمية)

**أهم المحتويات:**
- `ZakatType` enum (7 أنواع)
- `Madhhab` enum (4 مذاهب)
- `ZakatAssets` dataclass
- `ZakatResult` dataclass
- `calculate()` method
- Livestock zakat (hadith rates)
- Crops zakat (5%/10%)
- Nisab calculation (85g gold, 595g silver)

**مثال:**
```python
calculator = ZakatCalculator(gold_price=75, silver_price=0.9)
assets = ZakatAssets(cash=50000, gold_grams=100)
result = calculator.calculate(assets, debts=5000, madhhab="shafii")
# ZakatResult(zakat_amount=1125.0, is_zakatable=True)
```

**📖 الشرح التفصيلي:** 📝 قريباً

---

## 📈 المقارنة بين الملفات

### حسب النوع

| النوع | الملفات | السطور |
|-------|---------|--------|
| **إعدادات** | settings.py, intents.py | 320 |
| **تصنيف** | router.py | 250 |
| **تسجيل** | registry.py | 190 |
| **اقتباسات** | citation.py | 350 |
| **وكلاء** | base.py, chatbot_agent.py, fiqh_agent.py | 530 |
| **أدوات** | base.py, zakat_calculator.py | 420 |
| **المجموع** | 10 ملفات | **2,060 سطر** |

### حسب الأهمية

| الأهمية | الملفات | السبب |
|---------|---------|-------|
| **أساسية** | settings.py, intents.py, router.py | بدونها لا يعمل التطبيق |
| **مهمة** | registry.py, citation.py, base.py (agents) | تحتاجها معظم الوظائف |
| **متقدمة** | fiqh_agent.py, zakat_calculator.py | أمثلة على التطبيق |

---

## 🎯 كيف تقرأ الملفات بالترتيب الصحيح

### للمبتدئين (اليوم 1-7)

```
اليوم 1-2: settings.py          ← فهم الإعدادات
اليوم 3-4: intents.py           ← فهم النيات
اليوم 5-6: router.py            ← فهم التصنيف
اليوم 7:    جرب التطبيق
```

### للمتوسطين (اليوم 8-14)

```
اليوم 8-9: registry.py          ← فهم التسجيل
اليوم 10:  citation.py          ← فهم الاقتباسات
اليوم 11-12: base.py (agents)   ← فهم الفئات
اليوم 13-14: chatbot_agent.py   ← أبسط وكيل
```

### للمتقدمين (اليوم 15-21)

```
اليوم 15-17: fiqh_agent.py      ← وكيل RAG كامل
اليوم 18:    base.py (tools)    ← فئة الأدوات
اليوم 19-21: zakat_calculator.py ← أداة حتمية
```

---

## 📝 تمارين شاملة

### تمرين 1: تتبع سؤال من البداية للنهاية

```
سؤال: "ما حكم صلاة العيد؟"

1. settings.py:      ما الإعدادات المستخدمة؟
2. intents.py:       ما النية؟ ما الكلمات المفتاحية؟
3. router.py:        كيف صُنف؟ ما الـ confidence؟
4. registry.py:      ما الوكيل المسؤول؟
5. citation.py:      كيف تُطبع الاقتباسات؟
6. base.py:          ما النموذج المستخدم؟
7. chatbot_agent.py: هل هذا الوكيل مناسب؟
8. fiqh_agent.py:    كيف يبحث ويجيب؟
9. base.py (tools):  هل يمكن استخدام أداة؟
10. zakat_calculator.py: هل هذا سؤال زكاة؟
```

### تمرين 2: إضافة نية جديدة

أضف نية جديدة: `fatwa`

```python
# 1. intents.py
class Intent(str, Enum):
    FATWA = "fatwa"

INTENT_ROUTING = {
    Intent.FATWA: "fatwa_agent",
}

KEYWORD_PATTERNS = {
    Intent.FATWA: ["فتوى", "fatwa", "ما رأيكم في"],
}

# 2. registry.py
registry.register_agent("fatwa_agent", FatwaAgent())

# 3. agents/fatwa_agent.py (جديد)
class FatwaAgent(BaseAgent):
    name = "fatwa_agent"
    
    async def execute(self, input: AgentInput) -> AgentOutput:
        # Implementation
        pass
```

### تمرين 3: تحسين الأداء

```python
# settings.py
llm_cache_enabled = True
llm_cache_ttl = 3600  # 1 ساعة

# router.py
# إضافة caching للـ classification

# fiqh_agent.py
# إضافة caching للـ embeddings
```

---

## 🔗 روابط ذات صلة

- [`01_project_overview.md`](01_project_overview.md) - نظرة عامة
- [`02_folder_structure.md`](02_folder_structure.md) - شرح المجلدات
- [`03_api_main_entrypoint.md`](03_api_main_entrypoint.md) - نقطة الدخول
- [`learning_path.md`](learning_path.md) - خطة التعلم
- [`quick_reference.md`](quick_reference.md) - ملخص سريع
- [`06_top_10_files_index.md`](06_top_10_files_index.md) - فهرس الملفات

---

## 📊 إحصائيات المشروع

| المقياس | القيمة |
|---------|--------|
| **الأسطر البرمجية** | ~14,200 سطر |
| **الملفات** | ~120 ملف |
| **أهم 10 ملفات** | 2,060 سطر (14.5%) |
| **الاختبارات** | 9 ملفات (~91% تغطية) |
| **الـ Endpoints** | 18 endpoint |
| **الوكلاء** | 13 وكيل (6 منفذين) |
| **الأدوات** | 5 أدوات حتمية |

---

## 💡 نصائح نهائية

### اقرأ بالترتيب
لا تقفز بين الملفات. كل ملف يبني على سابقه.

### طبق التمارين
في نهاية كل شرح يوجد تمرين صغير. حله قبل المتابعة.

### اقرأ الكود
بعد قراءة الشرح، افتح الملف واقرأه بنفسك.

### جرب التغييرات
بعد فهم ملف، جرب تغيير بسيط وشاهد ماذا يحدث.

### اسأل الأسئلة
إذا لم تفهم شيئاً، اطلب شرحاً إضافياً.

---

**🚀 ابدأ الآن:** اقرأ الملفات بالترتيب من 1 إلى 10

**📖 الفهرس الكامل:** [`06_top_10_files_index.md`](06_top_10_files_index.md)

**📚 دليل التوجيه:** [`docs/mentoring/`](docs/mentoring/)

---

## 🏗️ الإصدار v2 - ملخص المعمارية الجديدة

### نظرة سريعة على v2
الإصدار v2 يقدم **نظام تصريحي** (declarative) حيث كل شيء يُعرَّف في ملفات YAML:

| الجانب | v1 (Legacy) | v2 (Config-Backed) |
|--------|-------------|-------------------|
| **التكوين** | كود Python | ملفات YAML |
| **الـ Prompts** | strings في الكود | ملفات .txt منفصلة |
| **الوكلاء** | BaseAgent, BaseRAGAgent | CollectionAgent |
| **التوجيه** | core/router.py | application/routing/ |
| **الاسترجاع** | knowledge/ | retrieval/ |
| **التحقق** | في الوكلاء | verification/ طبقة منفصلة |

### المسارات الجديدة في v2

```
src/
├── agents/collection/     ← 10 وكلاء جدد (config-backed)
├── config/agents/         ← 10 ملفات YAML
├── prompts/               ← ملفات Prompts منفصلة
├── retrieval/            ← طبقة الاسترجاع
├── verification/         ← طبقة التحقق
├── application/routing/  ← التوجيه الجديد
├── infrastructure/qdrant/← عميل Qdrant
└── generation/           ← طبقة التوليد
```

### ابدأ مع v2
- [`02_folder_structure.md`](02_folder_structure.md) - المعمارية الكاملة
- [`V2_MIGRATION_NOTES.md`](../../8-development/refactoring/V2_MIGRATION_NOTES.md) - دليل الانتقال

---

**مُعد الملخص:** AI Mentor System  
**التاريخ:** أبريل 2026  
**الإصدار:** 1.0
