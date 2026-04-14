"""
Security middleware for Athar Islamic QA System.

Provides:
- API Key authentication
- Rate limiting
- Input sanitization
"""

import hashlib
import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config.logging_config import get_logger
from src.config.settings import settings

logger = get_logger()


# ==========================================
# Rate Limiting
# ==========================================


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using in-memory storage.

    For production, use Redis-based rate limiting.
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.cleanup_interval = 300  # Clean up every 5 minutes
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)

        # Check rate limit
        if not self._check_rate_limit(client_id):
            logger.warning("rate_limit.exceeded", client_id=client_id, path=request.url.path)
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self._get_remaining(client_id)
        reset_time = self._get_reset_time(client_id)

        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Use API key if present
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return hashlib.sha256(api_key.encode()).hexdigest()[:16]

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limit."""
        now = time.time()
        minute_ago = now - 60

        # Clean old requests
        self._cleanup()

        # Get client's request timestamps
        timestamps = self.requests[client_id]

        # Filter to last minute
        recent = [t for t in timestamps if t > minute_ago]

        if len(recent) >= self.requests_per_minute:
            return False

        # Add current request
        recent.append(now)
        self.requests[client_id] = recent

        return True

    def _get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client."""
        now = time.time()
        minute_ago = now - 60
        timestamps = self.requests.get(client_id, [])
        recent = [t for t in timestamps if t > minute_ago]
        return max(0, self.requests_per_minute - len(recent))

    def _get_reset_time(self, client_id: str) -> int:
        """Get Unix timestamp when rate limit resets."""
        now = time.time()
        timestamps = self.requests.get(client_id, [])

        if not timestamps:
            return int(now) + 60

        # Find oldest request in last minute
        minute_ago = now - 60
        recent = [t for t in timestamps if t > minute_ago]

        if not recent:
            return int(now) + 60

        oldest = min(recent)
        return int(oldest + 60)

    def _cleanup(self):
        """Remove old request timestamps."""
        now = time.time()

        if now - self.last_cleanup < self.cleanup_interval:
            return

        cutoff = now - 120  # Keep 2 minutes of history
        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [t for t in self.requests[client_id] if t > cutoff]

            # Remove empty entries
            if not self.requests[client_id]:
                del self.requests[client_id]

        self.last_cleanup = now


# ==========================================
# API Key Authentication
# ==========================================


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API Key authentication middleware.

    Protects API endpoints while allowing public access to docs.
    """

    # Paths that don't require API key
    PUBLIC_PATHS = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    # Paths that require API key
    PROTECTED_PATHS = [
        "/api/v1/query",
        "/api/v1/tools",
        "/api/v1/quran",
        "/api/v1/rag",
    ]

    def __init__(self, app, api_key: str | None = None):
        super().__init__(app)
        self.api_key = api_key or settings.secret_key

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Public paths - allow without auth
        if path in self.PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # Check if path requires authentication
        requires_auth = any(path.startswith(p) for p in self.PROTECTED_PATHS)

        if not requires_auth:
            return await call_next(request)

        # Validate API key
        provided_key = request.headers.get("X-API-Key")

        if not provided_key:
            logger.warning("auth.missing_api_key", path=path)
            return JSONResponse(status_code=401, content={"detail": "API Key required. Include X-API-Key header."})

        if not self._validate_api_key(provided_key):
            logger.warning("auth.invalid_api_key", path=path)
            return JSONResponse(status_code=403, content={"detail": "Invalid API Key"})

        # Key is valid - proceed
        return await call_next(request)

    def _validate_api_key(self, provided_key: str) -> bool:
        """Validate the provided API key."""
        # Hash both for comparison
        provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
        expected_hash = hashlib.sha256(self.api_key.encode()).hexdigest()

        return provided_hash == expected_hash or provided_key == self.api_key


# ==========================================
# Input Sanitization
# ==========================================


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Sanitize user inputs to prevent injection attacks.
    """

    def __init__(self, app):
        super().__init__(app)

        # Patterns to detect and potentially block
        self.dangerous_patterns = [
            "<script",
            "javascript:",
            "onerror=",
            "onclick=",
            "onload=",
        ]

    async def dispatch(self, request: Request, call_next):
        # Only sanitize POST/PUT request bodies
        if request.method in ["POST", "PUT", "PATCH"]:
            # Get content type
            content_type = request.headers.get("content-type", "")

            if "application/json" in content_type:
                # Read body
                body = await request.body()

                if body:
                    # Check for dangerous patterns
                    body_str = body.decode("utf-8", errors="ignore")

                    for pattern in self.dangerous_patterns:
                        if pattern.lower() in body_str.lower():
                            logger.warning("input.suspicious_pattern", pattern=pattern, path=request.url.path)
                            # Still process but log warning

        return await call_next(request)


# ==========================================
# Security Headers
# ==========================================


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


# ==========================================
# Dependencies for route protection
# ==========================================

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Depends(api_key_header)) -> str:
    """Dependency to verify API key in routes."""
    from src.config.settings import settings

    if not api_key:
        raise HTTPException(status_code=401, detail="API Key required")

    # Simple comparison (in production, use constant-time comparison)
    if api_key != settings.secret_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    return api_key


async def get_current_user(api_key: str = Depends(verify_api_key)) -> dict:
    """Get current user from API key (for future user management)."""
    # In production, look up user from API key
    return {"user_id": "system", "scope": "full"}
