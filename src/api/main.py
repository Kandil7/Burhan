"""
FastAPI application factory for Athar Islamic QA system.

Creates and configures the FastAPI application with:
- Security middleware (rate limiting, API key, security headers)
- CORS middleware
- Error handling
- Request logging
- Route registration
- OpenAPI documentation

Phase 5: Security improvements and performance optimizations.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.error_handler import error_handler_middleware
from src.api.middleware.security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from src.api.routes.health import router as health_router
from src.api.routes.query import router as query_router
from src.api.routes.quran import router as quran_router
from src.api.routes.rag import router as rag_router
from src.api.routes.tools import router as tools_router
from src.config.logging_config import get_logger, setup_logging
from src.config.settings import settings

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Runs on startup and shutdown.
    Phase 5: Includes security and performance optimizations.
    """
    # Startup
    setup_logging()
    logger.info(
        "app.startup",
        app_name=settings.app_name,
        version="0.5.0",
        environment=settings.app_env,
    )

    yield

    # Shutdown
    logger.info("app.shutdown")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        description="""
# Athar Islamic QA System API

Multi-agent Islamic QA system based on Fanar-Sadiq architecture.

## Features
- **Intent Classification**: Automatically detects query type (fiqh, quran, zakat, etc.)
- **Grounded Answers**: All answers backed by verified sources with citations
- **Deterministic Calculators**: Zakat and inheritance calculations
- **Multi-language**: Arabic and English support
- **Madhhab-aware**: Handles differences between Islamic schools
- **Rate Limiting**: Protected against abuse
- **API Key Authentication**: Secure access

## Security
- API Key required for query endpoints
- Rate limiting: 60 requests/minute default
- Security headers on all responses

        """,
        version="0.5.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # ==========================================
    # Middleware (order matters - last added runs first)
    # ==========================================

    # Security headers (outermost - runs last)
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting
    if settings.app_env == "production":
        app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handling
    app.middleware("http")(error_handler_middleware)

    # ==========================================
    # Routes
    # ==========================================
    app.include_router(health_router)
    app.include_router(query_router, prefix=settings.api_v1_prefix)
    app.include_router(tools_router, prefix=settings.api_v1_prefix)
    app.include_router(rag_router, prefix=f"{settings.api_v1_prefix}")
    app.include_router(quran_router, prefix=f"{settings.api_v1_prefix}")

    # ==========================================
    # Root endpoint
    # ==========================================
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": "0.5.0",
            "phase": "5 - Security & Performance",
            "docs": "/docs",
            "health": "/health",
            "authentication": "API Key required (X-API-Key header)",
            "query_endpoint": f"{settings.api_v1_prefix}/query",
            "quran_endpoints": {
                "surahs": f"{settings.api_v1_prefix}/quran/surahs",
                "ayah": f"{settings.api_v1_prefix}/quran/ayah/{{surah}}:{{ayah}}",
                "search": f"{settings.api_v1_prefix}/quran/search",
                "validate": f"{settings.api_v1_prefix}/quran/validate",
                "analytics": f"{settings.api_v1_prefix}/quran/analytics",
                "tafsir": f"{settings.api_v1_prefix}/quran/tafsir/{{surah}}:{{ayah}}",
            },
            "tool_endpoints": {
                "zakat": f"{settings.api_v1_prefix}/tools/zakat",
                "inheritance": f"{settings.api_v1_prefix}/tools/inheritance",
                "prayer_times": f"{settings.api_v1_prefix}/tools/prayer-times",
                "hijri": f"{settings.api_v1_prefix}/tools/hijri",
                "duas": f"{settings.api_v1_prefix}/tools/duas",
            },
        }

    return app


# Create app instance
app = create_app()
