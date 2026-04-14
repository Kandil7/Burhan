# 🚀 مسار تشغيل المشروع End-to-End - شرح تفصيلي كامل

## 🕌 مقدمة

هذا الملف يشرح **رحلة تشغيل مشروع Athar** من البداية (عندما تكتب الأمر) للنهاية (عندما ترى الإجابة).

---

# المرحلة 0: قبل التشغيل (الإعداد)

## 📍 ما يحدث قبل أن تضغط Enter

### 1️⃣ بنية المشروع

```
Athar/
│
├── src/                          ← الكود الأساسي
│   ├── api/                      ← واجهة البرمجة (FastAPI)
│   │   ├── main.py               ← نقطة الدخول الرئيسية
│   │   ├── routes/               ← نقاط الدخول (endpoints)
│   │   ├── middleware/           ← طبقات الأمان
│   │   └── schemas/              ← نماذج البيانات
│   │
│   ├── config/                   ← الإعدادات
│   │   ├── settings.py           ← إعدادات التطبيق
│   │   ├── intents.py            ← أنواع النية
│   │   └── constants.py          ← الثوابت
│   │
│   ├── core/                     ← المنطق الأساسي
│   │   ├── router.py             ← تصنيف النية
│   │   ├── registry.py           ← تسجيل الوكلاء
│   │   └── citation.py           ← تطبيع الاقتباسات
│   │
│   ├── agents/                   ← الوكلاء المتخصصون
│   │   ├── base.py               ← الفئة الأساسية
│   │   ├── chatbot_agent.py      ← وكيل الترحيب
│   │   ├── fiqh_agent.py         ← وكيل الفقه
│   │   └── general_islamic_agent.py ← وكيل المعارف العامة
│   │
│   ├── tools/                    ← الأدوات الحتمية
│   │   ├── zakat_calculator.py   ← حاسبة الزكاة
│   │   └── ...                   ← أدوات أخرى
│   │
│   ├── knowledge/                ← بنية الـ RAG
│   │   ├── embedding_model.py    ← نموذج التضمين
│   │   ├── vector_store.py       ← قاعدة المتجهات
│   │   └── hybrid_search.py      ← البحث المختلط
│   │
│   └── infrastructure/           ← الخدمات الخارجية
│       ├── llm_client.py         ← عميل LLM
│       ├── database.py           ← قاعدة البيانات
│       └── redis.py              ← التخزين المؤقت
│
├── docker/                       ← Docker Compose
│   └── docker-compose.dev.yml    ← 5 خدمات
│
├── pyproject.toml                ← التبعيات
├── .env                          ← متغيرات البيئة
└── Makefile                      ← أوامر البناء
```

---

### 2️⃣ المتطلبات الأساسية

**قبل تشغيل المشروع، تحتاج:**

```bash
# 1. Python 3.12+
python --version
# لماذا؟ المشروع يستخدم ميزات Python الحديثة (type hints, async/await)

# 2. Poetry (إدارة التبعيات)
poetry --version
# لماذا؟ يعزل التبعيات في بيئة افتراضية

# 3. Docker + Docker Compose
docker --version
docker compose version
# لماذا؟ يشغل 5 خدمات (PostgreSQL, Qdrant, Redis, API, Frontend)

# 4. Git
git --version
# لماذا؟ لاستنساخ المشروع
```

---

### 3️⃣ ملف `.env` (الإعدادات)

**ما يحتويه:**

```bash
# ==========================================
# Application
# ==========================================
APP_NAME=Athar
APP_ENV=development          ← بيئة التطوير (ليس production)
DEBUG=true                   ← وضع التصحيح مفعل
SECRET_KEY=change-this-in-production

# ==========================================
# Database (PostgreSQL 16)
# ==========================================
DATABASE_URL=postgresql+asyncpg://athar:athar_password@localhost:5432/athar_db
#            نوع القاعدة        مستخدم   كلمة مرور       host     port   اسم القاعدة
DATABASE_POOL_SIZE=10          ← عدد الاتصالات في الـ pool

# ==========================================
# Redis
# ==========================================
REDIS_URL=redis://localhost:6379/0
#         بروتوكول   host     port   رقم قاعدة البيانات

# ==========================================
# Qdrant (Vector Database)
# ==========================================
QDRANT_URL=http://localhost:6333
# لماذا؟ قاعدة بيانات المتجهات للـ RAG

# ==========================================
# LLM Provider
# ==========================================
LLM_PROVIDER=groq              ← مزود الـ LLM
GROQ_API_KEY=gsk_xxxxx         ← مفتاح API
GROQ_MODEL=qwen/qwen3-32b      ← النموذج المستخدم
LLM_TEMPERATURE=0.1            ← حرارة منخفضة = إجابات دقيقة

# ==========================================
# Embeddings
# ==========================================
EMBEDDING_MODEL=BAAI/bge-m3    ← نموذج التضمين
EMBEDDING_DIMENSION=1024       ← أبعاد المتجه

# ==========================================
# CORS
# ==========================================
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
# لماذا؟ يسمح للـ frontend بالاتصال
```

**لماذا مهم؟**
- بدون `.env`، يستخدم الإعدادات الافتراضية
- الإعدادات الافتراضية قد لا تعمل عندك
- خاصة `GROQ_API_KEY` (يجب أن تكون مفتاحك)

---

# المرحلة 1: التثبيت (`make install-dev`)

## 📍 ما يحدث عند تشغيل `make install-dev`

### 1️⃣ قراءة Makefile

```makefile
install-dev:
	poetry install --with dev
```

**ما يعني:**
- `make install-dev` → ينفذ `poetry install --with dev`

---

### 2️⃣ Poetry يقرأ `pyproject.toml`

