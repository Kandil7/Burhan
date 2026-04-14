# 🎯 خطة تعلم مشروع Athar - دليل عملي

## 🕌 مقدمة

هذا الدليل مصمم ليأخذك من **الصفر** إلى **فهم عميق** لمشروع Athar.

كل مرحلة تحتوي على:
- ✅ أهداف واضحة
- 📚 ملفات للقراءة
- 💻 تمارين عملية
- 🎯 اختبار فهم

---

## 📊 المستويات

```
المستوى 0: مبتدئ كامل (لم ترَ الكود بعد)
    ↓
المستوى 1: فهم عام (تعرف البنية)
    ↓
المستوى 2: فهم متوسط (تعرف المكونات الرئيسية)
    ↓
المستوى 3: فهم متقدم (تعرف التفاصيل التقنية)
    ↓
المستوى 4: فهم عميق (تستطيع الشرح والتعديل)
```

---

## 🟢 المستوى 1: فهم عام (اليوم 1-3)

### الأهداف
- [ ] تعرف ما هو Athar
- [ ] تعرف على البنية العامة
- [ ] تشغيل التطبيق لأول مرة
- [ ] رؤية الـ API يعمل

### الملفات المطلوبة
```
1. README.md                      ← اقرأه كاملاً
2. docs/mentoring/01_project_overview.md
3. docs/mentoring/02_folder_structure.md
```

### التمارين

#### تمرين 1: رسم خريطة المشروع
على ورقة، ارسم:
- المجلدات الرئيسية (src/, data/, scripts/, tests/, docs/)
- داخل src/: كل المجلدات الفرعية
- أسهم توضح كيف تتصل ببعضها

#### تمرين 2: الإجابة على الأسئلة
أجب بدون الرجوع للشروح:
1. ما هو Athar؟
2. كم عدد الـ endpoints؟
3. ما هي الـ 5 أدوات حتمية؟
4. كم مجموعة متجهية في Qdrant؟
5. ما هو الـ RAG؟

#### تمرين 3: تشغيل التطبيق
```bash
# استنساخ
git clone https://github.com/Kandil7/Athar.git
cd Athar

# تثبيت
poetry install --with rag

# تشغيل الخدمات
docker compose -f docker/docker-compose.dev.yml up -d

# تشغيل التطبيق
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002

# اختبار
curl http://localhost:8002/health
```

### ✅ علامة الانتهاء
عندما تستطيع تشغيل التطبيق وترى `/health` يرجع `{"status": "ok"}`

---

## 🟡 المستوى 2: فهم متوسط (اليوم 4-10)

### الأهداف
- [ ] فهم نقطة الدخول (`main.py`)
- [ ] فهم الإعدادات (`settings.py`)
- [ ] فهم الـ 16 intent
- [ ] فهم كيف يُصنَّف السؤال

### الملفات المطلوبة
```
1. docs/mentoring/03_api_main_entrypoint.md
2. src/api/main.py                  ← اقرأه سطر سطر
3. src/config/settings.py           ← اقرأه سطر سطر
4. src/config/intents.py            ← اقرأه سطر سطر
5. src/config/constants.py          ← اقرأه سطر سطر
```

### التمارين

#### تمرين 1: تتبع إعداد
في `settings.py`:
1. كم متغير بيئة موجود؟
2. ما قيمة `llm_provider` الافتراضية؟
3. ما قيمة `embedding_model` الافتراضية؟
4. ما الفرق بين `is_production` و `is_development`؟

#### تمرين 2: تتبع Intent
في `intents.py`:
1. اكتب الـ 16 intent من الذاكرة
2. ما الـ agent المسؤول عن كل intent؟
3. ما الكلمات المفتاحية لـ fiqh؟
4. ما الكلمات المفتاحية لـ quran؟

#### تمرين 3: تجربة تصنيف
افتح Swagger UI (`http://localhost:8002/docs`) وجرب:

```json
// سؤال فقه
{"query": "ما حكم صلاة العيد؟"}

// سؤال قرآن
{"query": "ما تفسير آية الكرسي؟"}

// تحية
{"query": "السلام عليكم"}

// زكاة
{"query": "كيف أحسب الزكاة على ذهبي؟"}
```

شاهد الـ `intent` في الاستجابة. هل صنف بشكل صحيح؟

