"""
FastAPI dependencies shared by the route modules.

The application container is the single dependency the routes take. It is
built by src/composition.py at startup and stored on app.state; the per-route
helpers that used to read app.state attributes directly are gone.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, Request

if TYPE_CHECKING:
    from src.composition import Container


def get_container(request: Request) -> Container:
    """Get the application container the composition root built at startup."""
    container: Container | None = getattr(request.app.state, "container", None)
    if container is None:
        raise HTTPException(503, detail="Service container is not initialised.")
    return container
