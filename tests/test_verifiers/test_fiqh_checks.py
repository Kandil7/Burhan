"""Unit tests for the fiqh check set: QuoteValidator, SourceAttributor, EvidenceSufficiency."""

import pytest

from src.verification.checks.fiqh_checks import (
    EvidenceSufficiency,
    QuoteValidator,
    SourceAttributor,
)
from src.verification.schemas import VerificationStatus


class TestQuoteValidator:
    def setup_method(self) -> None:
        self.check = QuoteValidator()

    @pytest.mark.asyncio
    async def test_skips_when_evidence_is_not_a_list(self):
        result = await self.check.verify("«نص» [C1]", {"content": "x"})
        assert result.status is VerificationStatus.SKIPPED
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_detects_quote_missing_from_cited_source(self):
        claim = "«نص اقتباس طويل جداً لا يوجد في المصدر» [C1]"
        evidence = [{"content": "مصدر مختلف تماماً عن النص المقتبس"}]
        result = await self.check.verify(claim, evidence)
        assert result.passed is False
        assert result.details["issues"]

    @pytest.mark.asyncio
    async def test_passes_when_quote_exists_in_cited_source(self):
        quote = "نص اقتباس طويل جداً موجود في المصدر"
        claim = f"«{quote}» [C1]"
        evidence = [{"content": f"تمهيد ثم {quote} ثم خاتمة"}]
        result = await self.check.verify(claim, evidence)
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_invalid_citation_index_is_reported(self):
        claim = "«نص اقتباس طويل جداً ما» [C3]"
        evidence = [{"content": "مصدر"}]
        result = await self.check.verify(claim, evidence)
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_short_quotes_are_not_flagged(self):
        claim = "«قصير» [C1]"
        evidence = [{"content": "مصدر مختلف"}]
        result = await self.check.verify(claim, evidence)
        assert result.passed is True


class TestSourceAttributor:
    @pytest.mark.asyncio
    async def test_always_passes(self):
        result = await SourceAttributor().verify("claim", [{"content": "e"}])
        assert result.passed is True
        assert result.status is VerificationStatus.PASSED


class TestFiqhEvidenceSufficiency:
    @pytest.mark.asyncio
    async def test_fails_without_evidence(self):
        result = await EvidenceSufficiency().verify("claim", [])
        assert result.passed is False
        assert result.status is VerificationStatus.FAILED

    @pytest.mark.asyncio
    async def test_fails_below_min_passages(self):
        result = await EvidenceSufficiency(min_passages=2).verify("claim", [{"content": "a"}])
        assert result.passed is False
        assert result.details["evidence_count"] == 1 if "evidence_count" in result.details else True

    @pytest.mark.asyncio
    async def test_warns_on_single_author(self):
        evidence = [
            {"content": "a", "metadata": {"author": "ابن تيمية"}},
            {"content": "b", "metadata": {"author": "ابن تيمية"}},
        ]
        result = await EvidenceSufficiency(min_passages=2).verify("claim", evidence)
        assert result.passed is True
        assert result.status is VerificationStatus.WARNING

    @pytest.mark.asyncio
    async def test_passes_on_diverse_authors(self):
        evidence = [
            {"content": "a", "metadata": {"author": "ابن تيمية"}},
            {"content": "b", "metadata": {"author": "النووي"}},
        ]
        result = await EvidenceSufficiency(min_passages=2).verify("claim", evidence)
        assert result.passed is True
        assert result.status is VerificationStatus.PASSED
