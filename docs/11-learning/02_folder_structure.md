# 📂 دليل المجلدات - الجزء الثاني: شرح كل مجلد

## 🗂️ المجلد الرئيسي: `src/`

### نظرة عامة

```
src/
├── api/              # طبقة واجهة البرمجة (REST endpoints)
├── config/           # الإعدادات والثوابت
├── core/             # المنطق الأساسي (تصنيف، توجيه، اقتباسات)
├── agents/           # الوكلاء المتخصصون (13 وكيل)
├── tools/            # الأدوات الحتمية (5 أدوات)
├── quran/            # خط إنتاج القرآن (6 وحدات)
├── knowledge/        # بنية الـ RAG (تضمين، متجهات، بحث)
├── infrastructure/   # الخدمات الخارجية (DB, Redis, LLM)
└── data/             # نماذج البيانات والتحميل
```

---

## 1️⃣ مجلد `src/api/` - طبقة واجهة البرمجة

### 📍 الوظيفة
هذا المجلد يحتوي على **جميع نقاط الدخول** (endpoints) للتطبيق. هو أول ما يستقبل الطلب من المستخدم.

### 📁 الملفات

```
api/
├── main.py                     # نقطة الدخول الرئيسية (FastAPI factory)
├── routes/
│   ├── query.py                # POST /api/v1/query (الendpoint الرئيسي)
│   ├── tools.py                # POST /api/v1/tools/{zakat, inheritance, ...}
│   ├── quran.py                # GET/POST /api/v1/quran/* (6 endpoints)
│   ├── rag.py                  # POST /api/v1/rag/{fiqh, general, stats}
│   └── health.py               # GET /health, /ready
├── middleware/
│   ├── security.py             # Rate limiting, API key, CORS, sanitization
│   └── error_handler.py        # Global exception handling
└── schemas/
    ├── request.py              # Pydantic models للطلبات
    └── response.py             # Pydantic models للاستجابات
```

### 🔄 كيف يتدفق البيانات هنا

```
طلب HTTP من المستخدم
    ↓
main.py (FastAPI app)
    ↓
middleware/security.py (فحص الأمان)
    ↓
routes/query.py (استلام الطلب)
    ↓
schemas/request.py (التحقق من صحة البيانات)
    ↓
... (إرسال إلى core/orchestrator)
    ↓
schemas/response.py (تنسيق الاستجابة)
    ↓
middleware/error_handler.py (معالجة الأخطاء)
    ↓
استجابة HTTP للمستخدم
```

### 🎯 نمط التصميم المستخدم
- **Factory Pattern**: `create_app()` ينشئ التطبيق
- **Middleware Pattern**: طبقات متتالية للمعالجة
- **Schema Validation**: Pydantic models للتحقق

---

## 2️⃣ مجلد `src/config/` - الإعدادات

### 📍 الوظيفة
**كل الإعدادات والثوابت** في مكان واحد. لا توجد hardcoded values في الكود.

### 📁 الملفات

```
config/
├── settings.py                 # Pydantic BaseSettings (37 متغير بيئة)
├── intents.py                  # 16 intent + keyword patterns
├── constants.py                # Retrieval, LLM, classification thresholds
└── logging_config.py           # Structured logging (structlog)
```

### 🔑 `settings.py` - أهم المتغيرات

| المتغير | القيمة الافتراضية | الوصف |
|---------|------------------|-------|
| `llm_provider` | `groq` | مزود الـ LLM |
| `groq_model` | `qwen/qwen3-32b` | نموذج Groq |
| `embedding_model` | `BAAI/bge-m3` | نموذج التضمين |
| `database_url` | `postgresql+asyncpg://...` | رابط قاعدة البيانات |
| `redis_url` | `redis://localhost:6379/0` | رابط Redis |
| `qdrant_url` | `http://localhost:6333` | رابط Qdrant |

### 🎯 `intents.py` - 16 نوع نية

