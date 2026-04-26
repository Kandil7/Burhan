# 📚 أهم 10 ملفات في Burhan - شرح سطر بسطر

## 🕌 مقدمة

هذا الدليل يشرح **أهم 10 ملفات** في مشروع Burhan **سطر بسطر** بالتفصيل الكامل.

### الترتيب المقترح

| الأولوية | الملف | الحجم | السبب |
|----------|-------|-------|-------|
| 1 | `src/config/settings.py` | 140 سطر | كل الإعدادات |
| 2 | `src/config/intents.py` | 180 سطر | 16 نوع نية |
| 3 | `src/core/router.py` | 250 سطر | تصنيف النية |
| 4 | `src/core/registry.py` | 190 سطر | تسجيل الوكلاء |
| 5 | `src/core/citation.py` | 350 سطر | تطبيع الاقتباسات |
| 6 | `src/agents/base.py` | 90 سطر | الفئات الأساسية |
| 7 | `src/agents/chatbot_agent.py` | 160 سطر | أبسط وكيل |
| 8 | `src/agents/fiqh_agent.py` | 280 سطر | وكيل RAG كامل |
| 9 | `src/tools/base.py` | 70 سطر | فئة الأدوات |
| 10 | `src/tools/zakat_calculator.py` | 350 سطر | حاسبة الزكاة |

---

# الملف 1: `src/config/settings.py` (140 سطر)

## 1️⃣ وظيفة الملف

هذا الملف يحتوي على **كل إعدادات التطبيق**. يستخدم Pydantic BaseSettings لقراءة متغيرات البيئة من ملف `.env`.

## 2️⃣ نظرة عامة

| القسم | الأسطر | المحتوى |
|-------|--------|---------|
| Imports | 1-10 | مكتبات أساسية |
| Settings class | 11-140 | كل الإعدادات |
| Validators | 100-130 | التحقق من الإعدادات |
| Properties | 130-140 | خصائص محسوبة |

## 3️⃣ شرح سطر بسطر

### الأسطر 1-10: Imports الأساسية

```python
"""
Application settings with environment variable support.

Uses Pydantic BaseSettings for automatic environment variable parsing.

Phase 5: Added security, rate limiting, and caching settings.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path
```

**شرح**:
- `Field`: لتحديد حقول Pydantic مع قيود
- `field_validator`: للتحقق من صحة الحقول
- `BaseSettings`: فئة أساسية للإعدادات مع دعم `.env`
- `SettingsConfigDict`: تكوين الإعدادات
- `Optional`: للقيم الاختيارية
- `Path`: للتعامل مع المسارات

**لماذا مهم**: بدون هذه المكتبات، لا يمكن قراءة الإعدادات من `.env`.

---

### الأسطر 11-20: إعدادات التطبيق الأساسية

```python
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
```

**شرح**:
- `Settings(BaseSettings)`: فئة ترث من Pydantic Settings
- `model_config`: تكوين كيفية قراءة الإعدادات
  - `env_file=".env"`: يقرأ من ملف `.env`
  - `env_file_encoding="utf-8"`: ترميز UTF-8
  - `case_sensitive=False`: لا يفرق بين الحروف
  - `extra="ignore"`: يتجاهل المتغيرات غير المعروفة

**ما يحدث**:
```
عند إنشاء Settings():
1. يبحث عن ملف .env
2. يقرأ كل المتغيرات
3. يطابقها مع الحقول المعرفة
4. يستخدم القيم الافتراضية إذا لم توجد
```

---

### الأسطر 21-30: إعدادات التطبيق

```python
    # ==========================================
    # Application
    # ==========================================
    app_name: str = "Burhan"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = "change-this-in-production-please-use-random-string"
    api_v1_prefix: str = "/api/v1"
```

**شرح كل متغير**:

| المتغير | النوع | القيمة الافتراضية | ماذا يفعل |
|---------|-------|-------------------|------------|
| `app_name` | str | "Burhan" | اسم التطبيق |
| `app_env` | str | "development" | البيئة (development/production) |
| `debug` | bool | False | وضع التصحيح |
| `secret_key` | str | "change-this..." | مفتاح التشفير |
| `api_v1_prefix` | str | "/api/v1" | بادئة الـ API |

**لماذا مهم**:
- `app_env` يحدد إذا كان rate limiting مفعل
- `debug` يحدد مستوى الـ logging
- `secret_key` يستخدم لتشفير JWT sessions

