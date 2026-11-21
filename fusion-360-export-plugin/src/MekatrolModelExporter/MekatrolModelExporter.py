"""Fusion script entry point for the Mekatrol model exporter."""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

import adsk.core

if TYPE_CHECKING:
    from collections.abc import Callable

_startup_error: str | None = None
_STARTUP_EXCEPTIONS = (AttributeError, ImportError, RuntimeError, SyntaxError)


def _startup_unavailable() -> None:
    """Stand in for the exporter when its module graph cannot be imported."""


_run_export: Callable[[], None] = _startup_unavailable
try:
    from .entrypoint import run_export as _run_export
except _STARTUP_EXCEPTIONS:
    _startup_error = traceback.format_exc()


def run(_context: object) -> None:
    """Run the finite, user-triggered Fusion script."""
    if _startup_error is not None:
        application = adsk.core.Application.get()
        if application is not None:
            application.userInterface.messageBox(f"Mekatrol startup failed:\n{_startup_error}")
        return
    _run_export()
