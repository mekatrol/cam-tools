"""Typed core-capture reader for the active source design."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import adsk.core
import adsk.fusion
from application.export_service import CaptureCancelledError
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
from .value_reader import (
    length_in_millimetres,
    matrix_transform,
    neutral_parameter_value,
    property_map,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from application.ports import ProgressReporter


class UnsupportedDesignError(RuntimeError):
    """Raised when no supported parametric design is active."""


@dataclass(slots=True)
class _CaptureState:
    progress: ProgressReporter
    identities: IdentityMap = field(default_factory=IdentityMap)
    parameters: list[Parameter] = field(default_factory=list)
    definitions: list[Definition] = field(default_factory=list)
    instances: list[Instance] = field(default_factory=list)
    construction: list[GeometryRecord] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)
    results: list[EntityRecord] = field(default_factory=list)
    resources: list[EntityRecord] = field(default_factory=list)
    relationships: list[EntityRecord] = field(default_factory=list)
    configurations: list[EntityRecord] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    completed: int = 0
    estimated_total: int = 1

    def advance(self, activity: str) -> None:
        """Publish progress and stop promptly after cancellation."""
        self.completed += 1
        self.progress.update(self.completed, self.estimated_total, activity)
        if self.progress.cancelled:
            raise CaptureCancelledError


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

    def capture(self, progress: ProgressReporter) -> ModelDocument:
        """Capture hierarchy, parameters, sketches, history, and evaluated bodies."""
        design = adsk.fusion.Design.cast(self.application.activeProduct)
        if design is None:
            message = "The active document is not a supported design"
            raise UnsupportedDesignError(message)
        if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
            message = "The active design does not retain parametric history"
            raise UnsupportedDesignError(message)

        state = _CaptureState(progress=progress)
        state.estimated_total = max(
            1,
            design.allParameters.count
            + design.timeline.count
            + design.rootComponent.sketches.count
            + design.rootComponent.bRepBodies.count
            + design.rootComponent.occurrences.count,
        )
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
        self._read_advanced_state(design, state)
        statuses = [
            item.status
            for item in (
                *state.resources,
                *state.operations,
                *state.results,
                *state.relationships,
                *state.configurations,
            )
        ]
        coverage = Coverage(
            exact=statuses.count(CaptureStatus.EXACT),
            complete_with_fallback=statuses.count(CaptureStatus.COMPLETE_WITH_FALLBACK),
            approximated=statuses.count(CaptureStatus.APPROXIMATED),
            unclassified=statuses.count(CaptureStatus.UNCLASSIFIED),
        )
        title = self.application.activeDocument.name
        return ModelDocument(
            format=FormatInfo("neutral_parametric_model", "1.1.0", "0.4.0"),
            document=DocumentInfo(title=title, modified_at=datetime.now(UTC).isoformat()),
            conventions=Conventions(),
            parameters=tuple(state.parameters),
            resources=tuple(state.resources),
            definitions=tuple(state.definitions),
            instances=tuple(state.instances),
            construction=tuple(state.construction),
            operations=tuple(state.operations),
            results=tuple(state.results),
            relationships=tuple(state.relationships),
            configurations=tuple(state.configurations),
            diagnostics=tuple(state.diagnostics),
            coverage=coverage,
        )

    def _read_parameters(self, design: adsk.fusion.Design, state: _CaptureState) -> None:
        sources = tuple(_items(design.allParameters))
        identifiers = {
            source.name: state.identities.id_for("parameter", source.entityToken or source.name)
            for source in sources
        }
        for source in sources:
            state.advance("Capturing parameters")
            parameter_id = identifiers[source.name]
            value, dimension, unit = neutral_parameter_value(source.value, source.unit)
            expression = (
                ExpressionNode("opaque_expression", source.expression)
                if source.expression
                else None
            )
            dependencies = tuple(
                sorted(
                    identifier
                    for name, identifier in identifiers.items()
                    if name != source.name
                    and re.search(
                        rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", source.expression
                    )
                )
            )
            state.parameters.append(
                Parameter(
                    id=parameter_id,
                    label=source.name,
                    value=value,
                    dimension=dimension,
                    unit=unit,
                    expression=expression,
                    dependencies=dependencies,
                    comment=source.comment,
                    exposed=source.isUserParameter,
                )
            )
            if unit == "unresolved":
                state.diagnostics.append(
                    Diagnostic(
                        "capture.parameter_unit_unresolved",
                        Severity.WARNING,
                        "A parameter dimension could not be normalized to a canonical unit.",
                        parameter_id,
                        "Preserve the opaque expression and request an explicit unit mapping.",
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
            state.advance("Capturing assembly hierarchy")
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
            state.advance("Capturing construction geometry")
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
            state.advance("Capturing evaluated bodies")
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
                        length_in_millimetres(box.minPoint.x),
                        length_in_millimetres(box.minPoint.y),
                        length_in_millimetres(box.minPoint.z),
                    ),
                    "bounds_max": (
                        length_in_millimetres(box.maxPoint.x),
                        length_in_millimetres(box.maxPoint.y),
                        length_in_millimetres(box.maxPoint.z),
                    ),
                }
            )
            state.results.append(
                EntityRecord(
                    identifier,
                    "body",
                    status=CaptureStatus.COMPLETE_WITH_FALLBACK,
                    properties=properties,
                )
            )
            self._read_body_appearance(body, identifier, state)
        return identifiers

    def _read_history(self, design: adsk.fusion.Design, state: _CaptureState) -> None:
        for sequence, timeline_object in enumerate(_items(design.timeline)):
            state.advance("Capturing construction history")
            source = timeline_object.entity
            token = source.entityToken if source is not None else f"timeline-{sequence}"
            identifier = state.identities.id_for("operation", token)
            label = source.name if source is not None else f"Operation {sequence + 1}"
            kind = _neutral_operation_kind(source.objectType if source is not None else "")
            status = (
                CaptureStatus.COMPLETE_WITH_FALLBACK
                if kind != "unclassified_operation"
                else CaptureStatus.UNCLASSIFIED
            )
            diagnostic_codes = ("capture.operation_properties_fallback",)
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
            else:
                state.diagnostics.append(
                    Diagnostic(
                        "capture.operation_properties_fallback",
                        Severity.INFORMATION,
                        "The operation type and order were captured without a complete typed "
                        "parameter set.",
                        identifier,
                        "Preserve the operation and use evaluated body data for verification.",
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

    def _read_body_appearance(
        self, body: adsk.fusion.BRepBody, body_id: str, state: _CaptureState
    ) -> None:
        try:
            appearance = body.appearance
        except AttributeError, RuntimeError:
            appearance = None
        if appearance is None:
            return
        resource_id = state.identities.id_for("appearance", appearance.id or appearance.name)
        if not any(item.id == resource_id for item in state.resources):
            state.resources.append(
                EntityRecord(
                    resource_id,
                    "appearance",
                    properties=property_map(
                        {
                            "label": appearance.name,
                            "model": "physically_based",
                            "source_properties_available": False,
                        }
                    ),
                    status=CaptureStatus.COMPLETE_WITH_FALLBACK,
                )
            )
            state.diagnostics.append(
                Diagnostic(
                    "capture.appearance_fallback",
                    Severity.INFORMATION,
                    "A visual assignment was retained without decoded channel values.",
                    resource_id,
                    "Preserve the assignment and use evaluated display data when available.",
                )
            )
        state.relationships.append(
            EntityRecord(
                state.identities.id_for("relationship", f"appearance:{body_id}"),
                "visual_assignment",
                properties=property_map({"scope": "body"}),
                references=(body_id, resource_id),
            )
        )

    def _read_advanced_state(self, design: adsk.fusion.Design, state: _CaptureState) -> None:
        self._read_joints(design.rootComponent, state)
        try:
            configurations = design.configurations
        except AttributeError:
            state.diagnostics.append(
                Diagnostic(
                    "capture.configurations_unavailable",
                    Severity.INFORMATION,
                    "Configuration state is not exposed by this runtime.",
                    importer_guidance="Treat the captured state as the default variant.",
                )
            )
            return
        for source in _items(configurations):
            state.advance("Capturing configurations")
            identifier = state.identities.id_for("configuration", source.entityToken or source.name)
            state.configurations.append(
                EntityRecord(
                    identifier,
                    "configuration",
                    properties=property_map({"label": source.name, "active": source.isActive}),
                    status=CaptureStatus.COMPLETE_WITH_FALLBACK,
                )
            )

    def _read_joints(self, component: adsk.fusion.Component, state: _CaptureState) -> None:
        for source in (*_items(component.joints), *_items(component.asBuiltJoints)):
            state.advance("Capturing assembly relationships")
            identifier = state.identities.id_for("relationship", source.entityToken or source.name)
            references = tuple(
                state.identities.id_for(
                    "instance", occurrence.entityToken or occurrence.fullPathName
                )
                for occurrence in (source.occurrenceOne, source.occurrenceTwo)
                if occurrence is not None
            )
            if any(item.id == identifier for item in state.relationships):
                continue
            state.relationships.append(
                EntityRecord(
                    identifier,
                    "kinematic_relationship",
                    status=CaptureStatus.COMPLETE_WITH_FALLBACK,
                    properties=property_map(
                        {
                            "label": source.name,
                            "enabled": not source.isSuppressed,
                            "motion_class": "unspecified",
                            "source_properties_available": False,
                        }
                    ),
                    references=references,
                )
            )
        for occurrence in _items(component.occurrences):
            self._read_joints(occurrence.component, state)


def _neutral_operation_kind(object_type: str) -> str:
    normalized = object_type.casefold()
    mappings = (
        (("box", "cylinder", "sphere", "torus", "coil"), "primitive"),
        (("extrude",), "linear_sweep"),
        (("revolve",), "rotational_sweep"),
        (("sweep",), "path_sweep"),
        (("loft",), "loft"),
        (("fillet",), "edge_round"),
        (("chamfer",), "edge_bevel"),
        (("shell",), "thin_shell"),
        (("hole",), "hole"),
        (("combine",), "boolean_operation"),
        (("split",), "split"),
        (("thread",), "thread"),
        (("rib", "web"), "rib"),
        (("rectangularpattern",), "linear_array"),
        (("circularpattern",), "circular_array"),
        (("pattern",), "path_array"),
        (("mirror",), "mirror"),
        (("copy",), "copy"),
        (("move",), "move"),
        (("scale",), "scale"),
        (("draft",), "draft"),
        (("offsetface", "presspull"), "direct_face_offset"),
        (("construction", "plane", "axis", "point"), "construction_feature"),
        (("sheetmetal", "flange", "bend"), "sheet_metal_operation"),
        (("mesh",), "mesh_operation"),
        (("form", "freeform"), "freeform_edit"),
        (("derived",), "derived_definition"),
    )
    for fragments, kind in mappings:
        if any(fragment in normalized for fragment in fragments):
            return kind
    return "unclassified_operation"