```python
INTENT_ROUTING = {
    "fiqh": "fiqh_agent",
    "quran": "quran_pipeline",
    "islamic_knowledge": "general_islamic_agent",
    "greeting": "chatbot_agent",
    "zakat": "zakat_tool",
    "inheritance": "inheritance_tool",
    "dua": "dua_tool",
    "hijri_calendar": "hijri_tool",
    "prayer_times": "prayer_times_tool",
    "hadith": "hadith_agent",
    "tafsir": "tafsir_agent",
    "aqeedah": "aqeedah_agent",
    "seerah": "seerah_agent",
    "usul_fiqh": "usul_fiqh_agent",
    "islamic_history": "islamic_history_agent",
    "arabic_language": "arabic_language_agent",
}
```

### ⚙️ `constants.py` - الثوابت المهمة

| الفئة | الثابت | القيمة | الوصف |
|-------|--------|--------|-------|
| Retrieval | `TOP_K_FIQH` | 15 | عدد الوثائق المسترجعة للفتاوى |
| Retrieval | `SEMANTIC_THRESHOLD` | 0.15 | عتبة التشابه الدلالي |
| LLM | `TEMPERATURE_FIQH` | 0.1 | حرارة LLM للفتاوى (منخفضة للدقة) |
| Zakat | `GOLD_NISAB_GRAMS` | 85 | نصاب الذهب بالجرام |
| Zakat | `SILVER_NISAB_GRAMS` | 595 | نصاب الفضة بالجرام |

---

## 3️⃣ مجلد `src/core/` - المنطق الأساسي

### 📍 الوظيفة
هنا يوجد **العقل المدبر** للنظام: تصنيف الأسئلة، توجيهها، وتطبيع الاقتباسات.

### 📁 الملفات

```
core/
├── router.py                   # HybridQueryClassifier (3-tier)
├── registry.py                 # AgentRegistry
└── citation.py                 # CitationNormalizer
```

### 🧠 `router.py` - تصنيف النية (3-tier)

```
Tier 1: Keyword Matching (0.92 confidence)
    ↓ (إذا فشل)
Tier 2: LLM Classification (0.75 confidence)
    ↓ (إذا فشل)
Tier 3: Embedding Similarity (0.60 confidence)
```

**لماذا 3 tiers؟**
- **Tier 1**: سريع جداً (مقارنة كلمات)
- **Tier 2**: دقيق لكن مكلف (يحتاج LLM call)
- **Tier 3**: fallback أخير

### 📋 `registry.py` - تسجيل الوكلاء

```python
registry = AgentRegistry()
registry.register("fiqh_agent", FiqhAgent())
registry.register("zakat_tool", ZakatCalculator())
# ...

def get_for_intent(intent: str) -> BaseAgent:
    return registry.get(intent)
```

### 🔗 `citation.py` - تطبيع الاقتباسات

يحول المراجع النصية إلى أرقام مقتبسة:
```
"قال ابن تيمية في مجموع الفتاوى..." → [C1]
"رواه البخاري في صحيحه..." → [C2]
```

---

## 4️⃣ مجلد `src/agents/` - الوكلاء المتخصصون

### 📍 الوظيفة
**13 وكيل** كل واحد متخصص في مجال معين. كل وكيل يعرف كيف:
1. يسترجع الوثائق المناسبة
2. يولد الإجابة
3. يضيف الاقتباسات

### 📁 الملفات

```
agents/
├── base.py                     # BaseAgent, AgentInput, AgentOutput
├── base_rag_agent.py           # BaseRAGAgent (منطق RAG مشترك)
├── chatbot_agent.py            # للترحيب والتحيات
├── fiqh_agent.py               # للفتاوى والأحكام
├── hadith_agent.py             # للأحاديث
├── general_islamic_agent.py    # للمعارف الإسلامية العامة
├── seerah_agent.py             # للسيرة النبوية
└── (_agents محذوفة)            # fallback إلى general_islamic_agent
```

### 🏗️ التسلسل الهرمي

```
BaseAgent (abstract)
    ├── ChatbotAgent (template-based)
    ├── FiqhAgent (standalone RAG)
    ├── HadithAgent (standalone RAG)
    ├── GeneralIslamicAgent (standalone RAG)
    └── BaseRAGAgent (shared RAG logic)
        └── SeerahAgent
```

### 🎯 لماذا بعض الوكلاء standalone والبعض يرث BaseRAGAgent؟

**الوكلاء المستقلة** (Fiqh, Hadith, General):
- كُتبت أولاً، كل واحد بنى راج خاص به
- تحتوي على تكرار في الكود

