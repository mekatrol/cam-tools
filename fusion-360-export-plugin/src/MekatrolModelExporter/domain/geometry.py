"""Neutral coordinate, transform, and evaluated geometry records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import JsonValue

TRANSFORM_VALUE_COUNT = 16


@dataclass(frozen=True, slots=True)
class Vector3:
    """Three finite coordinates in the document length unit."""

    x: float
    y: float
    z: float


@dataclass(frozen=True, slots=True)
class Transform:
    """Row-major rigid 4 by 4 transformation matrix."""

    matrix: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.matrix) != TRANSFORM_VALUE_COUNT:
            message = "A transform must contain exactly 16 values"
            raise ValueError(message)


IDENTITY_TRANSFORM = Transform(
    (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
)


@dataclass(frozen=True, slots=True)
class GeometryRecord:
    """Typed exact or evaluated geometry with neutral properties."""

    id: str
    kind: str
    properties: tuple[tuple[str, JsonValue], ...] = ()
