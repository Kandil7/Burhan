"""Unit tests for the missing-requested-evidence detector."""

from src.verification.checks.missing_evidence import detect_missing_requested_evidence


def test_empty_inputs_are_clean():
    assert detect_missing_requested_evidence("", "") == []


def test_short_query_is_guarded():
    # two words, below the four-word minimum
    assert detect_missing_requested_evidence("أريد آية", "أي إجابة") == []


def test_plain_question_is_clean():
    assert detect_missing_requested_evidence("ما حكم الزكاة في المال؟", "الزكاة واجبة") == []


def test_quran_request_without_quran_in_answer_is_flagged():
    violations = detect_missing_requested_evidence(
        "أريد آية عن الصلاة اليومية",
        "الصلاة واجبة على المسلم",
    )
    assert [v["type"] for v in violations] == ["missing_quran_evidence"]


def test_quran_request_satisfied_by_verse_reference():
    violations = detect_missing_requested_evidence(
        "أريد آية عن الصلاة اليومية",
        "الدليل من سورة المائدة: 82",
    )
    assert violations == []


def test_hadith_request_without_hadith_in_answer_is_flagged():
    violations = detect_missing_requested_evidence(
        "أريد حديث عن الصلاة الجماعية",
        "الصلاة واجبة على المسلم",
    )
    assert [v["type"] for v in violations] == ["missing_hadith_evidence"]


def test_hadith_request_satisfied_by_collection_reference():
    violations = detect_missing_requested_evidence(
        "أريد حديث عن الصلاة الجماعية",
        "وقد رواه صحيح البخاري في كتابه",
    )
    assert violations == []
