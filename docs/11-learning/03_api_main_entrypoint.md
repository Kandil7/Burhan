# 🚀 نقطة الدخول - الجزء الثالث: `src/api/main.py`

## 1️⃣ وظيفة الملف

### ما دور هذا الملف داخل المشروع؟
هذا هو **ملف إنشاء التطبيق** (App Factory). عندما تشغل `make dev` أو `uvicorn src.api.main:app`، هذا الملف هو الذي:
1. ينشئ تطبيق FastAPI
2. يضيف الـ middleware (الأمان، CORS، معالجة الأخطاء)
3. يسجل الـ routers (الـ endpoints)
4. يهيئ الـ logging

### لماذا وجوده مهم؟
بدون هذا الملف، **لا يوجد تطبيق**! هو نقطة البداية لكل شيء.

### ما علاقته بباقي الملفات؟
```
main.py
    ├── يستورد: routes/*.py (الـ endpoints)
    ├── يستورد: middleware/*.py (الأمان)
    ├── يستورد: config/settings.py (الإعدادات)
    └── يستورد: config/logging_config.py (التسجيل)
```

---

## 2️⃣ نظرة عامة على محتويات الملف

###imports
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.config.settings import settings
from src.config.logging_config import setup_logging
from src.api.middleware.error_handler import error_handler_middleware
from src.api.middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    APIKeyMiddleware,
    InputSanitizationMiddleware,
)
from src.api.routes import health, query, tools, rag, quran
```

###constants
- `APP_NAME`: "Athar Islamic QA System"
- `APP_VERSION`: "0.5.0"
- `PHASE`: "Phase 5: Security & Performance"

###classes
- لا يوجد classes مباشرة في الملف (يستخدم factory function)

###functions
- `lifespan(app: FastAPI)`: يُنفذ عند البدء وعند الإيقاف
- `create_app() -> FastAPI`: الدالة الرئيسية لإنشاء التطبيق

###main execution block
```python
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 3️⃣ شرح الملف جزء جزء

###imports Block

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
```

**ما يفعله**:
- يستورد FastAPI (إطار عمل الويب)
- يستورد CORSMiddleware (للسماح بالطلبات من المتصفح)
- يستورد asynccontextmanager (لإدارة دورة حياة التطبيق)

**لماذا مهم**:
- FastAPI هو العمود الفقري لكل الـ API
- CORS ضروري للـ frontend (يختلف المنفذ عن backend)

---

###إعدادات التطبيق الأساسية

```python
from src.config.settings import settings
from src.config.logging_config import setup_logging
```

**ما يفعله**:
- يجلب الإعدادات من `.env` عبر Pydantic Settings
- يهيئ structured logging باستخدام structlog

**لماذا مهم**:
- `settings.llm_provider` يحدد إذا كان يستخدم Groq أم OpenAI
- `settings.debug` يحدد مستوى التفصيل في الـ logs

---

###Middleware imports

```python
from src.api.middleware.error_handler import error_handler_middleware
from src.api.middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    APIKeyMiddleware,
    InputSanitizationMiddleware,
)
```

**ما يفعله**:
- يستورد 5 middleware للأمان

**الـ Middleware بالترتيب (من الخارج للداخل)**:
```
طلب HTTP
    ↓
1. SecurityHeadersMiddleware    ← يضيف headers أمنية
    ↓
2. RateLimitMiddleware          ← يحدد 60 طلب/دقيقة
    ↓
3. CORSMiddleware               ← يسمح للـ frontend
    ↓
4. InputSanitizationMiddleware  ← ينظف المدخلات
    ↓
5. APIKeyMiddleware             ← يتحقق من API key
    ↓
6. error_handler_middleware     ← يمسك الأخطاء
    ↓
