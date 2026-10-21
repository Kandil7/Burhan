"""
Tests for the deterministic /tools endpoints.

The tool routes accept free-form dictionaries for assets and heirs, so these
tests pin the contract: documented field names work, aliases work, and a typo
returns 422 instead of a generic 500.
"""

import pytest
from fastapi.testclient import TestClient

from src.config.settings import settings

TOOLS_BASE = f"{settings.api_v1_prefix}/tools"


@pytest.fixture
def client():
    """Create test client."""
    from src.api.main import app

    return TestClient(app)


class TestZakatEndpoint:
    """Tests for POST /tools/zakat."""

    def test_documented_example_returns_200(self, client):
        """The example from the OpenAPI schema must succeed."""
        response = client.post(
            f"{TOOLS_BASE}/zakat",
            json={
                "assets": {
                    "cash": 10000,
                    "gold_grams": 50,
                    "silver_grams": 500,
                    "trade_goods": 5000,
                    "stocks": 20000,
                },
                "debts": 0,
                "madhhab": "general",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total_assets"] == pytest.approx(39200.0)
        assert body["zakat_amount"] == pytest.approx(980.0)
        assert body["is_zakatable"] is True
        assert body["breakdown"]["trade_goods"] == pytest.approx(5000.0)
        assert body["breakdown"]["stocks"] == pytest.approx(20000.0)

    def test_canonical_field_names_match_aliases(self, client):
        """Canonical dataclass names produce the same result as aliases."""
        response = client.post(
            f"{TOOLS_BASE}/zakat",
            json={
                "assets": {
                    "cash": 10000,
                    "gold_grams": 50,
                    "silver_grams": 500,
                    "trade_goods_value": 5000,
                    "stocks_value": 20000,
                },
            },
        )

        assert response.status_code == 200
        assert response.json()["zakat_amount"] == pytest.approx(980.0)

    def test_unknown_asset_key_returns_422(self, client):
        """A typo in an asset key must not surface as a 500."""
        response = client.post(
            f"{TOOLS_BASE}/zakat",
            json={"assets": {"cash": 10000, "gold_gram": 50}},
        )

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "gold_gram" in detail
        assert "gold_grams" in detail

    def test_below_nisab_returns_zero(self, client):
        """Assets below nisab produce no zakat."""
        response = client.post(
            f"{TOOLS_BASE}/zakat",
            json={"assets": {"cash": 100}},
        )

        assert response.status_code == 200
        assert response.json()["zakat_amount"] == 0
        assert response.json()["is_zakatable"] is False


class TestInheritanceEndpoint:
    """Tests for POST /tools/inheritance."""

    def test_wife_two_sons_one_daughter(self, client):
        """Fara'id shares sum to the estate."""
        response = client.post(
            f"{TOOLS_BASE}/inheritance",
            json={
                "estate_value": 100000,
                "heirs": {"wife_count": 1, "sons": 2, "daughters": 1},
                "debts": 0,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["total_distributed"] == pytest.approx(100000.0)
        assert body["remaining"] == pytest.approx(0.0)

        shares = {item["heir"]: item["amount"] for item in body["distribution"]}
        assert shares["Wife"] == pytest.approx(12500.0)
        assert shares["Sons"] == pytest.approx(70000.0)
        assert shares["Daughter"] == pytest.approx(17500.0)

    def test_unknown_heir_key_returns_422(self, client):
        """A typo in a heir key must not surface as a 500."""
        response = client.post(
            f"{TOOLS_BASE}/inheritance",
            json={
                "estate_value": 100000,
                "heirs": {"wife_count": 1, "son_count": 2},
            },
        )

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "son_count" in detail
        assert "sons" in detail