### ✅ علامة الانتهاء
عندما تستطيع تفسير لماذا كل سؤال صُنف إلى intent معين.

---

## 🟠 المستوى 3: فهم متقدم (اليوم 11-20)

### الأهداف
- [ ] فهم تصنيف النية (3-tier)
- [ ] فهم تسجيل الوكلاء
- [ ] فهم الوكلاء والأدوات
- [ ] فهم تدفق RAG

### الملفات المطلوبة
```
1. src/core/router.py               ← اقرأه سطر سطر
2. src/core/registry.py             ← اقرأه سطر سطر
3. src/core/citation.py             ← اقرأه سطر سطر
4. src/agents/base.py               ← اقرأه سطر سطر
5. src/agents/chatbot_agent.py      ← اقرأه سطر سطر
6. src/agents/fiqh_agent.py         ← اقرأه سطر سطر
7. src/tools/base.py                ← اقرأه سطر سطر
8. src/tools/zakat_calculator.py    ← اقرأه سطر سطر
```

### التمارين

#### تمرين 1: تتبع تصنيف نية
في `router.py`:
1. ما هي الـ 3 tiers؟
2. ما confidence كل tier؟
3. لماذا keyword أولاً وليس LLM؟
4. ماذا يحدث إذا فشل الـ 3 tiers؟

#### تمرين 2: تتبع وكيل
في `fiqh_agent.py`:
1. ما المدخلات؟
2. ما المخرجات؟
3. كيف يسترجع الوثائق؟
4. كيف يولد الإجابة؟
5. كيف يضيف الاقتباسات؟

#### تمرين 3: تتبع أداة
في `zakat_calculator.py`:
1. ما أنواع الزكاة المدعومة؟
2. ما هو nisab؟
3. كيف يحسب الزكاة على الذهب؟
4. كيف يحسب الزكاة على الفضة؟

#### تمرين 4: رسم تدفق RAG
ارسم diagram يوضح:
```
سؤال → تصنيف → وكيل → استرجاع → توليد → إجابة
```

### ✅ علامة الانتهاء
عندما تستطيع شرح RAG flow لشخص آخر بدون الرجوع للكود.

---

## 🔴 المستوى 4: فهم عميق (اليوم 21-30)

### الأهداف
- [ ] فهم نظام التضمين (embeddings)
- [ ] فهم Qdrant والبحث
- [ ] فهم البحث المختلط
- [ ] فهم خط إنتاج القرآن

### الملفات المطلوبة
```
1. src/knowledge/embedding_model.py
2. src/knowledge/embedding_cache.py
3. src/knowledge/vector_store.py
4. src/knowledge/hybrid_search.py
5. src/knowledge/hierarchical_retriever.py
6. src/quran/verse_retrieval.py
7. src/quran/nl2sql.py
8. src/quran/quotation_validator.py
```

### التمارين

#### تمرين 1: فهم Embedding
في `embedding_model.py`:
1. ما نموذج التضمين المستخدم؟
2. كم dimension للمتجه؟
3. كيف يتعامل مع CUDA vs CPU؟
4. كيف يعمل الـ caching؟

#### تمرين 2: فهم Vector Store
في `vector_store.py`:
1. كم مجموعة (collection) موجود؟
2. كيف يستورد المتجهات؟
3. كيف يبحث؟
4. ما هو HNSW؟

#### تمرين 3: فهم Hybrid Search
في `hybrid_search.py`:
1. ما هما نوعا البحث المدمجان؟
2. ما هو Reciprocal Rank Fusion؟
3. لماذا k=60؟
4. كيف يدمج النتيجتين؟

#### تمرين 4: فهم NL2SQL
في `nl2sql.py`:
1. كيف يحول اللغة الطبيعية إلى SQL؟
2. ما الـ templates المستخدمة؟
3. كيف يتجنب SQL injection؟
4. ما الأمثلة المستخدمة في الـ few-shot؟

### ✅ علامة الانتهاء
عندما تستطيع تفسير لماذا استرجاع معين أرجع نتيجة معينة.

---

## 🟣 المستوى 5: إتقان (اليوم 31+)

### الأهداف
- [ ] فهم كل الوكلاء
- [ ] فهم كل الأدوات
- [ ] فهم كل الـ endpoints
- [ ] القدرة على إضافة ميزة جديدة
- [ ] القدرة على مراجعة كود الآخرين

