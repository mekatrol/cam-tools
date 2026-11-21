"""Typed, neutral extraction of editable operation properties."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .value_reader import neutral_parameter_value, property_map

if TYPE_CHECKING:
    from ...domain.types import JsonValue


def _member(source: object, name: str) -> object | None:
    try:
        return getattr(source, name)
    except AttributeError, RuntimeError:
        return None


def _count(source: object | None) -> int | None:
    if source is None:
        return None
    value = _member(source, "count")
    return value if isinstance(value, int) else None


def _quantity(source: object | None) -> tuple[tuple[str, JsonValue], ...] | None:
    """Read a host model parameter without exposing host-specific names."""
    if source is None:
        return None
    value = _member(source, "value")
    unit = _member(source, "unit")
    expression = _member(source, "expression")
    if not isinstance(value, int | float) or not isinstance(unit, str):
        return None
    normalized, dimension, canonical_unit = neutral_parameter_value(float(value), unit)
    return property_map(
        {
            "value": normalized,
            "dimension": dimension,
            "unit": canonical_unit,
            "expression": expression if isinstance(expression, str) else "",
        }
    )


def _first_quantity(source: object, names: tuple[str, ...]) -> JsonValue:
    for name in names:
        value = _quantity(_member(source, name))
        if value is not None:
            return value
    return None


def _edge_sets(source: object, *, radius: bool) -> tuple[JsonValue, ...]:
    collection = _member(source, "edgeSets") or _member(source, "chamferEdgeSets")
    count = _count(collection)
    item_method = _member(collection, "item")
    if count is None or not callable(item_method):
        return ()
    records: list[JsonValue] = []
    for index in range(count):
        edge_set = item_method(index)
        quantity = _first_quantity(
            edge_set,
            ("radius",) if radius else ("distance", "distanceOne", "distanceTwo"),
        )
        records.append(
            property_map(
                {
                    "edge_count": _count(_member(edge_set, "edges")) or 0,
                    "size": quantity,
                }
            )
        )
    return tuple(records)


def _extent(source: object | None) -> tuple[tuple[str, JsonValue], ...] | None:
    if source is None:
        return None
    distance = _first_quantity(source, ("distance", "offset"))
    direction = _member(source, "isPositiveDirection")
    full_length = _member(source, "isFullLength")
    return property_map(
        {
            "distance": distance,
            "positive_direction": direction if isinstance(direction, bool) else None,
            "full_length": full_length if isinstance(full_length, bool) else None,
        }
    )


def operation_properties(
    source: object, kind: str, sequence: int
) -> tuple[tuple[str, JsonValue], ...]:
    """Capture known editable properties for a neutral operation category."""
    values: dict[str, JsonValue] = {"history_index": sequence}
    if kind == "linear_sweep":
        values.update(
            {
                "profile_count": _count(_member(source, "profile")),
                "extent_one": _extent(_member(source, "extentOne")),
                "extent_two": _extent(_member(source, "extentTwo")),
                "symmetric_extent": _extent(_member(source, "symmetricExtent")),
                "has_two_extents": bool(_member(source, "hasTwoExtents")),
                "taper_angle_one": _quantity(_member(source, "taperAngleOne")),
                "taper_angle_two": _quantity(_member(source, "taperAngleTwo")),
                "result_body_count": _count(_member(source, "bodies")),
            }
        )
    elif kind == "edge_round":
        values["edge_sets"] = _edge_sets(source, radius=True)
    elif kind == "edge_bevel":
        values["edge_sets"] = _edge_sets(source, radius=False)
    elif kind == "mirror":
        values.update(
            {
                "input_count": _count(_member(source, "inputEntities")),
                "result_body_count": _count(_member(source, "bodies")),
            }
        )
    elif kind == "assembly_position":
        transform = _member(source, "transform")
        values["transform_available"] = transform is not None
    return property_map(values)
