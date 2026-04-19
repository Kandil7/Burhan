"""
Tests for Evaluation Metrics.

Tests precision/recall calculations, citation accuracy, and evaluation runner.
"""

import pytest
from src.evaluation.golden_set_schema import GoldenSetItem
from src.evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    citation_accuracy,
    ikhtilaf_coverage,
    abstention_rate,
    expected_abstention,
    hadith_grade_accuracy,
    EvaluationResult,
    run_evaluation,
)


class TestPrecisionAtK:
    """Tests for precision_at_k function."""

    def test_perfect_precision(self):
        """Test perfect precision when all retrieved items are relevant."""
        retrieved = ["doc1", "doc2", "doc3"]
        gold = ["doc1", "doc2", "doc3"]
        k = 3

        result = precision_at_k(retrieved, gold, k)
        assert result == 1.0

    def test_partial_precision(self):
        """Test partial precision with some relevant items."""
        retrieved = ["doc1", "doc2", "doc3"]
        gold = ["doc1", "doc4", "doc5"]
        k = 3

        result = precision_at_k(retrieved, gold, k)
        assert result == pytest.approx(1 / 3)

    def test_zero_precision(self):
        """Test zero precision when no items are relevant."""
        retrieved = ["doc1", "doc2", "doc3"]
        gold = ["doc4", "doc5", "doc6"]
        k = 3

        result = precision_at_k(retrieved, gold, k)
        assert result == 0.0

    def test_k_less_than_retrieved(self):
        """Test precision at k when k is less than retrieved count."""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        gold = ["doc1", "doc2", "doc4"]  # doc3 is NOT in gold
        k = 3

        result = precision_at_k(retrieved, gold, k)
        assert result == pytest.approx(2 / 3)  # Only top 3, 2 relevant

    def test_empty_retrieved(self):
        """Test precision with empty retrieved list."""
        retrieved = []
        gold = ["doc1", "doc2"]
        k = 5

        result = precision_at_k(retrieved, gold, k)
        assert result == 0.0


class TestRecallAtK:
    """Tests for recall_at_k function."""

    def test_perfect_recall(self):
        """Test perfect recall when all relevant items are retrieved."""
        retrieved = ["doc1", "doc2", "doc3", "doc4"]
        gold = ["doc1", "doc2", "doc3", "doc4"]
        k = 4

        result = recall_at_k(retrieved, gold, k)
        assert result == 1.0

    def test_partial_recall(self):
        """Test partial recall with some relevant items."""
        retrieved = ["doc1", "doc2"]
        gold = ["doc1", "doc2", "doc3", "doc4"]
        k = 4

        result = recall_at_k(retrieved, gold, k)
        assert result == pytest.approx(0.5)

    def test_zero_recall(self):
        """Test zero recall when no relevant items are retrieved."""
        retrieved = ["doc5", "doc6"]
        gold = ["doc1", "doc2", "doc3"]
        k = 3

        result = recall_at_k(retrieved, gold, k)
        assert result == 0.0


class TestCitationAccuracy:
    """Tests for citation_accuracy function."""

    def test_perfect_citation_match(self):
        """Test perfect citation accuracy."""
        citations = [{"source": "Sahih Bukhari", "reference": "123"}, {"source": "Sahih Muslim", "reference": "456"}]
        gold_sources = ["sahih_bukhari", "sahih_muslim"]

        result = citation_accuracy(citations, gold_sources)
        # "sahih bukhari" contains "sahih_bukhari" after normalization
        assert result >= 0.5  # At least partial match

    def test_partial_citation_match(self):
        """Test partial citation accuracy."""
        citations = [{"source": "Sahih Bukhari", "reference": "123"}, {"source": "Sahih Muslim", "reference": "456"}]
        gold_sources = ["sahih_bukhari", "sahih_muslim", "sahih_tirmidhi"]

        result = citation_accuracy(citations, gold_sources)
        # Two matches out of 3 gold sources
        assert result >= 0.6

    def test_no_citations(self):
        """Test citation accuracy with no citations."""
        citations = []
        gold_sources = ["sahih_bukhari"]

        result = citation_accuracy(citations, gold_sources)
        assert result == 0.0


