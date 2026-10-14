# Pantheon Revit Gate — Developer Dossier

Status: candidate support doctrine — documented non-implemented.
Boundary profile: candidate_support_note.

This dossier is documentation only. It describes a future local Revit add-in that
does not exist yet. Nothing here is built; there is no runtime, no plugin code,
no schema change and no test in this repository. The repository state for this
document is **documented non-implemented**. Do not read any sentence below as a
claim that the plugin is implemented.

Doctrinal placement of the three named layers:

```text
Pantheon Architectonics understands and names the project.
Pantheon Model Gate governs rights and actions.
Pantheon Revit Gate executes locally inside Revit.
Hermes orchestrates.
The human validates.
```

Naming note: this dossier uses **Pantheon Revit Gate** as the single working
name for the local add-in, to keep it distinct from **Pantheon Model Gate**
(which governs rights, and does not execute). The alternative label "Pantheon
Model Gate Revit" is intentionally not used here to avoid conflating the two
layers; the final name is a human decision (see section 18).

## TL;DR

- This is a documentation-only dossier for a Revit add-in that does not exist
  yet. Repository state: documented non-implemented.
- Read first: sections 0 (critical framing), 1 (purpose) and 2 (placement).
- MVP scope is small: the **Read Pack** plus the **Control Band** come first;
  everything that writes to the model is later and is out of the MVP.
- The **Action preview list** (historically called the "Action Queue") is a
  human-facing review list, not an autonomous dispatcher: nothing runs on its
  own, the human reviews and decides.
- Default posture is read only. Every write capability is opt-in, gated,
  previewed and validated by a human. Deletion is never bundled into "full
  control".
- Sections 3–17 are reference detail for later sprints; they are not a backlog
  commitment. Section 18 lists the decisions still to arbitrate.

Reading order for this dossier:

```text
0. Critical framing (read first)
1. Purpose
2. Placement
3. General architecture
4. Control Band
5. Control Matrix
6. Action preview list (the "Action Queue") — never an autonomous queue
7. Dry-run / Preview / Temporary modes
8. Warning Broker
9. Indirect deletion / hosted elements / joins
10. Transaction Runner
11. Functional Packs
12. Action Contract
13. Batch Action Contract
14. Action Report
15. MCP/API Binding
16. MVP Roadmap
17. Absolute Forbidden Actions
18. Decisions to Arbitrate
19. Guiding sentence
Appendix — Glossary
```

## 0. Critical framing (read first)

This section is editorial: it states the risks of the dossier itself so the team
does not mistake a written intention for an existing capability.

- This dossier is large. Size is not maturity. Everything here remains a
  candidate until reviewed, and most of it is deliberately out of the MVP.
- The only part the team should commit to first is the **Read Pack** plus the
  **Control Band**. Everything that writes to the model is later.
- The most dangerous illusion would be to treat the rich Control Matrix as a
  promise of broad write control. It is not. The default posture is read only;
  every write capability is opt-in, gated and previewed.
- Two layers carry different authority and must not be conflated: Pantheon Next
  (doctrine, no execution) and the future Revit Gate add-in (local execution,
  outside Pantheon). This document lives in the first; it merely specifies the
  second.

## 1. Purpose

Pantheon Revit Gate is the planned local Revit add-in responsible for applying
governed actions to an open Revit model. It would receive a structured Action
Contract, validate it locally, preview it, and only then apply it through a Revit
transaction, with a human validating before any consequential effect.

It is **not**:

- an autonomous AI;
- a free code executor;
- a replacement for Revit;
- a runtime inside Pantheon Next;
- a system that modifies the model automatically without validation.

Principle:

```text
Hermes prepares.
Pantheon governs.
Revit Gate executes locally.
The human validates.
```

## 2. Placement

Pantheon Revit Gate is not part of the Pantheon Next runtime. It would run
outside Pantheon, locally inside Revit, on the architect's machine. Pantheon Next
never executes a Revit action; it only governs whether one is permitted.

Responsibilities:

- **Pantheon Next** — doctrine, rules, control profiles, action contracts, action
  reports, capability map. It decides nothing about geometry; it governs rights.
- **Hermes** — orchestration, active control session, preparation of requests,
  MCP/API call. It prepares; it does not approve and does not execute in Revit.
- **Pantheon Revit Gate** — the local Revit add-in: local validation, the
  plugin-side action preview list, dry-run, transaction runner, warning broker,
  action report. It applies the guard-rails and the transaction.
- **RVT** — minimal traces only, never the full source of governance.

