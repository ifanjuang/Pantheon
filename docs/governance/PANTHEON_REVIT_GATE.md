# Pantheon Revit Gate — local architecture plugin framing

Status: candidate support doctrine — Pantheon Revit Gate framing. Repository state: documented non-implemented.
Boundary profile: candidate_support_note.

This dossier frames a **local Revit architecture plugin** governed by Pantheon. The plugin is runtime and lives outside Pantheon, on the architect's machine and/or Hermes local side. Pantheon governs the vocabulary of capability status, evidence, traceability, approval posture and later regulation. Nothing here is implemented.

It implements no plugin, no Revit add-in, no MCP server, no schema, no test, no Docker and no operations change. It does not claim the plugin exists.

## Current arbitration — V0 Free Exploration Mode

Decision status: accepted as a **sandbox / exploration orientation**, not as production policy.

```text
V0 Revit Plugin = free exploration mode.
Architecture only.
Offline local first.
Hermes may act through the plugin.
No heavy governance in V0.
Minimal traces are mandatory from the beginning.
Regulation comes later from observed use.
```

This updates the earlier read-only MVP posture without promoting any implementation. The conservative read-first model remains the safe production direction. The V0 exploration posture exists to learn which architectural actions are useful before freezing a strict control matrix.

The decision does **not** mean:

- the plugin exists;
- the repository implements a runtime;
- Pantheon executes Revit actions;
- Revit model changes are professionally validated by Hermes;
- deletion, save, sync or arbitrary code execution are safe.

It means:

- the first runnable plugin may be permissive in a sandbox;
- the interface should expose a broad architecture capability catalogue;
- actions may be tried freely on test copies;
- traces must be captured so the later governed version can be based on real usage rather than speculation.

## Purpose

The purpose is to design a local Revit plugin that lets an architect converse with the open model through Hermes and, eventually, execute architectural operations from controlled natural-language or graphical intents.

V0 is not a compliance gate. It is a learning instrument:

```text
free enough to discover useful workflows;
traced enough to regulate later;
local enough to respect the offline requirement;
explicit enough to avoid mistaking runtime success for professional validation.
```

## Placement

The plugin is an adapter/runtime surface, not Pantheon doctrine.

```text
OpenWebUI / dashboard exposes.
Hermes prepares, orchestrates and calls.
The Revit plugin executes locally inside Revit.
Pantheon records the capability grammar and later governance posture.
The human remains responsible for project decisions.
```

Pantheon owns only the documented classification of capability effects and the later rules for promotion, evidence, memory, scope and approval. Installation, local relay, MCP, Revit API calls, queues, async workers, transactions and logs are runtime concerns outside the Pantheon repository.

## Scope

V0 is **architecture only**.

In scope:

```text
project / document context
views, sheets, schedules
walls, floors, ceilings, roofs
rooms, areas and surfaces
doors, windows and openings
curtain walls and façade composition
stairs and railings, when architectural
families and types used for architecture
materials and finishes
parameters
annotations, detail lines, dimensions
local exports and view snapshots
visual context packs
sketch / detail-line interpretation
```

Out of scope for V0:

```text
MEP
HVAC
structure
loads / sizing / calculations
networked cloud automation
APS as required dependency
linked-model write control
central/workshared production automation
```

## V0 non-negotiable traces

Free exploration does not mean invisible execution. Even in permissive sandbox mode, every consequential Revit action should produce a minimal trace.

Required from the first writable prototype:

```text
1. Display the active RVT document name before action.
2. Use a named Revit transaction for every committed write.
3. Write a local action log.
4. List created, modified and deleted ElementIds where possible.
5. Keep a stop / disable-Hermes control visible in the plugin.
```

Preferred when feasible, but not mandatory for the earliest sandbox spike:

```text
preview or dry-run
before/after snapshot
affected-elements table
failure packet
rollback note
local evidence pack candidate
```

## Free Exploration profiles

The interface should expose profiles, but V0 may default to the permissive one.

| Profile | Intended use | Posture |
|---|---|---|
| `Sandbox libre` | Test file, local copy, disposable model | broad freedom, logs mandatory |
| `Projet agence` | Real project copy or low-risk work session | broad freedom, confirmation light, logs mandatory |
| `Client / production` | Engaging model | regulated later, not V0 default |
| `Locked client model` | Sensitive or contractual model | read / inspect only |

The V0 accepted profile is `Sandbox libre`. The other profiles are placeholders for later regulation.

## Capability registry posture

The plugin settings should expose a **Capability Registry** rather than hiding powerful functions.

Each capability row should carry at least:

```text
tool_id
label
domain
operation_family
read_create_modify_model_modify_delete_export
architecture_only flag
default_profile availability
risk note
requires_log
requires_named_transaction
requires_preview when known
disabled_reason when blocked
```