### الملفات المتبقية
```
src/agents/hadith_agent.py
src/agents/general_islamic_agent.py
src/agents/seerah_agent.py
src/agents/base_rag_agent.py
src/tools/inheritance_calculator.py
src/tools/prayer_times_tool.py
src/tools/hijri_calendar_tool.py
src/tools/dua_retrieval_tool.py
src/api/routes/query.py
src/api/routes/tools.py
src/api/routes.quran.py
src/api/routes.rag.py
src/api/routes.health.py
src/api.middleware.security.py
src/api.middleware.error_handler.py
src/api.schemas.request.py
src/api.schemas.response.py
src.infrastructure.database.py
src.infrastructure.redis.py
src.infrastructure.llm_client.py
```

### التمارين

#### تمرين 1: إضافة Intent جديد
أضف intent جديد: `fatwa` مع:
- keyword patterns
- agent (يمكنك استخدام general_islamic_agent كبداية)
- routing

#### تمرين 2: إضافة Tool جديد
أضف tool جديد: `qibla_finder` يحسب اتجاه القبلة.

#### تمرين 3: مراجعة كود
راجع كود `fiqh_agent.py` واقترح تحسينات.

#### تمرين 4: كتابة اختبار
اكتب اختبار لـ `router.py` يغطي 100% من الكود.

### ✅ علامة الانتهاء
عندما تستطيع إضافة ميزة جديدة بدون مساعدة.

---

## 📅 جدول زمني مقترح

### الأسبوع 1: الأساسيات
| اليوم | المهمة | الملفات |
|-------|--------|---------|
| 1 | قراءة نظرة عامة | `01_project_overview.md` |
| 2 | قراءة المجلدات | `02_folder_structure.md` |
| 3 | تشغيل التطبيق | README.md |
| 4 | قراءة main.py | `03_api_main_entrypoint.md` |
| 5 | قراءة settings.py | src/config/settings.py |
| 6 | قراءة intents.py | src/config/intents.py |
| 7 | مراجعة وتمارين | كل ما سبق |

### الأسبوع 2: التصنيف والوكلاء
| اليوم | المهمة | الملفات |
|-------|--------|---------|
| 1 | قراءة router.py | src/core/router.py |
| 2 | قراءة registry.py | src/core/registry.py |
| 3 | قراءة citation.py | src/core/citation.py |
| 4 | قراءة base.py | src/agents/base.py |
| 5 | قراءة chatbot_agent.py | src/agents/chatbot_agent.py |
| 6 | قراءة fiqh_agent.py | src/agents/fiqh_agent.py |
| 7 | مراجعة وتمارين | كل ما سبق |

### الأسبوع 3: RAG
| اليوم | المهمة | الملفات |
|-------|--------|---------|
| 1 | قراءة embedding_model.py | src/knowledge/embedding_model.py |
| 2 | قراءة embedding_cache.py | src/knowledge/embedding_cache.py |
| 3 | قراءة vector_store.py | src/knowledge/vector_store.py |
| 4 | قراءة hybrid_search.py | src/knowledge/hybrid_search.py |
| 5 | قراءة hierarchical_retriever.py | src/knowledge/hierarchical_retriever.py |
| 6 | تجربة البحث | Swagger UI |
| 7 | مراجعة وتمارين | كل ما سبق |

