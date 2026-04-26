# ⚡ ملخص سريع - Burhan Islamic QA System

## 🕌 ما هو Burhan؟

نظام إجابة على الأسئلة الإسلامية يستخدم:
- **13 وكيل متخصص** (Agents) ← v2: 10 وكلاء CollectionAgent
- **5 أدوات حتمية** (Tools)
- **16 نوع نية** (Intents) + 4 فرعية للقرآن
- **10 مستويات أولوية** (المرحلة 8)
- **10 مجموعات متجهية** (Vector Collections)
- **5.7 مليون وثيقة** جاهزة للـ RAG
- **11.3 مليون** وثيقة لوكين
- **42.6 GB** بيانات على HuggingFace

### الإصدار v2 (أبريل 2026)
- **معمارية Config-Backed** - نظام تصريحي YAML
- **10 وكلاء CollectionAgent** - تكوين منفصل
- **طبقات جديدة**: retrieval, verification, generation

---

## 🎉 المرحلة 8: مصنف النية الهجين (15 أبريل 2026)

الآن النظام يتضمن:

```bash
# جرب نقطة النهاية الجديدة
POST /classify
{
  "query": "ما حكم صلاة الجمعة؟"
}

# النتيجة
{
  "result": {
    "intent": "fiqh",
    "confidence": 0.90,
    "method": "keyword",
    "requires_retrieval": true
  },
  "route": "fiqh_agent"
}
```

**السرعة:** <50ms (بدلاً من ~500ms مع LLM)

---

## 🗺️ خريطة سريعة

```
src/
├── api/              → 20 endpoint (FastAPI) ← جديد: /classify
├── application/     → طبقة التطبيق (المرحلة 8)
│   ├── hybrid_classifier.py  ← مصنف النية الهجين
│   ├── router.py             ← توجيه الوكيل
│   └── interfaces.py         ← بروتوكولات
├── domain/          ← تعريفات النطاق
│   ├── intents.py            ← 16 نوع نية + أولويات
│   └── models.py             ← ClassificationResult
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

## 🔑 أهم 15 ملف (محدث!)

| الأولوية | الملف | الوصف |
|----------|-------|-------|
| 1 | `src/api/main.py` | نقطة الدخول |
| 2 | `src/config/settings.py` | الإعدادات (37 متغير) |
| 3 | `src/config/intents.py` | 16 نوع نية |
| 4 | `src/application/hybrid_classifier.py` | **جديد!** مصنف النية الهجين |
| 5 | `src/domain/intents.py` | **جديد!** 16 نوع نية مع أولويات |
| 6 | `src/core/router.py` | تصنيف النية (3-tier) |
| 7 | `src/agents/base.py` | الفئات الأساسية |
| 8 | `src/agents/fiqh_agent.py` | وكيل RAG كامل |
| 9 | `src/knowledge/embedding_model.py` | BAAI/bge-m3 |
| 10 | `src/knowledge/vector_store.py` | Qdrant |
| 11 | `src/knowledge/hybrid_search.py` | Semantic + BM25 |
| 12 | `src/quran/nl2sql.py` | لغة طبيعية → SQL |
| 13 | `src/api/routes/classification.py` | **جديد!** نقطة /classify |
| 14 | `src/application/router.py` | **جديد!** توجيه الوكيل |
| 15 | `src/tools/zakat_calculator.py` | حاسبة الزكاة |

---

## 🔄 تدفق الاستعلام (محدث!)

```
مستخدم يسأل: "ما حكم صلاة العيد؟"
    ↓
POST /api/v1/query {"query": "..."}
    ↓
**HybridIntentClassifier (المرحلة 8)**
    ├─ Keyword Match: "ما حكم" → fiqh (0.92) ← سريع!
    ├─ Jaccard Fallback: (if keyword fails)
    └─ Confidence Gating: if < 0.5 → ISLAMIC_KNOWLEDGE
    ↓
Priority Resolution: 10 levels (TAFSIR=10 down to ISLAMIC_KNOWLEDGE=1)
    ↓
