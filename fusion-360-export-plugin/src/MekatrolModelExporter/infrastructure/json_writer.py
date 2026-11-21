"""Deterministic JSON conversion and canonical integrity hashing."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import tempfile
from contextlib import suppress
from enum import Enum
from typing import TYPE_CHECKING

from ..domain.document import Integrity, ModelDocument
from ..domain.operations import Operation

if TYPE_CHECKING:
    from pathlib import Path

type JsonData = bool | int | float | str | list[JsonData] | dict[str, JsonData] | None
PROPERTY_ITEM_LENGTH = 2
MAPPING_FIELDS = frozenset({"counts", "properties"})


def _to_data(value: object, *, as_mapping: bool = False) -> JsonData:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _to_data(
                getattr(value, item.name),
                as_mapping=item.name in MAPPING_FIELDS
                or (isinstance(value, Operation) and item.name == "parameters"),
            )
            for item in dataclasses.fields(value)
        }
    if isinstance(value, Enum):
        return _to_data(value.value)
    if isinstance(value, tuple):
        is_property_map = as_mapping or (
            bool(value)
            and all(
                isinstance(item, tuple)
                and len(item) == PROPERTY_ITEM_LENGTH
                and isinstance(item[0], str)
                for item in value
            )
        )
        if is_property_map:
            return {item[0]: _to_data(item[1]) for item in value}
        return [_to_data(item) for item in value]
    if value is None or isinstance(value, bool | int | float | str):
        return value
    message = f"Unsupported serialization value: {type(value).__name__}"
    raise TypeError(message)


def canonical_bytes(data: JsonData) -> bytes:
    """Encode data using the format's deterministic canonical representation."""
    return json.dumps(
        data, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()


def document_data(document: ModelDocument) -> dict[str, JsonData]:
    """Convert a document and calculate its canonical content integrity."""
    raw = _to_data(document)
    if not isinstance(raw, dict):
        message = "A model document must serialize to an object"
        raise TypeError(message)
    counts: dict[str, JsonData] = {
        name: len(getattr(document, name))
        for name in (
            "parameters",
            "resources",
            "definitions",
            "instances",
            "construction",
            "operations",
            "results",
            "relationships",
            "configurations",
            "diagnostics",
        )
    }
    integrity_free = dict(raw)
    integrity_free["integrity"] = {"algorithm": "sha256", "canonical_hash": "", "counts": counts}
    digest = hashlib.sha256(canonical_bytes(integrity_free)).hexdigest()
    raw["integrity"] = {"algorithm": "sha256", "canonical_hash": digest, "counts": counts}
    return raw


def with_integrity(document: ModelDocument) -> ModelDocument:
    """Return a document carrying the canonical hash and collection counts."""
    data = document_data(document)["integrity"]
    if not isinstance(data, dict):
        message = "Generated integrity value is invalid"
        raise TypeError(message)
    counts = data["counts"]
    digest = data["canonical_hash"]
    if not isinstance(counts, dict) or not isinstance(digest, str):
        message = "Generated integrity fields are invalid"
        raise TypeError(message)
    integer_counts: list[tuple[str, int]] = []
    for name, value in counts.items():
        if not isinstance(value, int) or isinstance(value, bool):
            message = f"Generated integrity count {name!r} is invalid"
            raise TypeError(message)
        integer_counts.append((name, value))
    integrity = Integrity(canonical_hash=digest, counts=tuple(integer_counts))
    return dataclasses.replace(document, integrity=integrity)


def write_json(document: ModelDocument, destination: Path, *, indented: bool = False) -> None:
    """Write deterministic UTF-8 JSON to an explicit destination."""
    data = document_data(document)
    text = json.dumps(
        data,
        allow_nan=False,
        ensure_ascii=False,
        indent=2 if indented else None,
        separators=None if indented else (",", ":"),
        sort_keys=True,
    )
    destination.write_text(f"{text}\n", encoding="utf-8", newline="\n")


def write_json_atomic(
    document: ModelDocument, destination: Path, *, indented: bool = False
) -> None:
    """Write beside the destination and atomically replace it after a successful flush."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".temporary", dir=destination.parent
    )
    temporary = destination.parent / temporary_name
    try:
        data = document_data(document)
        text = json.dumps(
            data,
            allow_nan=False,
            ensure_ascii=False,
            indent=2 if indented else None,
            separators=None if indented else (",", ":"),
            sort_keys=True,
        )
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(f"{text}\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(destination)
    except BaseException:
        with suppress(OSError):
            os.close(descriptor)
        temporary.unlink(missing_ok=True)
        raise
