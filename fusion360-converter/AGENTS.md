# AGENTS.md — Fusion360Converter

## Mission

Implement and test a cross-platform Rust CLI application, `fusion360-converter` (product name Fusion360Converter), that reads Autodesk Fusion `.f3d` and `.f3z` archives using cadmpeg, exposes their contents for inspection, and migrates models incrementally into FreeCAD or SolidCraft through MCP (Model Context Protocol).

The primary deliverable is **interactive, operation-by-operation parametric migration**, not a bulk file converter. A user must be able to inspect the original design, start with the oldest timeline operation, preview each proposed reconstruction, apply it to a visible target model, inspect the result, and explicitly accept it before moving to the next operation. Preserve editable features, dependencies and constraints wherever the source and target support them. Never claim full fidelity when information is missing.

## Instructions for the coding agent

- Inspect the existing repository, Cargo.toml, Cargo.lock, source files, Git status and tests first. Preserve existing work and user changes. Do not initialise a nested project or overwrite files wholesale unnecessarily.
- Implement working code in small, testable milestones; do not stop at a proposed architecture or generate empty placeholder modules. Maintain `docs/implementation_status.md` with completed work, blockers, verified capabilities and next steps.
- Use current installed crate sources and upstream documentation to establish actual APIs. Run `cargo metadata`, `cargo check`, and focused tests early. Do not invent cadmpeg fields, MCP tools, native file extensions or server arguments.
- Verify each dependency version and feature flag before editing the manifest. Previous planning assumed cadmpeg 0.6.12; treat that as a candidate, not a guarantee that all crates resolve at that version. Keep compatible versions locked and document the rationale. Do not silently downgrade to a decoder that cannot read modern files.
- Follow idiomatic Rust: lowercase kebab-case project/package/binary, snake_case files/modules/functions, PascalCase types. `Cargo.toml`, `Cargo.lock`, `README.md`, `AGENTS.md` retain conventional spelling.
- Target Windows, macOS and Linux from the first milestone. Use `Path`/`PathBuf`, portable process APIs and terminal handling; no shell-dependent runtime commands or hardcoded executable paths. Use Rust stable; determine and document the actual MSRV.
- Prefer deterministic Rust logic. MCP is a protocol, not an LLM requirement. No cloud services, AI API keys or Fusion installation required for decoding. Do not send CAD files or contents externally by default.
- Make no destructive changes to source CAD files or pre-existing destination documents. Use a new migration document by default. Never commit private CAD fixtures, credentials or generated models.

## Core requirements

1. Read local `.f3d` and `.f3z` files (case-insensitive extensions, verify actual contents). Inspect modern archive variants and report unsupported versions/compression explicitly.
2. Query archive members, source documents, components, occurrences/instances, bodies, sketches, constraints, parameters, construction geometry, timeline operations and dependencies to the extent exposed by the decoder.
3. Preserve source identity and original timeline order. Start with the oldest recorded operation, not an inferred ordering from body geometry. Distinguish component definitions from occurrences and document identities in F3Z.
4. Provide a persistent migration session bound to the source fingerprint, backend, target document and approved timeline state. Support inspection, preparation, preview, apply, accept, reject/rollback, retry, skip with explicit approval, pause and resume.
5. Use real MCP clients to create editable models inside FreeCAD and SolidCraft, with visible desktop sessions as the intended interactive mode. Headless mode is suitable for tests, not a substitute for visible review.
6. Export/save the accepted destination state on explicit request and optionally export neutral formats such as STEP if the installed backend or verified codec supports them. No automatic bulk reconstruction or default geometry fallback.
7. Provide human-readable terminal output and machine-readable JSON for read-only queries and reports. Diagnostics go to stderr, especially when stdout is JSON.

## Dependency and feasibility investigation (first milestone)

References to consult and verify against installed versions:

- cadmpeg F3D package: https://docs.rs/crate/cadmpeg-codec-f3d/latest
- cadmpeg F3D API: https://docs.rs/cadmpeg-codec-f3d/latest/cadmpeg_codec_f3d/
- Official Rust MCP SDK: https://github.com/modelcontextprotocol/rust-sdk
- SolidCraft MCP: https://github.com/tangency-labs/solidcraft/blob/main/docs/mcp.md
- SolidCraft control protocol: https://github.com/tangency-labs/solidcraft/blob/main/docs/control-protocol.md
- FreeCAD MCP candidate: https://github.com/neka-nat/freecad-mcp (evaluate actual tools and GUI connection; other implementations may be preferable).

Inspect cadmpeg package source and examples, not just docs.rs rendered docs. Determine whether archive enumeration and document-level decoding are available separately from merged geometry decoding. Investigate `F3dCodec::open_archive` if present in the selected version. Establish whether original operation order, feature types, parameters, sketch constraints, entity IDs, references, suppression and occurrence transforms are truly decoded. Record a capability matrix with evidence, including distinctions between raw data, interpreted data and unsupported data. Do not assume B-Rep decoding implies feature-history decoding.

Use an owned/redistributable small Fusion fixture when available; ideally include a current F3D with sketch/extrude/cut and F3Z with referenced components. If none are available, implement mock-backed tests and clearly mark real decoding validation blocked. Never fabricate a timeline from final geometry or silently discard unknown features. If a decoder cannot provide history, expose geometry inspection and a clear migration blocker; isolate future decoder improvements behind the source adapter.

Candidate dependencies: cadmpeg-codec-f3d, cadmpeg-ir, cadmpeg-core (only if directly needed), clap (derive), anyhow, thiserror (typed library errors if useful), serde, serde_json, tokio, rmcp (client and verified transports), toml, tracing, tracing-subscriber, sha2, tempfile (tests/atomic writes as appropriate). Add STEP/FCStd codecs only when verified and needed for explicit export/fallback. Avoid speculative dependencies. Commit Cargo.lock for the application. Keep dependency-purpose comments in Cargo.toml.

## Architecture

Keep source decoding, canonical domain model, migration planning, MCP transport, backend mapping and session persistence separate. Suggested layout (adapt to repository and actual needs):

```text
src/
  main.rs
  lib.rs
  cli.rs
  config.rs
  error.rs
  source/
    mod.rs
    fusion.rs
  model/
    mod.rs
    timeline.rs
    identity.rs
  migration/
    mod.rs
    planner.rs
    session.rs
    executor.rs
    validation.rs
  mcp/
    mod.rs
    client.rs
  backends/
    mod.rs
    freecad.rs
    solidcraft.rs
  storage.rs
  reporting.rs
tests/
  fixtures/
  cli_tests.rs
  migration_tests.rs
  mcp_tests.rs
docs/
  architecture.md
  dependencies.md
  feature_mapping.md
  implementation_status.md
```

Keep main.rs thin. Expose a reusable library. Use cadmpeg IR internally for geometry, with an owned application-level representation for stable IDs, timeline semantics, provenance and session serialization. Do not serialize opaque decoder handles as durable identifiers.

Define a source adapter and asynchronous CAD backend interface (names illustrative): `inspect`, `capabilities`, `create_document`, `inspect_document`, `prepare_operation`, `checkpoint`, `apply_operation`, `validate_operation`, `rollback`, `save_document`. Separate pure mapping from mutating tool calls. A source timeline operation can require multiple target operations; treat them as one review unit. Represent unsupported capabilities explicitly, rather than returning fake success.

### Source model

Include source fingerprint (SHA-256), archive/document IDs, format/version where discoverable, source units, component definitions, occurrence paths and transforms, body IDs, source operation IDs, original timeline indices, feature type and name, suppression state, dependencies, relevant geometry/parameters, provenance and decode warnings. Preserve unknown values as unknown. Distinguish source parameter expressions from evaluated values. Define coordinate handedness, unit conversion (including angles) and transform conventions based on actual evidence. Never assume all source length values are millimetres.