**ماذا يحدث إذا فقد**:
- بدون `secret_key`: لا يمكن تشفير الجلسات
- بدون `api_v1_prefix`: الـ endpoints لن تعمل

---

### الأسطر 31-40: إعدادات قاعدة البيانات

```python
    # ==========================================
    # Database (PostgreSQL 16)
    # ==========================================
    database_url: str = "postgresql+asyncpg://Burhan:Burhan_password@localhost:5432/Burhan_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
```

**شرح**:

| المتغير | القيمة | الوصف |
|---------|--------|-------|
| `database_url` | postgresql+asyncpg://... | رابط قاعدة البيانات |
| `database_pool_size` | 10 | عدد الاتصالات في الـ pool |
| `database_max_overflow` | 20 | الحد الأقصى للاتصالات الإضافية |

**ما يعني `postgresql+asyncpg`**:
- `postgresql`: نوع قاعدة البيانات
- `asyncpg`: driver غير متزامن (async)

**رابط قاعدة البيانات يتكون من**:
```
postgresql+asyncpg://user:password@host:port/database
                      ↓    ↓       ↓    ↓     ↓
                   Burhan  Burhan_password  localhost  5432  Burhan_db
```

**لماذا مهم**: بدون هذا الرابط، لا يمكن الاتصال بقاعدة البيانات.

---

### الأسطر 41-50: إعدادات Redis

```python
    # ==========================================
    # Redis
    # ==========================================
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
```

**شرح**:

| المتغير | القيمة | الوصف |
|---------|--------|-------|
| `redis_url` | redis://localhost:6379/0 | رابط Redis |
| `redis_max_connections` | 50 | الحد الأقصى للاتصالات |

**ما يستخدم Redis في Burhan**:
1. **Embedding cache**: حفظ المتجهات المولدة
2. **Rate limiting**: تتبع عدد الطلبات
3. **Session storage**: حفظ جلسات المستخدمين

**رابط Redis**:
```
redis://localhost:6379/0
       ↓        ↓     ↓
     protocol  host  port  db_number
```

---

### الأسطر 51-60: إعدادات Qdrant

```python
    # ==========================================
    # Qdrant (Vector Database)
    # ==========================================
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection_fiqh: str = "fiqh_passages"
    qdrant_collection_hadith: str = "hadith_passages"
    qdrant_collection_dua: str = "dua_passages"
    qdrant_collection_general: str = "general_islamic"
```

**شرح**:

| المتغير | الوصف |
|---------|-------|
| `qdrant_url` | رابط قاعدة المتجهات |
| `qdrant_api_key` | مفتاح API (اختياري) |
| `qdrant_collection_*` | أسماء المجموعات |

**ما هي Qdrant؟**:
قاعدة بيانات متخصصة في تخزين والبحث عن **المتجهات** (vectors).

**لماذا مهم**:
- بدون Qdrant، لا يمكن البحث الدلالي (semantic search)
- كل الوكلاء (Fiqh, Hadith, General) يحتاجون Qdrant

---

### الأسطر 61-75: إعدادات LLM

```python
    # ==========================================
    # LLM Provider
    # ==========================================
    llm_provider: str = "openai"  # openai or groq
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    groq_api_key: Optional[str] = None
    groq_model: str = "qwen/qwen3-32b"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048

    # HuggingFace
    hf_token: Optional[str] = None

    @property
    def llm_model(self) -> str:
        """Return the correct model based on provider."""
        return self.groq_model if self.llm_provider == "groq" else self.openai_model
```

**شرح**:

| المتغير | الوصف |
|---------|-------|
| `llm_provider` | مزود الـ LLM (openai أو groq) |
| `openai_api_key` | مفتاح OpenAI |
| `openai_model` | نموذج OpenAI |
| `groq_api_key` | مفتاح Groq |
| `groq_model` | نموذج Groq |
| `llm_temperature` | حرارة التوليد (0.1 = دقيق جداً) |
| `llm_max_tokens` | الحد الأقصى للرموز |

**`llm_model` property**:
```python
@property
def llm_model(self) -> str:
    return self.groq_model if self.llm_provider == "groq" else self.openai_model
```

**ما يفعل**:
- إذا `llm_provider == "groq"`: يرجع `groq_model`
- وإلا: يرجع `openai_model`

**لماذا مهم**: يسمح بتغيير المزود بدون تغيير الكود.

---

### الأسطر 76-85: إعدادات التضمين

```python
    # ==========================================
    # Embeddings
    # ==========================================
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimension: int = 1024
```

