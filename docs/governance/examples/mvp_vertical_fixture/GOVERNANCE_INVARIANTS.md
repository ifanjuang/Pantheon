# MVP Governance Invariants

Status: candidate support note — invariant registry — documented non-implemented.
Boundary profile: candidate_support_note.

Date: 2026-07-08

This registry names the governance invariants used by the MVP vertical fixture, validation plan and expected reports.

It adds no validator, command, CI workflow, runtime, database mapping, OpenWebUI feature, Hermes contract, approval engine or memory promotion.

## Purpose

The future validator should not invent invariant names from code.

It should first implement the invariants named here.

## Invariants

### `no_external_action_from_draft`

A `result_candidate` must not authorize external action by itself.

```text
result_candidate.external_action_authorized must be false unless a separate external-action decision exists.
```

This protects:

```text
runtime_success != approval
internal_draft_approval != external_send_authorization
```

### `internal_draft_does_not_authorize_send`

A decision to approve a draft for internal use must not authorize sending.

```text
decision: approve_for_internal_draft
```

must keep:

```text
send_authorization: not_granted
external_action: not_authorized
```

### `register_candidate_creation_is_not_memory_admission`

Creating a Register Candidate is not admitting memory.

```text
register_candidate_creation: allowed
memory_admission: not_granted
```

The Register Candidate must still declare:

```text
not_memory_until_admitted: true
```

### `register_candidate_must_remain_pending`

A `register_candidate` must remain pending until a separate register admission exists.

```text
status: pending_register_admission
```

It must not be rendered as accepted memory, stored truth or agency-wide rule.

### `human_decision_required`

A consequential decision must name a human actor.

```text
decided_by: human_practitioner
```

The value must not be a score, timeout, default, automatic policy or role-only alias.

### `retrieval_is_not_evidence`

Retrieval traces and source references are finding aids.

```text
retrieved != truth
source_ref != evidence
retrieval_trace != proof
```

Evidence status must be carried by `evidence_pack_candidate.evidence_items[*].support_status` and later reviewed by a human gate.

## Forbidden collapses

```text
schema_valid != approved
schema_valid != evidence
reference_valid != truth
governance_invariant_pass != external_action_authorization
fixture_pass != runtime_success
register_candidate_creation != memory_admission
```

## Implementation note

A future validator may report these invariant IDs, but passing all invariants still means only:

```text
reviewable governance state
```

It does not mean:

```text
truth proven
external action authorized
memory admitted
runtime accepted
```