**BaseRAGAgent**:
- محاولة لاحقاً لتقليل التكرار
- فقط SeerahAgent يستخدمه حالياً

---

## 5️⃣ مجلد `src/tools/` - الأدوات الحتمية

### 📍 الوظيفة
**5 أدوات حتمية** (deterministic) تعطي نتائج دقيقة بدون LLM.

### 📁 الملفات

```
tools/
├── base.py                     # BaseTool, ToolInput, ToolOutput
├── zakat_calculator.py         # حاسبة الزكاة
├── inheritance_calculator.py   # حاسبة المواريث
├── prayer_times_tool.py        # أوقات الصلاة
├── hijri_calendar_tool.py      # التاريخ الهجري
└── dua_retrieval_tool.py       # الأدعية والأذكار
```

### 🔑 الفرق بين Agent و Tool

| Agent | Tool |
|-------|------|
| يستخدم LLM لتوليد إجابة | خوارزمية حتمية بدون LLM |
| إجابة قد تختلف | إجابة دائماً نفسها |
| يحتاج RAG (vector search) | يحتاج معادلات رياضية |
| مثال: FiqhAgent | مثال: ZakatCalculator |

### 📊 `zakat_calculator.py` - مثال

```python
def calculate_zakat(assets, liabilities, nisab_type="gold"):
    net_wealth = assets - liabilities
    nisab = get_nisab(nisab_type)  # 85g gold or 595g silver
    
    if net_wealth >= nisab:
        return net_wealth * 0.025  # 2.5%
    else:
        return 0
```

---

## 6️⃣ مجلد `src/quran/` - خط إنتاج القرآن

### 📍 الوظيفة
كل ما يتعلق **بالقرآن الكريم**: البحث، التفسير، التحقق من الآيات، التحليلات.

### 📁 الملفات

```
quran/
├── quran_router.py             # تصنيف النيات الفرعية (4 أنواع)
├── verse_retrieval.py          # البحث عن الآيات
├── nl2sql.py                   # Natural Language → SQL
├── quotation_validator.py      # التحقق من اقتباسات القرآن
├── tafsir_retrieval.py         # جلب التفاسير
└── named_verses.json           # الآيات المسماة (الكرسي، الفاتحة، إلخ)
```

### 🎯 النيات الفرعية للقرآن

```python
QuranSubIntent = {
    "VERSE_LOOKUP": "ما هي الآية رقم 255 من البقرة؟",
    "INTERPRETATION": "ما تفسير هذه الآية؟",
    "ANALYTICS": "كم مرة ذكرت كلمة الرحمة في القرآن؟",
    "QUOTATION_VALIDATION": "هل هذا الاقتباس من القرآن صحيح؟"
}
```

### 🔍 `nl2sql.py` - تحويل اللغة إلى SQL

```
"كم مرة ذكرت كلمة الرحمة؟"
    ↓
NL2SQLEngine.generate_sql()
    ↓
SELECT COUNT(*) FROM quran_verses WHERE text LIKE '%الرحمة%'
    ↓
127 مرة
```

---

## 7️⃣ مجلد `src/knowledge/` - بنية الـ RAG

### 📍 الوظيفة
**كل ما يتعلق بالـ RAG**: التضمين، المتجهات، البحث، الاسترجاع.

### 📁 الملفات

```
knowledge/
├── embedding_model.py          # BAAI/bge-m3 wrapper
├── embedding_cache.py          # Redis caching للمتجهات
├── vector_store.py             # Qdrant integration
├── hybrid_search.py            # Semantic + BM25 + RRF
├── hierarchical_retriever.py   # Book-level retrieval
├── hierarchical_chunker.py     # Document chunking
├── title_loader.py             # Title/chapter metadata
├── hadith_grader.py            # Hadith authenticity grading
└── book_weighter.py            # Book importance scoring
```

### 🔄 تدفق الـ RAG

```
مستند جديد (كتاب فقه)
    ↓
hierarchical_chunker.py         → تقسيم إلى فقرات
    ↓
embedding_model.py              → توليد متجه 1024-dim
    ↓
embedding_cache.py              → حفظ في Redis
    ↓
vector_store.py                 → استيراد إلى Qdrant
    ↓
5.7 مليون متجه في 10 مجموعات
```

