"""Tests for the contradiction verifier.

The verifier compares each answer statement against each passage. It must not
fire on the ordinary fiqh pattern where one passage negates a ruling for one
group and another affirms it for a different group.
"""

import pytest

from src.verification.checks.contradiction import ContradictionVerifier


@pytest.fixture()
def verifier() -> ContradictionVerifier:
    return ContradictionVerifier()


FIQH_PASSAGES = [
    {"content": "باب صلاة الجماعة. صلاة الجماعة سنة مؤكدة على الرجال في المسجد."},
    {"content": "لا تجب صلاة الجماعة على المرأة، وتصح منفردة في بيتها."},
]


@pytest.mark.asyncio
async def test_positive_statement_is_not_contradicted_by_a_passage_about_another_group(verifier):
    """One negated passage must not condemn a statement about a different subject."""
    result = await verifier.verify("صلاة الجماعة سنة مؤكدة في المسجد.", FIQH_PASSAGES)

    assert result.passed is True
    assert result.message == "No contradictions found"


@pytest.mark.asyncio
async def test_negative_statement_against_positive_passage_is_a_contradiction(verifier):
    """A statement that denies what a passage affirms is a contradiction."""
    result = await verifier.verify(
        "صلاة الجماعة ليست واجبة على الرجال في المسجد.",
        [{"content": "صلاة الجماعة واجبة على الرجال في المسجد."}],
    )

    assert result.passed is False
    assert result.details["contradictions"][0]["reason"] == "polarity_conflict"


@pytest.mark.asyncio
async def test_numeric_conflict_is_detected(verifier):
    """Two different verse counts for the same surah conflict."""
    result = await verifier.verify(
        "عدد آيات سورة البقرة 285 آية.",
        [{"content": "عدد آيات سورة البقرة 286 آية."}],
    )

    assert result.passed is False
    assert result.details["contradictions"][0]["reason"] == "numeric_conflict"


@pytest.mark.asyncio
async def test_matching_number_is_not_a_conflict(verifier):
    """The same number in statement and passage passes."""
    result = await verifier.verify(
        "عدد آيات سورة البقرة 286 آية.",
        [{"content": "عدد آيات سورة البقرة 286 آية."}],
    )

    assert result.passed is True


@pytest.mark.asyncio
async def test_idiomatic_la_is_not_treated_as_negation(verifier):
    """ "لا شك" is emphasis, not a negation of the predicate."""
    result = await verifier.verify(
        "لا شك أن صلاة الجماعة سنة مؤكدة في المسجد.",
        [{"content": "صلاة الجماعة سنة مؤكدة في المسجد."}],
    )

    assert result.passed is True


@pytest.mark.asyncio
async def test_substring_la_inside_illa_is_not_negation(verifier):
    """ "إلا" contains "لا" as a substring but is not a negation."""
    result = await verifier.verify(
        "تصح صلاة الجماعة في المسجد.",
        [{"content": "تصح صلاة الجماعة إلا في المسجد."}],
    )

    assert result.passed is True


@pytest.mark.asyncio
async def test_restrictive_negation_is_not_a_denial(verifier):
    """ "لا ... إلا" restricts a rule; it does not deny it."""
    result = await verifier.verify(
        "يسن إعادة صلاة الكسوف مع الجماعة الثانية.",
        [{"content": "لا يجوز إعادة صلاة الكسوف إلا إن صلاها منفردا فيسن إعادتها معهم."}],
    )

    assert result.passed is True


@pytest.mark.asyncio
async def test_unrelated_passage_does_not_conflict(verifier):
    """Low content overlap is not evidence of a contradiction."""
    result = await verifier.verify(
        "الصلاة عماد الدين.",
        [{"content": "لا يجوز بيع الغرر في الفقه الإسلامي."}],
    )

    assert result.passed is True


@pytest.mark.asyncio
async def test_empty_evidence_is_skipped_not_passed(verifier):
    """No evidence means the check did not run; it must not claim a pass."""
    result = await verifier.verify("صلاة الجماعة سنة مؤكدة.", [])

    assert result.status.value == "skipped"
    assert result.message == "No claim or no evidence to compare"


@pytest.mark.asyncio
async def test_english_polarity_conflict(verifier):
    """The English negation path still works."""
    result = await verifier.verify(
        "The prayer is not obligatory for travelers.",
        [{"content": "The prayer is obligatory for travelers."}],
    )

    assert result.passed is False
    assert result.details["contradictions"][0]["reason"] == "polarity_conflict"