### الأسبوع 4: القرآن والأدوات
| اليوم | المهمة | الملفات |
|-------|--------|---------|
| 1 | قراءة verse_retrieval.py | src/quran/verse_retrieval.py |
| 2 | قراءة nl2sql.py | src/quran/nl2sql.py |
| 3 | قراءة quotation_validator.py | src/quran/quotation_validator.py |
| 4 | قراءة zakat_calculator.py | src/tools/zakat_calculator.py |
| 5 | قراءة inheritance_calculator.py | src/tools/inheritance_calculator.py |
| 6 | قراءة الأدوات الأخرى | src/tools/*.py |
| 7 | مراجعة وتمارين | كل ما سبق |

---

## 🎯 اختبارات الفهم

### اختبار المستوى 1 (بعد اليوم 3)

**السؤال 1:** ما هو Athar؟
- أ) تطبيق ويب للتجارة الإلكترونية
- ب) نظام إجابة على الأسئلة الإسلامية
- ج) محرك بحث عام
- د) قاعدة بيانات

**الإجابة:** ب

---

**السؤال 2:** كم عدد الـ endpoints في Athar؟
- أ) 10
- ب) 15
- ج) 18
- د) 20

**الإجابة:** ج

---

**السؤال 3:** ما هي التقنية المستخدمة في الـ RAG؟
- أ) فقط semantic search
- ب) فقط keyword search
- ج) hybrid search (semantic + BM25)
- د) لا يوجد RAG

**الإجابة:** ج

---

### اختبار المستوى 2 (بعد اليوم 10)

**السؤال 1:** ما هو الـ tier الأول في تصنيف النية؟
- أ) LLM classification
- ب) Embedding similarity
- ج) Keyword matching
- د) Rule-based

**الإجابة:** ج

---

**السؤال 2:** لماذا keyword matching أولاً؟
- أ) لأنه الأدق
- ب) لأنه الأسرع
- ج) لأنه الأرخص
- د) لأنه الأسهل

**الإجابة:** ب (لأنه سريع جداً - microseconds)

---

**السؤال 3:** ما الفرق بين Agent و Tool؟
- أ) لا فرق
- ب) Agent يستخدم LLM، Tool حتمي
- ج) Tool يستخدم LLM، Agent حتمي
- د) Agent للقرآن، Tool للفتاوى

**الإجابة:** ب

---

### اختبار المستوى 3 (بعد اليوم 20)

**السؤال 1:** ما هو Reciprocal Rank Fusion؟
- أ) خوارزمية دمج نتيجتين للبحث
- ب) خوارزمية تضمين النصوص
- ج) خوارزمية تصنيف النية
- د) خوارزمية توليد الإجابات

**الإجابة:** أ

---

**السؤال 2:** لماذا k=60 في RRF؟
- أ) لأنه رقم عشوائي
- ب) لأنه最优 في معظم الحالات
- ج لأنه مدروس تجريبياً
- د) لأنه مذكور في论文

**الإجابة:** ج (تجريبياً وجد أنه最优)

---

## 💡 نصائح لكل مستوى

### للمستوى 1 (مبتدئ)
- لا تستعجل
- اقرأ بتمعن
- نفذ التمارين
- شغل التطبيق

### للمستوى 2 (متوسط)
- اقرأ الكود بنفسك قبل الشرح
- جرب التغييرات الصغيرة
- اسأل "لماذا؟" ليس فقط "ماذا؟"

### للمستوى 3 (متقدم)
- ابدأ برسم diagrams
- تتبع البيانات من البداية للنهاية
- اقرأ الاختبارات

### للمستوى 4 (عميق)
- ابحث عن الـ tradeoffs
- لماذا هذا التصميم وليس آخر؟
- اقترح تحسينات

### للمستوى 5 (إتقان)
- أضف ميزات جديدة
- راجع كود الآخرين
- اشرح لغيرك

---

## 📚 مصادر إضافية

### وثائق المشروع
```
docs/getting-started/          ← دليل البداية
docs/architecture/             ← المعمارية
docs/api/                      ← توثيق الـ API
docs/core-features/            ← الميزات
docs/data/                     ← البيانات
docs/deployment/               ← النشر
```

### أبحاث وأوراق علمية
```
docs/Fanar-Sadiq A Multi-Agent Architecture for Grounded Islamic QA.pdf
```

### أدوات خارجية
```
https://qdrant.tech/documentation/     ← Qdrant docs
https://fastapi.tiangolo.com/          ← FastAPI docs
https://www.sbert.net/                 ← Sentence Transformers
```

---

## 🎓 الخلاصة

هذه الخطة مصممة لتأخذك من **الصفر** إلى **الإتقان**.

**المفتاح:**
1. اتبع الترتيب
2. لا تقفز
3. طبق التمارين
4. اسأل الأسئلة
5. اقرأ الكود بنفسك

**الهدف النهائي:**
تستطيع فهم، تعديل، وإضافة ميزات جديدة للمشروع بثقة.

---

**🚀 ابدأ الآن:** [`01_project_overview.md`](01_project_overview.md)

**📖 ثم:** [`02_folder_structure.md`](02_folder_structure.md)

**🔗 ثم:** [`03_api_main_entrypoint.md`](03_api_main_entrypoint.md)

---

**مُعد الدليل:** AI Mentor System  
**التاريخ:** أبريل 2026  
**الإصدار:** 1.0
