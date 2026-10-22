"""
Application-level models for Burhan Islamic QA system.

One-release shim: `RoutingDecision` moved to `src.domain.models` (Phase 2 of
docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md). Import from the
domain home in new code; this alias disappears after the next release.
"""

from __future__ import annotations

from src.domain.models import RoutingDecision as RoutingDecision

__all__ = ["RoutingDecision"]
