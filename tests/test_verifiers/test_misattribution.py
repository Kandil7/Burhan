"""Unit tests for the misattributed-Quran detector."""

import pytest

from src.verification.checks.misattribution import detect_misattributed_quran


class FakeQuranVerifier:
    """Stands in for ExactQuoteVerifier's is_quran_text."""

    def __init__(self, is_quran: bool) -> None:
        self.is_quran = is_quran
        self.seen: list[str] = []

    async def is_quran_text(self, quote: str) -> bool:
        self.seen.append(quote)
        return self.is_quran


VERSE = "012345678901234567890123456789"
NON_QURAN_CITATIONS = [
    {"source_id": "C1", "book_title": "السيرة النبوية", "metadata": {"collection": "seerah_passages"}}
]
QURAN_CITATIONS = [{"source_id": "C1", "book_title": "القرآن الكريم", "metadata": {"collection": "quran_tafsir"}}]


@pytest.mark.asyncio
async def test_mode_a_flags_verse_cited_to_a_non_quran_book():
    answer = f"ورد في النص «{VERSE}» [C1]"
    violations = await detect_misattributed_quran(answer, NON_QURAN_CITATIONS, FakeQuranVerifier(True))
    assert [v["issue"] for v in violations] == ["quran_text_attributed_to_non_quran_source"]
    assert violations[0]["attributed_to"] == "C1"


@pytest.mark.asyncio
async def test_quran_citation_is_not_flagged():
    answer = f"ورد في النص «{VERSE}» [C1]"
    violations = await detect_misattributed_quran(answer, QURAN_CITATIONS, FakeQuranVerifier(True))
    assert violations == []


@pytest.mark.asyncio
async def test_mode_c_flags_unattributed_verse_in_quotes():
    answer = f"هذا نص ثم «{VERSE}» ثم خاتمة"
    violations = await detect_misattributed_quran(answer, [], FakeQuranVerifier(True))
    assert [v["issue"] for v in violations] == ["quran_verse_in_wrong_delimiter"]
    assert violations[0]["mode"] == "delimiter_confusion"


@pytest.mark.asyncio
async def test_non_quran_quote_is_clean():
    answer = f"ورد في النص «{VERSE}» [C1]"
    violations = await detect_misattributed_quran(answer, NON_QURAN_CITATIONS, FakeQuranVerifier(False))
    assert violations == []


@pytest.mark.asyncio
async def test_short_quotes_are_ignored():
    answer = "نص «قصير» [C1]"
    verifier = FakeQuranVerifier(True)
    violations = await detect_misattributed_quran(answer, NON_QURAN_CITATIONS, verifier)
    assert violations == []
    assert verifier.seen == []