Inside the RVT only lightweight references are stored, never the governance source
itself:

```text
PTN_ControlProfileId
PTN_ActionReportRef
PTN_APU_RunRef
PTN_LastReview
```

## 3. General architecture

The chain is one-directional. MCP/API transports requests, but the plugin applies
the guard-rails. No upstream layer reaches into the Revit transaction directly.

```text
OpenWebUI / Dashboard
    ↓
Hermes
    ↓
Local MCP/API Relay
    ↓
Pantheon Revit Gate plugin
    ↓
Revit API
    ↓
Open RVT document
```

The relay carries an intention that has already been turned into a contract. The
plugin is the last and strongest checkpoint: even a well-formed contract is
re-validated locally against the live model and the local control state.

### Governance binding (Pantheon contract → local enforcement)

This is the crux the rest of the dossier depends on: how a Pantheon governance
decision becomes a controlled Revit transaction without the plugin ever granting
itself rights. It reuses the existing keystone in
`docs/governance/UNIFORM_CAPABILITY_GOVERNANCE.md` (one rulebook, one passport
per capability, an unbypassable gate split into a decision point and an
enforcement point) and the placement rules in
`docs/governance/CAPABILITY_PLACEMENT.md`.

Roles in one sentence each:

- **Pantheon Model Gate is the decision point (PDP).** It reads the capability
  passport, the active control profile and the approval ceiling and emits a
  decision as data. It does not execute.
- **Pantheon Revit Gate is the enforcement point (PEP), but a re-validating
  one.** It consumes an already-decided contract and may only narrow it, never
  widen it.

Authority chain for a single action:

```text
1. Each Revit action type maps to one capability id in the Pantheon capability
   map (e.g. revit.create_text_note -> a passport with scope, allowed
   operations and approval level).
2. The Model Gate evaluates passport + active control session + approval ceiling
   and returns allow/deny + constraints as data. It never executes.
3. Hermes packages that decision into the Action Contract (capability id,
   granted scope, approval status, constraints, provenance/run ref).
4. The Revit Gate treats the contract as a claim of permission, not proof. It
   re-derives the effective permission locally and may only reduce it:
   effective = minimum(contract grant, local control state, live model safety).
```

Mapping — every Action Contract field traces back to a governance source, not to
the plugin:

| Action Contract field | Governance source of truth |
|---|---|
| `action_type` / capability id | Pantheon capability map / passport |
| `risk_level`, `mode` (dry_run/execute) | Control profile + `CAPABILITY_PLACEMENT.md` |
| `approval_status` | `docs/governance/APPROVALS.md` + `docs/governance/USER_DECISION_GATE.md` |
| `constraints` (allow_create/modify/delete…) | Passport scope, narrowed by local state |
| `provenance.source_run_ref` | Hermes active control session |

Binding rules:

- The passport is the single source. The plugin must refuse any action whose
  capability id is absent, unknown or expired in the contract; the fallback is
  N0 Read only.
- The plugin never reads the capability map to grant itself rights. It only
  consumes the decided contract and can only narrow it.
- The RVT stores references only (`PTN_ControlProfileId`, `PTN_ActionReportRef`,
  …). The binding is resolved at request time against Pantheon, never
  reconstructed from the RVT.
- The dependency is one-way, mirroring the repository boundary: the plugin
  depends on the governance artifacts; the governance core never depends on the
  plugin. This specializes `docs/governance/BRIDGE_CONTRACT.md`.

## 4. Control Band

A small tab is always visible inside Revit. It is the at-a-glance state of the
gate. It must permanently display:

- active mode;
- freedom level;
- color;
- active profile;
- write permission active or not;
- dry-run required or not;
- approval required or not;
- Hermes connection;
- plugin connection.

Proposed levels:

```text
N0 — Read only
N1 — Annotation
N2 — Review parameters
N3 — Documentation / finishes
N4 — Controlled model modification
N5 — Family sandbox
N6 — Locked
N7 — Custom
```

Example display:

```text
Pantheon Gate · N3 Finishes · Dry-run required · Approval required
```

## 5. Control Matrix

Clicking the tab opens the Control Matrix panel: the explicit grid of what the
active profile may and may not do.

Columns:

```text
Forbidden | Read | Create | Light modify | Model modify | Delete | Sandbox / Admin
```

Rows:

```text
Project / document
Views
Sheets
Schedules
Legends
View filters
Graphic overrides
Text notes / annotations
Detail lines
Filled regions
Dimensions
Rooms / spaces
Walls
Floors / ceilings / roofs
Doors
Windows
Equipment
Materials
Fill patterns / hatches
Review parameters
Instance parameters
Type parameters
Loadable families
In-place families
Revit links
Groups
Phases
```

