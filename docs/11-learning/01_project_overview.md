# 🕌 دليل الترحيب بمشروع Athar - الجزء الأول: نظرة عامة

## 1️⃣ ما هو مشروع Athar؟

**Athar** (أثر) هو **نظام إجابة على الأسئلة الإسلامية** (Islamic QA System) مبني على معمارية متعددة الوكلاء تسمى **Fanar-Sadiq**.

### 🎯 الهدف الرئيسي
الإجابة على الأسئلة الدينية الإسلامية بإجابات:
- **موثقة** (Grounded): كل إجابة مرتبطة بمصادر حقيقية (قرآن، حديث، فتاوى)
- **مقتبسة** (Citation-backed): كل جملة مدعومة بمرجع [C1], [C2], إلخ
- **دقيقة** (Accurate): استخدام حاسوبات حتمية للزكاة والمواريث
- **متعددة اللغات** (Arabic-first): يدعم العربية والإنجليزية

### 🔑 المميزات الأساسية

| الميزة | الوصف |
|--------|-------|
| **13 وكيل متخصص** (Agents) | فقه، حديث، قرآن، تفسير، عقيدة، سيرة، تاريخ، لغة عربية، أصول فقه، روحانيات، عام، ترحيب،_chatbot |
| **16 نوع نية** (Intents) + 4 فرعية للقرآن | تصنيف ذكي مع 10 مستويات أولوية |
| **5 أدوات حتمية** (Tools) | حاسبة الزكاة، حاسبة المواريث، أوقات الصلاة، التاريخ الهجري، الأدعية |
| **10 مجموعات متجهية** (Vector Collections) | 5.7 مليون وثيقة جاهزة للـ RAG |
| **11.3 مليون** وثيقة لوكين | مرحلة استخراج لوكين مكتملة |
| **42.6 GB** على HuggingFace | البيانات جاهزة للتضمين |
| **20 endpoint** | (جديد: `/classify` في المرحلة 8) |
| **مكتبة الشاملة** (ElShamela) | 8,425 كتاب من 3,146 عالم |
| **معمارية v2 Config-Backed** | نظام تصريحي بـ YAML + Prompts منفصلة |

---

## 2️⃣ خريطة المشروع عالية المستوى

```
Athar/
│
├── src/                          # الكود الأساسي (Python/FastAPI)
│   ├── api/                      # طبقة واجهة البرمجة (20 endpoint) ← جديد: /classify
│   ├── application/              # طبقة التطبيق (المرحلة 8) ← جديد!
│   │   ├── hybrid_classifier.py  ← مصنف النية الهجين
│   │   ├── router.py             ← توجيه الوكيل
│   │   └── interfaces.py         ← بروتوكولات
│   ├── domain/                   # تعريفات النطاق (المرحلة 8) ← جديد!
│   │   ├── intents.py            ← 16 نوع نية + أولويات
│   │   └── models.py             ← ClassificationResult
│   ├── config/                   # الإعدادات والثوابت
│   ├── core/                     # المنطق الأساسي (تصنيف، توجيه، اقتباسات)
│   ├── agents/                   # الوكلاء المتخصصون (13 وكيل)
│   │   ├── collection/           ← NEW! v2 10 وكلاء config-backed
│   │   │   ├── base.py          ← CollectionAgent الأساسي
│   │   │   └── [fiqh, hadith, tafsir, ...].py
│   │   └── legacy/               ← DEPRECATED!
│   ├── tools/                    # الأدوات الحتمية (5 أدوات)
│   ├── quran/                    # خط إنتاج القرآن (6 وحدات)
│   ├── knowledge/                # بنية الـ RAG (تضمين، متجهات، بحث)
│   ├── retrieval/                ← NEW! v2 طبقة الاسترجاع
│   ├── verification/             ← NEW! v2 طبقة التحقق
│   ├── generation/               ← NEW! v2 طبقة التوليد
│   ├── infrastructure/           # الخدمات الخارجية (DB, Redis, LLM)
│   │   └── qdrant/              ← NEW! v2 Qdrant client
│   └── data/                     # نماذج البيانات والتحميل
│
├── config/                       ← NEW! v2 ملفات التكوين
│   └── agents/                   # 10 ملفات YAML للوكلاء
│       ├── fiqh.yaml
│       ├── hadith.yaml
│       └── ... (10 وكلاء)
│
├── prompts/                      ← NEW! v2 ملفات الـ Prompts
│   ├── fiqh/
│   │   ├── system.txt
│   │   └── user.txt
│   ├── hadith/
│   └── ... (10 وكلاء)
│
├── data/                         # البيانات
│   ├── mini_dataset/             # مجموعة بيانات مصغرة (1.7 MB)
│   ├── processed/                # بيانات معالجة (61 GB)
│   └── seed/                     # بيانات البذور (أدعية، قرآن)
│
├── scripts/                      # 15 سكريبت مساعدة
├── tests/                        # 9 ملفات اختبار (~91% تغطية)
├── docs/                         # 23 دليل توثيق
├── notebooks/                    # دفاتر Colab للتضمين
│
├── docker/                       # Docker Compose (5 خدمات)
├── migrations/                   # تهجير قاعدة البيانات (Alembic)
│
└── ملفات التكوين
    ├── pyproject.toml            # التبعيات (Poetry)
    ├── .env.example              # 37 متغير بيئة
    ├── Makefile                  # 25 أمر بناء
    └── alembic.ini               # إعدادات Alembic
```

