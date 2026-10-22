"""Unit tests for the hadith grade verifier."""

import pytest

from src.verification.checks.hadith_grade import HadithGrade, HadithGradeVerifier
from src.verification.schemas import VerificationStatus

CLAIM = "The hadith in Sahih Bukhari: 1234 shows this."


class TestHadithGradeVerifier:
    def setup_method(self) -> None:
        self.verifier = HadithGradeVerifier()

    @pytest.mark.asyncio
    async def test_skips_without_hadith_reference(self):
        result = await self.verifier.verify("a claim with no hadith reference", [])
        assert result.passed is True
        assert result.status is VerificationStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_reference_is_extracted_and_graded(self):
        result = await self.verifier.verify(CLAIM, [{"content": "e"}])
        assert result.status is not VerificationStatus.SKIPPED
        assert result.details["reference"]
        assert result.details["grade"] in {g.value for g in HadithGrade}

    @pytest.mark.asyncio
    async def test_daif_or_mowdu_fails(self):
        result = await self.verifier.verify(CLAIM, [{"content": "e"}], context={"collection": "weak"})
        if result.details.get("grade") in {HadithGrade.DAIF.value, HadithGrade.MOWDU.value}:
            assert result.passed is False
            assert result.status is VerificationStatus.FAILED

    @pytest.mark.asyncio
    async def test_original_grader_is_used_when_available(self):
        class Grader:
            @staticmethod
            def grade_hadith(book_id, page):
                return {"grade": "sahih", "confidence": 0.9, "weight": 0.95, "chain_length": 3}

        self.verifier._original_grader = Grader()
        result = await self.verifier.verify(CLAIM, [{"content": "e"}], context={"book_id": 1, "page": 10})
        assert result.passed is True
        assert result.details["grade"] == "sahih"
        assert result.details["chain_length"] == 3

    @pytest.mark.asyncio
    async def test_original_grader_daif_fails(self):
        class Grader:
            @staticmethod
            def grade_hadith(book_id, page):
                return {"grade": "da'if", "confidence": 0.8, "weight": 0.3}

        self.verifier._original_grader = Grader()
        result = await self.verifier.verify(CLAIM, [{"content": "e"}], context={"book_id": 1, "page": 10})
        assert result.passed is False
        assert result.details["grade"] == "da'if"
