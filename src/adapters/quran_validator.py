"""
Adapter: Quran quotation validation against the database.

Implements src.verification.ports.QuranQuotationPort on top of
src.quran.quotation_validator.QuotationValidator. It opens a database session
per call, which is what the exact-quote check did for itself before the port
existed.

Only the composition root builds this. Nothing under src/verification may
import it (hardening Phase 6).
"""

from __future__ import annotations

from typing import Any


class QuranQuotationAdapter:
    """QuranQuotationPort backed by QuotationValidator."""

    async def validate(self, text: str) -> dict[str, Any]:
        import asyncio

        from src.infrastructure.database import get_sync_session
        from src.quran.quotation_validator import QuotationValidator

        def _run_sync() -> dict[str, Any]:
            with get_sync_session() as session:
                validator = QuotationValidator(session=session)
                new_loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(new_loop)
                    return new_loop.run_until_complete(validator.validate(text))
                finally:
                    new_loop.close()

        return await asyncio.to_thread(_run_sync)
