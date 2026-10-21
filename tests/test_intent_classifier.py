"""Tests for the canonical KeywordBasedClassifier routing rules."""

import pytest

from src.application.router.classifier_factory import KeywordBasedClassifier
from src.domain.intents import Intent


@pytest.fixture()
def classifier() -> KeywordBasedClassifier:
    return KeywordBasedClassifier()


@pytest.mark.parametrize(
    "query",
    [
        "ما حكم زكاة المال؟",
        "ما هي أحكام زكاة عروض التجارة؟",
        "هل على الذهب زكاة؟",
        "ما نصاب زكاة الفطر؟",
        "كيف أحسب زكاة مالي؟",
    ],
)
def test_zakat_ruling_questions_are_fiqh(classifier, query):
    """A zakat question without an amount is a knowledge question."""
    assert classifier.classify_sync(query).intent is Intent.FIQH


@pytest.mark.parametrize(
    "query",
    [
        "زكاة 100000 ريال",
        "احسب زكاة 5000 دولار",
        "زكاة الذهب 85 جرام",
    ],
)
def test_zakat_requests_with_an_amount_reach_the_calculator(classifier, query):
    """An amount is what the zakat calculator consumes."""
    assert classifier.classify_sync(query).intent is Intent.ZAKAT


@pytest.mark.parametrize(
    "query",
    [
        "ما حكم الميراث؟",
        "تقسيم الميراث",
        "كيف أقسم الميراث؟",
        "ما نصيب الزوجة من تركة زوجها؟",
        "ما هي الفرائض في الإسلام؟",
    ],
)
def test_inheritance_ruling_questions_are_fiqh(classifier, query):
    """A question about inheritance rules is not a distribution request."""
    assert classifier.classify_sync(query).intent is Intent.FIQH


@pytest.mark.parametrize(
    "query",
    [
        "ميراث زوجة وأم",
        "تقسيم تركة 100000",
        "ورثة ابن وبنت",
    ],
)
def test_inheritance_cases_reach_the_calculator(classifier, query):
    """A described case, or an estate value, is a distribution request."""
    assert classifier.classify_sync(query).intent is Intent.INHERITANCE


def test_plain_fiqh_question_is_unaffected(classifier):
    """The downgrade must not disturb ordinary fiqh routing."""
    assert classifier.classify_sync("ما حكم صلاة الجماعة في المسجد؟").intent is Intent.FIQH


def test_proposition_ala_does_not_match_the_name_ali(classifier):
    """ "على" is a preposition; it must not route a question to Seerah."""
    assert classifier.classify_sync("هل يجب على المسلم صيام رمضان؟").intent is Intent.FIQH