Quran Sub-intent Detection (if quran):
    ├─ VERSE_LOOKUP: "ما رقم سورة..."
    ├─ ANALYTICS: "كم مرة ذكر..."
    ├─ INTERPRETATION: "ما تفسير..."
    └─ QUOTATION_VALIDATION: "هل صحيح..."
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
    "confidence": 0.89,
    "intent": "fiqh"
}
```

---

## 📊 16 Intent + الأولويات (محدث!)

| الأولوية | Intent | Agent/Tool | مثال |
|----------|--------|-----------|------|
| 10 | tafsir | general_islamic_agent | "ما تفسير آية كذا؟" |
| 9 | quran | quran_pipeline | "آية عن كذا" |
| 9 | hadith | hadith_agent | "حديث عن كذا" |
| 8 | seerah | seerah_agent | "متى ولد النبي؟" |
| 7 | islamic_history | islamic_history_agent | "متى كانت غزوة بدر؟" |
| 6 | arabic_language | arabic_language_agent | "ما معنى هذه الكلمة؟" |
| 5 | fiqh | fiqh_agent | "ما حكم صلاة العيد؟" |
| 5 | aqeedah | aqeedah_agent | "ما معنى التوحيد؟" |
| 4 | usul_fiqh | usul_fiqh_agent | "ما هي مصادر التشريع؟" |
| 3 | spirituality | general_islamic_agent | "ما هي طريق التصوف؟" |
| 2 | greeting | chatbot_agent | "السلام عليكم" |
| 2 | dua | dua_tool | "دعاء السفر" |
| 2 | hijri_calendar | hijri_tool | "متى يبدأ رمضان؟" |
| 2 | prayer_times | prayer_times_tool | "متى صلاة الفجر؟" |
| 2 | zakat | zakak_tool | "كيف أحسب الزكاة؟" |
| 2 | inheritance | inheritance_tool | "كيف أقسم الميراث؟" |
| 1 | islamic_knowledge | general_islamic_agent | (fallback) |

---

## 📊 Quran Sub-intents (جديد!)

| النوع | الوصف | مثال |
|-------|-------|------|
| VERSE_LOOKUP | البحث عن آية | "ما رقم سورة الإخلاص؟" |
| ANALYTICS | إحصاء القرآن | "كم مرة упомина اسم الله؟" |
| INTERPRETATION | تفسير الآيات | "ما تفسير آية الكرسي؟" |
| QUOTATION_VALIDATION | التحقق من الإقتباس | "هل صحيح قولهم...؟" |

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
- **اللغات**: 100+
- **الجهاز**: GPU (Colab T4) / CPU

### Vector Database
- **النظام**: Qdrant
- **المجموعات**: 10
- **المتجهات**: 5.7 مليون (حالياً على HuggingFace)
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

## 📈 إحصائيات سريعة (محدث!)

| المقياس | القيمة |
|---------|--------|
| الأسطر البرمجية | ~15,500 |
| الملفات | ~130 |
| الاختبارات | 9 ملفات (~91% تغطية) |
| **الـ endpoints** | **20** (+2 من المرحلة 8) |
| الوكلاء | 13 |
| الأدوات | 5 |
| أنواع النية | 16 + 4 فرعية للقرآن |
| **مستويات الأولوية** | **10** |
| لوكين Documents | 11,316,717 |
| RAG Documents | 5,717,177 |
| HuggingFace Data | 42.6 GB |
| المستندات | 8,425 كتاب |
| العلماء | 3,146 عالم |
| دقة التصنيف | ~90% |
| **سرعة /classify** | **<50ms** |
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

## 🌐 20 Endpoints (محدث!)

| Endpoint | Method | الوصف |
|----------|--------|-------|
| **جديد** `/classify` | POST | تصنيف النية السريع (<50ms) |
| `/api/v1/query` | POST | السؤال الرئيسي |
| `/api/v1/tools/zakat` | POST | حساب الزكاة |
| `/api/v1/tools/inheritance` | POST | تقسيم الميراث |
| `/api/v1/tools/prayer-times` | POST | أوقات الصلاة |
| `/api/v1/tools/hijri` | POST | التاريخ الهجري |
| `/api/v1/tools/duas` | POST | الأدعية |
| `/api/v1/quran/surahs` | GET | قائمة السور |
| `/api/v1/quran/surahs/{n}` | GET | تفاصيل سورة |
| `/api/v1/quran/ayah/{s}:{a}` | GET | آية محددة |
| `/api/v1/quran/search` | POST | بحث في القرآن |
| `/api/v1/quran/validate` | POST | التحقق من إقتباس |
| `/api/v1/quran/analytics` | POST | إحصائيات القرآن |
| `/api/v1/quran/tafsir/{s}:{a}` | GET | تفسير آية |
| `/api/v1/rag/fiqh` | POST | سؤال فقه |
| `/api/v1/rag/general` | POST | سؤال عام |
| `/api/v1/rag/stats` | GET | إحصائيات RAG |
| `/health` | GET | فحص الصحة |
| `/ready` | GET | فحص الجاهزية |
| `/docs` | GET | توثيق Swagger |

---

## 🔑 الفرق بين /classify و /api/v1/query

| الميزة | `/classify` | `/api/v1/query` |
|--------|-------------|-----------------|
| السرعة | <50ms | ~500ms |
| الطريقة | Keyword + Jaccard | LLM + RAG |
| الاستخدام | تحديد نوع السؤال | إجابة كاملة |
| الاسترجاع | لا | نعم |
| النتيجة | intent + confidence | answer + sources |

---

## 💡 نصائح سريعة

### استخدام /classify
```bash
# سريع - للتصنيف فقط
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "ما حكم الزكاة؟"}'

