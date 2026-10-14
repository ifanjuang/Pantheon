# Revit Operation and Action Report Contract

Status: supporting contract candidate — documented non-implemented — subordinate to `docs/governance/REVIT_LOCAL_ADAPTER.md`.

This document defines the technical envelopes exchanged around one Revit operation.

It does not define business status, workflow execution, approval policy or Evidence admission.

## Envelope family

```text
Adapter Operation Request
-> asks for one typed operation

Preflight Report
-> observes technical feasibility

Action Authorization
-> authorizes one exact consequential effect

Action Report
-> records what the add-in technically performed

Runtime Return
-> normalizes the Hermes return to Pantheon
```

## Adapter Operation Request

```yaml
schema_version: 1
request_id: request-381
action_id: action-019
created_at: 2026-08-06T22:00:00+02:00

correlation:
  project_ref: project-tilleul
  task_contract_ref: task-control-rdc-001
  context_pack_ref: context-project-tilleul-rdc-004
  policy_decision_ref: policy-104
  handoff_ref: handoff-001
  runtime_run_ref: hermes-run-091

binding:
  binding_id: revit-host-workstation-01
  instance_id: revit-2026-pid-18440
  expected_manifest_digest: sha256:...

capability:
  capability_id: building_model.observe.spaces
  operation_id: revit.rooms.snapshot.v1
  operation_version: 1
  effect_class: read_only

target:
  document_ref: revit-document://project-tilleul/model-a
  expected_snapshot_id: revit-snapshot-72
  expected_freshness_token: sha256:...
  scope:
    level_refs:
      - revit-level://rdc
    element_refs: []

arguments:
  include_boundaries: true
  include_doors: true
  include_parameters:
    - builtin://ROOM_NAME
    - builtin://ROOM_NUMBER
    - builtin://ROOM_AREA

idempotency:
  key: task-control-rdc-001.rooms
  posture: repeatable_observation

authorization_ref: null
```

The add-in receives structured arguments, not a natural-language instruction.

## Request validation

Before dispatch, the Host Agent should verify:

```text
schema version supported
binding and instance present
manifest digest matches
operation exists in the closed registry
effect class matches operation definition
Task Contract and handoff references present
document and scope are syntactically bounded
authorization present when required
payload size and geometry level within limits
```

Validation at the Host Agent does not replace the add-in's Revit-context checks.

## Preflight Report

A consequential operation must produce a fresh preflight.

```yaml
preflight_id: preflight-009
request_ref: request-412
request_digest: sha256:...
observed_at: 2026-08-06T22:02:00+02:00
status: blocked | ready_with_warnings | technically_ready

binding:
  binding_id: revit-host-workstation-01
  instance_id: revit-2026-pid-18440
  manifest_digest: sha256:...

document:
  document_ref: revit-document://project-tilleul/model-a
  match: true
  current_freshness_token: sha256:...
  expected_freshness_match: true
  read_only: false
  workshared: true

targets:
  requested: 14
  resolved: 14
  missing: 0
  pinned: 1
  grouped: 2
  linked: 0
  constrained: 0
  worksharing_conflicts: 1

predicted_effects:
  created_count: 0
  modified_count: 14
  deleted_count: 0
  categories:
    - OST_Doors

transaction:
  proposed_name: PantheonRevit:task-041:action-009:change-door-type
  policy: all_or_nothing
  rollback_posture: transaction_rollback_available

blockers:
  - code: worksharing_conflict
    target_ref: revit-element://door-03
    detail: owned_by_other_user

warnings:
  - code: grouped_targets
    count: 2

forbidden_effects_found: []
preflight_digest: sha256:...
```

```text
technically_ready != authorized
```

## Action Authorization

The server issues an authorization only after the required human decision.