Important rule:

```text
Delete is never included in full control.
Delete is always a separate explicit permission.
```

Safety rule — effective permission is the minimum of all sources, never the
maximum:

```text
Effective permission = minimum(
    Pantheon policy,
    Hermes session,
    Revit Gate local state,
    project safety checks
)
```

If a profile is absent, expired, incoherent or unknown, the fallback is the safest
state, not a permissive one:

```text
fallback = N0 Read only
```

### v0 minimal matrix (what is actually built first)

The full grid above (seven columns × twenty-six rows) is the **target
reference, not the v0 surface**. It is deliberately large, and keeping all of its
cells coherent is itself work; the enforcement engine evaluates `minimum(...)`
over whatever subset exists. To avoid mistaking that breadth for the first
release, v0 implements only the slice below. Everything not listed is **Read
only**, and **Delete and Model modify do not exist as columns in v0**.

| Domain (v0) | Read | Create | Light modify |
|---|---|---|---|
| Project / document | yes | — | — |
| Any model category (walls, floors, doors, windows, equipment…) | yes | — | — |
| Text notes / annotations | yes | yes | yes |
| Detail lines | yes | yes | yes |
| Review views | yes | yes | — |
| Review parameters | yes | — | yes |
| Type parameters, families, links, groups, phases | yes | — | — |

In other words, v0 lives between N0 and N3: it can read everything, create
annotations and review views, and set explicitly review-flagged parameters —
nothing else. Model modification, deletion, type changes, family edits and link
writes are out of v0 by construction, not by configuration. The richer matrix is
unlocked column by column only after the matching pack passes its feasibility
spike (section 11).

### Levels ↔ matrix columns ↔ packs (cross-map)

The dossier uses three parallel taxonomies — the N0–N7 levels (section 4), the
matrix columns (this section) and the functional packs (section 11). They are not
independent; this table ties them together so they cannot drift apart.

| Level | Matrix columns unlocked | Packs in scope | In v0? |
|---|---|---|---|
| N0 Read only | Read | Read | yes |
| N1 Annotation | + Create (annotations) | Annotation, Drafting (annotation side) | yes |
| N2 Review parameters | + Light modify (review params) | Parameter (review subset) | yes |
| N3 Documentation / finishes | + Light modify (views, schedules) | Schedule, View and Filter, Naming | partly (no finishes) |
| N4 Controlled model modification | + Model modify | Wall, Finish | no |
| N5 Family sandbox | + Sandbox / Admin (sandbox only) | Family Sandbox, In-Place Component | no |
| N6 Locked | none | none | n/a |
| N7 Custom | explicitly enumerated per profile | explicitly enumerated | no |

Delete is intentionally absent from every level above: it is never a column
unlocked by a level, only a separate explicit permission (see the rule earlier in
this section). v0 stops at N3 and, within N3, ships only the annotation and
review-parameter slice, not finishes.

## 6. Action preview list (the "Action Queue") — never an autonomous queue

This is a human-facing preview list, never an autonomous dispatcher. The word
"queue" here means an ordered preview the human reads, not a runtime that drains
itself: nothing runs on its own, no item self-dispatches, and there is no
background worker. The human reviews the list and decides. Each action or series
of actions must be shown before execution.

Example:

```text
Batch: Bathroom finishes
[1] Find room "Children bathroom"
[2] Resolve boundary walls
[3] Identify room-side faces
[4] Paint candidate wall faces
[5] Create baseboards
[6] Write room finish parameter
[7] Export action report
```

Each line must carry a status:

```text
Ready | Dry-run OK | Warning | Blocked | Skipped | Executed | Rolled back
```

The user can:

- disable an action;
- modify an option;
- apply only the safe actions;
- isolate the elements;
- export the preview report;
- cancel the batch.

## 7. Dry-run / Preview / Temporary modes

Every write action must pass through a dry-run, except an explicit, very low-risk
exception.

Three kinds of preview:

1. **Logical preview** — lists the actions without modifying Revit.
2. **Visual preview** — highlights / isolates / temporarily shows the concerned
   elements.
3. **Trial transaction preview** — temporarily applies the action in a controlled
   transaction, captures the result, then rolls back.

Preview mandatory for:

```text
delete
family edit
wall type change
type parameter edit
geometry modification
batch actions
actions touching hosted elements
actions with A3/A4 warnings
```

