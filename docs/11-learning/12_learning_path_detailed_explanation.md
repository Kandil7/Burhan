# 🎯 شرح مستويات خطة تعلم Burhan - تفصيل كامل بالعربية

## 🕌 مقدمة

هذا الملف يشرح **كل مستوى** في خطة التعلم بالتفصيل الكامل **سطر بسطر** بالعربية.

---

# المستوى 0: مبتدئ كامل (لم ترَ الكود بعد)

## 📍 ما معنى هذا المستوى؟

**"مبتدئ كامل"** يعني:
- لم تفتح المشروع بعد
- لا تعرف ما هو Burhan
- لم ترَ أي سطر من الكود
- لا تعرف البنية التقنية

**هذا طبيعي!** كل خبير كان مبتدئاً في البداية.

---

## 🎯 هدف هذا المستوى

الهدف ليس تعلم الكود، بل **الاستعداد النفسي والتقني**:

### 1️⃣ الاستعداد النفسي

```
قبل البدء:
├── قد تشعر بالرهبة (الكود كثير!)
├── قد تشعر بالارتباك (من أين أبدأ؟)
└── قد تشعر بالشك (هل أستطيع؟)

بعد المستوى 0:
├── تعرف أن هناك خطة واضحة
├── تعرف أن هناك دليلاً يشرح كل شيء
└── تعرف أن كل شيء ممكن خطوة بخطوة
```

### 2️⃣ الاستعداد التقني

```
المتطلبات التقنية:
├── Python 3.12+ مثبت
├── Poetry مثبت
├── Docker مثبت
├── VS Code أو أي IDE
└── git مثبت
```

---

## 🛠️ ماذا تفعل في المستوى 0؟

### الخطوة 1: تثبيت المتطلبات

```bash
# 1. تحقق من Python
python --version
# يجب أن يكون 3.12 أو أحدث
# إذا أقدم: حمل من https://python.org

# 2. تحقق من Poetry
poetry --version
# إذا أقدم:
# Windows: (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# 3. تحقق من Docker
docker --version
docker compose version
# إذا أقدم: حمل من https://docker.com

# 4. تحقق من git
git --version
# إذا أقدم: حمل من https://git-scm.com
```

### الخطوة 2: استنساخ المشروع

```bash
# افتح terminal أو PowerShell
# اذهب للمجلد الذي تريد حفظ المشروع فيه

git clone https://github.com/Kandil7/Burhan.git
cd Burhan

# تحقق من الملفات
ls
# يجب أن ترى: README.md, src/, docs/, pyproject.toml, إلخ
```

### الخطوة 3: فتح المشروع في IDE

```
1. افتح VS Code
2. File → Open Folder
3. اختر مجلد Burhan
4. انتظر حتى يحمّل المشروع
```

---

## ✅ علامة إكمال المستوى 0

تستطيع القول "أكملت المستوى 0" عندما:

- [ ] Python مثبت ويعمل
- [ ] Poetry مثبت ويعمل
- [ ] Docker مثبت ويعمل
- [ ] git مثبت ويعمل
- [ ] المشروع مستنسخ عندك
- [ ] المشروع مفتوح في IDE
- [ ] قرأت README.md (حتى لو لم تفهم كل شيء)

---

## 💡 نصائح مهمة للمستوى 0

### ❌ لا تفعل

```
❌ لا تحاول قراءة كل الكود دفعة واحدة
❌ لا تحاول فهم كل شيء مباشرة
❌ لا تقارن نفسك بغيرك
❌ لا تستعجل
```

### ✅ افعل

```
✅ اقرأ README.md بتركيز
✅ شاهد بنية المجلدات
✅ اسأل أسئلة
✅ جهز بيئة التطوير
✅ خذ وقتك
```

---

## 🧠 الحالة النفسية المتوقعة

```
قبل المستوى 0:
"هذا مشروع كبير جداً! لا أعرف من أين أبدأ..."

أثناء المستوى 0:
"أحتاج فقط تثبيت بعض الأشياء واستنساخ المشروع..."

بعد المستوى 0:
"حسناً، كل شيء جاهز. مستعد للبدء!"
```

---

## 📊 مقارنة المستويات

```
المستوى 0: تجهيز البيئة         (ساعة واحدة)
    ↓
المستوى 1: فهم عام               (3 أيام)
    ↓
المستوى 2: فهم متوسط             (7 أيام)
    ↓
المستوى 3: فهم متقدم             (10 أيام)
    ↓
المستوى 4: فهم عميق              (10 أيام)
    ↓
المستوى 5: إتقان                 (مستمر)
```

---

# المستوى 1: فهم عام (اليوم 1-3)

## 📍 ما معنى هذا المستوى؟

**"فهم عام"** يعني:
- تعرف ما هو Burhan بشكل عام
- تعرف البنية العامة (المجلدات الرئيسية)
- تستطيع تشغيل التطبيق
- ترى الـ API يعمل أمامك

**لا يعني**:
- ❌ لا تفهم الكود بالتفصيل
- ❌ لا تعرف كيف يعمل كل جزء
- ❌ لا تستطيع تعديل الكود

---

## 🎯 الأهداف الأربعة بالتفصيل

### الهدف 1: تعرف ما هو Burhan

**ما يجب أن تعرفه:**

```
Burhan هو:
├── نظام إجابة على الأسئلة الإسلامية
├── يستخدم الذكاء الاصطناعي (AI)
├── يستخدم تقنية RAG (Retrieval-Augmented Generation)
├── يجيب بإجابات موثقة بمصادر
└── يدعم العربية والإنجليزية
```

**ما يجب أن تفهمه:**

| المفهوم | المعنى البسيط | مثال |
|---------|---------------|------|
| **Islamic QA** | نظام يجيب على أسئلة إسلامية | "ما حكم صلاة العيد؟" |
| **AI** | يستخدم نموذج لغوي كبير (LLM) | Groq Qwen3-32B |
| **RAG** | يبحث في مصادر قبل الإجابة | يبحث في كتب الفقه |
| **Citations** | كل إجابة بمصادر | [C1] Quran 2:255 |

**لماذا مهم:**
- بدون فهم الهدف، لا تفهم لماذا الكود مكتوب هكذا
- Burhan ليس مجرد تطبيق عادي، هو نظام ديني موثوق

---

### الهدف 2: تعرف على البنية العامة

**ما يجب أن تعرفه:**

```
Burhan/
│
├── src/                    ← الكود الأساسي (Python)
│   ├── api/                ← نقاط الدخول (18 endpoint)
│   ├── config/             ← الإعدادات
│   ├── core/               ← المنطق الأساسي
│   ├── agents/             ← الوكلاء (13 وكيل)
│   ├── tools/              ← الأدوات (5 أدوات)
│   ├── quran/              ← خط إنتاج القرآن
│   ├── knowledge/          ← بنية الـ RAG
│   └── infrastructure/     ← DB, Redis, LLM
│
├── data/                   ← البيانات
├── scripts/                ← سكريبتات مساعدة
├── tests/                  ← الاختبارات
├── docs/                   ← التوثيق
│
└── ملفات التكوين
    ├── pyproject.toml      ← التبعيات
    ├── .env.example        ← إعدادات البيئة
    └── Makefile            ← أوامر البناء
```

**شرح كل مجلد:**

