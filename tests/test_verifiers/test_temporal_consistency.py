"""Unit tests for the temporal consistency verifier."""

import pytest

from src.verification.checks.temporal_consistency import TemporalConsistencyVerifier
from src.verification.schemas import VerificationStatus


class TestTemporalConsistencyVerifier:
    def setup_method(self) -> None:
        self.verifier = TemporalConsistencyVerifier()

    @pytest.mark.asyncio
    async def test_skips_without_temporal_information(self):
        result = await self.verifier.verify("a claim without dates", [{"content": "e"}])
        assert result.passed is True
        assert result.status is VerificationStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_passes_for_one_date_and_no_evidence_dates(self):
        result = await self.verifier.verify("the event happened in 40 AH", [{"content": "e"}])
        assert result.passed is True
        assert result.status is VerificationStatus.PASSED

    @pytest.mark.asyncio
    async def test_contradiction_needs_evidence_dates(self):
        # evidence date extraction is a placeholder returning no dates, so a
        # single claim date can never contradict; the guard is the skip path.
        result = await self.verifier.verify("in 100 AH and also 101 AH", [])
        assert result.passed is True

    def test_find_temporal_contradictions_flags_large_gaps(self):
        contradictions = self.verifier._find_temporal_contradictions([("AH 100", 100)], [("AH 400", 400)])
        assert len(contradictions) == 1

    def test_find_temporal_contradictions_allows_close_years(self):
        contradictions = self.verifier._find_temporal_contradictions([("AH 100", 100)], [("AH 150", 150)])
        assert contradictions == []

    def test_is_applicable(self):
        assert self.verifier.is_applicable("claim", []) is True
