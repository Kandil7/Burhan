"""
Evaluation Framework for Burhan RAG System.

This module provides evaluation capabilities for measuring agent performance
on Islamic scholarly questions using golden sets of test cases.
"""

from src.evaluation.golden_set_schema import GoldenSetItem, get_fiqh_golden_set, load_golden_set
from src.evaluation.metrics import (
    EvaluationResult,
    abstention_rate,
    citation_accuracy,
    hadith_grade_accuracy,
    ikhtilaf_coverage,
    precision_at_k,
    recall_at_k,
    run_evaluation,
)

__all__ = [
    "GoldenSetItem",
    "get_fiqh_golden_set",
    "load_golden_set",
    "EvaluationResult",
    "run_evaluation",
    "precision_at_k",
    "recall_at_k",
    "citation_accuracy",
    "ikhtilaf_coverage",
    "abstention_rate",
    "hadith_grade_accuracy",
]
