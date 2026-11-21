# Mekatrol Model Exporter

This repository provides a product-neutral, versioned model exporter for Autodesk Fusion. It is a
finite script: choose a JSON destination, capture the active parametric design, validate the model
graph, and atomically write the result. Cancellation or capture failure does not replace the
destination.

## Development setup

Install CPython 3.14 with the Windows `py` launcher, then run `.\scripts\bootstrap.ps1`.
The plugin has no third-party runtime dependencies; `.venv` is not deployed into Fusion.

## Install and run

Preview with `.\scripts\install-plugin.ps1 -WhatIf`, then install with
`.\scripts\install-plugin.ps1`. In Fusion, open **Utilities > Scripts and Add-Ins**, select
**MekatrolModelExporter**, and click **Run**. Choose a JSON destination. The exporter reports
progress, supports cancellation, validates the complete graph, and atomically replaces the
destination only after a successful capture and flushed write.

For an isolated install check, pass `-DestinationRoot <folder>`.

## Export contract

The repository provides immutable typed records, a JSON Schema 2020-12 contract at
`schema/model.schema.json`, deterministic serialization, referential validation, canonical SHA-256
integrity, progress/cancellation, and an atomic writer. Capture includes hierarchy, parameters and
dependencies, sketch summaries, ordered history classification, evaluated body summaries, visual
assignments, joint endpoints, and configurations.

The exporter reports fidelity honestly. Construction records include analytic sketch curves,
neutral constraints and dimensions. Recognized history features include available editable
quantities, and evaluated bodies include tolerance-bounded indexed triangle meshes. Full analytic
boundary representation and every feature subtype are not yet decoded completely, so affected
records retain an explicit degraded status and diagnostic. A successful write does not imply exact
parametric reconstruction.

Every successful export also writes a human-readable `<model-name>.log` beside the JSON. The log
contains only degraded or unsupported records and explains the capability that could not be
exported, together with associated diagnostic guidance.

Importer implementers should start with `docs/importer-guide.md`. It defines version negotiation,
canonical integrity verification, replay ordering, selection resolution, fallback handling,
fidelity metrics, and migration diagnostics alongside the authoritative JSON Schema.

See `ARCHITECTURE.md` for boundaries, units, capture semantics, commit guarantees, known fidelity
limits, and evolution rules. Manual host checks are in `docs/manual-smoke-models.md`.

Run the contract gate with:

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_contract.py
```

The gate validates the example against the schema, verifies collection counts and the
canonical SHA-256 digest, and audits domain/schema vocabulary for source-specific terms.

Also run `ruff check .` and `ruff format --check .`, and confirm Pylance has no warnings or errors
in changed Python files.
