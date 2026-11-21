"""Human-readable trace from aggregate fidelity counts to individual records."""

from __future__ import annotations

import os
import tempfile
from contextlib import suppress
from typing import TYPE_CHECKING

from ..domain.types import CaptureStatus

if TYPE_CHECKING:
    from pathlib import Path

    from ..domain.diagnostics import Diagnostic
    from ..domain.document import EntityRecord, ModelDocument
    from ..domain.operations import Operation
    from ..domain.types import JsonValue

DEGRADED_STATUSES = frozenset(
    {
        CaptureStatus.COMPLETE_WITH_FALLBACK,
        CaptureStatus.APPROXIMATED,
        CaptureStatus.UNCLASSIFIED,
    }
)


def fidelity_log_path(destination: Path) -> Path:
    """Return the companion log path for a model destination."""
    return destination.with_suffix(".log")


def _property(properties: tuple[tuple[str, JsonValue], ...], name: str) -> JsonValue:
    return next((value for key, value in properties if key == name), None)


def _reason(kind: str, status: CaptureStatus) -> str:
    if status is CaptureStatus.UNCLASSIFIED:
        return "No supported neutral construction category matched this history entry."
    if kind == "body" and status is CaptureStatus.APPROXIMATED:
        return (
            "The complete analytic boundary representation is not serialized; an indexed "
            "triangle mesh is supplied as evaluated geometry."
        )
    return {
        "appearance": "The assignment is retained, but visual channel values are not decoded.",
        "configuration": "Configuration identity is retained without its complete rule table.",
        "kinematic_relationship": (
            "Relationship endpoints are retained without a complete typed motion definition."
        ),
        "linear_sweep": (
            "Available extents and quantities are captured, but complete profile selection, "
            "participant selection, and result correspondence are not yet encoded."
        ),
        "edge_round": (
            "Available radii and edge-set sizes are captured, but stable selected-edge geometry "
            "references and every variable-radius definition are not yet encoded."
        ),
        "edge_bevel": (
            "Available distances and edge-set sizes are captured, but stable selected-edge "
            "geometry references and every two-distance definition are not yet encoded."
        ),
        "mirror": (
            "Input and result counts are captured, but the complete mirror plane and stable input "
            "entity references are not yet encoded."
        ),
        "sketch_definition": (
            "The corresponding construction record contains sketch geometry and semantics, but "
            "this history event does not yet reference every affected result explicitly."
        ),
        "component_instance_event": (
            "The component instance is captured in the assembly graph; this history event does "
            "not contain a complete independent replay definition."
        ),
        "assembly_position": (
            "The position event is retained without a complete set of occurrence transforms."
        ),
        "body": "Evaluated geometry capture failed; only the body summary is available.",
    }.get(kind, "The record is retained, but some typed construction semantics are incomplete.")


def _diagnostic_lines(
    diagnostics: tuple[Diagnostic, ...], entity_id: str, indent: str = "    "
) -> list[str]:
    matching = [item for item in diagnostics if item.entity_id == entity_id]
    if not matching:
        return [f"{indent}diagnostics: none"]
    lines = [f"{indent}diagnostics:"]
    for item in matching:
        lines.append(f"{indent}  - [{item.severity.value}] {item.code}: {item.message}")
        if item.importer_guidance:
            lines.append(f"{indent}    guidance: {item.importer_guidance}")
    return lines


def _operation_lines(operation: Operation, diagnostics: tuple[Diagnostic, ...]) -> list[str]:
    lines = [
        (
            f"- [{operation.status.value}] operation {operation.label!r} "
            f"(sequence {operation.sequence}, kind {operation.kind}, id {operation.id})"
        ),
        f"    cannot perform: {_reason(operation.kind, operation.status)}",
    ]
    lines.extend(_diagnostic_lines(diagnostics, operation.id))
    return lines


def _entity_lines(
    collection: str, record: EntityRecord, diagnostics: tuple[Diagnostic, ...]
) -> list[str]:
    label = _property(record.properties, "label")
    lines = [
        (f"- [{record.status.value}] {collection} {label!r} (kind {record.kind}, id {record.id})"),
        f"    cannot perform: {_reason(record.kind, record.status)}",
    ]
    lines.extend(_diagnostic_lines(diagnostics, record.id))
    return lines


def fidelity_log_text(document: ModelDocument, destination: Path) -> str:
    """Build a detailed, stable explanation of every degraded coverage record."""
    coverage = document.coverage
    lines = [
        "Export problems and unavailable actions",
        f"model: {destination}",
        (
            "problem counts: "
            f"fallback={coverage.complete_with_fallback} "
            f"approximated={coverage.approximated} "
            f"unclassified={coverage.unclassified}"
        ),
        "",
    ]
    degraded_count = 0
    for operation in document.operations:
        if operation.status in DEGRADED_STATUSES:
            degraded_count += 1
            lines.extend(_operation_lines(operation, document.diagnostics))
    for collection, records in (
        ("resources", document.resources),
        ("results", document.results),
        ("relationships", document.relationships),
        ("configurations", document.configurations),
    ):
        for record in records:
            if record.status in DEGRADED_STATUSES:
                degraded_count += 1
                lines.extend(_entity_lines(collection, record, document.diagnostics))
    if degraded_count == 0:
        lines.append("No export problems were reported.")
    lines.append("")
    return "\n".join(lines)


def write_fidelity_log_atomic(document: ModelDocument, destination: Path) -> Path:
    """Atomically write the companion fidelity log and return its path."""
    log_path = fidelity_log_path(destination)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{log_path.name}.", suffix=".temporary", dir=log_path.parent
    )
    temporary = log_path.parent / temporary_name
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(fidelity_log_text(document, destination))
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(log_path)
    except BaseException:
        with suppress(OSError):
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
        raise
    return log_path