| المجلد | الوظيفة | تشبيه بسيط |
|--------|---------|------------|
| `src/api/` | يستقبل الطلبات | موظف الاستقبال |
| `src/config/` | الإعدادات | دفتر الإعدادات |
| `src/core/` | المنطق الأساسي | الدماغ |
| `src/agents/` | الوكلاء المتخصصون | خبراء متخصصون |
| `src/tools/` | أدوات حتمية | حاسبات |
| `src/quran/` | القرآن | قسم القرآن |
| `src/knowledge/` | RAG | المكتبة |
| `src/infrastructure/` | DB, Redis | البنية التحتية |

---

### الهدف 3: تشغيل التطبيق لأول مرة

**الخطوات بالتفصيل:**

```bash
# الخطوة 1: تثبيت التبعيات
poetry install --with rag

# ما يحدث:
# 1. يقرأ pyproject.toml
# 2. يحمل كل المكتبات المطلوبة
# 3. ينشئ بيئة Python معزولة
# 4. قد يستغرق 5-10 دقائق

# الخطوة 2: تشغيل الخدمات
docker compose -f docker/docker-compose.dev.yml up -d

# ما يحدث:
# 1. ينشئ 5 خدمات:
#    - PostgreSQL (قاعدة البيانات)
#    - Qdrant (قاعدة المتجهات)
#    - Redis (التخزين المؤقت)
#    - API (تطبيق FastAPI)
#    - Frontend (تطبيق Next.js - اختياري)
# 2. ينتظر حتى تكون جاهزة

# الخطوة 3: تشغيل المهاجرين
make db-migrate

# ما يحدث:
# 1. ينشئ جداول قاعدة البيانات
# 2. يضيف جداول القرآن
# 3. يهيئ البنية

# الخطوة 4: تشغيل التطبيق
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8002

# ما يحدث:
# 1. يحمّل FastAPI
# 2. يسجل الـ endpoints
# 3. يبدأ الاستماع على المنفذ 8002
```

**ما يجب أن تراه:**

```
INFO:     Uvicorn running on http://0.0.0.0:8002 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

### الهدف 4: رؤية الـ API يعمل

**اختبار health endpoint:**

```bash
# الطريقة 1: curl
curl http://localhost:8002/health

# النتيجة المتوقعة:
{"status": "ok"}

# الطريقة 2: المتصفح
# افتح: http://localhost:8002/health
# يجب أن ترى: {"status": "ok"}

# الطريقة 3: Swagger UI
# افتح: http://localhost:8002/docs
# يجب أن ترى واجهة تفاعلية بكل الـ endpoints
```

**اختبار query endpoint:**

```bash
# افتح Swagger UI: http://localhost:8002/docs
# ابحث عن POST /api/v1/query
# اضغط "Try it out"
# أدخل:
{
  "query": "السلام عليكم"
}
# اضغط "Execute"
# يجب أن ترى إجابة تحية
```

---

## 📝 التمارين بالتفصيل

### تمرين 1: رسم خريطة المشروع

**المطلوب:**

```
على ورقة، ارسم:

1. مربع كبير يكتب عليه "Burhan"
2. داخله مربعات أصغر لكل مجلد رئيسي:
   ┌─────────────────────────────────┐
   │           Burhan                  │
   │  ┌─────┐ ┌──────┐ ┌──────┐     │
   │  │ api │ │config│ │ core │     │
   │  └─────┘ └──────┘ └──────┘     │
   │  ┌──────┐ ┌─────┐ ┌──────┐    │
   │  │agents│ │tools│ │quran │    │
   │  └──────┘ └─────┘ └──────┘    │
   └─────────────────────────────────┘

3. ارسم أسهم بين المجلدات التي تتصل:
   api → core → agents → knowledge
```

**لماذا هذا التمرين مهم:**
- يساعدك على تذكر البنية
- يربط المجلدات ببعضها ذهنياً
- مرجع سريع أثناء القراءة

---

### تمرين 2: الإجابة على الأسئلة

**الأسئلة الخمسة:**

```
1. ما هو Burhan؟
   ← نظام إجابة على الأسئلة الإسلامية باستخدام AI و RAG

2. كم عدد الـ endpoints؟
   ← 18 endpoint

3. ما هي الـ 5 أدوات حتمية؟
   ← ZakatCalculator, InheritanceCalculator,
     PrayerTimesTool, HijriCalendarTool, DuaRetrievalTool

4. كم مجموعة متجهية في Qdrant؟
   ← 10 collections

5. ما هو الـ RAG؟
   ← Retrieval-Augmented Generation
     تقنية تجمع بين البحث والتوليد
```

**كيف تختبر نفسك:**

```
1. أغلق كل الشروحات
2. حاول الإجابة من الذاكرة
3. قارن مع الإجابات الصحيحة
4. أعد حتى تحصل على 5/5
```

---

### تمرين 3: تشغيل التطبيق

**قائمة التحقق:**

```bash
# قبل التشغيل:
[ ] Python 3.12+ مثبت
[ ] Poetry مثبت
[ ] Docker مثبت

# أثناء التشغيل:
[ ] poetry install --with rag (ناجح)
[ ] docker compose up -d (ناجح)
[ ] make db-migrate (ناجح)
[ ] uvicorn ... --port 8002 (ناجح)

# بعد التشغيل:
[ ] http://localhost:8002/health → {"status": "ok"}
[ ] http://localhost:8002/docs → Swagger UI يظهر
[ ] curl http://localhost:8002/health → يعمل
```

---

## ✅ علامة إكمال المستوى 1

تستطيع القول "أكملت المستوى 1" عندما:

```
✅ تستطيع شرح ما هو Burhan في جملتين
✅ تستطيع رسم خريطة المشروع من الذاكرة
✅ التطبيق يعمل عندك على المنفذ 8002
[ ] ترى {"status": "ok"} عند استدعاء /health
✅ ترى Swagger UI عند فتح /docs
✅ تستطيع تشغيل تطبيق تحية بنجاح
```

---

## ⏱️ الوقت المتوقع

```
اليوم 1: قراءة README و 01_project_overview.md    (2-3 ساعات)
اليوم 2: قراءة 02_folder_structure.md + رسم خريطة (2-3 ساعات)
اليوم 3: تشغيل التطبيق + حل التمارين             (3-4 ساعات)
                                               ─────────
المجموع: 7-10 ساعات على 3 أيام
```

---

## 🧠 الحالة النفسية المتوقعة

```
قبل المستوى 1:
"هذا مشروع معقد جداً... هل أستطيع فهمه؟"

أثناء المستوى 1:
"أها! Burhan هو نظام إجابة إسلامي. البنية واضحة..."

بعد المستوى 1:
"فهمت الصورة العامة! التطبيق يعمل! مستعد للتفاصيل!"
```

---

# المستوى 2: فهم متوسط (اليوم 4-10)

## 📍 ما معنى هذا المستوى؟

**"فهم متوسط"** يعني:
- ✅ فهمت الصورة العامة (المستوى 1)
- 🔵 الآن تفهم **كيف يعمل كل جزء**
- 🔵 تستطيع قراءة الكود وفهمه
- 🔵 تعرف لماذا كل ملف مكتوب هكذا

**لا يعني**:
- ❌ لا تستطيع إضافة ميزات جديدة
- ❌ لا تفهم كل التفاصيل التقنية
- ❌ لا تستطيع مراجعة كود الآخرين

---

## 🎯 الأهداف الأربعة بالتفصيل

### الهدف 1: فهم نقطة الدخول (`main.py`)

**ما يجب أن تفهمه:**

```python
# الملف: src/api/main.py

