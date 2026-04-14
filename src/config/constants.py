"""
Centralized constants for Athar Islamic QA System.

All magic numbers, thresholds, and configuration values should be defined here.
This ensures consistency across the entire application.
"""

from typing import Final

# ==========================================
# Retrieval Configuration
# ==========================================


class RetrievalConfig:
    """Configuration for RAG retrieval pipelines."""

    # Top-K for different collections
    TOP_K_FIQH: Final[int] = 15
    TOP_K_GENERAL: Final[int] = 10
    TOP_K_DUA: Final[int] = 5
    TOP_K_HADITH: Final[int] = 10

    # Multiplier for initial retrieval (before reranking/fusion)
    TOP_K_MULTIPLIER: Final[int] = 2

    # Score thresholds (adjusted for BGE-M3 + hybrid search compatibility)
    SEMANTIC_SCORE_THRESHOLD: Final[float] = 0.15  # Lowered from 0.4 → 0.35 → 0.15 for better recall
    HYBRID_SCORE_THRESHOLD: Final[float] = 0.50   # Lowered from 0.65 for hybrid search

    # Reciprocal rank fusion parameter
    RRF_K: Final[int] = 60


# ==========================================
# Classification Configuration
# ==========================================


class ClassificationConfig:
    """Configuration for intent classification."""

    # Confidence thresholds
    KEYWORD_CONFIDENCE: Final[float] = 0.92  # High confidence for keyword match
    LLM_CONFIDENCE_THRESHOLD: Final[float] = 0.75
    EMBEDDING_CONFIDENCE: Final[float] = 0.6

    # Embedding fallback
    EMBEDDING_FALLBACK_ENABLED: Final[bool] = True
    EMBEDDING_FALLBACK_INTENT: Final[str] = "islamic_knowledge"


# ==========================================
# LLM Configuration
# ==========================================


class LLMConfig:
    """Configuration for LLM generation."""

    # Default models (can be overridden in settings)
    DEFAULT_MODEL: Final[str] = "gpt-4o-mini"
    FAST_MODEL: Final[str] = "gpt-4o-mini"
    SMART_MODEL: Final[str] = "gpt-4o"

    # Groq models
    GROQ_DEFAULT: Final[str] = "qwen/qwen3-32b"
    GROQ_FAST: Final[str] = "meta-llama/llama-3.3-70b-versatile"

    # Generation parameters
    DEFAULT_TEMPERATURE: Final[float] = 0.1
    FIQH_TEMPERATURE: Final[float] = 0.1  # Deterministic for fiqh
    GENERAL_TEMPERATURE: Final[float] = 0.3  # More conversational
    CHATBOT_TEMPERATURE: Final[float] = 0.5  # Friendly

    # Token limits
    DEFAULT_MAX_TOKENS: Final[int] = 2048
    SHORT_MAX_TOKENS: Final[int] = 1024
    LONG_MAX_TOKENS: Final[int] = 4096

    # Cache settings
    CACHE_ENABLED: Final[bool] = True
    CACHE_TTL_SECONDS: Final[int] = 3600  # 1 hour


# ==========================================
# Embedding Configuration
# ==========================================


class EmbeddingConfig:
    """Configuration for embedding models."""

    # Default model
    DEFAULT_MODEL: Final[str] = "BAAI/bge-m3"
    FALLBACK_MODEL: Final[str] = "sentence-transformers/all-MiniLM-L6-v2"

    # Dimensions
    QWEN_DIMENSION: Final[int] = 1024
    MINI_LM_DIMENSION: Final[int] = 384

    # Batch processing
    DEFAULT_BATCH_SIZE: Final[int] = 32
    MAX_BATCH_SIZE: Final[int] = 128

    # Cache
    CACHE_ENABLED: Final[bool] = True


# ==========================================
# Vector Store Configuration
# ==========================================


