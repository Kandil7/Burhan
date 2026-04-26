# 🚀 شرح ملف `src/api/main.py` سطر بسطر - Backend Entrypoint

## 🕌 مقدمة

هذا الملف هو **نقطة الدخول الرئيسية** لتطبيق Burhan. عندما تشغل `make dev`، هذا الملف هو الذي **ينشئ التطبيق بالكامل**.

---

## 📊 نظرة عامة على الملف

| القسم | الأسطر | المحتوى |
|-------|--------|---------|
| Docstring | 1-12 | وصف الملف |
| Imports | 13-30 | استيراد المكتبات |
| Logger | 31 | إعداد المسجل |
| Lifespan | 33-52 | دالة البدء/الإيقاف |
| create_app() | 54-180 | الدالة الرئيسية |
| App instance | 182-183 | إنشاء التطبيق |

---

## 3️⃣ شرح سطر بسطر

### الأسطر 1-12: Docstring (وصف الملف)

```python
"""
FastAPI application factory for Burhan Islamic QA system.

Creates and configures the FastAPI application with:
- Security middleware (rate limiting, API key, security headers)
- CORS middleware
- Error handling
- Request logging
- Route registration
- OpenAPI documentation

Phase 5: Security improvements and performance optimizations.
"""
```

**شرح**:

| السطر | المعنى |
|-------|--------|
| **1** | هذا ملف Factory Pattern (مصنع للتطبيق) |
| **3-8** | ما يفعله الملف: ينشئ و يهيئ التطبيق |
| **4** | Security middleware: حماية التطبيق |
| **5** | CORS middleware: السماح للـ frontend بالاتصال |
| **6** | Error handling: معالجة الأخطاء |
| **7** | Request logging: تسجيل الطلبات |
| **8** | Route registration: تسجيل نقاط الدخول |
| **9** | OpenAPI documentation: توليد Swagger UI |
| **11** | Phase 5: المرحلة الحالية (أمان وأداء) |

**لماذا Factory Pattern؟**

```python
# بدون Factory Pattern:
app = FastAPI(...)  # ← تطبيق واحد فقط
# مشكلة: صعب الاختبار، صعب إعادة الاستخدام

# مع Factory Pattern:
def create_app() -> FastAPI:
    app = FastAPI(...)
    return app  # ← يمكنك إنشاء تطبيقات متعددة

# مثال:
app1 = create_app()  # تطبيق للاختبار
app2 = create_app()  # تطبيق للإنتاج
```

---

### الأسطر 13-15: Imports الأساسية

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
```

**شرح كل استيراد**:

#### `contextlib.asynccontextmanager`

```python
# ما هو؟
← decorator يسمح بإنشاء context manager غير متزامن

# لماذا نحتاجه؟
← نريد دالة تُنفذ عند البدء وعند الإيقاف
← lifespan function تحتاج هذا

# مثال بسيط:
@asynccontextmanager
async def my_context():
    print("قبل البدء")
    yield
    print("بعد الإيقاف")

async with my_context():
    print="أثناء العمل"

# النتيجة:
# قبل البدء
# أثناء العمل
# بعد الإيقاف
```

#### `fastapi.FastAPI`

```python
# ما هو؟
← الفئة الرئيسية لإنشاء تطبيق FastAPI

# لماذا نحتاجه؟
← بدون هذا، لا يوجد تطبيق!

# مثال:
app = FastAPI(
    title="My App",
    version="1.0.0"
)
```

#### `fastapi.middleware.cors.CORSMiddleware`

```python
# ما هو؟
← middleware يسمح بالطلبات من domains مختلفة

# لماذا نحتاجه؟
← المتصفح يمنع الطلبات عبر domains مختلفة افتراضياً
← Frontend (localhost:3000) → Backend (localhost:8000)
← بدون CORS، الطلب يُرفض!

# مثال:
# بدون CORS:
# Frontend: fetch("http://localhost:8000/api/v1/query")
# Browser: ❌ Blocked by CORS policy!

# مع CORS:
# Frontend: fetch("http://localhost:8000/api/v1/query")
# Backend: يضيف header "Access-Control-Allow-Origin: http://localhost:3000"
# Browser: ✅ Allowed!
```

---

### الأسطر 16-21: Imports من المشروع (الإعدادات)

```python
from src.config.settings import settings
from src.config.logging_config import setup_logging, get_logger
```

#### `src.config.settings.settings`

```python
# ما هو؟
← كائن Settings محمّل من ملف .env