**شرح**:

| المتغير | الوصف |
|---------|-------|
| `embedding_model` | نموذج التضمين |
| `embedding_dimension` | أبعاد المتجه |

**ما هو Embedding؟**:
تحويل النص إلى **متجه رقمي** (vector) في فضاء متعدد الأبعاد.

**مثال**:
```
"ما حكم صلاة العيد؟" → [0.12, -0.34, 0.56, ...] (1024 رقم)
```

**لماذا مهم**:
- بدون embedding، لا يمكن البحث الدلالي
- RAG يحتاج embedding لمقارنة الأسئلة

---

### الأسطر 86-100: إعدادات التوجيه والأمان

```python
    # ==========================================
    # Routing
    # ==========================================
    router_confidence_threshold: float = 0.75
    router_fallback_enabled: bool = True

    # ==========================================
    # Rate Limiting
    # ==========================================
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # ==========================================
    # Security
    # ==========================================
    api_key_enabled: bool = False  # Enable in production
    cors_max_age: int = 600

    # ==========================================
    # Caching
    # ==========================================
    llm_cache_enabled: bool = True
    llm_cache_ttl: int = 3600  # 1 hour
```

**شرح**:

| المتغير | القيمة | الوصف |
|---------|--------|-------|
| `router_confidence_threshold` | 0.75 | عتبة الثقة للتصنيف |
| `router_fallback_enabled` | True | تفعيل fallback |
| `rate_limit_enabled` | True | تحديد عدد الطلبات |
| `rate_limit_per_minute` | 60 | 60 طلب في الدقيقة |
| `api_key_enabled` | False | مفتاح API (production فقط) |
| `cors_max_age` | 600 | عمر CORS Preflight (10 دقائق) |
| `llm_cache_enabled` | True | تخزين إجابات LLM |
| `llm_cache_ttl` | 3600 | عمر التخزين (ساعة) |

**لماذا مهم**:
- `rate_limit` يحمي من abuse
- `llm_cache` يقلل التكلفة (لا يعيد نفس الإجابة)
- `api_key` يحمي الـ API في production

---

### الأسطر 101-130: Validators

```python
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
```

**شرح**:
- `@field_validator`: يتحقق من صحة الحقل قبل تعيينه
- `parse_cors_origins`: يحول string إلى list

**مثال**:
```python
# Input: "http://localhost:3000,http://localhost:5173"
# Output: ["http://localhost:3000", "http://localhost:5173"]
```

**لماذا مهم**: CORS يحتاج list، لكن `.env` يحتوي string.

---

```python
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()
```

**شرح**:
- يتحقق أن مستوى الـ logging صحيح
- يحوله إلى uppercase

**مثال**:
```python
# Input: "info" → Output: "INFO"
# Input: "invalid" → ValueError
```

---

```python
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        """Ensure secret key is changed from default."""
        if v == "change-this-in-production-please-use-random-string":
            import warnings
            warnings.warn("Using default secret key! Change this in production.", UserWarning)
        return v
```

**شرح**:
- يتحقق أن `secret_key` ليس القيمة الافتراضية
- يعطي تحذير إذا كان كذلك

**لماذا مهم**:
- secret_key الافتراضي يعني أن الجلسات غير آمنة
- يجب تغييره في production

---

### الأسطر 131-140: Properties

```python
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


# Singleton instance
settings = Settings()
```

**شرح**:
- `is_production`: يرجع True إذا البيئة production
- `is_development`: يرجع True إذا البيئة development
- `settings = Settings()`: ينشئ نسخة واحدة (singleton)

**كيف يستخدم**:
```python
from src.config.settings import settings

if settings.is_production:
    # تفعيل rate limiting
    app.add_middleware(RateLimitMiddleware)
```

---

## 5️⃣ الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً؟

1. **Settings يقرأ من `.env`** تلقائياً عبر Pydantic
2. **كل الإعدادات في مكان واحد** - لا hardcoded values
3. **Validators تتحقق من صحة الإعدادات**
4. **Singleton instance** - نسخة واحدة في كل التطبيق

### 📝 تمرين صغير

1. افتح ملف `.env.example`
2. ما الفرق بين `llm_provider` و `llm_model`؟
3. لماذا `qdrant_api_key` Optional؟

### 🔜 الخطوة التالية

اقرأ الملف 2: `src/config/intents.py`

---

# الملف 2: `src/config/intents.py` (180 سطر)

## 1️⃣ وظيفة الملف

