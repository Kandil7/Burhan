"""
Comprehensive Test Suite for Burhan Islamic QA System.

Tests all major components for correctness and edge cases.
Phase 9: Added comprehensive test coverage.

Run with:
    pytest tests/test_comprehensive.py -v
    pytest tests/test_comprehensive.py -v -k "test_language"
"""

import pytest

# ==========================================
# Tests for Utils
# ==========================================


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
        from src.agents.base import AgentInput
        from src.agents.chatbot_agent import ChatbotAgent  # Keep - this is v1 but used in tests

        agent = ChatbotAgent()
        input_data = AgentInput(query="السلام عليكم", language="ar")

        result = await agent.execute(input_data)

        assert result.answer
        assert result.confidence > 0
        assert result.citations == []

    @pytest.mark.asyncio
    async def test_english_greeting(self):
        """Test English greeting."""
        from src.agents.base import AgentInput
        from src.agents.chatbot_agent import ChatbotAgent  # Keep - this is v1 but used in tests

        agent = ChatbotAgent()
        input_data = AgentInput(query="hello", language="en")

        result = await agent.execute(input_data)

        assert result.answer
        assert result.confidence > 0

    @pytest.mark.asyncio
    async def test_thank_you_response(self):
        """Test thank you response."""
        from src.agents.base import AgentInput
        from src.agents.chatbot_agent import ChatbotAgent  # Keep - this is v1 but used in tests

        agent = ChatbotAgent()
        input_data = AgentInput(query="شكراً", language="ar")

        result = await agent.execute(input_data)

        assert result.answer
        # A thank-you must be acknowledged as such, regardless of exact wording.
        assert result.metadata.get("type") == "thanks"


# ==========================================
# Tests for Tools
# ==========================================


class TestZakatCalculator:
    """Tests for Zakat calculator tool."""

    def test_zakat_calculation_below_nisab(self):
        """Test calculation when below nisab."""
        from src.tools.zakat_calculator import ZakatAssets, ZakatCalculator

        calc = ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9)
        # Silver nisab is 595g * 0.9 = 535.5, so 500 is below the threshold.
        assets = ZakatAssets(cash=500)

        result = calc.calculate(assets)

        assert result.zakat_amount == 0
        assert result.is_zakatable is False

    def test_zakat_calculation_above_nisab(self):
        """Test calculation when above nisab."""
        from src.tools.zakat_calculator import ZakatAssets, ZakatCalculator

        calc = ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9)
        assets = ZakatAssets(cash=10000)  # Above nisab

        result = calc.calculate(assets)

        assert result.zakat_amount > 0
        assert result.is_zakatable is True
        # 2.5% of 10000 = 250
        assert result.zakat_amount == pytest.approx(250.0, rel=1)

    def test_gold_zakat(self):
        """Test gold-based Zakat calculation."""
        from src.tools.zakat_calculator import ZakatAssets, ZakatCalculator

        calc = ZakatCalculator(gold_price_per_gram=75.0, silver_price_per_gram=0.9)
        assets = ZakatAssets(gold_grams=100)  # Above nisab

        result = calc.calculate(assets)

        # Gold value: 100 * 75 = 7500, Zakat: 187.5
        assert result.zakat_amount == pytest.approx(187.5, rel=1)
        assert result.is_zakatable is True


class TestInheritanceCalculator:
    """Tests for inheritance calculator."""

    def test_husband_with_descendants(self):
        """Test husband inheritance with descendants."""
        from src.tools.inheritance_calculator import Heirs, InheritanceCalculator

        calc = InheritanceCalculator()
        result = calc.calculate(10000, Heirs(husband=True, sons=1))

        husband = next(s for s in result.distribution if s.heir_name == "Husband")
        assert husband.amount == 2500  # 1/4
        assert float(husband.fraction) == 0.25

    def test_wife_without_descendants(self):
        """Test wife inheritance without descendants."""
        from src.tools.inheritance_calculator import Heirs, InheritanceCalculator

        calc = InheritanceCalculator()
        # With a residuary heir present so the fard share is not absorbed by radd.
        result = calc.calculate(10000, Heirs(wife_count=1, father=True))

        wife = next(s for s in result.distribution if s.heir_name.startswith("Wife"))
        assert wife.amount == 2500  # 1/4 without descendants
        assert float(wife.fraction) == 0.25

    def test_daughters_with_father(self):
        """Test daughter inheritance with father present."""
        from src.tools.inheritance_calculator import Heirs, InheritanceCalculator

        calc = InheritanceCalculator()
        result = calc.calculate(10000, Heirs(daughters=1, father=True))

        daughter = next(s for s in result.distribution if s.heir_name == "Daughter")
        assert daughter.amount == 5000  # 1/2 fard
        assert result.total_distributed <= 10000  # Can't exceed estate


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


# ==========================================
# Tests for BM25
# ==========================================


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

        assert citation.source_id == "C1"
        assert "رياض" in citation.book_title

    def test_citation_type_inference(self):
        """Test that the collection is preserved for type inference."""
        from src.application.services.citation_service import citation_from_raw

        raw = {
            "source_id": "C1",
            "text": "حديث نبوي",
            "metadata": {"collection": "hadith_passages"},
        }

        citation = citation_from_raw(raw)

        assert citation.collection == "hadith_passages"


# ==========================================
# Tests for Error Handling
# ==========================================


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

        assert agent == "fiqh_agent"


# ==========================================
# Run Tests
# ==========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
