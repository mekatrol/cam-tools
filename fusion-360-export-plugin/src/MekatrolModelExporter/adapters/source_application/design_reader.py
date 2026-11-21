"""Typed core-capture reader for the active source design."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import adsk.core
import adsk.fusion
from domain.diagnostics import Coverage, Diagnostic
from domain.document import (
    Conventions,
    Definition,
    DocumentInfo,
    EntityRecord,
    FormatInfo,
    Instance,
    ModelDocument,
)
from domain.expressions import ExpressionNode, Parameter
from domain.geometry import IDENTITY_TRANSFORM, GeometryRecord
from domain.operations import Operation
from domain.types import CaptureStatus, Severity

from .identity_map import IdentityMap
from .value_reader import finite, matrix_transform, property_map

if TYPE_CHECKING:
    from collections.abc import Iterable


class UnsupportedDesignError(RuntimeError):
    """Raised when no supported parametric design is active."""


@dataclass(slots=True)
class _CaptureState:
    identities: IdentityMap = field(default_factory=IdentityMap)
    parameters: list[Parameter] = field(default_factory=list)
    definitions: list[Definition] = field(default_factory=list)
    instances: list[Instance] = field(default_factory=list)
    construction: list[GeometryRecord] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)
    results: list[EntityRecord] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)


def _items[T](collection: adsk.core.ObjectCollection[T]) -> Iterable[T]:
    for index in range(collection.count):
        yield collection.item(index)


@dataclass(frozen=True, slots=True)
class ActiveDesignReader:
    """Capture the active parametric design into neutral domain records."""

    application: adsk.core.Application

    @classmethod
    def from_running_application(cls) -> ActiveDesignReader:
        """Create a reader for the currently running host application."""
        return cls(adsk.core.Application.get())

    def capture(self) -> ModelDocument:
        """Capture hierarchy, parameters, sketches, history, and evaluated bodies."""
        design = adsk.fusion.Design.cast(self.application.activeProduct)
        if design is None:
            message = "The active document is not a supported design"
            raise UnsupportedDesignError(message)
        if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
            message = "The active design does not retain parametric history"
            raise UnsupportedDesignError(message)

        state = _CaptureState()
        self._read_parameters(design, state)
        root_id = self._read_component(design.rootComponent, state)
        state.instances.append(
            Instance(
                "instance:root",
                root_id,
                design.rootComponent.name,
                IDENTITY_TRANSFORM,
                grounded=True,
            )
        )
        self._read_occurrences(design.rootComponent.occurrences, "instance:root", state)
        self._read_history(design, state)
        statuses = [item.status for item in (*state.operations, *state.results)]
        coverage = Coverage(
            exact=statuses.count(CaptureStatus.EXACT),
            complete_with_fallback=statuses.count(CaptureStatus.COMPLETE_WITH_FALLBACK),
            approximated=statuses.count(CaptureStatus.APPROXIMATED),
            unclassified=statuses.count(CaptureStatus.UNCLASSIFIED),
        )
        title = self.application.activeDocument.name
        return ModelDocument(
            format=FormatInfo("neutral_parametric_model", "1.0.0", "0.3.0"),
            document=DocumentInfo(title=title, modified_at=datetime.now(UTC).isoformat()),
            conventions=Conventions(),
            parameters=tuple(state.parameters),
            definitions=tuple(state.definitions),
            instances=tuple(state.instances),
            construction=tuple(state.construction),
            operations=tuple(state.operations),
            results=tuple(state.results),
            diagnostics=tuple(state.diagnostics),
            coverage=coverage,
        )

    def _read_parameters(self, design: adsk.fusion.Design, state: _CaptureState) -> None:
        for source in _items(design.allParameters):
            parameter_id = state.identities.id_for("parameter", source.entityToken or source.name)
            expression = (
                ExpressionNode("source_expression", source.expression)
                if source.expression
                else None
            )
            state.parameters.append(
                Parameter(
                    id=parameter_id,
                    label=source.name,
                    value=finite(source.value, "parameter value"),
                    dimension=source.unit,
                    unit=source.unit,
                    expression=expression,
                    comment=source.comment,
                    exposed=source.isUserParameter,
                )
            )

    def _read_component(self, component: adsk.fusion.Component, state: _CaptureState) -> str:
        definition_id = state.identities.id_for(
            "definition", component.entityToken or component.name
        )
        if any(item.id == definition_id for item in state.definitions):
            return definition_id
        construction_ids = self._read_sketches(component, state)
        result_ids = self._read_bodies(component, state)
        state.definitions.append(
            Definition(
                id=definition_id,
                label=component.name,
                construction_ids=tuple(construction_ids),
                result_ids=tuple(result_ids),
            )
        )
        return definition_id

    def _read_occurrences(
        self,
        occurrences: adsk.core.ObjectCollection[adsk.fusion.Occurrence],
        parent_id: str,
        state: _CaptureState,
    ) -> None:
        for source in _items(occurrences):
            definition_id = self._read_component(source.component, state)
            instance_id = state.identities.id_for(
                "instance", source.entityToken or source.fullPathName
            )
            state.instances.append(
                Instance(
                    id=instance_id,
                    definition_id=definition_id,
                    label=source.name,
                    transform=matrix_transform(source.transform2),
                    parent_id=parent_id,
                    visible=source.isLightBulbOn,
                    suppressed=source.isSuppressed,
                    grounded=source.isGrounded,
                )
            )
            self._read_occurrences(source.childOccurrences, instance_id, state)

    def _read_sketches(self, component: adsk.fusion.Component, state: _CaptureState) -> list[str]:
        identifiers: list[str] = []
        for sketch in _items(component.sketches):
            identifier = state.identities.id_for("sketch", sketch.entityToken or sketch.name)
            identifiers.append(identifier)
            state.construction.append(
                GeometryRecord(
                    identifier,
                    "sketch",
                    property_map(
                        {
                            "label": sketch.name,
                            "visible": sketch.isVisible,
                            "curve_count": sketch.sketchCurves.count,
                            "constraint_count": sketch.geometricConstraints.count,
                            "profile_count": sketch.profiles.count,
                            "transform": tuple(matrix_transform(sketch.transform).matrix),
                        }
                    ),
                )
            )
        return identifiers

    def _read_bodies(self, component: adsk.fusion.Component, state: _CaptureState) -> list[str]:
        identifiers: list[str] = []
        for body in _items(component.bRepBodies):
            identifier = state.identities.id_for("body", body.entityToken or body.name)
            identifiers.append(identifier)
            box = body.boundingBox
            properties = property_map(
                {
                    "label": body.name,
                    "visible": body.isVisible,
                    "solid": body.isSolid,
                    "face_count": body.faces.count,
                    "edge_count": body.edges.count,
                    "vertex_count": body.vertices.count,
                    "bounds_min": (
                        finite(box.minPoint.x, "bound"),
                        finite(box.minPoint.y, "bound"),
                        finite(box.minPoint.z, "bound"),
                    ),
                    "bounds_max": (
                        finite(box.maxPoint.x, "bound"),
                        finite(box.maxPoint.y, "bound"),
                        finite(box.maxPoint.z, "bound"),
                    ),
                }
            )
            state.results.append(EntityRecord(identifier, "body", properties=properties))
        return identifiers

    def _read_history(self, design: adsk.fusion.Design, state: _CaptureState) -> None:
        for sequence, timeline_object in enumerate(_items(design.timeline)):
            source = timeline_object.entity
            token = source.entityToken if source is not None else f"timeline-{sequence}"
            identifier = state.identities.id_for("operation", token)
            label = source.name if source is not None else f"Operation {sequence + 1}"
            kind = _neutral_operation_kind(source.objectType if source is not None else "")
            status = (
                CaptureStatus.EXACT
                if kind != "unclassified_operation"
                else CaptureStatus.UNCLASSIFIED
            )
            diagnostic_codes: tuple[str, ...] = ()
            if status is CaptureStatus.UNCLASSIFIED:
                diagnostic_codes = ("capture.operation_unclassified",)
                state.diagnostics.append(
                    Diagnostic(
                        "capture.operation_unclassified",
                        Severity.WARNING,
                        "An operation was retained as an ordered neutral fallback.",
                        identifier,
                        "Use the evaluated result and preserve the operation during migration.",
                    )
                )
            state.operations.append(
                Operation(
                    id=identifier,
                    kind=kind,
                    label=label,
                    sequence=sequence,
                    status=status,
                    enabled=not timeline_object.isSuppressed,
                    parameters=property_map({"history_index": sequence}),
                    diagnostic_codes=diagnostic_codes,
                )
            )


def _neutral_operation_kind(object_type: str) -> str:
    normalized = object_type.casefold()
    mappings = (
        (("extrude",), "linear_sweep"),
        (("revolve",), "rotational_sweep"),
        (("sweep",), "path_sweep"),
        (("loft",), "loft"),
        (("fillet",), "edge_round"),
        (("chamfer",), "edge_bevel"),
        (("shell",), "thin_shell"),
        (("hole",), "hole"),
        (("combine",), "boolean_operation"),
        (("pattern",), "array"),
        (("mirror",), "mirror"),
        (("move",), "move"),
        (("scale",), "scale"),
        (("draft",), "draft"),
    )
    for fragments, kind in mappings:
        if any(fragment in normalized for fragment in fragments):
            return kind
    return "unclassified_operation"
