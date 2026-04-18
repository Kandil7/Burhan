"""
Config Runtime - Runtime configuration loader and settings.

This module contains runtime configuration code that was moved from src/config/
as part of the v2 migration. The root config/ directory should now contain only
YAML declarative configuration files.

Migration:
- Settings, loader, constants, logging moved here from src/config/
- Config/__init__.py has AgentConfigManager which stays here
- domain/intents.py is the canonical intents definition (config/intents.py is backward compat)

Usage:
    from src.config_runtime.settings import settings
    from src.config_runtime.loader import load_agent_config
"""

from src.config.settings import Settings, settings
from src.config.loader import load_agent_config, load_agent_config_typed, get_all_agent_configs
from src.config import AgentConfigManager, get_config_manager

__all__ = [
    # Settings
    "Settings",
    "settings",
    # Loader
    "load_agent_config",
    "load_agent_config_typed",
    "get_all_agent_configs",
    # Agent config manager
    "AgentConfigManager",
    "get_config_manager",
]
