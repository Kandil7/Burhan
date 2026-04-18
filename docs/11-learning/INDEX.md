# 🕌 Athar Islamic QA System - دليل التوجيه الشامل

## 📚 مرحباً بك في دليل التوجيه

هذا الدليل مصمم لمهندسي الذكاء الاصطناعي والمطورين الذين يريدون فهم مشروع **Athar** بعمق واحترافية.

---

## 🎉 أحدث إنجاز: ترحيل v2 مكتمل (أبريل 2026)

### البنية الجديدة v2 - التكوين التصريحي (Declarative Config)

اعتباراً من **أبريل 2026**، النظام يتضمن الآن:

- ✅ **وكلاء مبنيين على YAML** - 10 ملفات تكوين + 11 ملف prompts
- ✅ **مسارات cannonical جديدة** - src/agents/collection/, src/retrieval/, src/verification/
- ✅ **طبقات من الدرجة الأولى** - retrieval, verification, routing كحزم منفصلة
- ✅ **بنية Qdrant** - src/infrastructure/qdrant/
- ✅ **مراقبة الطلبات** - RequestIDMiddleware + ResponseTrace
- ✅ **102+ اختبار** للنظام الجديد

---

## 🎯 ما ستجده في هذا الدليل

### 📖 الدليل الرئيسي

| الجزء | الملف | الموضوع | المدة |
|-------|-------|---------|-------|
| **1** | [`01_project_overview.md`](01_project_overview.md) | نظرة عامة على المشروع | 30-45 دقيقة |
| **2** | [`02_folder_structure.md`](02_folder_structure.md) | شرح كل مجلد | 45-60 دقيقة |
| **3** | [`03_api_main_entrypoint.md`](03_api_main_entrypoint.md) | نقطة الدخول (main.py) | 30-45 دقيقة |

### 🗺️ خرائط الطريق

| الملف | الوصف |
|-------|-------|
| [`learning_path.md`](learning_path.md) | خطة تعلم متدرجة (7 مراحل) |
| [`quick_reference.md`](quick_reference.md) | ملخص سريع للمعلومات الأساسية |
| [`README.md`](README.md) | فهرس الدليل |

---

## 🚀 كيف تبدأ

### للمبتدئين (ابدأ من هنا)

```
1. اقرأ: quick_reference.md         ← ملخص سريع (10 دقائق)
2. اقرأ: 01_project_overview.md     ← فهم الصورة الكبيرة
3. اقرأ: 02_folder_structure.md     ← فهم البنية
4. شغل: التطبيق لأول مرة
5. اققرأ: 03_api_main_entrypoint.md  ← فهم نقطة الدخول
6. جرب: /classify endpoint           ← الجديد في المرحلة 8
```

### للمتوسطين

```
1. اقرأ: learning_path.md           ← خطة التعلم
2. اتبع: المستوى 2 في الخطة
3. اقرأ: src/config/settings.py
4. اقرأ: src/config/intents.py
5. اقرأ: src/core/router.py
6. جرب: مصنف النية الهجين الجديد
```

### للمتقدمين

```
1. اقرأ: src/application/hybrid_classifier.py   ← المرحلة 8
2. اقرأ: src/domain/intents.py                  ← 16 نوع نية
3. اققرأ: src/agents/base.py
4. اقرأ: src/knowledge/embedding_model.py
5. اقرأ: src/knowledge/vector_store.py
```

---

## 📊 مستويات الفهم

```
المستوى 0: مبتدئ كامل
    ↓ (اليوم 1-3)
المستوى 1: فهم عام ← 01_project_overview.md
    ↓ (اليوم 4-10)
المستوى 2: فهم متوسط ← 02_folder_structure.md + learning_path.md
    ↓ (اليوم 11-20)
المستوى 3: فهم متقدم ← 03_api_main_entrypoint.md + core files
    ↓ (اليوم 21-30)
المستوى 4: فهم عميق ← knowledge/ + quran/ files
    ↓ (اليوم 31-40)
المستوى 5: إتقان ← إضافة ميزات جديدة
    ↓ (اليوم 41-50)
المستوى 6: المرحلة 8 ← Hybrid Intent Classifier (جديد!)
```

---

## 📋 قائمة الملفات الكاملة

### الدليل الرئيسي (3 ملفات)

- ✅ [`01_project_overview.md`](01_project_overview.md) - نظرة عامة شاملة
- ✅ [`02_folder_structure.md`](02_folder_structure.md) - شرح كل مجلد
- ✅ [`03_api_main_entrypoint.md`](03_api_main_entrypoint.md) - نقطة الدخول

