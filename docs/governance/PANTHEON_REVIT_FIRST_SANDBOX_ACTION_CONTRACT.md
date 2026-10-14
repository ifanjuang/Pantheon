# Pantheon Revit — First Sandbox Action Contract

Status: candidate support doctrine — first Revit sandbox action contract. Repository state: documented non-implemented.
Boundary profile: candidate_support_note.

This document defines the first bounded Revit sandbox action contract for the future local Revit plugin / Hermes-side adapter.

It does not implement a Revit plugin.

It does not add a Revit add-in, `.addin` manifest, C# project, local relay, MCP server, schema, test, Docker file, operations file, platform service, runtime worker, queue, scheduler, OpenWebUI plugin, Hermes skill or production automation.

## Purpose

The Revit work must prove one complete loop before widening the capability surface.

The first loop is:

```text
context pack
-> method candidate
-> light confirmation
-> write_light action
-> action log
-> action report candidate
```

This contract turns the broad Revit sandbox exception into a small buildable spine.

It remains documentation-only.

## Scope

Profile:

```text
Sandbox libre only
```

Model scope:

```text
local disposable RVT file
local copy of a real model when explicitly treated as disposable
not workshared production
not central model
not linked-model write target
not contractual client model
```

Domain scope:

```text
architecture only
```

Allowed effect ceiling:

```text
read_only
candidate_only
write_light
log
export local report/context only
```

Forbidden in this first contract (never granted):

```text
write_model
external_effect
save
sync
purge
delete
linked-model write
family load into production
arbitrary generated code execution
MCP exposure
hidden scheduler
hidden queue
memory promotion
professional validation
```

## First scenario

The first scenario should prove the product spine with the smallest useful action:

```text
1. User opens a disposable Revit model or sandbox copy.
2. User selects one wall, façade area, room, view region or annotation target.
3. Plugin reads the active document and active view.
4. Plugin creates a Visual Context Pack Candidate.
5. Hermes explains the context and proposes one method candidate.
6. User confirms a light review action.
7. Plugin creates a sandbox/review view, TextNote or DetailLine.
8. Plugin writes an Action Log Candidate.
9. Plugin generates an Action Report Candidate.
```

Recommended first write action:

```text
create_text_note
```

Fallback first write action:

```text
create_detail_line
```

Optional helper action:

```text
create_sandbox_view
```

## Contract envelope

### Input

```text
Revit Sandbox Action Contract Candidate
```

Minimum fields:

```text
contract_id
capability_id: revit_local_adapter
profile: Sandbox libre
active_document_required: true
active_view_required: true
selection_required: true
allowed_effects
forbidden_effects
expected_context_pack
expected_method_candidate
expected_write_light_action
expected_action_log
expected_action_report
stop_control_required
```

### Output

```text
Revit Sandbox Action Result Candidate
```

Minimum fields:

```text
contract_id
runtime: Revit local plugin / Hermes local side
status
active_document_summary
active_view_summary
context_pack_ref
method_candidate_ref
user_confirmation_ref
transaction_summary
affected_element_ids
action_log_ref
action_report_ref
blockers
warnings
capability_gaps
```

These shapes are governance-readable candidate forms. They are not schemas and not executable runtime contracts.

## Required preflight

Before any `write_light` transaction, the plugin should check:

```text
active document name
Revit version when available
active view id/name/type
worksharing signal when available
profile = Sandbox libre
disposable/sandbox flag visible to user
selection exists when required
write_light action is allowed
stop / disable-Hermes control visible
```

If the model appears to be production, workshared central, linked target or locked client model, the action must move to:

```text
blocked_profile
```

or:

```text
read_only_only
```

## Visual Context Pack Candidate

Minimum contents:

```text
context_pack_id
active_document_title
active_document_path_hash_or_redacted_path
revit_version_when_available
active_view_id
active_view_name
active_view_type
active_view_scale_when_available
selected_element_ids
selected_element_summaries
visible_element_summaries_when_reasonable
snapshot_ref_when_available
key_parameters
created_at
```

The context pack is a runtime observation candidate. It is not evidence by itself.

## Method Candidate

Before the write action, Hermes should return a method candidate.

For the first contract, acceptable methods are intentionally simple:

```text
add review TextNote in active/review view
add review DetailLine in active/review view
create sandbox/review view then add review TextNote
create sandbox/review view then add review DetailLine
```

The method candidate must include:

```text
method_candidate_id
intent_summary
selected_method
alternatives_considered
reason_for_selected_method
expected_effect
risk_note
confirmation_required
```

The method candidate must not claim architectural correctness, regulatory compliance, constructability or professional validation.

## Light confirmation

In `Sandbox libre`, confirmation may be light but must exist.

Allowed forms:

```text
button confirmation
short chat confirmation
plugin confirmation dialog
dashboard action confirmation
```

The confirmation record should include:

```text
confirmation_id
user_visible_action_summary
profile
allowed_effect
timestamp
```

