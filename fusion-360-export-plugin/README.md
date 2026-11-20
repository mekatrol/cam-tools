# Mekatrol Model Exporter

This repository is building a product-neutral, versioned model exporter for Autodesk Fusion.
The current completed milestone is a runnable **MekatrolModelExporter** Hello World
script and its development/deployment baseline.

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

Milestone A (setup phase) is complete. The neutral contract and extraction phases in
`PLAN.md` remain future work.