---

## 3️⃣ أهم 15 ملف/مجلد يجب فهمها أولاً (محدث!)

| الأولوية | الملف/المجلد | السبب |
|----------|-------------|-------|
| **1** | `src/api/main.py` | نقطة الدخول الرئيسية للتطبيق |
| **2** | `src/config/settings.py` | كل الإعدادات في مكان واحد |
| **3** | `src/application/hybrid_classifier.py` | **جديد!** مصنف النية الهجين (المرحلة 8) |
| **4** | `src/domain/intents.py` | **جديد!** 16 نوع نية مع 10 مستويات أولوية |
| **5** | `src/core/router.py` | منطق تصنيف النية (3-tier) |
| **6** | `src/core/orchestrator.py` | تنسيق الاستجابة بين الوكلاء |
| **7** | `src/agents/base.py` | الفئات الأساسية للوكلاء |
| **8** | `src/knowledge/embedding_model.py` | نموذج التضمين (BAAI/bge-m3) |
| **9** | `src/knowledge/vector_store.py` | Qdrant وإدارة المتجهات |
| **10** | `src/knowledge/hybrid_search.py` | البحث المختلط (دلالي + BM25) |
| **11** | `src/quran/nl2sql.py` | تحويل اللغة الطبيعية إلى SQL |
| **12** | `src/tools/zakat_calculator.py` | حاسبة الزكاة (منطق إسلامي دقيق) |
| **13** | `src/api/routes/classification.py` | **جديد!** نقطة نهاية /classify |
| **14** | `src/application/router.py` | **جديد!** توجيه الوكيل |
| **15** | `src/config/intents.py` | **محدث!** الأنماط القديمة (التوافق) |

---

## 4️⃣ كيف تقرأ المشروع بالترتيب الصحيح

### 📚 خطة القراءة المتدرجة

#### المرحلة 1: فهم البنية العامة (اليوم 1-2)
```
1. README.md              → نظرة عامة على المشروع
2. src/api/main.py        → كيف يبدأ التطبيق
3. src/config/settings.py → الإعدادات الأساسية
4. src/config/intents.py  → 16 نوع نية
5. src/config/constants.py → كل الثوابت والعتبات
```

#### المرحلة 2: فهم تصنيف الأسئلة (اليوم 3-4)
```
6. src/core/router.py     → HybridQueryClassifier (3-tier)
7. src/core/registry.py   → AgentRegistry
8. src/core/citation.py   → CitationNormalizer
```

#### المرحلة 3: فهم الوكلاء والأدوات (اليوم 5-7)
```
9.  src/agents/base.py    → BaseAgent, AgentInput, AgentOutput
10. src/agents/chatbot_agent.py      → أبسط وكيل (قوالب جاهزة)
11. src/agents/fiqh_agent.py         → وكيل RAG كامل
12. src/agents/base_rag_agent.py     → منطق RAG المشترك
13. src/tools/base.py                → BaseTool
14. src/tools/zakat_calculator.py    → مثال على أداة حتمية
```

