"""
Schemas for /ask endpoint.

Request/response models for the main query answering endpoint.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    """
    Request model for POST /api/v1/ask endpoint.

    Main entry point for all user queries to the Athar system.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question in Arabic or English",
        examples=["ما حكم زكاة المال؟", "How do I calculate inheritance?"],
    )
    language: str | None = Field(
        None,
        pattern="^(ar|en)$",
        description="Response language (auto-detect if null)",
        examples=["ar", "en"],
    )
    location: dict | None = Field(
        None,
        description="Location for prayer times: {lat, lng, city?, country?}",
        examples=[{"lat": 25.2854, "lng": 51.5310, "city": "Doha", "country": "Qatar"}],
    )
    madhhab: str | None = Field(
        None,
        pattern="^(hanafi|maliki|shafii|hanbali|auto)$",
        description="Islamic school of jurisprudence",
        examples=["hanafi", "shafii", "auto"],
    )
    session_id: str | None = Field(
        None,
        max_length=100,
        description="Session ID for conversation context",
    )
    stream: bool = Field(
        False,
        description="Enable streaming response (Server-Sent Events)",
    )

    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """Validate query is not empty or whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        import re

        v = re.sub(r"<[^>]+>", "", v)
        return v.strip()

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str | None) -> str | None:
        """Sanitize session ID."""
        if v is not None:
            import re

            v = re.sub(r"[^a-zA-Z0-9_-]", "", v)[:100]
        return v

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: dict | None) -> dict | None:
        """Validate location has required fields."""
        if v is not None:
            if "lat" not in v or "lng" not in v:
                raise ValueError("Location must include 'lat' and 'lng'")
            if not (-90 <= v["lat"] <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= v["lng"] <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        return v


# Filter parameters for query
class QueryFilters(BaseModel):
    """Filter parameters for query."""

    author: str | None = Field(None, description="Filter by author name")
    era: str | None = Field(None, description="Filter by historical era")
    book_id: int | None = Field(None, ge=0, description="Filter by book ID")
    category: str | None = Field(None, description="Filter by category")
    death_year_min: int | None = Field(None, ge=0, description="Minimum author death year")
    death_year_max: int | None = Field(None, ge=0, description="Maximum author death year")


class AskResponse(BaseModel):
    """
    Response model for POST /api/v1/ask endpoint.

    Contains answer, citations, and metadata for display.
    """

    query_id: str = Field(
        ...,
        description="Unique query ID for tracking",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    intent: str = Field(
        ...,
        description="Detected intent",
        examples=["fiqh", "quran", "zakat", "inheritance"],
    )
    intent_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in intent classification (0.0-1.0)",
        examples=[0.92, 0.85],
    )
    answer: str = Field(..., description="Generated answer text")
    citations: list[dict] = Field(
        default_factory=list,
        description="List of citations with structured references",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Processing metadata (agent, time, madhhab, etc.)",
    )
    follow_up_suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions",
    )
    # Trace metadata
    trace_id: str = Field(..., description="Request trace ID")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")
