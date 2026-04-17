"""
Main FastAPI application for Athar Islamic QA system.

Epic 7: Simplified API layer with thin transport routes.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.error_handler import error_handler_middleware
from src.api.middleware.security import RateLimitMiddleware, SecurityHeadersMiddleware
from src.api.middleware.request_logging import RequestLoggingMiddleware, RequestIDMiddleware
from src.api.routes.health import router as health_router
from src.api.routes.ask import ask_router
from src.api.routes.classify import classify_router
from src.api.routes.search import search_router
from src.api.routes.tools import tools_router
from src.api.routes.quran import router as quran_router
from src.api.routes.fiqh import fiqh_router
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
    app.include_router(classify_router)  # /classify
    app.include_router(fiqh_router)  # /fiqh

    # V1 API routes
    v1 = settings.api_v1_prefix
    app.include_router(ask_router, prefix=v1)  # /api/v1/ask
    app.include_router(search_router, prefix=v1)  # /api/v1/search (merged from rag)
    app.include_router(tools_router, prefix=v1)  # /api/v1/tools
    app.include_router(quran_router, prefix=v1)  # /api/v1/quran

    # ── Root ─────────────────────────────────────────────────────────────
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
            "ask_endpoint": f"{v1}/ask",
            "search_endpoint": f"{v1}/search",
            "classify_endpoint": "/classify",
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

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ask` | POST | Main query answering endpoint |
| `/search` | POST | Search and RAG operations |
| `/classify` | POST | Intent classification only |
| `/tools/zakat` | POST | Zakat calculator |
| `/tools/inheritance` | POST | Inheritance calculator |
| `/tools/prayer-times` | POST | Prayer times |
| `/tools/hijri` | POST | Hijri date conversion |
| `/tools/duas` | POST | Retrieve duas |
| `/quran/*` | GET/POST | Quran-specific endpoints |
| `/health` | GET | Health check |

## Authentication
All query endpoints require an `X-API-Key` header.
"""

app = create_app()
