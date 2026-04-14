# ⚡ ملخص سريع - Athar Islamic QA System

## 🕌 ما هو Athar؟

نظام إجابة على الأسئلة الإسلامية يستخدم:
- **13 وكيل متخصص** (Agents)
- **5 أدوات حتمية** (Tools)
- **16 نوع نية** (Intents)
- **10 مجموعات متجهية** (Vector Collections)
- **5.7 مليون وثيقة** جاهزة للـ RAG

---

## 🗺️ خريطة سريعة

```
src/
├── api/              → 18 endpoint (FastAPI)
├── config/           → إعدادات، intents، ثوابت
├── core/             → تصنيف النية، توجيه، اقتباسات
├── agents/           → 13 وكيل (6 منفذين)
├── tools/            → 5 أدوات حتمية
├── quran/            → خط إنتاج القرآن
├── knowledge/        → بنية الـ RAG
├── infrastructure/   → DB, Redis, LLM
└── data/             → نماذج البيانات
```

---

## 🔑 أهم 10 ملفات

| الأولوية | الملف | الوصف |
|----------|-------|-------|
| 1 | `src/api/main.py` | نقطة الدخول |
| 2 | `src/config/settings.py` | الإعدادات (37 متغير) |
| 3 | `src/config/intents.py` | 16 نوع نية |
| 4 | `src/core/router.py` | تصنيف النية (3-tier) |
| 5 | `src/agents/base.py` | الفئات الأساسية |
| 6 | `src/agents/fiqh_agent.py` | وكيل RAG كامل |
| 7 | `src/knowledge/embedding_model.py` | BAAI/bge-m3 |
| 8 | `src/knowledge/vector_store.py` | Qdrant |
| 9 | `src/knowledge/hybrid_search.py` | Semantic + BM25 |
| 10 | `src/quran/nl2sql.py` | لغة طبيعية → SQL |

---

## 🔄 تدفق الاستعلام

```
مستخدم يسأل: "ما حكم صلاة العيد؟"
    ↓
POST /api/v1/query {"query": "..."}
    ↓
HybridQueryClassifier (3-tier)
    ├─ Tier 1: Keyword (0.92) ← سريع
    ├─ Tier 2: LLM (0.75)     ← دقيق
    └─ Tier 3: Embedding (0.60) ← fallback
    ↓
Intent: fiqh → FiqhAgent
    ↓
RAG Pipeline:
    ├─ Qdrant.search() → Top 15 passages
    ├─ HybridSearch (semantic + BM25)
    ├─ HierarchicalRetriever (book-level)
    └─ Prompt assembly + LLM.generate()
    ↓
CitationNormalizer → [C1], [C2], [C3]
    ↓
QueryResponse {
    "answer": "صلاة العيد سنة مؤكدة...",
    "citations": [...],
    "confidence": 0.89
}
```

---

## 📊 16 Intent

| Intent | Agent/Tool | مثال |
|--------|-----------|------|
| fiqh | fiqh_agent | "ما حكم صلاة العيد؟" |
| quran | quran_pipeline | "ما تفسير آية الكرسي؟" |
| islamic_knowledge | general_islamic_agent | "ما فضل الصيام؟" |
| greeting | chatbot_agent | "السلام عليكم" |
| zakat | zakat_tool | "كيف أحسب الزكاة؟" |
| inheritance | inheritance_tool | "كيف أقسم الميراث؟" |
| dua | dua_tool | "دعاء السفر" |
| hijri_calendar | hijri_tool | "متى يبدأ رمضان؟" |
| prayer_times | prayer_times_tool | "متى صلاة الفجر؟" |
| hadith | hadith_agent | "ما حكم الحديث هذا؟" |
| tafsir | tafsir_agent | "ما تفسير هذه الآية؟" |
| aqeedah | aqeedah_agent | "ما معنى التوحيد؟" |
| seerah | seerah_agent | "متى ولد النبي؟" |
| usul_fiqh | usul_fiqh_agent | "ما هي مصادر التشريع؟" |
| islamic_history | islamic_history_agent | "متى كانت غزوة بدر؟" |
| arabic_language | arabic_language_agent | "ما معنى هذه الكلمة؟" |

