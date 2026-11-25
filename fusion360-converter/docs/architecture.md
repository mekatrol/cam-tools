# Architecture

The intended boundaries are source decoding (`src/source`), the owned source model (`src/model`), migration planning and sessions (`src/migration`), MCP transport (`src/mcp`), and target-specific mappings (`src/backends`). Tests and redistributable fixtures belong under `tests`.

These directories are reserved for future working implementations. The detailed requirements and safety constraints are in AGENTS.md.