class VectorStoreConfig:
    """Configuration for Qdrant vector store."""

    # Collection names
    COLLECTION_FIQH: Final[str] = "fiqh_passages"
    COLLECTION_HADITH: Final[str] = "hadith_passages"
    COLLECTION_TAFSIR: Final[str] = "quran_tafsir"
    COLLECTION_GENERAL: Final[str] = "general_islamic"
    COLLECTION_DUA: Final[str] = "duas_adhkar"

    # Collection dimensions (all using 1024 for Qwen)
    COLLECTION_DIMENSIONS: Final[dict[str, int]] = {
        "fiqh_passages": 1024,
        "hadith_passages": 1024,
        "quran_tafsir": 1024,
        "general_islamic": 1024,
        "duas_adhkar": 1024,
    }

    # Search parameters
    DEFAULT_TOP_K: Final[int] = 10
    MAX_TOP_K: Final[int] = 100

    # Timeout
    CLIENT_TIMEOUT: Final[int] = 60


# ==========================================
# Zakat Calculator Configuration
# ==========================================


class ZakatConfig:
    """Configuration for Zakat calculations."""

    # Nisab thresholds (in grams)
    GOLD_NISAB_GRAMS: Final[float] = 85.0
    SILVER_NISAB_GRAMS: Final[float] = 595.0

    # Rates
    WEALTH_ZAKAT_RATE: Final[float] = 0.025  # 2.5%
    MINERALS_ZAKAT_RATE: Final[float] = 0.025  # 2.5%
    CROP_ZAKAT_RATE_IRRIGATED: Final[float] = 0.05  # 5%
    CROP_ZAKAT_RATE_NATURAL: Final[float] = 0.10  # 10%

    # Validation
    MAX_DEBTS_RATIO: Final[float] = 1.0  # Can't deduct more than assets
    MIN_METAL_PRICE: Final[float] = 0.01  # Minimum metal price


# ==========================================
# Inheritance Calculator Configuration
# ==========================================


class InheritanceConfig:
    """Configuration for Inheritance calculations."""

    # Fixed shares from Quran (as fractions)
    HUSBAND_WITH_DESCENDANTS: Final[float] = 1 / 4
    HUSBAND_WITHOUT_DESCENDANTS: Final[float] = 1 / 2
    WIFE_WITH_DESCENDANTS: Final[float] = 1 / 8
    WIFE_WITHOUT_DESCENDANTS: Final[float] = 1 / 4
    FATHER_WITH_MALE_DESCENDANTS: Final[float] = 1 / 6
    MOTHER_WITH_SIBLINGS: Final[float] = 1 / 6
    MOTHER_WITHOUT_SIBLINGS: Final[float] = 1 / 3
    DAUGHTER_SINGLE: Final[float] = 1 / 2
    DAUGHTER_MULTIPLE: Final[float] = 2 / 3
    FULL_SISTER_SINGLE: Final[float] = 1 / 2
    FULL_SISTER_MULTIPLE: Final[float] = 2 / 3
    UTERINE_SINGLE: Final[float] = 1 / 6
    UTERINE_MULTIPLE: Final[float] = 1 / 3

    # Validation
    MAX_WASIYYAH_RATIO: Final[float] = 1 / 3  # Max bequest is 1/3 of estate
    MIN_ESTATE_VALUE: Final[float] = 0.01


# ==========================================
# API Configuration
# ==========================================


class APIConfig:
    """Configuration for API endpoints."""

    # Rate limiting
    RATE_LIMIT_ENABLED: Final[bool] = True
    RATE_LIMIT_DEFAULT: Final[str] = "10/minute"
    RATE_LIMIT_QUERY: Final[str] = "10/minute"
    RATE_LIMIT_TOOLS: Final[str] = "30/minute"
    RATE_LIMIT_QURAN: Final[str] = "60/minute"

    # Pagination
    DEFAULT_PAGE_SIZE: Final[int] = 10
    MAX_PAGE_SIZE: Final[int] = 100

    # Timeouts
    REQUEST_TIMEOUT_SECONDS: Final[int] = 30
    LONG_REQUEST_TIMEOUT_SECONDS: Final[int] = 120

    # Response limits
    MAX_CITATIONS: Final[int] = 10
    MAX_ANSWER_LENGTH: Final[int] = 10000


