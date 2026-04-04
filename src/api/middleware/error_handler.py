"""
Error handling middleware for Athar Islamic QA system.

Catches all exceptions and returns structured error responses.
"""
import uuid
from fastapi import Request, status
from fastapi.responses import JSONResponse
from src.config.logging_config import get_logger

logger = get_logger()


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
        logger.error(
            "api.unhandled_error",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            error=str(e)
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(e) if request.app.debug else "An unexpected error occurred",
                "request_id": request_id
            }
        )