#### المرحلة 4: فهم الـ RAG (اليوم 8-10)
```
15. src/knowledge/embedding_model.py     → BAAI/bge-m3 wrapper
16. src/knowledge/vector_store.py        → Qdrant integration
17. src/knowledge/hybrid_search.py       → Semantic + BM25 + RRF
18. src/knowledge/hierarchical_retriever.py → Book-level context
```

#### المرحلة 5: فهم خط إنتاج القرآن (اليوم 11-12)
```
19. src/quran/verse_retrieval.py    → Lookup by number/name
20. src/quran/nl2sql.py             → Natural language → SQL
21. src/quran/quotation_validator.py → Verify quotes
```

#### المرحلة 6: فهم البنية التحتية (اليوم 13-14)
```
22. src/infrastructure/database.py  → PostgreSQL (sync/async)
23. src/infrastructure/redis.py     → Redis caching
24. src/infrastructure/llm_client.py → Groq/OpenAI client
```

#### المرحلة 7: المرحلة 8 - مصنف النية الهجين (اليوم 15-16) ← جديد!
```
25. src/application/hybrid_classifier.py → مصنف النية الهجين
26. src/domain/intents.py               → 16 نوع نية + أولويات
27. src/application/router.py           → توجيه الوكيل
28. src/api/routes/classification.py    → نقطة /classify
```

---

## 5️⃣ الأجزاء المسؤولة عن AI/RAG/Backend/Config/Data Flow

### 🧠 الذكاء الاصطناعي (AI Components) - محدث!

```
src/application/hybrid_classifier.py   ← جديد! مصنف النية الهجين (Phase 8)
src/domain/intents.py                 ← جديد! 16 نوع نية + 10 أولويات + 4 فرعية قرآن
src/application/router.py             ← جديد! توجيه الوكيل
src/core/router.py                    ← تصنيف النية (Hybrid: keyword → LLM → embedding)
src/infrastructure/llm_client.py      ← التواصل مع Groq/OpenAI
src/agents/*_agent.py                 ← 13 وكيل متخصص
src/quran/nl2sql.py                   ← تحويل اللغة الطبيعية إلى SQL
```

### 🔍 نظام RAG (Retrieval-Augmented Generation)

```
src/knowledge/
├── embedding_model.py      → توليد المتجهات (BAAI/bge-m3)
├── embedding_cache.py      → Redis caching للمتجهات
├── vector_store.py         → Qdrant (10 مجموعات)
├── hybrid_search.py        → بحث دلالي + BM25
├── hierarchical_retriever.py → استرجاع على مستوى الكتاب
├── hadith_grader.py        → تقييم صحة الحديث
└── book_weighter.py        → وزن الكتب حسب الأهمية
```

### 🌐 الـ Backend - محدث!

```
src/api/
├── main.py                 → FastAPI factory
├── routes/
│   ├── classification.py   ← جديد! /classify endpoint
│   ├── query.py           → POST /api/v1/query (main)
│   ├── tools.py           → 5 tool endpoints
│   ├── quran.py           → 6 Quran endpoints
│   ├── rag.py             → 3 RAG endpoints
│   └── health.py          → Health checks
├── middleware/            → Security, CORS, rate limiting
└── schemas/               → Pydantic request/response models
```

### ⚙️ الإعدادات (Configuration)

```
src/config/
├── settings.py             → Pydantic BaseSettings (37 متغير)
├── intents.py              → 16 intent + keyword patterns
├── constants.py            → Retrieval, LLM, classification thresholds
└── logging_config.py       → Structured logging (structlog)
```

### 📊 تدفق البيانات (Data Flow) - محدث!

```
البيانات الخام (ElShamela 8,425 كتاب)
    ↓
scripts/ingestion/                  → تحميل البيانات
    ↓
src/knowledge/hierarchical_chunker.py → تقسيم المستندات
    ↓
11.3 مليون وثيقة لوكين (Phase 7 complete)
    ↓
5.7 مليون وثيقة محسنة (RAG ready)
    ↓
HuggingFace Upload (42.6 GB) ← مكتمل!
    ↓
Colab GPU Embedding (BAAI/bge-m3) ←_pending
    ↓
Qdrant Import (10 collections, 5.7M vectors)
```

---

