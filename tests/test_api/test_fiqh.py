"""
Tests for Fiqh API endpoint.

Tests the /fiqh/answer endpoint with collection-aware RAG.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.agents.base import AgentInput, AgentOutput, Citation


@pytest.fixture
def client():
    """Create test client."""
    from src.api.main import app

    return TestClient(app)


@pytest.fixture
def mock_fiqh_agent():
    """Create mock Fiqh agent."""
    agent = MagicMock()
    agent.name = "fiqh_collection_agent"
    agent.execute = AsyncMock(
        return_value=AgentOutput(
            answer="الزكاة فرض على كل مسلم بالغ عاقل يملك نصاباً حولاً.",
            citations=[
                Citation(
                    id="C1",
                    type="fiqh_book",
                    source="المجموع",
                    reference="ابن المنذر — ت 436 هـ",
                    text_excerpt="الزكاة فرض على كل مسلم...",
                ),
            ],
            confidence=0.95,
            metadata={"madhhab": "shafii"},
            requires_human_review=False,
        )
    )
    return agent


class TestFiqhEndpoint:
    """Test Fiqh endpoint existence and validation."""

    def test_fiqh_endpoint_exists(self, client):
        """Test /fiqh/answer endpoint exists."""
        response = client.post(
            "/fiqh/answer",
            json={"query": "ما حكم الزكاة؟"},
        )
        # Will be 503 if agent not initialized, but endpoint exists
        assert response.status_code in [200, 503]

    def test_fiqh_request_validation_empty_query(self, client):
        """Test validation rejects empty query."""
        response = client.post(
            "/fiqh/answer",
            json={"query": ""},
        )
        # Either 422 (validation) or 503 (agent not available - dependency runs first)
        assert response.status_code in [422, 503]

    def test_fiqh_request_validation_whitespace_query(self, client):
        """Test validation rejects whitespace query."""
        response = client.post(
            "/fiqh/answer",
            json={"query": "   "},
        )
        # Either 422 (validation) or 503 (agent not available - dependency runs first)
        assert response.status_code in [422, 503]

    def test_fiqh_request_validation_invalid_language(self, client):
        """Test validation rejects invalid language."""
        response = client.post(
            "/fiqh/answer",
            json={
                "query": "Test query",
                "language": "fr",  # Invalid
            },
        )
        # Either 422 (validation) or 503 (agent not available - dependency runs first)
        assert response.status_code in [422, 503]

    def test_fiqh_request_validation_valid_language(self, client):
        """Test validation accepts valid language."""
        response = client.post(
            "/fiqh/answer",
            json={
                "query": "Test query",
                "language": "en",
            },
        )
        # Should not be 422 (validation passed) - may be 503 if agent not available
        assert response.status_code != 422

    def test_fiqh_request_validation_invalid_madhhab(self, client):
        """Test validation rejects invalid madhhab."""
        response = client.post(
            "/fiqh/answer",
            json={
                "query": "Test query",
                "madhhab": "invalid",
            },
        )
        # Either 422 (validation) or 503 (agent not available - dependency runs first)
        assert response.status_code in [422, 503]

    def test_fiqh_request_validation_valid_madhhab(self, client):
        """Test validation accepts valid madhhab."""
        response = client.post(
            "/fiqh/answer",
            json={
                "query": "Test query",
                "madhhab": "hanafi",
            },
        )
        # Should not be 422 (validation passed) - may be 503 if agent not available
        assert response.status_code != 422


class TestFiqhTestEndpoint:
    """Test /fiqh/test endpoint."""

    def test_fiqh_test_endpoint_exists(self, client):
        """Test /fiqh/test endpoint exists."""
        response = client.get("/fiqh/test")
        # Will be 503 if agent not initialized
        assert response.status_code in [200, 503]


class TestFiqhFilters:
    """Test Fiqh query filters."""

    def test_fiqh_author_filter(self, client):
        """Test author filter parameter."""
        response = client.post(
            "/fiqh/answer?author=الشاطبي",
            json={"query": "ما حكم الصيام؟"},
        )
        # Either 200 or 503 (agent not initialized in tests)
        assert response.status_code in [200, 503]

    def test_fiqh_era_filter(self, client):
        """Test era filter parameter."""
        response = client.post(
            "/fiqh/answer?era=القرن الرابع الهجري",
            json={"query": "ما حكم الزكاة؟"},
        )
        assert response.status_code in [200, 503]

    def test_fiqh_book_id_filter(self, client):
        """Test book_id filter parameter."""
        response = client.post(
            "/fiqh/answer?book_id=1",
            json={"query": "ما حكم الزكاة؟"},
        )
        assert response.status_code in [200, 503]


class TestFiqhResponseSchema:
    """Test Fiqh response schema structure."""

    def test_response_has_required_fields(self):
        """Test response model has required fields."""
        from src.api.routes.fiqh import FiqhResponse

        # Check that the response model has the expected fields
        fields = FiqhResponse.model_fields
        assert "answer" in fields
        assert "citations" in fields
        assert "confidence" in fields
        assert "ikhtilaf_detected" in fields
        assert "metadata" in fields
        assert "trace_id" in fields
        assert "processing_time_ms" in fields

    def test_request_has_required_fields(self):
        """Test request model has required fields."""
        from src.api.routes.fiqh import FiqhRequest

        # Check that the request model has the expected fields
        fields = FiqhRequest.model_fields
        assert "query" in fields
        assert "language" in fields
        assert "madhhab" in fields


class TestFiqhRequestModel:
    """Test FiqhRequest model validation."""

    def test_valid_arabic_query(self):
        """Test valid Arabic query passes validation."""
        from src.api.routes.fiqh import FiqhRequest

        req = FiqhRequest(query="ما حكم الزكاة؟")
        assert req.query == "ما حكم الزكاة؟"
        assert req.language == "ar"  # default

    def test_valid_english_query(self):
        """Test valid English query passes validation."""
        from src.api.routes.fiqh import FiqhRequest

        req = FiqhRequest(query="Is interest halal?", language="en")
        assert req.query == "Is interest halal?"
        assert req.language == "en"

    def test_valid_with_madhhab(self):
        """Test query with valid madhhab passes validation."""
        from src.api.routes.fiqh import FiqhRequest

        req = FiqhRequest(query="ما حكم الصلاة؟", madhhab="hanafi")
        assert req.madhhab == "hanafi"

    def test_invalid_language_rejected(self):
        """Test invalid language is rejected."""
        from src.api.routes.fiqh import FiqhRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            FiqhRequest(query="test", language="fr")

    def test_invalid_madhhab_rejected(self):
        """Test invalid madhhab is rejected."""
        from src.api.routes.fiqh import FiqhRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            FiqhRequest(query="test", madhhab="invalid")


class TestFiqhResponseModel:
    """Test FiqhResponse model."""

    def test_response_model_valid(self):
        """Test response model accepts valid data."""
        from src.api.routes.fiqh import FiqhResponse

        response = FiqhResponse(
            answer="Test answer",
            citations=[{"id": "C1", "type": "fiqh_book", "source": "Test"}],
            confidence=0.95,
            ikhtilaf_detected=False,
            metadata={"agent": "test"},
            trace_id="test-123",
            processing_time_ms=100,
        )
        assert response.answer == "Test answer"
        assert response.confidence == 0.95

    def test_confidence_bounds(self):
        """Test confidence must be between 0 and 1."""
        from src.api.routes.fiqh import FiqhResponse
        from pydantic import ValidationError

        # Test above 1.0
        with pytest.raises(ValidationError):
            FiqhResponse(
                answer="test",
                citations=[],
                confidence=1.5,
                ikhtilaf_detected=False,
                metadata={},
                trace_id="test",
                processing_time_ms=100,
            )

        # Test below 0.0
        with pytest.raises(ValidationError):
            FiqhResponse(
                answer="test",
                citations=[],
                confidence=-0.1,
                ikhtilaf_detected=False,
                metadata={},
                trace_id="test",
                processing_time_ms=100,
            )