الـ router (endpoint)
```

---

###Routes imports

```python
from src.api.routes import health, query, tools, rag, quran
```

**ما يفعله**:
- يستورد 5 routers (مجموعات endpoints)

| Router | Prefix | عدد Endpoints |
|--------|--------|---------------|
| `health` | `/` | 2 (`/health`, `/ready`) |
| `query` | `/api/v1` | 1 (`/query`) |
| `tools` | `/api/v1` | 5 (`/tools/*`) |
| `quran` | `/api/v1` | 6 (`/quran/*`) |
| `rag` | `/api/v1` | 3 (`/rag/*`) |

---

###Lifespan Function

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Athar starting up", environment=settings.environment)
    
    yield
    
    # Shutdown
    logger.info("Athar shutting down")
```

**ما يفعله**:
1. **عند البدء**: يهيئ logging
2. **أثناء التشغيل**: `yield` يسمح للتطبيق بالعمل
3. **عند الإيقاف**: يسجل رسالة إيقاف

**لماذا مهم**:
- بدون `setup_logging()`, لا توجد logs منظمة
- يمكن إضافة هنا: فتح DB connections, تحميل models في الذاكرة

---

###Create App Function (الدالة الرئيسية)

```python
def create_app() -> FastAPI:
    app = FastAPI(
        title="Athar Islamic QA System",
        version="0.5.0",
        description="Production-ready Islamic QA system",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
```

**المدخلات**: لا يوجد (يقرأ من `settings`)

**المخرجات**: كائن FastAPI جاهز

**ما يفعله**:
1. ينشئ تطبيق FastAPI بالمواصفات:
   - الاسم: "Athar Islamic QA System"
   - الإصدار: "0.5.0"
   - الـ docs على `/docs` (Swagger)
   - الـ redoc على `/redoc`

---

###إضافة Middleware

```python
    # Security headers (always enabled)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Rate limiting (production only)
    if settings.is_production:
        app.add_middleware(
            RateLimitMiddleware,
            rate_limit_per_minute=60,
            rate_limit_burst=10,
        )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Input sanitization
    app.add_middleware(InputSanitizationMiddleware)
    
    # API key (if configured)
    if settings.api_key_required:
        app.add_middleware(APIKeyMiddleware)
    
    # Error handler (must be last = outermost)
    app.add_middleware(error_handler_middleware)
```

**لماذا الترتيب مهم**:

```
الترتيب في الكود (من الأول للأخير):
1. SecurityHeadersMiddleware      ← داخلي أولاً
2. RateLimitMiddleware            ← ثم هذا
3. CORSMiddleware                 ← ثم هذا
4. InputSanitizationMiddleware    ← ثم هذا
5. APIKeyMiddleware               ← ثم هذا
6. error_handler_middleware       ← خارجي أخيراً

الطلب يمر من الخارج للداخل:
Internet → error_handler → API_key → sanitize → CORS → rate_limit → security_headers → router
```

**ملاحظات هندسية**:
- ✅ Rate limiting فقط في production (لتجنب البطء في development)
- ✅ API key اختياري (يمكن تعطيله في development)
- ✅ Error handler في الخارج ليمسك كل الأخطاء

---

###تسجيل Routers

```python
    # Include routers
    app.include_router(health.router)
    app.include_router(query.router, prefix="/api/v1")
    app.include_router(tools.router, prefix="/api/v1")
    app.include_router(quran.router, prefix="/api/v1")
    app.include_router(rag.router, prefix="/api/v1")
```

**ما يفعله**:
- يسجل 5 routers مع التطبيق

**لماذا مهم**:
- بدون هذا، الـ endpoints لن تعمل!
- كل router يحتوي على مجموعة endpoints

**النتيجة**:
```
/api/v1/query          ← query.router
/api/v1/tools/*        ← tools.router
/api/v1/quran/*        ← quran.router
/api/v1/rag/*          ← rag.router
/health                ← health.router
/ready                 ← health.router
```

---

###إعدادات إضافية

```python
    # Health check endpoint for Docker
    @app.get("/ping")
    async def ping():
        return {"status": "ok"}
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "Athar Islamic QA System",
            "version": "0.5.0",
            "phase": "Phase 5: Security & Performance",
            "docs": "/docs",
        }
```

**ما يفعله**:
- `/ping`: لـ Docker health checks
- `/`: معلومات التطبيق

**لماذا مهم**:
- `/ping` يستخدم في Docker Compose للتحقق من أن التطبيق يعمل
- `/` يعطي معلومات سريعة للمستخدم

---

###Return و Run

```python
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower(),
    )
```

**ما يفعله**:
1. `create_app()` ينشئ التطبيق
2. `uvicorn.run()` يشغله على المنفذ 8000

**لماذا مهم**:
- عند تشغيل `make dev`, هذا ما يحدث
- `host="0.0.0.0"` يعني يقبل طلبات من أي مكان (ليس فقط localhost)

---

## 4️⃣ شرح سطر سطر

###الأسطر 1-10: Imports الأساسية
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
```
- يستورد المكونات الأساسية من FastAPI

###الأسطر 11-20: Imports من المشروع
```python
from src.config.settings import settings
from src.config.logging_config import setup_logging
from src.api.middleware.error_handler import error_handler_middleware
from src.api.middleware.security import (...)
from src.api.routes import health, query, tools, rag, quran
```
- يستورد كل المكونات من المشروع

###الأسطر 21-35: Lifespan function
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Athar starting up")
    yield
    logger.info("Athar shutting down")
```
- يدير دورة حياة التطبيق

###الأسطر 36-70: Create app function
```python
def create_app() -> FastAPI:
    app = FastAPI(...)
    app.add_middleware(...)
    app.include_router(...)
    return app
```
- ينشئ التطبيق ويهيئه

###الأسطر 71-85: Run
```python
app = create_app()
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
- يشغل التطبيق

---

## 5️⃣ المصطلحات المهمة

### FastAPI
**تعريف**: إطار عمل Python حديث لبناء APIs بسرعة عالية.

**لماذا مهم**:
- أسرع من Flask بـ 10x
- يدعم async/await بشكل أصلي
- يولد Swagger docs تلقائياً

**في هذا المشروع**: كل الـ 18 endpoint مبنية بـ FastAPI

---

### Middleware
**تعريف**: طبقة برمجية تمر عليها كل الطلبات قبل الوصول للـ endpoint.

**لماذا مهم**:
- يتعامل مع مهام مشتركة (أمان، CORS, logging)
- يبقي الـ endpoint نظيفة ومنطقها واضح

**في هذا المشروع**: 6 middleware مرتبة بعناية

---

### Lifespan
**تعريف**: دالة تُنفذ عند بدء وإيقاف التطبيق.

**لماذا مهم**:
- تهيئة الموارد (DB connections, cache warming)
- تنظيف الموارد عند الإيقاف

**في هذا المشروع**: يهيئ logging فقط (يمكن توسيعه)

---

### Router
**تعريف**: مجموعة endpoints مترابطة في ملف واحد.

**لماذا مهم**:
- ينظم الكود (كل feature في ملف)
- يسهل الصيانة والاختبار

**في هذا المشروع**: 5 routers (health, query, tools, quran, rag)

---

### CORS (Cross-Origin Resource Sharing)
**تعريف**: آلية تسمح للمتصفح بطلب موارد من domain مختلف.

**لماذا مهم**:
- بدون CORS, الـ frontend (localhost:3000) لا يمكنه طلب الـ backend (localhost:8000)
- المتصفح يرفض الطلبات عبر الـ domains المختلفة افتراضياً

**في هذا المشروع**: يسمح للـ frontend بالاتصال بالـ backend

---

## 6️⃣ ملاحظات هندسية

### ✅ نقاط القوة
1. **Factory Pattern**: `create_app()` يسهل الاختبار (يمكن إنشاء تطبيقات متعددة)
2. **Middleware Ordering**: مرتب بعناية من الخارج للداخل
3. **Conditional Middleware**: rate limiting و API key فقط عند الحاجة
4. **Lifespan Management**: إدارة نظيفة لدورة حياة التطبيق

### ⚠️ نقاط التحسين
1. **Lifescan يمكن توسيعه**: إضافة DB connection pool initialization
2. **No startup validation**: لا يتحقق من أن DB/Redis/Qdrant متصلين عند البدء
3. **Hardcoded version**: "0.5.0" يمكن نقلها إلى settings

### 🔧 مقترحات Refactoring
```python
# إضافة startup validation
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    
    # Validate connections
    try:
        await validate_db_connection()
        await validate_redis_connection()
        await validate_qdrant_connection()
    except Exception as e:
        logger.error("Startup validation failed", error=str(e))
        raise
    
    yield
    
    # Cleanup
    await close_connections()
```

---

## 📊 الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً من هذا الجزء؟

1. **`main.py` هو نقطة البداية** لكل شيء في التطبيق
2. **Factory Pattern** (`create_app()`) يسمح بإنشاء تطبيقات متعددة
3. **Middleware مرتبة بعناية** من الخارج للداخل
4. **5 routers** مسجلين مع التطبيق (18 endpoint)
5. **Lifespan function** تدير البدء والإيقاف

### 📝 تمرين صغير

1. شغل التطبيق: `make dev`
2. افتح: http://localhost:8000/docs
3. كم endpoint ترى؟ ما هي الـ routers الخمسة؟

### 🔜 الخطوة التالية المنطقية

اقرأ الملف التالي: `src/api/routes/query.py` (الـ endpoint الرئيسي)

---

**📖 الملف التالي في السلسلة:** الجزء الرابع - الـ endpoint الرئيسي (`src/api/routes/query.py`)
