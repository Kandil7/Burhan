"""
FastAPI application factory for Athar Islamic QA system.

Creates and configures the FastAPI application with:
- CORS middleware
- Error handling
- Request logging
- Route registration
- OpenAPI documentation
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.config.logging_config import setup_logging, get_logger
from src.api.middleware.error_handler import error_handler_middleware
from src.api.routes.health import router as health_router
from src.api.routes.query import router as query_router

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Runs on startup and shutdown.
    Phase 1: Basic logging setup
    Phase 2+: Initialize database, Redis, Qdrant connections
    """
    # Startup
    setup_logging()
    logger.info(
        "app.startup",
        app_name=settings.app_name,
        version="0.1.0",
        environment=settings.app_env
    )
    
    yield
    
    # Shutdown
    logger.info("app.shutdown")
    # TODO: Close database connections, Redis, etc.


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

## Authentication
Phase 1: No authentication required
Phase 2: API key authentication for rate limiting

## Rate Limiting
Phase 1: No rate limiting
Phase 2: 100 requests/minute for free tier
        """,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug
    )
    
    # ==========================================
    # Middleware
    # ==========================================
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Error handling (custom middleware)
    app.middleware("http")(error_handler_middleware)
    
    # ==========================================
    # Routes
    # ==========================================
    app.include_router(health_router)
    app.include_router(query_router, prefix=settings.api_v1_prefix)
    
    # ==========================================
    # Root endpoint
    # ==========================================
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
            "query_endpoint": f"{settings.api_v1_prefix}/query"
        }
    
    return app


# Create app instance
app = create_app()