```toml
[tool.poetry]
name = "athar"
version = "0.5.0"
description = "Islamic QA System"

[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.115"           ← إطار عمل الويب
uvicorn = "^0.32"            ← خادم ASGI
pydantic = "^2.9"            ← نماذج البيانات
pydantic-settings = "^2.6"   ← إعدادات البيئة
sqlalchemy = "^2.0"          ← ORM لقاعدة البيانات
asyncpg = "^0.30"            ← driver لـ PostgreSQL
redis = "^5.2"               ← عميل Redis
qdrant-client = "^1.12"      ← عميل Qdrant
openai = "^1.58"             ← عميل OpenAI
httpx = "^0.27"              ← HTTP client
structlog = "^24.4"          ← تسجيل منظم
pyyaml = "^6.0"              ← YAML parser

[tool.poetry.group.dev.dependencies]
pytest = "^8.3"              ← اختبار
pytest-asyncio = "^0.24"     ← اختبار async
pytest-cov = "^6.0"          ← تغطية الاختبار
ruff = "^0.7"                ← linting
mypy = "^1.13"               ← type checking

[tool.poetry.group.rag.dependencies]
torch = "^2.5"               ← PyTorch للـ embeddings
transformers = "^4.46"       ← نماذج HuggingFace
```

---

### 3️⃣ ما يحدث بالتفصيل

```bash
$ poetry install --with dev

# الخطوة 1: ينشئ بيئة افتراضية
# ~/.cache/pypoetry/virtualenvs/athar-xxxxx-py3.12/

# الخطوة 2: يقرأ poetry.lock
# ملف يحتوي كل التبعيات مع إصداراتها الدقيقة
# يضمن أن كل المطورين يستخدمون نفس الإصدارات

# الخطوة 3: يحمل التبعيات الأساسية
# └── fastapi 0.115.0
# └── uvicorn 0.32.0
# └── pydantic 2.9.0
# └── sqlalchemy 2.0.36
# └── asyncpg 0.30.0
# └── redis 5.2.0
# └── qdrant-client 1.12.0
# └── openai 1.58.0
# └── httpx 0.27.0
# └── structlog 24.4.0
# └── pyyaml 6.0.2
# └── ... (30+ مكتبة)

# الخطوة 4: يحمل تبعيات التطوير (--with dev)
# └── pytest 8.3.3
# └── pytest-asyncio 0.24.0
# └── pytest-cov 6.0.0
# └── ruff 0.7.0
# └── mypy 1.13.0

# الخطوة 5: ينشئ ملفات .pth
# تسمح لـ Python بإيجاد المكتبات في البيئة الافتراضية

# الخطوة 6: يطبع النتيجة
# Installing dependencies from lock file...
# Package operations: 85 installs, 0 updates, 0 removals
# ✓ Installed fastapi-0.115.0
# ✓ Installed uvicorn-0.32.0
# ...
# ✓ Installing the current project: athar@0.5.0
```

---

### 4️⃣ التحقق من التثبيت

```bash
# تحقق من أن Poetry ثبت كل شيء
poetry show

# يجب أن ترى 85+ مكتبة
# fastapi        0.115.0 FastAPI framework
# uvicorn        0.32.0  ASGI server
# pydantic       2.9.0   Data validation
# ...

# تحقق من أن المكتبات تعمل
poetry run python -c "import fastapi; print(fastapi.__version__)"
# يجب أن يطبع: 0.115.0
```

---

# المرحلة 2: تشغيل الخدمات (`make docker-up`)

## 📍 ما يحدث عند تشغيل `make docker-up`

### 1️⃣ قراءة Makefile

```makefile
docker-up:
	docker compose -f docker/docker-compose.dev.yml up -d
```

**ما يعني:**
- `make docker-up` → ينفذ `docker compose -f docker/docker-compose.dev.yml up -d`
- `-f docker/docker-compose.dev.yml` → يستخدم هذا الملف
- `up` → يشغل الخدمات
- `-d` → في الخلفية (detached mode)

---

### 2️⃣ قراءة `docker-compose.dev.yml`

```yaml
services:
  # ==========================================
  # PostgreSQL 16 (قاعدة البيانات)
  # ==========================================
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: athar_db         ← اسم قاعدة البيانات
      POSTGRES_USER: athar          ← اسم المستخدم
      POSTGRES_PASSWORD: athar_password  ← كلمة المرور
    ports:
      - "5432:5432"                 ← يعرض المنفذ 5432
    volumes:
      - postgres_data:/var/lib/postgresql/data  ← حفظ البيانات
      - ./docker/init-db:/docker-entrypoint-initdb.d  ← سكريبتات التهيئة
    networks:
      - athar-network

  # ==========================================
  # Qdrant (قاعدة المتجهات)
  # ==========================================
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"                 ← يعرض المنفذ 6333
      - "6334:6334"                 ← يعرض المنفذ 6334 (gRPC)
    volumes:
      - qdrant_data:/qdrant/storage  ← حفظ البيانات
    networks:
      - athar-network

  # ==========================================
  # Redis 7 (التخزين المؤقت)
  # ==========================================
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"                 ← يعرض المنفذ 6379
    volumes:
      - redis_data:/data            ← حفظ البيانات
    networks:
      - athar-network

  # ==========================================
  # FastAPI API (تطبيق Athar)
  # ==========================================
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    ports:
      - "8000:8000"                 ← يعرض المنفذ 8000
    environment:
      - DATABASE_URL=postgresql+asyncpg://athar:athar_password@postgres:5432/athar_db
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - postgres                    ← ينتظر PostgreSQL
      - redis                       ← ينتظر Redis
      - qdrant                      ← ينتظر Qdrant
    networks:
      - athar-network

  # ==========================================
  # Next.js Frontend (اختياري)
  # ==========================================
  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/Dockerfile.frontend
    ports:
      - "3000:3000"                 ← يعرض المنفذ 3000
    depends_on:
      - api                         ← ينتظر API
    networks:
      - athar-network
    profiles:
      - frontend                    ← لا يشغل إلا إذا طلبته

volumes:
  postgres_data:                    ← volume للبيانات
  qdrant_data:
  redis_data:

networks:
  athar-network:
    driver: bridge                  ← شبكة افتراضية
```

---

### 3️⃣ ما يحدث بالتفصيل

