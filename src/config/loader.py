"""
Config Loader for Agent Configurations

Loads YAML configuration files and combines them with system prompts
to create complete CollectionAgentConfig instances.

Features:
- Simple in-memory caching for performance
- Lazy loading of prompts
- Type-safe validation with Pydantic
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, ValidationError


# Base path for config and prompts directories
BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = BASE_DIR / "config" / "agents"
PROMPTS_DIR = BASE_DIR / "prompts"

# Simple in-memory cache for configs
_config_cache: dict[str, dict] = {}


def _get_cache_key(agent_name: str, load_prompts: bool) -> str:
    """Generate cache key for agent config."""
    return f"{agent_name}:{load_prompts}"


def clear_config_cache() -> None:
    """Clear the config cache. Useful for testing."""
    global _config_cache
    _config_cache = {}


def load_agent_config(
    agent_name: str,
    load_prompts: bool = True,
    use_cache: bool = True,
) -> dict:
    """
    Load agent configuration from YAML file.

    Args:
        agent_name: Name of the agent (without _agent suffix if needed)
        load_prompts: Whether to load associated prompts
        use_cache: Whether to use cached config (default: True)

    Returns:
        Dictionary with config data and optional system_prompt

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    cache_key = _get_cache_key(agent_name, load_prompts)

    # Return cached config if available
    if use_cache and cache_key in _config_cache:
        return _config_cache[cache_key]

    # Normalize agent name - add _agent suffix if not present
    normalized_name = agent_name
    if not normalized_name.endswith("_agent"):
        normalized_name = f"{normalized_name}_agent"

    config_path = CONFIG_DIR / f"{normalized_name.replace('_agent', '')}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f) or {}

    if load_prompts:
        # Load system prompt
        prompt_path = PROMPTS_DIR / f"{normalized_name.replace('_agent', '')}_agent.txt"

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

    # Cache the config
    if use_cache:
        _config_cache[cache_key] = config_data

    return config_data


def load_agent_config_typed(
    agent_name: str,
    config_class: type[BaseModel],
    load_prompts: bool = True,
) -> BaseModel:
    """
    Load agent configuration and validate with Pydantic.

    Args:
        agent_name: Name of the agent
        config_class: Pydantic model class for validation
        load_prompts: Whether to load associated prompts

    Returns:
        Validated config instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config validation fails
    """
    config_data = load_agent_config(agent_name, load_prompts)

    try:
        return config_class(**config_data)
    except ValidationError as e:
        raise ValueError(f"Invalid config for {agent_name}: {e}")


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
        return yaml.safe_load(f) or {}


__all__ = [
    "load_agent_config",
    "load_agent_config_typed",
    "get_all_agent_configs",
    "load_yaml_config",
    "clear_config_cache",
    "CONFIG_DIR",
    "PROMPTS_DIR",
]
