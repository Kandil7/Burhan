"""
Structured exception hierarchy for Athar Islamic QA System.

Provides meaningful error codes and structured error details for better
error handling, logging, and API responses.

Phase 9: Added structured exception hierarchy.
"""

from enum import Enum
from typing import Any


class AtharErrorCode(str, Enum):
    """Error codes with business meaning."""

    RETRIEVAL_FAILED = "retrieval_failed"
    CLASSIFICATION_FAILED = "classification_failed"
    AGENT_TIMEOUT = "agent_timeout"
    AGENT_EXECUTION_FAILED = "agent_execution_failed"
    VECTOR_STORE_UNAVAILABLE = "vector_store_unavailable"
    LLM_GENERATION_FAILED = "llm_generation_failed"
    INVALID_QUERY = "invalid_query"
    AUTHENTICATION_FAILED = "authentication_failed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DATABASE_ERROR = "database_error"
    EMBEDDING_FAILED = "embedding_failed"
    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"
    NOT_FOUND = "not_found"
    QUOTA_EXCEEDED = "quota_exceeded"


class AtharException(Exception):
    """Base exception with structured error code."""

    def __init__(
        self,
        message: str,
        code: AtharErrorCode,
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": self.code.value,
            "message": self.message,
            "details": self.details,
        }


class RetrievalException(AtharException):
    """Raised when document retrieval fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message,
            AtharErrorCode.RETRIEVAL_FAILED,
            details,
            status_code=503,
        )


class ClassificationException(AtharException):
    """Raised when intent classification fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message,
            AtharErrorCode.CLASSIFICATION_FAILED,
            details,
            status_code=422,
        )


class AgentTimeoutException(AtharException):
    """Raised when agent execution times out."""

    def __init__(self, agent_name: str, timeout_seconds: float):
        super().__init__(
            f"Agent '{agent_name}' timed out after {timeout_seconds}s",
            AtharErrorCode.AGENT_TIMEOUT,
            {"agent": agent_name, "timeout_seconds": timeout_seconds},
            status_code=504,
        )


class AgentExecutionException(AtharException):
    """Raised when agent execution fails."""

    def __init__(
        self,
        agent_name: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        details["agent"] = agent_name
        super().__init__(
            f"Agent '{agent_name}' execution failed: {message}",
            AtharErrorCode.AGENT_EXECUTION_FAILED,
            details,
            status_code=500,
        )


class VectorStoreException(AtharException):
    """Raised when vector store operations fail."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message,
            AtharErrorCode.VECTOR_STORE_UNAVAILABLE,
            details,
            status_code=503,
        )


class LLMGenerationException(AtharException):
    """Raised when LLM generation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message,
            AtharErrorCode.LLM_GENERATION_FAILED,
            details,
            status_code=502,
        )


class EmbeddingException(AtharException):
    """Raised when embedding generation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message,
            AtharErrorCode.EMBEDDING_FAILED,
            details,
            status_code=502,
        )


class InvalidQueryException(AtharException):
    """Raised when query validation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message,
            AtharErrorCode.INVALID_QUERY,
            details,
            status_code=400,
        )


class AuthenticationException(AtharException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message,
            AtharErrorCode.AUTHENTICATION_FAILED,
            details,
            status_code=401,
        )


class RateLimitException(AtharException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        limit: int,
        window_seconds: int = 60,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        details.update(
            {
                "limit": limit,
                "window_seconds": window_seconds,
            }
        )
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window_seconds}s",
            AtharErrorCode.RATE_LIMIT_EXCEEDED,
            details,
            status_code=429,
        )


class DatabaseException(AtharException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message,
            AtharErrorCode.DATABASE_ERROR,
            details,
            status_code=500,
        )


class NotFoundException(AtharException):
    """Raised when a resource is not found."""

    def __init__(
        self,
        resource: str,
        identifier: str | int,
        details: dict[str, Any] | None = None,
    ):
        details = details or {}
        details["resource"] = resource
        details["identifier"] = identifier
        super().__init__(
            f"{resource} not found: {identifier}",
            AtharErrorCode.NOT_FOUND,
            details,
            status_code=404,
        )


class ConfigurationException(AtharException):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message,
            AtharErrorCode.CONFIGURATION_ERROR,
            details,
            status_code=500,
        )
