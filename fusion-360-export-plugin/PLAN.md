# Mekatrol product-neutral parametric model exporter: implementation plan

> Status: **Milestones A-B complete (2026-11-21).** Milestones C-E and source-model
> extraction Phases 0-6 remain pending.

## 0. Prerequisites

Read AGENTS.md before commencing any steps in this plan.

## 1. Objective and non-negotiable constraints

Build a Python script for Autodesk Fusion that exports the active design to a
versioned, technology-independent JSON document. The document must contain
enough construction intent, geometry, identity, dependency, assembly, material,
and evaluated-result information for a separate importer to reconstruct the
project as faithfully as the destination permits.

The exporter is a capture system, not a lowest-common-denominator converter.
It must record source capabilities even when no current destination supports
them. Import-time migration policy belongs to each importer.

Constraints:

- The JSON vocabulary must use general modelling terminology. Product names,
  API class names, API enum spellings, and vendor namespaces are forbidden in
  the interchange document.
- API-specific logic must be confined to the source-adapter package. Domain
  models, serializers, schema definitions, and fixtures must not import the
  host API.
- All Python is strongly typed and passes the repository's Ruff checks.
- Do not create test classes at this stage. Validation is initially performed
  with schema validation, linting, type-friendly boundary checks, and manual
  smoke models.
- Do not emit executable code. Export deterministic data only.
- Preserve unknown or not-yet-decoded features as neutral, structured records
  with warnings and evaluated geometry; never silently discard them.

## 2. Runtime and development environment

As of November 2026, Fusion embeds Python 3.14. Use CPython 3.14 for `.venv`
so syntax, standard-library behavior, and compiled dependency compatibility
match the host. Reconfirm the embedded version from the installed application's
release notes before changing the pin in the future.

Planned files:

```text
fusion-360-export-plugin/
|-- .python-version                 # 3.14
|-- .venv/                          # ignored, local only
|-- requirements.txt                # runtime dependencies; preferably empty
|-- requirements-dev.txt            # pinned Ruff version
|-- pyproject.toml                   # Ruff and Python 3.14 configuration
|-- .vscode/
|   |-- extensions.json             # Python and Ruff recommendations
|   `-- settings.json               # .venv, Ruff formatter/linter, format-on-save
|-- scripts/
|   |-- bootstrap.ps1               # create .venv and install requirements
|   `-- install-plugin.ps1          # deploy the runnable plugin atomically
|-- src/
|-- schema/
|-- examples/
|-- AGENTS.md
`-- README.md
```

Use the standard library for runtime serialization and validation wherever
practical. The host cannot use the development virtual environment at runtime,
so every runtime dependency would need to be vendored as source and verified
under the embedded interpreter. Start with an intentionally empty
`requirements.txt` containing an explanatory comment. Put Ruff only in
`requirements-dev.txt`; do not make the plugin depend on Ruff.

`scripts/bootstrap.ps1` will:

1. Resolve `py -3.14` and fail with a clear installation message if unavailable.
2. Create `.venv` using `python -m venv`.
3. Upgrade `pip` inside that environment.
4. Install `requirements.txt` and `requirements-dev.txt`.
5. Run `ruff check .` and `ruff format --check .` as a setup verification.

Avoid adopting `uv` initially: the plugin needs no third-party runtime package,
and standard `venv`/`pip` keeps contributor and host-runtime behavior obvious.
This can be revisited if dependency locking becomes valuable.

## 3. Linting and editor policy

Configure Ruff in `pyproject.toml` with:

- `target-version = "py314"`;
- a 100-character line length;
- the formatter enabled with consistent double quotes and spaces;
- core error, style, import, naming, upgrade, bugbear, annotation, simplification,
  pathlib, exception, logging, and Ruff-specific rule families;
- explicit, narrowly documented ignores only where the host callback signatures
  require them;
- first-party package names declared for deterministic import sorting;
- no blanket `noqa`, wildcard imports, or untyped public functions.

`.vscode/settings.json` will select `${workspaceFolder}/.venv/Scripts/python.exe`,
make Ruff the default formatter, enable format and import organization on save,
and enable linting on save. `.vscode/extensions.json` will recommend the official
Python and Ruff extensions.

The repository `AGENTS.md` is created with this plan and is binding for later
implementation. It requires every code change to pass both Ruff commands and
forbids test classes at this stage.

## 4. Runnable plugin skeleton

Implement the first runnable milestone as a **script**, because the requested
deployment target is the host's `API\Scripts` directory and export is a
user-triggered, finite operation. Keep application services independent of the
entry point so conversion to a persistent add-in later is small.

Planned runtime layout:

```text
src/MekatrolModelExporter/
|-- MekatrolModelExporter.py        # host-required run(context) entry point
|-- MekatrolModelExporter.manifest  # type: script, Windows support initially
|-- entrypoint.py                   # exception boundary and UI interaction
|-- application/
|   |-- export_service.py           # orchestration and progress/report result
|   `-- ports.py                    # Protocol interfaces
|-- domain/
|   |-- document.py                 # typed neutral model graph
|   |-- geometry.py                 # vectors, curves, surfaces, topology
|   |-- operations.py               # ordered construction operations
|   |-- expressions.py              # parameter/expression AST
|   `-- diagnostics.py              # fidelity and warning records
|-- adapters/
|   `-- source_application/         # the only package importing the host API
|       |-- design_reader.py
|       |-- history_reader.py
|       |-- geometry_reader.py
|       `-- identity_map.py
`-- infrastructure/
    |-- json_writer.py
    `-- schema_validator.py
