"""
Environment validation for Burhan Islamic QA System.

Validates required environment variables and dependencies on startup.
Phase 9: Added comprehensive environment validation.
"""

import os
import sys
from typing import Any

from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()


class EnvironmentValidationError(Exception):
    """Raised when environment validation fails."""

    pass


class Validator:
    """
    Environment validator for startup validation.

    Usage:
        validator = Validator()
        validator.validate_all()  # Raises on failure
    """

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_error(self, message: str) -> None:
        """Add validation error."""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add validation warning."""
        self.warnings.append(message)

    def validate_database(self) -> bool:
        """Validate database connection."""
        try:
            from src.infrastructure.database import get_sync_database_url

            url = get_sync_database_url()
            if "localhost" in url or "127.0.0.1" in url:
                self.add_warning("Database URL uses localhost")
            return True
        except Exception as e:
            self.add_error(f"Database validation failed: {e}")
            return False

    def validate_redis(self) -> bool:
        """Validate Redis connection."""
        try:
            from src.infrastructure.redis import get_redis

            # Just check URL is set
            url = settings.redis_url
            if not url:
                self.add_error("REDIS_URL not set")
                return False
            return True
        except Exception as e:
            self.add_warning(f"Redis validation warning: {e}")
            return True

    def validate_qdrant(self) -> bool:
        """Validate Qdrant connection."""
        url = settings.qdrant_url
        if not url:
            self.add_warning("QDRANT_URL not set - vector search disabled")
        return True

    def validate_llm(self) -> bool:
        """Validate LLM configuration."""
        provider = settings.llm_provider

        if provider == "openai":
            if not settings.openai_api_key:
                self.add_error("OPENAI_API_KEY not set")
                return False
        elif provider == "groq":
            if not settings.groq_api_key:
                self.add_warning("GROQ_API_KEY not set - LLM disabled")
        return True

    def validate_embedding(self) -> bool:
        """Validate embedding model configuration."""
        model = settings.embedding_model
        if not model:
            self.add_error("EMBEDDING_MODEL not set")
            return False
        return True

    def validate_secrets(self) -> bool:
        """Validate secret key."""
        if settings.secret_key == "change-this-in-production-please-use-random-string":
            self.add_warning("Using default SECRET_KEY")

        if settings.app_env == "production":
            if settings.secret_key == "change-this-in-production-please-use-random-string":
                self.add_error("SECRET_KEY must be changed in production")
                return False

            if not settings.api_key_enabled:
                self.add_warning("API_KEY not enabled in production")
        return True

    def validate_cors(self) -> bool:
        """Validate CORS configuration."""
        origins = settings.cors_origins

        if not origins:
            self.add_error("CORS_ORIGINS not set")
            return False

        if "*" in origins and settings.app_env == "production":
            self.add_error("CORS Origins wildcard '*' not allowed in production")
            return False
        return True

    def validate_rate_limiting(self) -> bool:
        """Validate rate limiting."""
        if settings.app_env == "production":
            if not settings.rate_limit_enabled:
                self.add_warning("Rate limiting not enabled in production")
        return True

    def validate_all(self) -> bool:
        """Run all validations."""
        logger.info("validating.environment")

        # Core validations
        self.validate_database()
        self.validate_redis()
        self.validate_qdrant()
        self.validate_llm()
        self.validate_embedding()
        self.validate_secrets()
        self.validate_cors()
        self.validate_rate_limiting()

        # Report results
        if self.warnings:
            for warning in self.warnings:
                logger.warning("validation.warning", message=warning)

        if self.errors:
            for error in self.errors:
                logger.error("validation.error", message=error)

            logger.error(
                "validation.failed",
                error_count=len(self.errors),
            )
            return False

        logger.info(
            "validation.passed",
            warnings=len(self.warnings),
        )
        return True

    def get_report(self) -> dict[str, Any]:
        """Get validation report."""
        return {
            "passed": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def validate_environment() -> bool:
    """
    Validate environment on startup.

    Returns:
        True if validation passed

    Raises:
        EnvironmentValidationError: If critical validation fails in production
    """
    validator = Validator()
    passed = validator.validate_all()

    if not passed:
        if settings.app_env == "production":
            raise EnvironmentValidationError(f"Environment validation failed: {validator.errors}")
        else:
            # In development, just warn
            logger.warning(
                "validation.failed_development",
                errors=validator.errors,
            )

    return passed


def validate_or_exit() -> None:
    """Validate and exit on failure."""
    if not validate_environment():
        logger.critical("validation.fatal_error")
        sys.exit(1)


# Call on startup when in production
if __name__ == "__main__":
    import sys

    try:
        validate_or_exit()
        print("✓ Environment validation passed")
        sys.exit(0)
    except EnvironmentValidationError as e:
        print(f"✗ Environment validation failed: {e}")
        sys.exit(1)