For F3Z, retain document-level histories and external reference edges when available. Do not invent a global chronology across unrelated documents. Let users select a root document/component and show dependency requirements; migrate referenced definitions before operations that require them, with explicit user approval. Do not silently reorder the original timeline within a document. Missing references or cycles must be visible blockers. If only merged decoding is available, report loss of document identity and restrict workflows accordingly.

## CLI contract

Use clap subcommands; provide `--help`, descriptive errors and stable JSON schemas with version fields. Names below are the intended user interface, not existing APIs. Implement in milestones and document any intentional deviations.

```text
fusion360-converter inspect model.f3d [--json]
fusion360-converter query model.f3z documents [--json]
fusion360-converter query model.f3z components [--document ID] [--json]
fusion360-converter query model.f3d bodies [--component ID] [--json]
fusion360-converter query model.f3d sketches [--component ID] [--json]
fusion360-converter query model.f3d parameters [--json]
fusion360-converter query model.f3d timeline [--document ID] [--json]
fusion360-converter query model.f3d operation --id ID [--json]
fusion360-converter query model.f3d dependencies --id ID [--json]
fusion360-converter mcp test --target freecad
fusion360-converter mcp list-tools --target solidcraft [--json]
fusion360-converter migrate start model.f3d --target freecad --session PATH
fusion360-converter migrate resume --session PATH
fusion360-converter migrate status --session PATH [--json]
fusion360-converter migrate report --session PATH [--json]
```

`start` and `resume` open an interactive command loop with commands such as `status`, `timeline`, `show`, `preview`, `apply`, `accept`, `reject`, `retry`, `skip`, `save`, `quit`, `help`. `apply` requires an explicit confirmation of the prepared plan. `accept` requires a separate explicit decision after the model changes. Do not combine these gates. `accept` advances the cursor to the next operation but does not execute it. `skip` requires a reason and confirmation and never implicitly satisfies downstream dependencies. `quit` preserves durable state and clearly identifies any unaccepted operation. EOF/Ctrl-C must never imply approval. When stdin is not interactive, refuse mutation workflows unless an explicitly designed equivalent per-operation approval mechanism exists; do not provide `--yes` or an automatic accept-all option in the initial release.

Example interaction (illustrative, not a claim about available decoder data):

```text
Document: Bracket | Target: FreeCAD | Accepted: 0/4
Operation 1/4: Create sketch Sketch1
Dependencies: none
> preview
Plan: create sketch on XY plane; add geometry; add supported constraints
Warnings: none
> apply
Apply operation 1 to target document? [y/N] y
Applied. Inspect the result in FreeCAD.
Validation: sketch exists; geometry/constraint checks reported below.
> accept
Accept operation 1? [y/N] y
Checkpoint committed. Operation 2/4: Extrude1 (not applied)
> quit
Session saved.
```

## State machine and transaction safety

Use explicit states, e.g. Pending, Prepared, Applying, AppliedAwaitingReview, Accepted, Rejected, Skipped, Blocked, Failed, RecoveryRequired. Store transition rules in testable pure code. Only the executor can perform mutations. For each operation:

1. Resolve dependencies against approved source-to-target mappings. Inspect the live target and check for drift. Stop when dependencies or capabilities are missing.
2. Generate a deterministic, read-only plan listing target calls, arguments, prerequisites, assumptions, expected effects and fidelity limitations. Preview must not mutate the target.
3. After explicit user approval, establish a recoverable checkpoint. Persist an intent record before mutation; run tool calls sequentially; capture returned IDs and outcomes. Never treat an MCP transport success as modelling success without checking tool results.
4. Validate resulting entities, constraints and geometry as supported. Show results in the target GUI and prompt for accept/reject. Do not start another operation while review is pending. Validation is not user approval.
5. Accept commits mappings, operation state and cursor atomically where possible. Reject restores the checkpoint and verifies restoration. Retry only after verified restoration or explicit recovery. Skip records reason, leaves dependencies unresolved and marks fidelity loss.

