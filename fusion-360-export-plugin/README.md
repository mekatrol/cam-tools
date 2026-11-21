# Mekatrol Model Exporter

This repository is building a product-neutral, versioned model exporter for Autodesk Fusion.
The developer baseline, version 1.1.0 neutral interchange contract, typed broad-capture
pipeline, atomic export workflow, and importer hand-off contract are complete.

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

## Current scope

Milestones A through E are complete. The repository provides immutable typed records in `domain`,
the JSON Schema 2020-12 contract at `schema/model.schema.json`, an authored minimal example,
deterministic JSON serialization, and graph/integrity validation. Source-model extraction
plus typed readers for hierarchy, parameters, sketches, common history operations, and evaluated
body summaries. The breadth phase adds advanced operation classification, visual assignments,
kinematic relationships, configurations, explicit fallbacks, and coverage reporting.

Importer implementers should start with `docs/importer-guide.md`. It defines version negotiation,
canonical integrity verification, replay ordering, selection resolution, fallback handling,
fidelity metrics, and migration diagnostics alongside the authoritative JSON Schema.

Run the contract gate with:

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_contract.py
```

The gate validates the example against the schema, verifies collection counts and the
canonical SHA-256 digest, and audits domain/schema vocabulary for source-specific terms.
