"""Validate authored examples and audit the neutral interchange vocabulary."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import Protocol, runtime_checkable

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "MekatrolModelExporter"
sys.path.insert(0, str(SOURCE_ROOT))

type JsonValue = bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None


@runtime_checkable
class _JsonWriterModule(Protocol):
    @staticmethod
    def canonical_bytes(data: JsonValue) -> bytes: ...


@runtime_checkable
class _SchemaValidatorModule(Protocol):
    @staticmethod
    def validate_json(data: JsonValue, schema: JsonValue) -> None: ...


def _load_modules() -> tuple[_JsonWriterModule, _SchemaValidatorModule]:
    writer = importlib.import_module("infrastructure.json_writer")
    validator = importlib.import_module("infrastructure.schema_validator")
    if not isinstance(writer, _JsonWriterModule):
        message = "JSON writer module does not provide the expected interface"
        raise TypeError(message)
    if not isinstance(validator, _SchemaValidatorModule):
        message = "Schema validator module does not provide the expected interface"
        raise TypeError(message)
    return writer, validator


FORBIDDEN_TERMS = ("autodesk", "fusion", "adsk", "mekatrol")
AUDITED_PATHS = (
    REPOSITORY_ROOT / "schema" / "model.schema.json",
    REPOSITORY_ROOT / "examples" / "minimal-model.json",
    REPOSITORY_ROOT / "docs" / "importer-guide.md",
    *(SOURCE_ROOT / "domain").glob("*.py"),
)


def _load_json(path: Path) -> dict[str, JsonValue]:
    value = _normalize_json(json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(value, dict):
        message = f"Expected a JSON object in {path}"
        raise TypeError(message)
    return value


def _normalize_json(value: object) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, list):
        return [_normalize_json(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                message = "JSON object keys must be strings"
                raise TypeError(message)
            normalized[key] = _normalize_json(item)
        return normalized
    message = f"Unsupported decoded JSON value: {type(value).__name__}"
    raise TypeError(message)


def _validate_hash(example: dict[str, JsonValue], writer: _JsonWriterModule) -> None:
    integrity = example.get("integrity")
    if not isinstance(integrity, dict):
        message = "Example integrity must be an object"
        raise TypeError(message)
    declared = integrity.get("canonical_hash")
    integrity["canonical_hash"] = ""
    calculated = hashlib.sha256(writer.canonical_bytes(example)).hexdigest()
    integrity["canonical_hash"] = declared
    if declared != calculated:
        message = f"Example canonical hash is stale; expected {calculated}"
        raise ValueError(message)


def _validate_counts(example: dict[str, JsonValue]) -> None:
    integrity = example.get("integrity")
    if not isinstance(integrity, dict):
        message = "Example integrity must be an object"
        raise TypeError(message)
    counts = integrity.get("counts")
    if not isinstance(counts, dict):
        message = "Example integrity counts must be an object"
        raise TypeError(message)
    for name, declared in counts.items():
        collection = example.get(name)
        if not isinstance(collection, list) or declared != len(collection):
            message = f"Integrity count for {name!r} does not match its collection"
            raise ValueError(message)


def _audit_vocabulary() -> None:
    for path in AUDITED_PATHS:
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            if term in content:
                relative_path = path.relative_to(REPOSITORY_ROOT)
                message = f"Forbidden interchange term {term!r} in {relative_path}"
                raise ValueError(message)


def main() -> None:
    """Validate the schema, examples, integrity hash, and neutral terminology."""
    schema = _load_json(REPOSITORY_ROOT / "schema" / "model.schema.json")
    example = _load_json(REPOSITORY_ROOT / "examples" / "minimal-model.json")
    writer, validator = _load_modules()
    validator.validate_json(example, schema)
    _validate_hash(example, writer)
    _validate_counts(example)
    _audit_vocabulary()
    sys.stdout.write(
        "Contract validation passed: 1 example; schema and terminology audit complete\n"
    )


if __name__ == "__main__":
    main()
