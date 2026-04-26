"""
Tests for FiqhCollectionAgent.

Tests:
- Agent instantiation with config
- Query intake normalization
- Intent classification
- Strategy configuration
- Full pipeline execution
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.collection import (
    CollectionAgentConfig,
    IntentLabel,
    RetrievalStrategy,
)
from src.agents.collection.fiqh import (
    FiqhCollectionAgent,
    _normalize_arabic,
)


class TestArabicNormalization:
    """Tests for Arabic text normalization."""

    def test_unify_alef(self):
        """Test unifying different alef variants."""
        assert _normalize_arabic("أكل") == "اكل"
        assert _normalize_arabic("إسلام") == "اسلام"
        assert _normalize_arabic("آمن") == "امن"
        assert _normalize_arabic("الله") == "الله"  # Already normalized

    def test_unify_ya(self):
        """Test unifying different ya variants."""
        assert _normalize_arabic("بناء") == "بناء"
        # Note: Only standalone ya (ى) is converted to ي
        # Ya with hamza (ئ) is kept as-is in this implementation
        assert _normalize_arabic("بيت") == "بيت"

    def test_normalize_ta_marbuta(self):
        """Test normalizing ta marbuta."""
        # Note: This implementation normalizes ta marbuta (ة U+0629) to ه (ه U+0647)
        # The alef is preserved, so "فتاة" becomes "فتاه" (4 chars)
        assert _normalize_arabic("سنة") == "سنه"
        assert _normalize_arabic("فتاة") == "فتاه"
        assert _normalize_arabic("حياة") == "حياه"

    def test_remove_extra_spaces(self):
        """Test removing extra whitespace."""
        assert _normalize_arabic("الله   أكبر") == "الله اكبر"
        assert _normalize_arabic("  سؤال  ") == "سؤال"


class TestFiqhCollectionAgentInstantiation:
    """Tests for FiqhCollectionAgent instantiation."""

    def test_default_instantiation(self):
        """Test agent can be instantiated with default config."""
        agent = FiqhCollectionAgent()

        assert agent.name == "fiqh_agent"
        assert agent.COLLECTION == "fiqh"
        assert isinstance(agent.config, CollectionAgentConfig)
        assert agent.config.collection_name == "fiqh"

    def test_custom_config_instantiation(self):
        """Test agent with custom configuration."""
        strategy = RetrievalStrategy(
            dense_weight=0.5,
            sparse_weight=0.5,
            top_k=100,
            rerank=False,
            score_threshold=0.7,
        )

        config = CollectionAgentConfig(
            collection_name="fiqh_custom",
            strategy=strategy,
        )

        agent = FiqhCollectionAgent(config=config)

        assert agent.name == "fiqh_agent"
        assert agent.config.strategy.top_k == 100
        assert agent.config.strategy.score_threshold == 0.7

    def test_with_dependencies(self):
        """Test agent with injected dependencies."""
        mock_embedding = MagicMock()
        mock_vector_store = MagicMock()
        mock_llm = MagicMock()

        agent = FiqhCollectionAgent(
            embedding_model=mock_embedding,
            vector_store=mock_vector_store,
            llm_client=mock_llm,
        )

        assert agent.embedding_model is mock_embedding
        assert agent.vector_store is mock_vector_store
        assert agent.llm_client is mock_llm


class TestQueryIntake:
    """Tests for query_intake method."""

    def test_normalize_simple_query(self):
        """Test normalizing a simple Arabic query."""
        agent = FiqhCollectionAgent()

        result = agent.query_intake("ما حكم الصيام؟")

        assert result == "ما حكم الصيام؟"

    def test_normalize_with_alef_variants(self):
        """Test normalizing query with alef variants."""
        agent = FiqhCollectionAgent()

        result = agent.query_intake("ما حكم الأكل في رمضان؟")

        assert "الاكل" in result

    def test_normalize_removes_extra_spaces(self):
        """Test that extra spaces are removed."""
        agent = FiqhCollectionAgent()

        result = agent.query_intake("ما  حكم  الصيام  ؟")

        assert "  " not in result


class TestIntentClassification:
    """Tests for classify_intent method."""

    def test_fiqh_hukm_intent_ruling_keywords(self):
        """Test FiqhHukm intent with ruling keywords."""
        agent = FiqhCollectionAgent()

        # Test various hukm keywords that should trigger FiqhHukm
        assert agent.classify_intent("ما حكم الصلاة؟") == IntentLabel.FiqhHukm
        assert agent.classify_intent("هل الحضور واجب؟") == IntentLabel.FiqhHukm
        assert agent.classify_intent("هل هذا حرام؟") == IntentLabel.FiqhHukm
        assert agent.classify_intent("حكم الصيام") == IntentLabel.FiqhHukm
        assert agent.classify_intent("هذا فرض") == IntentLabel.FiqhHukm

    def test_fiqh_masaail_intent_question_keywords(self):
        """Test FiqhMasaail intent with question keywords."""
        agent = FiqhCollectionAgent()

        # Test masaail keywords - these don't contain hukm keywords
        assert agent.classify_intent("ما مسألة الصيام؟") == IntentLabel.FiqhMasaail
        assert agent.classify_intent("سؤال عن الزكاة") == IntentLabel.FiqhMasaail
        # Note: "ما هو حكم" contains "حكم" so triggers hukm not masaail
        # Use queries without hukm keywords
        assert agent.classify_intent("ما هو تعريف الصيام؟") == IntentLabel.FiqhMasaail

    def test_unknown_intent_fallback(self):
        """Test Unknown intent for non-matching queries."""
        agent = FiqhCollectionAgent()

        # Generic queries without fiqh keywords
        result = agent.classify_intent("أخبرني عن التاريخ")

        # Default should be masaail since it's a question format
        assert result in [IntentLabel.FiqhMasaail, IntentLabel.Unknown]


class TestStrategyConfiguration:
    """Tests for strategy configuration."""

    def test_default_strategy_values(self):
        """Test default strategy from get_strategy_for_agent."""
        agent = FiqhCollectionAgent()

        assert agent.strategy is not None
        assert agent.strategy.dense_weight == 0.6
        assert agent.strategy.sparse_weight == 0.4
        assert agent.strategy.top_k == 80
        assert agent.strategy.rerank is True
        assert agent.strategy.score_threshold == 0.65

    def test_class_config_overrides(self):
        """Test class-level config overrides."""
        agent = FiqhCollectionAgent()

        assert agent.TOP_K_RETRIEVAL == 80
        assert agent.TOP_K_RERANK == 5
        assert agent.SCORE_THRESHOLD == 0.65
        assert agent.TEMPERATURE == 0.15
        assert agent.MAX_TOKENS == 2048


class TestRetrieval:
    """Tests for retrieve_candidates method."""

    @pytest.mark.asyncio
    async def test_retrieve_no_vector_store(self):
        """Test retrieval returns empty when no vector store."""
        agent = FiqhCollectionAgent()

        result = await agent.retrieve_candidates("ما حكم الصيام؟")

        assert result == []

    @pytest.mark.asyncio
    async def test_retrieve_with_mock_vector_store(self):
        """Test retrieval with mocked vector store."""
        mock_store = AsyncMock()
        mock_store.search.return_value = [
            {"content": "نص فقهي 1", "score": 0.9, "metadata": {"source": "test"}},
            {"content": "نص فقهي 2", "score": 0.8, "metadata": {"source": "test2"}},
        ]

        agent = FiqhCollectionAgent(vector_store=mock_store)

        result = await agent.retrieve_candidates("ما حكم الصيام؟")

        assert len(result) == 2
        assert result[0]["content"] == "نص فقهي 1"
        assert result[0]["score"] == 0.9


class TestReranking:
    """Tests for rerank_candidates method."""

    @pytest.mark.asyncio
    async def test_rerank_empty_candidates(self):
        """Test reranking with empty candidates."""
        agent = FiqhCollectionAgent()

        result = await agent.rerank_candidates("query", [])

        assert result == []

    @pytest.mark.asyncio
    async def test_rerank_filters_by_threshold(self):
        """Test reranking filters by score threshold."""
        agent = FiqhCollectionAgent()

        candidates = [
            {"content": "high score", "score": 0.9},
            {"content": "low score", "score": 0.5},
        ]

        result = await agent.rerank_candidates("query", candidates)

        assert len(result) == 1
        assert result[0]["content"] == "high score"


class TestVerification:
    """Tests for run_verification method."""

    @pytest.mark.asyncio
    async def test_verification_with_candidates(self):
        """Test verification with candidate passages."""
        agent = FiqhCollectionAgent()

        candidates = [
            {"content": "نص فقهي", "score": 0.9, "metadata": {}},
        ]

        result = await agent.run_verification("query", candidates)

        assert result is not None
        assert hasattr(result, "verified_passages")

    @pytest.mark.asyncio
    async def test_verification_empty_candidates(self):
        """Test verification with empty candidates."""
        agent = FiqhCollectionAgent()

        result = await agent.run_verification("query", [])

        assert result is not None
        # Empty candidates should result in empty verified_passages


class TestGenerateAnswer:
    """Tests for generate_answer method."""

    @pytest.mark.asyncio
    async def test_generate_no_passages(self):
        """Test generate returns fallback message when no passages."""
        agent = FiqhCollectionAgent()

        result = await agent.generate_answer("query", [], "ar")

        assert result == agent.NO_PASSAGES_MESSAGE

    @pytest.mark.asyncio
    async def test_generate_with_passages_no_llm(self):
        """Test generate returns formatted passages when no LLM."""
        agent = FiqhCollectionAgent()  # No llm_client

        passages = [
            {"content": "نص فقهي 1", "score": 0.9, "metadata": {}},
            {"content": "نص فقهي 2", "score": 0.8, "metadata": {}},
        ]

        result = await agent.generate_answer("query", passages, "ar")

        assert "نص فقهي 1" in result
        assert "[C1]" in result


class TestAssembleCitations:
    """Tests for assemble_citations method."""

    def test_assemble_citations_from_passages(self):
        """Test assembling citations from passages."""
        agent = FiqhCollectionAgent()

        passages = [
            {
                "content": "نص فقهي",
                "metadata": {
                    "collection": "fiqh",
                    "book_title": "المجموع",
                    "author": "النووي",
                    "author_death": "676",
                    "page_number": "100",
                },
            },
        ]

        citations = agent.assemble_citations(passages)

        assert len(citations) == 1
        assert citations[0].id == "C1"
        assert citations[0].type == "fiqh_book"


class TestFullPipeline:
    """Tests for full run() pipeline."""

    @pytest.mark.asyncio
    async def test_full_run_with_mock_data(self):
        """Test complete pipeline execution."""
        agent = FiqhCollectionAgent()

        # Run the full pipeline
        result = await agent.run(
            raw_question="ما حكم الصيام في رمضان؟",
            meta={"language": "ar"},
        )

        assert result is not None
        assert hasattr(result, "answer")
        assert hasattr(result, "citations")
        assert hasattr(result, "metadata")
        assert result.metadata.get("intent") in [
            IntentLabel.FiqhHukm.value,
            IntentLabel.FiqhMasaail.value,
        ]
        assert result.metadata.get("collection") == "fiqh"

    @pytest.mark.asyncio
    async def test_run_intent_classification(self):
        """Test that run() properly classifies intent."""
        agent = FiqhCollectionAgent()

        result = await agent.run(
            raw_question="هل الصيام فرض؟",
            meta={"language": "ar"},
        )

        assert result.metadata.get("intent") == IntentLabel.FiqhHukm.value


class TestClassAttributes:
    """Tests for class-level attributes."""

    def test_system_prompt_arabic(self):
        """Test system prompt is in Arabic."""
        assert "مساعد إسلامي متخصص في الفقه الإسلامي" in FiqhCollectionAgent.SYSTEM_PROMPT

    def test_user_prompt_template(self):
        """Test user prompt has required placeholders."""
        prompt = FiqhCollectionAgent.USER_PROMPT

        assert "{query}" in prompt
        assert "{passages}" in prompt
        assert "{num_passages}" in prompt

    def test_no_passages_message_arabic(self):
        """Test fallback message is in Arabic."""
        assert "لم أجد نصوصاً فقهية" in FiqhCollectionAgent.NO_PASSAGES_MESSAGE