Preview may be compact or disabled only for:

```text
read-only
single TextNote
small review parameter update
simple view/schedule creation
```

## 8. Warning Broker

This is the central handling of Revit alerts.

Principle:

```text
A Revit warning is not automatically a stop.
It is an attention debt to qualify, accept, resolve, defer, or block.
```

Classes:

```text
A0 — Information
A1 — Acceptable warning
A2 — Warning requiring confirmation
A3 — Indirect impact
A4 — Model risk
A5 — Blocking failure
```

Examples:

A0:

```text
Element already has requested value.
```

A1:

```text
Text note already exists.
Schedule already exists.
```

A2:

```text
Exterior face inferred with uncertainty.
Wall is flipped.
Room boundary imperfect but usable.
```

A3:

```text
Dimensions may be deleted or disassociated.
Hosted element may be affected.
Wall join will be recalculated.
```

A4:

```text
Wall type change may create collision.
Type parameter affects many instances.
Family reload may affect many placed elements.
```

A5:

```text
Action targets linked model.
Family is not editable.
Delete permission missing.
Transaction failed.
Action Contract incomplete.
```

Rule:

```text
A warning blocks only if it is unknown, unlisted, unaccepted, or outside the active policy.
```

Never silently suppress all warnings automatically.

### Mapping the Revit FailureProcessing API to A0–A5

The A0–A5 classes are not invented out of nothing: they are a governance layer
over the real Revit failure API. The plugin registers an `IFailuresPreprocessor`
(and, where needed, an `IFailuresProcessor`) so it sees every failure inside the
transaction, before commit, and can decide rather than let Revit auto-resolve.

For each failure the preprocessor reads the `FailureMessageAccessor` and derives
the class from three signals:

```text
- GetSeverity()              -> Warning | Error | DocumentCorruption
- GetFailureDefinitionId()   -> matched against a known/allowlisted set
- GetApplicableResolutionTypes() / resolution caption
                             -> does any resolution delete or detach elements?
```

Mapping:

| Class | Derived from FailureProcessing | Preprocessor action |
|---|---|---|
| A0 Information | No failure, or a Warning whose effect is a no-op (value already set) | Continue; note only |
| A1 Acceptable | `Warning` whose `FailureDefinitionId` is in the known/allowlisted set | May `DeleteWarning`, recorded in the Action Report |
| A2 Confirmation | `Warning` that is allowlisted but inferred/ambiguous (flipped wall, inferred face) | Hold for human confirmation; do not auto-resolve |
| A3 Indirect impact | Any failure whose resolution types include deleting or detaching elements (`GetApplicableResolutionTypes` / failing + additional element ids) | Never auto-apply; list affected ids, require confirmation (see section 9) |
| A4 Model risk | `Error` affecting many instances, or type/family changes with wide `GetFailingElementIds` | Block pending explicit review and a dry-run that enumerates impact |
| A5 Blocking failure | `Error` / `DocumentCorruption`, no acceptable resolution, or a rolled-back transaction | `RollBackPendingTransaction`; report and stop |

Two rules keep this safe:

- **Default-deny on the unknown.** A `FailureDefinitionId` that is not in the
  known set is treated as at least blocking until it is classified — never
  silently dismissed. This is the API-level form of the section 8 rule that a
  warning blocks if it is unknown, unlisted, unaccepted or outside policy.
- **A resolution that deletes is never automatic.** Any resolution type that
  removes or detaches elements is at minimum A3: it is listed, confirmed and
  written to the Action Report, mirroring the indirect-deletion rule in
  section 9.

Some conditions are A5 before Revit ever runs: a missing delete permission, a
target in a linked model, or an incomplete Action Contract are refused by the
plugin up front, not surfaced as Revit failures.

## 9. Indirect deletion / hosted elements / joins

Distinguish:

- **direct deletion** — an action explicitly requested.
- **indirect deletion** — a deletion or disassociation produced by Revit as a side
  effect.

Direct deletion remains forbidden by default.

Indirect deletion may be accepted only if:

- the elements are listed;
- the user confirms;
- the Action Report keeps the trace;
- a note or follow-up action is created if necessary.

Hosted objects to watch:

```text
doors
windows
MEP fixtures
wall-hosted families
dimensions
tags
wall sweeps / baseboards
join relationships
```

For a wall modification, the dry-run must list:

- hosted openings;
- detectable dependent dimensions;
- hosted equipment;
- joins;
- elements inside groups;
- constraints;
- clash risks.

## 10. Transaction Runner

