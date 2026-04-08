"""
Error handling middleware for Athar Islamic QA system.

Catches all exceptions and returns structured error responses.
"""
import uuid
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from src.config.logging_config import get_logger

logger = get_logger()


def _safe_error_str(e: Exception) -> str:
    """
    Get a safe string representation of an exception.
    
    Handles ExceptionGroup and other complex exceptions that
    produce multi-line output with special characters.
    """
    # For ExceptionGroup, just get the exception type and first sub-exception
    if hasattr(e, 'exceptions') and callable(e.exceptions):
        sub_exceptions = e.exceptions()
        if sub_exceptions:
            first = sub_exceptions[0]
            return f"{type(e).__name__}: {type(first).__name__}: {str(first)[:500]}"
    
    # Get traceback summary instead of full str() for complex exceptions
    try:
        tb = traceback.format_exception_only(type(e), e)
        if tb:
            # Return just the exception line, limited to 500 chars
            return tb[-1].strip()[:500]
    except Exception as e:
        logger.warning("error_handler.safe_str_failed", error=str(e))
        pass
    
    # Fallback to type name only
    return f"{type(e).__name__}"


async def error_handler_middleware(request: Request, call_next):
    """
    Global error handling middleware.

    Catches all exceptions and returns structured JSON error responses
    with request ID for tracking.
    """
    request_id = str(uuid.uuid4())

    try:
        response = await call_next(request)
        return response

    except Exception as e:
        error_str = _safe_error_str(e)
        logger.error(
            "api.unhandled_error",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            error=error_str
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(e) if request.app.debug else "An unexpected error occurred",
                "request_id": request_id
            }
        )
