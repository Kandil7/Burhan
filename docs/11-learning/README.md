# 📚 فهرس دليل التوجيه - Burhan Islamic QA System

## 🕌 مرحباً بك في دليل التوجيه الشامل

هذا الدليل مصمم لمهندسي الذكاء الاصطناعي والمطورين الذين يريدون فهم مشروع **Burhan** بعمق.

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

### ما الجديد في v2 Migration

| المكون | الوصف | المسار الجديد |
|--------|-------|--------------|
| Collection Agents | وكلاء RAG مبنيين على التكوين | `src/agents/collection/` |
| Retrieval Layer | طبقة الاسترجاع المحسنة | `src/retrieval/` + schemas, filters, fusion |
| Verification | التحقق من المصادر | `src/verification/` |
| Routing | توجيه الوكلاء | `src/application/routing/` |
| Infrastructure | عمليات Qdrant | `src/infrastructure/qdrant/` |
| Generation | توليد الإجابات | `src/generation/` |
| Observability | التتبع والمراقبة | `src/api/middleware/request_id.py` |

---

## 📋 محتويات الدليل

### الجزء الأول: نظرة عامة على المشروع
**الملف:** [`01_project_overview.md`](01_project_overview.md)

**ماذا ستتعلم:**
- ما هو مشروع Burhan؟
- خريطة المشروع عالية المستوى
- أهم 10 ملفات يجب فهمها أولاً
- كيف تقرأ المشروع بالترتيب الصحيح
- المعمارية العامة (Architecture)
- تدفق البيانات الرئيسي

**المدة المتوقعة:** 30-45 دقيقة

---

### الجزء الثاني: شرح المجلدات (مُحدث!)
**الملف:** [`02_folder_structure.md`](02_folder_structure.md)

**ماذا ستتعلم:**
- كل مجلد في المشروع ووظيفته
- كيف تتدفق البيانات بين المجلدات
- نمط التصميم المستخدم في كل مجلد
- أين تبدأ القراءة في كل مجلد
- **المجلدات الجديدة في v2**: `src/agents/collection/`, `src/verification/`, `src/application/routing/`, `src/infrastructure/qdrant/`, `src/generation/`

**المجلدات المغطاة:**
1. `src/api/` - طبقة واجهة البرمجة (25+ endpoint)
2. `src/application/` - طبقة التطبيق (incl. v2 routing/)
3. `src/domain/` - تعريفات النطاق (intents, models)
4. `src/config/` - الإعدادات والثوابت
5. `src/core/` - المنطق الأساسي
6. `src/agents/` - الوكلاء المتخصصون (16+ وكيل)
   - `legacy/` - الوكلاء التقليديون (مُهمل)
   - `collection/` - الوكلاء الجدد v2 (canonical)
7. `src/tools/` - الأدوات الحتمية (5 أدوات)
8. `src/quran/` - خط إنتاج القرآن
9. `src/knowledge/` - بنية RAG (مُهمل → استخدم src/retrieval/)
10. `src/infrastructure/` - الخدمات الخارجية (incl. v2 Qdrant)
11. `src/retrieval/` - **جديد v2** طبقة الاسترجاع
12. `src/verification/` - **جديد v2** طبقة التحقق
13. `src/generation/` - **جديد v2** طبقة التوليد

**المدة المتوقعة:** 45-60 دقيقة

---

### الجزء الثالث: نقطة الدخول
**الملف:** [`03_api_main_entrypoint.md`](03_api_main_entrypoint.md)

**ماذا ستتعلم:**
- كيف يبدأ التطبيق
- Factory Pattern في FastAPI
- Middleware ordering والأمان
- Lifespan management
- Router registration
- كيف تقرأ `src/api/main.py` سطر بسطر

**المدة المتوقعة:** 30-45 دقيقة

---

## 🗺️ خارطة الطريق المقترحة

### للمبتدئين (أسبوع 1-2)

```
اليوم 1-2:  01_project_overview.md       ← فهم الصورة الكبيرة
اليوم 3-4:  02_folder_structure.md       ← فهم البنية
اليوم 5-6:  03_api_main_entrypoint.md    ← فهم نقطة الدخول
اليوم 7:    تشغيل التطبيق لأول مرة
```

### للمتوسطين (أسبوع 3-4)