```

The initial `run(context)` obtains the application UI and displays a simple
“Hello world” message. It catches `Exception`, formats a useful traceback for
the development dialog, and does not initialize export code yet. The manifest
base name, folder name, and entry module name must match so the script manager
discovers it reliably.

Milestone acceptance:

- copying the runtime folder makes the script appear in the script manager;
- running it displays the message without console setup or `.venv` activation;
- stopping/returning leaves no handlers or global application objects alive.

## 5. Deployment script

Create `scripts/install-plugin.ps1` with `SupportsShouldProcess` and these rules:

1. Compute the source from the repository; do not depend on the caller's working
   directory.
2. Resolve the destination from
   `$env:APPDATA\Autodesk\Autodesk Fusion 360\API\Scripts\MekatrolModelExporter`.
3. Fail if `APPDATA` is missing, the source manifest is missing, or paths resolve
   unexpectedly.
4. Stage into a sibling temporary directory, excluding `.venv`, caches, editor
   files, plans, development configuration, and bytecode.
5. Validate the staged manifest and entry module.
6. Replace only the named plugin folder, with `-WhatIf` support. If an existing
   installation exists, delete it after the staged copy passes validation, then
   install the staged copy cleanly. Do not retain backups.
7. Print the exact installed path and the steps to refresh/run the script.

Support optional `-DestinationRoot` for controlled development installs, while
keeping the roaming application-data path as the default. Never clear the
entire `Scripts` directory.

## 6. Interchange format design

### 6.1 Design principles

The file is a directed, ordered model graph rather than a dump of API objects.
Use stable generated IDs and explicit references. Human labels are metadata,
never identity. Serialize in deterministic order with UTF-8, invariant decimal
formatting, and a declared coordinate convention.

Every document has:

- `format`: neutral format name, semantic version, generator version;
- `document`: title, description, custom properties, creation/modification time;
- `conventions`: right-handed basis, axis vectors, angle unit, length unit,
  numeric precision, tolerance, and colour encoding;
- `parameters`: typed scalar values, unit dimensions, expressions, dependencies,
  comments, and exposed/hidden status;
- `resources`: materials, appearance data, and optional external references;
- `definitions`: reusable part/component definitions;
- `instances`: hierarchy, definition reference, rigid transform, visibility,
  suppression, and quantity;
- `construction`: datum points, directions, axes, planes, coordinate frames,
  projected/reference geometry, and sketches;
- `operations`: ordered, typed construction operations and their dependencies;
- `results`: bodies, shells, faces, loops, edges, vertices, analytic or NURBS
  geometry, tessellation previews, and physical properties;
- `relationships`: joints/constraints, contact relationships, and assembly motion;
- `diagnostics`: per-entity capture status, information loss, approximation,
  source-path-neutral warning codes, and recommended importer handling;
- `integrity`: canonical-content hash and counts.

### 6.2 Neutral vocabulary

Use terms such as `part_definition`, `instance`, `body`, `sketch`, `profile`,
`datum_plane`, `linear_sweep`, `rotational_sweep`, `path_sweep`, `loft`,
`edge_round`, `edge_bevel`, `thin_shell`, `hole`, `boolean_union`,
`boolean_difference`, `boolean_intersection`, `linear_array`, `circular_array`,
`mirror`, `move`, `scale`, `draft`, `direct_face_offset`, `sheet_metal_rule`, and
`freeform_edit`. Do not encode source API type strings or enum tokens.

Where an operation is not yet fully understood, emit `unclassified_operation`
with a general property/value tree, input/result references, ordering, and
evaluated boundary representation. The property tree may contain only neutral
primitive types, quantities, references, and general geometric terms.

### 6.3 Geometry and topology

Preserve both exact definitions and evaluated results:

- points/vectors as three finite decimal numbers;
- lines, circles, ellipses, arcs, polylines, and NURBS curves;
- planes, cylinders, cones, spheres, tori, and NURBS surfaces;
- B-rep topology with oriented coedges, loops, face orientation, shell closure,
  body manifold state, and persistent intra-file IDs;
- trimmed parameter ranges and periodicity;
- optional mesh preview with normals and material groups, never as a replacement
  for exact geometry;
- computed mass properties and bounding boxes for replay verification.

Use millimetres and radians as canonical storage units while preserving original
display units and full expressions as metadata. Do not round to UI precision.

### 6.4 Parametric history and references

Record operations in source evaluation order. Each operation contains:

- stable ID, neutral type, label, enabled/suppressed state, and sequence number;
- input references, output references, target bodies, and operation mode;
- typed parameters with literal value, dimensionality, expression AST, and
  dependency IDs;
- selection intent where known (named entity, adjacency, geometric predicate,
  or query), plus the resolved topology IDs at export time;
- construction frame and transforms;
- capture status: `exact`, `complete_with_fallback`, `approximated`, or
  `unclassified`;
- diagnostics that are machine-readable and human-readable.

Never rely solely on transient topology indexes. Build an identity map from
available persistent tokens, operation provenance, geometry signatures, and
adjacency. Persistent source tokens may be used internally while reading but
must be replaced with generated neutral IDs before serialization.

### 6.5 Schema and versioning

Create `schema/model.schema.json` using JSON Schema 2020-12. Keep
`additionalProperties: false` for specified records and provide explicit
extension maps containing only neutral values. Version the format semantically:
additive fields are minor changes; changed meaning or removed fields require a
major version. Exporters write one version; importers declare accepted ranges.

Include minimal hand-authored example documents for schema development, not
exports copied from another implementation.

## 7. Source-model extraction roadmap

### Phase 0 — discovery matrix

Create an API capability matrix before implementing extractors. For every
domain concept, document API access, stable identity availability, expression
access, geometry access, suppression behavior, assembly context behavior, and
fallback. Verify behavior using small manually created models.

### Phase 1 — document, units, parameters, and hierarchy

- Confirm an active parametric design and fail clearly for unsupported document
  modes without corrupting output.
- Read document metadata, unit settings, named/user/model parameters, expressions,
  comments, and dependency relationships.
- Walk reusable definitions and instances recursively, preserving transforms,
  visibility, suppression, grounded state, and external-link metadata in neutral
  terms.
- Assign all IDs before exporting cross-references.

### Phase 2 — construction geometry and sketches

- Export datum frames, points, axes, and planes.
- Export sketch placement, curves, construction curves, projected/reference
  curves, profiles, dimensions, geometric constraints, text, and fixed state.
- Express all constraints using general geometric relationships: coincident,
  parallel, perpendicular, tangent, concentric, equal, symmetric, horizontal,
  vertical, distance, angle, radius, diameter, and curvature continuity.
- Preserve spline degree, knots, control points, weights, fit points, periodicity,
  and trimming.

### Phase 3 — solid and surface construction history

Implement small typed readers registered by neutral operation type. Prioritize:

1. primitive solids and surface primitives;
2. linear and rotational sweeps, path sweeps, and lofts;
3. boolean operations and split operations;
4. holes, threads, ribs/webs, drafts, shells, rounds, and bevels;
5. linear/circular/path arrays, mirrors, moves, copies, and scales;
6. construction features and direct face edits;
7. sheet-metal, mesh, freeform/subdivision, derived, and configuration-driven
   operations without reducing their data to destination capabilities.

Each reader must either return a complete typed domain record or a diagnostic
fallback record. It must not partially populate a nominally exact operation.

### Phase 4 — evaluated topology and appearance

- Export the final evaluated body topology and exact analytic/NURBS geometry.
- Export per-body, per-face, and per-instance visual assignments in a general
  physically based material model where properties are available.
- Record area, volume, centre of mass, inertia tensor, bounding box, topology
  counts, and watertight/manifold status.
- Generate an optional tessellated preview at documented tolerances.

### Phase 5 — relationships and advanced document state

- Export assembly constraints/joints as general rigid-body relationships with
  frames, degrees of freedom, limits, offsets, rest state, and motion links.
- Export configurations as named parameter/visibility/suppression variants and
  rule expressions.
- Export physical materials, custom properties, and external-reference identity.
- Treat manufacturing instructions, drawings, simulation, and electronics as
  separate future schema modules; their absence must be reported in document
  coverage rather than silently ignored.

### Phase 6 — serialization and user workflow

- Present a save dialog filtered to `.json`.
- Capture into immutable typed domain records first; never write JSON while
  traversing live API objects.
- Validate referential integrity, finiteness, units, graph ordering, and schema
  conformance before replacing the destination file.
- Write to a sibling temporary file, flush/close it, then atomically replace the
  destination.
- Show a completion summary with exact/ fallback/approximated/unclassified counts
  and write diagnostics inside the document.

## 8. Fidelity and validation strategy

“Verbatim” is an acceptance target, not an assumption. Measure it at three
levels:

1. **Structural:** every visible/suppressed definition, instance, parameter,
   operation, body, and relationship is accounted for.
2. **Parametric:** replay preserves operation ordering, editable parameters,
   expressions, constraints, selections, and dependencies.
3. **Geometric:** replayed bodies match stored evaluated results within declared
   tolerance using volume, area, bounds, topology signatures, and sampled surface
   distance.

Every export includes a coverage summary. A successful file write with an
unclassified feature is a completed export with degraded fidelity, not a silent
success. The UI must state this clearly.

Initial smoke-model catalogue (manual, not test classes):

- parameter-driven constrained sketch and linear sweep;
- multi-body boolean design;
- rotational/path sweep and loft with guide geometry;
- holes, rounds, bevels, shell, draft, and thread metadata;
- arrays and mirrors referencing earlier operations;
- nested reusable definitions with transformed instances;
- suppressed operation, renamed entities, custom units, and expressions;
- surface, mesh, sheet-metal, and freeform examples;
- deliberately unsupported operation to prove fallback and diagnostics.

For each smoke model, retain only an authored checklist and expected invariant
counts until automated testing is explicitly introduced.

## 9. Implementation milestones and completion gates

### Milestone A — developer baseline — COMPLETE (2026-11-21)

- [x] Add environment, requirements, VS Code, Ruff, ignore, README, and deployment
  files.
- [x] Add runnable Hello World script and manifest with the `Mekatrol` prefix.
- [x] Gate: deployment works with `-WhatIf`, both Ruff commands pass, and the runtime is
  copied to the host scripts folder. The bootstrap is ready but needs local CPython 3.14;
  the host dialog requires manual confirmation in Fusion.

### Milestone B — neutral contract — COMPLETE (2026-11-21)

- [x] Add typed domain records, schema, example JSON, deterministic serializer, and
  integrity validator.
- [x] Gate: examples validate; domain and schema terminology audit finds no product
  or vendor-specific names.

### Milestone C — core capture — PENDING

- Add hierarchy, units, parameters, construction geometry, sketches, common
  operations, and evaluated B-rep readers.
- Gate: initial smoke models export with complete reference graphs and explicit
  coverage summaries.

### Milestone D — breadth and robustness — PENDING

- Add remaining operation families, assembly relationships, appearances,
  configurations, fallbacks, progress, cancellation, and atomic writes.
- Gate: no encountered entity disappears silently; interruption leaves no
  partial destination file.

### Milestone E — importer hand-off contract — PENDING

- Publish format versioning, importer guidance, replay ordering, selection
  resolution policy, fidelity metrics, and migration diagnostics.
- Gate: an importer can be implemented from schema and documentation without
  importing or understanding the source application's API vocabulary.

## 10. Risks and mitigations

- **Host Python changes:** pin development Python to the embedded major/minor and
  review each host release; ship source, not bytecode.
- **Unavailable history details:** retain evaluated exact geometry, generic
  property trees, operation ordering, and a precise coverage diagnostic.
- **Unstable topology identity:** combine provenance, adjacency, geometry
  signatures, and selection predicates; keep resolved IDs as verification data.
- **Assembly-context transforms:** normalize all captured frames through an
  explicit transform stack and state the file's coordinate conventions.
- **Floating-point drift:** preserve full available precision, canonical units,
  tolerances, and evaluated-result invariants.
- **Large files:** use compact deterministic encoding by default, optional
  indentation for debugging, deduplicated reusable definitions, and separately
  optional mesh previews. Do not sacrifice exact geometry for size.
- **API calls that fail on individual entities:** isolate reads at entity
  boundaries, create diagnostics, and continue only when graph integrity can be
  maintained.

## 11. Definition of done for the requested setup phase

The setup phase is complete when a contributor can clone the repository, run
one bootstrap command, edit with Ruff feedback, deploy one named plugin folder,
and run Hello World from the host. The repository must also contain the neutral
schema design and phased extraction roadmap above, with the agent rules applied
to all subsequent code.

