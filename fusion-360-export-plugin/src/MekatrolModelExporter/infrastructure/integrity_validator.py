"""Validation of model graph identity, finiteness, counts, and integrity."""

from __future__ import annotations

import dataclasses
import math
from typing import TYPE_CHECKING, Protocol

from .json_writer import document_data

if TYPE_CHECKING:
    from collections.abc import Iterable

    from domain.document import ModelDocument


class _Identified(Protocol):
    @property
    def id(self) -> str: ...


class ModelValidationError(ValueError):
    """Raised when a model document violates the neutral contract."""


def _records(document: ModelDocument) -> Iterable[_Identified]:
    yield from document.parameters
    yield from document.resources
    yield from document.definitions
    yield from document.instances
    yield from document.construction
    yield from document.operations
    yield from document.results
    yield from document.relationships


def _check_finite(value: object, path: str = "document") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        message = f"Non-finite number at {path}"
        raise ModelValidationError(message)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for item in dataclasses.fields(value):
            _check_finite(getattr(value, item.name), f"{path}.{item.name}")
    elif isinstance(value, tuple):
        for index, item in enumerate(value):
            _check_finite(item, f"{path}[{index}]")


def validate_document(document: ModelDocument) -> None:
    """Raise a precise error if the neutral document graph is invalid."""
    _check_finite(document)
    records = tuple(_records(document))
    ids = [record.id for record in records]
    if len(ids) != len(set(ids)):
        message = "Entity identifiers must be unique across the document"
        raise ModelValidationError(message)
    known_ids = set(ids)
    references: list[tuple[str, str]] = []
    for definition in document.definitions:
        references.extend(
            (definition.id, item)
            for item in (
                *definition.construction_ids,
                *definition.operation_ids,
                *definition.result_ids,
            )
        )
    for instance in document.instances:
        references.append((instance.id, instance.definition_id))
        if instance.parent_id is not None:
            references.append((instance.id, instance.parent_id))
    for parameter in document.parameters:
        references.extend((parameter.id, item) for item in parameter.dependencies)
    for operation in document.operations:
        references.extend(
            (operation.id, item)
            for item in (*operation.inputs, *operation.outputs, *operation.target_bodies)
        )
    for geometry in document.construction:
        references.extend((geometry.id, item) for item in geometry.references)
    for record in (*document.resources, *document.results, *document.relationships):
        references.extend((record.id, item) for item in record.references)
    missing = [(owner, target) for owner, target in references if target not in known_ids]
    if missing:
        message = f"Unresolved reference {missing[0][1]!r} from {missing[0][0]!r}"
        raise ModelValidationError(message)
    data = document_data(document)
    calculated = data["integrity"]
    if document.integrity.canonical_hash and isinstance(calculated, dict):
        expected = calculated["canonical_hash"]
        if document.integrity.canonical_hash != expected:
            message = "Canonical content hash does not match the document"
            raise ModelValidationError(message)
