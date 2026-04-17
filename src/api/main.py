from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.error_handler import error_handler_middleware
from src.api.middleware.security import RateLimitMiddleware, SecurityHeadersMiddleware
from src.api.middleware.request_logging import RequestLoggingMiddleware, RequestIDMiddleware
from src.api.routes.health import router as health_router
from src.api.routes.query import query_router
from src.api.routes.classification import router as classification_router
from src.api.routes.quran import router as quran_router
from src.api.routes.rag import router as rag_router
from src.api.routes.tools import router as tools_router
from src.api.lifespan import lifespan
from src.config.logging_config import get_logger, setup_logging
from src.config.settings import settings


def create_app() -> FastAPI:
    # ── Logging: هنا فقط، مرة واحدة ─────────────────────────────────────
    setup_logging()
    logger = get_logger()

    app = FastAPI(
        title=settings.app_name,
        description=_API_DESCRIPTION,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # ── Middleware (LIFO: آخر مُضاف = أول يُنفَّذ) ───────────────────────
    # Request ID middleware (first to track requests)
    app.add_middleware(RequestIDMiddleware)

    # Request/response logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    app.add_middleware(SecurityHeadersMiddleware)

    if settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=settings.rate_limit_rpm,
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    app.middleware("http")(error_handler_middleware)

    # ── Routes ───────────────────────────────────────────────────────────
    # Health + classification: intentionally without api_v1_prefix (public endpoints)
    app.include_router(health_router)
    app.include_router(classification_router)

    v1 = settings.api_v1_prefix
    app.include_router(query_router, prefix=v1)
    app.include_router(tools_router, prefix=v1)
    app.include_router(rag_router, prefix=v1)
    app.include_router(quran_router, prefix=v1)

    # ── Root ─────────────────────────────────────────────────────────────
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
            "query_endpoint": f"{v1}/query",
        }

    logger.info(f"Athar API v{settings.app_version} created (debug={settings.debug})")
    return app


_API_DESCRIPTION = """
# Athar Islamic QA System

Multi-agent Islamic QA system based on Fanar-Sadiq architecture.

## Features
- Intent classification (fiqh, quran, hadith, seerah, …)
- Grounded answers with citations
- Deterministic calculators (zakat, inheritance)
- Arabic & English support

## Authentication
All query endpoints require an `X-API-Key` header.
"""

app = create_app()