```
اليوم 1-2:  src/config/settings.py       ← الإعدادات
اليوم 3-4:  src/config/intents.py        ← 16 نوع نية
اليوم 5-6:  src/core/router.py           ← تصنيف النية
اليوم 7-8:  src/core/registry.py         ← تسجيل الوكلاء
```

### للمتقدمين (أسبوع 5-6)

```
اليوم 1-2:  src/agents/base.py           ← الفئات الأساسية
اليوم 3-4:  src/agents/fiqh_agent.py     ← وكيل RAG كامل
اليوم 5-6:  src/knowledge/embedding_model.py  ← التضمين
اليوم 7-8:  src/knowledge/vector_store.py     ← Qdrant
```

### للمتقدمين جداً (أسبوع 7-8)

```
اليوم 1-2:  src/application/hybrid_classifier.py  ← مصنف النية الهجين
اليوم 3-4:  src/domain/intents.py          ← 16 نوع نية مع الأولويات
اليوم 5-6:  src/api/routes/classification.py  ← نقطة نهاية /classify
اليوم 7-8:  تجربة التصنيف الجديد
```

### لـ v2 Migration (أسبوع 9-10) - جديد!

```
اليوم 1-2:  src/agents/collection/base.py    ← قاعدة CollectionAgent
اليوم 3-4:  config/agents/*.yaml            ← ملفات التكوين
اليوم 5-6:  src/config/__init__.py        ← تحميل التكوين
اليوم 7-8:  src/application/routing/       ← التوجيه الجديد
```

---

## 🎯 كيف تستخدم هذا الدليل

### 1️⃣ اقرأ بالترتيب
لا تقفز بين الملفات. كل ملف يبني على سابقه.

### 2️⃣ طبق التمارين
في نهاية كل ملف يوجد تمرين صغير. حله قبل المتابعة.

### 3️⃣ اسأل الأسئلة
إذا لم تفهم شيئاً، اسأل: "اشرح لي هذا الجزء بالتفصيل"

### 4️⃣ اقرأ الكود
بعد قراءة الشرح، افتح الملف واقرأه بنفسك.

### 5️⃣ جرب التغييرات
بعد فهم ملف، جرب تغيير بسيط وشاهد ماذا يحدث.

---

## 📖 طلبات شائعة

### "اشرح الملف X"
سأستخدم **بروتوكول شرح الملفات**:
1. وظيفة الملف
2. نظرة عامة على المحتويات
3. شرح جزء جزء
4. شرح سطر سطر (إذا لم يكن كبيراً)
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

## 🔑 المصطلحات الأساسية

### Retrieval-Augmented Generation (RAG)
**تعريف**: تقنية تجمع بين البحث (Retrieval) والتوليد (Generation).

**كيف تعمل**:
```
سؤال المستخدم
    ↓
Retrieve (استرجع): ابحث عن وثائق مشابهة
    ↓
Augment (أضف): أضف الوثائق إلى الـ prompt
    ↓
Generate (ولد): LLM يولد إجابة مبنية على الوثائق
```

**في Burhan**: كل الوكلاء (Fiqh, Hadith, General) يستخدمون RAG

---

### Embeddings (التضمينات)
**تعريف**: تمثيل رقمي للنصوص كأرقام (متجهات) في فضاء متعدد الأبعاد.

**لماذا مهم**:
- نصوص متشابهة = متجهات متشابهة
- يمكننا حساب التشابه بين النصوص

**في Burhan**: BAAI/bge-m3 (1024 dimensions, 8192 tokens, 100+ languages)

---

### Vector Database (قاعدة المتجهات)
**تعريف**: قاعدة بيانات متخصصة في تخزين والبحث عن المتجهات.

**لماذا مهم**:
- بحث سريع جداً (ملايين المتجهات في ميلي ثواني)
- يدعم البحث الدلالي (semantic search)

**في Burhan**: Qdrant (10 مجموعات، 5.7 مليون متجه)

---

### Intent Classification (تصنيف النية)
**تعريف**: فهم ما يريده المستخدم من السؤال.

**لماذا مهم**:
- يوجه السؤال للوكيل الصحيح
- يحسن دقة الإجابة

**في Burhan**: 
- **v2**: ConfigRouter مبني على DOMAIN_KEYWORDS
- **Phase 8**: Hybrid (keyword → Jaccard → confidence gating)
- **16 نوع نية** مع 10 مستويات أولوية
- **4 أنواع فرعية للقرآن**

---