The plugin must apply actions through Revit transactions, never through free
modification.

Policies:

```text
L0 read actions:    No transaction.
L1/L2:              Named transaction.
Batch actions:      TransactionGroup if appropriate.
Trial preview:      Rollback required.
N4/N5:              Backup / sandbox policy required.
```

No transaction is committed without an Action Report.

### Idempotency and re-run

The same contract may arrive twice (a retry, a double click, a replayed call).
The plugin must be safe under repetition, not blindly re-apply.

- Every contract carries an `idempotency_key` (the `contract_id` by default). The
  plugin keeps a short per-session record of keys it has already executed.
- A second contract with a known key is **not** re-executed. The plugin returns
  the existing Action Report for that key instead of producing a new effect.
- A dry-run never consumes the key; only a committed execution records it.
- Where the action is naturally idempotent (the requested value is already set),
  the result is an A0 information outcome (no-op), not a new write.

This keeps retries cheap and prevents a replayed contract from duplicating notes,
parameters or geometry.

## 11. Functional Packs

The following packs are documented as future capabilities. None is implemented.
Only the **Read Pack** and the **Annotation Pack** are MVP scope; every other
pack below is explicitly out of the MVP and is reference detail for later
sprints, not a backlog commitment.

### Feasibility against the Revit API (first-pass, to verify)

The lists below are desired behavior. They are not graded by difficulty in the
action names themselves, which would make a trivial read look equal to a hard
geometry operation. This table is a **first-pass estimate to confirm with a
Revit API spike**, not a commitment or a measured benchmark.

Legend:

```text
native   — supported cleanly by the Revit API; mostly wiring.
costly   — feasible, but real geometry/logic work, verbose API and edge cases.
research — hard or partially impractical; needs a spike before it is promised.
```

| Pack | Feasibility | Rough effort | Main caveats |
|---|---|---|---|
| Read | native | low | Snapshots/export are native; safe MVP anchor. |
| Annotation | native | low–medium | Text notes / detail lines native; review boundary medium. |
| Parameter | costly | medium | Instance set is native; type-parameter impact count and shared/project parameters add work. |
| Schedule | costly | medium | `ViewSchedule` creation is native; field/filter/sort wiring is fiddly. |
| View and Filter | costly | medium | Filters and overrides are native but verbose; prefer review views. |
| Drafting | native–costly | low–medium | Detail lines and filled regions native; zone marking medium. |
| Measurement | costly | medium | Geometry measures need solid/face extraction; tracking each value's origin adds work. |
| Naming | native | low–medium | Rename is native; conflict and dependency detection is the real work. |
| Finish | research | high | Paint face, paint room wall faces, baseboards and finish-as-data need face references and room-boundary→face mapping; genuinely hard. |
| Wall | research | high | "Change type while preserving the interior finish face" plus hosted elements, joins and dimensions is the hardest target in this dossier. |
| Legend and Graphics | costly | medium | Legend views and fill-pattern creation are fiddly but feasible. |
| Family Sandbox | research | high | Family document open/edit/reload orchestration and sandbox isolation are complex. |
| In-Place Component | costly | medium–high | The in-place family API is limited and awkward; keep to review/coordination volumes. |

Reading the table: build the `native` packs first (Read, Annotation, Naming),
treat `costly` packs as normal sprints, and gate every `research` pack behind a
dedicated feasibility spike before it is shown to a user as available. The three
`research` packs (Finish, Wall, Family Sandbox) carry most of the project risk
and must not be promised on the strength of this document alone.

### Read Pack

```text
revit.ping
revit.get_project_info
revit.get_active_view
revit.list_selection
revit.get_element_summary
revit.read_instance_parameters
revit.read_type_parameters
revit.read_dimensions
revit.measure_distance
revit.export_view_snapshot
```

MVP priority.

### Annotation Pack

```text
revit.create_text_note
revit.create_review_view
revit.create_detail_line
revit.create_review_boundary
```

MVP priority.

### Parameter Pack

Must distinguish:

```text
instance parameter
type parameter
project parameter
shared parameter
family parameter
read-only parameter
calculated value
```

Actions:

```text
revit.parameter.list_instance
revit.parameter.list_type
revit.parameter.compare_instance_type
revit.parameter.set_review
revit.parameter.set_instance
revit.parameter.set_type_dry_run
revit.parameter.audit_missing
```

Modifying a type parameter must display the number of impacted instances.

### Schedule Pack

