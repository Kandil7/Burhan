"""
Evaluation Metrics for Athar RAG System.

Provides metrics for measuring retrieval quality, answer accuracy,
citation correctness, Ikhtilaf coverage, and abstention behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agents.base import AgentOutput
    from src.evaluation.golden_set_schema import GoldenSetItem


# =============================================================================
# Retrieval Metrics
# =============================================================================


def precision_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int) -> float:
    """
    Calculate Precision@k - the proportion of retrieved items that are relevant.

    Args:
        retrieved_ids: List of retrieved evidence IDs.
        gold_ids: List of golden/expected evidence IDs.
        k: Number of top results to consider.

    Returns:
        Precision@k value between 0 and 1.
    """
    if not gold_ids or k <= 0:
        return 0.0

    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0

    relevant = sum(1 for id_ in top_k if id_ in gold_ids)
    return relevant / k


def recall_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int) -> float:
    """
    Calculate Recall@k - the proportion of relevant items that were retrieved.

    Args:
        retrieved_ids: List of retrieved evidence IDs.
        gold_ids: List of golden/expected evidence IDs.
        k: Number of top results to consider.

    Returns:
        Recall@k value between 0 and 1.
    """
    if not gold_ids or k <= 0:
        return 0.0

    top_k = set(retrieved_ids[:k])
    relevant = sum(1 for id_ in gold_ids if id_ in top_k)
    return relevant / len(gold_ids)


# =============================================================================
# Citation Metrics
# =============================================================================


def citation_accuracy(citations: list[dict], gold_sources: list[str]) -> float:
    """
    Calculate citation accuracy - how well the citations match expected sources.

    Args:
        citations: List of citation dictionaries with 'source' and 'reference' fields.
        gold_sources: List of expected source identifiers.

    Returns:
        Citation accuracy score between 0 and 1.
    """
    if not citations or not gold_sources:
        return 0.0

    # Normalize sources for comparison (replace underscores with spaces)
    gold_set = set(gold_sources)
    matched = 0

    for citation in citations:
        # Check if citation source matches any gold source
        source = citation.get("source", "").lower().replace("_", " ")
        for gold in gold_set:
            gold_normalized = gold.lower().replace("_", " ")
            if gold_normalized in source or source in gold_normalized:
                matched += 1
                break

    return min(matched / len(gold_sources), 1.0)


def extract_citation_ids(citations: list[dict]) -> list[str]:
    """Extract source IDs from citations for retrieval comparison."""
    return [citation.get("source", "") for citation in citations]


# =============================================================================
# Ikhtilaf (Difference of Opinion) Coverage
# =============================================================================


def ikhtilaf_coverage(answer: str, expected_schools: list[str]) -> float:
    """
    Calculate Ikhtilaf coverage - whether the answer includes madhhab differences.

    Args:
        answer: The generated answer text.
        expected_schools: List of expected madhhabs to be covered.

    Returns:
        Ikhtilaf coverage score between 0 and 1.
    """
    if not expected_schools:
        return 1.0

    answer_lower = answer.lower()

    # Common madhhab names in Arabic and transliteration
    school_keywords = {
        "hanafi": ["حنيفي", "حنفي", "الحنفية", "الحنفية", "hanafi", "hanaf"],
        "malki": ["ماليكي", "مالكي", "المالكية", "المالكي", "malki", "maliki"],
        "shafi_i": ["شافعي", "الشافعية", "الشافعية", "shafi", "shafii"],
        "hanbali": ["حنبلي", "حنبلي", "الحنبيلة", "الحنابلة", "hanbali", "hanbali"],
        "zahiri": ["ظاهري", "الظاهرة", "zahiri"],
        "ibadi": [" Ibadi"],
    }

    matched_schools = set()
    for school in expected_schools:
        school_key = school.lower()
        if school_key in school_keywords:
            keywords = school_keywords[school_key]
            if any(kw.lower() in answer_lower for kw in keywords):
                matched_schools.add(school)
        else:
            # Try direct match with the school name itself
            if school.lower() in answer_lower:
                matched_schools.add(school)

    return len(matched_schools) / len(expected_schools) if expected_schools else 1.0


# =============================================================================
# Abstention Metrics
# =============================================================================


def abstention_rate(confidence: float, threshold: float = 0.5) -> float:
    """
    Calculate whether agent abstained based on confidence threshold.

    Args:
        confidence: Agent's confidence score (0 to 1).
        threshold: Minimum confidence to answer (default 0.5).

    Returns:
        1.0 if agent abstained (confidence below threshold), else 0.0.
    """
    return 1.0 if confidence < threshold else 0.0


def expected_abstention(actual_confidence: float, expected_abstain: bool, threshold: float = 0.5) -> float:
    """
    Check if abstention behavior matches expectations.

    Args:
        actual_confidence: Actual confidence score from agent.
        expected_abstain: Whether abstention was expected.
        threshold: Confidence threshold for abstention.

    Returns:
        1.0 if abstention matches expectation, else 0.0.
    """
    did_abstain = actual_confidence < threshold
    return 1.0 if did_abstain == expected_abstain else 0.0


# =============================================================================
# Hadith Grade Accuracy
# =============================================================================


def hadith_grade_accuracy(hadith_grades: list[dict], gold_grades: list[str]) -> float:
    """
    Calculate hadith grade accuracy - do cited hadiths have correct grades?

    Args:
        hadith_grades: List of dictionaries with 'grade' field.
        gold_grades: List of expected grades (e.g., ['sahih', 'hasan']).

    Returns:
        Accuracy score between 0 and 1.
    """
    if not hadith_grades:
        return 0.0

    gold_set = set(gold_grades)
    matched = 0

    for hg in hadith_grades:
        grade = hg.get("grade", "").lower()
        if any(gold.lower() in grade or grade in gold.lower() for gold in gold_set):
            matched += 1

    return matched / len(hadith_grades)


# =============================================================================
# Evaluation Result
# =============================================================================


@dataclass
class EvaluationResult:
    """
    Aggregated evaluation results for a test run.

    Attributes:
        precision: Mean Precision@k across all test items.
        recall: Mean Recall@k across all test items.
        citation_accuracy: Mean citation accuracy across all test items.
        ikhtilaf_coverage: Mean Ikhtilaf coverage across relevant test items.
        abstention_rate: Proportion of items where abstention was correct.
        overall_score: Weighted combination of all metrics.
    """

    precision: float = 0.0
    recall: float = 0.0
    citation_accuracy: float = 0.0
    ikhtilaf_coverage: float = 0.0
    abstention_rate: float = 0.0
    overall_score: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "citation_accuracy": round(self.citation_accuracy, 4),
            "ikhtilaf_coverage": round(self.ikhtilaf_coverage, 4),
            "abstention_rate": round(self.abstention_rate, 4),
            "overall_score": round(self.overall_score, 4),
        }

    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"EvaluationResult(\n"
            f"  precision={self.precision:.4f},\n"
            f"  recall={self.recall:.4f},\n"
            f"  citation_accuracy={self.citation_accuracy:.4f},\n"
            f"  ikhtilaf_coverage={self.ikhtilaf_coverage:.4f},\n"
            f"  abstention_rate={self.abstention_rate:.4f},\n"
            f"  overall_score={self.overall_score:.4f}\n"
            f")"
        )


# =============================================================================
# Evaluation Runner
# =============================================================================


async def run_evaluation(
    agent: "BaseAgent", golden_set: list["GoldenSetItem"], k: int = 5, abstention_threshold: float = 0.5
) -> EvaluationResult:
    """
    Run evaluation on a golden set using an agent.

    Args:
        agent: The agent to evaluate (must implement execute method).
        golden_set: List of GoldenSetItem test cases.
        k: Number of top retrieval results to consider.
        abstention_threshold: Confidence threshold for abstention.

    Returns:
        EvaluationResult with aggregated metrics.
    """
    from src.agents.base import AgentInput

    if not golden_set:
        return EvaluationResult()

    precisions = []
    recalls = []
    citation_accuracies = []
    ikhtilaf_coverages = []
    abstention_scores = []

    for item in golden_set:
        # Run agent on question
        input_ = AgentInput(query=item.question, language="ar", metadata={"domains": item.domains})

        try:
            output = await agent.execute(input_)
        except Exception as e:
            # Handle agent execution errors gracefully
            precisions.append(0.0)
            recalls.append(0.0)
            citation_accuracies.append(0.0)
            ikhtilaf_coverages.append(0.0)
            abstention_scores.append(0.0)
            continue

        # Extract retrieved IDs from metadata if available
        retrieved_ids = output.metadata.get("retrieved_ids", [])
        gold_ids = item.gold_evidence_ids

        # Calculate retrieval metrics
        prec = precision_at_k(retrieved_ids, gold_ids, k)
        rec = recall_at_k(retrieved_ids, gold_ids, k)
        precisions.append(prec)
        recalls.append(rec)

        # Calculate citation accuracy
        citations = [{"source": c.source, "reference": c.reference} for c in output.citations]
        cit_acc = citation_accuracy(citations, gold_ids)
        citation_accuracies.append(cit_acc)

        # Calculate Ikhtilaf coverage if required
        if item.ikhtilaf_required:
            expected_schools = item.metrics_flags.get("expected_schools", [])
            ikht_cov = ikhtilaf_coverage(output.answer, expected_schools)
        else:
            ikht_cov = 1.0  # Not required, full score
        ikhtilaf_coverages.append(ikht_cov)

        # Calculate abstention correctness
        abst = expected_abstention(output.confidence, item.abstention_expected, abstention_threshold)
        abstention_scores.append(abst)

    # Aggregate results
    n = len(golden_set)
    result = EvaluationResult(
        precision=sum(precisions) / n if n > 0 else 0.0,
        recall=sum(recalls) / n if n > 0 else 0.0,
        citation_accuracy=sum(citation_accuracies) / n if n > 0 else 0.0,
        ikhtilaf_coverage=sum(ikhtilaf_coverages) / n if n > 0 else 0.0,
        abstention_rate=sum(abstention_scores) / n if n > 0 else 0.0,
    )

    # Calculate weighted overall score
    result.overall_score = (
        0.20 * result.precision
        + 0.20 * result.recall
        + 0.25 * result.citation_accuracy
        + 0.20 * result.ikhtilaf_coverage
        + 0.15 * result.abstention_rate
    )

    return result


# =============================================================================
# BaseAgent Import for Type Checking
# =============================================================================


class BaseAgent:
    """Placeholder for type checking - actual import from src.agents.base."""

    pass
