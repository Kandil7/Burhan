"""
API response schemas for Athar Islamic QA system.

Pydantic models for response structure and documentation.
"""

from pydantic import BaseModel, Field


class CitationResponse(BaseModel):
    """
    Citation in API response.

    Structured reference for sources used in answer generation.
    """
    id: str = Field(description="Citation ID: C1, C2, C3, etc.")
    type: str = Field(
        description="Source type: quran, hadith, fatwa, fiqh_book, dua, seerah, tafsir, aqeedah",
        examples=["quran", "hadith", "fatwa", "fiqh_book", "dua", "seerah", "tafsir", "aqeedah"]
    )
    source: str = Field(description="Normalized source name")
    reference: str = Field(description="Specific reference (book, chapter, number)")
    url: str | None = Field(
        None,
        description="External URL for verification",
        examples=["https://quran.com/2/255", "https://sunnah.com/bukhari/1234"]
    )
    text_excerpt: str | None = Field(
        None,
        description="Quoted passage from source"
    )


class QueryResponse(BaseModel):
    """
    Response model for POST /api/v1/query endpoint.

    Contains answer, citations, and metadata for display.
    """
    query_id: str = Field(description="Unique query ID for tracking")
    intent: str = Field(
        description="Detected intent",
        examples=["fiqh", "quran", "zakat", "inheritance"]
    )
    intent_confidence: float = Field(
        description="Confidence in intent classification (0.0-1.0)",
        ge=0.0,
        le=1.0,
        examples=[0.92, 0.85]
    )
    answer: str = Field(description="Generated answer text")
    citations: list[CitationResponse] = Field(
        default_factory=list,
        description="List of citations with structured references"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Processing metadata (agent, time, madhhab, etc.)"
    )
    follow_up_suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )


class HealthResponse(BaseModel):
    """
    Health check response for GET /health endpoint.

    Returns service status and version information.
    """
    status: str = Field(default="ok", examples=["ok", "error"])
    version: str = Field(default="0.1.0", description="API version")
    services: dict = Field(
        default_factory=dict,
        description="Status of dependent services (postgres, redis, qdrant)"
    )


class ErrorResponse(BaseModel):
    """
    Error response for failed requests.

    Returned when request validation fails or internal error occurs.
    """
    error: str = Field(description="Error type or message")
    detail: str | None = Field(
        None,
        description="Detailed error message for debugging"
    )
    request_id: str | None = Field(
        None,
        description="Request ID for error tracking"
    )
