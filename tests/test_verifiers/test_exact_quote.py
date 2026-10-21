"""Tests for the exact-quote verifier.

Arabic quotes rarely match a stored passage byte for byte: the model drops
diacritics, normalises alef forms, and writes ta-marbuta differently. The
verifier has to fold those variants, while still rejecting fabricated quotes.
"""

import pytest

from src.verification.checks.exact_quote import ExactQuoteVerifier


@pytest.fixture()
def verifier() -> ExactQuoteVerifier:
    return ExactQuoteVerifier()


@pytest.mark.asyncio
async def test_quote_with_different_diacritics_passes(verifier):
    """The passage carries tashkeel, the answer does not."""
    result = await verifier.verify(
        "قال: «صلاة الجماعة سنة مؤكدة» [C1]",
        [{"content": "صَلَاةُ الْجَمَاعَةِ سُنَّةٌ مُؤَكَّدَةٌ"}],
    )

    assert result.passed is True


@pytest.mark.asyncio
async def test_quote_with_alef_variants_passes(verifier):
    """أ/إ/آ fold to a plain alef on both sides."""
    result = await verifier.verify(
        "قال: «إنما الأعمال بالنيات»",
        [{"content": "إِنَّمَا الأَعْمَالُ بِالنِّيَّاتِ"}],
    )

    assert result.passed is True


@pytest.mark.asyncio
async def test_fabricated_quote_fails(verifier):
    """A quoted phrase that is not in any passage is a hard violation."""
    result = await verifier.verify(
        "قال: «صلاة الجماعة فرض عين على كل مسلم»",
        [{"content": "صلاة الجماعة سنة مؤكدة على الرجال"}],
    )

    assert result.passed is False
    assert result.details["failed_quotes"]


@pytest.mark.asyncio
async def test_no_quotes_is_skipped(verifier):
    """An answer with no quoted text has nothing to verify."""
    result = await verifier.verify(
        "صلاة الجماعة سنة مؤكدة في المسجد.",
        [{"content": "صلاة الجماعة سنة مؤكدة"}],
    )

    assert result.passed is True
    assert result.status.value == "skipped"
