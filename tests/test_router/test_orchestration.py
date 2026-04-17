# Tests for Router Orchestration
"""
Tests for:
- Orchestration plan creation
- Multi-agent routing
- Fallback behavior
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.application.router.orchestration import (
    OrchestrationPattern,
    AgentTask,
    OrchestrationPlan,
    create_orchestration_plan,
    MultiAgentOrchestrator,
    route_via_decision_tree,
    PRIMARY_THRESHOLD,
    SECONDARY_THRESHOLD,
    LOW_CONFIDENCE_THRESHOLD,
)
from src.domain.intents import Intent
from src.agents.base import AgentOutput, AgentInput


# ============================================================================
# Test: Orchestration Plan Creation
# ============================================================================


class TestOrchestrationPlanCreation:
    """Tests for create_orchestration_plan function."""

    def test_simple_query_sequential(self):
        """Test that simple queries create SEQUENTIAL plan with single task."""
        query = "ما حكم الصيام في شهر رمضان؟"
        intent = Intent.FIQH

        plan = create_orchestration_plan(query, intent)

        assert plan.pattern == OrchestrationPattern.SEQUENTIAL
        assert len(plan.tasks) == 1
        assert plan.primary_agent == "fiqh_agent"
        assert plan.fallback_agent == "general_islamic_agent"

    def test_simple_quran_query(self):
        """Test that Quran queries route to tafsir_agent."""
        query = "ما هي سورة الفاتحة؟"
        intent = Intent.QURAN

        plan = create_orchestration_plan(query, intent)

        assert plan.pattern == OrchestrationPattern.SEQUENTIAL
        assert plan.primary_agent == "tafsir_agent"

    def test_simple_hadith_query(self):
        """Test that Hadith queries route to hadith_agent."""
        query = "حديث عن الصبر"
        intent = Intent.HADITH

        plan = create_orchestration_plan(query, intent)

        assert plan.pattern == OrchestrationPattern.SEQUENTIAL
        assert plan.primary_agent == "hadith_agent"

    def test_complex_query_parallel(self):
        """Test that complex queries with multiple domains create PARALLEL plan."""
        query = "ما حكم قراءة القرآن مع الحديث في الصيام؟"
        intent = Intent.FIQH

        plan = create_orchestration_plan(query, intent)

        # Should detect multiple domains (Quran + Hadith keywords)
        assert plan.pattern == OrchestrationPattern.PARALLEL
        assert len(plan.tasks) >= 2  # Primary + at least one secondary

    def test_fallback_agent(self):
        """Test that fallback agent is always general_islamic_agent."""
        query = "ما هو الإسلام؟"
        intent = Intent.ISLAMIC_KNOWLEDGE

        plan = create_orchestration_plan(query, intent)

        assert plan.fallback_agent == "general_islamic_agent"


# ============================================================================
# Test: Agent Task Data Class
# ============================================================================


class TestAgentTask:
    """Tests for AgentTask dataclass."""

    def test_agent_task_creation(self):
        """Test creating an AgentTask."""
        task = AgentTask(
            agent_name="fiqh_agent",
            query="ما حكم الزكاة؟",
            priority=1,
            requires_verification=False,
        )

        assert task.agent_name == "fiqh_agent"
        assert task.query == "ما حكم الزكاة؟"
        assert task.priority == 1
        assert task.requires_verification is False

    def test_default_values(self):
        """Test default values for AgentTask."""
        task = AgentTask(
            agent_name="hadith_agent",
            query="حديث",
        )

        assert task.priority == 0
        assert task.requires_verification is False


# ============================================================================
# Test: Orchestration Plan Data Class
# ============================================================================


class TestOrchestrationPlan:
    """Tests for OrchestrationPlan dataclass."""

    def test_plan_creation(self):
        """Test creating an OrchestrationPlan."""
        tasks = [
            AgentTask(agent_name="fiqh_agent", query="test query"),
        ]
        plan = OrchestrationPlan(
            pattern=OrchestrationPattern.SEQUENTIAL,
            tasks=tasks,
            primary_agent="fiqh_agent",
            fallback_agent="general_islamic_agent",
        )

        assert plan.pattern == OrchestrationPattern.SEQUENTIAL
        assert len(plan.tasks) == 1
        assert plan.primary_agent == "fiqh_agent"
        assert plan.fallback_agent == "general_islamic_agent"


# ============================================================================
# Test: Multi-Agent Orchestrator
# ============================================================================


class TestMultiAgentOrchestrator:
    """Tests for MultiAgentOrchestrator class."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = AsyncMock()
        agent.execute = AsyncMock(
            return_value=AgentOutput(
                answer="Test answer",
                citations=[],
                metadata={"agent_name": "test_agent"},
                confidence=0.8,
            )
        )
        return agent

    @pytest.fixture
    def orchestrator(self, mock_agent):
        """Create orchestrator with mock agent registry."""
        return MultiAgentOrchestrator(
            agent_registry={
                "fiqh_agent": mock_agent,
                "general_islamic_agent": mock_agent,
                "chatbot_agent": mock_agent,
            }
        )

    @pytest.mark.asyncio
    async def test_execute_sequential_plan(self, orchestrator, mock_agent):
        """Test executing a SEQUENTIAL plan."""
        plan = OrchestrationPlan(
            pattern=OrchestrationPattern.SEQUENTIAL,
            tasks=[
                AgentTask(agent_name="fiqh_agent", query="ما حكم الصيام؟"),
            ],
            primary_agent="fiqh_agent",
        )

        result = await orchestrator.execute_plan(plan, "ما حكم الصيام؟")

        assert result.answer == "Test answer"
        assert result.confidence == 0.8
        mock_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_parallel_plan(self, orchestrator, mock_agent):
        """Test executing a PARALLEL plan with multiple tasks."""
        plan = OrchestrationPlan(
            pattern=OrchestrationPattern.PARALLEL,
            tasks=[
                AgentTask(agent_name="fiqh_agent", query="ما حكم الصيام؟"),
                AgentTask(agent_name="hadith_agent", query="حديث عن الصيام"),
            ],
            primary_agent="fiqh_agent",
        )

        result = await orchestrator.execute_plan(plan, "ما حكم الصيام؟")

        # Should aggregate results from multiple agents
        assert "Test answer" in result.answer
        assert result.metadata.get("orchestration") == "parallel"
        assert result.metadata.get("num_agents") >= 1

    @pytest.mark.asyncio
    async def test_fallback_on_low_confidence(self, orchestrator):
        """Test that low confidence triggers fallback."""
        # Create a mock agent that returns low confidence
        low_conf_agent = AsyncMock()
        low_conf_agent.execute = AsyncMock(
            return_value=AgentOutput(
                answer="",
                citations=[],
                metadata={},
                confidence=0.1,  # Below LOW_CONFIDENCE_THRESHOLD
            )
        )

        orchestrator.register_agent("fiqh_agent", low_conf_agent)

        plan = OrchestrationPlan(
            pattern=OrchestrationPattern.SEQUENTIAL,
            tasks=[
                AgentTask(agent_name="fiqh_agent", query="test"),
            ],
            primary_agent="fiqh_agent",
        )

        result = await orchestrator.execute_plan(plan, "test")

        # Should route to fallback
        assert result.metadata.get("fallback_used") is True

    @pytest.mark.asyncio
    async def test_route_to_fallback(self, orchestrator):
        """Test fallback routing."""
        result = await orchestrator.route_to_fallback("test query")

        # Should return output from fallback agent
        assert result.metadata.get("fallback_used") is True

    @pytest.mark.asyncio
    async def test_agent_not_found(self, orchestrator):
        """Test handling when agent not in registry."""
        plan = OrchestrationPlan(
            pattern=OrchestrationPattern.SEQUENTIAL,
            tasks=[
                AgentTask(agent_name="nonexistent_agent", query="test"),
            ],
            primary_agent="nonexistent_agent",
        )

        result = await orchestrator.execute_plan(plan, "test")

        # Should handle gracefully - falls through to fallback
        # When agent not found, confidence drops below threshold and triggers fallback
        # Fallback returns result from general_islamic_agent
        assert result.metadata.get("fallback_used") is True