### 🔍 `hybrid_search.py` - البحث المختلط

```
سؤال: "ما حكم صلاة العيد؟"
    ↓
Semantic Search (BAAI/bge-m3)
    ├─ يجد الوثائق المتشابهة دلالياً
    └─ Score: 0.85, 0.78, 0.72, ...
    ↓
BM25 Search (keyword matching)
    ├─ يجد الوثائق التي تحتوي الكلمات
    └─ Score: 0.90, 0.82, 0.75, ...
    ↓
Reciprocal Rank Fusion (k=60)
    ├─ يدمج النتيجتين
    └─ Final Score: 0.88, 0.80, 0.74, ...
    ↓
Top 15 وثيقة
```

---

## 8️⃣ مجلد `src/infrastructure/` - الخدمات الخارجية

### 📍 الوظيفة
التواصل مع **الخدمات الخارجية**: قاعدة البيانات، Redis، LLM.

### 📁 الملفات

```
infrastructure/
├── database.py                 # PostgreSQL (sync + async)
├── redis.py                    # Redis async client
├── llm_client.py               # Groq/OpenAI client
└── db_sync.py                  # Sync DB dependency
```

### 🗄️ `database.py` - قاعدة البيانات

```python
# Sync (للمهاجرين والعمليات البسيطة)
def get_sync_session():
    return SessionLocal()

# Async (لـ FastAPI endpoints)
async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session
```

### 🤖 `llm_client.py` - التواصل مع LLM

```python
async def generate_text(prompt: str, temperature: float = 0.1):
    if settings.llm_provider == "groq":
        return await groq_client.generate(prompt, temperature)
    else:
        return await openai_client.generate(prompt, temperature)
```

---

## 9️⃣ مجلد `src/data/` - نماذج البيانات

### 📍 الوظيفة
**نماذج SQLAlchemy** و**سكريبتات تحميل البيانات**.

### 📁 الملفات

```
data/
├── models/
│   └── quran_models.py         # SQLAlchemy models للقرآن
└── ingestion/
    └── data_loaders.py         # سكريبتات تحميل البيانات
```

---

## 🔟 مجلد `data/` - البيانات

### 📍 الوظيفة
تخزين **البيانات الخام والمعالجة**.

### 📁 الملفات

```
data/
├── mini_dataset/               # مجموعة بيانات مصغرة (1.7 MB)
│   ├── fiqh_passages.jsonl     # 347 وثيقة
│   ├── hadith_passages.jsonl   # 126 وثيقة
│   └── ...
├── processed/                  # بيانات معالجة (61 GB)
│   ├── master_catalog.json     # 8,425 كتاب
│   ├── category_mapping.json   # 40 → 10 فئات
│   ├── author_catalog.json     # 3,146 عالم
│   └── lucene_pages/           # 5.7 مليون وثيقة
└── seed/                       # بيانات البذور
    ├── duas.json               # الأدعية
    └── quran_samples.json      # عينات القرآن
```

---

## 1️⃣1️⃣ مجلد `scripts/` - السكريبتات المساعدة

### 📍 الوظيفة
**15 سكريبت** للمهام المختلفة: تحميل، معالجة، اختبار.

### 📁 الملفات

```
scripts/
├── lucene/                     # سكريبتات استخراج Lucene
├── ingestion/                  # سكريبتات تحميل البيانات
├── data/                       # سكريبتات تحليل البيانات
├── tests/                      # سكريبتات اختبار
├── backup_embeddings_and_qdrant.py
├── restore_from_huggingface.py
├── download_embeddings_and_upload_qdrant.py
└── cli.py                      # واجهة سطر الأوامر
```

---

## 1️⃣2️⃣ مجلد `tests/` - الاختبارات

### 📍 الوظيفة
**9 ملفات اختبار** مع ~91% تغطية.

### 📁 الملفات

```
tests/
├── conftest.py                 # Pytest fixtures
├── test_router.py              # اختبار تصنيف النية
├── test_api.py                 # اختبار الـ endpoints
├── test_zakat_calculator.py    # اختبار حاسبة الزكاة
├── test_inheritance_calculator.py
├── test_prayer_times_tool.py
├── test_hijri_calendar_tool.py
├── test_dua_retrieval_tool.py
└── test_quran_pipeline.py
```