# لماذا نحتاجه؟
← يحتوي كل إعدادات التطبيق
← نستخدمه في كل مكان

# ما يحتويه:
settings.app_name         # "Burhan"
settings.app_env          # "development" أو "production"
settings.debug            # True أو False
settings.api_v1_prefix    # "/api/v1"
settings.cors_origins     # ["http://localhost:3000", ...]

# مثال استخدام:
app = FastAPI(title=settings.app_name)
# ← title = "Burhan"
```

#### `src.config.logging_config.setup_logging, get_logger`

```python
# ما هما؟
← setup_logging(): يهيئ نظام التسجيل
← get_logger(): يرجع مسجل جاهز للاستخدام

# لماذا نحتاجهما؟
← نريد تسجيل الأحداث بشكل منظم
← نريد تتبع الطلبات والأخطاء

# مثال:
setup_logging()  # ← يهيئ structlog
logger = get_logger()  # ← يرجع logger
logger.info("app.startup", app_name="Burhan")
# ← يطبع: 2024-04-14 10:30:00 [info] app.startup app_name=Burhan
```

---

### الأسطر 22-27: Imports من المشروع (Middleware)

```python
from src.api.middleware.error_handler import error_handler_middleware
from src.api.middleware.security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
```

#### `error_handler_middleware`

```python
# ما هو؟
← middleware يمسك كل الأخطاء

# لماذا نحتاجه؟
← بدون هذا، الأخطاء ترجع HTML بدلاً من JSON
← نريد تسجيل كل الأخطاء
← نريد إرجاع استجابة خطأ منظمة

# مثال:
# بدون error_handler:
# خطأ في الكود → 500 Internal Server Error (HTML)
# {"detail": "Internal Server Error"}

# مع error_handler:
# خطأ في الكود → يسجل الخطأ → يرجع:
# {
#     "error": "Internal error: division by zero",
#     "query_id": "550e8400-...",
#     "timestamp": "2024-04-14T10:30:00"
# }
```

#### `RateLimitMiddleware`

```python
# ما هو؟
← middleware يحدد عدد الطلبات في الدقيقة

# لماذا نحتاجه؟
← حماية من abuse (شخص يرسل 1000 طلب/ثانية)
← يوفر تكلفة LLM (كل طلب = API call مكلف)

# كيف يعمل:
# طلب 1-60 في الدقيقة → ✅ مسموح
# طلب 61+ في الدقيقة → ❌ 429 Too Many Requests

# مثال:
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
```

#### `SecurityHeadersMiddleware`

```python
# ما هو؟
← middleware يضيف headers أمنية لكل استجابة

# لماذا نحتاجه؟
← حماية من هجمات XSS
← حماية من Clickjacking
← تفعيل HTTPS

# ما يضيفه:
# X-Content-Type-Options: nosniff        ← يمنع MIME sniffing
# X-Frame-Options: DENY                  ← يمنع التضمين في iframe
# X-XSS-Protection: 1; mode=block        ← يفعيل XSS filter
# Strict-Transport-Security: max-age=...  ← يجبر HTTPS
# Content-Security-Policy: ...           ← يحدد المصادر المسموحة

# مثال:
# بدون SecurityHeaders:
# Response Headers:
#   Content-Type: application/json

# مع SecurityHeaders:
# Response Headers:
#   Content-Type: application/json
#   X-Content-Type-Options: nosniff
#   X-Frame-Options: DENY
#   X-XSS-Protection: 1; mode=block
#   Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

### الأسطر 28-32: Imports من المشروع (Routers)

```python
from src.api.routes.health import router as health_router
from src.api.routes.query import router as query_router
from src.api.routes.tools import router as tools_router
from src.api.routes.rag import router as rag_router
from src.api.routes.quran import router as quran_router
```

**شرح كل router**:

