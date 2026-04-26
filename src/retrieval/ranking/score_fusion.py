"""
Score Fusion Utilities for Burhan retrieval system.

Provides various score fusion strategies for combining
results from multiple retrievers (semantic, keyword, etc.).

Phase 9: Added score fusion utilities for hybrid retrieval.
"""

from typing import Any


def reciprocal_rank_fusion(
    result_lists: list[list[dict[str, Any]]],
    k: float = 60.0,
    score_field: str = "score",
) -> list[dict[str, Any]]:
    """
    Combine multiple result lists using Reciprocal Rank Fusion (RRF).

    RRF formula: score = sum(1 / (k + rank)) for each list

    Args:
        result_lists: List of result lists from different retrievers
        k: RRF parameter (default: 60)
        score_field: Field name for score in result dicts

    Returns:
        Combined and ranked results
    """
    if not result_lists:
        return []

    # Build RRF scores
    rrf_scores: dict[int, float] = {}

    for result_list in result_lists:
        for rank, result in enumerate(result_list):
            doc_id = result.get("id")
            if doc_id is None:
                continue

            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0

            rrf_scores[doc_id] += 1.0 / (k + rank + 1)

    # Build result map
    id_to_result: dict[int, dict[str, Any]] = {}
    for result_list in result_lists:
        for result in result_list:
            doc_id = result.get("id")
            if doc_id is not None and doc_id not in id_to_result:
                id_to_result[doc_id] = result

    # Sort by RRF score
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

    # Build final results
    final_results = []
    for doc_id in sorted_ids:
        result = id_to_result.get(doc_id, {}).copy()
        result["rrf_score"] = rrf_scores[doc_id]
        final_results.append(result)

    return final_results


def linear_combination_fusion(
    result_lists: list[list[dict[str, Any]]],
    weights: list[float] | None = None,
    score_field: str = "score",
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """
    Combine scores using weighted linear combination.

    Args:
        result_lists: List of result lists from different retrievers
        weights: Weights for each list (default: equal weights)
        score_field: Field name for score in result dicts
        top_k: Number of results to return

    Returns:
        Combined and ranked results
    """
    if not result_lists:
        return []

    # Default to equal weights
    if weights is None:
        weights = [1.0 / len(result_lists)] * len(result_lists)

    if len(weights) != len(result_lists):
        raise ValueError("Number of weights must match number of result lists")

    # Normalize weights
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]

    # Collect all unique documents
    all_docs: dict[int, dict[str, Any]] = {}
    doc_max_scores: dict[int, float] = {}

    for result_list, weight in zip(result_lists, weights):
        for result in result_list:
            doc_id = result.get("id")
            if doc_id is None:
                continue

            # Store first result
            if doc_id not in all_docs:
                all_docs[doc_id] = result.copy()

            # Add weighted score
            doc_score = result.get(score_field, 0)
            if doc_id not in doc_max_scores:
                doc_max_scores[doc_id] = 0.0
            doc_max_scores[doc_id] += doc_score * weight

    # Sort by combined score
    sorted_ids = sorted(doc_max_scores.keys(), key=lambda x: doc_max_scores[x], reverse=True)

    # Build final results
    final_results = []
    for doc_id in sorted_ids[:top_k]:
        result = all_docs[doc_id].copy()
        result["combined_score"] = doc_max_scores[doc_id]
        final_results.append(result)

    return final_results


def score_normalization_min_max(
    scores: list[float],
) -> list[float]:
    """
    Normalize scores to [0, 1] range using min-max normalization.

    Args:
        scores: List of raw scores

    Returns:
        Normalized scores
    """
    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)

    if max_score == min_score:
        return [1.0] * len(scores)

    return [(s - min_score) / (max_score - min_score) for s in scores]


def score_normalization_z_score(
    scores: list[float],
) -> list[float]:
    """
    Normalize scores using z-score standardization.

    Args:
        scores: List of raw scores

    Returns:
        Standardized scores (mean=0, std=1)
    """
    if not scores:
        return []

    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    std = variance**0.5

    if std == 0:
        return [0.0] * len(scores)

    return [(s - mean) / std for s in scores]


def merge_ranked_lists(
    lists: list[list[dict[str, Any]]],
    strategy: str = "rrf",
    k: float = 60.0,
    weights: list[float] | None = None,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """
    Merge multiple ranked lists using specified strategy.

    Args:
        lists: List of ranked result lists
        strategy: Fusion strategy ("rrf", "linear", "interleave")
        k: RRF parameter (for RRF strategy)
        weights: Weights for linear combination (for linear strategy)
        top_k: Number of results to return

    Returns:
        Merged and ranked results
    """
    if not lists:
        return []

    # Filter out empty lists
    non_empty_lists = [l for l in lists if l]
    if not non_empty_lists:
        return []

    if strategy == "rrf":
        return reciprocal_rank_fusion(non_empty_lists, k=k)[:top_k]
    elif strategy == "linear":
        return linear_combination_fusion(non_empty_lists, weights=weights)[:top_k]
    else:
        raise ValueError(f"Unknown fusion strategy: {strategy}")
