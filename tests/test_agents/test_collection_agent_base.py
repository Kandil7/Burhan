"""
Tests for CollectionAgent base abstraction.

Tests:
- CollectionAgent can be subclassed
- Abstract methods are properly defined
- IntentLabel enum values work correctly
- Pydantic models work as expected
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.collection_agent import (
    CollectionAgent,
    CollectionAgentConfig,
    IntentLabel,
    RetrievalStrategy,
    VerificationCheck,
    VerificationSuite,
    FallbackPolicy,
    VerificationReport,
)
from src.agents.base import Citation


class TestIntentLabel:
    """Tests for IntentLabel enum."""

    def test_fiqh_intents(self):
        """Test Fiqh-related intent labels."""
        assert IntentLabel.FiqhHukm.value == "fiqh_hukm"
        assert IntentLabel.FiqhMasaail.value == "fiqh_masaail"

    def test_hadith_intents(self):
        """Test Hadith-related intent labels."""
        assert IntentLabel.HadithTakhrij.value == "hadith_takhrij"
        assert IntentLabel.HadithSanad.value == "hadith_sanad"
        assert IntentLabel.HadithMatn.value == "hadith_matn"

    def test_tafsir_intents(self):
        """Test Tafsir-related intent labels."""
        assert IntentLabel.TafsirAyah.value == "tafsir_ayah"
        assert IntentLabel.TafsirMaqasid.value == "tafsir_maqasid"

    def test_aqeedah_intents(self):
        """Test Aqeedah-related intent labels."""
        assert IntentLabel.AqeedahTawhid.value == "aqeedah_tawhid"
        assert IntentLabel.AqeedahIman.value == "aqeedah_iman"

    def test_seerah_intents(self):
        """Test Seerah-related intent labels."""
        assert IntentLabel.SeerahEvent.value == "seerah_event"
        assert IntentLabel.SeerahMilad.value == "seerah_milad"

    def test_usul_fiqh_intents(self):
        """Test Usul Fiqh-related intent labels."""
        assert IntentLabel.UsulFiqhIjtihad.value == "usul_fiqh_ijtihad"
        assert IntentLabel.UsulFiqhQiyas.value == "usul_fiqh_qiyas"

    def test_unknown_intent(self):
        """Test Unknown intent label."""
        assert IntentLabel.Unknown.value == "unknown"


class TestRetrievalStrategy:
    """Tests for RetrievalStrategy Pydantic model."""

    def test_default_values(self):
        """Test default values for retrieval strategy."""
        strategy = RetrievalStrategy()

        assert strategy.dense_weight == 0.7
        assert strategy.sparse_weight == 0.3
        assert strategy.top_k == 12
        assert strategy.rerank is True
        assert strategy.score_threshold == 0.65

    def test_custom_values(self):
        """Test custom values for retrieval strategy."""
        strategy = RetrievalStrategy(
            dense_weight=0.5,
            sparse_weight=0.5,
            top_k=20,
            rerank=False,
            score_threshold=0.7,
        )

        assert strategy.dense_weight == 0.5
        assert strategy.sparse_weight == 0.5
        assert strategy.top_k == 20
        assert strategy.rerank is False
        assert strategy.score_threshold == 0.7

    def test_weight_validation(self):
        """Test that weights are validated (0-1 range)."""
        with pytest.raises(Exception):
            RetrievalStrategy(dense_weight=1.5)  # > 1.0 should fail

        with pytest.raises(Exception):
            RetrievalStrategy(sparse_weight=-0.1)  # < 0 should fail


class TestVerificationCheck:
    """Tests for VerificationCheck Pydantic model."""

    def test_default_values(self):
        """Test default values for verification check."""
        check = VerificationCheck(name="test_check")

        assert check.name == "test_check"
        assert check.fail_policy == "abstain"
        assert check.enabled is True

    def test_custom_values(self):
        """Test custom values for verification check."""
        check = VerificationCheck(
            name="source_check",
            fail_policy="warn",
            enabled=False,
        )

        assert check.name == "source_check"
        assert check.fail_policy == "warn"
        assert check.enabled is False


class TestVerificationSuite:
    """Tests for VerificationSuite Pydantic model."""

    def test_default_values(self):
        """Test default values for verification suite."""
        suite = VerificationSuite()

        assert suite.checks == []
        assert suite.fail_fast is True

    def test_with_checks(self):
        """Test verification suite with checks."""
        checks = [
            VerificationCheck(name="check1"),
            VerificationCheck(name="check2", fail_policy="proceed"),
        ]
        suite = VerificationSuite(checks=checks, fail_fast=False)

        assert len(suite.checks) == 2
        assert suite.fail_fast is False


class TestFallbackPolicy:
    """Tests for FallbackPolicy Pydantic model."""

    def test_default_values(self):
        """Test default values for fallback policy."""
        policy = FallbackPolicy()

        assert policy.strategy == "chatbot"
        assert policy.message is None

    def test_custom_values(self):
        """Test custom values for fallback policy."""
        policy = FallbackPolicy(
            strategy="human_review",
            message="Please consult an expert",
        )

        assert policy.strategy == "human_review"
        assert policy.message == "Please consult an expert"


class TestCollectionAgentConfig:
    """Tests for CollectionAgentConfig Pydantic model."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CollectionAgentConfig(collection_name="test_collection")

        assert config.collection_name == "test_collection"
        assert isinstance(config.strategy, RetrievalStrategy)
        assert isinstance(config.verification_suite, VerificationSuite)
        assert isinstance(config.fallback_policy, FallbackPolicy)

    def test_custom_config(self):
        """Test custom configuration."""
        strategy = RetrievalStrategy(top_k=20)
        suite = VerificationSuite(fail_fast=False)
        policy = FallbackPolicy(strategy="clarify")

        config = CollectionAgentConfig(
            collection_name="fiqh",
            strategy=strategy,
            verification_suite=suite,
            fallback_policy=policy,
        )

        assert config.collection_name == "fiqh"
        assert config.strategy.top_k == 20
        assert config.verification_suite.fail_fast is False
        assert config.fallback_policy.strategy == "clarify"