```text
revit.schedule.create
revit.schedule.add_field
revit.schedule.add_filter
revit.schedule.set_sort_group
revit.schedule.hide_field
revit.schedule.create_review_schedule
```

Examples:

- door schedule to verify;
- rooms without finish;
- exterior walls by type / level;
- families with missing parameters.

### View and Filter Pack

```text
revit.view.create_review_view
revit.view_filter.create
revit.view_filter.apply_to_view
revit.view_filter.set_overrides
revit.view.export_image
revit.view.snapshot
```

Rule:

```text
Prefer review views over changing production views.
```

### Drafting Pack

```text
revit.detail_line.create
revit.detail_line.create_polyline
revit.detail_line.set_style
revit.filled_region.create
revit.filled_region.set_type
revit.drafting.mark_zone
```

Uses:

- zone to review;
- demolition limit;
- candidate finish zone;
- façade return to control.

### Measurement Pack

```text
revit.measure.wall_length
revit.measure.room_area
revit.measure.opening_width
revit.measure.distance_between_elements
revit.measure.face_to_face_distance
revit.dimension.read_existing
revit.dimension.create_candidate
```

Each measurement must state its origin:

```text
from parameter
from geometry
from dimension element
from computed relation
from view annotation
```

### Naming Pack

```text
revit.naming.rename_view
revit.naming.rename_schedule
revit.naming.rename_type
revit.naming.rename_material
revit.naming.rename_filter
revit.naming.standardize_names_dry_run
```

Rule:

```text
Renaming changes display identity, not stable identity.
```

Dry-run must show:

- old name;
- new name;
- ElementId;
- UniqueId;
- number of affected instances;
- conflicts;
- possible dependencies.

### Finish Pack

```text
revit.finish.apply_room_finish_data
revit.finish.paint_face
revit.finish.paint_room_wall_faces
revit.finish.paint_exterior_wall_faces
revit.finish.create_baseboards
```

Rule:

```text
Finish must first be data.
Paint or modeled baseboards are projections of that data.
```

### Wall Pack

```text
revit.wall.change_type_dry_run
revit.wall.change_type_keep_reference
revit.wall.duplicate_type
revit.wall.set_type_parameter
revit.wall.check_orientation
```

Target case:

```text
Change selected walls to a target type while preserving interior finish face.
```

Required controls:

- wall flipped;
- joined;
- hosted elements;
- dimensions;
- groups;
- constraints;
- doors/windows hosted;
- wall sweeps;
- linked context.

### Legend and Graphics Pack

```text
revit.legend.create_view
revit.legend.create_material_legend_candidate
revit.graphics.create_filled_region_type
revit.graphics.create_fill_pattern_candidate
revit.graphics.set_region_color
revit.graphics.create_line_style
```

### Family Sandbox Pack

```text
revit.family.open_sandbox
revit.family.duplicate_type
revit.family.set_parameter
revit.family.save_candidate
revit.family.reload_candidate
```

Rule:

```text
Family edits never happen directly in production mode.
```

### In-Place Component Pack

Accepted use:

- reservation volume;
- clearance volume;
- review mass;
- coordination marker;
- temporary control component.

Forbidden by default:

- automatic in-situ production component;
- repeated families that should be loadable;
- unreviewed geometry.

## 12. Action Contract

The plugin receives only a structured contract, never a free intention.

```yaml
schema_version: "0.1-draft"
contract_id: ACT-REVIT-0001
idempotency_key: ACT-REVIT-0001
action_type: create_text_note
mode: dry_run
risk_level: N1_ANNOTATION
approval_status: pending
target:
  view:
    source: active_view
  position:
    mode: near_element
    element_ref:
      source_type: revit
      element_id: "184233"
payload:
  text: "Largeur utile à vérifier avant VISA."
  note_type: "Pantheon Review Note"
constraints:
  allow_create: true
  allow_modify_geometry: false
  allow_delete: false
  require_transaction: true
  require_human_approval_before_execute: true
provenance:
  requested_by: human
  source_run_ref: APU-RUN-001
```

## 13. Batch Action Contract

```yaml
schema_version: "0.1-draft"
batch_action:
  id: BATCH-REVIT-0042
  title: "Finitions SDB enfants"
  mode: dry_run
  actions:
    - action_type: resolve_room
      target: "SDB enfants"
    - action_type: paint_room_wall_faces
      material: "Faïence verte 10x10"
    - action_type: create_baseboards
      baseboard_type: "Plinthe carrelée 10 cm"
    - action_type: set_room_finish_parameter
      finish_height: "2.00 m"
  execution_policy:
    all_or_nothing: true
    transaction_group: true
    require_preview: true
    require_human_approval: true
```

