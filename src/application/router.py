"""
Router Agent for Athar Islamic QA system.

DEPRECATED: This module has been moved to src/application/router/router_agent.py
Please update your imports to use the new module path.

This module will be removed in a future version.

---
Migration guide:
    Old: from src.application.router import RouterAgent
    New: from src.application.router.router_agent import RouterAgent
        or from src.application.router import router_agent (singleton)
"""

from __future__ import annotations

import warnings

# Issue deprecation warning when module is imported
warnings.warn(
    "src.application.router is deprecated. "
    "Please import from src.application.router.router_agent instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for backward compatibility
from src.application.router.router_agent import RouterAgent
from src.application.router.router_agent import router_agent
from src.application.router.router_agent import RoutingDecision

__all__ = ["RouterAgent", "router_agent", "RoutingDecision"]
