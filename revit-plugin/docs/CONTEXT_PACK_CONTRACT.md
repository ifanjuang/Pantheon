# Revit Context Snapshot Contract

Status: supporting contract candidate — documented non-implemented — subordinate to `docs/governance/REVIT_LOCAL_ADAPTER.md`.

The generic Pantheon `Context Pack` defines admitted project and source context.

The Revit adapter produces a more specific `Revit Context Snapshot` as a source-linked technical observation.

```text
Pantheon Context Pack
!= Revit Context Snapshot

Context Pack
-> what context the task may use

Revit Context Snapshot
-> what the live Revit instance currently exposes
```

Neither object is proof, approval or Project Anatomy.

## Purpose

A Revit Context Snapshot provides enough exact context to:

```text
correlate one request with one open document
bound model observation
detect stale or mismatched execution
preserve source locators
support Project Anatomy matching
prepare a write preflight
```

It should not export the full model when a bounded observation is sufficient.

## Reference shape

```yaml
schema_version: 1
snapshot_id: revit-snapshot-01
binding_id: revit-host-workstation-01
instance_id: revit-2026-pid-18440
observed_at: 2026-08-06T22:00:00+02:00

source:
  source_type: revit_live_document
  project_ref: project-tilleul
  document_ref: revit-document://project-tilleul/model-a
  title: Maison Tilleul
  path_hash: sha256:...
  model_guid: optional-guid
  central_model_guid: optional-guid
  workshared: true
  read_only: false

runtime:
  revit_version: "2026"
  plugin_version: 0.1.0
  host_agent_version: 0.1.0
  manifest_digest: sha256:...
  connection_mode: offline_local

active_context:
  view:
    view_ref: revit-view://12345
    element_id: 12345
    unique_id: optional
    name: RDC
    view_type: FloorPlan
  phase:
    phase_ref: revit-phase://construction
    name: Construction neuve
  design_option:
    option_ref: revit-option://main
    name: Option principale
  workset:
    workset_ref: revit-workset://1
    name: Workset1

selection:
  source: explicit_user_selection
  element_refs:
    - revit-element://unique-id-1
  element_ids:
    - 34567

scope:
  included_levels:
    - revit-level://rdc
  included_categories:
    - OST_Rooms
    - OST_Doors
  included_element_refs: []
  excluded_element_refs: []
  linked_documents_allowed: false

freshness:
  document:
    token: sha256:...
    strategy: revit_document_digest_v1
    material_inputs:
      - document_identity
      - document_version
      - document_state
  view:
    token: sha256:...
    strategy: revit_view_digest_v1
    material_inputs:
      - active_view
      - phase
      - design_option
  selection:
    token: sha256:...
    strategy: revit_selection_digest_v1
    material_inputs:
      - selected_element_ids

limitations: []
warnings: []
```

## Identity rules

### Document identity

The adapter should distinguish:

```text
document title
local path hash
model GUID when available
central model GUID when available
Revit process and instance
```

A title alone is insufficient.

Raw local filesystem paths should not cross the boundary unless a separately reviewed need exists.

### Element identity

One observed element reference may include:

```yaml
element_ref: revit-element://unique-id
element_id: 34567
unique_id: "..."
category: OST_Doors
type_ref: revit-type://...
document_ref: revit-document://...
```

```text
ElementId
-> session/document locator

Revit UniqueId
-> stronger source identity candidate

stable_object_id
-> Pantheon internal cross-source identity
```

None are interchangeable.

## Scope sources

A snapshot should state how scope was selected.

```text
explicit_user_selection
active_view_visible_elements
named_view
level_and_category_filter
explicit_element_refs
project_anatomy_object_refs
workflow_defined_bounded_query
```

Hidden global model scans are forbidden unless the Task Contract explicitly admits them.

## Element observation

A bounded element observation may include:

```yaml
element_ref: revit-element://unique-id-1
element_id: 34567
category: OST_Doors
family: Porte intérieure
type: 83 x 204
level_ref: revit-level://rdc
phase_created_ref: revit-phase://construction
phase_demolished_ref: null
design_option_ref: revit-option://main
workset_ref: revit-workset://1
pinned: false
group_refs: []
host_ref: revit-element://wall-unique-id
bounding_box:
  coordinate_system: internal
  unit: feet
  min: [0.0, 0.0, 0.0]
  max: [3.0, 1.0, 7.0]
parameters:
  - parameter_ref: builtin://DOOR_WIDTH
    name: Largeur
    storage_type: double
    raw_value: 2.7231
    display_value: "830 mm"
    normalized_value: 0.83
    normalized_unit: m
```