## 14. Action Report

```yaml
schema_version: "0.1-draft"
report_id: RPT-REVIT-0001
contract_id: ACT-REVIT-0001
action_type: create_text_note
mode: execute
status: executed
revit_context:
  document_title: "Projet test.rvt"
  active_view: "RDC - Plan"
  revit_version: "2026"
control:
  control_profile: "Annotation"
  control_level_at_execution: N1_ANNOTATION
  permission_used:
    domain: text_notes
    operation: create
transaction:
  name: "Pantheon Revit Gate - Create Text Note"
  status: committed
result:
  created_elements:
    - element_id: "921844"
      category: "Text Notes"
  modified_elements: []
  deleted_elements: []
warnings:
  - class: A1_ACCEPTABLE_WARNING
    message: "Position inferred near selected element."
governance:
  canonicalizes_project_truth: false
  writes_pantheon_memory: false
  requires_human_review: true
```

### Worked example: one review note, end to end

To see how the parts connect, here is a single concrete case threaded through the
whole chain. It creates one review note near a selected door.

```text
1. Intent (human, in OpenWebUI / Dashboard)
   "Add a review note next to this door: useful width to check before VISA."

2. Hermes
   Resolves the active control session, maps the intent to capability
   revit.create_text_note, requests a decision from the Model Gate.

3. Model Gate (decision point)
   Reads the passport + active profile (N1 Annotation) + approval ceiling.
   Returns: allow create on text_notes, dry-run required, approval required.
   It does not execute.

4. Action Contract (see section 12)
   Hermes packages the decision: action_type create_text_note, mode dry_run,
   allow_create true, allow_delete false, idempotency_key ACT-REVIT-0001,
   provenance.source_run_ref APU-RUN-001.

5. Revit Gate — local re-validation
   effective = minimum(grant, local control state, model safety).
   Capability id is known and unexpired; effective level N1; create allowed.

6. Action preview list (section 6) + dry-run (section 7)
   One line: "Create review TextNote near door 184233" -> Dry-run OK.
   The note position is inferred near the selected element.

7. Warning Broker (section 8)
   IFailuresPreprocessor sees a Warning: position inferred near element.
   FailureDefinitionId is allowlisted, no deleting resolution -> class A1.

8. Human approval (User Decision Gate)
   The human sees the preview, the A1 warning and the dry-run result, approves.

9. Transaction Runner (section 10)
   Named transaction "Create Text Note"; commit; idempotency_key recorded.

10. Action Report (section 14)
    status executed, created_elements [TextNotes 921844], A1 warning recorded,
    canonicalizes_project_truth false, requires_human_review true.

11. RVT trace
    Only PTN_ActionReportRef + PTN_ControlProfileId are written; governance
    stays in Pantheon, not in the RVT.
```

If the same contract is sent again, step 9 is skipped and the existing Action
Report is returned (idempotency, section 10).

## 15. MCP/API Binding

Phase 1:

```text
local HTTP API for debugging
```

Phase 2:

```text
MCP wrapper around the same allowlisted actions
```

MCP must not expose:

```text
execute_generated_code
delete_anything
modify_without_dry_run
edit_family_direct
write_linked_model
```

MCP must only expose named, allowlisted tools.

### Threat model of the local relay

The relay (Phase 1 local HTTP, Phase 2 MCP) is the most security-sensitive part
of the design, because the asset it sits in front of is an open RVT that can be
mutated. The relay must be treated as a development/control surface, not a
network service.

Asset to protect: the open Revit document and its governed traces.

Threats and the control that contains each one:

| Threat | Control |
|---|---|
| Another local process reaches the HTTP port and drives writes | Bind to loopback `127.0.0.1` only, never `0.0.0.0`; it is not a network service |
| Forged or replayed Action Contract not issued by Pantheon/Hermes | Per-session shared secret between Hermes and the plugin; contract carries a Pantheon-issued run ref; reject unauthenticated or unknown/expired contracts |
| Over-broad contract used for privilege escalation | The plugin re-validates locally: `effective = minimum(grant, local state, model safety)`; it can only narrow, never widen |
| Confused deputy (a benign surface tricked into sending a write) | Default-deny, N0 fallback on any ambiguity, and per-action human approval before any consequential effect |
| Tampered RVT references or stale control profile | Binding resolved at request time against Pantheon, not reconstructed from the RVT; expired/unknown profile falls back to N0 |
| Missing or altered audit trail | No transaction is committed without an Action Report; read actions take no transaction |
| Arbitrary code or unlisted operation | Allowlist only; `execute_generated_code` and equivalents are forbidden (section 17) |
| Writes to linked or central/workshared models | Refused by default; one document context per session |