| Router | الملف | Endpoints | الوصف |
|--------|-------|-----------|-------|
| `health_router` | `routes/health.py` | `/health`, `/ready` | فحص الصحة |
| `query_router` | `routes/query.py` | `/api/v1/query` | السؤال الرئيسي |
| `tools_router` | `routes/tools.py` | `/api/v1/tools/*` | 5 أدوات |
| `rag_router` | `routes/rag.py` | `/api/v1/rag/*` | RAG مباشر |
| `quran_router` | `routes/quran.py` | `/api/v1/quran/*` | 6 endpoints للقرآن |

**لماذا `as health_router`؟**

```python
# كل الملفات تستخدم اسم "router"
from src.api.routes.health import router  # ← router
from src.api.routes.query import router   # ← router أيضاً!

# مشكلة: اسم متكرر!
# حل: نعيد تسمية عند الاستيراد

from src.api.routes.health import router as health_router  # ← health_router
from src.api.routes.query import router as query_router    # ← query_router
```

---

### السطر 33: Logger

```python
logger = get_logger()
```

**ما يحدث:**

```python
# get_logger() يرجع logger جاهز
logger = get_logger()

# الآن نستطيع تسجيل الأحداث:
logger.info("app.startup")
logger.error("query.error", error=str(e))
logger.warning("fiqh_agent.llm_unavailable")

# ما يطبعه (في development):
# 2024-04-14 10:30:00 [info     ] app.startup

# ما يطبعه (في production):
# {"timestamp": "2024-04-14T10:30:00", "level": "info", "event": "app.startup"}
```

---

### الأسطر 35-52: Lifespan Function

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Runs on startup and shutdown.
    Phase 5: Includes security and performance optimizations.
    """
    # Startup
    setup_logging()
    logger.info(
        "app.startup",
        app_name=settings.app_name,
        version="0.5.0",
        environment=settings.app_env,
    )

    yield

    # Shutdown
    logger.info("app.shutdown")
```

**شرح تفصيلي**:

#### `@asynccontextmanager`

```python
# هذا decorator يحول الدالة إلى context manager
# ما يعني: تُنفذ مرتين (قبل وبعد)

# كيف يعمل:
# 1. عند بدء التطبيق:
#    ← ينفذ الكود قبل yield
#    ← setup_logging()
#    ← logger.info("app.startup")

# 2. التطبيق يعمل:
#    ← yield يسمح للتطبيق بالعمل
#    ← كل الطلبات تُعالج هنا

# 3. عند إيقاف التطبيق:
#    ← ينفذ الكود بعد yield
#    ← logger.info("app.shutdown")
```

#### `setup_logging()`

```python
# ما تفعله:
def setup_logging():
    # 1. يهيئ structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()  # في production
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )
    
    # 2. يحدد مستوى logging
    #    development: DEBUG (كل شيء)
    #    production: INFO (مهم فقط)
    
    # 3. يحدد الشكل
    #    development: console ملون
    #    production: JSON (سهل التحليل)
```

#### `logger.info("app.startup", ...)`

```python
# ما يحدث:
logger.info(
    "app.startup",                      # اسم الحدث
    app_name=settings.app_name,         # "Burhan"
    version="0.5.0",                    # الإصدار
    environment=settings.app_env,       # "development"
)

# ما يطبعه (development):
# 2024-04-14 10:30:00 [info     ] app.startup app_name=Burhan version=0.5.0 environment=development

# ما يطبعه (production):
# {"timestamp": "2024-04-14T10:30:00Z", "level": "info", "event": "app.startup", "app_name": "Burhan", "version": "0.5.0", "environment": "development"}
```

#### `yield`

```python
# هذه أهم نقطة!
# yield تعني: "توقف هنا واسمح للتطبيق بالعمل"

# قبل yield:
setup_logging()
logger.info("app.startup")
# ← تهيئة التسجيل

yield
# ← التطبيق يعمل الآن!
# ← كل الطلبات تُعالج هنا
# ← ينتظر حتى يُوقف التطبيق

# بعد yield:
logger.info("app.shutdown")
# ← تنظيف الموارد عند الإيقاف
```

**متى يُنفذ كل جزء؟**

```
make dev
    ↓
Uvicorn يبدأ
    ↓
يستدعي create_app()
    ↓
ينشئ FastAPI مع lifespan=lifespan
    ↓
Uvicorn يستدعي lifespan.__aenter__()
    ↓
✅ يُنفذ الكود قبل yield (Startup)
    ↓
yield
    ↓
✅ التطبيق يعمل (يستقبل طلبات)
    ↓
... (ساعات/أيام من العمل) ...
    ↓
CTRL+C
    ↓
Uvicorn يستدعي lifespan.__aexit__()
    ↓
✅ يُنفذ الكود بعد yield (Shutdown)
```

---

### الأسطر 54-135: create_app() Function

```python
def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
```

**شرح**:

```python
# ما هي create_app()؟
← Factory Function: دالة تنشئ تطبيق FastAPI

# لماذا نستخدمها؟
1. يسهل الاختبار (ننشئ تطبيق اختبار منفصل)
2. يسهل إعادة الاستخدام (ننشئ تطبيقات متعددة)
3. ينظم الكود (كل الإعداد في مكان واحد)

# مثال:
# تطبيق للإنتاج:
prod_app = create_app()  ← يحمل إعدادات production

# تطبيق للاختبار:
test_app = create_app()  ← يحمل إعدادات testing
```

---

### الأسطر 63-89: إنشاء FastAPI Application

```python
    app = FastAPI(
        title=settings.app_name,
        description="""
