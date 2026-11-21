"""Conversions from source values to neutral immutable values."""

import math
from typing import TYPE_CHECKING

from domain.geometry import Transform

if TYPE_CHECKING:
    import adsk.core
    from domain.types import JsonValue


def finite(value: float, label: str) -> float:
    """Require a finite source number."""
    if not math.isfinite(value):
        message = f"Source supplied a non-finite {label}"
        raise ValueError(message)
    return value


def matrix_transform(matrix: adsk.core.Matrix3D) -> Transform:
    """Convert a source transform to the row-major neutral representation."""
    values = tuple(
        finite(matrix.getCell(row, column), "transform value")
        for row in range(4)
        for column in range(4)
    )
    return Transform(values)


def property_map(values: dict[str, JsonValue]) -> tuple[tuple[str, JsonValue], ...]:
    """Freeze a mapping in deterministic key order."""
    return tuple(sorted(values.items()))
