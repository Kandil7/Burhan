"""Unit tests for the evidence sufficiency verifier."""

import pytest

from src.verification.checks.evidence_sufficiency import (
    EvidenceSufficiencyVerifier,
    SufficiencyCriteria,
)
from src.verification.schemas import VerificationStatus


def make_evidence(count: int, source: str = "s", authority: float = 0.9) -> list[dict]:
    return [
        {"content": f"passage {i}", "source_id": f"{source}{i}", "authority_score": authority} for i in range(count)
    ]


class TestEvidenceSufficiencyVerifier:
    def setup_method(self) -> None:
        self.verifier = EvidenceSufficiencyVerifier(SufficiencyCriteria(min_evidences=2))

    @pytest.mark.asyncio
    async def test_fails_below_minimum_count(self):
        result = await self.verifier.verify("claim", make_evidence(1))
        assert result.passed is False
        assert result.status is VerificationStatus.FAILED
        assert result.details["evidence_count"] == 1

    @pytest.mark.asyncio
    async def test_fails_on_low_authority(self):
        evidence = make_evidence(2, authority=0.1)
        result = await self.verifier.verify("claim", evidence)
        assert result.passed is False
        assert "Authority" in result.message or "authority" in result.message

    @pytest.mark.asyncio
    async def test_fails_when_sources_are_not_multiple(self):
        evidence = [
            {"content": "a", "source_id": "same", "authority_score": 0.9},
            {"content": "b", "source_id": "same", "authority_score": 0.9},
        ]
        result = await self.verifier.verify("claim", evidence)
        assert result.passed is False
        assert "Multiple sources" in result.message

    @pytest.mark.asyncio
    async def test_passes_on_sufficient_diverse_evidence(self):
        result = await self.verifier.verify("claim", make_evidence(3, source="s"))
        assert result.passed is True
        assert result.status is VerificationStatus.PASSED
        assert result.details["evidence_count"] == 3
        assert 0.0 <= result.details["sufficiency_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_non_list_evidence_is_insufficient(self):
        result = await self.verifier.verify("claim", {"content": "one"})
        assert result.passed is False

    def test_is_applicable_requires_evidence(self):
        assert self.verifier.is_applicable("claim", []) is True
        assert self.verifier.is_applicable("claim", None) is False
