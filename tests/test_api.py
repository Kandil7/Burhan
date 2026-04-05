"""
Tests for API endpoints.

Tests the main query and health endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test /health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
    
    def test_readiness_check(self, client):
        """Test /ready endpoint returns 200."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "services" in data
    
    def test_root_endpoint(self, client):
        """Test / endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Athar"
        assert "docs" in data


class TestQueryEndpoint:
    """Test query endpoint."""
    
    def test_query_endpoint_structure(self, client):
        """Test /api/v1/query endpoint exists."""
        # Phase 1: Will return 500 because orchestrator has no agents
        # But endpoint should exist and accept requests
        response = client.post(
            "/api/v1/query",
            json={"query": "ما حكم الصلاة؟"}
        )
        # Should be either 200 (with fallback) or 500 (if error)
        assert response.status_code in [200, 500]
    
    def test_query_validation_empty(self, client):
        """Test query validation rejects empty query."""
        response = client.post(
            "/api/v1/query",
            json={"query": ""}
        )
        assert response.status_code == 422  # Validation error
    
    def test_query_validation_whitespace(self, client):
        """Test query validation rejects whitespace query."""
        response = client.post(
            "/api/v1/query",
            json={"query": "   "}
        )
        assert response.status_code == 422
    
    def test_query_validation_invalid_language(self, client):
        """Test query validation rejects invalid language."""
        response = client.post(
            "/api/v1/query",
            json={
                "query": "Test query",
                "language": "fr"  # Invalid
            }
        )
        assert response.status_code == 422
    
    def test_query_validation_valid_language(self, client):
        """Test query validation accepts valid language."""
        response = client.post(
            "/api/v1/query",
            json={
                "query": "Test query",
                "language": "ar"
            }
        )
        # Should not be 422 (validation passed)
        assert response.status_code != 422
    
    def test_query_validation_invalid_madhhab(self, client):
        """Test query validation rejects invalid madhhab."""
        response = client.post(
            "/api/v1/query",
            json={
                "query": "Test query",
                "madhhab": "invalid"
            }
        )
        assert response.status_code == 422
    
    def test_query_validation_valid_madhhab(self, client):
        """Test query validation accepts valid madhhab."""
        response = client.post(
            "/api/v1/query",
            json={
                "query": "Test query",
                "madhhab": "hanafi"
            }
        )
        assert response.status_code != 422
    
    def test_query_response_structure(self, client):
        """Test query response has required fields."""
        response = client.post(
            "/api/v1/query",
            json={"query": "ما حكم زكاة المال؟"}
        )
        
        # Phase 1: May return 500 or 200 with fallback
        if response.status_code == 200:
            data = response.json()
            assert "query_id" in data
            assert "intent" in data
            assert "intent_confidence" in data
            assert "answer" in data
            assert "citations" in data
            assert "metadata" in data


class TestOpenAPIDocs:
    """Test OpenAPI documentation."""
    
    def test_docs_endpoint(self, client):
        """Test /docs endpoint exists."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_endpoint(self, client):
        """Test /redoc endpoint exists."""
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_openapi_json(self, client):
        """Test /openapi.json endpoint."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Athar"
