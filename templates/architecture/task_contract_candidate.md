# Architecture Task Contract Candidate Template

Status: template candidate — non-executable.

This template is for the fictional architecture MVP slice.

It does not authorize execution, external action, memory promotion, professional validation or delivery.

## Task identity

```text
task_id:
project_alias:
request_date:
requested_by:
prepared_for:
```

## User request

```text
Original request:

Normalized request:
```

## Scope

```text
In scope:

Out of scope:

Unknown / requires confirmation:
```

## Admitted corpus

```text
Context Pack Candidate ref:
Corpus manifest ref:
Allowed source folder:
Excluded source folders:
```

## Requested effect

```text
requested_effect: read_only | internal_state_change | external_effect | canonical_effect

Expected first MVP value: read_only or internal_state_change only.
```

## Allowed outputs

```text
- Corpus Inventory Candidate
- Context Pack Candidate
- Fragment Candidate
- Retrieval Candidate
- Evidence Pack Candidate
- Result Candidate
- Capability Gap
```

## Forbidden outputs

```text
- approval
- professional validation
- client-facing delivery
- Registre Probatoire entry
- canonical memory
- external send
- commit / publish / file
- autonomous ingestion or auto-sync
```

## Evidence expectation

```text
Every material claim must link to a source fragment or be marked as assumption.
Contradictions must be surfaced.
Missing documents must be listed.
Retrieved excerpts are candidates, not proof.
```

## Approval ceiling

```text
approval_ceiling: C0 | C1 | C2 | C3 | C4 | C5

MVP default: C1 — internal candidate review only.
```

## Return expected

```text
handoff_delivery_status:
runtime_task_status:
result_candidate:
evidence_pack_candidate:
capability_gaps:
approval_gap:
memory_impact:
external_effect_status:
unchanged_objects:
```

## Stop conditions

```text
- source version missing for a consequential claim
- source authority unclear
- contradiction unresolved
- requested external action
- requested memory promotion
- requested canonical conclusion
- missing approval ceiling
- missing source-fragment-provenance link
```
