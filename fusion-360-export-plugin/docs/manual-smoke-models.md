# Milestone D manual smoke catalogue

Run each authored model through the installed script. Cancel once during capture. A cancelled
capture must not create or replace the selected destination.

For every completed export, validate the JSON and inspect the completion summary. Every history
entry must contribute an operation record. Unknown entries must use `unclassified_operation`,
include `capture.operation_unclassified`, and retain the evaluated body summary.

| Model | Required observations |
| --- | --- |
| Primitive and feature breadth | Primitive, sweep, split, hole, thread, rib, draft, shell, round, bevel, and direct-edit entries remain in evaluation order. |
| Repetition and transformation | Linear, circular, and path arrays plus mirror, move, copy, and scale entries are present. |
| Advanced construction | Sheet, mesh, freeform, derived, and construction entries are classified or explicitly retained as fallbacks. |
| Nested assembly | Every visible and suppressed instance is present; joint records reference existing instances and retain enabled state. |
| Visual assignment | Assigned bodies reference appearance resources; undecoded channels carry `capture.appearance_fallback`. |
| Configured design | Each exposed variant is represented and the active variant is marked. A runtime without configuration access emits `capture.configurations_unavailable`. |
| Deliberately unknown feature | The feature is not omitted, coverage reports one unclassified record, and the destination remains schema-valid. |