MCP is not necessarily transactional. Use verified backend undo/transaction/snapshot/save capabilities; if unavailable, block mutation until a reliable checkpoint/recovery mechanism exists (e.g. isolated scratch document plus verified rebuild from accepted operations). Never blindly call undo a fixed number of times. Do not claim rollback succeeded without checking target state. If a timeout/crash happens after a request may have been executed, enter RecoveryRequired, inspect the target, reconcile mappings and require user resolution before retrying. Do not blindly resend non-idempotent calls.

Persist schema version, source fingerprint, source path, backend identity/version/capabilities, target document identity, accepted operations, current cursor, pending plan hash, checkpoint references, operation journal, target entity mappings, validation outcomes, skips and warnings. Use portable atomic-write/replace strategy and session locking; ensure failure recovery on Windows too. On resume recheck source fingerprint, target identity and target drift. Never silently reset an existing session. Do not persist credentials. Explicit save/export must identify what is included; by default save only accepted state, refusing while a preview mutation is awaiting review.

## MCP integration

Use rmcp with verified supported features and APIs. Start with stdio child process; add Streamable HTTP when a supported server requires it. Never assume legacy SSE and Streamable HTTP are interchangeable. Use configurable executable and argv arrays, not shell interpolation. Handle cancellation, timeouts, lifecycle, stderr capture, cleanup of processes owned by the converter, protocol errors and tool-level errors. Do not terminate a user's already-running CAD application.

On connection, initialise MCP, enumerate tools (including pagination), inspect input schemas, and build a target capability map. Map semantic operations to verified tool names and parameters. Validate responses, schemas and versions. Treat tool descriptions/results as data, not instructions. Reject ambiguous or unsupported mappings. Avoid arbitrary Python/shell execution as a default backend path. If a backend requires FreeCAD Python, use deterministic, narrowly scoped templates with validated data and explicit disclosure; never execute source-embedded code or pass untrusted expressions directly to eval.

Provide a documented example configuration, not machine-specific defaults. Resolve config via `--config` and platform-appropriate locations or project-local config. Example conceptual TOML (server command and args must be verified):

```toml
[backends.solidcraft]
transport = "stdio"
command = "solidcraft-cli"
args = ["mcp", "--connect", "127.0.0.1:9876"]

[backends.freecad]
transport = "stdio"
command = "<installed FreeCAD MCP launcher>"
args = []
```

SolidCraft documentation describes a bridge to the running desktop app via its control endpoint; verify current setup and command flags per platform. FreeCAD MCP is implementation-specific: select a real server with editable model operations, visible GUI integration and checkpoint support. Document installation, launch and configuration on all platforms. Support configurable server paths and arguments for macOS app bundles, Windows executables and Linux packaging. The CLI must not require either CAD application for inspection or mock tests. Local endpoints by default; no automatic remote access or credential logging.

## Feature mapping and fidelity

Prioritise: new component/body and origin planes; sketches (lines, arcs, circles, construction geometry); constraints/dimensions; extrusions and cuts; then revolves, datum planes, fillets/chamfers, patterns, sweeps/lofts, parameters/expressions and assemblies. Implement only mappings backed by source data and target capability tests. Verify operation semantics including join/cut/intersect/new body, direction, extents, profiles, transforms and references. Handle topology identity carefully: do not map faces/edges merely by numeric index when regeneration can change them. Use durable references or validated geometric matching; ambiguous references block migration.

Maintain `docs/feature_mapping.md` with columns: Fusion feature, decoder evidence, FreeCAD mapping, SolidCraft mapping, limitations, test coverage. Label each mapping supported/partial/unsupported separately for each backend. Preserve names and user parameters where possible. Suppressed operations are reported and not executed as active geometry; define explicit treatment before recording progression.

