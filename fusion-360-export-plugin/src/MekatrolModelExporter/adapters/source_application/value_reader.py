"""Conversions from source values to neutral immutable values."""

import math
from typing import TYPE_CHECKING

from ...domain.geometry import Transform

if TYPE_CHECKING:
    import adsk.core

    from ...domain.types import JsonValue

TRANSLATION_COLUMN = 3
SPATIAL_ROW_COUNT = 3
SOURCE_LENGTH_TO_MILLIMETRES = 10.0


def finite(value: float, label: str) -> float:
    """Require a finite source number."""
    if not math.isfinite(value):
        message = f"Source supplied a non-finite {label}"
        raise ValueError(message)
    return value


def matrix_transform(matrix: adsk.core.Matrix3D) -> Transform:
    """Convert a source transform to row-major form with millimetre translation."""
    values = tuple(
        finite(matrix.getCell(row, column), "transform value")
        * (
            SOURCE_LENGTH_TO_MILLIMETRES
            if column == TRANSLATION_COLUMN and row < SPATIAL_ROW_COUNT
            else 1.0
        )
        for row in range(4)
        for column in range(4)
    )
    return Transform(values)


def length_in_millimetres(value: float) -> float:
    """Convert the source application's centimetre database length to millimetres."""
    return finite(value, "length") * SOURCE_LENGTH_TO_MILLIMETRES


def neutral_parameter_value(value: float, unit: str) -> tuple[float, str, str]:
    """Return a database value with a neutral dimension and canonical unit."""
    normalized = unit.casefold().replace(" ", "")
    length_units = {"mm", "cm", "m", "in", "ft", "yd"}
    angle_units = {"deg", "degree", "degrees", "rad", "radian", "radians"}
    if normalized in length_units:
        return length_in_millimetres(value), "length", "millimetre"
    if normalized in angle_units:
        return finite(value, "angle"), "angle", "radian"
    if normalized in {"", "unitless", "ul"}:
        return finite(value, "scalar"), "scalar", "one"
    return finite(value, "parameter value"), "source_defined", "unresolved"


def property_map(values: dict[str, JsonValue]) -> tuple[tuple[str, JsonValue], ...]:
    """Freeze a mapping in deterministic key order."""
    return tuple(sorted(values.items()))