```bash
$ docker compose -f docker/docker-compose.dev.yml up -d

# الخطوة 1: ينشئ شبكة athar-network
# لماذا؟ حتى تستطيع الخدمات التواصل مع بعضها
# كل الخدمات على نفس الشبكة → تستطيع استخدام أسماء الخدمات كـ hostnames

# الخطوة 2: ينشئ volumes
# postgres_data:  ← لحفظ بيانات PostgreSQL
# qdrant_data:    ← لحفظ بيانات Qdrant
# redis_data:     ← لحفظ بيانات Redis
# لماذا؟ حتى لا تضيع البيانات عند إيقاف الخدمات

# الخطوة 3: يشغل PostgreSQL
# └── يحمل صورة postgres:16-alpine
# └── ينشئ قاعدة بيانات athar_db
# └── ينشئ مستخدم athar
# └── يعرض المنفذ 5432 على localhost
# └── ينفذ سكريبتات التهيئة من docker/init-db/

# الخطوة 4: يشغل Qdrant
# └── يحمل صورة qdrant/qdrant:latest
# └── يعرض المنفذ 6333 (HTTP) و 6334 (gRPC)
# └── ينشئ storage في /qdrant/storage

# الخطوة 5: يشغل Redis
# └── يحمل صورة redis:7-alpine
# └── يعرض المنفذ 6379
# └── يحفظ البيانات في /data

# الخطوة 6: يشغل API (إذا كان موجوداً)
# └── يبني Dockerfile.api
# └── ينتظر حتى تكون postgres, redis, qdrant جاهزة
# └── يعرض المنفذ 8000

# الخطوة 7: يطبع النتيجة
# ✔ Network athar-network Created
# ✔ Volume postgres_data Created
# ✔ Volume qdrant_data Created
# ✔ Volume redis_data Created
# ✔ Container postgres Started
# ✔ Container qdrant Started
# ✔ Container redis Started
```

---

### 4️⃣ التحقق من الخدمات

```bash
# تحقق من أن الخدمات تعمل
docker compose -f docker/docker-compose.dev.yml ps

# يجب أن ترى:
# NAME           STATUS         PORTS
# postgres       Up (healthy)   0.0.0.0:5432->5432/tcp
# qdrant         Up             0.0.0.0:6333->6333/tcp
# redis          Up             0.0.0.0:6379->6379/tcp

# تحقق من أن PostgreSQL جاهز
docker compose -f docker/docker-compose.dev.yml exec postgres pg_isready
# يجب أن يطبع: /var/run/postgresql:5432 - accepting connections

# تحقق من أن Qdrant جاهز
curl http://localhost:6333/healthz
# يجب أن يطبع: {"status":"ok"}

# تحقق من أن Redis جاهز
docker compose -f docker/docker-compose.dev.yml exec redis redis-cli ping
# يجب أن يطبع: PONG
```

---

# المرحلة 3: تهجير قاعدة البيانات (`make db-migrate`)

## 📍 ما يحدث عند تشغيل `make db-migrate`

### 1️⃣ قراءة Makefile

```makefile
db-migrate:
	poetry run alembic upgrade head
```

**ما يعني:**
- `make db-migrate` → ينفذ `poetry run alembic upgrade head`
- `poetry run` → يشغل داخل البيئة الافتراضية
- `alembic upgrade head` → يطبق كل المهاجرين

---

### 2️⃣ ما هو Alembic؟

```
Alembic هو أداة لإدارة تهجير قاعدة البيانات (database migrations).

ما يعني "تهجير"؟
← تغيير بنية قاعدة البيانات بشكل منظم
← مثال: إضافة جدول جديد، إضافة عمود، تعديل نوع بيانات

لماذا نحتاجه؟
← يضمن أن كل البيئات (dev, staging, production) لها نفس البنية
← يسمح بالرجوع إلى نسخة سابقة (rollback)
← يتتبع التغييرات في Git
```

---

### 3️⃣ بنية مجلد migrations

```
migrations/
├── alembic.ini                   ← إعدادات Alembic
├── env.py                        ← بيئة التنفيذ
├── script.py.mako                ← قالب المهايير
└── versions/
    ├── 001_initial_schema.sql    ← أول مهاير
    ├── 002_add_tafsir_table.sql  ← مهاير ثاني
    └── ...
```

---

### 4️⃣ ما يحدث بالتفصيل

```bash
$ poetry run alembic upgrade head

# الخطوة 1: يقرأ alembic.ini
# └── يحدد رابط قاعدة البيانات
#     sqlalchemy.url = postgresql+asyncpg://athar:athar_password@localhost:5432/athar_db

# الخطوة 2: يتصل بـ PostgreSQL
# └── يحاول الاتصال
# └── إذا نجح: ✓ Connected
# └── إذا فشل: ✗ Error (تأكد أن Docker يعمل)

# الخطوة 3: يتحقق من جدول alembic_version
# └── إذا لم يوجد: ينشئه
# └── يحتوي على رقم آخر مهاير مُطبق
# └── مثال: 000 (لا شيء مُطبق)

# الخطوة 4: يجد المهايرات غير المُطبقة
# └── يقرأ مجلد versions/
# └── يقارن مع alembic_version
# └── يجد: 001_initial_schema.sql (غير مُطبق)

# الخطوة 5: يطبق 001_initial_schema.sql
# └── ينشئ جداول:
#     ├── surahs                   ← جدول السور
#     ├── ayahs                    ← جدول الآيات
#     ├── translations             ← جدول الترجمات
#     ├── tafsirs                  ← جدول التفاسير
#     └── alembic_version          ← جدول تتبع المهايرات

# الخطوة 6: يحدث alembic_version
# └── يغير من 000 إلى 001

# الخطوة 7: يطبع النتيجة
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# INFO  [alembic.runtime.migration] Running upgrade 000 -> 001, initial schema
```

---

### 5️⃣ ما تم إنشاؤه في PostgreSQL

