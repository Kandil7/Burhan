"""
Integration test for Config-Backed Agent System

Tests the complete flow from config loading to routing to orchestration.
"""

import pytest

from src.agents.collection import RetrievalStrategy
from src.application.router.config_router import ConfigRouter
from src.application.router.orchestration import (
    OrchestrationPattern,
    create_orchestration_plan,
    route_via_decision_tree,
)
from src.config import get_config_manager
from src.config.loader import get_all_agent_configs, load_agent_config


class TestConfigLoader:
    """Test config loading functionality."""

    def test_list_all_agents(self):
        """Test that all 10 agents are available."""
        agents = get_all_agent_configs()
        assert len(agents) == 10
        assert "fiqh" in agents
        assert "hadith" in agents
        assert "tafsir" in agents

    def test_load_fiqh_config(self):
        """Test loading Fiqh agent config."""
        config = load_agent_config("fiqh")
        assert config["name"] == "FiqhAgent"
        assert config["domain"] == "fiqh"
        assert config["collection_name"] == "fiqh_passages"

    def test_load_hadith_config(self):
        """Test loading Hadith agent config."""
        config = load_agent_config("hadith")
        assert config["name"] == "HadithAgent"
        assert config["retrieval"]["primary"] == "hybrid"

    def test_load_system_prompts(self):
        """Test that system prompts are loaded."""
        config = load_agent_config("fiqh", load_prompts=True)
        assert "system_prompt" in config
        assert len(config["system_prompt"]) > 100


class TestConfigManager:
    """Test AgentConfigManager."""

    def test_config_manager_singleton(self):
        """Test that config manager is a singleton."""
        cm1 = get_config_manager()
        cm2 = get_config_manager()
        assert cm1 is cm2

    def test_get_collection_agent_config(self):
        """Test converting YAML config to CollectionAgentConfig."""
        cm = get_config_manager()
        config = cm.get_collection_agent_config("fiqh", include_prompt=False)

        assert config.collection_name == "fiqh_passages"
        assert isinstance(config.strategy, RetrievalStrategy)
        assert config.strategy.dense_weight == 0.6
        assert len(config.verification_suite.checks) == 4

    def test_all_agents_have_configs(self):
        """Test that all 10 agents can be loaded."""
        cm = get_config_manager()
        agents = cm.list_available_agents()

        for agent in agents:
            config = cm.load_config(agent)
            assert config.name is not None
            assert config.domain is not None


class TestConfigRouter:
    """Test ConfigRouter with keyword-based routing."""

    def test_fiqh_routing(self):
        """Test routing for Fiqh queries."""
        router = ConfigRouter()
        result = router.route("ما حكم صلاة الجماعة في المسجد؟")
        assert result.agent_name == "fiqh_agent"

    def test_hadith_routing(self):
        """Test routing for Hadith queries."""
        router = ConfigRouter()
        result = router.route("حدثني عن حديث صحيح البخاري")
        assert result.agent_name == "hadith_agent"

    def test_tafsir_routing(self):
        """Test routing for Tafsir queries."""
        router = ConfigRouter()
        result = router.route("ما تفسير آية الكرسي؟")
        assert result.agent_name == "tafsir_agent"

    def test_aqeedah_routing(self):
        """Test routing for Aqeedah queries."""
        router = ConfigRouter()
        result = router.route("ما هي عقيدة أهل السنة؟")
        assert result.agent_name == "aqeedah_agent"

    def test_seerah_routing(self):
        """Test routing for Seerah queries."""
        router = ConfigRouter()
        result = router.route("ما سبب غزوة بدر الكبرى؟")
        assert result.agent_name == "seerah_agent"

    def test_usul_fiqh_routing(self):
        """Test routing for Usul Fiqh queries."""
        router = ConfigRouter()
        result = router.route("ما هو القياس في أصول الفقه؟")
        assert result.agent_name == "usul_fiqh_agent"

    def test_history_routing(self):
        """Test routing for History queries."""
        router = ConfigRouter()
        result = router.route("متى كانت الدولة الأموية؟")
        assert result.agent_name == "history_agent"

    def test_language_routing(self):
        """Test routing for Language queries."""
        router = ConfigRouter()
        result = router.route("ما إعراب كلمة الله؟")
        assert result.agent_name == "language_agent"

    def test_tazkiyah_routing(self):
        """Test routing for Tazkiyah queries."""
        router = ConfigRouter()
        result = router.route("كيف أتحقق من صفة الإخلاص؟")
        assert result.agent_name == "tazkiyah_agent"

    def test_general_fallback(self):
        """Test fallback to general agent for unknown queries."""
        router = ConfigRouter()
        result = router.route("مرحبا كيف حالك؟")
        assert result.agent_name == "general_islamic_agent"

    def test_multi_routing(self):
        """Test multi-agent routing for complex queries."""
        router = ConfigRouter()
        results = router.route_multi("ما حكم الصلاة وما صحة هذا الحديث؟")
        assert len(results) >= 1
        assert results[0].agent_name in ["fiqh_agent", "hadith_agent"]


