"""
Config module for loading and managing agent configurations.

This module provides:
- AgentConfigManager: Class for loading and managing all agent configs
- Config-backed CollectionAgent implementations
- Factory functions for creating agents from config files

Usage:
    from src.config import AgentConfigManager

    manager = AgentConfigManager()
    fiqh_config = manager.get_config("fiqh")
    fiqh_agent = manager.create_agent("fiqh")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from src.agents.collection.base import (
    CollectionAgent,
    CollectionAgentConfig,
    FallbackPolicy,
    RetrievalStrategy,
    VerificationCheck,
    VerificationSuite,
)
from src.agents.base import AgentOutput
from src.config.settings import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Config Paths
# ============================================================================

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config" / "agents"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# ============================================================================
# Config Data Models (mirroring YAML structure)
# ============================================================================


class RetrievalConfig(BaseModel):
    """Retrieval configuration from YAML."""

    primary: str = "hybrid"
    alpha: float = 0.6
    topk_initial: int = 50
    topk_reranked: int = 12
    min_relevance: float = 0.5
    metadata_filters_priority: list[str] = Field(default_factory=list)


class VerificationCheckConfig(BaseModel):
    """Verification check configuration from YAML."""

    name: str
    enabled: bool = True
    fail_policy: str = "abstain"


class VerificationConfig(BaseModel):
    """Verification configuration from YAML."""

    fail_fast: bool = True
    checks: list[VerificationCheckConfig] = Field(default_factory=list)


class FallbackConfig(BaseModel):
    """Fallback configuration from YAML."""

    strategy: str = "chatbot"
    message: Optional[str] = None


class AbstentionConfig(BaseModel):
    """Abstention rules configuration from YAML."""

    high_risk_personal_fatwa: bool = False
    require_diverse_evidence: bool = False
    minimum_sources: int = 1
    # Additional agent-specific fields
    require_sahih_for_aqeedah_and_ahkam: bool = False
    allow_daif_for_fadail_with_warning: bool = False
    require_authentic_sources: bool = False
    require_sahih_evidence_only: bool = False
    block_kufr_tafreet_statements: bool = False
    block_extreme_statements: bool = False
    require_balanced_presentation: bool = False


class AgentYamlConfig(BaseModel):
    """Complete agent configuration from YAML."""

    name: str
    domain: str
    collection_name: str
    retrieval: RetrievalConfig
    verification: VerificationConfig
    fallback: FallbackConfig
    abstention: AbstentionConfig = Field(default_factory=AbstentionConfig)


# ============================================================================
# Configuration Manager
# ============================================================================


class AgentConfigManager:
    """
    Manager for loading and managing agent configurations.

    Provides:
    - Loading configs from YAML files
    - Creating agent instances from configs
    - Managing system prompts from files
    """

    def __init__(self, config_dir: Optional[Path] = None, prompts_dir: Optional[Path] = None):
        """
        Initialize the config manager.

        Args:
            config_dir: Path to config/agents directory
            prompts_dir: Path to prompts directory
        """
        self._config_dir = config_dir or CONFIG_DIR
        self._prompts_dir = prompts_dir or PROMPTS_DIR
        self._configs: dict[str, AgentYamlConfig] = {}
        self._system_prompts: dict[str, str] = {}

    def load_config(self, agent_name: str) -> AgentYamlConfig:
        """
        Load a single agent configuration.

        Args:
            agent_name: Name of the agent (e.g., "fiqh", "hadith")

        Returns:
            AgentYamlConfig instance
        """
        if agent_name in self._configs:
            return self._configs[agent_name]

        config_path = self._config_dir / f"{agent_name}.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        config = AgentYamlConfig(**data)
        self._configs[agent_name] = config

        return config

    def load_system_prompt(self, agent_name: str) -> str:
        """
        Load system prompt for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Combined system prompt (preamble + agent prompt)
        """
        if agent_name in self._system_prompts:
            return self._system_prompts[agent_name]

        # Load shared preamble
        preamble_path = self._prompts_dir / "_shared_preamble.txt"
        preamble = ""
        if preamble_path.exists():
            with open(preamble_path, "r", encoding="utf-8") as f:
                preamble = f.read().strip()

        # Load agent-specific prompt
        prompt_path = self._prompts_dir / f"{agent_name}_agent.txt"
        agent_prompt = ""
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                agent_prompt = f.read().strip()

        # Combine preamble and agent prompt
        system_prompt = f"{preamble}\n\n{agent_prompt}" if preamble else agent_prompt
        self._system_prompts[agent_name] = system_prompt

        return system_prompt

    def get_collection_agent_config(
        self,
        agent_name: str,
        include_prompt: bool = True,
    ) -> CollectionAgentConfig:
        """
        Get a CollectionAgentConfig for the specified agent.

        Args:
            agent_name: Name of the agent (e.g., "fiqh")
            include_prompt: Whether to include system prompt

        Returns:
            CollectionAgentConfig instance
        """
        yaml_config = self.load_config(agent_name)

        # Convert retrieval config
        retrieval_strategy = RetrievalStrategy(
            dense_weight=yaml_config.retrieval.alpha,
            sparse_weight=1.0 - yaml_config.retrieval.alpha,
            top_k=yaml_config.retrieval.topk_reranked,
            rerank=True,
            score_threshold=yaml_config.retrieval.min_relevance,
        )

        # Convert verification checks
        verification_checks = [
            VerificationCheck(
                name=check.name,
                fail_policy=check.fail_policy,
                enabled=check.enabled,
            )
            for check in yaml_config.verification.checks
        ]

        verification_suite = VerificationSuite(
            checks=verification_checks,
            fail_fast=yaml_config.verification.fail_fast,
        )

        # Convert fallback policy
        fallback_policy = FallbackPolicy(
            strategy=yaml_config.fallback.strategy,
            message=yaml_config.fallback.message,
        )

        # Get system prompt if requested
        system_prompt = ""
        if include_prompt:
            system_prompt = self.load_system_prompt(agent_name)

        return CollectionAgentConfig(
            collection_name=yaml_config.collection_name,
            strategy=retrieval_strategy,
            verification_suite=verification_suite,
            fallback_policy=fallback_policy,
        )

    def list_available_agents(self) -> list[str]:
        """
        List all available agent configurations.

        Returns:
            List of agent names
        """
        if not self._config_dir.exists():
            return []

        return [f.stem for f in self._config_dir.glob("*.yaml")]

    def get_all_configs(self) -> dict[str, AgentYamlConfig]:
        """
        Load all available agent configurations.

        Returns:
            Dictionary mapping agent names to configs
        """
        agents = self.list_available_agents()
        return {agent: self.load_config(agent) for agent in agents}


# ============================================================================
# Singleton instance
# ============================================================================


_config_manager: Optional[AgentConfigManager] = None


def get_config_manager() -> AgentConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = AgentConfigManager()
    return _config_manager


__all__ = [
    "AgentConfigManager",
    "AgentYamlConfig",
    "RetrievalConfig",
    "VerificationConfig",
    "FallbackConfig",
    "AbstentionConfig",
    "get_config_manager",
    "CONFIG_DIR",
    "PROMPTS_DIR",
    # Also export settings for convenience
    "settings",
]
