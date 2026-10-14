# Revit freshness scopes

Status: active contract clarification — executable adapter implementation remains external and live Revit validation remains pending.

Authority relationship:

- `revit-plugin/docs/PROJECT_ANATOMY_OBSERVATION_CONTRACT.md` remains the Revit 2027 ↔ Project Anatomy V0.2 observation owner;
- `docs/governance/REVIT_LOCAL_ADAPTER.md` remains the Revit execution-boundary owner;
- `schemas/architecture-project-understanding/observation_bundle.schema.yaml` owns the executable candidate exchange shape;
- this note specializes freshness semantics only and creates no new Project Anatomy primitive, approval path or runtime authority.

## Why freshness is scoped

A single context token over-constrains read operations because unrelated UI changes can invalidate otherwise valid source observations.

The executable Revit binding therefore distinguishes:

```text
document_freshness
view_freshness
selection_freshness
```

These scopes are independent execution preconditions.

```text
selection changed
!= document changed

active view changed
!= document changed
```

An operation must declare exactly which scopes it requires.

## Scope definitions

### `document_freshness`

Represents the observed state of the active Revit document relevant to source/model reads.

Current implementation inputs include:

```text
document identity
DocumentVersion.VersionGUID
DocumentVersion.NumberOfSaves
Document.IsModified
Document.IsReadOnly
Document.IsModifiable
Document.IsWorkshared
```

A model edit, relevant document-state transition or document replacement may invalidate this scope.

### `view_freshness`

Represents the active view context independently from document freshness.

Current implementation inputs include:

```text
active view identity
active-view phase
design-option context
```

Changing the active view, phase context or design-option context invalidates this scope without automatically invalidating document freshness.

### `selection_freshness`

Represents the exact current Revit selection independently from document and view freshness.

Current implementation input is the sorted set of selected element IDs within the already-bound document.

Changing only the selection invalidates this scope without automatically invalidating document or view freshness.

## Operation requirements

The first W0 registry slice uses:

```text
revit.system.observe_runtime.v1
  freshness: []

revit.document.observe_context.v1
  freshness: []

revit.view.observe_active.v1
  freshness: [document, view]

revit.selection.observe.v1
  freshness: [document, selection]

revit.architecture.observe_rooms.v1
  freshness: [document]

revit.architecture.observe_doors.v1
  freshness: [document]
```

The Host must not invent these requirements. It consumes them from the closed Operation Registry / Capability Manifest.

## Refusal semantics

Scoped freshness produces specific refusal outcomes:

```text
refused_document_mismatch
refused_stale_document
refused_stale_view
refused_stale_selection
```

This lets Hermes distinguish a changed model from a changed UI context and choose an appropriate retry/re-observation path without treating every state change as a generic failure.

## Project Anatomy seam

Project Anatomy V0.2 `source_representation.freshness_token` and
`observation_bundle.freshness_token` remain **document freshness** for Revit
source observations.

View and selection freshness are execution-context guards; they are not additional Project Anatomy canonical primitives.

Therefore:

```text
Revit execution context
  document_freshness
  view_freshness
  selection_freshness

Project Anatomy source observation
  freshness_token = document_freshness
```

The Revit Context Snapshot carries the three execution tokens. The Observation
Bundle carries only document freshness because its `scope` and `coverage`
already describe the bounded source observation. View or selection changes may
refuse operations that require those scopes, but they do not create additional
APU freshness fields.

This preserves the frozen V0.2 source-representation contract while avoiding false staleness in the Revit adapter.

## Conformance expectations

Live Revit 2027 tests must prove at minimum:

1. changing only selection invalidates `selection_freshness` but does not invalidate document-only operations;
2. changing only active view invalidates `view_freshness` but does not invalidate document-only operations;
3. modifying the model invalidates `document_freshness` for document-bound operations;
4. wrong active document is refused independently of freshness;
5. each operation enforces only the freshness scopes declared in the registry;
6. source representations and Observation Bundles retain document freshness as their canonical source freshness token.

`compiled != supported`: these semantics remain live-validation requirements until exercised in Autodesk Revit 2027.
