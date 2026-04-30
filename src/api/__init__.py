"""
API Module for Burhan Islamic QA system.

This module provides the FastAPI application and all REST endpoints.

Submodules:
- main: FastAPI application factory
- lifespan: Application lifecycle management
- routes: API endpoint definitions
- schemas: Request/response data models
- middleware: Request/response middleware
- versioning: API versioning utilities
"""

from src.api.main import app
from src.api.routes.ask import ask_router
from src.api.routes.classify import classify_router
from src.api.routes.fiqh import fiqh_router
from src.api.routes.health import health_router
from src.api.routes.quran import quran_router
from src.api.routes.search import search_router
from src.api.routes.tools import tools_router

__all__ = [
    "app",
    "ask_router",
    "classify_router",
    "fiqh_router",
    "health_router",
    "quran_router",
    "search_router",
    "tools_router",
]
