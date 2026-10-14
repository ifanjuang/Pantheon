# Pantheon Revit Local Sandbox Exception

Status: candidate support doctrine — Revit local sandbox exception. Repository state: documented non-implemented.
Boundary profile: candidate_support_note.

This document defines a controlled exception for early Revit local sandbox exploration through a future local plugin / Hermes-side adapter.

It does not implement a Revit plugin.

It does not add a Revit add-in, `.addin` manifest, C# project, MCP server, schema, test, Docker file, operations file, platform service, runtime worker, queue, scheduler, connector, OpenWebUI plugin or production automation.

## Purpose

Revit is not a passive external source. It is a professional modeling environment with live geometry, views, families, phases, parameters, transactions, worksharing and documentation effects.

A strict read-only-only posture would slow discovery of useful architectural workflows. A fully permissive production posture would be unsafe.

This exception allows a narrow middle path:

```text
Explore freely in sandbox.
Trace everything.
Promote only what survived real use.
Regulate production later.
```

## Core exception

For local disposable Revit models or explicit sandbox copies, Hermes may execute exploratory read, candidate, preview and `write_light` actions through the local Revit plugin with light confirmation and mandatory trace.

For real project, production, workshared, linked or contractual models, Pantheon gates apply progressively.

The exception never covers:

```text
save model
sync central
purge unused
delete model content as a first-build primitive
write to linked models
execute arbitrary generated code
load unreviewed families into production
silent worksharing mutation
external publication or transmission
professional validation by runtime success
```

## Profiles

| Profile | Intended use | Posture |
|---|---|---|
| `Sandbox libre` | Test file, local copy, disposable model | broad freedom, logs mandatory |
| `Projet agence` | Real project copy or low-risk agency session | broad freedom, light confirmation, logs mandatory |
| `Client / production` | Engaging model | preview, affected elements, approval, report |
| `Locked client model` | Sensitive, contractual or workshared model | read / inspect only |

The accepted V0 profile is `Sandbox libre` only.

## Mandatory traces

Even in free sandbox mode, every committed Revit write must produce a minimal trace.

Required from the first writable prototype:

```text
active RVT document name before action
Revit version when available
named Revit transaction for every committed write
local action log
created ElementIds where possible
modified ElementIds where possible
deleted ElementIds where possible
failure packet when available
visible stop / disable-Hermes control
```

Preferred when feasible:

```text
dry-run or preview
before / after snapshot
affected-elements table
rollback note
local evidence pack candidate
method candidate id
user confirmation event
```

## Effect classification

### `read_only`

Observes Revit state and returns data.

Examples:

```text
read active document
read active view
read selection
read visible elements
read element parameters
capture active view image
export context pack
```

### `candidate_only`

Proposes, highlights, previews or reports without committing model changes.

Examples:

```text
highlight proposed targets
number elements temporarily
propose modeling method
preflight host check
preflight phase check
preflight pinned/group/link check
```

### `write_light`

Writes low-risk review information inside the local model or review view.

Examples:

```text
create sandbox view
create text note
create detail line
create simple review schedule
write allowed review parameter
create local action report
```

`write_light` is allowed earlier in sandbox than general model mutation, but it still requires named transactions and logs.

### `write_model`

Creates, modifies or demolishes architectural model geometry.

Examples:

```text
create door
create window
modify wall profile
demolish window
create curtain wall
assign curtain panel
load family into model
```

`write_model` remains visible in the registry but should not be first-build unless separately spiked and bounded.

### `external_effect`

Changes persistence, shared state, execution environment or external commitments.

Examples:

```text
save RVT
sync central
publish
send
purge
run arbitrary generated code
start server
expose MCP
```

`external_effect` is blocked by this exception.

## Visible capability rule

```text
capability_visible != capability_enabled
sandbox_action != production_approval
Revit_transaction_success != professional_validation
write_light != write_model
model_local_action != external_communication
```

The plugin may display future capabilities so the user understands the intended direction, but display does not authorize execution.

## Blockers and non-blocking dialogue

Revit actions often fail because the model lacks a precondition rather than because the intent is invalid.

Examples:

```text
missing annotation family
missing titleblock
missing door type
missing material
pinned element
group member
linked-model target
worksharing lock
stale selection
phase mismatch
design option mismatch
invalid host
view cannot host annotation
```

Hermes and the plugin should treat these as action-level blockers, not global failures when independent work can continue.

### Blocker record shape

```text
blocker_id
action_id
blocker_type
blocking_scope
affected_element_ids
required_user_or_plugin_action
can_continue_independent_actions
resume_condition
status
```

This is a governance-readable candidate shape, not an executable schema.

### Example: missing family

```text
action: create_annotation
blocker_type: missing_family
required_resolution: load or select valid annotation family
can_continue_independent_actions: true
dependent_actions: wait
independent_actions: continue
```

## Action state vocabulary

Revit adapter actions may use:

```text
planned
ready
running
waiting_user
waiting_resource
blocked_missing_family
blocked_invalid_host
blocked_pinned_element
blocked_group_member
blocked_linked_model
blocked_worksharing
blocked_phase_or_option
stale_context
preview_ready
committed
rolled_back
failed
skipped
superseded
```

These states support recursive and dependent procedural work without turning Pantheon into a scheduler or queue.

## Dependency posture

Revit work may contain multiple procedural actions.

```text
simple action
procedural action dependent on previous result
procedural action independent of blocked branch
recursive refinement loop
```

Allowed in sandbox:

```text
continue independent read_only or candidate_only actions
continue independent write_light actions when scoped and logged
pause dependent writes until blocker is resolved
ask user through non-blocking dialogue
resume after explicit user/plugin signal
```

Forbidden:

```text
silently bypass blocker
load family into production without approval
write to linked model because local target failed
change method silently after user selected another method
continue stale write after model changed materially
promote runtime workaround to doctrine
```

## Async posture

Async is allowed for analysis and preparation:

```text
context extraction from snapshot
Hermes analysis
sketch interpretation
candidate generation
preflight table preparation
report generation
local export preparation
```

Committed model changes must occur through the local Revit plugin in Revit context, using named transactions and freshness checks when possible.

If model context changes between candidate generation and execution, the action should be marked:

```text
stale_context
```

and should be rechecked before commit.

## Method-first modeling

Spatial or graphical commands should produce a method candidate before transaction in all regulated profiles.

In sandbox V0, this can be a light confirmation, but the selected method must still be recorded.

Example:

```text
intent: create curtain wall composition from sketch
method_candidates:
  - Revit curtain wall with grids and mullions
  - window/panel family array
  - 2D drafting representation only
  - reference mass / guide geometry
```

The method changes future edits, quantities, schedules, documentation and responsibility. Therefore, the method is part of the trace.

## Human responsibility

The user remains responsible for deciding whether a resulting Revit workflow is acceptable.

Hermes may propose and execute bounded sandbox actions.

Pantheon may later regulate, classify and promote successful patterns.

No Revit transaction, log entry, preview or successful API call validates architectural quality or professional responsibility.

## Production promotion rule

A sandbox action may be considered for production only after review of:

```text
observed use
failure logs
affected element patterns
rollback feasibility
family/type dependencies
phase/design option behavior
worksharing risk
user acceptance
professional consequence
```

Promotion path:

```text
sandbox_visible
-> sandbox_enabled
-> observed_use
-> failure_review
-> guided_agency_candidate
-> regulated_profile_candidate
-> production_gate
```

No action jumps directly from sandbox success to production approval.

## Relationship to Pantheon Control

Control-plane status and non-equivalence rules are defined in:

```text
docs/governance/PANTHEON_CONTROL_PLANE_BOUNDARY.md
```

The Revit capability slot is listed in:

```text
docs/governance/HERMES_CAPABILITY_BINDINGS.md
```

The broader Revit plugin framing remains:

```text
docs/governance/PANTHEON_REVIT_GATE.md
```

## Status

```text
implemented: no
runtime_added: no
schemas_added: no
protected_paths_touched: no
repo_state: documented non-implemented
```

## Final rule

```text
Revit deserves a local sandbox exception.
It does not deserve a governance exception.
Sandbox exploration may be freer.
Production remains governed.
Trace everything.
The human decides.
```
