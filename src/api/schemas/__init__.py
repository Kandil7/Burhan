"""
API Schemas for Burhan Islamic QA system.

This module contains all Pydantic models for request/response validation.

Submodules:
- ask: Ask endpoint schemas
- classification: Classification schemas
- common: Common schemas (errors, etc.)
- request: Generic request schemas
- response: Generic response schemas
- search: Search endpoint schemas
- tools: Tools endpoint schemas
- trace: Tracing schemas
"""

from src.api.schemas.ask import (
    AskRequest,
    AskResponse,
)
from src.api.schemas.classification import (
    ClassificationResultSchema,
    ClassifyRequest,
    RoutingDecisionSchema,
)
from src.api.schemas.common import (
    ErrorResponse,
)
from src.api.schemas.search import (
    RAGQueryRequest,
    RAGQueryResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from src.api.schemas.tools import (
    DuaRequest,
    DuaResponse,
    HijriRequest,
    HijriResponse,
    InheritanceRequest,
    InheritanceResponse,
    PrayerTimesRequest,
    PrayerTimesResponse,
    ZakatRequest,
    ZakatResponse,
)

__all__ = [
    # Ask
    "AskRequest",
    "AskResponse",
    # Classification
    "ClassifyRequest",
    "ClassificationResultSchema",
    "RoutingDecisionSchema",
    # Common
    "ErrorResponse",
    # Search
    "RAGQueryRequest",
    "RAGQueryResponse",
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    # Tools
    "ZakatRequest",
    "ZakatResponse",
    "InheritanceRequest",
    "InheritanceResponse",
    "PrayerTimesRequest",
    "PrayerTimesResponse",
    "HijriRequest",
    "HijriResponse",
    "DuaRequest",
    "DuaResponse",
]
