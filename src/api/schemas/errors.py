"""
Standardized error response schemas for Athar API.

All API errors follow a consistent format:
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": {} // optional
    }
}
"""

from typing import Optional, Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: Optional[str] = None
    message: str


class APIError(BaseModel):
    """Standardized API error response."""

    code: str = Field(description="Error code (e.g., VALIDATION_ERROR, NOT_FOUND)")
    message: str = Field(description="Human readable error message")
    details: Optional[dict[str, Any]] = Field(default=None, description="Additional error details")

    # Common error codes
    class Config:
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": {"field": "email", "issue": "Invalid format"},
            }
        }


class ErrorResponse(BaseModel):
    """Full error response wrapper."""

    error: APIError


# ==========================================
# Error Code Enumeration
# ==========================================


class ErrorCode(str):
    """Standard error codes for the API."""

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"

    # Not found errors
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"

    # Authentication/Authorization errors
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID = "AUTH_INVALID"
    FORBIDDEN = "FORBIDDEN"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Processing errors
    PROCESSING_ERROR = "PROCESSING_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

    # Tool-specific errors
    CALCULATION_ERROR = "CALCULATION_ERROR"
    VALIDATION_TOOL_ERROR = "VALIDATION_TOOL_ERROR"

    # Query errors
    QUERY_TOO_LONG = "QUERY_TOO_LONG"
    INTENT_NOT_RECOGNIZED = "INTENT_NOT_RECOGNIZED"

    # RAG errors
    RETRIEVAL_ERROR = "RETRIEVAL_ERROR"
    GENERATION_ERROR = "GENERATION_ERROR"


# ==========================================
# Helper Functions
# ==========================================


def create_error_response(code: str, message: str, details: Optional[dict[str, Any]] = None) -> dict:
    """Create a standardized error response dictionary."""
    return {"error": {"code": code, "message": message, "details": details}}


def validation_error(message: str, field: Optional[str] = None) -> dict:
    """Create a validation error response."""
    details = {"field": field} if field else None
    return create_error_response(code=ErrorCode.VALIDATION_ERROR, message=message, details=details)


def not_found_error(resource: str, identifier: Any) -> dict:
    """Create a not found error response."""
    return create_error_response(code=ErrorCode.NOT_FOUND, message=f"{resource} not found: {identifier}")


def auth_error(message: str = "Authentication required") -> dict:
    """Create an authentication error response."""
    return create_error_response(code=ErrorCode.AUTH_REQUIRED, message=message)


def rate_limit_error(retry_after: int = 60) -> dict:
    """Create a rate limit error response."""
    return create_error_response(
        code=ErrorCode.RATE_LIMIT_EXCEEDED,
        message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
        details={"retry_after": retry_after},
    )


def internal_error(message: str = "An internal error occurred") -> dict:
    """Create an internal error response."""
    return create_error_response(code=ErrorCode.INTERNAL_ERROR, message=message)