class TestOrchestrationIntegration:
    """Test integration between config router and orchestration."""

    def test_decision_tree_routing(self):
        """Test decision tree routing function."""
        # Test known patterns
        assert route_via_decision_tree("ما حكم الصيام؟") == "fiqh_agent"
        assert route_via_decision_tree("حديث عن الصبر") == "hadith_agent"
        assert route_via_decision_tree("تفسير سورة البقرة") == "tafsir_agent"

    def test_orchestration_plan_creation(self):
        """Test creating orchestration plans."""
        from src.domain.intents import Intent

        # Create plan for simple query
        plan = create_orchestration_plan("ما حكم الصلاة؟", Intent.FIQH)
        assert plan.primary_agent == "fiqh_agent"
        assert plan.pattern == OrchestrationPattern.SEQUENTIAL


class TestRetrievalStrategyMapping:
    """Test retrieval strategy mapping."""

    def test_fiqh_strategy(self):
        """Test Fiqh retrieval strategy."""
        cm = get_config_manager()
        config = cm.get_collection_agent_config("fiqh", include_prompt=False)

        assert config.strategy.dense_weight == 0.6
        assert config.strategy.sparse_weight == 0.4

    def test_hadith_strategy(self):
        """Test Hadith retrieval strategy."""
        cm = get_config_manager()
        config = cm.get_collection_agent_config("hadith", include_prompt=False)

        assert config.strategy.dense_weight == 0.3
        assert config.strategy.sparse_weight == 0.7

    def test_tafsir_strategy(self):
        """Test Tafsir retrieval strategy."""
        cm = get_config_manager()
        config = cm.get_collection_agent_config("tafsir", include_prompt=False)

        assert config.strategy.dense_weight == 0.7
        # Use pytest.approx for floating point comparison
        assert config.strategy.sparse_weight == pytest.approx(0.3, rel=0.01)


class TestVerificationSuiteMapping:
    """Test verification suite mapping."""

    def test_fiqh_verification(self):
        """Test Fiqh verification checks."""
        cm = get_config_manager()
        config = cm.get_collection_agent_config("fiqh", include_prompt=False)

        checks = config.verification_suite.checks
        assert len(checks) == 4
        check_names = [c.name for c in checks]
        assert "quote_validator" in check_names
        assert "source_attributor" in check_names

    def test_aqeedah_strict_verification(self):
        """Test Aqeedah has stricter verification."""
        cm = get_config_manager()
        config = cm.get_collection_agent_config("aqeedah", include_prompt=False)

        # Aqeedah should have abstain for source_attributor
        checks = config.verification_suite.checks
        source_check = next((c for c in checks if c.name == "source_attributor"), None)
        assert source_check is not None
        assert source_check.fail_policy == "abstain"


class TestFallbackPolicy:
    """Test fallback policy configuration."""

    def test_fiqh_fallback(self):
        """Test Fiqh fallback policy."""
        cm = get_config_manager()
        config = cm.get_collection_agent_config("fiqh", include_prompt=False)

        assert config.fallback_policy.strategy == "chatbot"

    def test_aqeedah_human_review(self):
        """Test Aqeedah has human review fallback."""
        cm = get_config_manager()
        config = cm.get_collection_agent_config("aqeedah", include_prompt=False)

        assert config.fallback_policy.strategy == "human_review"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
