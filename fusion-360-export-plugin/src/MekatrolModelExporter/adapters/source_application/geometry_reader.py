"""Neutral capture of construction curves and evaluated body meshes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import adsk.core
import adsk.fusion

from .value_reader import finite, length_in_millimetres, neutral_parameter_value, property_map

if TYPE_CHECKING:
    from ...domain.types import JsonValue

MESH_TOLERANCE_MILLIMETRES = 0.01


def _point(point: adsk.core.Point3D) -> tuple[float, float, float]:
    return (
        length_in_millimetres(point.x),
        length_in_millimetres(point.y),
        length_in_millimetres(point.z),
    )


def _vector(vector: adsk.core.Vector3D) -> tuple[float, float, float]:
    return (
        finite(vector.x, "vector component"),
        finite(vector.y, "vector component"),
        finite(vector.z, "vector component"),
    )


def _curve_base(curve: adsk.fusion.SketchCurve) -> dict[str, JsonValue]:
    return {
        "construction": curve.isConstruction,
        "fixed": curve.isFixed,
        "visible": curve.isVisible,
    }


def sketch_curve_data(curve: object) -> tuple[tuple[str, JsonValue], ...]:
    """Return one exact neutral sketch-curve representation."""
    line = adsk.fusion.SketchLine.cast(curve)
    if line is not None:
        values = _curve_base(line)
        values.update(
            {
                "kind": "line_segment",
                "start": _point(line.geometry.startPoint),
                "end": _point(line.geometry.endPoint),
            }
        )
        return property_map(values)

    arc = adsk.fusion.SketchArc.cast(curve)
    if arc is not None:
        values = _curve_base(arc)
        values.update(
            {
                "kind": "circular_arc",
                "center": _point(arc.geometry.center),
                "normal": _vector(arc.geometry.normal),
                "radius": length_in_millimetres(arc.geometry.radius),
                "start": _point(arc.geometry.startPoint),
                "end": _point(arc.geometry.endPoint),
                "start_angle": finite(arc.geometry.startAngle, "arc angle"),
                "end_angle": finite(arc.geometry.endAngle, "arc angle"),
            }
        )
        return property_map(values)

    circle = adsk.fusion.SketchCircle.cast(curve)
    if circle is not None:
        values = _curve_base(circle)
        values.update(
            {
                "kind": "circle",
                "center": _point(circle.geometry.center),
                "normal": _vector(circle.geometry.normal),
                "radius": length_in_millimetres(circle.geometry.radius),
            }
        )
        return property_map(values)

    ellipse = adsk.fusion.SketchEllipse.cast(curve)
    elliptical_arc = adsk.fusion.SketchEllipticalArc.cast(curve)
    if ellipse is not None or elliptical_arc is not None:
        geometry = elliptical_arc.geometry if elliptical_arc is not None else ellipse.geometry
        values = _curve_base(elliptical_arc if elliptical_arc is not None else ellipse)
        values.update(
            {
                "kind": "elliptical_arc" if elliptical_arc is not None else "ellipse",
                "center": _point(geometry.center),
                "normal": _vector(geometry.normal),
                "major_axis": _vector(geometry.majorAxis),
                "major_radius": length_in_millimetres(geometry.majorRadius),
                "minor_radius": length_in_millimetres(geometry.minorRadius),
            }
        )
        if elliptical_arc is not None:
            values["start_angle"] = finite(elliptical_arc.geometry.startAngle, "ellipse angle")
            values["end_angle"] = finite(elliptical_arc.geometry.endAngle, "ellipse angle")
        return property_map(values)

    spline = adsk.fusion.SketchFittedSpline.cast(curve)
    if spline is not None:
        geometry = spline.geometry
        values = _curve_base(spline)
        values.update(
            {
                "kind": "rational_spline" if geometry.isRational else "polynomial_spline",
                "degree": geometry.degree,
                "periodic": geometry.isPeriodic,
                "control_points": tuple(_point(point) for point in geometry.controlPoints),
                "knots": tuple(finite(value, "spline knot") for value in geometry.knots),
                "weights": tuple(finite(value, "spline weight") for value in geometry.weights),
            }
        )
        return property_map(values)

    return property_map({"kind": "unsupported_curve"})


def sketch_curves(sketch: adsk.fusion.Sketch) -> tuple[JsonValue, ...]:
    """Capture all curves in stable source collection order."""
    return tuple(
        sketch_curve_data(sketch.sketchCurves.item(index))
        for index in range(sketch.sketchCurves.count)
    )


def _member(source: object, name: str) -> object | None:
    try:
        return getattr(source, name)
    except AttributeError, RuntimeError:
        return None


def _semantic_kind(source: object, mappings: tuple[tuple[tuple[str, ...], str], ...]) -> str:
    object_type = _member(source, "objectType")
    normalized = object_type.casefold() if isinstance(object_type, str) else ""
    for fragments, kind in mappings:
        if any(fragment in normalized for fragment in fragments):
            return kind
    return "unclassified"


def _entity_indices(source: object, curve_indices: dict[str, int]) -> tuple[int, ...]:
    indices: set[int] = set()
    for name in (
        "entity",
        "entityOne",
        "entityTwo",
        "line",
        "lineOne",
        "lineTwo",
        "curve",
        "curveOne",
        "curveTwo",
        "point",
        "pointOne",
        "pointTwo",
    ):
        entity = _member(source, name)
        token = _member(entity, "entityToken") if entity is not None else None
        if isinstance(token, str) and token in curve_indices:
            indices.add(curve_indices[token])
    return tuple(sorted(indices))


def sketch_constraints(sketch: adsk.fusion.Sketch) -> tuple[JsonValue, ...]:
    """Capture neutral constraint kinds and their referenced curve indices."""
    curve_indices: dict[str, int] = {}
    for index in range(sketch.sketchCurves.count):
        token = _member(sketch.sketchCurves.item(index), "entityToken")
        if isinstance(token, str) and token:
            curve_indices[token] = index
    mappings = (
        (("coincident",), "coincident"),
        (("collinear",), "collinear"),
        (("concentric",), "concentric"),
        (("equal",), "equal"),
        (("horizontal",), "horizontal"),
        (("vertical",), "vertical"),
        (("parallel",), "parallel"),
        (("perpendicular",), "perpendicular"),
        (("tangent",), "tangent"),
        (("midpoint",), "midpoint"),
        (("symmetry",), "symmetric"),
        (("smooth",), "curvature_continuity"),
        (("fixed",), "fixed"),
    )
    return tuple(
        property_map(
            {
                "kind": _semantic_kind(sketch.geometricConstraints.item(index), mappings),
                "curve_indices": _entity_indices(
                    sketch.geometricConstraints.item(index), curve_indices
                ),
            }
        )
        for index in range(sketch.geometricConstraints.count)
    )


def sketch_dimensions(sketch: adsk.fusion.Sketch) -> tuple[JsonValue, ...]:
    """Capture driving and reference dimensions with canonical units."""
    mappings = (
        (("angular",), "angle"),
        (("diameter",), "diameter"),
        (("radial",), "radius"),
        (("distance", "offset"), "distance"),
    )
    records: list[JsonValue] = []
    for index in range(sketch.sketchDimensions.count):
        dimension = sketch.sketchDimensions.item(index)
        parameter = _member(dimension, "parameter")
        value = _member(parameter, "value") if parameter is not None else None
        unit = _member(parameter, "unit") if parameter is not None else None
        expression = _member(parameter, "expression") if parameter is not None else None
        normalized: JsonValue = None
        dimension_name = "unresolved"
        canonical_unit = "unresolved"
        if isinstance(value, int | float) and isinstance(unit, str):
            normalized, dimension_name, canonical_unit = neutral_parameter_value(float(value), unit)
        records.append(
            property_map(
                {
                    "kind": _semantic_kind(dimension, mappings),
                    "value": normalized,
                    "dimension": dimension_name,
                    "unit": canonical_unit,
                    "expression": expression if isinstance(expression, str) else "",
                    "driving": bool(_member(dimension, "isDriving")),
                }
            )
        )
    return tuple(records)


def evaluated_mesh(body: adsk.fusion.BRepBody) -> tuple[tuple[str, JsonValue], ...]:
    """Tessellate a body into a portable indexed triangle mesh."""
    calculator = body.meshManager.createMeshCalculator()
    calculator.surfaceTolerance = MESH_TOLERANCE_MILLIMETRES / 10.0
    mesh = calculator.calculate()
    return property_map(
        {
            "representation": "indexed_triangle_mesh",
            "tolerance": MESH_TOLERANCE_MILLIMETRES,
            "tolerance_unit": "millimetre",
            "vertices": tuple(_point(point) for point in mesh.nodeCoordinates),
            "triangles": tuple(
                tuple(mesh.nodeIndices[index : index + 3])
                for index in range(0, len(mesh.nodeIndices), 3)
            ),
            "normals": tuple(_vector(vector) for vector in mesh.normalVectors),
        }
    )