No confirmation is required for read-only context extraction, but confirmation is required before committed `write_light`.

## Write-light action

### `create_text_note`

Allowed when:

```text
active view supports text notes
annotation target is in current view
text content is review-only
profile is Sandbox libre
transaction can be named
```

Transaction name:

```text
Pantheon Revit Gate — sandbox create text note
```

Required trace:

```text
transaction_name
created_text_note_element_id
view_id
text_preview_or_hash
method_candidate_id
confirmation_id
```

### `create_detail_line`

Allowed when:

```text
active view supports detail lines
line geometry is view-local
profile is Sandbox libre
transaction can be named
```

Transaction name:

```text
Pantheon Revit Gate — sandbox create detail line
```

Required trace:

```text
transaction_name
created_detail_line_element_ids
view_id
geometry_summary
method_candidate_id
confirmation_id
```

### `create_sandbox_view`

Allowed when:

```text
source view is eligible for duplication or a review view can be created safely
new view name is clearly marked as sandbox/review
profile is Sandbox libre
transaction can be named
```

Transaction name:

```text
Pantheon Revit Gate — sandbox create review view
```

Required trace:

```text
transaction_name
created_view_id
source_view_id_when_applicable
view_name
method_candidate_id
confirmation_id
```

## Blocker handling

The first contract must support action-level blockers.

Blockers do not automatically fail the whole run if independent steps can continue.

Common blockers:

```text
no_active_document
no_active_view
empty_selection
unsupported_view_type
view_cannot_host_annotation
missing_text_note_type
invalid_line_geometry
workshared_or_central_model
locked_client_profile
stale_context
user_cancelled
stop_control_used
```

Blocker record candidate:

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

Example:

```text
action: create_text_note
blocker_type: view_cannot_host_annotation
blocking_scope: write_light_only
can_continue_independent_actions: true
resume_condition: user switches to compatible view or plugin creates sandbox view
status: waiting_user
```

## Action states

Allowed action states:

```text
planned
ready
running
waiting_user
waiting_resource
preview_ready
blocked_profile
blocked_preflight
blocked_missing_type
blocked_unsupported_view
blocked_worksharing
stale_context
committed
rolled_back
failed
skipped
superseded
```

Pantheon may display these states. Pantheon must not schedule, queue or execute them.

## Action Log Candidate

Every committed `write_light` action must produce a local action log record.

Minimum record:

```text
action_id
contract_id
timestamp
profile
active_document_title
active_view_id
action_type
effect: write_light
transaction_name
created_element_ids
modified_element_ids
deleted_element_ids
method_candidate_id
confirmation_id
status
warnings
blockers
```

For this first contract, `deleted_element_ids` should normally be empty.

If deletion occurs unexpectedly, the action must be marked:

```text
failed_or_needs_review
```

and the report must surface it clearly.

## Action Report Candidate

After the run, Hermes or the plugin may generate a report candidate.

Minimum report:

```text
report_id
contract_id
summary
profile
model_scope
context_pack_ref
method_candidate_ref
actions_attempted
actions_committed
actions_blocked
affected_element_ids
warnings
capability_gaps
user_next_decision
```

The report is not proof and not professional validation.

It may support later governance review.

## Human stop control

The plugin UI must expose a stop / disable-Hermes control before any writable prototype is considered acceptable.

The stop control should cause future actions in the current run to move to:

```text
skipped
```

or:

```text
user_cancelled
```

It must not silently roll back already committed Revit transactions unless the plugin has a safe, explicit rollback operation and the user confirms it.

## Promotion rule

This first contract is successful only if it demonstrates:

```text
context pack created
method candidate produced
user understood intended write_light action
named Revit transaction committed
created ElementIds captured
local action log written
action report generated
blockers surfaced without global collapse
no save/sync/purge/delete/external effect occurred
```

Only after repeated successful runs should additional Revit actions be considered.

Promotion path:

```text
first_contract_documented
-> sandbox_spike_candidate
-> observed_use
-> failure_review
-> capability_gap_review
-> guided_agency_candidate
```

No success in this first contract authorizes production model mutation.

## Relationship to other Revit doctrine

This file specializes:

```text
docs/governance/PANTHEON_REVIT_LOCAL_SANDBOX_EXCEPTION.md
```

It remains compatible with:

```text
docs/governance/PANTHEON_REVIT_GATE.md
docs/governance/PANTHEON_REVIT_GATE_2027_PROTOTYPE_PLAN.md
docs/governance/PANTHEON_REVIT_GATE_DEVELOPER_DOSSIER.md
docs/governance/PANTHEON_CONTROL_PLANE_BOUNDARY.md
docs/governance/HERMES_CAPABILITY_BINDINGS.md
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
Prove one Revit loop first.
Keep it local.
Keep it sandbox.
Write lightly.
Trace everything.
Do not promote runtime success into professional validation.
```