# 1. ما هو FastAPI؟
#    ← إطار عمل Python حديث لبناء APIs
#    ← أسرع من Flask بـ 10 مرات
#    ← يدعم async/await بشكل أصلي

# 2. ما هو create_app()؟
#    ← Factory Pattern: دالة تنشئ التطبيق
#    ← لماذا؟ يسهل الاختبار وإعادة الاستخدام

# 3. ما هو Middleware؟
#    ← طبقة تمر عليها كل الطلبات
#    ← مثال: SecurityHeadersMiddleware يضيف headers أمنية

# 4. ما هو Router؟
#    ← مجموعة endpoints في ملف واحد
#    ← مثال: routes/query.py فيها POST /api/v1/query
```

**التطبيق العملي:**

```python
# افتح src/api/main.py
# ابحث عن:

def create_app() -> FastAPI:
    app = FastAPI(
        title="Burhan Islamic QA System",  # ← اسم التطبيق
        version="0.5.0",                   # ← الإصدار
        docs_url="/docs",                  # ← Swagger UI
    )

# ما يحدث عند التشغيل:
# 1. يستدعي create_app()
# 2. ينشئ FastAPI application
# 3. يضيف middleware (الأمان، CORS, معالجة الأخطاء)
# 4. يسجل routers (query, tools, quran, rag, health)
# 5. يرجع التطبيق جاهز للاستخدام
```

**تمرين تطبيقي:**

```python
# جرب هذا في Python console:

from src.api.main import create_app

app = create_app()

print(app.title)       # "Burhan Islamic QA System"
print(app.version)     # "0.5.0"
print(app.routes)      # قائمة الـ routes
```

---

### الهدف 2: فهم الإعدادات (`settings.py`)

**ما يجب أن تفهمه:**

```python
# الملف: src/config/settings.py

# 1. ما هو Pydantic BaseSettings؟
#    ← مكتبة تقرأ متغيرات البيئة من .env
#    ← تحول النصوص إلى أنواع صحيحة (int, bool, list)
#    ← تتحقق من صحة القيم

# 2. كيف يعمل:

class Settings(BaseSettings):
    app_name: str = "Burhan"
    llm_provider: str = "groq"
    database_url: str = "postgresql+asyncpg://..."

# ما يحدث:
# 1. يبحث عن ملف .env
# 2. يقرأ APP_NAME=Burhan
# 3. يطابقه مع app_name في الكلاس
# 4. إذا لم يجد، يستخدم القيمة الافتراضية
```

**المتغيرات الأساسية (37 متغير):**

| المتغير | النوع | الافتراضي | الوصف |
|---------|-------|-----------|-------|
| `app_name` | str | "Burhan" | اسم التطبيق |
| `llm_provider` | str | "groq" | مزود الـ LLM |
| `groq_model` | str | "qwen/qwen3-32b" | نموذج Groq |
| `embedding_model` | str | "BAAI/bge-m3" | نموذج التضمين |
| `database_url` | str | "postgresql+asyncpg://..." | رابط DB |
| `redis_url` | str | "redis://localhost:6379/0" | رابط Redis |
| `qdrant_url` | str | "http://localhost:6333" | رابط Qdrant |

**تمرين تطبيقي:**

```python
# افتح src/config/settings.py
# أجب على الأسئلة:

# 1. كم متغير بيئة موجود؟
#    ← 37 متغير

# 2. ما قيمة llm_provider الافتراضية؟
#    ← "openai"

# 3. ما الفرق بين is_production و is_development؟
#    ← @property ترجع True/False حسب app_env

# 4. لماذا بعض المتغيرات Optional؟
#    ← لأنها ليست مطلوبة (مثل qdrant_api_key)
```

---

### الهدف 3: فهم الـ 16 intent

**ما يجب أن تفهمه:**

```python
# الملف: src/config/intents.py

# 1. ما هو Intent؟
#    ← "نية" المستخدم من السؤال
#    ← مثال: "ما حكم صلاة العيد؟" → fiqh
#    ← مثال: "السلام عليكم" → greeting

# 2. لماذا 16 نية؟
#    ← تغطي كل أنواع الأسئلة الإسلامية
#    ← كل نية تذهب لوكيل مختلف

# 3. كيف تستخدم:

class Intent(str, Enum):
    FIQH = "fiqh"                    # أحكام فقهية
    QURAN = "quran"                  # أسئلة عن القرآن
    GREETING = "greeting"            # تحيات
    ZAKAT = "zakat"                  # حساب الزكاة
    # ... (16 نوع)

# ما يحدث عند سؤال:
# "ما حكم صلاة العيد؟"
#   ↓
# HybridQueryClassifier.classify()
#   ↓
# RouterResult(intent=Intent.FIQH, confidence=0.92)
#   ↓
# AgentRegistry.get_for_intent(Intent.FIQH)
#   ↓
# FiqhAgent() ← هذا الوكيل سيجيب
```

**الـ 16 نية بالتفصيل:**

| النية | الوكيل | مثال سؤال | نوع |
|-------|--------|-----------|-----|
| `fiqh` | fiqh_agent | "ما حكم صلاة العيد؟" | Agent (RAG) |
| `quran` | quran_agent | "ما تفسير آية الكرسي؟" | Pipeline |
| `islamic_knowledge` | general_islamic_agent | "ما فضل الصيام؟" | Agent (RAG) |
| `greeting` | chatbot_agent | "السلام عليكم" | Agent (templates) |
| `zakat` | zakat_tool | "كيف أحسب الزكاة؟" | Tool (deterministic) |
| `inheritance` | inheritance_tool | "كيف أقسم الميراث؟" | Tool (deterministic) |
| `dua` | dua_tool | "دعاء السفر" | Tool (retrieval) |
| `hijri_calendar` | hijri_tool | "متى يبدأ رمضان؟" | Tool (calculation) |
| `prayer_times` | prayer_tool | "متى صلاة الفجر؟" | Tool (calculation) |
| `hadith` | hadith_agent | "ما حكم هذا الحديث؟" | Agent (RAG) |
| `tafsir` | general_islamic_agent | "ما تفسير هذه الآية؟" | Agent (fallback) |
| `aqeedah` | general_islamic_agent | "ما معنى التوحيد؟" | Agent (fallback) |
| `seerah` | seerah_agent | "متى ولد النبي؟" | Agent (RAG) |
| `usul_fiqh` | general_islamic_agent | "ما مصادر التشريع؟" | Agent (fallback) |
| `islamic_history` | general_islamic_agent | "متى كانت غزوة بدر؟" | Agent (fallback) |
| `arabic_language` | general_islamic_agent | "ما معنى هذه الكلمة؟" | Agent (fallback) |

**ملاحظة مهمة:**

```python
# لماذا بعض النيات تذهب إلى general_islamic_agent؟
# لأن الوكلاء المتخصصة (tafsir, aqeedah, ...) محذوفة
# سيتم إعادة كتابتها لاحقاً
# حالياً تستخدم general_islamic_agent كـ fallback
```

---

### الهدف 4: فهم كيف يُصنَّف السؤال

**ما يجب أن تفهمه:**

```python
# الملف: src/core/router.py

# 1. ما هو HybridQueryClassifier؟
#    ← مصنف يستخدم 3 طرق (tiers)

# 2. الـ 3 tiers:

Tier 1: Keyword Matching
├── السرعة: microseconds (سريع جداً)
├── الدقة: 70%
├── الثقة: 0.92
└── مثال: "ما حكم" → fiqh