class TestVerificationReport:
    """Tests for VerificationReport Pydantic model."""

    def test_from_passages(self):
        """Test creating verification report from passages."""
        passages = [
            {"content": "Test passage 1", "metadata": {"source": "test"}},
            {"content": "Test passage 2", "metadata": {"source": "test2"}},
        ]

        report = VerificationReport.from_passages(
            passages=passages,
            is_verified=True,
            confidence=0.9,
        )

        assert report.is_verified is True
        assert report.confidence == 0.9
        assert len(report.verified_passages) == 2

    def test_to_dict(self):
        """Test conversion to dictionary."""
        report = VerificationReport(
            is_verified=True,
            confidence=0.85,
            issues=["issue1"],
            details={"key": "value"},
            verified_passages=[],
        )

        result = report.to_dict()

        assert result["is_verified"] is True
        assert result["confidence"] == 0.85
        assert result["issues"] == ["issue1"]
        assert result["verified_passages_count"] == 0


class ConcreteCollectionAgent(CollectionAgent):
    """
    Concrete implementation of CollectionAgent for testing.
    """

    name = "test_agent"
    COLLECTION = "test_collection"

    def query_intake(self, query: str) -> str:
        """Normalize query - strip and lowercase for test."""
        return query.strip()

    def classify_intent(self, query: str) -> IntentLabel:
        """Simple classification for test."""
        # Check for common fiqh keywords
        fiqh_keywords = ["حكم", "حلال", "حرام", "فقيه", "فتوى"]
        if any(kw in query for kw in fiqh_keywords):
            return IntentLabel.FiqhHukm
        return IntentLabel.Unknown

    async def retrieve_candidates(self, query: str) -> list[dict]:
        """Return mock candidates."""
        return [{"content": "Test passage", "score": 0.9, "metadata": {"source": "test"}}]

    async def rerank_candidates(
        self,
        query: str,
        candidates: list[dict],
    ) -> list[dict]:
        """Return candidates as-is for test."""
        return candidates

    async def run_verification(
        self,
        query: str,
        candidates: list[dict],
    ) -> VerificationReport:
        """Return verification report from candidates."""
        return VerificationReport.from_passages(
            passages=candidates,
            is_verified=True,
            confidence=0.9,
        )

    async def generate_answer(
        self,
        query: str,
        verified_passages: list[dict],
        language: str,
    ) -> str:
        """Return mock answer."""
        return "Test answer"

    def assemble_citations(self, passages: list[dict]) -> list[Citation]:
        """Return mock citations."""
        return [Citation.from_passage(p, i) for i, p in enumerate(passages, 1)]


