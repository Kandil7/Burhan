"""
Request/Response Logging Middleware for Athar Islamic QA System.

Logs all HTTP requests and responses with structured logging.
Phase 10: Added request/response logging middleware.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.logging_config import get_logger

logger = get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.

    Logs:
    - Request method, path, query params
    - Request headers (sanitized)
    - Response status code
    - Response time

    Phase 10: Added request/response logging.
    """

    EXCLUDE_PATHS = {"/health", "/metrics", "/ready"}
    SENSITIVE_HEADERS = {"authorization", "x-api-key", "cookie"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if request.url.path in self.EXCLUDE_PATHS:
            return await call_next(request)

        # Start timing
        start_time = time.perf_counter()

        # Log request
        request_id = request.headers.get("x-request-id", "-")
        logger.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params)[:100],
            client_ip=self._get_client_ip(request),
            request_id=request_id,
            user_agent=request.headers.get("user-agent", "-")[:100],
        )

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.error(
                "http.request.error",
                method=request.method,
                path=request.url.path,
                error=str(e)[:200],
            )
            raise

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log response
        logger.info(
            "http.response",
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            request_id=request_id,
        )

        # Add timing header
        response.headers["X-Process-Time-Ms"] = str(round(duration_ms, 2))
        response.headers["X-Request-ID"] = request_id

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client
        if request.client:
            return request.client.host

        return "-"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to each request.

    Phase 10: Added request ID tracking.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID if not provided
        request_id = request.headers.get("x-request-id")
        if not request_id:
            import uuid

            request_id = str(uuid.uuid4())[:8]

        # Add to request state for access in handlers
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response