### Config-Backed Agents (الوكلاء المبنيون على التكوين) - جديد!
**تعريف**: وكلاء يتم تحديدهم من ملفات YAML بدلاً من الكود.

**لماذا مهم**:
- فصل التكوين عن الكود
- سهولة التغيير بدون تعديل الكود
- تكوين مختلف لكل مجال

**في Burhan v2**:
- 10 ملفات YAML في `config/agents/`
- 11 ملف prompts في `prompts/`
- `AgentConfigManager` يحمّل التكوين

---

### Hybrid Search (البحث المختلط)
**تعريف**: دمج البحث الدلالي (semantic) والبحث بالكلمات (BM25).

**لماذا مهم**:
- Semantic: يفهم المعنى
- BM25: يتطابق مع الكلمات
- الجمع = نتائج أفضل

**في Burhan**: Reciprocal Rank Fusion (k=60)

---

## 🎓 خطة التعلم المقترحة

### المرحلة 1: الأساسيات (أسبوع 1-2)
- [ ] قراءة `01_project_overview.md`
- [ ] قراءة `02_folder_structure.md`
- [ ] قراءة `03_api_main_entrypoint.md`
- [ ] تشغيل التطبيق
- [ ] تجربة الـ 20 endpoint عبر Swagger

### المرحلة 2: فهم التصنيف (أسبوع 3-4)
- [ ] قراءة `src/config/intents.py`
- [ ] قراءة `src/core/router.py`
- [ ] فهم 3-tier classification
- [ ] تجربة تصنيف الأسئلة المختلفة

### المرحلة 3: فهم الوكلاء (أسبوع 5-6)
- [ ] قراءة `src/agents/base.py`
- [ ] قراءة `src/agents/chatbot_agent.py`
- [ ] قراءة `src/agents/fiqh_agent.py`
- [ ] فهم RAG flow

### المرحلة 4: فهم RAG (أسبوع 7-8)
- [ ] قراءة `src/knowledge/embedding_model.py`
- [ ] قراءة `src/knowledge/vector_store.py`
- [ ] قراءة `src/knowledge/hybrid_search.py`
- [ ] فهم retrieval pipeline

### المرحلة 5: فهم القرآن (أسبوع 9-10)
- [ ] قراءة `src/quran/verse_retrieval.py`
- [ ] قراءة `src/quran/nl2sql.py`
- [ ] قراءة `src/quran/quotation_validator.py`
- [ ] فهم Quran pipeline

### المرحلة 6: فهم الأدوات (أسبوع 11-12)
- [ ] قراءة `src/tools/base.py`
- [ ] قراءة `src/tools/zakat_calculator.py`
- [ ] قراءة `src/tools/inheritance_calculator.py`
- [ ] فهم deterministic tools

### المرحلة 7: المرحلة الثامنة - مصنف النية الهجين (أسبوع 13-14)
- [ ] قراءة `src/application/hybrid_classifier.py`
- [ ] قراءة `src/domain/intents.py`
- [ ] قراءة `src/application/router.py`
- [ ] قراءة `src/api/routes/classification.py`
- [ ] تجربة نقطة نهاية `/classify`

### المرحلة 8: ترحيل v2 (أسبوع 15-16) - جديد!
- [ ] قراءة `src/agents/collection/base.py` - قاعدة CollectionAgent
- [ ] قراءة `config/agents/fiqh.yaml` - مثال على التكوين
- [ ] قراءة `src/config/__init__.py` - تحميل التكوين
- [ ] قراءة `src/application/routing/intent_router.py` - التوجيه الجديد
- [ ] قراءة `src/verification/schemas.py` - مخطط التحقق
- [ ] تجربة: استيراد الوكلاء الجدد

---

## 📊 إحصائيات المشروع المُحدثة

| المقياس | القيمة |
|---------|--------|
| **الأسطر البرمجية** | ~20,000 سطر |
| **الملفات** | ~140 ملف |
| **الاختبارات** | 12+ ملف (~92% تغطية) |
| **الـ Endpoints** | 25+ endpoint |
| **الوكلاء** | 16+ وكيل (10 collection + 6 legacy) |
| **الأدوات** | 5 أدوات حتمية |
| **أنواع النية** | 16 نوع + 4 فرعية للقرآن |
| **مستويات الأولوية** | 10 مستويات |
| **المتجهات** | 5.7 مليون متجه |
| **المستندات** | 8,425 كتاب |
| **العلماء** | 3,146 عالم |
| **لوكين Documents** | 11,316,717 وثيقة |
| **بيانات HuggingFace** | 45+ GB |
| **ملفات التكوين (v2)** | 10 YAML + 11 prompts |
| **حزم v2 الجديدة** | 7 حزم (retrieval, verification, routing, etc.) |

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
git clone https://github.com/Kandil7/Burhan.git
cd Burhan

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
{
  "query": "ما حكم صلاة الجمعة؟"
}

