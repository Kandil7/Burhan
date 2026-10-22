"""
Ports the verification layer needs from the outside world.

The consumer declares the interface here, so nothing under src/verification
has to import an adapter or infrastructure module. The composition root
injects an implementor at startup (src/adapters/quran_validator.py wires the
QuotationValidator); without one, the checks fail closed.

Hardening Phase 6 (docs/8-development/refactoring/REFACTOR_PLAN_HARDENING.md).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class QuranQuotationPort(Protocol):
    """Quote validation against Quran text."""

    async def validate(self, text: str) -> dict[str, Any]:
        """Return a result dict with at least an ``is_quran`` boolean."""
        ...