Tier 2: LLM Classification
├── السرعة: milliseconds (متوسط)
├── الدقة: 90%
├── الثقة: 0.75+
└── مثال: يرسل السؤال لـ LLM يصنفه

Tier 3: Embedding Similarity
├── السرعة: milliseconds (متوسط)
├── الدقة: 80%
├── الثقة: 0.60
└── مثال: يقارن متجه السؤال مع متجهات مصنفة

# 3. كيف يعمل:

query = "ما حكم صلاة العيد؟"
    ↓
Tier 1: Keyword
├── يبحث عن "ما حكم" في KEYWORD_PATTERNS
├── يجد في Intent.FIQH
├── confidence = 0.92 >= 0.90 → ✅ يرجع
└── RouterResult(intent=FIQH, confidence=0.92)

# لو فشل Tier 1:
    ↓
Tier 2: LLM
├── يرسل prompt لـ Groq
├── LLM يرجع JSON: {"intent": "fiqh", "confidence": 0.95}
├── confidence = 0.95 >= 0.75 → ✅ يرجع
└── RouterResult(intent=FIQH, confidence=0.95)

# لو فشل Tier 2:
    ↓
Tier 3: Embedding
├── يحول السؤال لمتجه
├── يقارن مع متجهات مصنفة
├── يرجع أقرب واحد
└── RouterResult(intent=ISLAMIC_KNOWLEDGE, confidence=0.60)

# لو فشل Tier 3:
    ↓
Default Fallback
└── RouterResult(intent=ISLAMIC_KNOWLEDGE, confidence=0.50)
```

---

## 📝 التمارين بالتفصيل

### تمرين 1: تتبع إعداد

**افتح `settings.py` وأجب:**

```python
# السؤال 1: كم متغير بيئة موجود؟
# الجواب: 37 متغير
# التحقق: عد كل الأسطر التي فيها ": str =", ": int =", إلخ

# السؤال 2: ما قيمة llm_provider الافتراضية؟
# الجواب: "openai"
# التحقق: ابحث عن llm_provider: str = "openai"

# السؤال 3: ما قيمة embedding_model الافتراضية؟
# الجواب: "BAAI/bge-m3"
# التحقق: ابحث عن embedding_model: str = "BAAI/bge-m3"

# السؤال 4: ما الفرق بين is_production و is_development؟
# الجواب:
#   is_production = True عندما app_env == "production"
#   is_development = True عندما app_env == "development"
# التحقق: ابحث عن @property def is_production
```

---

### تمرين 2: تتبع Intent

**افتح `intents.py` وأجب:**

```python
# السؤال 1: اكتب الـ 16 intent من الذاكرة
# الجواب:
#   fiqh, quran, islamic_knowledge, greeting,
#   zakat, inheritance, dua, hijri_calendar, prayer_times,
#   hadith, tafsir, aqeedah, seerah, usul_fiqh,
#   islamic_history, arabic_language

# السؤال 2: ما الـ agent المسؤول عن كل intent؟
# الجواب: انظر INTENT_ROUTING
#   fiqh → fiqh_agent
#   quran → quran_agent
#   greeting → chatbot_agent
#   zakat → zakat_tool
#   ...

# السؤال 3: ما الكلمات المفتاحية لـ fiqh؟
# الجواب: انظر KEYWORD_PATTERNS[Intent.FIQH]
#   ["حكم", "fiqh", "halal", "haram", "Islamic law",
#    "ما حكم", "هل يجوز", "هل هو حلال", "هل هو حرام"]

# السؤال 4: ما الكلمات المفتاحية لـ quran؟
# الجواب: انظر KEYWORD_PATTERNS[Intent.QURAN]
#   ["آية", "سورة", "قرآن", "ayah", "surah", "quran",
#    "تفسير", "كم عدد آيات", "أطول سورة"]
```

---

### تمرين 3: تجربة تصنيف

**افتح Swagger UI (`http://localhost:8002/docs`):**

```json
// التجربة 1: سؤال فقه
POST /api/v1/query
{
  "query": "ما حكم صلاة العيد؟"
}

// النتيجة المتوقعة:
{
  "intent": "fiqh",
  "confidence": 0.92,
  "method": "keyword",
  "answer": "صلاة العيد سنة مؤكدة...",
  "citations": [...]
}

// التجربة 2: سؤال قرآن
POST /api/v1/query
{
  "query": "ما تفسير آية الكرسي؟"
}

// النتيجة المتوقعة:
{
  "intent": "quran",
  "confidence": 0.92,
  "method": "keyword",
  "answer": "آية الكرسي هي الآية 255 من سورة البقرة...",
  "citations": [...]
}

// التجربة 3: تحية
POST /api/v1/query
{
  "query": "السلام عليكم"
}

// النتيجة المتوقعة:
{
  "intent": "greeting",
  "confidence": 0.92,
  "method": "keyword",
  "answer": "وعليكم السلام ورحمة الله وبركاته",
  "citations": []
}

// التجربة 4: زكاة
POST /api/v1/query
{
  "query": "كيف أحسب الزكاة على ذهبي؟"
}

// النتيجة المتوقعة:
{
  "intent": "zakat",
  "confidence": 0.92,
  "method": "keyword",
  "answer": "لحساب الزكاة على الذهب...",
  "citations": []
}
```

---

## ✅ علامة إكمال المستوى 2

تستطيع القول "أكملت المستوى 2" عندما:

```
✅ تستطيع شرح ما يفعل main.py بالتفصيل
✅ تعرف كل متغيرات settings.py
✅ تستطيع كتابة الـ 16 intent من الذاكرة
✅ تعرف الكلمات المفتاحية لكل نية
✅ تستطيع تفسير لماذا كل سؤال صُنف لنية معينة
✅ تستطيع تتبع سؤال من /query إلى الإجابة
```

---

## ⏱️ الوقت المتوقع

```
اليوم 4: قراءة 03_api_main_entrypoint.md + main.py       (3 ساعات)
اليوم 5: قراءة settings.py + تمرين تتبع إعداد            (2 ساعات)
اليوم 6: قراءة intents.py + تمرين تتبع Intent            (2 ساعات)
اليوم 7: قراءة constants.py                              (2 ساعات)
اليوم 8: تجربة تصنيف Swagger UI                          (2 ساعات)
اليوم 9-10: مراجعة + حل كل التمارين                     (4 ساعات)
                                                      ───────
المجموع: 15-17 ساعة على 7 أيام
```

---

# المستوى 3: فهم متقدم (اليوم 11-20)

## 📍 ما معنى هذا المستوى؟

**"فهم متقدم"** يعني:
- ✅ فهمت الإعدادات والنيات (المستوى 2)
- 🟠 الآن تفهم **المنطق الأساسي** (core logic)
- 🟠 تعرف كيف يعمل تصنيف النية بالتفصيل
- 🟠 تعرف كيف يعمل كل وكيل وأداة
- 🟠 تستطيع تعديل كود موجود

**لا يعني**:
- ❌ لا تفهم الـ RAG بالتفصيل
- ❌ لا تعرف كيف يعمل Qdrant
- ❌ لا تستطيع كتابة وكيل جديد من الصفر

---

## 🎯 الأهداف الأربعة بالتفصيل

### الهدف 1: فهم تصنيف النية (3-tier)

**ما يجب أن تفهمه:**