The registry is allowed to be permissive in V0, but it must already be structured enough to support future regulation.

## Target capability families

V0 exploration may list the full architecture surface, even if only part of it is initially implemented.

```text
Read / inspect
Create
Modify
Model
Parameterize
Annotate
Dimension
Views / sheets
Schedules
Materials / finishes
Families / types
Sketch / detail-line interpretation
Visual context pack
Export
Log / action report
```

Example capability groups:

- read document, active view, selection, visible elements, parameters and families;
- capture active view image and visual context pack;
- create walls, floors, ceilings, roofs, rooms, doors, windows, curtain walls, railings and architectural components;
- modify element position, type, level, phase, geometry and façade composition;
- write parameters on selection or filtered sets;
- create annotations, detail lines, filled regions, tags and dimensions;
- create or modify views, sheets, schedules, filters and graphic overrides;
- interpret selected detail lines as profiles, façade guides or modeling references;
- interpret an imported sketch as a composition candidate;
- export local images, CSV, JSON, PDF or IFC candidates;
- generate logs, action reports, before/after summaries and failure packets.

## V0 initial capability registry slice

This slice is the proposed first registry to display in the plugin and to guide implementation. It is still documentation only. It does not mean any tool exists.

The slice keeps the V0 wide enough for exploration, but small enough to build. The product principle is:

```text
context first;
selection second;
spatial understanding third;
method candidate before complex modeling;
write actions last;
log everything.
```

### Effect vocabulary

```text
read_only        observes Revit state and returns data
candidate_only   proposes, highlights, previews or reports without committing a model change
write_light      writes annotation, review view, review parameter or similarly low-risk data
write_model      creates or modifies architectural model geometry
external_effect  saves, syncs, executes code, touches central/workshared state or produces another external effect
export           writes an external local file
log              records what happened
blocked_v0       visible in registry, not enabled in first prototype
```

### Difficulty vocabulary

```text
low       normal Revit API wiring, few edge cases
medium    feasible but needs careful category/view/parameter handling
high      geometry, hosting, joins, phases, families or side effects
research  must be spiked before it is promised as available
```

### Core V0 registry