```sql
-- جدول السور
CREATE TABLE surahs (
    id SERIAL PRIMARY KEY,
    number INTEGER NOT NULL,           -- رقم السورة (1-114)
    name VARCHAR(100) NOT NULL,        -- اسم السورة
    english_name VARCHAR(100),         -- الاسم بالإنجليزية
    verses_count INTEGER NOT NULL,     -- عدد الآيات
    revelation_place VARCHAR(10),      -- مكان النزول (Mecca/Medina)
    created_at TIMESTAMP DEFAULT NOW()
);

-- جدول الآيات
CREATE TABLE ayahs (
    id SERIAL PRIMARY KEY,
    surah_id INTEGER REFERENCES surahs(id),  -- مفتاح أجنبي للسورة
    verse_number INTEGER NOT NULL,            -- رقم الآية
    text TEXT NOT NULL,                       -- نص الآية
    created_at TIMESTAMP DEFAULT NOW()
);

-- جدول الترجمات
CREATE TABLE translations (
    id SERIAL PRIMARY KEY,
    ayah_id INTEGER REFERENCES ayahs(id),    -- مفتاح أجنبي للآية
    language VARCHAR(10) NOT NULL,            -- لغة الترجمة
    text TEXT NOT NULL,                       -- نص الترجمة
    translator VARCHAR(100),                  -- اسم المترجم
    created_at TIMESTAMP DEFAULT NOW()
);

-- جدول التفاسير
CREATE TABLE tafsirs (
    id SERIAL PRIMARY KEY,
    ayah_id INTEGER REFERENCES ayahs(id),    -- مفتاح أجنبي للآية
    text TEXT NOT NULL,                       -- نص التفسير
    author VARCHAR(100),                      -- اسم المفسر
    created_at TIMESTAMP DEFAULT NOW()
);

-- جدول تتبع المهايرات
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL
);
INSERT INTO alembic_version VALUES ('001');
```

---

# المرحلة 4: تشغيل التطبيق (`make dev`)

## 📍 ما يحدث عند تشغيل `make dev`

هذه هي **المرحلة الأهم** - سأشرحها بالتفصيل الكامل!

### 1️⃣ قراءة Makefile

```makefile
dev:
	poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**ما يعني:**
- `make dev` → ينفذ `poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000`

**الخيارات:**
| الخيار | المعنى |
|--------|--------|
| `poetry run` | يشغل داخل البيئة الافتراضية |
| `uvicorn` | خادم ASGI لـ FastAPI |
| `src.api.main:app` | الملف:الدالة (src/api/main.py → app) |
| `--reload` | يعيد التشغيل عند تغيير الكود (development فقط) |
| `--host 0.0.0.0` | يقبل طلبات من أي مكان (ليس فقط localhost) |
| `--port 8000` | يستمع على المنفذ 8000 |

---

### 2️⃣ Uvicorn يبدأ

```bash
$ poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# الخطوة 1: Uvicorn ينشئ عملية Python
# └── يحدد مسار Python من البيئة الافتراضية
#     ~/.cache/pypoetry/virtualenvs/athar-xxxxx-py3.12/bin/python

# الخطوة 2: يستورد src.api.main
# └── يضيف src/ إلى Python path
# └── يستورد src/api/main.py
# └── هذا ينفذ كل الـ imports في الملف
```

---

### 3️⃣ ما يحدث عند استيراد `src/api/main.py`

```python
# ==========================================
# الأسطر 1-30: Imports
# ==========================================

# يستورد المكتبات الأساسية
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# يستورد الإعدادات
from src.config.settings import settings
# ← هذا ينفذ src/config/settings.py
# ← الذي يقرأ ملف .env
# ← وينشئ كائن Settings

from src.config.logging_config import setup_logging, get_logger
# ← هذا يهيئ نظام التسجيل (structlog)

# يستورد الـ middleware
from src.api.middleware.error_handler import error_handler_middleware
from src.api.middleware.security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)

# يستورد الـ routers
from src.api.routes.health import router as health_router
from src.api.routes.query import router as query_router
from src.api.routes.tools import router as tools_router
from src.api.routes.rag import router as rag_router
from src.api.routes.quran import router as quran_router

# ==========================================
# الأسطر 31-50: Lifespan function
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    
    # Startup (يُنفذ عند بدء التطبيق)
    setup_logging()
    logger.info(
        "app.startup",
        app_name=settings.app_name,
        version="0.5.0",
        environment=settings.app_env,
    )

    yield  # ← يسمح للتطبيق بالعمل

    # Shutdown (يُنفذ عند إيقاف التطبيق)
    logger.info("app.shutdown")

# ==========================================
# الأسطر 51-120: create_app()
# ==========================================

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # الخطوة 1: ينشئ FastAPI application
    app = FastAPI(
        title=settings.app_name,              # "Athar"
        description="Multi-agent Islamic QA system...",
        version="0.5.0",
        docs_url="/docs",                     # Swagger UI
        redoc_url="/redoc",                   # ReDoc
        openapi_url="/openapi.json",          # OpenAPI schema
        lifespan=lifespan,                    # دالة البدء/الإيقاف
        debug=settings.debug,                 # True في development
    )

    # الخطوة 2: يضيف Middleware (الترتيب مهم!)
    
    # 2.1: Security headers (outermost - يعمل أولاً)
    app.add_middleware(SecurityHeadersMiddleware)
    # ← يضيف headers أمنية لكل استجابة:
    #   X-Content-Type-Options: nosniff
    #   X-Frame-Options: DENY
    #   X-XSS-Protection: 1; mode=block
    #   Strict-Transport-Security: max-age=31536000

    # 2.2: Rate limiting (في production فقط)
    if settings.app_env == "production":
        app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
    # ← يحدد عدد الطلبات (60/دقيقة)
    # ← لكننا في development → لا يُضاف

    # 2.3: CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # ["http://localhost:3000", ...]
        allow_credentials=True,
        allow_methods=["*"],                  # كل الطرق (GET, POST, ...)
        allow_headers=["*"],                  # كل الـ headers
    )
    # ← يسمح للـ frontend بالاتصال من domain مختلف

    # 2.4: Error handling
    app.middleware("http")(error_handler_middleware)
    # ← يمسك كل الأخطاء ويسجلها
    # ← يرجع استجابة خطأ منظمة

    # الخطوة 3: يسجل الـ Routers
    
    app.include_router(health_router)
    # ← يسجل /health و /ready
    
    app.include_router(query_router, prefix=settings.api_v1_prefix)
    # ← يسجل POST /api/v1/query
    
    app.include_router(tools_router, prefix=settings.api_v1_prefix)
    # ← يسجل POST /api/v1/tools/*
    
    app.include_router(rag_router, prefix=settings.api_v1_prefix)
    # ← يسجل POST /api/v1/rag/*
    
    app.include_router(quran_router, prefix=settings.api_v1_prefix)
    # ← يسجل GET/POST /api/v1/quran/*

    # الخطوة 4: ينشئ Root endpoint
    
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.app_name,
            "version": "0.5.0",
            "phase": "5 - Security & Performance",
            "docs": "/docs",
            "health": "/health",
            ...
        }

    # الخطوة 5: يرجع التطبيق
    return app