# ============================================================================
# Test: Decision Tree Routing
# ============================================================================


class TestDecisionTreeRouting:
    """Tests for route_via_decision_tree function."""

    def test_hadith_keyword_routes_to_hadith_agent(self):
        """Test that 'حديث' keyword routes to hadith_agent."""
        assert route_via_decision_tree("حديث عن الصبر") == "hadith_agent"
        assert route_via_decision_tree("ما صحة هذا الحديث") == "hadith_agent"

    def test_quran_keyword_routes_to_tafsir_agent(self):
        """Test that Quran keywords route to tafsir_agent."""
        assert route_via_decision_tree("آية عن الصبر") == "tafsir_agent"
        assert route_via_decision_tree("سورة الفاتحة") == "tafsir_agent"
        assert route_via_decision_tree("قرآن كريم") == "tafsir_agent"

    def test_tafsir_keyword_routes_to_tafsir_agent(self):
        """Test that 'تفسير' keyword routes to tafsir_agent."""
        assert route_via_decision_tree("تفسير سورة البقرة") == "tafsir_agent"

    def test_aqeedah_keyword_routes_to_aqeedah_agent(self):
        """Test that aqeedah keywords route to aqeedah_agent."""
        assert route_via_decision_tree("ما هي العقيدة") == "aqeedah_agent"
        assert route_via_decision_tree("توحيد الله") == "aqeedah_agent"

    def test_seerah_keyword_routes_to_seerah_agent(self):
        """Test that seerah keywords route to seerah_agent."""
        assert route_via_decision_tree("السيرة النبوية") == "seerah_agent"
        assert route_via_decision_tree("غزوة بدر") == "seerah_agent"

    def test_fiqh_keyword_routes_to_fiqh_agent(self):
        """Test that fiqh keywords route to fiqh_agent."""
        assert route_via_decision_tree("ما حكم الصيام") == "fiqh_agent"
        assert route_via_decision_tree("هل يجوز") == "fiqh_agent"

    def test_unknown_query_fallback(self):
        """Test that unknown queries fallback to general_islamic_agent."""
        assert route_via_decision_tree("ما هو الفرق") == "general_islamic_agent"
        assert route_via_decision_tree("random text") == "general_islamic_agent"