---

## 🛠️ 5 أدوات حتمية

| الأداة | الوظيفة | ميزات |
|--------|---------|-------|
| ZakatCalculator | حساب الزكاة | ذهب، فضة، عروض، ماشية، زروع |
| InheritanceCalculator | تقسيم الميراث | فروض، تعصيب، عول، رد |
| PrayerTimesTool | أوقات الصلاة | 6 طرق، اتجاه القبلة |
| HijriCalendarTool | التاريخ الهجري | Umm al-Qura، تواريخ خاصة |
| DuaRetrievalTool | الأدعية | Hisn al-Muslim، Azkar-DB |

---

## 🧠 تقنيات AI/RAG

### Embedding Model
- **النموذج**: BAAI/bge-m3
- **الأبعاد**: 1024
- **الرموز**: 8192 token
- **الجهاز**: CPU (يدعم CUDA)

### Vector Database
- **النظام**: Qdrant
- **المجموعات**: 10
- **المتجهات**: 5.7 مليون
- **الفهرسة**: HNSW
- **المسافة**: Cosine

### Hybrid Search
- **البحث 1**: Semantic (BAAI/bge-m3)
- **البحث 2**: BM25 (keyword matching)
- **الدمج**: Reciprocal Rank Fusion (k=60)

### Retrieval
- **Hierarchical**: على مستوى الكتاب
- **Faceted**: تصفية حسب المؤلف، العصر، الكتاب
- **Weighted**: وزن الكتب حسب الأهمية
- **Graded**: تقييم صحة الحديث

---

## 📈 إحصائيات سريعة

| المقياس | القيمة |
|---------|--------|
| الأسطر البرمجية | ~14,200 |
| الملفات | ~120 |
| الاختبارات | 9 ملفات (~91% تغطية) |
| الـ endpoints | 18 |
| الوكلاء | 13 (6 منفذين) |
| الأدوات | 5 |
| المتجهات | 5.7 مليون |
| المستندات | 8,425 كتاب |
| العلماء | 3,146 عالم |
| دقة التصنيف | ~90% |
| سرعة الاستجابة (RAG) | ~257ms |
| سرعة الاستجابة (تحية) | <100ms |

---

## 🚀 أوامر سريعة

```bash
# تثبيت
make install-dev

# تشغيل الخدمات
make docker-up

# تشغيل المهاجرين
make db-migrate

# تشغيل التطبيق
make dev

# الاختبارات
make test

# التوثيق
make lint

# التنسيق
make format

# تنظيف
make clean
```

---

## 🌐 Endpoints رئيسية

| Endpoint | Method | الوصف |
|----------|--------|-------|
| `/api/v1/query` | POST | السؤال الرئيسي |
| `/api/v1/tools/zakat` | POST | حساب الزكاة |
| `/api/v1/tools/inheritance` | POST | تقسيم الميراث |
| `/api/v1/tools/prayer-times` | POST | أوقات الصلاة |
| `/api/v1/tools/hijri` | POST | التاريخ الهجري |
| `/api/v1/tools/duas` | POST | الأدعية |
| `/api/v1/quran/surahs` | GET | قائمة السور |
| `/api/v1/quran/ayah/{s}:{a}` | GET | آية محددة |
| `/api/v1/quran/search` | POST | البحث في القرآن |
| `/api/v1/quran/validate` | POST | التحقق من الاقتباس |
| `/api/v1/quran/analytics` | POST | تحليلات NL2SQL |
| `/api/v1/rag/fiqh` | POST | RAG للفتاوى |
| `/api/v1/rag/general` | POST | RAG عام |
| `/health` | GET | فحص الصحة |
| `/ready` | GET | فحص الجاهزية |

---

## 🔧 إعدادات مهمة

