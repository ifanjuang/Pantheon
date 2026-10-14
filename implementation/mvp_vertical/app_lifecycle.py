"""Small FastAPI lifespan composition helpers.

Additional bounded schema initializers run once after the previously installed
lifespan has entered. This preserves initializer ordering without deprecated
startup-event registration and never runs DDL per request.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI


def install_post_start_initializer(app: FastAPI, initializer: Callable[[], None]) -> None:
    """Run one initializer once, after the current lifespan startup has completed."""
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        async with original_lifespan(application) as state:
            initializer()
            yield state

    app.router.lifespan_context = lifespan
