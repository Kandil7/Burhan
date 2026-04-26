"""
Tests for retrieval strategies module.

Tests the retrieval matrix, strategy retrieval, and collection mapping functions.
"""

import pytest

from src.agents.collection import RetrievalStrategy
from src.retrieval.strategies import (
    DEFAULT_STRATEGY,
    get_collection_for_agent,
    get_strategy_for_agent,
    retrieval_matrix,
)


class TestGetStrategyForAgent:
    """Tests for get_strategy_for_agent function."""

    @pytest.mark.parametrize(
        "agent_name,expected_dense_weight,expected_sparse_weight,expected_top_k,expected_rerank,expected_threshold",
        [
            ("fiqh_agent", 0.6, 0.4, 80, True, 0.65),
            ("hadith_agent", 0.5, 0.5, 60, True, 0.70),
            ("tafsir_agent", 0.7, 0.3, 40, True, 0.75),
            ("aqeedah_agent", 0.6, 0.4, 50, True, 0.65),
            ("seerah_agent", 0.5, 0.5, 50, True, 0.60),
            ("usul_fiqh_agent", 0.7, 0.3, 60, True, 0.70),
            ("history_agent", 0.5, 0.5, 50, True, 0.60),
            ("language_agent", 0.4, 0.6, 40, True, 0.65),
            ("general_islamic_agent", 0.5, 0.5, 30, False, 0.55),
        ],
    )
    def test_retrieval_strategy_values(
        self,
        agent_name: str,
        expected_dense_weight: float,
        expected_sparse_weight: float,
        expected_top_k: int,
        expected_rerank: bool,
        expected_threshold: float,
    ) -> None:
        """Test each agent's retrieval strategy has correct values."""
        strategy = get_strategy_for_agent(agent_name)

        assert isinstance(strategy, RetrievalStrategy)
        assert strategy.dense_weight == expected_dense_weight
        assert strategy.sparse_weight == expected_sparse_weight
        assert strategy.top_k == expected_top_k
        assert strategy.rerank == expected_rerank
        assert strategy.score_threshold == expected_threshold

    def test_unknown_agent_returns_default_strategy(self) -> None:
        """Test that unknown agent returns default strategy."""
        unknown_agents = ["unknown_agent", "fake_agent", "", "random_agent"]

        for agent_name in unknown_agents:
            strategy = get_strategy_for_agent(agent_name)
            assert strategy == DEFAULT_STRATEGY


class TestGetCollectionForAgent:
    """Tests for get_collection_for_agent function."""

    @pytest.mark.parametrize(
        "agent_name,expected_collection",
        [
            ("fiqh_agent", "fiqh"),
            ("hadith_agent", "hadith"),
            ("tafsir_agent", "quran"),
            ("aqeedah_agent", "aqeedah"),
            ("seerah_agent", "seerah"),
            ("usul_fiqh_agent", "usul_fiqh"),
            ("history_agent", "islamic_history"),
            ("language_agent", "arabic_language"),
            ("general_islamic_agent", "general_islamic"),
        ],
    )
    def test_collection_mapping(self, agent_name: str, expected_collection: str) -> None:
        """Test each agent maps to correct collection."""
        collection = get_collection_for_agent(agent_name)
        assert collection == expected_collection

    def test_unknown_agent_returns_unknown(self) -> None:
        """Test that unknown agent returns 'unknown'."""
        unknown_agents = ["unknown_agent", "fake_agent", "", "random_agent"]

        for agent_name in unknown_agents:
            collection = get_collection_for_agent(agent_name)
            assert collection == "unknown"


class TestRetrievalMatrix:
    """Tests for retrieval_matrix dictionary."""

    def test_all_agents_in_matrix(self) -> None:
        """Test all expected agents are in retrieval_matrix."""
        expected_agents = [
            "fiqh_agent",
            "hadith_agent",
            "tafsir_agent",
            "aqeedah_agent",
            "seerah_agent",
            "usul_fiqh_agent",
            "history_agent",
            "language_agent",
            "general_islamic_agent",
        ]

        for agent_name in expected_agents:
            assert agent_name in retrieval_matrix
            assert isinstance(retrieval_matrix[agent_name], RetrievalStrategy)

    def test_weight_sum_equals_one(self) -> None:
        """Test dense_weight + sparse_weight = 1.0 for all strategies."""
        for agent_name, strategy in retrieval_matrix.items():
            total_weight = strategy.dense_weight + strategy.sparse_weight
            assert total_weight == 1.0, (
                f"{agent_name}: dense_weight ({strategy.dense_weight}) + "
                f"sparse_weight ({strategy.sparse_weight}) = {total_weight}, expected 1.0"
            )

    def test_top_k_in_valid_range(self) -> None:
        """Test top_k is within valid range (1-100)."""
        for agent_name, strategy in retrieval_matrix.items():
            assert 1 <= strategy.top_k <= 100, f"{agent_name}: top_k {strategy.top_k} not in range [1, 100]"

    def test_score_threshold_in_valid_range(self) -> None:
        """Test score_threshold is within valid range (0.0-1.0)."""
        for agent_name, strategy in retrieval_matrix.items():
            assert 0.0 <= strategy.score_threshold <= 1.0, (
                f"{agent_name}: score_threshold {strategy.score_threshold} not in range [0.0, 1.0]"
            )
