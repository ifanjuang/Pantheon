# Revit Local Adapter Execution Model

Status: supporting execution contract — documented non-implemented — subordinate to `docs/governance/REVIT_LOCAL_ADAPTER.md`.

This document defines execution semantics only. It is not a scheduler, queue, workflow engine or approval mechanism.

## Execution layers

```text
governance state
-> owned by Pantheon / pantheon-mvp

runtime reasoning state
-> owned by Hermes

transport state
-> owned by the Host Agent

Revit technical state
-> owned by the add-in and live document
```

These states must remain separately visible.

## Required correlation

Every request and return should carry or reference:

```text
project_ref
task_contract_ref
context_pack_ref
policy_decision_ref
handoff_ref
runtime_run_ref
binding_id
instance_id
document_ref
snapshot_id
request_id
action_id
idempotency_key
authorization_ref when applicable
```

## Operation lifecycle

A technical operation may pass through:

```text
prepared
validated
dispatched
accepted_by_host
queued_for_external_event
executing
succeeded
partial
refused
failed
timed_out
cancelled_before_execution
rolled_back
```

This is a technical lifecycle. It does not replace WorkIssue, DecisionRequest or task business status.

## Read-only flow

```text
1. Hermes receives one governed handoff.
2. Hermes selects an admitted capability.
3. Hermes prepares an Adapter Operation Request.
4. The Host Agent validates schema, binding and correlation.
5. The add-in resolves the requested Revit instance.
6. The add-in executes through the Revit thread.
7. The add-in returns a source-linked observation.
8. Hermes interprets the observation inside the Task Contract.
9. pantheon-mvp persists the Execution Result and reviewable candidates.
```

Read-only does not mean globally unrestricted. Project, document, view, selection and category scope still apply.

## Candidate-only flow

Candidate-only operations may affect temporary UI state but not persisted model state.

Examples:

```text
highlight elements
temporary isolate
zoom to targets
temporary graphics
prepare a preview
capture a view
```

The operation must report whether temporary state was changed and whether it was restored.

Temporary UI state is not a project decision.

## Consequential write flow

```text
1. Hermes or a deterministic preparation step produces a ChangeCandidate.
2. The add-in resolves the current document and targets.
3. The add-in returns a Preflight Report.
4. Cockpit exposes effects, warnings and blockers.
5. A human records the exact decision.
6. pantheon-mvp issues a single-use Action Authorization.
7. The Host Agent forwards the authorized request.
8. The add-in verifies authorization binding and freshness again.
9. The add-in enters one named Transaction or TransactionGroup.
10. The add-in commits, rolls back or returns a partial technical result.
11. The add-in emits an Action Report.
12. Hermes returns a Result Candidate and trace.
13. The human separately reviews the result.
```

The authorization does not allow method substitution. Any material change to targets, operation, arguments or predicted effects requires a new preflight and decision.

## Revit-thread discipline

All Revit API access must run in an allowed Revit execution context.

A modeless UI or Host Agent request should use `ExternalEvent` or an equivalent reviewed mechanism.

The add-in must not:

```text
call the Revit API from an arbitrary background thread
block the Revit UI while waiting for Hermes reasoning
hold a transaction open across a network or model call
start a transaction before human authorization
silently retry a failed write with changed arguments
```

## Transaction discipline

Transaction naming:

```text
PantheonRevit:<task_id>:<action_id>:<short_effect>
```

One métier intention should normally correspond to one transaction or one explicitly documented TransactionGroup.

For bulk operations, the contract must define:

```text
all_or_nothing
best_effort_with_item_results
grouped_by_independent_scope
```

The chosen policy must be visible before authorization.

## Freshness

A Revit Context Snapshot must carry independent document, view and selection
freshness observations.

Each operation consumes only the scopes declared by the closed Operation
Registry. Current scope inputs are:

```text
document -> document identity, version and material document state
view -> active view, phase and design option
selection -> exact current selection
```

A mismatch returns the corresponding `refused_stale_document`,
`refused_stale_view` or `refused_stale_selection`. A wrong document remains
`refused_document_mismatch`.

The add-in must not silently refresh targets and continue a consequential write.

## Idempotency

Each operation declares one posture.

```text
repeatable_observation
-> repeated execution is expected and returns a new observation

idempotent_effect
-> repeated request with the same key must not duplicate the effect

single_use_effect
-> authorization and request may be consumed once only

non_repeatable_effect
-> automatic retry is forbidden
```

The Host Agent may retry transport delivery only when the operation contract and server receipt make duplicate execution impossible.

## Cancellation

Cancellation has distinct meanings.

```text
cancel_before_dispatch
cancel_before_external_event_execution
cannot_cancel_revit_api_call_in_progress
rolled_back_after_failure
```

A cancellation request does not imply that Revit stopped unless the add-in confirms it.

## Partial result

A partial technical result may occur when the operation contract allows per-item handling.

It must include:

```text
requested target count
resolved target count
successful target refs
failed target refs
skipped target refs
failure reason per target
transaction policy used
committed effects
rolled-back effects
```

A partial result is not silently converted to success.

## Refusal families

### Binding and capability

```text
refused_binding_not_found
refused_binding_not_admitted
refused_manifest_mismatch
refused_capability_not_supported
refused_capability_disabled
refused_capability_unavailable
```

### Scope and identity

```text
refused_project_mismatch
refused_document_mismatch
refused_view_mismatch
refused_scope_violation
refused_target_missing
refused_linked_target
```

### Freshness and concurrency

```text
refused_stale_document
refused_stale_view
refused_stale_selection
refused_worksharing_conflict
refused_document_read_only
refused_transaction_busy
refused_revit_context_unavailable
```

### Authorization

```text
refused_authorization_missing
refused_authorization_expired
refused_authorization_used
refused_authorization_mismatch
refused_preflight_mismatch
```

### Effect and safety

```text
refused_forbidden_effect
refused_arbitrary_code
refused_save_or_sync
refused_linked_model_write
refused_precondition_failed
```

## Failure handling

A Revit exception or Failure API event should be normalized without hiding the original technical information.

The return should preserve:

```text
exception family
Revit failure id when available
user-readable summary
technical message
affected targets
transaction state
rollback state
manual-reversal note
```

Sensitive local paths and credentials must be redacted.

## Worksharing

Before a write, the add-in should observe:

```text
workshared state
central/local posture
active workset
target worksets
ownership
borrowability
editing requests required
synchronization status when observable
```

The adapter must not automatically synchronize with central.

## Groups, hosts and constraints

A preflight should identify at least:

```text
pinned elements
group membership
nested groups
host relationships
dependent elements
constraints
design-option ownership
phase constraints
linked-model ownership
```

The operation contract must state whether these are blockers or warnings.

## Runtime continuation

Hermes may continue only work that is independent of the blocked Revit operation and already admitted by the Task Contract.

The system must not create a hidden resume queue for stale writes.

A resumed write requires:

```text
fresh context
fresh preflight
still-valid ChangeCandidate
new or still-valid authorization according to policy
```

## Result semantics

```text
transport delivered != Revit executed
Revit executed != transaction committed
transaction committed != task succeeded
task succeeded != result accepted
result accepted != Evidence admitted
```

The add-in returns technical facts. Hermes may produce interpretation candidates. Pantheon and the human determine what those results mean.

## Planning boundary

This contract defines semantics, not implementation sequencing.
