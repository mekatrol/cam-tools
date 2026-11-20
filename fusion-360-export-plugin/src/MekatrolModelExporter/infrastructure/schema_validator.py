"""Small dependency-free validator for the schema keywords used by this format."""

from __future__ import annotations

import re
from typing import Never

type JsonValue = bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None


class SchemaValidationError(ValueError):
    """Raised when JSON data does not satisfy the model schema."""


def _matches_type(value: JsonValue, expected: str) -> bool:
    result = False
    match expected:
        case "null":
            result = value is None
        case "boolean":
            result = isinstance(value, bool)
        case "integer":
            result = isinstance(value, int) and not isinstance(value, bool)
        case "number":
            result = isinstance(value, int | float) and not isinstance(value, bool)
        case "string":
            result = isinstance(value, str)
        case "array":
            result = isinstance(value, list)
        case "object":
            result = isinstance(value, dict)
        case _:
            result = False
    return result


def _fail(path: str, detail: str) -> Never:
    message = f"{path}: {detail}"
    raise SchemaValidationError(message)


def validate_json(data: JsonValue, schema: JsonValue) -> None:
    """Validate JSON data against the supported JSON Schema 2020-12 subset."""
    if not isinstance(schema, dict):
        _fail("$", "schema must be an object")
    definitions = schema.get("$defs", {})
    if not isinstance(definitions, dict):
        _fail("$.$defs", "must be an object")
    _validate(data, schema, schema, "$", definitions)


def _validate(
    value: JsonValue,
    rule: dict[str, JsonValue],
    root: dict[str, JsonValue],
    path: str,
    definitions: dict[str, JsonValue],
) -> None:
    if _validate_indirection(value, rule, root, path, definitions):
        return
    _validate_scalar_keywords(value, rule, path)
    if isinstance(value, list):
        _validate_array(value, rule, root, path, definitions)
    if isinstance(value, dict):
        _validate_object(value, rule, root, path, definitions)


def _validate_indirection(
    value: JsonValue,
    rule: dict[str, JsonValue],
    root: dict[str, JsonValue],
    path: str,
    definitions: dict[str, JsonValue],
) -> bool:
    reference = rule.get("$ref")
    if isinstance(reference, str):
        prefix = "#/$defs/"
        if not reference.startswith(prefix) or reference[len(prefix) :] not in definitions:
            _fail(path, f"unsupported reference {reference!r}")
        target = definitions[reference[len(prefix) :]]
        if not isinstance(target, dict):
            _fail(path, "referenced schema must be an object")
        _validate(value, target, root, path, definitions)
        return True
    options = rule.get("oneOf")
    if isinstance(options, list):
        matches = 0
        for option in options:
            if not isinstance(option, dict):
                continue
            try:
                _validate(value, option, root, path, definitions)
            except SchemaValidationError:
                continue
            matches += 1
        if matches != 1:
            _fail(path, f"must match exactly one alternative; matched {matches}")
        return True
    return False


def _validate_scalar_keywords(value: JsonValue, rule: dict[str, JsonValue], path: str) -> None:
    expected = rule.get("type")
    accepted_types = [expected] if isinstance(expected, str) else expected
    if isinstance(accepted_types, list) and not any(
        isinstance(item, str) and _matches_type(value, item) for item in accepted_types
    ):
        _fail(path, f"has unexpected type {type(value).__name__}")
    if "const" in rule and value != rule["const"]:
        _fail(path, f"must equal {rule['const']!r}")
    enum = rule.get("enum")
    if isinstance(enum, list) and value not in enum:
        _fail(path, f"must be one of {enum!r}")
    if isinstance(value, str):
        pattern = rule.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            _fail(path, f"does not match {pattern!r}")
    if isinstance(value, int | float) and not isinstance(value, bool):
        minimum = rule.get("minimum")
        if isinstance(minimum, int | float) and value < minimum:
            _fail(path, f"must be at least {minimum}")


def _validate_array(
    value: list[JsonValue],
    rule: dict[str, JsonValue],
    root: dict[str, JsonValue],
    path: str,
    definitions: dict[str, JsonValue],
) -> None:
    minimum = rule.get("minItems")
    maximum = rule.get("maxItems")
    if isinstance(minimum, int) and len(value) < minimum:
        _fail(path, f"must contain at least {minimum} items")
    if isinstance(maximum, int) and len(value) > maximum:
        _fail(path, f"must contain at most {maximum} items")
    if rule.get("uniqueItems") is True and len({repr(item) for item in value}) != len(value):
        _fail(path, "must contain unique items")
    item_rule = rule.get("items")
    if isinstance(item_rule, dict):
        for index, item in enumerate(value):
            _validate(item, item_rule, root, f"{path}[{index}]", definitions)


def _validate_object(
    value: dict[str, JsonValue],
    rule: dict[str, JsonValue],
    root: dict[str, JsonValue],
    path: str,
    definitions: dict[str, JsonValue],
) -> None:
    required = rule.get("required", [])
    if isinstance(required, list):
        missing = [item for item in required if isinstance(item, str) and item not in value]
        if missing:
            _fail(path, f"is missing required property {missing[0]!r}")
    properties = rule.get("properties", {})
    properties = properties if isinstance(properties, dict) else {}
    additional = rule.get("additionalProperties", True)
    for name, item in value.items():
        property_rule = properties.get(name)
        if isinstance(property_rule, dict):
            _validate(item, property_rule, root, f"{path}.{name}", definitions)
        elif additional is False:
            _fail(path, f"contains unknown property {name!r}")
        elif isinstance(additional, dict):
            _validate(item, additional, root, f"{path}.{name}", definitions)
