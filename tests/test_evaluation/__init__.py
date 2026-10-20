"""
Tests for Evaluation module.
"""

from src.evaluation import (
    EvaluationResult,
    GoldenSetItem,
    abstention_rate,
    citation_accuracy,
    get_fiqh_golden_set,
    hadith_grade_accuracy,
    ikhtilaf_coverage,
    precision_at_k,
    recall_at_k,
)

__all__ = [
    "GoldenSetItem",
    "EvaluationResult",
    "get_fiqh_golden_set",
    "precision_at_k",
    "recall_at_k",
    "citation_accuracy",
    "ikhtilaf_coverage",
    "abstention_rate",
    "hadith_grade_accuracy",
]