# كامل - للإجابة
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "ما حكم الزكاة؟"}'
```

### اختيار Agent
- **أسئلة دينية** → `/classify` أولاً ثم `/api/v1/query`
- **حسابات** (زكاة، مواريث) → `/api/v1/tools/*` مباشرة
- **أسئلة القرآن** → `/api/v1/quran/*`

---

## 📚 مصادر سريعة

- [docs/11-learning/README.md](docs/11-learning/README.md) - دليل التوجيه
- [docs/10-operations/LUCENE_MERGE_COMPLETE.md](docs/10-operations/LUCENE_MERGE_COMPLETE.md) - المرحلة 7
- [notebooks/COLAB_GPU_EMBEDDING_GUIDE.md](notebooks/COLAB_GPU_EMBEDDING_GUIDE.md) - تشغيل التضمين
- [https://huggingface.co/datasets/Kandil7/Athar-Datasets](https://huggingface.co/datasets/Kandil7/Athar-Datasets) - البيانات

---

## 🎯 الخلاصة

- **20 endpoint** (جديد: `/classify`)
- **<50ms** لتصنيف النية (المرحلة 8)
- **16 intent + 4 فرعية للقرآن**
- **10 مستويات أولوية**
- **5.7M متجه** على HuggingFace
- **~91% اختبار تغطية**

**المرحلة 8 مكتملة!** 🎉

---

## 🏗️ الإصدار v2 - المعمارية الجديدة (أبريل 2026)

### ما الجديد؟
الإصدار v2 يقدم **نظام تصريحي** (declarative) مع:
- **10 ملفات YAML** للتكوين
- **ملفات Prompts منفصلة**
- **CollectionAgent** جديد
- **طبقات جديدة**: retrieval, verification, generation

### المسارات الجديدة

```
src/agents/collection/     ← 10 وكلاء CollectionAgent
config/agents/             ← 10 ملفات YAML
prompts/                  ← ملفات Prompts
src/retrieval/            ← طبقة الاسترجاع
src/verification/         ← طبقة التحقق
src/application/routing/ ← التوجيه
src/generation/           ← التوليد
```

### للمزيد
- [02_folder_structure.md](02_folder_structure.md) - المعمارية الكاملة
- [V2_MIGRATION_NOTES.md](../8-development/refactoring/V2_MIGRATION_NOTES.md) - دليل الانتقال

---

*ملخص سريع - الإصدار 2.0 - أبريل 2026*
*Built with ❤️ for the Muslim community*