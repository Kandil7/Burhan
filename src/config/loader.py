"""
Config Loader for Agent Configurations

Loads YAML configuration files and combines them with system prompts
to create complete CollectionAgentConfig instances.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml


# Base path for config and prompts directories
BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = BASE_DIR / "config" / "agents"
PROMPTS_DIR = BASE_DIR / "prompts"


def load_agent_config(
    agent_name: str,
    load_prompts: bool = True,
) -> dict:
    """
    Load agent configuration from YAML file.

    Args:
        agent_name: Name of the agent (without _agent suffix if needed)
        load_prompts: Whether to load associated prompts

    Returns:
        Dictionary with config data and optional system_prompt
    """
    # Normalize agent name - add _agent suffix if not present
    if not agent_name.endswith("_agent"):
        agent_name = f"{agent_name}_agent"

    config_path = CONFIG_DIR / f"{agent_name.replace('_agent', '')}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    if load_prompts:
        # Load system prompt
        prompt_path = PROMPTS_DIR / f"{agent_name.replace('_agent', '')}_agent.txt"

        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                agent_prompt = f.read()

            # Also load shared preamble
            preamble_path = PROMPTS_DIR / "_shared_preamble.txt"
            if preamble_path.exists():
                with open(preamble_path, "r", encoding="utf-8") as f:
                    shared_preamble = f.read()
                config_data["system_prompt"] = f"{shared_preamble}\n\n{agent_prompt}"
            else:
                config_data["system_prompt"] = agent_prompt
        else:
            config_data["system_prompt"] = ""

    return config_data


def get_all_agent_configs() -> list[str]:
    """
    Get list of all available agent configuration names.

    Returns:
        List of agent names (without _agent suffix)
    """
    if not CONFIG_DIR.exists():
        return []

    return [f.stem for f in CONFIG_DIR.glob("*.yaml")]


def load_yaml_config(config_path: Path) -> dict:
    """
    Load a single YAML config file.

    Args:
        config_path: Path to the YAML config file

    Returns:
        Dictionary with config data
    """
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


__all__ = [
    "load_agent_config",
    "get_all_agent_configs",
    "load_yaml_config",
    "CONFIG_DIR",
    "PROMPTS_DIR",
]