```python
# الملف: src/core/router.py

# ==========================================
# Tier 1: Keyword Matching
# ==========================================

def _keyword_match(self, query: str) -> Optional[RouterResult]:
    query_lower = query.lower()

    for intent, patterns in KEYWORD_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in query_lower:
                return RouterResult(
                    intent=intent,
                    confidence=0.92,  # ← لماذا 0.92؟
                    method="keyword",
                    reason=f"Keyword match: '{pattern}'"
                )

# لماذا 0.92 وليس 1.0؟
# ← لأنه سريع لكن ليس دقيقاً 100%
# ← "ما حكم" قد تكون في سؤال غير فقه (نادر)
# ← 0.92 تعني "واثق جداً لكن ليس تماماً"

# ==========================================
# Tier 2: LLM Classification
# ==========================================

async def _llm_classify(self, query: str) -> RouterResult:
    prompt = self.LLM_CLASSIFIER_PROMPT.format(
        intent_descriptions=intent_descriptions,
        query=query
    )

    response = await self.llm_client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "You are an expert intent classifier..."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,       # ← لماذا 0.0؟
        max_tokens=300,
        response_format={"type": "json_object"}
    )

# لماذا temperature=0.0؟
# ← نريد إجابة دقيقة ومتسقة
# ← نفس السؤال → نفس الإجابة دائماً
# ← لا نريد إبداع من LLM في التصنيف

# ==========================================
# Tier 3: Embedding Fallback
# ==========================================

async def _embedding_classify(self, query: str) -> RouterResult:
    # يحول السؤال لمتجه
    # يقارن مع متجهات مصنفة
    # يرجع أقرب واحد
    return RouterResult(
        intent=Intent.ISLAMIC_KNOWLEDGE,
        confidence=0.6,  # ← لماذا 0.6؟
        method="embedding"
    )

# لماذا 0.6؟
# ← أقل من tier 1 (0.92) و tier 2 (0.75)
# ← لأنه الأقل دقة
# ← لكنه أفضل من لا شيء
```

---

### الهدف 2: فهم تسجيل الوكلاء

**ما يجب أن تفهمه:**

```python
# الملف: src/core/registry.py

# 1. ما هو AgentRegistry؟
#    ← قاموس يسجل كل الوكلاء والأدوات
#    ← يجد الوكيل المناسب لكل نية

# 2. كيف يعمل:

class AgentRegistry:
    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}  # ← قاموس الوكلاء
        self.tools: dict[str, BaseTool] = {}    # ← قاموس الأدوات

    def register_tool(self, name: str, tool: BaseTool):
        self.tools[name] = tool

    def get_for_intent(self, intent: Intent) -> tuple:
        target = INTENT_ROUTING.get(intent)  # ← "fiqh_agent"
        if target in self.agents:
            return self.agents[target], True
        if target in self.tools:
            return self.tools[target], False
        return None, False

# 3. التهيئة:

def initialize_registry():
    _registry = AgentRegistry()

    # تسجيل الأدوات
    _registry.register_tool("zakat_tool", ZakatCalculator())
    _registry.register_tool("inheritance_tool", InheritanceCalculator())
    _registry.register_tool("prayer_tool", PrayerTimesTool())
    _registry.register_tool("hijri_tool", HijriCalendarTool())
    _registry.register_tool("dua_tool", DuaRetrievalTool())

    # تسجيل الوكلاء
    _registry.register_agent("chatbot_agent", ChatbotAgent())

    return _registry
```

---

### الهدف 3: فهم الوكلاء والأدوات

**ما يجب أن تفهمه:**

```python
# الفرق بين Agent و Tool:

Agent (وكيل):
├── يستخدم LLM لتوليد إجابة
├── إجابة قد تختلف (غير حتمي)
├── يحتاج RAG (بحث في وثائق)
├── مثال: FiqhAgent, HadithAgent
└── execute() → AgentOutput(answer, citations)

Tool (أداة):
├── خوارزمية حتمية بدون LLM
├── إجابة دائماً نفسها (حتمي)
├── يحتاج معادلات رياضية
├── مثال: ZakatCalculator, InheritanceCalculator
└── execute() → ToolOutput(result, success)
```

---

### الهدف 4: فهم تدفق RAG

**ما يجب أن تفهمه:**

```
سؤال: "ما حكم صلاة العيد؟"
    ↓
1. FiqhAgent.execute()
    ↓
2. embedding_model.encode_query()
   ← يحول السؤال لمتجه 1024-dim
   ← "ما حكم صلاة العيد؟" → [0.12, -0.34, 0.56, ...]
    ↓
3. hybrid_searcher.search()
   ← يبحث في Qdrant (fiqh_passages collection)
   ← Semantic search: يجد وثائق متشابهة دلالياً
   ← BM25 search: يجد وثائق تحتوي الكلمات
   ← Reciprocal Rank Fusion: يدمج النتيجتين
   ← يرجع top 15 وثيقة
    ↓
4. filter by score threshold
   ← يحتفظ فقط بالوثائق > 0.15
   ← إذا لم يجد، يأخذ top 3 بأي حال
    ↓
5. _format_passages()
   ← ينسق الوثائق للـ LLM
   ← "[C1] صلاة العيد سنة مؤكدة...\nالمصدر: موطأ مالك"
    ↓
6. _generate_with_llm()
   ← يرسل prompt لـ Groq
   ← system: "أنت مساعد إسلامي متخصص في الفقه..."
   ← user: "السؤال: ما حكم صلاة العيد؟\nالنصوص: [C1]..."
   ← temperature=0.1 (دقيق جداً)
   ← يرجع إجابة
    ↓
7. citation_normalizer.normalize()
   ← يحول "موطأ مالك" لـ [C1]
   ← يحول "صحيح البخاري" لـ [C2]
    ↓
8. _add_disclaimer()
   ← يضيف تنويه: "يجب استفتاء عالم متخصص..."
    ↓
AgentOutput(
    answer="صلاة العيد سنة مؤكدة... [C1] [C2]\n\n⚠️ تنبيه...",
    citations=[Citation(C1, ...), Citation(C2, ...)],
    confidence=0.89
)
```

---

## 📝 التمارين بالتفصيل

### تمرين 1: تتبع تصنيف نية

**افتح `router.py` وأجب:**

```python
# السؤال 1: ما هي الـ 3 tiers؟
# الجواب:
#   Tier 1: Keyword matching (0.92 confidence)
#   Tier 2: LLM classification (0.75 threshold)
#   Tier 3: Embedding similarity (0.60 fallback)

# السؤال 2: ما confidence كل tier؟
# الجواب:
#   Keyword: 0.92 (عالي لأنه سريع)
#   LLM: 0.75+ (threshold للقبول)
#   Embedding: 0.60 (منخفض لأنه fallback)

# السؤال 3: لماذا keyword أولاً وليس LLM؟
# الجواب:
#   ← Keyword أسرع (microseconds vs milliseconds)
#   ← Keyword مجاني (لا يحتاج API call)
#   ← LLM أدق لكن مكلف
#   ← نستخدم LLM فقط عندما يفشل keyword

# السؤال 4: ماذا يحدث إذا فشل الـ 3 tiers؟
# الجواب:
#   ← يرجع default fallback
#   ← intent = ISLAMIC_KNOWLEDGE
#   ← confidence = 0.50
#   ← reason = "No classifier matched..."
```

---

### تمرين 2: تتبع وكيل

**افتح `fiqh_agent.py` وأجب:**

