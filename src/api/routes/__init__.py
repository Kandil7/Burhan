"""
API Routes for Burhan Islamic QA system.

This module contains all API route definitions.

Submodules:
- ask: Ask endpoint (RAG question answering)
- classify: Classification endpoint
- fiqh: Fiqh-specific endpoint
- health: Health check endpoint
- quran: Quran-related endpoints
- search: Search endpoint
- tools: Tools endpoint (calculators, etc.)
"""

from src.api.routes.ask import ask_router
from src.api.routes.classify import classify_router
from src.api.routes.fiqh import fiqh_router
from src.api.routes.health import health_router
from src.api.routes.quran import quran_router
from src.api.routes.search import search_router
from src.api.routes.tools import tools_router

__all__ = [
    "ask_router",
    "classify_router",
    "fiqh_router",
    "health_router",
    "quran_router",
    "search_router",
    "tools_router",
]