هذا الملف يحدد **كل أنواع النية** (intents) في النظام. كل نية تمثل **نوع سؤال** يمكن للمستخدم أن يسأله.

## 2️⃣ نظرة عامة

| القسم | الأسطر | المحتوى |
|-------|--------|---------|
| Intent Enum | 1-20 | 16 نوع نية |
| QuranSubIntent | 21-35 | 4 نيات فرعية للقرآن |
| INTENT_DESCRIPTIONS | 36-55 | وصف كل نية |
| INTENT_ROUTING | 56-80 | توجيه كل نية لوكيل |
| KEYWORD_PATTERNS | 81-170 | كلمات مفتاحية لكل نية |
| Helper functions | 171-180 | دوال مساعدة |

## 3️⃣ شرح سطر بسطر

### الأسطر 1-20: Intent Enum

```python
from enum import Enum
from typing import Optional


class Intent(str, Enum):
    """
    Supported query intents for Burhan Islamic QA system.

    Based on Fanar-Sadiq hybrid query classifier with 15 primary intents.
    """

    FIQH = "fiqh"
    QURAN = "quran"
    ISLAMIC_KNOWLEDGE = "islamic_knowledge"
    GREETING = "greeting"
    ZAKAT = "zakat"
    INHERITANCE = "inheritance"
    DUA = "dua"
    HIJRI_CALENDAR = "hijri_calendar"
    PRAYER_TIMES = "prayer_times"
    HADITH = "hadith"
    TAFSIR = "tafsir"
    AQEEDAH = "aqeedah"
    SEERAH = "seerah"
    USUL_FIQH = "usul_fiqh"
    ISLAMIC_HISTORY = "islamic_history"
    ARABIC_LANGUAGE = "arabic_language"
```

**شرح**:

| النية | الوكيل المسؤول | مثال سؤال |
|-------|---------------|-----------|
| `FIQH` | fiqh_agent | "ما حكم صلاة العيد؟" |
| `QURAN` | quran_agent | "ما تفسير آية الكرسي؟" |
| `ISLAMIC_KNOWLEDGE` | general_islamic_agent | "ما فضل الصيام؟" |
| `GREETING` | chatbot_agent | "السلام عليكم" |
| `ZAKAT` | zakat_tool | "كيف أحسب الزكاة؟" |
| `INHERITANCE` | inheritance_tool | "كيف أقسم الميراث؟" |
| `DUA` | dua_tool | "دعاء السفر" |
| `HIJRI_CALENDAR` | hijri_tool | "متى يبدأ رمضان؟" |
| `PRAYER_TIMES` | prayer_tool | "متى صلاة الفجر؟" |
| `HADITH` | hadith_agent | "ما حكم هذا الحديث؟" |
| `TAFSIR` | general_islamic_agent | "ما تفسير هذه الآية؟" |
| `AQEEDAH` | general_islamic_agent | "ما معنى التوحيد؟" |
| `SEERAH` | seerah_agent | "متى ولد النبي؟" |
| `USUL_FIQH` | general_islamic_agent | "ما مصادر التشريع؟" |
| `ISLAMIC_HISTORY` | general_islamic_agent | "متى كانت غزوة بدر؟" |
| `ARABIC_LANGUAGE` | general_islamic_agent | "ما معنى هذه الكلمة؟" |

**لماذا Enum؟**:
- يحدد القيم المسموحة (لا يمكن إضافة نية جديدة بدون تعديل الكود)
- يساعد الـ type checker في اكتشاف الأخطاء

---

### الأسطر 21-40: QuranSubIntent

```python
class QuranSubIntent(str, Enum):
    """
    Sub-intents for Quran queries.

    Used by Quran router to direct to appropriate pipeline:
    - verse_lookup: Exact verse retrieval (2:255, Ayat al-Kursi, etc.)
    - interpretation: Tafsir and meaning
    - analytics: NL2SQL for statistics (count, length, etc.)
    - quotation_validation: Verify if text is actually a Quran verse
    """

    VERSE_LOOKUP = "verse_lookup"
    INTERPRETATION = "interpretation"
    ANALYTICS = "analytics"
    QUOTATION_VALIDATION = "quotation_validation"
```

**شرح**:

| النية الفرعية | الوصف | مثال |
|---------------|-------|------|
| `VERSE_LOOKUP` | البحث عن آية محددة | "ما هي آية الكرسي؟" |
| `INTERPRETATION` | التفسير والمعنى | "ما تفسير هذه الآية؟" |
| `ANALYTICS` | إحصائيات | "كم مرة ذكرت كلمة الرحمة؟" |
| `QUOTATION_VALIDATION` | التحقق من اقتباس | "هل هذا من القرآن؟" |

