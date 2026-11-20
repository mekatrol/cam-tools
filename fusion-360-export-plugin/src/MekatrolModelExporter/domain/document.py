"""Top-level immutable neutral model document."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .diagnostics import Coverage, Diagnostic
from .types import CaptureStatus, JsonValue

if TYPE_CHECKING:
    from .expressions import Parameter
    from .geometry import GeometryRecord, Transform
    from .operations import Operation


@dataclass(frozen=True, slots=True)
class FormatInfo:
    """Interchange and generator versions."""

    name: str
    version: str
    generator_version: str


@dataclass(frozen=True, slots=True)
class DocumentInfo:
    """User-facing document metadata using ISO 8601 timestamps."""

    title: str
    description: str = ""
    created_at: str | None = None
    modified_at: str | None = None
    properties: tuple[tuple[str, JsonValue], ...] = ()


@dataclass(frozen=True, slots=True)
class Conventions:
    """Coordinate, unit, numeric, and colour conventions."""

    handedness: str = "right"
    length_unit: str = "millimetre"
    angle_unit: str = "radian"
    up_axis: str = "positive_z"
    forward_axis: str = "positive_y"
    numeric_precision: int = 17
    tolerance: float = 1e-6
    colour_encoding: str = "srgb"


@dataclass(frozen=True, slots=True)
class Definition:
    """Reusable model definition."""

    id: str
    label: str
    construction_ids: tuple[str, ...] = ()
    operation_ids: tuple[str, ...] = ()
    result_ids: tuple[str, ...] = ()
    properties: tuple[tuple[str, JsonValue], ...] = ()


@dataclass(frozen=True, slots=True)
class Instance:
    """Occurrence of a reusable definition in the assembly hierarchy."""

    id: str
    definition_id: str
    label: str
    transform: Transform
    parent_id: str | None = None
    visible: bool = True
    suppressed: bool = False
    grounded: bool = False
    quantity: int = 1


@dataclass(frozen=True, slots=True)
class EntityRecord:
    """Generic typed resource, result, or relationship record."""

    id: str
    kind: str
    status: CaptureStatus = CaptureStatus.EXACT
    properties: tuple[tuple[str, JsonValue], ...] = ()
    references: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Integrity:
    """Canonical content digest and declared collection counts."""

    algorithm: str = "sha256"
    canonical_hash: str = ""
    counts: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True, slots=True)
class ModelDocument:
    """Complete neutral graph captured before serialization."""

    format: FormatInfo
    document: DocumentInfo
    conventions: Conventions
    parameters: tuple[Parameter, ...] = ()
    resources: tuple[EntityRecord, ...] = ()
    definitions: tuple[Definition, ...] = ()
    instances: tuple[Instance, ...] = ()
    construction: tuple[GeometryRecord, ...] = ()
    operations: tuple[Operation, ...] = ()
    results: tuple[EntityRecord, ...] = ()
    relationships: tuple[EntityRecord, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    coverage: Coverage = field(default_factory=Coverage)
    integrity: Integrity = field(default_factory=Integrity)
