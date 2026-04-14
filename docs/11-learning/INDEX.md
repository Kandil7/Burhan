# 🕌 Athar Islamic QA System - دليل التوجيه الشامل

## 📚 مرحباً بك في دليل التوجيه

هذا الدليل مصمم لمهندسي الذكاء الاصطناعي والمطورين الذين يريدون فهم مشروع **Athar** بعمق واحترافية.

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
| [`learning_path.md`](learning_path.md) | خطة تعلم متدرجة (5 مستويات) |
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
5. اقرأ: 03_api_main_entrypoint.md  ← فهم نقطة الدخول
```

### للمتوسطين

```
1. اقرأ: learning_path.md           ← خطة التعلم
2. اتبع: المستوى 2 في الخطة
3. اقرأ: src/config/settings.py
4. اقرأ: src/config/intents.py
5. اقرأ: src/core/router.py
```

### للمتقدمين

```
1. اقرأ: src/agents/base.py
2. اقرأ: src/agents/fiqh_agent.py
3. اقرأ: src/knowledge/embedding_model.py
4. اقرأ: src/knowledge/vector_store.py
5. اقرأ: src/knowledge/hybrid_search.py
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
    ↓ (اليوم 31+)
المستوى 5: إتقان ← إضافة ميزات جديدة
```

---

## 📋 قائمة الملفات الكاملة

### الدليل الرئيسي (3 ملفات)

- ✅ [`01_project_overview.md`](01_project_overview.md) - نظرة عامة شاملة
- ✅ [`02_folder_structure.md`](02_folder_structure.md) - شرح كل مجلد
- ✅ [`03_api_main_entrypoint.md`](03_api_main_entrypoint.md) - نقطة الدخول

### خرائط الطريق (3 ملفات)

- ✅ [`learning_path.md`](learning_path.md) - خطة تعلم متدرجة
- ✅ [`quick_reference.md`](quick_reference.md) - ملخص سريع
- ✅ [`README.md`](README.md) - فهرس الدليل

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

## 📖 المصطلحات الأساسية

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

**في Athار**: BAAI/bge-m3 (1024 dimensions)

---

### Vector Database (قاعدة المتجهات)
**تعريف**: قاعدة بيانات متخصصة في تخزين والبحث عن المتجهات.

**لماذا مهم**:
- بحث سريع جداً (ملايين المتجهات في ميلي ثواني)
- يدعم البحث الدلالي (semantic search)

**في Athar**: Qdrant (10 مجموعات، 5.7 مليون متجه)

---

### Intent Classification (تصنيف النية)
**تعريف**: فهم ما يريده المستخدم من السؤال.

**لماذا مهم**:
- يوجه السؤال للوكيل الصحيح
- يحسن دقة الإجابة

**في Athar**: 3-tier (keyword → LLM → embedding)

---

### Hybrid Search (البحث المختلط)
**تعريف**: دمج البحث الدلالي (semantic) والبحث بالكلمات (BM25).

**لماذا مهم**:
- Semantic: يفهم المعنى
- BM25: يتطابق مع الكلمات
- الجمع = نتائج أفضل

**في Athar**: Reciprocal Rank Fusion (k=60)

---

## 📊 إحصائيات المشروع

| المقياس | القيمة |
|---------|--------|
| **الأسطر البرمجية** | ~14,200 سطر |
| **الملفات** | ~120 ملف |
| **الاختبارات** | 9 ملفات (~91% تغطية) |
| **الـ Endpoints** | 18 endpoint |
| **الوكلاء** | 13 وكيل (6 منفذين) |
| **الأدوات** | 5 أدوات حتمية |
| **المتجهات** | 5.7 مليون متجه |
| **المستندات** | 8,425 كتاب |
| **العلماء** | 3,146 عالم |

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

# جرب endpoint /api/v1/query
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

هذا الدليل صُمم ليأخذك من **مبتدئ** إلى **فاهم بعمق** لمشروع Athar.

كل جزء يبني على سابقه. لا تقفز. طبق التمارين. اسأل الأسئلة.

**الهدف**: أن تصبح قادراً على:
1. فهم البنية العامة
2. قراءة أي ملف وفهمه
3. إضافة ميزات جديدة
4. مراجعة كود الآخرين
5. شرح المشروع لغيرك

---

## 📝 ملاحظات مهمة

### عن هذا الدليل
- **المُعد**: AI Mentor System
- **التاريخ**: أبريل 2026
- **الإصدار**: 1.0
- **المشروع**: Athar Islamic QA System v0.5.0

### كيف تساهم
إذا وجدت خطأ أو تحسين، شاركنا ملاحظاتك.

### الدعم
للأسئلة والاستفسارات، اطلب المساعدة في أي وقت.

---

**🚀 ابدأ الآن:** [`01_project_overview.md`](01_project_overview.md)

**📖 التالي:** [`02_folder_structure.md`](02_folder_structure.md)

**🔗 ثم:** [`03_api_main_entrypoint.md`](03_api_main_entrypoint.md)

---

<div align="center">

**بُني بـ ❤️ للمجتمع المسلم**

[🕌](#) Athar Islamic QA System •基于 Fanar-Sadiq Architecture

**دليل توجيه شامل • فهم عميق • تعلم متدرج**

</div>
