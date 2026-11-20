"""Ordered parametric construction operation records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import CaptureStatus, JsonValue


@dataclass(frozen=True, slots=True)
class Operation:
    """One ordered construction step with explicit graph references."""

    id: str
    kind: str
    label: str
    sequence: int
    status: CaptureStatus
    enabled: bool = True
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    target_bodies: tuple[str, ...] = ()
    mode: str = "new"
    parameters: tuple[tuple[str, JsonValue], ...] = ()
    diagnostic_codes: tuple[str, ...] = ()