# ==========================================
# الأسطر 121-125: إنشاء التطبيق
# ==========================================

app = create_app()
# ← ينفذ create_app()
# ← يحفظ النتيجة في app
# ← هذا ما يستورده Uvicorn
```

---

### 4️⃣ Lifespan Startup يُنفذ

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup (يُنفذ الآن!)
    setup_logging()
    # ← يهيئ structlog
    # ← يحدد مستوى logging (DEBUG في development)
    # ← يحدد الشكل (JSON في production, console في development)
    
    logger.info(
        "app.startup",
        app_name=settings.app_name,        # "Athar"
        version="0.5.0",
        environment=settings.app_env,      # "development"
    )
    # ← يطبع:
    #   2024-04-14 10:30:00 [info     ] app.startup app_name=Athar version=0.5.0 environment=development

    yield  # ← يسمح للتطبيق بالعمل
    # ← من هنا، التطبيق جاهز لاستقبال الطلبات
```

---

### 5️⃣ Uvicorn يبدأ الاستماع

```bash
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
2024-04-14 10:30:00 [info     ] app.startup app_name=Athar version=0.5.0 environment=development
INFO:     Application startup complete.
```

**ما يعني:**
- `Uvicorn running on http://0.0.0.0:8000` ← التطبيق جاهز
- `Started reloader process` ← `--reload` يعمل (يعيد التشغيل عند تغيير الكود)
- `Started server process` ← الخادم يعمل
- `Application startup complete` ← lifespan startup اكتمل

---

### 6️⃣ التطبيق الآن جاهز!

```
الآن تستطيع:
├── فتح http://localhost:8000/docs       ← Swagger UI
├── فتح http://localhost:8000/redoc      ← ReDoc
├── فتح http://localhost:8000/health     ← Health check
└── إرسال طلبات إلى http://localhost:8000/api/v1/query
```

---

# المرحلة 5: معالجة طلب End-to-End

## 📍 ما يحدث من الطلب إلى الإجابة

الآن سأشرح **رحلة طلب كامل** من البداية للنهاية!

### الطلب

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "ما حكم صلاة العيد؟"}'
```

---

### الخطوة 1: الطلب يصل إلى Uvicorn

```
HTTP Request:
  Method: POST
  URL: http://localhost:8000/api/v1/query
  Headers:
    Content-Type: application/json
  Body: {"query": "ما حكم صلاة العيد؟"}

Uvicorn يستمع على المنفذ 8000
  ↓
يستقبل الطلب
  ↓
يحلل HTTP request
  ↓
ينشئ ASGI scope:
  {
    "type": "http",
    "method": "POST",
    "path": "/api/v1/query",
    "headers": [(b"content-type", b"application/json"), ...],
  }
  ↓
يرسل إلى FastAPI
```

---

### الخطوة 2: FastAPI يستقبل الطلب

```python
# FastAPI يبحث عن router مطابق
# يجد: query_router مع prefix="/api/v1/query"

# من src/api/routes/query.py:
@router.post("")
async def handle_query(request: QueryRequest, ...):
    # ← هذا الـ endpoint يتعامل مع POST /api/v1/query
```

---

### الخطوة 3: Middleware يُنفذ (من الخارج للداخل)

```python
# Middleware 1: SecurityHeadersMiddleware
# ← لا يغير الطلب، يضيف headers للاستجابة فقط

# Middleware 2: CORS (إذا كان الطلب من frontend)
# ← يتحقق من Origin header
# ← إذا localhost:3000 → يسمح
# ← يضيف Access-Control-Allow-Origin header

# Middleware 3: error_handler_middleware
# ← لا يغير الطلب، يمسك الأخطاء فقط
```

---

### الخطوة 4: Pydantic يتحقق من الطلب

```python
# من src/api/schemas/request.py:
class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's question"
    )
    language: Optional[str] = Field(
        None,
        description="Response language (ar/en)"
    )
    madhhab: Optional[str] = Field(
        None,
        description="Islamic school of jurisprudence"
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID for conversation context"
    )
    stream: bool = Field(
        False,
        description="Stream response"
    )

# ما يحدث:
request_data = {"query": "ما حكم صلاة العيد؟"}

# Pydantic يتحقق:
# 1. query موجود؟ ← نعم ✓
# 2. query هو str؟ ← نعم ✓
# 3. query length بين 1 و 1000؟ ← نعم (18 حرف) ✓
# 4. language موجود؟ ← لا، لكن Optional ✓
# 5. madhhab موجود؟ ← لا، لكن Optional ✓

# إذا نجح:
request = QueryRequest(
    query="ما حكم صلاة العيد؟",
    language=None,
    madhhab=None,
    session_id=None,
    stream=False
)

# إذا فشل (مثلاً query فارغ):
# ValidationError: query: Field required
```

---

### الخطوة 5: endpoint يُنفذ

```python
# من src/api/routes/query.py:
@router.post("")
async def handle_query(request: QueryRequest, ...):
    """Handle user query with intent-based routing."""
    
    start_time = time.time()
    query_id = str(uuid.uuid4())
    # ← query_id = "550e8400-e29b-41d4-a716-446655440000"

    logger.info("query.received", query_id=query_id, query=request.query[:50])
    # ← query.received query_id=550e8400-e29b-41d4-a716-446655440000 query="ما حكم صلاة العيد؟"
