# Implementation status

The repository currently contains the initial Rust binary and the planned directory structure. The binary prints `Hello, world!`; inspection, migration, and MCP integration are not implemented.

- Verified locally: `cargo metadata --format-version 1 --no-deps`, `cargo check`, and `cargo test` succeed. There are currently no tests.
- No Fusion fixtures are present. Real decoding and backend migration have not been validated.
- Dependency APIs, supported archive variants, backend capabilities, and the actual minimum supported Rust version have not yet been investigated.

Next: complete the dependency and API investigation described in AGENTS.md, then implement and test the first read-only inspection milestone.
