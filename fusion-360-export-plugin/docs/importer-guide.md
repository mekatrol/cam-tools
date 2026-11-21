# Neutral parametric model importer guide

This document is the normative importer hand-off for format version `1.1.0`. The JSON
Schema is authoritative for document shape and primitive constraints. This guide defines
compatibility, interpretation, replay, selection resolution, fidelity assessment, and
migration behaviour that cannot be expressed completely in JSON Schema.

An importer needs only this guide, `schema/model.schema.json`, and the neutral records in
an exported document. It must not depend on the exporter implementation or any source-system
concepts.

## 1. Acceptance and version negotiation

An importer must perform these checks before creating or changing a destination model:

1. Parse the file as UTF-8 JSON and reject duplicate object keys.
2. Require `format.name` to equal `neutral_parametric_model`.
3. Parse `format.version` as a semantic version and select a supported schema by the complete
   version, not by `generator_version`.
4. Validate the complete document against that schema.
5. Apply the graph and integrity checks in section 3.
6. Build an import plan and diagnostics before committing destination changes.

`format.version` versions the interchange contract. `generator_version` identifies the
writer and must never be used to infer document semantics.

The compatibility policy is:

- A patch release clarifies constraints or fixes a defect without changing valid document
  meaning. Importers should accept supported patch releases within the same minor line after
  validating against the matching schema.
- A minor release may add optional fields, record kinds, diagnostic codes, or neutral property
  keys. An importer may accept a newer minor release only if it preserves unknown data or
  reports every unhandled item as described in section 8. Schema `1.1.0` itself fixes the
  emitted version to exactly `1.1.0`.
- A major release may remove fields or change their meaning. It requires an explicit migration
  step and must not be opened by an importer that only supports another major version.

Importers should declare a closed supported range, for example `>=1.1.0,<2.0.0`, plus the
record kinds they can replay exactly. A version-range match does not imply support for every
`kind` value.

## 2. Document conventions

All geometry is right-handed. Lengths are stored in millimetres and angles in radians. Axis
fields establish the document frame. Transform matrices contain 16 finite numbers in row-major
order and operate on column position vectors; translation occupies indices 3, 7, and 11. An
instance transform maps its definition frame into its parent instance frame. Compose transforms
from the root toward the leaf.

Numbers must be finite. `numeric_precision` describes significant decimal digits retained by
the writer; it is not a rounding instruction. `tolerance` is the document's geometric comparison
tolerance in the declared length unit. Colour values in neutral property maps use the declared
`colour_encoding`.

Identifiers are opaque, document-local identities. Their prefix is a neutral category hint, not
a dispatch key and not a persistent identity across independently generated files. Labels are
display metadata and must never resolve references.

Property maps are data-only extension points. Importers must preserve unknown keys and nested
neutral values when their destination has an extension store. Otherwise they must issue a
migration diagnostic rather than silently dropping them.

## 3. Integrity and graph validation

Before replay, an importer must verify all of the following:

- Every `id` is unique across parameters, resources, definitions, instances, construction,
  operations, results, relationships, and configurations.
- Every ID in `dependencies`, `references`, definition membership lists, hierarchy links,
  operation inputs, outputs, and target bodies resolves to an existing record.
- `parent_id` links form an acyclic instance forest.
- Operation `sequence` values establish a deterministic total order after the tie-break rule in
  section 4.
- Every `integrity.counts` entry equals the length of the top-level collection with that name,
  and the required top-level collections all have a count.
- The canonical digest matches.

To verify the digest, deep-copy the parsed document, set `integrity.canonical_hash` to the empty
string, and replace `integrity.counts` with the observed top-level collection counts. Encode that
value as UTF-8 JSON with object keys sorted lexicographically, no insignificant whitespace,
non-ASCII characters unescaped, and separators `,` and `:`. SHA-256 the resulting bytes and
compare the lowercase hexadecimal digest with `integrity.canonical_hash`.

Reject a document on structural, reference, cycle, count, numeric, schema, or digest failure.
Do not attempt best-effort replay of a structurally invalid graph.

## 4. Deterministic replay order

Importers should construct an in-memory import plan in this order:

1. Read conventions, document metadata, resources, and parameters.
2. Create definition shells so recursive membership references can be resolved.
3. Create construction records needed by operation inputs.
4. Replay enabled operations in ascending `(sequence, id)` order. The ID tie-break makes files
   with duplicate sequence values deterministic; emit `migration.operation_sequence_collision`
   for each collision.
5. Attach or verify evaluated results. Evaluated geometry is evidence and a fallback, not an
   instruction to discard successfully replayed construction history.
6. Create instances in parent-before-child order and apply composed transforms.
7. Apply visual resources, relationships, and configurations after their referenced entities
   exist.
8. Compare the constructed model with stored results and commit only according to the importer's
   transaction policy.

Parameter dependencies must be evaluated in topological order. A dependency cycle is an import
error unless the destination has an equivalent simultaneous solver; if retained by such a solver,
report the decision. Disabled operations retain their position and metadata but are not evaluated.
Suppressed instances retain hierarchy and configuration identity but do not contribute active
evaluated geometry.

Within each definition, membership lists determine ownership. They do not override operation
sequence or graph dependencies. Array order is meaningful where the schema does not declare a
set; importers must not reorder records merely to match destination display order.

