# Stable Hermes Admission Routes

Status: implemented migration record.

Date: 2026-08-03.

## Scope

This tranche stabilizes the three Cockpit routes for one explicit human execution admission:

```text
POST /cockpit/hermes-handoffs/{handoff_id}/admissions
GET  /cockpit/hermes-execution-admissions/{admission_id}
POST /cockpit/hermes-execution-admissions/{admission_id}/revocations
```

The retired `/v1/cockpit/...` paths are removed without aliases.

## Boundary

A submitted handoff and its Work Issue do not authorize execution. Admission requires:

- an exact handoff identifier;
- an editor key;
- an explicit human actor;
- a bounded TTL;
- an idempotency key;
- the current immutable Work Issue and handoff snapshots.

Admission creates one bounded opportunity for an external Hermes-side binding. Pantheon does not dispatch, queue, schedule or start Hermes.

```text
submission != admission
admission != runtime start
admitted != consumed
expired != revoked
runtime success != Evidence
```

Revocation remains an explicit human action and is valid only before consumption according to the existing admission contract.

## Deliberately excluded

The eight runtime-facing routes remain in a separate tranche:

```text
execution envelope
launch reservation
runtime start observation
scoped context manifest/entity reads
active context manifest/entity reads
runtime return
```

The Hermes Project ChangeCandidate route remains separate because it proposes a consequential Agency Data modification.

## Debt reduction

```text
generation-named active artifacts: 0
internal versioned-route files:     2
internal versioned declarations:    12 -> 9
```

## Non-goals

No runtime, scheduler, queue, provider router, automatic approval, automatic Evidence admission or memory promotion is introduced.