## 6️⃣ المعمارية العامة (Architecture Overview) - محدثة!

### نموذج الطبقات الخمس (المرحلة 8)

```
┌─────────────────────────────────────────────────────────┐
│              طبقة الـ API (FastAPI)                       │
│  POST /classify  •  POST /api/v1/query  •  20 endpoint  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│            طبقة التطبيق (Application Layer) - جديد!      │
│  HybridIntentClassifier  •  RouterAgent                 │
│  ├── Keyword fast-path (100+ patterns)                │
│  ├── Jaccard similarity fallback                      │
│  └── Quran sub-intent detection (4 types)              │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              طبقة التنسيق (Orchestration)               │
│  Hybrid Intent Classifier (LLM)  •  Response Orchestrator│
│  Citation Normalizer  •  Agent Registry                 │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│          طبقة الوكلاء والأدوات (13 + 5)                  │
│  ┌──────────┬──────────┬──────────┬──────────────┐      │
│  │ FiqhAgent│QuranAgent│ Zakat    │ Inheritance  │      │
│  │ (RAG)    │(NL2SQL)  │ Calc     │ Calc         │      │
│  └──────────┴──────────┴──────────┴──────────────┘      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              طببة المعرفة (Knowledge)                   │
│  PostgreSQL (Quran)  •  Qdrant (10 collections)         │
│  Redis (Cache)  •  LLM (Groq Qwen3-32B)                 │
│  BAAI/bge-m3 (1024-dim, 8192 tokens)                    │
└─────────────────────────────────────────────────────────┘
```

### تدفق الاستعلام الرئيسي

```
مستخدم يسأل: "ما حكم صلاة العيد؟"
    ↓
POST /api/v1/query {"query": "ما حكم صلاة العيد؟"}
    ↓
HybridQueryClassifier.classify()
    ├─ Tier 1: Keyword matching ("صلاة", "العيد") → fiqh (0.92)
    └─ ✅ Keyword match found!
    ↓
AgentRegistry.get_for_intent("fiqh") → FiqhAgent
    ↓
FiqhAgent.execute()
    ├─ VectorStore.search() → Qdrant (fiqh_passages collection)
    ├─ HybridSearcher.search() → Top 15 passages
    ├─ HierarchicalRetriever.group_by_book()
    ├─ Prompt assembly: "بناءً على المصادر الفقهية..."
    ├─ LLM.generate() → Groq Qwen3-32B
    └─ CitationNormalizer.enrich() → [C1], [C2], [C3]
    ↓
QueryResponse {
    "answer": "صلاة العيد سنة مؤكدة...",
    "citations": [...],
    "confidence": 0.89
}
```

---

## 7️⃣ الخلاصة العملية (محدثة!)

### ما الذي يجب أن تفهمه فعلاً من هذا الجزء؟

1. **Athar هو نظام إجابة إسلامي** يستخدم معمارية متعددة الوكلاء
2. **5 مكونات أساسية**: تطبيق (هجين) → تصنيف → توجيه → وكيل → إجابة مقتبسة
3. **20 endpoint** تغطي كل الوظائف (جديد: `/classify` في المرحلة 8)
4. **5.7 مليون وثيقة** + 11.3M لوكين على HuggingFace
5. **16 نوع نية + 4 فرعية للقرآن** مع **10 مستويات أولوية** (المرحلة 8)
6. **<50ms** لتصنيف النية باستخدام مصنف النية الهجين

### 🎉 المرحلة 8: مصنف النية الهجين (15 أبريل 2026)

```
# جرب الآن!
POST /classify
{"query": "ما حكم صلاة الجمعة؟"}

# النتيجة (<50ms)
{
  "intent": "fiqh",
  "confidence": 0.90,
  "method": "keyword"
}
```

### 📝 تمرين صغير

افتح ملف `src/domain/intents.py` وأجب:
1. ما هي الـ 16 intent؟
2. ما هي مستويات الأولوية (1-10)؟
3. ما هي النيات الفرعية للقرآن؟

### 🔜 الخطوة التالية المنطقية

اقرأ الملف: `src/application/hybrid_classifier.py` (جديد في المرحلة 8)

---

**📖 الملف التالي في السلسلة:** الجزء الثاني - نقطة الدخول (`src/api/main.py`)
