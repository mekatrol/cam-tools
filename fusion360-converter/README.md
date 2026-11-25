# Fusion360Converter

A read-only first step toward reviewed, operation-by-operation Fusion migration. Requires Rust 1.89 or newer for the currently locked dependencies (the minimum has not yet been tested on that toolchain).

```text
cargo build --locked
cargo run --locked -- inspect "path/to/model.f3d"
cargo run --locked -- inspect "path/to/assembly.f3z" --json
cargo run --locked -- inspect "path/to/model.f3d" --json --output "report.json"
```

The command decodes locally using cadmpeg; Fusion and a target CAD application are not required. It reports decoded product definitions, occurrences, root occurrences, bodies and sketches. Root occurrences are not a count of every kind of top-level Fusion object. Decoder losses are reported as warnings. JSON output has a schema version and includes warnings; errors go to stderr. Extensions are case-insensitive, and file contents are validated by the decoder.

F3Z model decoding merges documents, so counts do not preserve document identity. Counts can be incomplete where source data is unsupported. No real Fusion fixtures have been tested yet; current Fusion archive compatibility is unverified. Migration, timeline inspection, MCP and saving models are not implemented. See [implementation status](docs/implementation_status.md).

To investigate decoder messages individually, run:

```text
cargo run --locked -- diagnostics "path/to/model.f3d"
cargo run --locked -- diagnostics "path/to/model.f3d" --number 1
cargo run --locked -- diagnostics "path/to/model.f3d" --number 1 --json
```

Numbers identify positions in the current decode report and may change between runs or decoder versions. The listing includes informational notes as well as warnings. Each entry retains the cadmpeg code and any reported provenance; only investigated codes have a practical explanation. The original `inspect --json` schema remains unchanged. Application-level count limitations in that report are separate from decoder diagnostics.

Use `--json --output FILE` (or `--json -o FILE`) with either command to write JSON directly to a new file. Existing files are never overwritten. Without `--output`, JSON is printed to standard output, so shell redirection also works.