```yaml
authorization_id: authorization-203
issued_at: 2026-08-06T22:04:00+02:00
expires_at: 2026-08-06T22:14:00+02:00
single_use: true
status: active

correlation:
  project_ref: project-tilleul
  task_contract_ref: task-041
  decision_ref: decision-088
  action_id: action-009

bound_to:
  request_digest: sha256:...
  preflight_digest: sha256:...
  binding_id: revit-host-workstation-01
  instance_id: revit-2026-pid-18440
  document_ref: revit-document://project-tilleul/model-a
  freshness_token: sha256:...

effect:
  effect_class: write_model
  permitted_operation: revit.element.change_type.v1
  permitted_operation_version: 1
  target_refs:
    - revit-element://door-01
  maximum_targets: 14
  forbidden_effects:
    - save
    - sync
    - delete
    - linked_model_write
```

The authorization is invalid when any bound value differs.

The authorization is not a reusable role permission or plugin setting.

## Write recheck

Immediately before opening a transaction, the add-in must recheck:

```text
authorization active and unused
request and preflight digests
binding and instance
document identity
freshness token
operation and version
target identity
target count
effect ceiling
forbidden effects
Revit document modifiability
```

A failed recheck returns a refusal and performs no mutation.

## Action Report

```yaml
action_report_id: report-819
request_ref: request-412
authorization_ref: authorization-203
reported_at: 2026-08-06T22:05:00+02:00

binding:
  binding_id: revit-host-workstation-01
  instance_id: revit-2026-pid-18440
  plugin_version: 0.1.0
  host_agent_version: 0.1.0
  revit_version: "2026"
  manifest_digest: sha256:...

document:
  document_ref: revit-document://project-tilleul/model-a
  freshness_before: sha256:...
  freshness_after: sha256:...

transaction:
  name: PantheonRevit:task-041:action-009:change-door-type
  policy: all_or_nothing
  status: committed
  started_at: 2026-08-06T22:04:30+02:00
  finished_at: 2026-08-06T22:04:31+02:00

effects:
  created: []
  modified:
    - element_ref: revit-element://door-01
      element_id: 34567
      before_digest: sha256:...
      after_digest: sha256:...
  deleted: []

item_results:
  - target_ref: revit-element://door-01
    status: succeeded
    warnings: []

warnings: []
failures: []

rollback:
  performed: false
  available_during_transaction: true
  manual_reversal_required: false
  note: null

authorization_consumption:
  status: consumed
  consumed_at: 2026-08-06T22:04:31+02:00

report_digest: sha256:...
```

## Observation report

Read-only operations may use the same report family without transaction or authorization fields.

They should still record:

```text
request correlation
binding and manifest
document and snapshot
operation and arguments
start and finish times
result reference
warnings
limitations
freshness
```

## Append-only event record

The implementation may project action events such as:

```text
request_validated
request_refused
external_event_queued
execution_started
preflight_completed
authorization_verified
transaction_started
transaction_committed
transaction_rolled_back
action_reported
```

Events should have their own occurrence timestamps and deterministic causal references.

The event stream is a technical audit trail. It is not Evidence by itself.

## Status separation

The return must keep at least these axes separate:

```text
transport_status
host_validation_status
revit_execution_status
transaction_status
runtime_task_status
governance_result_status
human_review_status
```

Forbidden collapse:

```text
transport sent = operation executed
operation executed = transaction committed
transaction committed = result accepted
result accepted = Evidence admitted
```

## Refusal report

```yaml
action_report_id: report-refused-01
request_ref: request-412
status: refused
refusal:
  code: refused_stale_document
  detail: document_freshness_mismatch
  safe_next_step: request_new_snapshot_and_preflight
effects:
  created: []
  modified: []
  deleted: []
transaction:
  status: not_started
```

A refusal that prevents unauthorized or stale work is a valid safe outcome.

## Redaction

The report must not expose:

```text
raw credentials
access tokens
unnecessary filesystem paths
unrelated user identities
full model payloads unrelated to the request
```

Technical details needed to diagnose Revit failures may be retained under the project's access policy.

## Evidence posture

```text
Action Report
-> technical receipt candidate

Execution Result
-> persisted runtime record

Result Candidate
-> interpreted output

Evidence Pack Candidate
-> selected supporting material

Evidence
-> separately admitted
```

```text
action_report != Evidence
successful transaction != professional validation
before/after digest != semantic correctness
```

## Planning boundary

This contract defines shapes and invariants only.
