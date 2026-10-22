"""Unit tests for the groundedness judge."""

import pytest

from src.verification.checks.groundedness_judge import GroundednessJudge, GroundednessLevel
from src.verification.schemas import VerificationStatus


class TestGroundednessJudge:
    def setup_method(self) -> None:
        self.judge = GroundednessJudge()

    @pytest.mark.asyncio
    async def test_skips_without_claims(self):
        result = await self.judge.verify("", [{"content": "e"}])
        assert result.passed is True
        assert result.status is VerificationStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_fully_grounded_with_evidence(self):
        result = await self.judge.verify("A claim. Another claim.", [{"content": "e"}])
        assert result.passed is True
        assert result.details["level"] == GroundednessLevel.FULL.value
        assert result.details["groundedness_ratio"] == 1.0

    @pytest.mark.asyncio
    async def test_ungrounded_without_evidence(self):
        result = await self.judge.verify("A claim. Another claim.", [])
        assert result.passed is False
        assert result.status is VerificationStatus.FAILED
        assert result.details["level"] == GroundednessLevel.UNGROUNDED.value

    @pytest.mark.asyncio
    async def test_partial_level_reports_warning(self):
        judge = GroundednessJudge(min_evidence_ratio=1.5)
        result = await judge.verify("A claim. Another claim.", [{"content": "e"}])
        # ratio 1.0 is below 1.5 but at or above 0.5: partial
        assert result.status is VerificationStatus.WARNING
        assert result.details["level"] == GroundednessLevel.PARTIAL.value

    def test_is_applicable(self):
        assert self.judge.is_applicable("claim", []) is True
        assert self.judge.is_applicable("claim", None) is False