### خرائط الطريق (3 ملفات)

- ✅ [`learning_path.md`](learning_path.md) - خطة تعلم متدرجة (7 مراحل)
- ✅ [`quick_reference.md`](quick_reference.md) - ملخص سريع
- ✅ [`README.md`](README.md) - فهرس الدليل (هذا الملف)

### ملفات التعلم المتقدمة (17 ملف)

- ✅ [`04_top_10_files_deep_explanation.md`](04_top_10_files_deep_explanation.md) - شرح عميق لأهم 10 ملفات
- ✅ [`05_router_deep_dive.md`](05_router_deep_dive.md) - شرحRouter
- ✅ [`06_top_10_files_index.md`](06_top_10_files_index.md) - فهرس أهم الملفات
- ✅ [`07_top_10_files_summary.md`](07_top_10_files_summary.md) - ملخص أهم الملفات
- ✅ [`08_registry_deep_dive.md`](08_registry_deep_dive.md) - شرحRegistry
- ✅ [`09_citation_deep_dive.md`](09_citation_deep_dive.md) - شرحالاقتباسات
- ✅ [`10_agents_and_tools_combined.md`](10_agents_and_tools_combined.md) - الوكلاء والأدوات
- ✅ [`11_complete_index.md`](11_complete_index.md) - فهرس كامل
- ✅ [`12_learning_path_detailed_explanation.md`](12_learning_path_detailed_explanation.md) - شرح مفصل للخطة
- ✅ [`13_end_to_end_execution_flow.md`](13_end_to_end_execution_flow.md) - تدفق التنفيذ من البداية للنهاية
- ✅ [`14_main_py_line_by_line.md`](14_main_py_line_by_line.md) - main.py سطر بسطر
- ✅ [`15_architecture_review_and_refactoring.md`](15_architecture_review_and_refactoring.md) - مراجعة المعمارية
- ✅ [`16_refactoring_implementation_summary.md`](16_refactoring_implementation_summary.md) - ملخص إعادة الهيكلة
- ✅ [`17_final_refactoring_report.md`](17_final_refactoring_report.md) - التقرير النهائي
- ✅ [`TOP_10_FILES_README.md`](TOP_10_FILES_README.md) - README لأهم الملفات

---

## 🎓 خطة التعلم المقترحة

### الأسبوع 1: الأساسيات

| اليوم | المهمة | الملف |
|-------|--------|-------|
| 1 | نظرة عامة | `01_project_overview.md` |
| 2 | المجلدات | `02_folder_structure.md` |
| 3 | تشغيل التطبيق | README.md |
| 4 | نقطة الدخول | `03_api_main_entrypoint.md` |
| 5 | الإعدادات | src/config/settings.py |
| 6 | intents | src/config/intents.py |
| 7 | مراجعة | كل ما سبق |

### الأسبوع 2: التصنيف والوكلاء

| اليوم | المهمة | الملف |
|-------|--------|-------|
| 1 | router | src/core/router.py |
| 2 | registry | src/core/registry.py |
| 3 | citation | src/core/citation.py |
| 4 | base agent | src/agents/base.py |
| 5 | chatbot | src/agents/chatbot_agent.py |
| 6 | fiqh agent | src/agents/fiqh_agent.py |
| 7 | مراجعة | كل ما سبق |

### الأسبوع 3: RAG

| اليوم | المهمة | الملف |
|-------|--------|-------|
| 1 | embedding | src/knowledge/embedding_model.py |
| 2 | cache | src/knowledge/embedding_cache.py |
| 3 | vector store | src/knowledge/vector_store.py |
| 4 | hybrid search | src/knowledge/hybrid_search.py |
| 5 | hierarchical | src/knowledge/hierarchical_retriever.py |
| 6 | تجربة | Swagger UI |
| 7 | مراجعة | كل ما سبق |

### الأسبوع 4: القرآن والأدوات