## 5. Operation and selection resolution

Dispatch operations by the complete neutral `kind` value. Interpret `mode`, `parameters`, inputs,
target bodies, and outputs together. Never infer operation meaning from labels or ID prefixes.
An operation with status `exact` is still unsupported if the importer has no matching reader.

Selection information may be carried in an operation parameter map as neutral references,
adjacency information, geometry predicates, query values, and resolved entity IDs. Resolve each
selection using this priority:

1. A directly referenced entity that exists and has the expected neutral category.
2. Provenance through an earlier operation output and the current definition membership.
3. An adjacency signature, requiring the referenced neighbours to resolve first.
4. A geometric predicate or signature evaluated in the entity's definition frame using the
   document tolerance.
5. A query evaluated against the already replayed model state at that operation's sequence.
6. The exported resolved entity IDs as verification or last-resort matching evidence.

If zero candidates remain, the selection is unresolved. If multiple candidates remain within
tolerance, the selection is ambiguous. Do not choose by transient collection index, label, or
iteration order. A failed required selection downgrades operation replay to evaluated-result
fallback when available; otherwise it prevents faithful creation of that operation. Emit a
migration diagnostic in either case.

## 6. Capture status and fallback behaviour

The four status values describe captured source fidelity, not destination support:

- `exact`: the record is represented without a known capture loss.
- `complete_with_fallback`: construction intent is incomplete, but structured fallback data and
  evaluated evidence are present.
- `approximated`: one or more values or shapes are deliberate approximations.
- `unclassified`: the exporter could not assign complete typed construction semantics.

For `complete_with_fallback`, `approximated`, and `unclassified` records, prefer exact replay only
for the portions whose semantics are understood. Preserve the original neutral record, then use
evaluated boundary geometry or tessellation as the fallback available in the record graph. Never
upgrade the status merely because the destination accepted the fallback.

If a destination cannot preserve a supported record, it must retain the neutral record in an
extension store or emit a diagnostic identifying the record and discarded capability. Silent
omission is non-conforming.

## 7. Fidelity metrics

Importers must report structural, parametric, and geometric outcomes separately.

Structural coverage is measured against all declared records, including hidden, disabled, and
suppressed records. Report counts for created exactly, created with fallback, approximated,
preserved but not replayed, and failed. Compare source capture totals with top-level `coverage`;
these totals describe capture quality and are not importer success counts.

Parametric fidelity reports whether operation order, editable parameters, expression trees,
dependencies, constraints, selection intent, and configuration behaviour remain editable.
Evaluated geometry alone does not count as parametric replay.

Geometric fidelity compares replayed results with exported evaluated results using the document
tolerance. Where present, compare bounding boxes, volume, surface area, centre of mass, inertia,
topology counts, manifold or watertight state, and sampled curve or surface distance. Report each
available metric independently; do not claim exact geometry from a matching bounding box alone.

An import may succeed with degraded fidelity. The completion summary must distinguish clean
success, success with migration diagnostics, and failure.

## 8. Migration diagnostics

Importer-generated diagnostic codes use the `migration.` prefix and lowercase dotted terms.
Each diagnostic must contain a stable code, severity, message, affected neutral entity ID when
available, and recommended action. At minimum, use these codes consistently:

| Code | Meaning |
| --- | --- |
| `migration.unsupported_version` | No declared migration path supports the format version. |
| `migration.unknown_kind` | A valid record kind has no destination replay implementation. |
| `migration.unknown_property` | A property cannot be represented or preserved. |
| `migration.selection_unresolved` | No selection candidate matched. |
| `migration.selection_ambiguous` | More than one selection candidate matched. |
| `migration.operation_sequence_collision` | Multiple operations share a sequence value. |
| `migration.parametric_fallback` | Evaluated geometry replaced editable construction intent. |
| `migration.geometry_approximated` | Destination geometry exceeds the source tolerance. |
| `migration.relationship_degraded` | A relationship lost degrees of freedom, limits, or motion. |
| `migration.configuration_degraded` | A variant rule or state could not be reproduced. |
| `migration.data_not_preserved` | Valid neutral data was necessarily discarded. |

Existing document diagnostics must be retained and presented alongside migration diagnostics;
do not rewrite their codes or severity. Importer diagnostics describe destination migration, while
document diagnostics describe source capture.

For a supported minor-version migration, copy the input into an immutable intermediate model,
apply ordered and documented transformations, retain original IDs where records retain identity,
revalidate against the target schema, and recompute counts and the digest. Never mutate the only
copy of the source file. A migration that invents a value must mark the value and emit a diagnostic.

## 9. Minimum conformance checklist

An importer is contract-conforming when it:

- validates the matching schema and all graph and digest rules before replay;
- negotiates format versions independently of generator versions;
- uses neutral kinds and explicit references rather than labels or array positions;
- follows deterministic replay and selection-resolution policies;
- preserves or diagnoses every valid but unsupported record and property;
- keeps source capture diagnostics distinct from migration diagnostics;
- measures structural, parametric, and geometric fidelity separately; and
- performs destination changes transactionally or clearly reports partial-commit behaviour before
  import begins.

The authored `examples/minimal-model.json` document is the baseline parser and digest fixture. It
demonstrates contract shape, a reusable definition, an instance transform, an evaluated result,
collection counts, and canonical hashing; it is not intended to exercise every record kind.