class TestCollectionAgentSubclass:
    """Tests for CollectionAgent subclassing."""

    def test_can_instantiate_concrete(self):
        """Test that a concrete subclass can be instantiated."""
        agent = ConcreteCollectionAgent()

        assert agent.name == "test_agent"
        assert agent.COLLECTION == "test_collection"
        assert isinstance(agent.config, CollectionAgentConfig)

    def test_abstract_methods_exist(self):
        """Test all abstract methods are defined."""
        agent = ConcreteCollectionAgent()

        # Check all required methods exist
        assert hasattr(agent, "query_intake")
        assert hasattr(agent, "classify_intent")
        assert hasattr(agent, "retrieve_candidates")
        assert hasattr(agent, "rerank_candidates")
        assert hasattr(agent, "run_verification")
        assert hasattr(agent, "generate_answer")
        assert hasattr(agent, "assemble_citations")
        assert hasattr(agent, "run")

    @pytest.mark.asyncio
    async def test_run_method(self):
        """Test the full run() pipeline executes correctly."""
        agent = ConcreteCollectionAgent()

        result = await agent.run(
            raw_question="ما حكم الصيام؟",
            meta={"language": "ar"},
        )

        assert result.answer == "Test answer"
        assert len(result.citations) >= 0
        assert result.metadata["intent"] == "fiqh_hukm"
        assert result.metadata["collection"] == "test_collection"

    @pytest.mark.asyncio
    async def test_run_with_unknown_intent(self):
        """Test run with non-matching query."""
        agent = ConcreteCollectionAgent()

        result = await agent.run(
            raw_question="غير معروف",
            meta={"language": "ar"},
        )

        assert result.metadata["intent"] == "unknown"


class TestCollectionAgentCannotInstantiate:
    """Tests that CollectionAgent cannot be instantiated directly."""

    def test_cannot_instantiate_base(self):
        """Test that CollectionAgent cannot be instantiated without implementation."""
        with pytest.raises(TypeError):
            CollectionAgent()

    def test_abstract_methods_enforced(self):
        """Test that missing abstract methods raise TypeError."""

        # This should fail because we don't implement all abstract methods
        class IncompleteAgent(CollectionAgent):
            name = "incomplete"
            COLLECTION = "test"

            def query_intake(self, query: str) -> str:
                return query

            # Missing other abstract methods

        with pytest.raises(TypeError):
            IncompleteAgent()


class TestCitationIntegration:
    """Tests for Citation integration with CollectionAgent."""

    def test_assemble_citations_from_passages(self):
        """Test assembling citations from passages."""
        agent = ConcreteCollectionAgent()

        passages = [
            {
                "content": "نص الحديث: من حديث عمر",
                "metadata": {
                    "collection": "hadith",
                    "book_title": "صحيح البخاري",
                    "author": "البخاري",
                    "author_death": "256",
                    "page_number": "42",
                },
            },
        ]

        citations = agent.assemble_citations(passages)

        assert len(citations) == 1
        assert citations[0].type == "hadith"
        assert citations[0].source == "صحيح البخاري"
        assert citations[0].id == "C1"
