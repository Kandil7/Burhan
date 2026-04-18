"""
Request ID Middleware for Athar Islamic QA system.

Adds unique request ID to each request for tracing.
"""

from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to each request.

    The request ID is:
    - Added to request.state for access in route handlers
    - Added to response headers for client tracking
    - Added to logging context

    Usage:
        app.add_middleware(RequestIDMiddleware)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:16]}"

        # Store in request state
        request.state.request_id = request_id

        # Add to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


def get_request_id(request: Request) -> str:
    """
    Get request ID from request state.

    Args:
        request: FastAPI request

    Returns:
        Request ID string
    """
    return getattr(request.state, "request_id", "unknown")


__all__ = ["RequestIDMiddleware", "get_request_id"]