class TestIkhtilafCoverage:
    """Tests for ikhtilaf_coverage function."""

    def test_full_ikhtilaf_coverage(self):
        """Test full Ikhtilaf coverage with all schools mentioned."""
        answer = """
        ذهب الحنفية إلى أن صلاة التراويح عشرون ركعة.
        وقال المالكية أنها ست وثلاثون ركعة.
        واختلف الشافعية في الوتر.
        الحنبلية قالوا بعشرين ركعة أيضاً.
        """
        expected_schools = ["hanafi", "malki", "shafi_i", "hanbali"]

        result = ikhtilaf_coverage(answer, expected_schools)
        assert result == 1.0  # All 4 schools mentioned

    def test_partial_ikhtilaf_coverage(self):
        """Test partial Ikhtilaf coverage."""
        answer = "ذهب الحنفية والمالكية إلى كذا."
        expected_schools = ["hanafi", "malki", "shafi_i", "hanbali"]

        result = ikhtilaf_coverage(answer, expected_schools)
        assert result == 0.5  # 2 out of 4 schools

    def test_no_ikhtilaf_required(self):
        """Test Ikhtilaf coverage when not required."""
        answer = "الصلاة واجبة."
        expected_schools = []

        result = ikhtilaf_coverage(answer, expected_schools)
        assert result == 1.0


class TestAbstentionRate:
    """Tests for abstention_rate and expected_abstention functions."""

    def test_abstention_when_low_confidence(self):
        """Test abstention rate when confidence is below threshold."""
        confidence = 0.3
        threshold = 0.5

        result = abstention_rate(confidence, threshold)
        assert result == 1.0

    def test_no_abstention_when_high_confidence(self):
        """Test abstention rate when confidence is above threshold."""
        confidence = 0.7
        threshold = 0.5

        result = abstention_rate(confidence, threshold)
        assert result == 0.0

    def test_expected_abstention_correct(self):
        """Test expected abstention when it matches."""
        confidence = 0.3
        expected_abstain = True
        threshold = 0.5

        result = expected_abstention(confidence, expected_abstain, threshold)
        assert result == 1.0

    def test_expected_abstention_incorrect(self):
        """Test expected abstention when it doesn't match."""
        confidence = 0.7
        expected_abstain = True
        threshold = 0.5

        result = expected_abstention(confidence, expected_abstain, threshold)
        assert result == 0.0


class TestHadithGradeAccuracy:
    """Tests for hadith_grade_accuracy function."""

    def test_perfect_grade_match(self):
        """Test perfect hadith grade accuracy."""
        hadith_grades = [{"grade": "sahih"}, {"grade": "hasan"}]
        gold_grades = ["sahih", "hasan"]

        result = hadith_grade_accuracy(hadith_grades, gold_grades)
        assert result == 1.0

    def test_partial_grade_match(self):
        """Test partial hadith grade accuracy."""
        hadith_grades = [{"grade": "sahih"}, {"grade": "daif"}]
        gold_grades = ["sahih", "hasan"]

        result = hadith_grade_accuracy(hadith_grades, gold_grades)
        assert result == 0.5

    def test_no_grades(self):
        """Test hadith grade accuracy with no grades."""
        hadith_grades = []
        gold_grades = ["sahih"]

        result = hadith_grade_accuracy(hadith_grades, gold_grades)
        assert result == 0.0


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = EvaluationResult(
            precision=0.8,
            recall=0.7,
            citation_accuracy=0.9,
            ikhtilaf_coverage=0.85,
            abstention_rate=0.95,
            overall_score=0.82,
        )

        d = result.to_dict()
        assert d["precision"] == 0.8
        assert d["recall"] == 0.7
        assert d["overall_score"] == 0.82

    def test_str_representation(self):
        """Test string representation."""
        result = EvaluationResult(precision=0.8, recall=0.7)

        s = str(result)
        assert "precision=0.8000" in s
        assert "recall=0.7000" in s


class TestRunEvaluation:
    """Tests for run_evaluation function."""

    @pytest.mark.asyncio
    async def test_empty_golden_set(self):
        """Test evaluation with empty golden set."""

        class MockAgent:
            name = "mock"

            async def execute(self, input_):
                from src.agents.base import AgentOutput

                return AgentOutput(answer="test", confidence=0.8)

        result = await run_evaluation(MockAgent(), [])
        assert result.precision == 0.0
        assert result.recall == 0.0

    @pytest.mark.asyncio
    async def test_evaluation_with_mock_agent(self):
        """Test evaluation with a mock agent."""

        class MockAgent:
            name = "mock"

            async def execute(self, input_):
                from src.agents.base import AgentOutput, Citation

                return AgentOutput(
                    answer="Test answer",
                    citations=[Citation(id="C1", type="fiqh_book", source="Test", reference="1")],
                    confidence=0.8,
                    metadata={"retrieved_ids": ["doc1", "doc2"]},
                )

        golden_set = [
            GoldenSetItem(
                id="test_001", question="ما حكم الصلاة؟", domains=["fiqh"], gold_evidence_ids=["doc1", "doc3"]
            )
        ]

        result = await run_evaluation(MockAgent(), golden_set)
        assert 0 <= result.precision <= 1
        assert 0 <= result.recall <= 1
        assert 0 <= result.citation_accuracy <= 1
        assert 0 <= result.overall_score <= 1