| Tool id | Purpose | Effect | Difficulty | V0 posture | Minimal trace |
|---|---|---|---|---|---|
| `revit.ping` | Check plugin connection and Revit availability | read_only | low | first build | timestamp, Revit version |
| `revit.get_project_info` | Read document title, path, units, worksharing signal and version | read_only | low | first build | document id/title |
| `revit.get_active_view` | Read active view metadata | read_only | low | first build | view id/name/type |
| `revit.capture_active_view` | Export local image of active view | read_only / export | medium | first build | image path, view id |
| `revit.list_selection` | Return selected elements and basic summaries | read_only | low | first build | selected ElementIds |
| `revit.selection_explain` | Explain selected elements in architectural language | read_only | medium | first build | selected ElementIds + categories |
| `revit.visible_elements_context` | Return visible walls, rooms, doors, windows and annotations for the active view | read_only | medium | first build | view id + visible ElementIds |
| `revit.visual_context_pack` | Bundle image + view + selection + visible elements + key parameters | read_only / export | medium | first build | context pack id |
| `revit.get_element_details` | Read one element deeply: category, family, type, host, level, phase, parameters | read_only | medium | first build | ElementId + UniqueId |
| `revit.read_parameters` | Read instance/type parameters for selected or visible elements | read_only | medium | first build | parameter names/ids + element refs |
| `revit.read_rooms` | Read rooms, areas, levels and boundaries where available | read_only | medium | first build | room ElementIds |
| `revit.read_walls_doors_windows` | Read architecture shell/openings in current scope | read_only | medium | first build | ElementIds grouped by category |
| `revit.read_sheets` | Read sheets, sheet numbers, titles, placed views and titleblock data | read_only | medium | first build | sheet ids |
| `revit.read_schedules` | Read schedule names, categories and fields where accessible | read_only | medium | first build | schedule ids |
| `revit.read_warnings` | Read Revit warnings and affected elements | read_only | medium | first build | warning ids + elements |
| `revit.define_work_area_from_selection` | Treat current selection as bounded work area | candidate_only | medium | first build | work area id + ElementIds |
| `revit.define_work_area_from_view` | Treat active view/crop as bounded work area | candidate_only | medium | first build | view id/crop signal |
| `revit.temporary_highlight_elements` | Highlight detected or proposed target elements | candidate_only | medium | first writable slice | highlighted ElementIds |
| `revit.temporary_number_elements` | Number elements in a review view or overlay for user confirmation | candidate_only | medium | first writable slice | numbering map |
| `revit.temporary_preview_geometry` | Show ghost geometry for a proposed door, line, wall or opening | candidate_only | high | candidate later | proposed geometry + refs |
| `revit.find_parallel_elements` | Find walls/lines parallel to selected reference | read_only | medium | first spatial slice | reference id + candidates |
| `revit.find_nearest_element` | Find nearest element of a target category to a reference | read_only | medium | first spatial slice | reference id + distance |
| `revit.project_point_to_element` | Project a source point to a target wall/line | candidate_only | high | first spatial slice | source, target, projection |
| `revit.detect_alignment_candidates` | Detect elements aligned with selected reference | candidate_only | high | later spatial slice | candidate refs + tolerance |
| `revit.propose_modeling_method` | Return possible Revit methods for an intent | candidate_only | medium | first build | method candidate id |
| `revit.record_modeling_method_choice` | Record selected method before modeling | log | low | first build | method id + user choice |
| `revit.preflight_host_check` | Check whether target wall can host a door/window | candidate_only | medium | first write preflight | host id + result |
| `revit.preflight_phase_check` | Check phase/design option consistency | candidate_only | medium | first write preflight | phase ids/status |
| `revit.preflight_group_pin_link_check` | Detect group, pinned element or linked-model target risk | candidate_only | medium | first write preflight | affected ids + risk |
| `revit.create_sandbox_view` | Create a review/sandbox view for visual testing | write_light | medium | first writable slice | transaction + view id |
| `revit.create_text_note` | Create a note in active/review view | write_light | low | first writable slice | transaction + note id |
| `revit.create_detail_line` | Create detail line/polyline in a view | write_light | medium | first writable slice | transaction + line ids |
| `revit.write_parameter_selected` | Write allowed instance parameter on selected elements | write_light | medium | first writable slice | before/after values |
| `revit.create_schedule_candidate` | Propose schedule fields, filters and grouping | candidate_only | medium | first documentation slice | schedule candidate id |
| `revit.create_schedule` | Create a simple schedule after candidate review | write_light | medium | first documentation slice | transaction + schedule id |
| `revit.create_sheet_candidate` | Propose sheet(s), titleblock and placed views | candidate_only | medium | first documentation slice | sheet candidate id |
| `revit.create_review_sheet` | Create a review sheet, not a production sheet | write_light | medium | later documentation slice | transaction + sheet id |
| `revit.export_context_json` | Export local JSON context pack | export | low | first build | file path + hash if available |
| `revit.export_view_image` | Export active/review view image | export | medium | first build | file path + view id |
| `revit.action_log_read` | Read local plugin action log | log | low | first build | log path/range |
| `revit.action_report_generate` | Generate local action report after a run | log / export | medium | first writable slice | report id + action refs |
| `revit.usage_log_summary` | Summarize used/failed/risky actions to inform later regulation | log | medium | later V0 | summary period + counts |

### Visible but not first-build tools

These tools should be visible in the registry because they express the intended direction. They should remain candidate or blocked until a dedicated Revit API spike proves the method.

| Tool id | Purpose | Effect | Difficulty | V0 posture | Why not first |
|---|---|---|---|---|---|
| `revit.create_door_on_wall` | Place door on selected/target wall | write_model | high | sandbox later | host, level, orientation, type and conflicts |
| `revit.create_window_on_wall` | Place window on selected/target wall | write_model | high | sandbox later | host, sill/header/type/orientation |
| `revit.create_aligned_door_candidate` | Propose door aligned by projection to reference door | candidate_only | high | candidate later | needs spatial primitives first |
| `revit.apply_aligned_door` | Commit aligned door placement | write_model | high | blocked first build | geometry and hosting side effects |
| `revit.propose_window_removal` | Propose delete/demolish/2D mark for a window | candidate_only | medium | candidate later | method choice needed |
| `revit.demolish_window` | Set demolition phase on a window | write_model | high | sandbox later | phase semantics and documentation impact |
| `revit.delete_window` | Delete a window | write_model | high | blocked_v0 | deletion is not a first-build primitive |
| `revit.read_selected_detail_lines` | Read selected detail/model lines as geometric guides | read_only | medium | candidate later | view-plane and coordinate mapping |
| `revit.convert_lines_to_profile_candidate` | Convert detail lines to wall-profile candidate | candidate_only | high | candidate later | geometry and wall matching |
| `revit.propose_wall_profile_edit` | Propose wall top/profile edit | candidate_only | research | research only | API/method spike required |
| `revit.apply_wall_profile_edit` | Commit wall profile edit | write_model | research | blocked_v0 | high model-risk operation |
| `revit.propose_curtain_wall_grid` | Propose curtain wall grid from sketch/lines | candidate_only | high | candidate later | types/mullions/panels required |
| `revit.create_curtain_wall` | Create curtain wall from accepted method | write_model | research | sandbox much later | family/type/grid complexity |
| `revit.assign_curtain_panels` | Assign glazed/opaque curtain panels | write_model | research | sandbox much later | panel family availability |
| `revit.load_family_sandbox` | Load family into sandbox/test document | write_model | high | blocked first build | family isolation required |
| `revit.purge_unused` | Purge unused content | write_model | high | blocked_v0 | broad irreversible effects |
| `revit.save_model` | Save RVT | external_effect | high | blocked_v0 | outside exploration action scope |
| `revit.sync_model` | Sync central/workshared model | external_effect | high | blocked_v0 | production/worksharing risk |
| `revit.execute_generated_code` | Execute arbitrary C#/script | external_effect | research | blocked_v0 | unrestricted code execution |

