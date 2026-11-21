# Architecture

## Purpose

Mekatrol Model Exporter is a finite, user-triggered Fusion script. It reads the active
parametric design into an immutable, product-neutral model graph, validates that graph, seals it
with a canonical SHA-256 digest, and atomically writes JSON. The exported file is data only; it
never contains executable code.

The exporter is a capture system, not a lowest-common-denominator converter. Unsupported or
partially decoded source features remain ordered records with evaluated-result context and
machine-readable diagnostics. Destination-specific compromises belong in importers.

## Boundaries and data flow

```text
host entry point
    -> source adapter
    -> immutable domain records
    -> graph and finite-number validation
    -> deterministic serialization and integrity seal
    -> sibling temporary file
    -> atomic destination replacement
```

- `MekatrolModelExporter.py` is the host-required `run(context)` entry module.
- `entrypoint.py` owns dialogs, progress, cancellation, and the top-level exception boundary.
- `adapters/source_application/` is the only package that translates host API objects and names.
- `application/` orchestrates capture without depending on host types.
- `domain/` defines immutable, host-independent records.
- `infrastructure/` validates the graph and serializes it deterministically.

Host objects must not escape the adapter. IDs are allocated before cross-references are emitted.
Labels are metadata and never identity.

## Interchange contract

The authoritative JSON Schema 2020-12 document is `schema/model.schema.json`. Version `1.1.0`
contains document metadata, coordinate and unit conventions, parameters, reusable definitions,
instances, construction geometry, ordered operations, evaluated results, relationships,
configurations, diagnostics, coverage, and integrity data.

The interchange vocabulary uses general modelling terms. Product names, API class names, source
enum spellings, transient source tokens, and vendor namespaces may not appear in JSON fields,
values, diagnostics, IDs, or schema definitions. Stable neutral IDs replace source identities.

Storage conventions are right-handed coordinates, millimetres, radians, sRGB colour, finite
numbers, and a declared tolerance. The source API stores linear database values in centimetres;
the adapter converts parameter lengths, body bounds, and transform translations to millimetres.
Unrecognized parameter dimensions are retained with `unresolved` units and an explicit
diagnostic rather than being silently mislabelled.

Serialization is UTF-8 and deterministic. Object keys are sorted and compact JSON is used by
default. The integrity hash is SHA-256 over the canonical document with an empty hash field and
the final collection counts. `docs/importer-guide.md` defines version negotiation, hash
verification, replay order, selection resolution, fallback handling, and migration policy.

## Fidelity model

Every status is a statement about captured information, not whether the write succeeded:

- `exact`: the typed record contains the complete available representation.
- `complete_with_fallback`: identity and useful structure are retained, but some typed detail is
  represented through evaluated or generic data.
- `approximated`: the representation is intentionally approximate.
- `unclassified`: the entity remains ordered and identifiable but has no known neutral type.

The current adapter captures hierarchy, transforms, parameters and opaque expressions, parameter
dependencies, analytic sketch curves, neutral constraints and dimensions, operation order and
neutral classifications, available editable operation quantities, evaluated body bounds/topology
counts and triangle meshes, visual assignments, joint endpoints, and configuration identity.
History operations do not yet expose complete selection intent for every subtype, and body results
do not contain complete analytic/NURBS boundary representation. Those records therefore retain an
explicit degraded status. An unrecognized history entity becomes `unclassified_operation` with
`capture.operation_unclassified`.

Each committed model has a companion `.log` exception report. It contains only fallback,
approximated, or unclassified records and explains the unavailable capability and related
diagnostics. The completion dialog reports both output paths.

This explicit limitation is part of the contract: a schema-valid export can be complete as a
snapshot while still reporting degraded reconstruction fidelity.

## Validation and commit semantics

Before commit, `CaptureService` checks cancellation, computes integrity data, rejects non-finite
numbers, duplicate IDs, unresolved references, and a mismatched digest. JSON encoding additionally
rejects NaN and infinity. The writer creates a temporary file beside the destination, flushes and
syncs it, and replaces the destination only after the snapshot is complete. A cancellation before
commit does not replace the destination; a failed write removes its temporary file.

The installer stages and validates the complete runtime tree. When replacing an existing install,
it temporarily renames the prior folder, moves the staged folder into place, and restores the prior
folder if installation fails before the new folder is committed. It never targets the surrounding
Scripts directory.

## Evolution rules

Additive contract fields require a minor version. Removed fields or changed meanings require a
major version. Exporters write one version; importers declare supported ranges. New capture work
should be implemented as small typed readers registered by neutral operation type. A reader must
return either a complete typed record or a diagnostic fallback; it must not partially populate a
record marked exact.

Priority areas for deeper fidelity are exact sketch curves and constraints, typed operation
parameters and selection intent, analytic/NURBS topology, mass properties and tessellation,
kinematic degrees of freedom, complete appearance channels, and configuration rules. Manufacturing,
drawing, simulation, and electronics data should become separate schema modules rather than being
mixed into the modelling contract.

## Quality gates

Python targets the host's embedded Python 3.14 and must remain strongly typed. Host imports are
limited to the entry point and source adapter. Do not add blanket `Any`, wildcard imports, broad
suppressions, or test frameworks. Before a change is complete, run:

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe .\scripts\validate_contract.py
```

Pylance must report no warnings or errors in changed Python files. Development-only declarations
for unavailable host APIs live under `typings/adsk`; refine those stubs instead of weakening type
checking.

Manual smoke coverage is documented in `docs/manual-smoke-models.md`. It includes feature breadth,
repetition, advanced construction, nested assemblies, visual assignments, configurations,
unsupported features, cancellation, and destination preservation.