## Units

Every numeric field crossing the adapter boundary must declare its unit or be explicitly unitless.

Recommended pattern:

```text
raw_value
-> exact Revit storage value when useful

normalized_value
-> transport value in a declared SI unit

display_value
-> optional current-project presentation
```

A workflow must never infer metric or imperial behavior from localized display text alone.

## Geometry posture

The snapshot should prefer geometry summaries over unrestricted mesh transfer.

Possible levels:

```text
none
bounding_box
location_and_orientation
profile_summary
boundary_curves
tessellated_geometry
```

The selected level must be admitted by the Task Contract and recorded in the snapshot.

Geometry transfer must state:

```text
coordinate system
units
transform
linked-document transform when applicable
level of detail
omitted geometry
```

## Spatial observations

For rooms and spaces relevant to architecture:

```yaml
space_ref: revit-element://room-unique-id
number: "RDC-01"
name: Séjour
level_ref: revit-level://rdc
area:
  value: 42.6
  unit: m2
volume:
  value: 112.0
  unit: m3
boundary_status: enclosed
boundary_refs:
  - revit-element://wall-1
opening_refs:
  - revit-element://door-1
adjacent_space_refs:
  - revit-element://room-2
```

Adjacency is an observation candidate and must preserve the method used.

## Quantity observations

Quantity output should preserve grouping and derivation.

```yaml
quantity_set_id: revit-quantity-set-01
scope_ref: revit-snapshot-01
grouping:
  - category
  - type
  - material
items:
  - object_ref: revit-type://wall-type-01
    quantity_kind: area
    value: 180.4
    unit: m2
    derivation: host_face_area
    source_element_refs:
      - revit-element://wall-1
uncertainties: []
```

A quantity observation does not include an approved price or approved environmental impact unless those come from separately governed sources.

## Thermal and environmental observations

The snapshot may carry source data such as:

```text
orientation
envelope classification candidate
surface and volume
opening area
material layers
declared thermal parameters
product identifiers
component quantities
```

It must not label a regulatory result as produced by Revit observation alone.

## Provenance

Each important field should be traceable to:

```text
document_ref
snapshot_id
element_ref
parameter_ref or geometry method
binding and plugin version
observed_at
unit conversion method
warnings
```

This can later support APU `attribute_claim` evidence locators.

## Scoped freshness tokens

Each token should be deterministic for its own material scope. The operation
registry declares which of `document`, `view` and `selection` it requires.
Unrelated UI changes must not invalidate document-only observations.

A conceptual input set is:

```text
binding and manifest version
document token -> document identity/version/state
view token -> active view, phase and design option
selection token -> exact sorted selected element identities
```

The exact algorithm is binding metadata and must be versioned.

```text
same scoped token
-> same observed material inputs according to the declared algorithm

different scoped token
-> at least one material input changed

same scoped token != model professionally validated
```

For Project Anatomy source observations, only the document token crosses the
canonical seam as `source_representation.freshness_token` and
`observation_bundle.freshness_token`. View and selection tokens remain execution
preconditions.

## Data minimization

The adapter should omit:

```text
unrelated categories
unrequested parameters
unbounded full-model geometry
raw local paths
credentials
personal data unrelated to the task
linked-model contents when not admitted
```

Omissions should be visible when they affect interpretation.

## Staleness

A snapshot may be:

```text
current
stale
superseded
invalid_document
invalid_binding
```

Stale material may remain useful as historical source context, but it must not authorize a live write.

## Relation to Project Anatomy

```text
Revit Context Snapshot
-> source observation

mapping candidate
-> proposed cross-source identity

APU operation
-> governed internal project-object update

Project Anatomy
-> server-calculated UX projection
```

The snapshot is not persisted as a replacement for APU.

## Minimal acceptance expectations

A conforming implementation should prove:

```text
document identity is stronger than title alone
selection source is explicit
units are declared
source element references are retained
sensitive paths are redacted
freshness strategy is versioned
out-of-scope targets are refused
ElementId is never used as stable_object_id
```