```

---

### الخطوة 6: جلب المكونات (Lazy Initialization)

```python
# 6.1: جلب ChatbotAgent
chatbot = get_chatbot()

def get_chatbot() -> ChatbotAgent:
    global _chatbot
    with _chatbot_lock:
        if _chatbot is None:
            _chatbot = ChatbotAgent()  # ← ينشئ أول مرة فقط
        return _chatbot

# ما يحدث:
# أول طلب: ينشئ ChatbotAgent()
# ثاني طلب: يرجع النفسة (لا يعيد الإنشاء)
# لماذا؟ Lazy Initialization (يوفر الذاكرة والوقت)

# 6.2: جلب HybridQueryClassifier
classifier = await get_classifier()

async def get_classifier() -> HybridQueryClassifier:
    global _classifier
    with _classifier_lock:
        if _classifier is None:
            llm_client = await get_llm_client()
            # ← يتصل بـ Groq/OpenAI
            # ← يحفظ العميل للاستخدام المستقبلي
            _classifier = HybridQueryClassifier(llm_client=llm_client)
        return _classifier
```

---

### الخطوة 7: تصنيف النية

```python
# تصنيف النية
router_result = await classifier.classify(request.query)
# ← request.query = "ما حكم صلاة العيد؟"

# ما يحدث داخل classify():

# ==========================================
# Tier 1: Keyword Matching
# ==========================================
keyword_result = self._keyword_match("ما حكم صلاة العيد؟")

def _keyword_match(self, query: str):
    query_lower = "ما حكم صلاة العيد؟"
    
    # يبحث في KEYWORD_PATTERNS:
    for intent, patterns in KEYWORD_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in query_lower:
                return RouterResult(
                    intent=intent,
                    confidence=0.92,
                    method="keyword",
                    reason=f"Keyword match: '{pattern}'"
                )

    # iteration 1: intent=FIQH, patterns=["حكم", "ما حكم", ...]
    #   pattern = "حكم" → "حكم" in "ما حكم صلاة العيد؟" ← نعم!
    #   يرجع RouterResult(intent=Intent.FIQH, confidence=0.92)

# keyword_result.confidence = 0.92 >= 0.90 → ✅ يرجع مباشرة!

intent = router_result.intent  # Intent.FIQH
language = request.language or router_result.language  # "ar"

logger.info(
    "query.classified",
    query_id=query_id,
    intent=intent.value,         # "fiqh"
    confidence=router_result.confidence,  # 0.92
)
```

---

### الخطوة 8: توجيه للوكيل المناسب

```python
# intent = Intent.FIQH
# يتحقق من if/elif:

if intent == Intent.GREETING:
    # ← لا، هذا fiqh وليس greeting

elif intent == Intent.FIQH:
    # ← نعم! هذا fiqh
    
    # يجلب FiqhAgent
    fiqh_agent = await get_fiqh_agent()
    
    async def get_fiqh_agent():
        global _fiqh_agent
        with _fiqh_lock:
            if _fiqh_agent is None:
                _fiqh_agent = FiqhAgent()
                await _fiqh_agent._initialize()
                # ← يحمل embedding model
                # ← يحمل vector store
                # ← يحمل hybrid searcher
            return _fiqh_agent
    
    # يتحقق من أن FiqhAgent جاهز
    if fiqh_agent and fiqh_agent.embedding_model:
        # ← نعم، جاهز
        
        # ينشئ AgentInput
        agent_input = AgentInput(
            query="ما حكم صلاة العيد؟",
            language="ar",
            metadata={
                "madhhab": None,
                "filters": None,
                "hierarchical": False,
            }
        )
        
        # ينفذ FiqhAgent
        agent_result = await fiqh_agent.execute(agent_input)
        
        agent_name = "fiqh_agent"