### البيئة (`.env`)
```bash
# LLM
LLM_PROVIDER=groq
GROQ_API_KEY=your-key
GROQ_MODEL=qwen/qwen3-32b

# Embeddings
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIMENSION=1024

# Database
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
```

### الثوابت
```python
# Retrieval
TOP_K_FIQH = 15
TOP_K_GENERAL = 10
SEMANTIC_THRESHOLD = 0.15
RRF_K = 60

# Classification
KEYWORD_CONFIDENCE = 0.92
LLM_CONFIDENCE = 0.75
EMBEDDING_CONFIDENCE = 0.60

# LLM
TEMPERATURE_FIQH = 0.1
TEMPERATURE_GENERAL = 0.3
TEMPERATURE_CHATBOT = 0.5
```

---

## 📚 دليل التوجيه

| الملف | الوصف |
|-------|-------|
| [`docs/mentoring/README.md`](docs/mentoring/README.md) | فهرس الدليل |
| [`docs/mentoring/01_project_overview.md`](docs/mentoring/01_project_overview.md) | نظرة عامة |
| [`docs/mentoring/02_folder_structure.md`](docs/mentoring/02_folder_structure.md) | شرح المجلدات |
| [`docs/mentoring/03_api_main_entrypoint.md`](docs/mentoring/03_api_main_entrypoint.md) | نقطة الدخول |
| [`docs/mentoring/learning_path.md`](docs/mentoring/learning_path.md) | خطة التعلم |

---

## 🎯 نصائح سريعة

### للمبتدئين
1. ابدأ بـ `README.md`
2. شغل التطبيق
3. جرب Swagger UI
4. اقرأ `01_project_overview.md`

### للمتوسطين
1. اقرأ `settings.py`
2. اقرأ `intents.py`
3. اقرأ `router.py`
4. تتبع سؤال من البداية للنهاية

### للمتقدمين
1. اقرأ `fiqh_agent.py`
2. اقرأ `embedding_model.py`
3. اقرأ `vector_store.py`
4. اقرأ `hybrid_search.py`

---

## ⚠️ نقاط مهمة

### نقاط القوة
- ✅ Factory Pattern في `create_app()`
- ✅ 3-tier classification
- ✅ Hybrid search (semantic + BM25)
- ✅ Citation normalization
- ✅ Deterministic tools (zakat, inheritance)

### نقاط التحسين
- ⚠️ تكرار الكود في الوكلاء
- ⚠️ 23 bare except clauses
- ⚠️ بعض الملفات hardcoded model names
- ⚠️ `inheritance_calculator.py` مبتور عند سطر 662

### الأمن
- 🔒 Rate limiting (60/min)
- 🔒 API key middleware
- 🔒 Input sanitization
- 🔒 Security headers
- 🔒 CORS configuration

---

## 📖 المصطلحات الأساسية

| المصطلح | التعريف |
|---------|---------|
| RAG | Retrieval-Augmented Generation |
| Embedding | تمثيل رقمي للنص كمتجه |
| Vector DB | قاعدة بيانات للمتجهات |
| Semantic Search | بحث حسب المعنى |
| BM25 | بحث حسب الكلمات |
| Intent | نية المستخدم من السؤال |
| Agent | وكيل يستخدم LLM |
| Tool | أداة حتمية بدون LLM |
| Citation | مرجع موثق للإجابة |
| Middleware | طبقة معالجة الطلبات |

---

## 🔗 روابط مهمة

- **المستودع**: https://github.com/Kandil7/Athar
- **Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **HuggingFace**: https://huggingface.co/datasets/Kandil7/Athar-Datasets
- **الشمela**: https://shamela.ws/

---

**🚀 ابدأ التعلم:** [`docs/mentoring/README.md`](docs/mentoring/README.md)

**📖 الدليل الكامل:** [`docs/mentoring/`](docs/mentoring/)

---

**آخر تحديث:** أبريل 2026  
**الإصدار:** 0.5.0  
**المعمارية:** Fanar-Sadiq Multi-Agent