| اليوم | المهمة | الملف |
|-------|--------|-------|
| 1 | verse retrieval | src/quran/verse_retrieval.py |
| 2 | nl2sql | src/quran/nl2sql.py |
| 3 | quotation validator | src/quran/quotation_validator.py |
| 4 | zakat calculator | src/tools/zakat_calculator.py |
| 5 | inheritance calculator | src/tools/inheritance_calculator.py |
| 6 | الأدوات الأخرى | src/tools/*.py |
| 7 | مراجعة | كل ما سبق |

### الأسبوع 5-6: المرحلة 8 - مصنف النية الهجين (جديد!)

| اليوم | المهمة | الملف |
|-------|--------|-------|
| 1 | hybrid classifier | src/application/hybrid_classifier.py |
| 2 | domain intents | src/domain/intents.py |
| 3 | application router | src/application/router.py |
| 4 | classification endpoint | src/api/routes/classification.py |
| 5 | تجربة /classify | Swagger UI |
| 6-7 | مراجعة شاملة | كل ما سبق |

---

## 💡 كيف تستخدم هذا الدليل

### 1️⃣ اقرأ بالترتيب
لا تقفز بين الملفات. كل ملف يبني على سابقه.

### 2️⃣ طبق التمارين
في نهاية كل ملف يوجد تمرين صغير. حله قبل المتابعة.

### 3️⃣ اسأل الأسئلة
إذا لم تفهم شيئاً، اطلب: "اشرح لي هذا الجزء بالتفصيل"

### 4️⃣ اقرأ الكود
بعد قراءة الشرح، افتح الملف واقرأه بنفسك.

### 5️⃣ جرب التغييرات
بعد فهم ملف، جرب تغيير بسيط وشاهد ماذا يحدث.

---

## 🎯 طلبات شائعة

### "اشرح الملف X"
سأستخدم **بروتوكول شرح الملفات**:
1. وظيفة الملف
2. نظرة عامة على المحتويات
3. شرح جزء جزء
4. شرح سطر سطر
5. المصطلحات المهمة
6. ملاحظات هندسية

### "اشرح المجلد X"
سأستخدم **بروتوكول شرح المجلدات**:
1. دور المجلد
2. الملفات داخله
3. كيف تتعاون الملفات
4. النمط المستخدم
5. أين أبدأ القراءة

### "اشرح الدالة X"
سأستخدم **بروتوكول شرح الدوال**:
1. الهدف
2. المدخلات
3. المخرجات
4. تدفق التحكم
5. الاعتماديات
6. الحالات الحدية
7. سبب اختيار هذا التصميم
8. فرص التحسين

---

## 📖 المصطلحات الأساسية المُحدثة

### Retrieval-Augmented Generation (RAG)
**تعريف**: تقنية تجمع بين البحث (Retrieval) والتوليد (Generation).

**كيف تعمل**:
```
سؤال المستخدم
    ↓
Retrieve: ابحث عن وثائق مشابهة
    ↓
Augment: أضف الوثائق إلى الـ prompt
    ↓
Generate: LLM يولد إجابة مبنية على الوثائق
```

**في Athar**: كل الوكلاء (Fiqh, Hadith, General) يستخدمون RAG

---

### Embeddings (التضمينات)
**تعريف**: تمثيل رقمي للنصوص كأرقام (متجهات) في فضاء متعدد الأبعاد.

**لماذا مهم**:
- نصوص متشابهة = متجهات متشابهة
- يمكننا حساب التشابه بين النصوص

**في Athar**: BAAI/bge-m3 (1024 dimensions, 8192 tokens, 100+ languages)

---

### Vector Database (قاعدة المتجهات)
**تعريف**: قاعدة بيانات متخصصة في تخزين والبحث عن المتجهات.

**لماذا مهم**:
- بحث سريع جداً (ملايين المتجهات في ميلي ثواني)
- يدعم البحث الدلالي (semantic search)

**في Athar**: Qdrant (10 مجموعات، 5.7 مليون متجه)

---

### Intent Classification (تصنيف النية) - مُحدث!
**تعريف**: فهم ما يريده المستخدم من السؤال.

**لماذا مهم**:
- يوجه السؤال للوكيل الصحيح
- يحسن دقة الإجابة

**في Athar (المرحلة 8)**:
- **Hybrid Intent Classifier** (keyword + Jaccard + confidence gating)
- **16 نوع نية** مع **10 مستويات أولوية**
- **4 أنواع فرعية للقرآن** (VERSE_LOOKUP, ANALYTICS, INTERPRETATION, QUOTATION_VALIDATION)
- **نقطة نهاية `/classify` جديدة** (<50ms)

---

### Hybrid Search (البحث المختلط)
**تعريف**: دمج البحث الدلالي (semantic) والبحث بالكلمات (BM25).

**لماذا مهم**:
- Semantic: يفهم المعنى
- BM25: يتطابق مع الكلمات
- الجمع = نتائج أفضل

**في Athar**: Reciprocal Rank Fusion (k=60)

---

## 📊 إحصائيات المشروع المُحدثة

| المقياس | القيمة |
|---------|--------|
| **الأسطر البرمجية** | ~15,500 سطر |
| **الملفات** | ~130 ملف |
| **الاختبارات** | 9 ملفات (~91% تغطية) |
| **الـ Endpoints** | 20 endpoint (جديد: /classify) |
| **الوكلاء** | 13 وكيل |
| **الأدوات** | 5 أدوات حتمية |
| **أنواع النية** | 16 نوع + 4 فرعية للقرآن |
| **مستويات الأولوية** | 10 مستويات |
| **لوكين Documents** | 11,316,717 وثيقة |
| **RAG Documents** | 5,717,177 وثيقة |
| **المستندات** | 8,425 كتاب |
| **العلماء** | 3,146 عالم |
| **بيانات HuggingFace** | 42.6 GB |

---

## 🚀 البدء السريع

### المتطلبات
```bash
# Python 3.12+
python --version

# Poetry
poetry --version

# Docker
docker --version
```

### التثبيت
```bash
# استنساخ المستودع
git clone https://github.com/Kandil7/Athar.git
cd Athar

# تثبيت التبعيات
make install-dev

# بدء الخدمات
make docker-up

# تشغيل المهاجرين
make db-migrate

# تشغيل التطبيق
make dev
```

### التجربة
```bash
# افتح Swagger UI
http://localhost:8000/docs

# جرب endpoint /classify الجديد (المرحلة 8)
POST /classify
{
  "query": "ما حكم صلاة الجمعة؟"
}

# أو جرب endpoint /api/v1/query
POST /api/v1/query
{
  "query": "ما حكم صلاة العيد؟"
}
```

---

## 📚 مصادر إضافية

### وثائق المشروع
```
docs/getting-started/          ← دليل البداية
docs/architecture/             ← المعمارية
docs/api/                      ← توثيق الـ API (20 endpoint)
docs/core-features/            ← الميزات
docs/data/                     ← البيانات
docs/deployment/               ← النشر
docs/10-operations/            ← المرحلة 8 وثائق
```

### أبحاث وأوراق علمية
```
docs/Fanar-Sadiq A Multi-Agent Architecture for Grounded Islamic QA.pdf
```

### أدوات خارجية
```
https://qdrant.tech/documentation/     ← Qdrant docs
https://fastapi.tiangolo.com/          ← FastAPI docs
https://huggingface.co/BAAI/bge-m3    ← BGE-m3 model
```

---

## 🎓 الخلاصة

هذا الدليل صُمم ليأخذك من **مبتدئ** إلى **فاهم بعمق** لمشروع Athar.

كل جزء يبني على سابقه. لا تقفز. طبق التمارين. اسأل الأسئلة.

**الهدف**: أن تصبح قادراً على:
1. فهم البنية العامة
2. قراءة أي ملف وفهمه
3. إضافة ميزات جديدة
4. مراجعة كود الآخرين
5. شرح المشروع لغيرك
6. **استخدام مصنف النية الهجين الجديد** (المرحلة 8)

---

## 📝 ملاحظات مهمة

### عن هذا الدليل
- **المُعد**: AI Mentor System
- **التاريخ**: أبريل 2026
- **الإصدار**: 2.0
- **المشروع**: Athar Islamic QA System v0.8.0 (Phase 8 Complete)

### كيف تساهم
إذا وجدت خطأ أو تحسين، شاركنا ملاحظاتك.

### الدعم
للأسئلة والاستفسارات، اطلب المساعدة في أي وقت.

---

## 🎉 المراحل

| المرحلة | الحالة | الإنجاز |
|---------|--------|---------|
| المرحلة 1-6 | ✅ مكتملة | الأساسيات، الأدوات، RAG، 13 وكيل |
| المرحلة 7 | ✅ مكتملة | 11.3 مليون وثيقة لوكين |
| **المرحلة 8** | ✅ **مكتملة** | **مصنف النية الهجين** (15 أبريل 2026) |
| المرحلة 9 | ⏳ 待命 | GPU Embedding و Qdrant Import |

---

**🚀 ابدأ الآن:** [`01_project_overview.md`](01_project_overview.md)

**📖 التالي:** [`02_folder_structure.md`](02_folder_structure.md)

**🔗 ثم:** [`03_api_main_entrypoint.md`](03_api_main_entrypoint.md)

---

<div align="center">

**بُني بـ ❤️ للمجتمع المسلم**

[🕌](#) Athar Islamic QA System • مبني على معمارية Fanar-Sadiq

**دليل توجيه شامل • فهم عميق • تعلم متدرج • المرحلة 8 مكتملة**

</div>