"""Shared immutable value types used by the neutral model graph."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

type JsonScalar = bool | int | float | str | None
type JsonValue = JsonScalar | tuple[JsonValue, ...] | tuple[tuple[str, JsonValue], ...]


class CaptureStatus(StrEnum):
    """Completeness of a captured entity."""

    EXACT = "exact"
    COMPLETE_WITH_FALLBACK = "complete_with_fallback"
    APPROXIMATED = "approximated"
    UNCLASSIFIED = "unclassified"


class Severity(StrEnum):
    """Importance of a capture diagnostic."""

    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class Reference:
    """Reference to another record by neutral identifier."""

    id: str


@dataclass(frozen=True, slots=True)
class Quantity:
    """Finite numeric value with an explicit dimensional unit."""

    value: float
    unit: str