# ============================================================================
# Test: Threshold Constants
# ============================================================================


class TestThresholds:
    """Tests for threshold constants."""

    def test_threshold_values(self):
        """Test that thresholds are properly defined."""
        assert PRIMARY_THRESHOLD == 0.7
        assert SECONDARY_THRESHOLD == 0.4
        assert LOW_CONFIDENCE_THRESHOLD == 0.2

        # Verify ordering
        assert PRIMARY_THRESHOLD > SECONDARY_THRESHOLD > LOW_CONFIDENCE_THRESHOLD


# ============================================================================
# Test: Orchestration Pattern Enum
# ============================================================================


class TestOrchestrationPattern:
    """Tests for OrchestrationPattern enum."""

    def test_pattern_values(self):
        """Test enum values."""
        assert OrchestrationPattern.SEQUENTIAL.value == "sequential"
        assert OrchestrationPattern.PARALLEL.value == "parallel"
        assert OrchestrationPattern.HIERARCHICAL.value == "hierarchical"


# ============================================================================
# Test: Multi-Agent Router
# ============================================================================


class TestMultiAgentRouter:
    """Tests for MultiAgentRouter class (if imported separately)."""

    def test_import_multi_agent_router(self):
        """Test that MultiAgentRouter can be imported."""
        from src.application.router.multi_agent import MultiAgentRouter

        assert MultiAgentRouter is not None

    def test_import_create_multi_agent_router(self):
        """Test that create_multi_agent_router can be imported."""
        from src.application.router.multi_agent import create_multi_agent_router

        assert create_multi_agent_router is not None
