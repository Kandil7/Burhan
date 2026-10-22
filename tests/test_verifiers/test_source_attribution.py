"""Unit tests for the source attribution verifier."""

import pytest

from src.verification.checks.source_attribution import SourceAttributionVerifier
from src.verification.schemas import VerificationStatus


class TestSourceAttributionVerifier:
    def setup_method(self) -> None:
        self.verifier = SourceAttributionVerifier()

    @pytest.mark.asyncio
    async def test_skips_when_no_sources_claimed(self):
        result = await self.verifier.verify("a plain sentence", [{"content": "e"}])
        assert result.passed is True
        assert result.status is VerificationStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_fails_for_sources_missing_from_evidence(self):
        claim = "As in [Unknown Book] the ruling is clear."
        result = await self.verifier.verify(claim, [{"content": "evidence"}])
        assert result.passed is False
        assert result.status is VerificationStatus.FAILED
        assert result.details["invalid_sources"]

    @pytest.mark.asyncio
    async def test_passes_when_claimed_sources_match_evidence(self):
        claim = "As in [Bukhari] the ruling is clear."
        evidence = [{"text": "evidence text", "metadata": {"book": "Bukhari"}}]
        result = await self.verifier.verify(claim, evidence)
        assert result.passed is True
        assert result.details["valid_sources"]

    @pytest.mark.asyncio
    async def test_context_sources_count_as_valid(self):
        claim = "As in [Bukhari] the ruling is clear."
        result = await self.verifier.verify(claim, [{"content": "e"}], context={"sources": ["Bukhari"]})
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_citation_markers_match_by_position(self):
        claim = "As in [C1] the ruling is clear."
        result = await self.verifier.verify(claim, [{"content": "evidence text"}])
        assert result.passed is True

    def test_is_applicable(self):
        assert self.verifier.is_applicable("anything", []) is True