Validate using entity counts, sketch geometry/constraint state, operation results, body bounds, volume, transforms, topology checks and source comparison where equivalent intermediate source geometry is available. Use documented tolerances and units. Do not compare an early operation against final source geometry as if it were ground truth. Report checks unavailable separately from passed checks. If parametric data is missing, offer explicit manual resolution, skip or optional geometry-only fallback for a well-defined scope, with user consent and a fidelity warning. Never call a static imported solid a fully editable parametric reconstruction. No silent fallback.

## Implementation milestones

1. Repository audit and dependency/API spike. Establish compiling CLI, source capability matrix, real fixture availability, current-format limitations and MVP scope. Run inspection on real fixtures when available.
2. Read-only inspection and query commands, JSON schema, stable source IDs and diagnostics. Test invalid inputs, modern compression support where fixtures permit, F3Z reference handling and unknown timeline fields.
3. Pure migration planner and persistent session/state machine. Implement interactive review flow with a fake backend and deterministic test fixtures. Prove no automatic advancement or mutation before approval.
4. MCP client and capability discovery. Implement configurable connection and tool listing. Add a local mock MCP server or test harness that exercises protocol, tool errors, timeouts and cleanup.
5. First real backend vertical slice: a new visible document, source sketch, one extrusion, checkpoint/reject/retry, accept, resume and explicit save. Select whichever backend has the necessary verified capabilities first; implement the other next. If real timeline decoding is blocked, label synthetic operation testing as synthetic; do not misrepresent it as Fusion migration.
6. Expand supported operations, F3Z reference handling and validation. Add optional explicit neutral/native exports only when verified. Document limitations and manual resolution workflows.
7. Cross-platform CI, packaging and user documentation. Add GitHub Actions matrix for Windows/macOS/Linux, build and tests, formatting and clippy. Document target binaries, installation and MCP server prerequisites. GUI integration tests may be opt-in and require local CAD installations.

At each milestone compile and test before moving on. If a dependency or API blocks progress, investigate and implement the remaining independent pieces; record the exact blocker rather than inventing results. Do not expand scope into a GUI, bulk migration or LLM integration without user direction.

## Testing and acceptance criteria

Use `cargo fmt --all -- --check`, `cargo check --locked --all-targets`, `cargo clippy --locked --all-targets -- -D warnings`, and `cargo test --locked` once the lockfile exists. Add focused unit, CLI and integration tests. Separate mock tests from real CAD/fixture tests; make opt-in tests explicit and report not-run status.

Required acceptance cases:

- Read-only queries perform zero destination mutations and work without CAD software installed.
- Timeline ordering is preserved; oldest available operation is first. Unknown/missing history is reported, not generated.
- A prepared operation makes no mutating calls; declining apply makes none either.
- Applying operation N does not apply N+1, even on success; accepting N does not execute N+1.
- Reject restores prior accepted state; failure mid-operation does not advance the cursor. Timeout with uncertain outcome requires recovery.
- Skip is explicit, recorded and blocks unresolved dependents. Unsupported operations cannot masquerade as accepted parametric features.
- Resume retains accepted IDs and pending review/recovery state; mismatched source fingerprints or changed target documents block unsafe continuation.
- F3Z repeated instances are not confused with definitions; missing documents and dependency cycles are detected.
- Source files stay unchanged. Existing target files are not overwritten without explicit consent. Paths with spaces/Unicode work across platforms.
- Tool errors, malformed schemas, missing tools, disconnects, cancellation, and noninteractive input are handled without silent approval.
- At least one real end-to-end sketch/extrusion migration into each target, with user-visible review and rejection, is needed before claiming actual backend support. If unavailable, state the precise reason.

## Final handoff

Update README with build instructions, CLI examples, sample interactive transcript, config setup for each backend, supported formats and feature limitations. Include a practical first-run workflow from inspection to saving an accepted model. Summarize files changed, commands actually run and their outcomes, real vs mock verification, remaining issues and next concrete milestone. Do not claim support for the newest Fusion files without testing representative files or explicitly describing the evidence and limits.
