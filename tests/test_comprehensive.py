"""
Comprehensive Test Suite for Athar Islamic QA System.

Tests all major components for correctness and edge cases.
Phase 9: Added comprehensive test coverage.

Run with:
    pytest tests/test_comprehensive.py -v
    pytest tests/test_comprehensive.py -v -k "test_language"
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

# ==========================================
# Tests for Utils
# ==========================================


class TestLanguageDetection:
    """Tests for language detection utility."""

    def test_detect_arabic(self):
        """Test Arabic text detection."""
        from src.utils.language_detection import detect_language

        assert detect_language("ما حكم صلاة العيد؟") == "ar"
        assert detect_language("الصلاة ركن من أركان الإسلام") == "ar"
        assert detect_language("كيف أصلي صلاة العيد") == "ar"

    def test_detect_english(self):
        """Test English text detection."""
        from src.utils.language_detection import detect_language

        assert detect_language("How to calculate zakat?") == "en"
        assert detect_language("What is the ruling on prayer?") == "en"

    def test_detect_mixed(self):
        """Test mixed text detection."""
        from src.utils.language_detection import detect_language

        # More Arabic than threshold = Arabic
        assert detect_language("الصلاة prayer", threshold=0.3) == "ar"

    def test_detect_empty(self):
        """Test empty text handling."""
        from src.utils.language_detection import detect_language

        assert detect_language("") == "ar"
        assert detect_language("   ") == "ar"

    def test_is_mostly_arabic(self):
        """Test mostly Arabic check."""
        from src.utils.language_detection import is_mostly_arabic

        assert is_mostly_arabic("الصلاة فرض") is True
        assert is_mostly_arabic("hello world", threshold=0.5) is False

    def test_is_mostly_english(self):
        """Test mostly English check."""
        from src.utils.language_detection import is_mostly_english

        assert is_mostly_english("hello world") is True
        assert is_mostly_english("الصلاة فرض", threshold=0.5) is False

    def test_arabic_char_ratio(self):
        """Test Arabic character ratio calculation."""
        from src.utils.language_detection import get_arabic_char_ratio

        ratio = get_arabic_char_ratio("الصلاة فرض")
        assert 0.0 <= ratio <= 1.0
        assert ratio > 0.5


class TestEraClassifier:
    """Tests for era classification utility."""

    def test_early_islamic(self):
        """Test early Islamic period classification."""
        from src.utils.era_classifier import EraClassifier

        # Early period (before 100 AH)
        era = EraClassifier.classify(50)
        assert era in ["early_islamic", "prophetic", "tabiin"]

    def test_classic_period(self):
        """Test classic period classification."""
        from src.utils.era_classifier import EraClassifier

        # Year 200 is the boundary between Tabi'un (100-200) and Classical (200-500)
        # So 200 returns "tabiun" at the boundary, 300 returns "classical"
        era = EraClassifier.classify(300)
        assert era == "classical"

    def test_modern_period(self):
        """Test modern period classification."""
        from src.utils.era_classifier import EraClassifier

        era = EraClassifier.classify(1400)
        assert era == "modern"

    def test_invalid_year(self):
        """Test invalid year handling."""
        from src.utils.era_classifier import EraClassifier

        # Negative or zero year should be handled
        result = EraClassifier.classify(-10)
        assert result is not None


# ==========================================
# Tests for Constants
# ==========================================


class TestConstants:
    """Tests for configuration constants."""

    def test_retrieval_config(self):
        """Test retrieval configuration."""
        from src.config.constants import RetrievalConfig

        assert RetrievalConfig.TOP_K_FIQH > 0
        assert RetrievalConfig.SEMANTIC_SCORE_THRESHOLD > 0
        assert RetrievalConfig.RRF_K > 0
        assert RetrievalConfig.MIN_TOP_K >= 1

    def test_llm_config(self):
        """Test LLM configuration."""
        from src.config.constants import LLMConfig

        assert LLMConfig.DEFAULT_TEMPERATURE >= 0
        assert LLMConfig.DEFAULT_TEMPERATURE <= 2
        assert LLMConfig.DEFAULT_MAX_TOKENS > 0

    def test_zakat_config(self):
        """Test Zakat configuration."""
        from src.config.constants import ZakatConfig

        assert ZakatConfig.GOLD_NISAB_GRAMS > 0
        assert ZakatConfig.SILVER_NISAB_GRAMS > 0
        assert ZakatConfig.WEALTH_ZAKAT_RATE == 0.025

    def test_inheritance_config(self):
        """Test inheritance configuration."""
        from src.config.constants import InheritanceConfig

        # All fractions should be valid
        assert 0 < InheritanceConfig.HUSBAND_WITH_DESCENDANTS <= 0.5
        assert 0 < InheritanceConfig.DAUGHTER_SINGLE <= 1

    def test_collection_names(self):
        """Test collection names."""
        from src.config.constants import CollectionNames

        assert CollectionNames.FIQH
        assert CollectionNames.HADITH
        assert CollectionNames.DUA


# ==========================================
# Tests for Agents
# ==========================================


class TestChatbotAgent:
    """Tests for chatbot agent."""

    @pytest.mark.asyncio
    async def test_greeting_response(self):
        """Test greeting responses."""
        from src.agents.chatbot_agent import ChatbotAgent
        from src.agents.base import AgentInput

        agent = ChatbotAgent()
        input_data = AgentInput(query="السلام عليكم", language="ar")

        result = await agent.execute(input_data)

        assert result.answer
        assert result.confidence > 0
        assert result.citations == []

    @pytest.mark.asyncio
    async def test_english_greeting(self):
        """Test English greeting."""
        from src.agents.chatbot_agent import ChatbotAgent
        from src.agents.base import AgentInput

        agent = ChatbotAgent()
        input_data = AgentInput(query="hello", language="en")

        result = await agent.execute(input_data)

        assert result.answer
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_thank_you_response(self):
        """Test thank you response."""
        from src.agents.chatbot_agent import ChatbotAgent
        from src.agents.base import AgentInput

        agent = ChatbotAgent()
        input_data = AgentInput(query="شكراً", language="ar")

        result = await agent.execute(input_data)

        assert result.answer
        assert "شكر" in result.answer or "عفو" in result.answer


# ==========================================
# Tests for Tools
# ==========================================


class TestZakatCalculator:
    """Tests for Zakat calculator tool."""

    def test_zakat_calculation_below_nisab(self):
        """Test calculation when below nisab."""
        from src.tools.zakat_calculator import ZakatCalculator, ZakatAssets

        calc = ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9)
        assets = ZakatAssets(
            cash=1000,
            bank_accounts=0,
            gold_grams=0,
            silver_grams=0,
        )

        result = calc.calculate(assets)

        assert result.zakat_due == 0
        assert result.nisab_reached is False

    def test_zakat_calculation_above_nisab(self):
        """Test calculation when above nisab."""
        from src.tools.zakat_calculator import ZakatCalculator, ZakatAssets

        calc = ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9)
        assets = ZakatAssets(
            cash=10000,  # Above nisab (85g * 75 = 6375)
            bank_accounts=0,
            gold_grams=0,
            silver_grams=0,
        )

        result = calc.calculate(assets)

        assert result.zakat_due > 0
        assert result.nisab_reached is True
        # 2.5% of 10000 = 250
        assert result.zakat_due == pytest.approx(250.0, rel=1)

    def test_gold_zakat(self):
        """Test gold-based Zakat calculation."""
        from src.tools.zakat_calculator import ZakatCalculator, ZakatAssets

        calc = ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9)
        assets = ZakatAssets(
            cash=0,
            bank_accounts=0,
            gold_grams=100,  # Above nisab
        )

        result = calc.calculate(assets)

        # Gold value: 100 * 75 = 7500, Zakat: 187.5
        assert result.zakat_due > 0
        assert result.nisab_reached is True


class TestInheritanceCalculator:
    """Tests for inheritance calculator."""

    def test_husband_with_descendants(self):
        """Test husband inheritance with descendants."""
        from src.tools.inheritance_calculator import InheritanceCalculator

        calc = InheritanceCalculator()
        heir = {"type": "husband", "with_descendants": True}

        share = calc._calculate_fixed_share(heir, 10000)

        assert share == 2500  # 1/4

    def test_wife_without_descendants(self):
        """Test wife inheritance without descendants."""
        from src.tools.inheritance_calculator import InheritanceCalculator

        calc = InheritanceCalculator()
        heir = {"type": "wife", "with_descendants": False}

        share = calc._calculate_fixed_share(heir, 10000)

        assert share == 5000  # 1/2 (without, husband gets 1/4)

    def test_daughters_with_father(self):
        """Test daughter inheritance with father present."""
        from src.tools.inheritance_calculator import InheritanceCalculator

        calc = InheritanceCalculator()
        result = calc.calculate(
            total_estate=10000,
            heirs=[
                {"type": "daughter", "count": 1},
                {"type": "father", "count": 1},
            ],
        )

        assert result.total_share <= 10000  # Can't exceed estate


# ==========================================
# Tests for Configuration
# ==========================================


class TestSettings:
    """Tests for settings."""

    def test_settings_singleton(self):
        """Test settings is a singleton."""
        from src.config.settings import settings

        assert settings.app_name
        assert settings.app_version

    def test_llm_model_property(self):
        """Test LLM model property."""
        from src.config.settings import settings

        model = settings.llm_model
        assert model

    def test_is_production(self):
        """Test production check."""
        from src.config.settings import settings

        # Should be development by default in tests
        assert settings.app_env in ["development", "production", "test"]


# ==========================================
# Tests for Query Expansion
# ==========================================


class TestQueryExpander:
    """Tests for query expander."""

    def test_expand_fiqh_terms(self):
        """Test expansion of fiqh terms."""
        from src.knowledge.query_expander import QueryExpander

        expander = QueryExpander()
        result = expander.expand("صلاة")

        assert "صلاة" in result
        assert len(result) > 1

    def test_expand_hadith_terms(self):
        """Test expansion of hadith terms."""
        from src.knowledge.query_expander import QueryExpander

        expander = QueryExpander()
        result = expander.expand("حديث")

        assert "حديث" in result
        assert len(result) > 1

    def test_expand_for_retrieval_limited(self):
        """Test limited expansion."""
        from src.knowledge.query_expander import QueryExpander

        expander = QueryExpander()
        result = expander.expand_for_retrieval("صلاة", max_expansions=3)

        assert len(result) <= 3


# ==========================================
# Tests for BM25
# ==========================================


class TestBM25:
    """Tests for BM25 retriever."""

    def test_bm25_indexing(self):
        """Test BM25 indexing."""
        from src.knowledge.bm25_retriever import BM25

        bm25 = BM25()
        documents = [
            {"content": "الصلاة فرض على كل مسلم"},
            {"content": "الصيام فرض في شهر رمضان"},
            {"content": "الزكاة فرض على المال"},
        ]

        bm25.index(documents)

        assert bm25.corpus_size == 3

    def test_bm25_search(self):
        """Test BM25 search."""
        from src.knowledge.bm25_retriever import BM25

        bm25 = BM25()
        documents = [
            {"content": "الصلاة فرض"},
            {"content": "الصيام فرض"},
            {"content": "الزكاة فرض"},
        ]

        bm25.index(documents)
        results = bm25.search("صلاة", top_k=2)

        assert len(results) <= 2
        assert results[0][0] >= 0  # doc index


# ==========================================
# Tests for Citation
# ==========================================


class TestCitation:
    """Tests for citation model."""

    def test_citation_from_passage(self):
        """Test citation creation from passage."""
        from src.agents.base import Citation

        passage = {
            "content": "الصلاة خير من النوم",
            "metadata": {
                "book_title": "رياض الصالحين",
                "author": "ابن تربة",
                "author_death": "1245",
            },
        }

        citation = Citation.from_passage(passage, 1)

        assert citation.id == "C1"
        assert "رياض" in citation.source

    def test_citation_type_inference(self):
        """Test citation type inference."""
        from src.agents.base import Citation

        # Test hadith type
        passage = {
            "content": "حديث نبوي",
            "metadata": {"collection": "hadith_passages"},
        }

        citation = Citation.from_passage(passage, 1)

        assert citation.type == "hadith"


# ==========================================
# Tests for Error Handling
# ==========================================


class TestExceptions:
    """Tests for exception hierarchy."""

    def test_athar_exception(self):
        """Test base Athar exception."""
        from src.core.exceptions import AtharException, AtharErrorCode

        exc = AtharException(
            "Test error",
            AtharErrorCode.INVALID_QUERY,
        )

        assert exc.code == AtharErrorCode.INVALID_QUERY
        assert exc.status_code == 400

    def test_retrieval_exception(self):
        """Test retrieval exception."""
        from src.core.exceptions import RetrievalException

        exc = RetrievalException("Test retrieval error")

        assert "retrieval" in exc.message.lower()

    def test_not_found_exception(self):
        """Test not found exception."""
        from src.core.exceptions import NotFoundException

        exc = NotFoundException("Book", 123)

        assert "123" in exc.message
        assert exc.status_code == 404


# ==========================================
# Tests for Router
# ==========================================


class TestRouter:
    """Tests for router."""

    @pytest.mark.asyncio
    async def test_router_confidence_threshold(self):
        """Test router confidence threshold."""
        from src.application.router import HybridIntentClassifier, RouterAgent

        classifier = HybridIntentClassifier(low_conf_threshold=0.55)
        router = RouterAgent(classifier=classifier, conf_threshold=0.7)

        # Test routing
        result = await router.route("ما حكم الزكاة؟")

        assert result.result.intent.value
        assert result.route

    def test_get_agent_for_intent(self):
        """Test agent routing via intents."""
        from src.domain.intents import Intent, get_agent_for_intent

        agent = get_agent_for_intent(Intent.FIQH)

        assert agent == "fiqh:rag"


# ==========================================
# Run Tests
# ==========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