```

---

### الخطوة 9: FiqhAgent يُنفذ (RAG Pipeline)

```python
# من src/agents/fiqh_agent.py:
async def execute(self, input: AgentInput) -> AgentOutput:
    
    # ==========================================
    # الخطوة 9.1: تحويل السؤال لمتجه
    # ==========================================
    query_embedding = await self.embedding_model.encode_query(input.query)
    
    # ما يحدث داخل encode_query():
    # 1. tokenizer يحول النص إلى tokens
    #    "ما حكم صلاة العيد؟" → [101, 2345, 6789, 10123, 456, 102]
    # 2. model يحول tokens إلى embedding
    #    [101, 2345, ...] → [0.12, -0.34, 0.56, ...] (1024 رقم)
    # 3. يرجع embedding
    
    # query_embedding = [0.1234, -0.5678, 0.9012, ...] (1024 dimension)

    # ==========================================
    # الخطوة 9.2: البحث في Qdrant
    # ==========================================
    passages = await self.hybrid_searcher.search(
        query=input.query,              # "ما حكم صلاة العيد؟"
        query_embedding=query_embedding,  # [0.1234, -0.5678, ...]
        collection="fiqh_passages",     # مجموعة الفقه
        top_k=self.TOP_K_RETRIEVAL,     # 15
    )
    
    # ما يحدث داخل hybrid_searcher.search():
    # 1. Semantic Search:
    #    ← يبحث في Qdrant باستخدام المتجه
    #    ← يرجع top 15 وثيقة متشابهة دلالياً
    #    ← النتائج: [doc1 (0.85), doc2 (0.78), ...]
    
    # 2. BM25 Search:
    #    ← يبحث عن الكلمات "ما", "حكم", "صلاة", "العيد"
    #    ← يرجع top 15 وثيقة تحتوي الكلمات
    #    ← النتائج: [doc2 (0.90), doc1 (0.82), ...]
    
    # 3. Reciprocal Rank Fusion:
    #    ← يدمج النتيجتين
    #    ← score = 1/(60+rank_semantic) + 1/(60+rank_bm25)
    #    ← النتائج النهائية: [doc1 (0.0323), doc2 (0.0320), ...]
    
    # passages = [
    #     {"content": "صلاة العيد سنة مؤكدة...", "score": 0.85},
    #     {"content": "كان النبي صلى الله عليه وسلم...", "score": 0.78},
    #     ... (15 وثيقة)
    # ]

    # ==========================================
    # الخطوة 9.3: تصفية الوثائق
    # ==========================================
    good_passages = [
        p for p in passages
        if p.get("score", 0) >= self.SCORE_THRESHOLD  # 0.15
    ]
    
    # يحتفظ فقط بالوثائق > 0.15
    # good_passages = [doc1, doc2, ..., doc12] (12 وثيقة)

    # ==========================================
    # الخطوة 9.4: تنسيق الوثائق للـ LLM
    # ==========================================
    formatted_passages = self._format_passages(good_passages[:self.TOP_K_RERANK])
    # ← يأخذ top 5 فقط
    
    def _format_passages(self, passages):
        formatted = []
        for i, passage in enumerate(passages, 1):
            content = passage.get("content", "")[:500]
            source = passage.get("metadata", {}).get("source", "Unknown")
            passage_text = f"[C{i}] {content}\nالمصدر: {source}"
            formatted.append(passage_text)
        return "\n\n".join(formatted)
    
    # formatted_passages = """
    # [C1] صلاة العيد سنة مؤكدة عند الجمهور من العلماء...
    # المصدر: موطأ مالك
    #
    # [C2] كان النبي صلى الله عليه وسلم يخرج إلى المصلى...
    # المصدر: صحيح البخاري
    #
    # ... (5 وثائق)
    # """

    # ==========================================
    # الخطوة 9.5: توليد الإجابة بـ LLM
    # ==========================================
    answer = await self._generate_with_llm(
        query=input.query,
        passages=formatted_passages,
        language=input.language
    )
    
    # ما يحدث داخل _generate_with_llm():
    # 1. يبني prompt:
    prompt = """أنت مساعد إسلامي متخصص في الفقه الإسلامي.

المهم:
- أجب بناءً ONLY على النصوص المسترجاعة المقدمة
- لا تختلق أي معلومات غير موجودة في النصوص
- استخدم المراجع [C1]، [C2]، إلخ لكل مصدر تستشهد به

السؤال: ما حكم صلاة العيد؟

اللغة المطلوبة: العربية

النصوص المسترجاعة:
[C1] صلاة العيد سنة مؤكدة عند الجمهور من العلماء...
المصدر: موطأ مالك

[C2] كان النبي صلى الله عليه وسلم يخرج إلى المصلى...
المصدر: صحيح البخاري

...

أجب بناءً على النصوص أعلاه مع الالتزام بالتعليمات."""

    # 2. يرسل إلى Groq:
    response = await self.llm_client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[
            {"role": "system", "content": "أنت مساعد إسلامي متخصص..."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,  # دقيق جداً
        max_tokens=2048,
    )
    
    # 3. Groq يعالج:
    #    ← يحلل الـ prompt
    #    ← يفهم السؤال
    #    ← يقرأ النصوص المسترجاعة
    #    ← يولد إجابة مبنية على النصوص
    #    ← يستغرق ~2-5 ثواني
    
    # 4. يرجع الإجابة:
    answer = response.choices[0].message.content
    # answer = "صلاة العيد سنة مؤكدة عند الجمهور من العلماء..."

    # ==========================================
    # الخطوة 9.6: تطبيع الاقتباسات
    # ==========================================
    normalized_text = self.citation_normalizer.normalize(answer)
    
    # ما يحدث داخل normalize():
    # 1. يبحث عن أنماط الاقتباس في النص
    # 2. يجد "موطأ مالك" → يستبدل بـ [C1]
    # 3. يجد "صحيح البخاري" → يستبدل بـ [C2]
    # 4. يرجع النص مع الاقتباسات المطبعة
    
    # normalized_text = "صلاة العيد سنة مؤكدة [C1] [C2]..."
    
    citations = self.citation_normalizer.get_citations()
    # citations = [
    #     Citation(id="C1", type="fiqh_book", source="موطأ مالك", ...),
    #     Citation(id="C2", type="hadith", source="صحيح البخاري", ...),
    # ]

    # ==========================================
    # الخطوة 9.7: إضافة التنويه
    # ==========================================
    final_answer = self._add_disclaimer(normalized_text)
    
    def _add_disclaimer(self, text):
        disclaimer = "\n\n---\n⚠️ **تنبيه مهم**: هذه الإجابة مبنية على النصوص المسترجاعة..."
        return text + disclaimer

    # ==========================================
    # الخطوة 9.8: إرجاع AgentOutput
    # ==========================================
    return AgentOutput(
        answer=final_answer,
        citations=citations,
        metadata={
            "retrieved_count": 12,
            "used_count": 5,
            "collection": "fiqh_passages",
        },
        confidence=0.89,
        requires_human_review=False,
    )
```

---

### الخطوة 10: بناء الاستجابة

```python
# من src/api/routes/query.py:
processing_time = int((time.time() - start_time) * 1000)
# ← processing_time = 2847 (ملّي ثانية = 2.8 ثانية)

return QueryResponse(
    query_id=query_id,
    intent=intent.value,                   # "fiqh"
    intent_confidence=router_result.confidence,  # 0.92
    answer=agent_result.answer,            # "صلاة العيد سنة مؤكدة..."
    citations=[
        CitationResponse(
            id=c.id,            # "C1"
            type=c.type,        # "fiqh_book"
            source=c.source,    # "موطأ مالك"
            reference=c.reference,
            url=c.url,
            text_excerpt=c.text_excerpt
        )
        for c in agent_result.citations
    ],
    metadata={
        "agent": agent_name,               # "fiqh_agent"
        "processing_time_ms": processing_time,  # 2847
        "classification_method": router_result.method,  # "keyword"
        **agent_result.metadata,
    },
    follow_up_suggestions=agent_result.metadata.get("follow_up_suggestions", []),
)
```

---

### الخطوة 11: الاستجابة تُرسل

```json
HTTP Response:
  Status: 200 OK
  Headers:
    Content-Type: application/json
    X-Content-Type-Options: nosniff
    X-Frame-Options: DENY
    Access-Control-Allow-Origin: http://localhost:3000
  Body:
  {
    "query_id": "550e8400-e29b-41d4-a716-446655440000",
    "intent": "fiqh",
    "intent_confidence": 0.92,
    "answer": "صلاة العيد سنة مؤكدة عند الجمهور من العلماء...\n\n[C1] [C2]\n\n---\n⚠️ تنبيه مهم...",
    "citations": [
      {
        "id": "C1",
        "type": "fiqh_book",
        "source": "موطأ مالك",
        "reference": "كتاب صلاة العيد",
        "url": null,
        "text_excerpt": "صلاة العيد سنة مؤكدة..."
      },
      {
        "id": "C2",
        "type": "hadith",
        "source": "صحيح البخاري",
        "reference": "حديث 1234",
        "url": "https://sunnah.com/bukhari/1234",
        "text_excerpt": "كان النبي يصلي العيد..."
      }
    ],
    "metadata": {
      "agent": "fiqh_agent",
      "processing_time_ms": 2847,
      "classification_method": "keyword",
      "retrieved_count": 12,
      "used_count": 5,
      "collection": "fiqh_passages"
    },
    "follow_up_suggestions": []
  }
```

---

## 📊 ملخص الرحلة الكاملة

```
┌─────────────────────────────────────────────────────────┐
│ المرحلة 0: قبل التشغيل                                  │
│ ← تثبيت Python, Poetry, Docker                         │
│ ← إنشاء ملف .env                                        │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ المرحلة 1: make install-dev                             │
│ ← poetry install --with dev                            │
│ ← يحمل 85+ مكتبة في بيئة افتراضية                      │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ المرحلة 2: make docker-up                               │
│ ← docker compose up -d                                  │
│ ← يشغل PostgreSQL, Qdrant, Redis                       │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ المرحلة 3: make db-migrate                              │
│ ← alembic upgrade head                                 │
│ ← ينشئ جداول قاعدة البيانات                             │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ المرحلة 4: make dev                                     │
│ ← uvicorn src.api.main:app --port 8000                 │
│ ← يحمّل FastAPI + middleware + routers                 │
│ ← lifespan startup → التطبيق جاهز!                     │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ المرحلة 5: معالجة الطلب                                 │
│                                                         │
│ 1. Uvicorn يستقبل الطلب                                │
│    ↓                                                    │
│ 2. FastAPI يطابق الـ endpoint                          │
│    ↓                                                    │
│ 3. Middleware يُنفذ                                     │
│    ↓                                                    │
│ 4. Pydantic يتحقق من الطلب                             │
│    ↓                                                    │
│ 5. endpoint يُنفذ                                       │
│    ↓                                                    │
│ 6. Lazy Initialization للمكونات                        │
│    ↓                                                    │
│ 7. تصنيف النية (3-tier) → fiqh (0.92)                  │
│    ↓                                                    │
│ 8. توجيه إلى FiqhAgent                                 │
│    ↓                                                    │
│ 9. FiqhAgent ينفذ RAG Pipeline:                        │
│    9.1 encode_query → متجه 1024-dim                   │
│    9.2 hybrid_search → top 15 وثيقة                   │
│    9.3 filter by score > 0.15                          │
│    9.4 format_passages للـ LLM                        │
│    9.5 generate_with_llm → Groq يولد إجابة            │
│    9.6 citation_normalize → [C1], [C2]                │
│    9.7 add_disclaimer                                  │
│    ↓                                                    │
│ 10. بناء QueryResponse                                │
│    ↓                                                    │
│ 11. إرسال الاستجابة للمستخدم                           │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ النتيجة:                                                │
│ ← إجابة موثقة بمصادر                                   │
│ ← وقت المعالجة: ~2.8 ثانية                             │
│ ← ثقة التصنيف: 0.92                                    │
│ ← 12 وثيقة مسترجاعة، 5 مستعملة                         │
└─────────────────────────────────────────────────────────┘
```

---

## ⏱️ توقيت كل مرحلة

| المرحلة | الوقت | ملاحظات |
|---------|-------|---------|
| **make install-dev** | 5-10 دقائق | أول مرة فقط |
| **make docker-up** | 30-60 ثانية | أول مرة يحمل الصور |
| **make db-migrate** | 1-2 ثانية | ينشئ الجداول |
| **make dev** | 3-5 ثواني | يحمل التطبيق |
| **معالجة الطلب الأول** | 10-15 ثانية | Lazy initialization |
| **معالجة الطلب الثاني** | 2-5 ثواني | المكونات جاهزة |

---

## 🎯 الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً؟

1. **make install-dev** ← يثبت التبعيات في بيئة افتراضية
2. **make docker-up** ← يشغل 3 خدمات (PostgreSQL, Qdrant, Redis)
3. **make db-migrate** ← ينشئ جداول قاعدة البيانات
4. **make dev** ← يشغل FastAPI على المنفذ 8000
5. **معالجة الطلب** ← 11 خطوة من الطلب إلى الإجابة
6. **RAG Pipeline** ← encode → search → filter → generate → cite

### 📝 تمرين صغير

1. شغل التطبيق من البداية (`make install-dev` → `make dev`)
2. افتح Swagger UI (`http://localhost:8000/docs`)
3. أرسل سؤال "السلام عليكم"
4. أرسل سؤال "ما حكم صلاة العيد؟"
5. قارن الـ intent و processing_time بين السؤالين

### 🔜 الخطوة التالية

اقرأ الملف التالي: `src/api/routes/query.py` بالتفصيل

---

**📖 الدليل الكامل:** [`docs/mentoring/`](docs/mentoring/)

**🚀 ابدأ الآن:** شغل التطبيق وتابع الخطوات!

---

**مُعد الشرح:** AI Mentor System  
**التاريخ:** أبريل 2026  
**الإصدار:** 1.0  
**الحالة:** ✅ شرح تفصيلي end-to-end