Phase 2 (MCP) does not widen the surface: it keeps the same loopback and
per-session-secret posture and exposes only named, allowlisted tools.

Residual risks, stated rather than solved:

- A fully compromised machine running with the user's own privileges can drive
  Revit directly, with or without this plugin; the relay does not claim to defend
  against that.
- OS-level sandboxing of the Revit process itself is out of scope.

## 16. MVP Roadmap

This roadmap is documented, not implemented; nothing below is built. The plugin
preview list, dry-run and write actions are future work and remain candidates.

Sprint 1:

```text
Revit add-in loads
Control Band visible
ping
get_project_info
list_selection
read_instance_parameters
read_type_parameters
export active view snapshot
```

Done = the add-in loads in Revit, the Control Band shows N0 Read only, and
ping / get_project_info / list_selection return structured JSON for an open
document with no write path present.

Sprint 2:

```text
Action Contract parser
Action Report writer
Action preview list
dry-run mode
```

Done = a sample Action Contract is parsed and rejected when malformed; a logical
dry-run produces a preview list and an Action Report with status dry_run, still
without committing any transaction.

Sprint 3:

```text
create_text_note
create_review_view
set review parameter
```

Done = the worked example above runs for real up to a committed text note, with
human approval before commit and an Action Report written; delete and model
modification remain absent.

Sprint 4:

```text
Warning Broker v0
preview panel
batch action list
```

Done = an inferred-position warning is classified A1 and shown in the preview
panel; an unknown failure id is treated as blocking by default; a batch of
annotation actions can be previewed and approved as one.

Only afterwards:

```text
schedules
view filters
detail lines
measurements
paint face
baseboards
wall type change
family sandbox
```

## 17. Absolute Forbidden Actions

Forbidden by default:

```text
execute arbitrary generated code
delete without explicit element list
modify linked model
commit without Action Report
write action without permission check
modify family directly in production
bulk modify without dry-run
edit central/workshared model without safety checks
unknown action type
```

## 18. Decisions to Arbitrate

To be decided before any build starts:

- Revit target version: 2026, 2027, or both
- Plugin name: recommended **Pantheon Revit Gate** (alias to avoid: "Pantheon
  Model Gate Revit"); final name is a human decision
- Initial communication: HTTP local first or MCP first
- Parameter prefix: PTN_ or Pantheon_
- Control profile storage location
- Policy expiration defaults
- First enabled write action
- Whether deletion remains fully disabled in v0

Critical notes to weigh during arbitration:

- The naming overlap with Pantheon Model Gate is a real risk. Recommendation:
  keep a single name, **Pantheon Revit Gate**, and do not adopt "Pantheon Model
  Gate Revit"; if both names ever survive, the boundary between "governs rights"
  (Model Gate) and "executes locally" (Revit Gate) must be documented at the same
  time, or the team will conflate them.
- HTTP-first is faster to debug but easier to leave open by accident; if chosen,
  bind it to localhost only and treat it as a development surface, not a product
  surface.
- Defaulting deletion to fully disabled in v0 is the conservative choice and is
  recommended; re-enabling later is a small change, while a wrong deletion is not
  reversible from outside Revit.
- Control profile storage should live with Pantheon Next governance, not inside
  the RVT; the RVT keeps only the lightweight references named in section 2.

## 19. Guiding sentence

```text
Pantheon Revit Gate transforms a governed intention into a controlled Revit transaction. It never executes a free intention.
```

## Appendix — Glossary

Short definitions for the acronyms used above, for a reader new to the project.

```text
PDP   — Policy Decision Point: decides allow/deny (here, Pantheon Model Gate). It does not execute.
PEP   — Policy Enforcement Point: applies the decision (here, the Revit Gate plugin), and may only narrow it.
RVT   — Revit project file (the open model the plugin would act on).
APU   — Architecture Project Understanding: the Pantheon belief/contract layer a run ref points back to.
VISA  — the architect's review/sign-off milestone referenced in the example review note.
N0–N7 — the control levels shown on the Control Band (section 4).
A0–A5 — the warning classes of the Warning Broker (section 8).
Pack  — a named group of future actions in section 11 (Read Pack, Annotation Pack, …).
PTN_  — prefix for the lightweight references stored in the RVT (PTN_ControlProfileId, …).
```
