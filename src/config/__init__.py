"""
Config module: paths and environment for the Burhan project.

The agent configuration itself lives in config/agents/*.yaml and is loaded by
src.agents.spec_loader into src.domain.agent_spec.AgentSpec. The old
AgentConfigManager, which mapped the retired YAML schema onto the deleted
collection agent classes, was removed in hardening Phase 5
(docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md).
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config" / "agents"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

__all__ = [
    "PROJECT_ROOT",
    "CONFIG_DIR",
    "PROMPTS_DIR",
    "settings",
]