**لماذا مهم**:
- النية الرئيسية `quran` عامة جداً
- النية الفرعية تحدد **أي pipeline** يستخدم

---

### الأسطر 41-70: INTENT_DESCRIPTIONS

```python
INTENT_DESCRIPTIONS = {
    Intent.FIQH: "Islamic jurisprudence (halal/haram, worship, transactions, rulings, fiqh questions)",
    Intent.QURAN: "Quranic verses, surahs, tafsir, or Quran statistics",
    Intent.ISLAMIC_KNOWLEDGE: "General Islamic knowledge (history, biography, theology, concepts)",
    Intent.GREETING: "Greetings, salutations, polite phrases (As-salamu alaykum, Ramadan Kareem, etc.)",
    Intent.ZAKAT: "Calculate zakat on wealth, gold, silver, trade goods, livestock",
    Intent.INHERITANCE: "Calculate inheritance distribution (fara'id, mirath, estate division)",
    Intent.DUA: "Request specific duas or adhkar (supplications, remembrance, Hisn al-Muslim)",
    Intent.HIJRI_CALENDAR: "Hijri dates, Ramadan dates, Eid dates, Islamic calendar conversion",
    Intent.PRAYER_TIMES: "Prayer times or qibla direction for a location",
    Intent.HADITH: "Hadith retrieval, authentication, sanad, and matn (Prophetic traditions)",
    Intent.TAFSIR: "Quran interpretation and exegesis (Ibn Kathir, Al-Jalalayn, Al-Qurtubi)",
    Intent.AQEEDAH: "Islamic creed and theology (Tawhid, faith, beliefs, theological questions)",
    Intent.SEERAH: "Prophet Muhammad's biography and life events (Seerah, prophetic history)",
    Intent.USUL_FIQH: "Principles of Islamic jurisprudence (methodology, sources of Islamic law)",
    Intent.ISLAMIC_HISTORY: "Islamic history and civilization (historical events, figures, culture)",
    Intent.ARABIC_LANGUAGE: "Arabic language: grammar (nahw), morphology (sarf), rhetoric (balaghah), literature, poetry, dictionaries",
}
```

**شرح**:
- قاموس يربط كل نية بـ **وصفه**
- يستخدم في **LLM classification prompt**

**كيف يستخدم**:
```python
prompt = f"""
Available Intents:
{intent_descriptions}
"""
```

---

### الأسطر 71-100: INTENT_ROUTING

```python
INTENT_ROUTING = {
    Intent.FIQH: "fiqh_agent",
    Intent.QURAN: "quran_agent",
    Intent.ISLAMIC_KNOWLEDGE: "general_islamic_agent",
    Intent.GREETING: "chatbot_agent",
    Intent.ZAKAT: "zakat_tool",
    Intent.INHERITANCE: "inheritance_tool",
    Intent.DUA: "dua_tool",
    Intent.HIJRI_CALENDAR: "hijri_tool",
    Intent.PRAYER_TIMES: "prayer_tool",
    Intent.HADITH: "hadith_agent",
    Intent.SEERAH: "seerah_agent",
    # NOTE: tafsir, aqeedah, usul_fiqh, islamic_history, arabic_language agents
    # were deleted as orphan files. These intents will fall back to general_islamic_agent.
    Intent.TAFSIR: "general_islamic_agent",
    Intent.AQEEDAH: "general_islamic_agent",
    Intent.USUL_FIQH: "general_islamic_agent",
    Intent.ISLAMIC_HISTORY: "general_islamic_agent",
    Intent.ARABIC_LANGUAGE: "general_islamic_agent",
}
```

**شرح**:
- يربط كل نية بـ **الوكيل أو الأداة** المسؤولة

**ملاحظة مهمة**:
```python
# NOTE: tafsir, aqeedah, usul_fiqh, islamic_history, arabic_language agents
# were deleted as orphan files. These intents will fall back to general_islamic_agent.
```

**ما يعني**:
- الوكلاء المتخصصة (tafsir, aqeedah, ...) **محذوفة**
- هذه النيات تذهب إلى `general_islamic_agent`

**لماذا؟**:
- ربما كانت هذه الملفات مكررة أو غير مكتملة
- سيتم إعادة كتابتها لاحقاً

---