# Burhan Islamic QA System API

Multi-agent Islamic QA system based on Fanar-Sadiq architecture.

## Features
- **Intent Classification**: Automatically detects query type (fiqh, quran, zakat, etc.)
- **Grounded Answers**: All answers backed by verified sources with citations
- **Deterministic Calculators**: Zakat and inheritance calculations
- **Multi-language**: Arabic and English support
- **Madhhab-aware**: Handles differences between Islamic schools
- **Rate Limiting**: Protected against abuse
- **API Key Authentication**: Secure access

## Security
- API Key required for query endpoints
- Rate limiting: 60 requests/minute default
- Security headers on all responses

        """,
        version="0.5.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug,
    )
```

**شرح كل parameter**:

#### `title=settings.app_name`

```python
# ما هو؟
← اسم التطبيق (يظهر في Swagger UI)

# القيمة:
settings.app_name = "Burhan"

# أين يظهر؟
# Swagger UI:
# ┌─────────────────────────────────┐
# │ Burhan                           │
# │ Multi-agent Islamic QA system   │
# └─────────────────────────────────┘
```

#### `description="""..."""`

```python
# ما هو؟
← وصف تفصيلي للتطبيق (Markdown)

# أين يظهر؟
# في Swagger UI تحت الاسم

# ما يحتويه:
# 1. وصف عام
# 2. Features (7 ميزات)
# 3. Security (3 ميزات أمنية)
```

#### `version="0.5.0"`

```python
# ما هو؟
← إصدار التطبيق

# Semantic Versioning:
# 0.5.0
# ↑ ↑ ↑
# │ │ └─ Patch (إصلاحات أخطاء)
# │ └─── Minor (ميزات جديدة)
# └───── Major (تغييرات كبيرة)

# الإصدار الحالي: 0.5.0
# ← لا يزال في التطوير (0.x)
# ← Phase 5 من 7
```

#### `docs_url="/docs"`

```python
# ما هو؟
← URL لـ Swagger UI

# أين يظهر؟
http://localhost:8000/docs

# ما تراه:
┌─────────────────────────────────────────┐
│ FastAPI - Swagger UI                    │
│                                         │
│ Burhan                                   │
│ Multi-agent Islamic QA system           │
│ v0.5.0                                  │
│                                         │
│ GET  /health                            │
│ GET  /ready                             │
│ POST /api/v1/query                      │
│ POST /api/v1/tools/zakat                │
│ ...                                     │
└─────────────────────────────────────────┘

# يمكنك تجربة كل endpoint من هنا!
```

#### `redoc_url="/redoc"`

```python
# ما هو؟
← URL لـ ReDoc (توثيق بديل)

# الفرق بين Swagger و ReDoc:
# Swagger: تفاعلي (يمكنك تجربة endpoints)
# ReDoc: للقراءة فقط (لكن أجمل)

http://localhost:8000/redoc
```

#### `openapi_url="/openapi.json"`

```python
# ما هو؟
← URL لـ OpenAPI schema (JSON)

# ما يحتويه:
{
  "openapi": "3.1.0",
  "info": {
    "title": "Burhan",
    "version": "0.5.0"
  },
  "paths": {
    "/health": {...},
    "/api/v1/query": {...},
    ...
  }
}

# لماذا مهم؟
← أدوات مثل Postman تستورده
← Frontend يولّد clients تلقائياً
← Validation tools تستخدمه
```

#### `lifespan=lifespan`

```python
# ما هو؟
← يربط دالة lifespan التي عرفناها سابقاً

# ما يحدث:
# عند بدء التطبيق:
lifespan.__aenter__()
    ↓
setup_logging()
logger.info("app.startup")
    ↓
yield  ← التطبيق يعمل

# عند إيقاف التطبيق:
logger.info("app.shutdown")
    ↓
lifespan.__aexit__()
```

#### `debug=settings.debug`

```python
# ما هو؟
← وضع التصحيح

# القيمة من .env:
DEBUG=true  ← في development
DEBUG=false ← في production

# ما يفعله:
# True:
# ← يعرض stack traces في الأخطاء
# ← يعيد تحميل الكود تلقائياً (--reload)
# ← لا يخفي أي معلومات

# False:
# ← يخفي stack traces
# ← لا يعيد التحميل
# ← رسائل خطأ عامة فقط
```

---

### الأسطر 91-120: Middleware Registration

```python
    # ==========================================
    # Middleware (order matters - last added runs first)
    # ==========================================
```

**ملاحظة مهمة**:

```python
# الترتيب مهم جداً!
# آخر middleware يُضاف = أول ما يُنفذ

# مثال:
app.add_middleware(Middleware1)  ← يُضاف أولاً (يُنفذ أخيراً)
app.add_middleware(Middleware2)  ← يُضاف ثانياً (يُنفذ أولاً)

# الطلب يمر هكذا:
Request → Middleware2 → Middleware1 → Endpoint
Response ← Middleware2 ← Middleware1 ← Endpoint

# لماذا؟
# Middleware مثل طبقات البصل!
```

---

#### السطر 95-96: Security Headers

```python
    # Security headers (outermost - runs last)
    app.add_middleware(SecurityHeadersMiddleware)
```

**ما يضيفه**:

```python
# كل استجابة تحصل على هذه headers:

Response Headers:
  X-Content-Type-Options: nosniff
  ← يمنع المتصفح من تفسير الملفات بشكل خاطئ
  ← حماية من MIME type sniffing attacks

  X-Frame-Options: DENY
  ← يمنع تضمين الموقع في iframe
  ← حماية من Clickjacking attacks

  X-XSS-Protection: 1; mode=block
  ← يفعّل XSS filter في المتصفح
  ← حماية من Cross-Site Scripting

  Strict-Transport-Security: max-age=31536000; includeSubDomains
  ← يجبر المتصفح على استخدام HTTPS
  ← حماية من Man-in-the-Middle attacks

  Content-Security-Policy: default-src 'self'
  ← يحدد المصادر المسموحة للـ JavaScript/CSS
  ← حماية من Code Injection
```

---

#### الأسطر 98-100: Rate Limiting

```python
    # Rate limiting
    if settings.app_env == "production":
        app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
```

**شرح**:

```python
# لماذا `if settings.app_env == "production"`؟
← Rate limiting مهم في production (حماية من abuse)
← لكن في development، نريده سريع بدون قيود
← نريده معطلاً لتجربة التطبيق بسهولة

# ما يحدث في production:
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
# ← يحدد 60 طلب في الدقيقة
# ← إذا تجاوز → 429 Too Many Requests

# كيف يعمل:
# request 1:   ✅ Allowed (1/60)
# request 2:   ✅ Allowed (2/60)
# ...
# request 60:  ✅ Allowed (60/60)
# request 61:  ❌ 429 Too Many Requests

# لماذا 60؟
← معدل معقول (1 طلب/ثانية)
← يحمي من abuse
← يوفر تكلفة LLM
```

---

#### الأسطر 102-109: CORS

```python
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

**شرح كل parameter**:

#### `allow_origins=settings.cors_origins`

```python
# ما هو؟
← قائمة الـ domains المسموحة بالاتصال

# القيمة من .env:
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ما يحدث:
# طلب من http://localhost:3000:
# ← Origin: http://localhost:3000
# ← CORS يتحقق: "3000" في القائمة؟ ← نعم ✅
# ← يضيف header: Access-Control-Allow-Origin: http://localhost:3000
# ← الطلب يُقبل

# طلب من http://evil.com:
# ← Origin: http://evil.com
# ← CORS يتحقق: "evil.com" في القائمة؟ ← لا ❌
# ← لا يضيف header
# ← الطلب يُرفض من المتصفح
```

#### `allow_credentials=True`

```python
# ما هو؟
← يسمح بإرسال cookies و authentication headers

# لماذا مهم؟
← Frontend يحتاج إرسال API key
← Frontend يحتاج إرسال session cookie
← بدون هذا، المصادقة لا تعمل!
```

#### `allow_methods=["*"]`

```python
# ما هو؟
← يسمح بكل HTTP methods

# ما يعني:
GET, POST, PUT, DELETE, PATCH, OPTIONS
← كل الطرق مسموحة

# لماذا "*"؟
← API يحتاج كل الطرق
← GET للـ health check
← POST للـ query
← PUT/DELETE لإدارة المستخدمين (مستقبلاً)
```

#### `allow_headers=["*"]`

```python
# ما هو؟
← يسمح بكل الـ headers

# ما يعني:
Content-Type, Authorization, X-API-Key, ...
← كل الـ headers مسموحة

# لماذا "*"؟
← Frontend يرسل headers مختلفة
← Content-Type: application/json
← X-API-Key: your-api-key
← Authorization: Bearer token
```

---

#### الأسطر 111-112: Error Handling

```python
    # Error handling
    app.middleware("http")(error_handler_middleware)
```

**شرح**:

```python
# ما هو error_handler_middleware؟
← دالة تمسك كل الأخطاء في التطبيق

# كيف يعمل:

async def error_handler_middleware(request, call_next):
    try:
        # يحاول معالجة الطلب
        response = await call_next(request)
        return response
    except Exception as e:
        # إذا فشل، يمسك الخطأ
        logger.error("error", error=str(e), exc_info=True)
        
        # يرجع استجابة خطأ منظمة
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Internal error: {str(e)}",
                "query_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat()
            }
        )

# مثال:
# بدون error_handler:
# خطأ في الكود → FastAPI يرجع:
# {"detail": "Internal Server Error"}

# مع error_handler:
# خطأ في الكود → error_handler يمسكه → يرجع:
# {
#     "error": "Internal error: division by zero",
#     "query_id": "550e8400-e29b-41d4-a716-446655440000",
#     "timestamp": "2024-04-14T10:30:00"
# }
```

---

### الأسطر 114-122: Routes Registration

```python
    # ==========================================
    # Routes
    # ==========================================
    app.include_router(health_router)
    app.include_router(query_router, prefix=settings.api_v1_prefix)
    app.include_router(tools_router, prefix=settings.api_v1_prefix)
    app.include_router(rag_router, prefix=f"{settings.api_v1_prefix}")
    app.include_router(quran_router, prefix=f"{settings.api_v1_prefix}")
```

**شرح كل router**:

#### `app.include_router(health_router)`

```python
# ما يفعل:
# يسجل endpoints من health.py

# endpoints المسجلة:
GET /health      ← فحص الصحة
GET /ready       ← فحص الجاهزية

# بدون prefix لأننا نريدها على الجذر

# مثال:
curl http://localhost:8000/health
# {"status": "ok"}
```

#### `app.include_router(query_router, prefix=settings.api_v1_prefix)`

```python
# ما يفعل:
# يسجل endpoints من query.py

# settings.api_v1_prefix = "/api/v1"
# endpoints المسجلة:
POST /api/v1/query  ← السؤال الرئيسي

# مثال:
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "ما حكم صلاة العيد؟"}'
```

#### `app.include_router(tools_router, prefix=settings.api_v1_prefix)`

```python
# ما يفعل:
# يسجل endpoints من tools.py

# endpoints المسجلة:
POST /api/v1/tools/zakat           ← حساب الزكاة
POST /api/v1/tools/inheritance     ← تقسيم الميراث
POST /api/v1/tools/prayer-times    ← أوقات الصلاة
POST /api/v1/tools/hijri           ← التاريخ الهجري
POST /api/v1/tools/duas            ← الأدعية
```

#### `app.include_router(rag_router, prefix=f"{settings.api_v1_prefix}")`

```python
# ما يفعل:
# يسجل endpoints من rag.py

# endpoints المسجلة:
POST /api/v1/rag/fiqh       ← RAG للفتاوى
POST /api/v1/rag/general    ← RAG عام
GET  /api/v1/rag/stats      ← إحصائيات RAG
```

#### `app.include_router(quran_router, prefix=f"{settings.api_v1_prefix}")`

```python
# ما يفعل:
# يسجل endpoints من quran.py

# endpoints المسجلة:
GET  /api/v1/quran/surahs              ← قائمة السور
GET  /api/v1/quran/surahs/{n}          ← سورة محددة
GET  /api/v1/quran/ayah/{s}:{a}        ← آية محددة
POST /api/v1/quran/search              ← بحث في القرآن
POST /api/v1/quran/validate            ← التحقق من اقتباس
POST /api/v1/quran/analytics           ← تحليلات NL2SQL
GET  /api/v1/quran/tafsir/{s}:{a}      ← تفسير آية
GET  /api/v1/quran/tafsir-sources      ← مصادر التفسير
```

**ملخص الـ 18 endpoint**:

| Router | Endpoints | Prefix |
|--------|-----------|--------|
| health | 2 | `/` |
| query | 1 | `/api/v1` |
| tools | 5 | `/api/v1` |
| rag | 3 | `/api/v1` |
| quran | 7 | `/api/v1` |
| **المجموع** | **18** | |

---

### الأسطر 124-170: Root Endpoint

```python
    # ==========================================
    # Root endpoint
    # ==========================================
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": "0.5.0",
            "phase": "5 - Security & Performance",
            "docs": "/docs",
            "health": "/health",
            "authentication": "API Key required (X-API-Key header)",
            "query_endpoint": f"{settings.api_v1_prefix}/query",
            "quran_endpoints": {
                "surahs": f"{settings.api_v1_prefix}/quran/surahs",
                "ayah": f"{settings.api_v1_prefix}/quran/ayah/{{surah}}:{{ayah}}",
                "search": f"{settings.api_v1_prefix}/quran/search",
                "validate": f"{settings.api_v1_prefix}/quran/validate",
                "analytics": f"{settings.api_v1_prefix}/quran/analytics",
                "tafsir": f"{settings.api_v1_prefix}/quran/tafsir/{{surah}}:{{ayah}}",
            },
            "tool_endpoints": {
                "zakat": f"{settings.api_v1_prefix}/tools/zakat",
                "inheritance": f"{settings.api_v1_prefix}/tools/inheritance",
                "prayer_times": f"{settings.api_v1_prefix}/tools/prayer-times",
                "hijri": f"{settings.api_v1_prefix}/tools/hijri",
                "duas": f"{settings.api_v1_prefix}/tools/duas",
            },
        }
```

**شرح**:

```python
# @app.get("/", tags=["Root"])
← يحدد endpoint لـ GET /

# async def root():
← الدالة التي تُنفذ عند访问 /

# return {...}
← يرجع JSON بكل معلومات التطبيق
```

**ما تراه عند访问 http://localhost:8000/**:

```json
{
  "name": "Burhan",
  "version": "0.5.0",
  "phase": "5 - Security & Performance",
  "docs": "/docs",
  "health": "/health",
  "authentication": "API Key required (X-API-Key header)",
  "query_endpoint": "/api/v1/query",
  "quran_endpoints": {
    "surahs": "/api/v1/quran/surahs",
    "ayah": "/api/v1/quran/ayah/{surah}:{ayah}",
    "search": "/api/v1/quran/search",
    "validate": "/api/v1/quran/validate",
    "analytics": "/api/v1/quran/analytics",
    "tafsir": "/api/v1/quran/tafsir/{surah}:{ayah}"
  },
  "tool_endpoints": {
    "zakat": "/api/v1/tools/zakat",
    "inheritance": "/api/v1/tools/inheritance",
    "prayer_times": "/api/v1/tools/prayer-times",
    "hijri": "/api/v1/tools/hijri",
    "duas": "/api/v1/tools/duas"
  }
}
```

**لماذا مهم؟**

```
← يعطي نظرة عامة سريعة على التطبيق
← يسهل على المطورين الجدد معرفة endpoints
← مثل "صفحة ترحيب" للتطبيق
```

---

### الأسطر 172-173: Return App

```python
    return app


# Create app instance
app = create_app()
```

**شرح**:

```python
# return app
← يرجع التطبيق المهيأ

# app = create_app()
← ينفذ create_app() ويحفظ النتيجة

# ما يحدث:
# 1. Uvicorn يستورد src.api.main
# 2. هذا ينفذ: app = create_app()
# 3. app الآن يحتوي على FastAPI application
# 4. Uvicorn يستخدم app لاستقبال الطلبات
```

---

## 5️⃣ المصطلحات المهمة

### Factory Pattern

**تعريف**: نمط تصميم يستخدم دالة لإنشاء كائنات بدلاً من المنشئ مباشرة.

**في هذا الملف**: `create_app()` تنشيء FastAPI application

**لماذا مهم**:
- يسهل الاختبار
- يسهل إعادة الاستخدام
- ينظم الكود

---

### Middleware

**تعريف**: طبقة برمجية تمر عليها كل الطلبات قبل الوصول للـ endpoint.

**في هذا الملف**: 4 middleware (Security, CORS, Rate Limiting, Error Handling)

**لماذا مهم**:
- يتعامل مع مهام مشتركة
- يبقي الـ endpoint نظيفة
- يسهل الصيانة

---

### Lifespan

**تعريف**: دالة تُنفذ عند بدء وإيقاف التطبيق.

**في هذا الملف**: `lifespan()` تهيئ logging عند البدء

**لماذا مهم**:
- يدير دورة حياة التطبيق
- يهيئ الموارد
- ينظف الموارد عند الإيقاف

---

### Router

**تعريف**: مجموعة endpoints مترابطة في ملف واحد.

**في هذا الملف**: 5 routers (health, query, tools, rag, quran)

**لماذا مهم**:
- ينظم الكود
- يسهل الصيانة
- يسهل الاختبار

---

## 6️⃣ ملاحظات هندسية

### ✅ نقاط القوة

1. **Factory Pattern**: يسهل الاختبار وإعادة الاستخدام
2. **Lifespan Management**: إدارة نظيفة لدورة حياة التطبيق
3. **Middleware Ordering**: مرتب بعناية
4. **Conditional Middleware**: Rate limiting في production فقط
5. **Comprehensive Root Endpoint**: يعطي كل المعلومات

### ⚠️ نقاط التحسين

1. **Lifespan يمكن توسيعه**: إضافة DB connection validation
2. **Hardcoded version**: "0.5.0" يمكن نقلها إلى settings
3. **No startup validation**: لا يتحقق من DB/Redis/Qdrant عند البدء

### 🔧 مقترح Refactoring

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    
    # Validate connections
    try:
        await validate_db_connection()
        await validate_redis_connection()
        await validate_qdrant_connection()
    except Exception as e:
        logger.error("Startup validation failed", error=str(e))
        raise
    
    logger.info("app.startup", ...)
    
    yield
    
    # Shutdown
    await close_connections()
    logger.info("app.shutdown")
```

---

## 📊 الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً؟

1. **`main.py` هو نقطة البداية** لكل شيء
2. **Factory Pattern** (`create_app()`) يسمح بإنشاء تطبيقات متعددة
3. **Middleware مرتبة بعناية** (Security → Rate Limit → CORS → Error Handling)
4. **Lifespan function** تدير البدء والإيقاف
5. **5 routers** مسجلين مع التطبيق (18 endpoint)

### 📝 تمرين صغير

1. افتح `src/api/main.py`
2. عد كم middleware موجود
3. ما هو الترتيب؟ لماذا هذا الترتيب؟
4. كم endpoint مسجل؟ ما هي؟
5. شغل التطبيق: `make dev`
6. افتح http://localhost:8000/
7. ما الذي تراه؟

### 🔜 الخطوة التالية

اقرأ الملف التالي: `src/api/routes/query.py` (الـ endpoint الرئيسي)

---

**📖 الدليل الكامل:** [`docs/mentoring/`](docs/mentoring/)

**🚀 الملف التالي:** `src/api/routes/query.py`

---

**مُعد الشرح:** AI Mentor System  
**التاريخ:** أبريل 2026  
**الإصدار:** 1.0  
**الحالة:** ✅ شرح سطر بسطر كامل
