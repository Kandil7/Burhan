"""
API request schemas for Burhan Islamic QA system.

Pydantic models for request validation and documentation.
"""

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """
    Request model for POST /api/v1/query endpoint.

    Main entry point for all user queries to the Burhan system.
    """

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question in Arabic or English",
        examples=["ما حكم زكاة المال؟", "How do I calculate inheritance?"],
    )
    language: str | None = Field(
        None, pattern="^(ar|en)$", description="Response language (auto-detect if null)", examples=["ar", "en"]
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
    session_id: str | None = Field(None, max_length=100, description="Session ID for conversation context")
    stream: bool = Field(False, description="Enable streaming response (Server-Sent Events)")

    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v):
        """Validate query is not empty or whitespace."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        # Sanitize: remove potential HTML/script tags
        import re

        v = re.sub(r"<[^>]+>", "", v)
        return v.strip()

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v):
        """Sanitize session ID."""
        if v is not None:
            # Only allow alphanumeric, dash, underscore
            import re

            v = re.sub(r"[^a-zA-Z0-9_-]", "", v)[:100]
        return v

    @field_validator("location")
    @classmethod
    def validate_location(cls, v):
        """Validate location has required fields."""
        if v is not None:
            if "lat" not in v or "lng" not in v:
                raise ValueError("Location must include 'lat' and 'lng'")
            if not (-90 <= v["lat"] <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= v["lng"] <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        return v


class HealthRequest(BaseModel):
    """Request model for health checks (empty)."""

    pass