```python
# السؤال 1: ما المدخلات؟
# الجواب:
#   AgentInput(
#       query="ما حكم صلاة العيد؟",
#       language="ar",
#       metadata={"madhhab": "shafii"}
#   )

# السؤال 2: ما المخرجات؟
# الجواب:
#   AgentOutput(
#       answer="صلاة العيد سنة مؤكدة...",
#       citations=[Citation(...)],
#       confidence=0.89
#   )

# السؤال 3: كيف يسترجع الوثائق؟
# الجواب:
#   1. embedding_model.encode_query(query)
#   2. hybrid_searcher.search(query, embedding, "fiqh_passages", top_k=15)
#   3. filter by score >= 0.15
#   4. يرجع top 5 وثائق

# السؤال 4: كيف يولد الإجابة؟
# الجواب:
#   1. يبني prompt:
#      system: "أنت مساعد إسلامي متخصص في الفقه..."
#      user: "السؤال: ما حكم صلاة العيد؟\nالنصوص: [C1]..."
#   2. يرسل لـ Groq
#   3. يستلم إجابة
#   4. يرجع

# السؤال 5: كيف يضيف الاقتباسات؟
# الجواب:
#   1. citation_normalizer.normalize(answer)
#   2. يحول "موطأ مالك" لـ [C1]
#   3. citation_normalizer.get_citations()
#   4. يرجع مع AgentOutput
```

---

### تمرين 3: تتبع أداة

**افتح `zakat_calculator.py` وأجب:**

```python
# السؤال 1: ما أنواع الزكاة المدعومة؟
# الجواب:
#   ZakatType.WEALTH        # المال
#   ZakatType.GOLD          # الذهب
#   ZakatType.SILVER        # الفضة
#   ZakatType.TRADE_GOODS   # عروض التجارة
#   ZakatType.STOCKS        # الأسهم
#   ZakatType.LIVESTOCK     # الماشية
#   ZakatType.CROPS         # الزروع

# السؤال 2: ما هو nisab؟
# الجواب:
#   ← الحد الأدنى للزكاة
#   ← الذهب: 85 جرام
#   ← الفضة: 595 جرام
#   ← إذا مالك < nisab → لا زكاة
#   ← إذا مالك >= nisab → زكاة 2.5%

# السؤال 3: كيف يحسب الزكاة على الذهب؟
# الجواب:
#   gold_value = gold_grams * gold_price_per_gram
#   if gold_value >= nisab_gold:
#       zakat = gold_value * 0.025

# السؤال 4: كيف يحسب الزكاة على الفضة؟
# الجواب:
#   silver_value = silver_grams * silver_price_per_gram
#   if silver_value >= nisab_silver:
#       zakat = silver_value * 0.025
```

---

### تمرين 4: رسم تدفق RAG

**المطلوب:**

```
ارسم diagram يوضح:

سؤال → تصنيف → وكيل → استرجاع → توليد → إجابة

التفصيل:

┌──────────────┐
│ سؤال المستخدم │
└──────┬───────┘
       ↓
┌──────────────┐
│ تصنيف النية   │  router.py
│ fiqh (0.92)  │
└──────┬───────┘
       ↓
┌──────────────┐
│ FiqhAgent    │  fiqh_agent.py
└──────┬───────┘
       ↓
┌──────────────┐
│ Embedding    │  embedding_model.py
│ encode_query │
└──────┬───────┘
       ↓
┌──────────────┐
│ Hybrid       │  hybrid_search.py
│ Search       │
└──────┬───────┘
       ↓
┌──────────────┐
│ LLM          │  Groq/OpenAI
│ Generate     │
└──────┬───────┘
       ↓
┌──────────────┐
│ Citation     │  citation.py
│ Normalize    │
└──────┬───────┘
       ↓
┌──────────────┐
│ إجابة        │  AgentOutput
│ + اقتباسات   │
└──────────────┘
```

---

## ✅ علامة إكمال المستوى 3

تستطيع القول "أكملت المستوى 3" عندما:

```
✅ تستطيع شرح الـ 3 tiers بالتفصيل
✅ تعرف لماذا كل tier confidence مختلف
✅ تستطيع تتبع وكيل من execute() إلى AgentOutput
✅ تعرف الفرق بين Agent و Tool
✅ تستطيع رسم تدفق RAG من الذاكرة
✅ تعرف كيف يحسب ZakatCalculator الزكاة
```

---

## ⏱️ الوقت المتوقع

```
اليوم 11: قراءة router.py + تمرين تتبع تصنيف     (3 ساعات)
اليوم 12: قراءة registry.py                       (2 ساعات)
اليوم 13: قراءة citation.py                       (3 ساعات)
اليوم 14: قراءة base.py (agents)                  (2 ساعات)
اليوم 15: قراءة chatbot_agent.py                  (2 ساعات)
اليوم 16: قراءة fiqh_agent.py                     (3 ساعات)
اليوم 17: قراءة base.py (tools)                   (1 ساعة)
اليوم 18: قراءة zakat_calculator.py               (3 ساعات)
اليوم 19-20: مراجعة + حل التمارين + رسم diagrams (4 ساعات)
                                                  ───────
المجموع: 23-25 ساعة على 10 أيام
```

---

# المستوى 4: فهم عميق (اليوم 21-30)

## 📍 ما معنى هذا المستوى؟

**"فهم عميق"** يعني:
- ✅ فهمت المنطق الأساسي (المستوى 3)
- 🔴 الآن تفهم **البنية التحتية** (infrastructure)
- 🔴 تعرف كيف يعمل الـ RAG بالتفصيل
- 🔴 تعرف كيف يعمل Qdrant والبحث
- 🔴 تعرف كيف يعمل خط إنتاج القرآن

**لا يعني**:
- ❌ لا تستطيع إضافة ميزة جديدة من الصفر
- ❌ لا تفهم كل التفاصيل الدقيقة
- ❌ لا تستطيع مراجعة كود المحترفين

---

## 🎯 الأهداف الأربعة بالتفصيل

### الهدف 1: فهم نظام التضمين (embeddings)

**ما يجب أن تفهمه:**

```python
# الملف: src/knowledge/embedding_model.py

# 1. ما هو Embedding؟
#    ← تحويل النص لمتجه رقمي
#    ← "ما حكم صلاة العيد؟" → [0.12, -0.34, 0.56, ...]
#    ← نصوص متشابهة = متجهات متشابهة

# 2. ما النموذج المستخدم؟
#    ← BAAI/bge-m3
#    ← 1024 dimensions (أبعاد)
#    ← 8192 tokens (الحد الأقصى)
#    ← يدعم 100+ لغة

# 3. كيف يعمل:

class EmbeddingModel:
    async def load_model(self):
        # يحمل النموذج في الذاكرة
        self.model = AutoModel.from_pretrained("BAAI/bge-m3")
        self.tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3")

    async def encode_query(self, query: str) -> list[float]:
        # يحول النص لمتجه
        inputs = self.tokenizer(query, return_tensors="pt")
        outputs = self.model(**inputs)
        embedding = outputs.last_hidden_state[:, 0].tolist()
        return embedding  # [0.12, -0.34, ...] (1024 رقم)

# 4. لماذا caching؟
#    ← توليد المتجهات بطيء (~6 ثواني/وثيقة على CPU)
#    ← نحفظ في Redis لتجنب إعادة التوليد
#    ← إذا نفس النص → نفس المتجه
```

---

### الهدف 2: فهم Qdrant والبحث

**ما يجب أن تفهمه:**

