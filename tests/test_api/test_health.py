"""
Tests for health and metrics endpoints.

The metrics reset route mutates process state, so it must stay unreachable
unless debug mode is on.
"""

import pytest
from fastapi.testclient import TestClient

from src.config.logging_config import metrics
from src.config.settings import settings


@pytest.fixture
def client():
    """Create test client."""
    from src.api.main import app

    return TestClient(app)


class TestHealthEndpoints:
    """Basic liveness and readiness checks."""

    def test_health_ok(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_metrics_ok(self, client):
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "counters" in response.json()

    def test_requests_are_counted(self, client):
        """The collector must see the traffic, or the metrics endpoints are dead."""
        metrics.reset()

        client.get("/")

        counters = metrics.get_metrics()["counters"]
        assert counters.get("GET /") == 1
        assert counters.get("status.2xx") == 1
        timings = metrics.get_metrics()["timings"]
        assert any(entry["name"] == "GET /" for entry in timings)


class TestMetricsReset:
    """The reset route is destructive and development-only."""

    def test_reset_hidden_by_default(self, client):
        response = client.post("/metrics/reset")

        assert response.status_code == 404

    def test_reset_available_in_debug(self, client, monkeypatch):
        monkeypatch.setattr(settings, "debug", True)
        metrics.increment("test.counter")

        response = client.post("/metrics/reset")

        assert response.status_code == 204
        # The reset clears what was recorded before it. The reset request
        # itself is counted afterwards, so the collector is not empty.
        assert "test.counter" not in metrics.get_metrics()["counters"]

    def test_get_method_not_allowed(self, client, monkeypatch):
        """A GET must never mutate metrics."""
        monkeypatch.setattr(settings, "debug", True)

        response = client.get("/metrics/reset")

        assert response.status_code == 405