### First scenario to prove the registry

The first prototype should prove one complete loop, not a large number of tools:

```text
1. User selects one wall or façade area.
2. Plugin creates a visual context pack.
3. Hermes explains the selection and visible context.
4. Plugin highlights or numbers the relevant elements.
5. Hermes proposes one simple review action.
6. Plugin creates a TextNote or DetailLine in a sandbox/review view.
7. Plugin writes an action report.
```

This proves the product spine:

```text
see -> understand -> show -> propose -> act lightly -> log
```

Only after this loop works should geometry-writing tools be promoted into the sandbox surface.

## Visual context pack

Hermes should not rely only on text commands. The plugin should let the user send the active Revit context to Hermes.

A visual context pack may include:

```text
active view snapshot
view id and name
view type, scale and level
selected element ids
visible element ids
rooms / walls / doors / windows visible in the view
key parameters
user-drawn detail lines or model lines
optional cropped region
```

This is the preferred way to support commands such as:

```text
look at this façade
use these lines as the top profile of the wall
create a curtain wall composition from this sketch
place a door aligned to the selected reference door
remove or demolish the window nearest to the tree
```

Image-only interpretation is always weaker than image + Revit data. A sketch or screenshot may generate a method candidate, not a professional truth.

## Method-first modeling

For spatial or graphical commands, Hermes must propose a modeling method before the plugin applies a transaction in any regulated profile. In sandbox V0 this may be reduced to a light confirmation, but the method should still be recorded in the log.

Examples:

```text
intent: cut the top of walls along selected detail lines
possible_methods:
  - edit wall profile
  - void cut
  - attach wall to host
  - create graphic-only representation
  - create reference mass
```

```text
intent: compose curtain wall from sketch
possible_methods:
  - Revit curtain wall with grid and mullions
  - independent window/panel families
  - 2D façade drafting only
```

The method is part of the trace because the method changes quantities, model semantics, documentation and future edits.

## Async posture

Async is allowed for analysis and preparation, not for uncontrolled model mutation.

Allowed async work:

```text
context extraction from a snapshot
Hermes analysis
sketch interpretation
candidate generation
preview table preparation
report generation
local export preparation
```

Committed Revit model changes still occur through the plugin in the Revit context, using a named transaction. If the model changed between candidate generation and execution, the action should be marked stale when the plugin can detect it.

## MCP / API binding

MCP is optional. The safer development sequence is:

```text
Phase 1: local plugin API / local relay for debugging
Phase 2: MCP wrapper around the same capability registry
Phase 3: stricter governed handoff once real use is understood
```

MCP must not become the authority layer. It is a transport / adapter. The same action should carry the same capability id and trace whether it arrives through local API, MCP or another local bridge.

## Free exploration versus production regulation

The current working distinction:

| Mode | Purpose | Governance posture |
|---|---|---|
| Free exploration | learn uses, prototype broad actions | permissive, trace mandatory |
| Guided agency use | useful project work, still local | confirmation light, preview when feasible |
| Regulated production | model-changing consequential work | preview, affected elements, approval, report |
| Locked / sensitive | client-sensitive or contractual file | read-only / inspect |

The later Pantheon-regulated version should be built from logs and observed failures, not from a premature theoretical matrix.

## Boundary

- No plugin, add-in, MCP server, runtime, schema, test, Docker or operations change is added.
- V0 Free Exploration Mode is a documented orientation, not an implementation.
- The Revit plugin executes locally outside Pantheon.
- Hermes may orchestrate and call the plugin.
- Pantheon remains the governance vocabulary and later status/approval layer.
- The human decides whether the resulting workflow is acceptable in practice.

## Governance references

- docs/governance/STATUS.md
- docs/governance/CAPABILITY_PLACEMENT.md
- docs/governance/MODULAR_DOMAIN_REORIENTATION.md
- docs/governance/DOMAIN_PACK_SPEC.md
- docs/governance/PANTHEON_REVIT_GATE_DEVELOPER_DOSSIER.md
- docs/domain-packs/architecture/PROJECT_UNDERSTANDING_ADAPTER_CONTRACT.md
- docs/domain-packs/architecture/PROJECT_ANATOMY_MODEL.md
