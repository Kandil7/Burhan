"""
API Versioning for Burhan Islamic QA System.

Supports URL-based API versioning (e.g., /api/v1/, /api/v2/)
Phase 10: Added API versioning support.
"""

from enum import Enum
from typing import Callable

from fastapi import APIRouter, FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware


class APIVersion(str, Enum):
    """API Version enumeration."""

    V1 = "v1"
    V2 = "v2"
    CURRENT = "v1"


class APIRouterManager:
    """
    Manages API routers with versioning support.

    Usage:
        manager = APIRouterManager()
        manager.include_v1_router(query_router)
        manager.include_v2_router(query_router_v2)
    """

    def __init__(self, app: FastAPI):
        self.app = app
        self.v1_router = APIRouter(prefix="/v1")
        self.v2_router = APIRouter(prefix="/v2")

        # Track registered routes
        self._v1_routes = set()
        self._v2_routes = set()

    def include_v1_router(self, router: APIRouter, tags: list[str] | None = None):
        """Include router in v1."""
        self.v1_router.include_router(router, tags=tags)
        for route in router.routes:
            if hasattr(route, "path"):
                self._v1_routes.add(route.path)

    def include_v2_router(self, router: APIRouter, tags: list[str] | None = None):
        """Include router in v2."""
        self.v2_router.include_router(router, tags=tags)
        for route in router.routes:
            if hasattr(route, "path"):
                self._v2_routes.add(route.path)

    def register(self):
        """Register all routers to the app."""
        self.app.include_router(self.v1_router, prefix="/api")
        self.app.include_router(self.v2_router, prefix="/api")

    def get_registered_routes(self, version: str) -> set:
        """Get registered routes for a version."""
        if version == "v1":
            return self._v1_routes
        elif version == "v2":
            return self._v2_routes
        return set()


class VersionedAPIRouter:
    """
    Router that supports multiple API versions.

    Phase 10: Added versioned routing.

    Usage:
        router = VersionedAPIRouter()

        @router.v1.get("/items")
        async def get_items_v1():
            return {"version": "v1", "items": []}

        @router.v2.get("/items")
        async def get_items_v2():
            return {"version": "v2", "items": [], "metadata": {}}
    """

    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.v1 = APIRouter(prefix=f"{prefix}/v1")
        self.v2 = APIRouter(prefix=f"{prefix}/v2")

    def include_v1_router(self, router: APIRouter, tags: list[str] | None = None):
        """Include a router in v1."""
        self.v1.include_router(router, tags=tags)

    def include_v2_router(self, router: APIRouter, tags: list[str] | None = None):
        """Include a router in v2."""
        self.v2.include_router(router, tags=tags)


# Version compatibility checker
class VersionCompatibility:
    """Check API version compatibility."""

    # Version compatibility matrix
    COMPATIBILITY = {
        ("v1", "v1"): True,
        ("v1", "v2"): False,  # v1 clients can't use v2
        ("v2", "v1"): True,  # v2 clients can use v1
        ("v2", "v2"): True,
    }

    @classmethod
    def is_compatible(cls, client_version: str, endpoint_version: str) -> bool:
        """Check if client version is compatible with endpoint version."""
        return cls.COMPATIBILITY.get((client_version, endpoint_version), False)

    @classmethod
    def get_supported_versions(cls) -> list[str]:
        """Get list of supported API versions."""
        return ["v1", "v2"]

    @classmethod
    def get_latest_version(cls) -> str:
        """Get the latest API version."""
        return "v2"


# API Version dependency
async def get_api_version(request: Request) -> str:
    """
    Dependency to get API version from URL path.

    Usage:
        @app.get("/items")
        async def get_items(version: str = Depends(get_api_version)):
            ...
    """
    path = request.url.path

    if "/v2/" in path:
        return "v2"
    elif "/v1/" in path:
        return "v1"

    # Default to v1 for backward compatibility
    return "v1"
