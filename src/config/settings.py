"""
Application settings with environment variable support.

Uses Pydantic BaseSettings for automatic environment variable parsing.

Phase 5: Added security, rate limiting, and caching settings.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    # ==========================================
    # Application
    # ==========================================
    app_name: str = "Athar"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = "change-this-in-production-please-use-random-string"
    api_v1_prefix: str = "/api/v1"

    # ==========================================
    # Database (PostgreSQL 16)
    # ==========================================
    database_url: str = "postgresql+asyncpg://athar:athar_password@localhost:5432/athar_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ==========================================
    # Redis
    # ==========================================
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # ==========================================
    # Qdrant (Vector Database)
    # ==========================================
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection_fiqh: str = "fiqh_passages"
    qdrant_collection_hadith: str = "hadith_passages"
    qdrant_collection_dua: str = "dua_passages"
    qdrant_collection_general: str = "general_islamic"

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

    # ==========================================
    # Embeddings
    # ==========================================
    embedding_model: str = "Qwen/Qwen3-Embedding-0.6B"
    embedding_dimension: int = 1024

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

    # ==========================================
    # CORS
    # ==========================================
    cors_origins: list[str] = ["http://localhost:3000"]

    # ==========================================
    # Logging
    # ==========================================
    log_level: str = "INFO"
    log_format: str = "json"

    # ==========================================
    # API Configuration
    # ==========================================
    api_timeout: int = 30
    max_query_length: int = 1000

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        """Ensure secret key is changed from default."""
        if v == "change-this-in-production-please-use-random-string":
            import warnings

            warnings.warn("Using default secret key! Change this in production.", UserWarning)
        return v

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