# أو جرب endpoint /api/v1/query
{
  "query": "ما حكم صلاة العيد؟"
}
```

---

## 💡 نصائح من Mentor

### 1. اقرأ الكود قبل الشرح
لا تعتمد على الشرح فقط. اقرأ الكود بنفسك أولاً.

### 2. جرب التغييرات الصغيرة
بعد فهم ملف، جرب تغيير بسيط وشاهد ماذا يحدث.

### 3. استخدم Debugger
تعلم استخدام pdb أو IDE debugger لفهم تدفق التنفيذ.

### 4. اقرأ الاختبارات
الاختبارات توضح كيف يُتوقع استخدام الكود.

### 5. اسأل "لماذا؟"
لا تسأل "ماذا يفعل هذا الكود؟" فقط. اسأل "لماذا كُتب هكذا؟"

---

## 📝 تمارين عامة

### تمرين 1: خريطة المشروع
ارسم خريطة المشروع على ورقة. أين يوجد كل مكون؟

### تمرين 2: تدفق السؤال
اكتب تدفق سؤال من البداية للنهاية:
```
مستخدم يسأل → ??? → إجابة
```

### تمرين 3: عدد الـ Endpoints
افتح Swagger UI وعد الـ endpoints. كم وجدت؟ (الإجابة: 20)

### تمرين 4: قراءة ملف
افتح `src/domain/intents.py`. اقرأه دون شرح. ماذا فهمت؟

### تمرين 5: اختبار /classify
جرب نقطة النهاية الجديدة:
```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"query": "ما حكم الزكاة؟"}'
```

### تمرين 6: اختبار v2 (جديد!)
```bash
# اختبار استيراد الوكلاء الجدد
python -c "from src.agents.collection import FiqhCollectionAgent; print('v2 import OK!')"

# اختبار التوجيه
python -c "from src.application.routing import IntentRouter; print('Routing OK!')"
```

---

## 🎯 الخلاصة

هذا الدليل صُمم ليأخذك من **مبتدئ** إلى **فاهم بعمق** لمشروع Burhan.

كل جزء يبني على سابقه. لا تقفز. طبق التمارين. اسأل الأسئلة.

**الهدف**: أن تصبح قادراً على:
1. فهم البنية العامة
2. قراءة أي ملف وفهمه
3. إضافة ميزات جديدة
4. مراجعة كود الآخرين
5. شرح المشروع لغيرك
6. **استخدام مصنف النية الهجين الجديد** (المرحلة 8)

---

## 📚 مصادر إضافية

- **[docs/8-development/refactoring/V2_MIGRATION_NOTES.md](../8-development/refactoring/V2_MIGRATION_NOTES.md)** - تفاصيل ترحيل v2
- **[docs/9-reference/CONFIG_BACKED_AGENTS.md](../9-reference/CONFIG_BACKED_AGENTS.md)** - الوكلاء المبنيين على التكوين
- **[docs/9-reference/DOMAIN_KEYWORDS.md](../9-reference/DOMAIN_KEYWORDS.md)** - كلمات المفتاح للتوجيه
- **[docs/10-operations/LUCENE_MERGE_COMPLETE.md](../10-operations/LUCENE_MERGE_COMPLETE.md)** - تفاصيل المرحلة 7
- **[notebooks/COLAB_GPU_EMBEDDING_GUIDE.md](../notebooks/COLAB_GPU_EMBEDDING_GUIDE.md)** - تشغيل التضمين على GPU

---

**🚀 ابدأ بـ:** [`01_project_overview.md`](01_project_overview.md)

**📖 التالي:** [`02_folder_structure.md`](02_folder_structure.md)

**🔗 ثم:** [`03_api_main_entrypoint.md`](03_api_main_entrypoint.md)

---

**مُعد الدليل:** AI Mentor System  
**التاريخ:** أبريل 2026  
**الإصدار:** 3.0  
**المشروع:** Burhan Islamic QA System v2.0 (v2 Migration Complete)