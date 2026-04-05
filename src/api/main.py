"""
FastAPI application factory for Athar Islamic QA system.

Creates and configures the FastAPI application with:
- CORS middleware
- Error handling
- Request logging
- Route registration
- OpenAPI documentation

Phase 2: Includes tool endpoints for direct access.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.config.logging_config import setup_logging, get_logger
from src.api.middleware.error_handler import error_handler_middleware
from src.api.routes.health import router as health_router
from src.api.routes.query import router as query_router
from src.api.routes.tools import router as tools_router
from src.api.routes.quran import router as quran_router

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Runs on startup and shutdown.
    Phase 2: All tools initialized and ready.
    """
    # Startup
    setup_logging()
    logger.info(
        "app.startup",
        app_name=settings.app_name,
        version="0.3.0",  # Phase 3 version
        environment=settings.app_env
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

## Phase 2 Features
- **Deterministic Calculators**: Zakat and Inheritance
- **Service Tools**: Prayer Times, Hijri Calendar, Dua Retrieval
- **Intent Classification**: 9 intents with routing
- **Direct Tool Access**: Tool endpoints bypass router

## Authentication
Phase 1-2: No authentication required

## Rate Limiting
Phase 1-2: No rate limiting
        """,
        version="0.2.0",
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
    
    # Error handling
    app.middleware("http")(error_handler_middleware)
    
    # ==========================================
    # Routes
    # ==========================================
    app.include_router(health_router)
    app.include_router(query_router, prefix=settings.api_v1_prefix)
    app.include_router(tools_router, prefix=settings.api_v1_prefix)  # Phase 2
    app.include_router(quran_router, prefix=f"{settings.api_v1_prefix}")  # Phase 3
    
    # ==========================================
    # Root endpoint
    # ==========================================
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": "0.3.0",
            "phase": "3 - Quranic Pipeline",
            "docs": "/docs",
            "health": "/health",
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
            }
        }
    
    return app


# Create app instance
app = create_app()