---

## 1️⃣3️⃣ مجلد `docs/` - التوثيق

### 📍 الوظيفة
**23 دليل** يغطي كل جوانب المشروع.

### 📁 الملفات

```
docs/
├── getting-started/            # دليل البداية
├── architecture/               # المعمارية
├── api/                        # توثيق الـ API
├── core-features/              # الميزات الأساسية
├── data/                       # توثيق البيانات
├── deployment/                 # دليل النشر
├── development/                # دليل التطوير
├── guides/                     # أدلة الاستخدام
├── improvements/               # مقترحات التحسين
├── planning/                   # تخطيط المشروع
├── reference/                  # مراجع
├── reports/                    # تقارير
├── status/                     # تحديثات الحالة
└── mentoring/                  # دليل التوجيه (هذا المجلد!)
```

---

## 1️⃣4️⃣ مجلد `notebooks/` - دفاتر Colab

### 📍 الوظيفة
**دفاتر Jupyter** لتوليد المتجهات على Colab GPU.

### 📁 الملفات

```
notebooks/
├── 02_upload_and_embed.ipynb   # رفع وتضمين على GPU
├── verify_upload.ipynb         # التحقق من الرفع
└── archive/                    # دفاتر مؤرشفة
    └── 05_upload_to_kaggle.ipynb
```

---

## 1️⃣5️⃣ مجلد `docker/` - Docker Compose

### 📍 الوظيفة
**5 خدمات** تعمل بـ Docker.

### 📁 الملفات

```
docker/
└── docker-compose.dev.yml      # PostgreSQL, Qdrant, Redis, API, Frontend
```

### 🐳 الخدمات الخمس

| الخدمة | المنفذ | الوصف |
|--------|--------|-------|
| PostgreSQL | 5432 | قاعدة البيانات |
| Qdrant | 6333 | قاعدة المتجهات |
| Redis | 6379 | التخزين المؤقت |
| API | 8000 | تطبيق FastAPI |
| Frontend | 3000 | تطبيق Next.js (اختياري) |

---

## 📊 ملخص المجلدات

| المجلد | الملفات | الوظيفة الرئيسية |
|--------|---------|-----------------|
| `api/` | 8 | REST endpoints (18) |
| `config/` | 4 | الإعدادات والثوابت |
| `core/` | 3 | تصنيف، توجيه، اقتباسات |
| `agents/` | 9 | 13 وكيل متخصص |
| `tools/` | 6 | 5 أدوات حتمية |
| `quran/` | 6 | خط إنتاج القرآن |
| `knowledge/` | 9 | بنية الـ RAG |
| `infrastructure/` | 4 | DB, Redis, LLM |
| `data/` (src) | 2 | نماذج البيانات |
| `data/` (root) | 3 مجلدات | البيانات الخام |
| `scripts/` | 15 | سكريبتات مساعدة |
| `tests/` | 9 | اختبارات (~91%) |
| `docs/` | 23 مجلد | توثيق شامل |

---

## 🏗️ المعمارية الجديدة v2 - Era of Config-Backed Systems

### نظرة عامة
مع الإصدار v2، انتقلنا من **الكود الصلب** (hardcoded) إلى **النظام التصريحي** (declarative). كل شيء الآن يُعرَّف في ملفات YAML والت prompts.

### المجلدات الجديدة