```python
# الملف: src/knowledge/vector_store.py

# 1. ما هو Qdrant؟
#    ← قاعدة بيانات متخصصة في المتجهات
#    ← بحث سريع جداً (ملايين المتجهات في ميلي ثواني)
#    ← يدعم البحث الدلالي (semantic search)

# 2. المجموعات العشر:

collection_name           ← الوثائق
─────────────────────────────────────────────
fiqh_passages             ← كتب الفقه (10,132+ متجه)
hadith_passages           ← الأحاديث (160+ متجه)
quran_tafsir              ← التفسير
general_islamic           ← معارف إسلامية (5+ متجه)
duas_adhkar               ← الأدعية (10 متجه)
aqeedah_passages          ← العقيدة (90+ متجه)
seerah_passages           ← السيرة (100+ متجه)
islamic_history_passages  ← التاريخ (270+ متجه)
arabic_language_passages  ← اللغة العربية (240+ متجه)
spirituality_passages     ← الروحانيات (150+ متجه)

# 3. كيف يعمل البحث:

class VectorStore:
    async def search(
        self,
        collection: str,
        query_embedding: list[float],
        top_k: int = 15
    ) -> list[dict]:
        # يبحث عن أقرب المتجهات
        results = self.client.query_points(
            collection_name=collection,
            query=query_embedding,
            limit=top_k
        )
        return results  # top 15 وثيقة
```

---

### الهدف 3: فهم البحث المختلط

**ما يجب أن تفهمه:**

```python
# الملف: src/knowledge/hybrid_search.py

# 1. ما هو Hybrid Search؟
#    ← دمج نوعين من البحث:
#      أ) Semantic search (دلالي): يفهم المعنى
#      ب) BM25 search (كلمات): يتطابق مع الكلمات

# 2. لماذا دمج؟
#    ← Semantic: يجد "صلاة العيد" حتى لو السؤال "حكم العيد"
#    ← BM25: يتطابق مع الكلمات الدقيقة
#    ← الجمع = نتائج أفضل

# 3. كيف يدمج: Reciprocal Rank Fusion (RRF)

# مثال:
# Semantic results:  [doc1 (0.85), doc2 (0.78), doc3 (0.72)]
# BM25 results:      [doc2 (0.90), doc1 (0.82), doc4 (0.75)]

# RRF formula:
# score(doc) = 1 / (k + rank_semantic) + 1 / (k + rank_bm25)
# حيث k = 60

# doc1: 1/(60+1) + 1/(60+2) = 0.0164 + 0.0159 = 0.0323
# doc2: 1/(60+2) + 1/(60+1) = 0.0159 + 0.0164 = 0.0323
# doc3: 1/(60+3) + 0         = 0.0159
# doc4: 0 + 1/(60+3)         = 0.0159

# Final ranking: doc1 = doc2 > doc3 = doc4
```

---

### الهدف 4: فهم خط إنتاج القرآن

**ما يجب أن تفهمه:**

```python
# الملفات: src/quran/*.py

# 1. verse_retrieval.py
#    ← البحث عن آيات محددة
#    ← "ما هي آية الكرسي؟" → Quran 2:255

# 2. nl2sql.py
#    ← تحويل اللغة الطبيعية إلى SQL
#    ← "كم مرة ذكرت كلمة الرحمة؟" →
#      SELECT COUNT(*) FROM quran_verses WHERE text LIKE '%الرحمة%'

# 3. quotation_validator.py
#    ← التحقق من اقتباسات القرآن
#    ← "الله لا إله إلا هو" → ✅ صحيح
#    ← "الله واحد" → ❌ ليس آية

# 4. التدفق:

سؤال عن القرآن
    ↓
QuranSubRouter.classify()
    ↓
VERSE_LOOKUP → verse_retrieval.py
INTERPRETATION → tafsir_retrieval.py
ANALYTICS → nl2sql.py
QUOTATION_VALIDATION → quotation_validator.py
```

---

## ✅ علامة إكمال المستوى 4

تستطيع القول "أكملت المستوى 4" عندما:

```
✅ تستطيع شرح ما هو embedding ولماذا مهم
✅ تعرف كيف يعمل BAAI/bge-m3
✅ تعرف كيف يعمل Qdrant والبحث
✅ تعرف ما هو Hybrid Search ولماذا ندمج
✅ تعرف ما هو Reciprocal Rank Fusion
✅ تستطيع تفسير لماذا استرجاع معين أرجع نتيجة معينة
```

---

# المستوى 5: إتقان (اليوم 31+)

## 📍 ما معنى هذا المستوى؟

**"إتقان"** يعني:
- ✅ فهمت كل شيء (المستويات 1-4)
- 🟣 الآن تستطيع **إضافة ميزات جديدة**
- 🟣 تستطيع **مراجعة كود الآخرين**
- 🟣 تستطيع **شرح المشروع لغيرك**
- 🟣 تستطيع **تحسين الأداء**

**هذا مستوى مستمر**:
- لا ينتهي أبداً
- كل يوم تتعلم شيء جديد
- كل ميزة جديدة تضيفها تزيد خبرتك

---

## 🎯 الأهداف الخمسة بالتفصيل

### الهدف 1: فهم كل الوكلاء

```python
# الوكلاء المنفذين:
# 1. ChatbotAgent      ← التحيات (template-based)
# 2. FiqhAgent         ← الفقه (RAG كامل)
# 3. HadithAgent       ← الحديث (RAG كامل)
# 4. GeneralIslamicAgent ← معارف عامة (RAG كامل)
# 5. SeerahAgent       ← السيرة (RAG كامل)

# الوكلاء المحذوفين (fallback إلى general_islamic_agent):
# 6. TafsirAgent       ← التفسير (محذوف)
# 7. AqeedahAgent      ← العقيدة (محذوف)
# 8. UsulFiqhAgent     ← أصول الفقه (محذوف)
# 9. IslamicHistoryAgent ← التاريخ (محذوف)
# 10. ArabicLanguageAgent ← اللغة العربية (محذوف)
```

---

### الهدف 2: فهم كل الأدوات

```python
# الأدوات الخمس:
# 1. ZakatCalculator         ← الزكاة (7 أنواع، 4 مذاهب)
# 2. InheritanceCalculator   ← المواريث (فروض، تعصيب، عول، رد)
# 3. PrayerTimesTool         ← أوقات الصلاة (6 طرق، اتجاه القبلة)
# 4. HijriCalendarTool       ← التاريخ الهجري (Umm al-Qura)
# 5. DuaRetrievalTool        ← الأدعية (Hisn al-Muslim)
```

---

### الهدف 3: فهم كل الـ endpoints

```python
# الـ 18 endpoint:

# Main query (1):
POST /api/v1/query

# Tools (5):
POST /api/v1/tools/zakat
POST /api/v1/tools/inheritance
POST /api/v1/tools/prayer-times
POST /api/v1/tools/hijri
POST /api/v1/tools/duas

# Quran (6):
GET  /api/v1/quran/surahs
GET  /api/v1/quran/surahs/{n}
GET  /api/v1/quran/ayah/{s}:{a}
POST /api/v1/quran/search
POST /api/v1/quran/validate
POST /api/v1/quran/analytics

# RAG (3):
POST /api/v1/rag/fiqh
POST /api/v1/rag/general
GET  /api/v1/rag/stats

# Health (2):
GET  /health
GET  /ready
```

---

### الهدف 4: القدرة على إضافة ميزة جديدة

**تمرين تطبيقي: أضف intent جديد `fatwa`**

