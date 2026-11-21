# Repository instructions

These rules apply to every file under this directory.

## Quality gates

- All Python code must conform to the Ruff configuration in `pyproject.toml`.
- Before completing a code change, run `ruff check .` and
  `ruff format --check .`; fix all findings rather than weakening rules.
- Before completing a code change, ensure Pylance reports no errors in changed
  Python files. Add or refine strongly typed, development-only stubs for
  unavailable host APIs instead of suppressing missing-import, unknown-type, or
  unknown-member diagnostics.
- Keep public and internal interfaces strongly typed. Do not add untyped public
  functions, blanket `Any`, wildcard imports, blanket `noqa`, or unchecked casts.
- Prefer immutable domain records, small single-purpose modules, explicit error
  types, and dependency inversion at application/API boundaries.
- Host-API imports are allowed only in the source-adapter and entry-point layers.
  Domain models, schema, serializers, and general validation must remain
  host-independent.
- Ensure Pylance checks also pass without warning or error.

## Interchange-format rules

- JSON field names, enum values, IDs, diagnostics, and schema definitions must
  use general modelling terminology. Do not expose product names, vendor names,
  source API class names, source enum spellings, or vendor namespaces.
- Do not limit captured data to features supported by a prospective destination.
  Destination limitations are importer migration concerns.
- Do not silently omit unsupported data. Preserve a neutral structured fallback,
  evaluated geometry where available, and an explicit fidelity diagnostic.
- Serialization must be deterministic, versioned, unit-explicit, finite-number
  checked, referentially valid, and data-only; never emit executable code.

## Scope rule for tests

- Do not create test classes at this stage.
- Do not introduce a test framework or automated test suite unless the user
  explicitly expands the scope. Use Ruff, schema checks, validation scripts, and
  documented manual smoke models for the current phase.

## Provenance and naming

- Implement original, purpose-built code and documentation. Do not copy code,
  comments, structure, namespaces, or nomenclature from external example
  projects.
- Do not mention external example repositories in project code, schema,
  documentation, comments, manifests, or generated files.
- Keep all source-application vocabulary behind the adapter boundary. The
  runtime entry point and deployment path may use the official host integration
  requirements, but the exported format may not.