# ==========================================
# Security Configuration
# ==========================================


class SecurityConfig:
    """Configuration for security settings."""

    # API Key
    API_KEY_HEADER: Final[str] = "X-API-Key"
    API_KEY_MIN_LENGTH: Final[int] = 32

    # CORS
    CORS_MAX_AGE: Final[int] = 600  # 10 minutes

    # Input validation
    MAX_QUERY_LENGTH: Final[int] = 1000
    MAX_LOCATION_LENGTH: Final[int] = 200

    # SQL limits
    SQL_MAX_IN_CLAUSE: Final[int] = 100


# ==========================================
# Logging Configuration
# ==========================================


class LoggingConfig:
    """Configuration for logging."""

    # Log levels
    DEFAULT_LEVEL: Final[str] = "INFO"
    API_LEVEL: Final[str] = "INFO"
    LLM_LEVEL: Final[str] = "WARNING"
    DB_LEVEL: Final[str] = "WARNING"

    # Structured logging
    STRUCTURED_LOGGING: Final[bool] = True

    # Sensitive fields to redact
    SENSITIVE_FIELDS: Final[list[str]] = [
        "api_key",
        "password",
        "token",
        "secret",
    ]


# ==========================================
# Response Messages
# ==========================================


class ResponseMessages:
    """Standardized response messages."""

    # Errors
    ERROR_GENERIC: Final[str] = "حدث خطأ في معالجة الطلب. يرجى المحاولة لاحقاً."
    ERROR_NOT_FOUND: Final[str] = "المورد المطلوب غير موجود."
    ERROR_VALIDATION: Final[str] = "بيانات الإدخال غير صالحة."
    ERROR_RATE_LIMIT: Final[str] = "تم تجاوز الحد المسموح به. يرجى المحاولة لاحقاً."
    ERROR_AUTH_REQUIRED: Final[str] = "مطلوب مصادقة للوصول إلى هذا المورد."
    ERROR_AUTH_INVALID: Final[str] = "مفتاح API غير صالح."

    # Fallback messages
    FALLBACK_ZAKAT: Final[str] = (
        "أعتذر، النظام حالياً في وضع الصيانة. للمعلومات الأساسية:\n\n• الزكاة: wajib على المال عند بلوغ النصاب\n• نسبة الزكاة: 2.5%"
    )
    FALLBACK_PRAYER: Final[str] = (
        "أعتذر، النظام حالياً في وضع الصيانة. للمعلومات الأساسية:\n\n• الصلاة: ركن من أركان الإسلام"
    )
    FALLBACK_GENERAL: Final[str] = (
        "أعتذر، النظام حالياً في وضع الصيانة. يمكنني مساعدتك في:\n\n• الأسئلة العامة عن الإسلام\n• الآيات القرآنية"
    )

    # Success
    SUCCESS_CALCULATION: Final[str] = "تم الحساب بنجاح."
    SUCCESS_VALIDATION: Final[str] = "تم التحقق بنجاح."
    SUCCESS_RETRIEVAL: Final[str] = "تم الاسترجاع بنجاح."


# ==========================================
# Disclaimers
# ==========================================


class Disclaimers:
    """Standardized disclaimer messages."""

    FIQH_DISCLAIMER: Final[str] = (
        "⚠️ **تنبيه مهم**: هذه الإجابة مبنية على النصوص المسترجاعة من المصادر المتاحة. "
        "يجب استفاء عالم متخصص للتأكد من الحكم في حالتك الخاصة."
    )

    GENERAL_DISCLAIMER: Final[str] = "⚠️ **تنبيه**: هذه المعلومات تعليمية فقط. يرجى مراجعة أهل العلم للاستشارة."

    CALCULATOR_DISCLAIMER: Final[str] = (
        "⚠️ **تنبيه**: هذا الحساب رياضي بناءً على القواعد الفقهية. للحالات المعقدة، يرجى استشارة عالم متخصص."
    )
