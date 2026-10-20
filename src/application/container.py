"""
Compatibility shim for the retired dependency-injection container.

The original module depended on ``dependency_injector``, which is not a
project dependency, and on modules that no longer exist. It was never
imported by the application.

Wiring now lives in two places:

* ``src/api/lifespan.py`` builds infrastructure and attaches it to app state.
* ``src/core/registry.py`` owns agent and tool resolution.

This module keeps the old import path working and delegates to the registry.
"""

from __future__ import annotations

from src.core.registry import AgentRegistry, get_registry

__all__ = [
    "Container",
    "get_container",
    "initialize_container",
    "close_container",
]

# Backwards-compatible name for the registry.
Container = AgentRegistry


def get_container() -> AgentRegistry:
    """Return the application-wide agent registry."""
    return get_registry()


async def initialize_container() -> None:
    """Ensure the registry exists.

    Infrastructure is initialized by the application lifespan, not here.
    """
    get_registry()


async def close_container() -> None:
    """No-op kept for API compatibility.

    Lifespan shutdown closes the shared clients it created.
    """
    return None