### الأسطر 101-170: KEYWORD_PATTERNS

```python
KEYWORD_PATTERNS = {
    Intent.FIQH: [
        "حكم",
        "fiqh",
        "halal",
        "haram",
        "Islamic law",
        "ما حكم",
        "هل يجوز",
        "هل هو حلال",
        "هل هو حرام",
    ],
    Intent.ISLAMIC_KNOWLEDGE: [
        "من هو",
        "ما هو",
        "ما هي",
        "who is",
        "what is",
        "explain",
        "شرح",
        "معلومات عن",
    ],
    # ... (بقية الأنماط)
}
```

**شرح**:
- قاموس يربط كل نية بـ **قائمة كلمات مفتاحية**
- إذا وجدت هذه الكلمات في السؤال، **يصنف مباشرة** بدون LLM

**كيف يعمل**:
```python
query = "ما حكم صلاة العيد؟"

for intent, patterns in KEYWORD_PATTERNS.items():
    for pattern in patterns:
        if pattern in query.lower():
            return intent  # Found!
```

**مثال**:
```
query: "ما حكم صلاة العيد؟"
    ↓
pattern: "ما حكم" → MATCH!
    ↓
intent: FIQH (confidence: 0.92)
```

---

## 5️⃣ الخلاصة العملية

### ما الذي يجب أن تفهمه فعلاً؟

1. **16 نية** تغطي كل أنواع الأسئلة الإسلامية
2. **INTENT_ROUTING** يربط كل نية بوكيل
3. **KEYWORD_PATTERNS** للتصنيف السريع (بدون LLM)
4. **QuranSubIntent** لتحديد pipeline القرآن

### 📝 تمرين صغير

1. ما الـ agent المسؤول عن نية `hadith`؟
2. ما الكلمات المفتاحية لـ `zakat`؟
3. لماذا بعض النيات تذهب إلى `general_islamic_agent`؟

### 🔜 الخطوة التالية

اقرأ الملف 3: `src/core/router.py`

---

*(يتبع شرح الملفات 3-10 بنفس التفصيل...)*

---

**📖 الدليل الكامل:** [`docs/mentoring/`](docs/mentoring/)

**🚀 ابدأ الآن:** اقرأ الملفات بالترتيب من 1 إلى 10

---

## 🏗️ التحديثات في الإصدار v2 - أهم الملفات

### نظرة عامة على المعمارية الجديدة
مع الإصدار v2، تم إضافة مسارات جديدة مهمة:

```
src/
├── config/
│   └── agents/              ← NEW! 10 ملفات YAML للوكلاء
│       ├── fiqh.yaml
│       ├── hadith.yaml
│       └── ... (10 وكلاء)
├── prompts/                 ← NEW! ملفات الـ Prompts منفصلة
│   ├── fiqh/
│   ├── hadith/
│   └── ... (10 وكلاء)
├── agents/
│   ├── collection/         ← NEW! CollectionAgent 10 وكلاء
│   ├── legacy/             ← DEPRECATED!
│   └── base.py             ← DEPRECATED!
├── retrieval/              ← NEW! طبقة الاسترجاع
│   ├── schemas.py
│   ├── filters/
│   ├── fusion/
│   └── mapping/
├── verification/           ← NEW! طبقة التحقق
├── application/            ← NEW! طبقة التطبيق
│   └── routing/
├── infrastructure/
│   └── qdrant/            ← NEW! عميل Qdrant
└── generation/             ← NEW! طبقة التوليد
```

### الملفات الجديدة في v2

| الملف | السطور | الوظيفة |
|-------|--------|---------|
| `src/agents/collection/base.py` | ~200 | CollectionAgent الأساسي |
| `src/application/routing/intent_router.py` | ~150 |router جديد |
| `src/retrieval/strategies.py` | ~150 | استراتيجيات الاسترجاع |
| `src/verification/` | ~100 | طبقة التحقق |

### السبب وراء التغييرات
1. **فصل الاهتمامات**: كل طبقة مسئولة عن شيء واحد
2. **النظام التصريحي**: التكوين في ملفات YAML
3. **الصيانة**: تغيير الـ prompts بدون كود
4. **الاختبار**: اختبار التكوينات منفصلاً

### للمزيد من التفاصيل
- راجع: [`V2_MIGRATION_NOTES.md`](../../8-development/refactoring/V2_MIGRATION_NOTES.md)
- راجع: [`02_folder_structure.md`](02_folder_structure.md) - المعمارية الجديدة