```python
# الخطوة 1: أضف النية في intents.py

class Intent(str, Enum):
    # ... (الأنواع الموجودة)
    FATWA = "fatwa"  # ← جديد

INTENT_ROUTING = {
    # ... (التوجيه الموجود)
    Intent.FATWA: "fatwa_agent",  # ← جديد
}

KEYWORD_PATTERNS = {
    # ... (الأنماط الموجودة)
    Intent.FATWA: [  # ← جديد
        "فتوى",
        "fatwa",
        "ما رأيكم في",
        "ما حكمكم في",
    ],
}

# الخطوة 2: أنشئ الوكيل الجديد

# src/agents/fatwa_agent.py
from src.agents.base import BaseAgent, AgentInput, AgentOutput
from src.knowledge.embedding_model import EmbeddingModel
from src.knowledge.vector_store import VectorStore
from src.knowledge.hybrid_search import HybridSearcher
from src.core.citation import CitationNormalizer

class FatwaAgent(BaseAgent):
    name = "fatwa_agent"

    def __init__(self):
        self.embedding_model = None
        self.vector_store = None
        self.hybrid_searcher = None
        self.citation_normalizer = CitationNormalizer()

    async def execute(self, input: AgentInput) -> AgentOutput:
        # يطبق نفس RAG flow مثل FiqhAgent
        # لكن يستخدم fatwa_passages collection
        pass

# الخطوة 3: سجل الوكيل في registry.py

from src.agents.fatwa_agent import FatwaAgent

def initialize_registry():
    # ... (التسجيل الموجود)
    _registry.register_agent("fatwa_agent", FatwaAgent())
```

---

### الهدف 5: القدرة على مراجعة كود الآخرين

**تمرين تطبيقي: راجع كود FiqhAgent**

```python
# نقاط القوة:
✅ يستخدم lazy initialization
✅ يستخدم hybrid search
✅ يضيف citation normalization
✅ يضيف disclaimer
✅ يتعامل مع الأخطاء

# نقاط الضعف:
❌ تكرار الكود مع HadithAgent و GeneralIslamicAgent
❌ hard-coded collection name ("fiqh_passages")
❌ no caching للـ embeddings
❌ no timeout للـ LLM call

# مقترحات التحسين:
1. استخدم BaseRAGAgent لتقليل التكرار
2. اجعل collection name configurable
3. أضف caching للـ embeddings
4. أضف timeout للـ LLM call
```

---

## ✅ علامة إكمال المستوى 5

تستطيع القول "أكملت المستوى 5" عندما:

```
✅ أضفت intent جديد من الصفر
✅ أضفت tool جديد من الصفر
✅ أضفت agent جديد من الصفر
✅ راجعت كود شخص آخر
✅ شرحت المشروع لمبرمج آخر
✅ حسنت أداء جزء من المشروع
✅ كتبت اختبار يغطي 100% من ملف
```

---

## ⏱️ الوقت المتوقع

```
المستوى 5 لا ينتهي!

لكن كبداية:
اليوم 31-35: فهم الوكلاء المتبقية           (10 ساعات)
اليوم 36-40: فهم الأدوات المتبقية           (10 ساعات)
اليوم 41-45: فهم الـ endpoints المتبقية     (10 ساعات)
اليوم 46-50: إضافة intent جديد              (10 ساعات)
اليوم 51-55: إضافة tool جديد                (10 ساعات)
اليوم 56-60: مراجعة كود + تحسينات           (10 ساعات)
                                                  ───────
المجموع: 60 ساعة على 30 يوم (للبداية فقط)
```

---

## 💡 نصائح ذهبية لكل مستوى

### المستوى 0 (مبتدئ)

```
✅ جهز البيئة فقط
✅ لا تقرأ كود بعد
✅ استعد نفسياً
✅ خذ وقتك
```

### المستوى 1 (فهم عام)

```
✅ اقرأ الشروحات
✅ شغل التطبيق
✅ ارسم خرائط
✅ لا تحاول فهم كل شيء
```

### المستوى 2 (فهم متوسط)

```
✅ اقرأ الكود مع الشرح
✅ تتبع الإعدادات
✅ جرب Swagger UI
✅ اسأل "لماذا؟"
```

### المستوى 3 (فهم متقدم)

```
✅ ارسم diagrams
✅ تتبع البيانات
✅ اقرأ الاختبارات
✅ قارن الوكلاء
```

### المستوى 4 (فهم عميق)

```
✅ افهم tradeoffs
✅ لماذا هذا التصميم؟
✅ اقترح تحسينات
✅ اقرأ التوثيق الخارجي
```

### المستوى 5 (إتقان)

```
✅ أضف ميزات جديدة
✅ راجع كود الآخرين
✅ اشرح لغيرك
✅ علم شخص آخر
```

---

## 🎓 الخلاصة النهائية

هذه الخطة تأخذك من **الصفر** إلى **الإتقان** في **60 يوم**:

```
المستوى 0: تجهيز البيئة         (ساعة واحدة)
المستوى 1: فهم عام               (10 ساعات / 3 أيام)
المستوى 2: فهم متوسط             (17 ساعة / 7 أيام)
المستوى 3: فهم متقدم             (25 ساعة / 10 أيام)
المستوى 4: فهم عميق              (30 ساعة / 10 أيام)
المستوى 5: إتقان                 (60 ساعة / 30 يوم)
                              ────────────────────
المجموع: 142 ساعة / 60 يوم
```

**المفتاح:**
1. اتبع الترتيب
2. لا تقفز
3. طبق التمارين
4. اسأل الأسئلة
5. اقرأ الكود بنفسك

**الهدف النهائي:**
تستطيع فهم، تعديل، وإضافة ميزات جديدة للمشروع بثقة.

---

**🚀 ابدأ الآن:** اقرأ [`01_project_overview.md`](01_project_overview.md)

**📖 الدليل الكامل:** [`docs/mentoring/`](docs/mentoring/)

---

## 🏗️ الإصدار v2 - مسار تعلم جديد

### ما الجديد في v2؟
مع الإصدار v2، появиت مسارات جديدة مهمة:

```
src/agents/collection/     ← 10 وكلاء CollectionAgent جدد
src/retrieval/            ← طبقة الاسترجاع
src/verification/         ← طبقة التحقق
src/application/routing/ ← التوجيه الجديد
src/infrastructure/qdrant/← عميل Qdrant
src/generation/           ← طبقة التوليد

config/agents/            ← 10 ملفات YAML
prompts/                  ← ملفات Prompts منفصلة
```

### المسار المقترح لـ v2

| المستوى | المحتوى | الوقت |
|---------|---------|-------|
| **v2 Basics** | فهم CollectionAgent + التكوين YAML | 5 ساعات |
| **v2 Retrieval** | طبقة الاسترجاع + الاستراتيجيات | 4 ساعات |
| **v2 Routing** | IntentRouter + Planner + Executor | 4 ساعات |
| **v2 Verification** | نظام التحقق + Trace | 3 ساعات |

### الموارد
- [`02_folder_structure.md`](02_folder_structure.md) - المعمارية الكاملة
- [`V2_MIGRATION_NOTES.md`](../../8-development/refactoring/V2_MIGRATION_NOTES.md) - دليل الانتقال

---

**مُعد الشرح:** AI Mentor System  
**التاريخ:** أبريل 2026  
**الإصدار:** 1.0  
**الحالة:** ✅ شرح تفصيلي لكل المستويات
