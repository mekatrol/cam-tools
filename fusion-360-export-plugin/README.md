# Mekatrol Model Exporter

This repository is building a product-neutral, versioned model exporter for Autodesk Fusion.
The developer baseline and the version 1.0.0 neutral interchange contract are complete. The
runnable **MekatrolModelExporter** remains a Hello World script until core capture is added.

## Development setup

Install CPython 3.14 with the Windows `py` launcher, then run `.\scripts\bootstrap.ps1`.
The plugin has no third-party runtime dependencies; `.venv` is not deployed into Fusion.

## Install and run

Preview with `.\scripts\install-plugin.ps1 -WhatIf`, then install with
`.\scripts\install-plugin.ps1`. In Fusion, open **Utilities > Scripts and Add-Ins**, select
**MekatrolModelExporter**, and click **Run**. It displays
**Hello World from Mekatrol** and exits without retaining handlers or host objects.

For an isolated install check, pass `-DestinationRoot <folder>`.

## Current scope

Milestones A and B are complete. Milestone B provides immutable typed records in `domain`,
the JSON Schema 2020-12 contract at `schema/model.schema.json`, an authored minimal example,
deterministic JSON serialization, and graph/integrity validation. Source-model extraction
remains future work.

Run the contract gate with:

```powershell
.\.venv\Scripts\python.exe .\scripts\validate_contract.py
```

The gate validates the example against the schema, verifies collection counts and the
canonical SHA-256 digest, and audits domain/schema vocabulary for source-specific terms.