```
src/
├── agents/
│   ├── collection/           ← NEW! 10 وكلاء بمعمارية CollectionAgent
│   │   ├── base.py            # CollectionAgent الأساسي
│   │   ├── fiqh.py            # وكيل الفقه (config-backed)
│   │   ├── hadith.py          # وكيل الحديث
│   │   ├── tafsir.py          # وكيل التفسير
│   │   ├── aqeedah.py         # وكيل العقيدة
│   │   ├── seerah.py          # وكيل السيرة
│   │   ├── usul_fiqh.py       # وكيل أصول الفقه
│   │   ├── history.py         # وكيل التاريخ
│   │   ├── language.py        # وكيل اللغة العربية
│   │   ├── tazkiyah.py        # وكيل التربية الروحية
│   │   └── general.py         # وكيل العام
│   └── legacy/                ← DEPRECATED! الوكلاء القدامى
│
├── retrieval/                 ← NEW! طبقة الاسترجاع
│   ├── schemas.py             # مخططات الاسترجاع
│   ├── filters/               # فلاتر الاسترجاع
│   ├── fusion/                # دمج النتائج (RRF)
│   └── mapping/               # خرائط الاسترجاع
│
├── verification/              ← NEW! طبقة التحقق
│   ├── schemas.py             # مخططات التحقق
│   ├── trace.py               # تتبع التحقق
│   └── checks/                # فحوصات التحقق
│
├── application/               ← NEW! طبقة التطبيق
│   └── routing/
│       ├── intent_router.py   # توجيه النيات
│       ├── planner.py         # مخطط الاستجابة
│       └── executor.py        # منفذ الاستجابة
│
├── infrastructure/
│   └── qdrant/               ← NEW! طبقة Qdrant
│       ├── client.py         # عميل Qdrant
│       ├── collections.py    # إدارة المجموعات
│       └── payload_indexes.py # فهارس البيانات
│
└── generation/               ← NEW! طبقة التوليد
    ├── schemas.py            # مخططات التوليد
    └── prompt_loader.py     # محمل الـ Prompts
```

### ملفات التكوين

```
config/
└── agents/
    ├── fiqh.yaml            # تكوين وكيل الفقه
    ├── hadith.yaml          # تكوين وكيل الحديث
    ├── tafsir.yaml          # تكوين وكيل التفسير
    ├── aqeedah.yaml         # تكوين وكيل العقيدة
    ├── seerah.yaml          # تكوين وكيل السيرة
    ├── usul_fiqh.yaml       # تكوين وكيل أصول الفقه
    ├── history.yaml         # تكوين وكيل التاريخ
    ├── language.yaml        # تكوين وكيل اللغة
    ├── tazkiyah.yaml        # تكوين وكيل التربية
    └── general.yaml         # تكوين وكيل العام
```

### ملفات الـ Prompts

```
prompts/
├── fiqh/
│   ├── system.txt           # prompt النظام
│   └── user.txt             # prompt المستخدم
├── hadith/
├── tafsir/
├── ... (10 وكلاء)
└── common/
    └── verification.txt     # prompt التحقق
```

### الفرق بين v1 و v2

| الجانب | v1 (Legacy) | v2 (Config-Backed) |
|--------|-------------|-------------------|
| **التكوين** | كود صلب في Python | ملفات YAML |
| **الـ Prompts** | strings في الكود | ملفات .txt منفصلة |
| **الوكلاء** | BaseAgent, BaseRAGAgent | CollectionAgent |
| **الاسترجاع** | knowledge/ | retrieval/ |
| **التحقق** | مضمن في الوكلاء | طبقة منفصلة verification/ |
| **التوجيه** | core/router.py | application/routing/ |
| **التوليد** | في الوكلاء | generation/ طبقة منفصلة |

### لماذا v2؟

1. **فصل الاهتمامات**: التكوين منفصل عن الكود
2. **الصيانة**: تغيير الـ prompts لا يتطلب إعادة نشر الكود
3. **المرونة**: إضافة وكيل جديد مجرد إضافة ملف YAML
4. **الاختبار**: يمكن اختبار التكوينات بدون كود
5. **التوثيق**: الـ prompts تصبح التوثيق نفسه

---

## 🎯 الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً من هذا الجزء؟

1. **كل مجلد له مسؤولية واحدة** (Single Responsibility)
2. **التدفق**: API → Core → Agent/Tool → Knowledge → Infrastructure
3. **RAG موجود في `knowledge/`** وليس في `agents/`
4. **الإعدادات في `config/`** ولا توجد hardcoded values
5. **الوكلاء في `agents/`** والأدوات الحتمية في `tools/`

### 📝 تمرين صغير

افتح المجلد `src/agents/` وأجب:
1. كم ملف موجود؟
2. ما الفرق بين `base.py` و `base_rag_agent.py`؟
3. لماذا بعض الوكلاء standalone والبعض يرث BaseRAGAgent؟

### 🔜 الخطوة التالية المنطقية

اقرأ الملف التالي: `src/api/main.py` (نقطة الدخول الرئيسية)

---

**📖 الملف التالي في السلسلة:** الجزء الثالث - نقطة الدخول (`src/api/main.py`)
