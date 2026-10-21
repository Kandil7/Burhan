"""
Tests for CollectionAgent base abstraction.

Tests:
- CollectionAgent can be subclassed
- Abstract methods are properly defined
- Agents classify to domain Intents
- Pydantic models work as expected
"""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.agents.base import Citation
from src.agents.collection import (
    CollectionAgent,
    CollectionAgentConfig,
    FallbackPolicy,
    RetrievalStrategy,
    VerificationCheck,
    VerificationReport,
    VerificationSuite,
)
from src.domain.intents import Intent


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
        with pytest.raises(ValidationError):
            RetrievalStrategy(dense_weight=1.5)  # > 1.0 should fail

        with pytest.raises(ValidationError):
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

    def classify_intent(self, query: str) -> Intent:
        """Simple classification for test."""
        # Check for common fiqh keywords
        fiqh_keywords = ["حكم", "حلال", "حرام", "فقيه", "فتوى"]
        if any(kw in query for kw in fiqh_keywords):
            return Intent.FIQH
        return Intent.ISLAMIC_KNOWLEDGE

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
        answer: str = "",
        stage: str = "evidence",
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


class _QuotaLimitedClient:
    """A model client that refuses any request above its output quota."""

    class _Completions:
        def __init__(self, outer: "_QuotaLimitedClient") -> None:
            self.outer = outer

        async def create(self, *, model, messages, temperature, max_tokens):
            self.outer.calls.append(max_tokens)
            if max_tokens > self.outer.limit:
                raise RuntimeError(
                    "Request too large for model on output tokens per minute (OTPM): "
                    f"Limit {self.outer.limit}, Requested {max_tokens}"
                )
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="composed answer"))])

    def __init__(self, limit: int = 1000) -> None:
        self.limit = limit
        self.calls: list[int] = []
        self.chat = SimpleNamespace(completions=self._Completions(self))


class TestOutputBudgetRetry:
    """A metered provider can refuse a request over its output budget."""

    @pytest.mark.asyncio
    async def test_retries_with_a_smaller_budget(self, monkeypatch):
        from src.config.settings import settings

        monkeypatch.setattr(settings, "llm_max_tokens", 4096)
        agent = ConcreteCollectionAgent()
        agent.llm_client = _QuotaLimitedClient(limit=1000)

        answer = await agent._complete(
            system="system",
            user="user",
            max_tokens=2048,
            temperature=0.2,
        )

        assert answer == "composed answer"
        assert agent.llm_client.calls == [2048, 1000]

    @pytest.mark.asyncio
    async def test_gives_up_when_every_budget_is_refused(self, monkeypatch):
        from src.config.settings import settings

        monkeypatch.setattr(settings, "llm_max_tokens", 4096)
        agent = ConcreteCollectionAgent()
        agent.llm_client = _QuotaLimitedClient(limit=100)

        with pytest.raises(RuntimeError):
            await agent._complete(
                system="system",
                user="user",
                max_tokens=2048,
                temperature=0.2,
            )

    @pytest.mark.asyncio
    async def test_another_failure_is_not_retried(self, monkeypatch):
        from src.config.settings import settings

        monkeypatch.setattr(settings, "llm_max_tokens", 4096)
        agent = ConcreteCollectionAgent()
        client = _QuotaLimitedClient(limit=1000)

        async def boom(**kwargs):
            raise ValueError("connection reset")

        client.chat.completions.create = boom
        agent.llm_client = client

        with pytest.raises(ValueError):
            await agent._complete(
                system="system",
                user="user",
                max_tokens=2048,
                temperature=0.2,
            )

        assert client.calls == []


class _EvidenceFallbackAgent(ConcreteCollectionAgent):
    """Agent whose generation step returns the raw evidence text."""

    def _format_passages(self, passages: list[dict]) -> str:
        return "\n".join(f"[C{i}] {p.get('content', '')}" for i, p in enumerate(passages, 1))

    async def generate_answer(
        self,
        query: str,
        verified_passages: list[dict],
        language: str,
    ) -> str:
        return self._format_passages(verified_passages)


class _PartialFilterAgent(ConcreteCollectionAgent):
    """Agent whose verification keeps one of the retrieved candidates."""

    async def retrieve_candidates(self, query: str) -> list[dict]:
        return [
            {"content": "kept passage", "score": 0.9, "metadata": {"source": "test"}},
            {"content": "dropped passage", "score": 0.1, "metadata": {"source": "test"}},
        ]

    async def run_verification(
        self,
        query: str,
        candidates: list[dict],
        answer: str = "",
        stage: str = "evidence",
    ) -> VerificationReport:
        kept = [c for c in candidates if c["content"] == "kept passage"]
        return VerificationReport(
            is_verified=True,
            confidence=0.95,
            verified_passages=kept,
        )


class _DropsEveryCandidateAgent(ConcreteCollectionAgent):
    """Agent whose verification rejects every retrieved candidate."""

    async def run_verification(
        self,
        query: str,
        candidates: list[dict],
        answer: str = "",
        stage: str = "evidence",
    ) -> VerificationReport:
        return VerificationReport(
            is_verified=False,
            confidence=0.2,
            verified_passages=[],
        )


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
        assert result.metadata["intent"] == "fiqh"
        assert result.metadata["collection"] == "test_collection"

    @pytest.mark.asyncio
    async def test_run_with_fallback_intent(self):
        """Test run with a non-matching query falls back to a general intent."""
        agent = ConcreteCollectionAgent()

        result = await agent.run(
            raw_question="غير معروف",
            meta={"language": "ar"},
        )

        assert result.metadata["intent"] == "islamic_knowledge"

    @pytest.mark.asyncio
    async def test_evidence_fallback_is_not_reported_as_answer(self):
        """Raw evidence text must be marked as evidence, not as an answer."""
        agent = _EvidenceFallbackAgent()

        result = await agent.run(
            raw_question="ما حكم الصيام؟",
            meta={"language": "ar"},
        )

        assert result.metadata["answer_mode"] == "evidence"
        assert result.requires_human_review is True
        assert any(issue.get("type") == "generation_fallback" for issue in result.metadata["verification_issues"])

    @pytest.mark.asyncio
    async def test_partial_filtering_is_not_reported_as_a_verification_issue(self):
        """Dropping some candidates is normal reranking, not a failed check."""
        agent = _PartialFilterAgent()

        result = await agent.run(
            raw_question="ما حكم الصيام؟",
            meta={"language": "ar"},
        )

        assert result.metadata["answer_mode"] == "answer"
        assert result.metadata["verification_confidence"] == 0.9
        assert not any(issue.get("type") == "evidence_filtered_out" for issue in result.metadata["verification_issues"])

    @pytest.mark.asyncio
    async def test_dropping_every_candidate_is_reported(self):
        """When verification rejects everything, the response says why."""
        agent = _DropsEveryCandidateAgent()

        result = await agent.run(
            raw_question="ما حكم الصيام؟",
            meta={"language": "ar"},
        )

        issues = result.metadata["verification_issues"]
        assert result.metadata["answer_mode"] == "abstain"
        assert any(issue.get("type") == "evidence_filtered_out" for issue in issues)
        assert any(issue.get("type") == "no_evidence_found" for issue in issues)


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
        assert citations[0].metadata["collection"] == "hadith"
        assert citations[0].book_title == "صحيح البخاري"
        assert citations[0].source_id == "C1"
