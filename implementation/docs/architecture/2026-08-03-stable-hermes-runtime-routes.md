# Stable Hermes Runtime Routes

Status: implemented migration record.

Date: 2026-08-03.

## Scope

This tranche stabilizes the eight routes exposed to one external Hermes-side binding:

```text
GET  /hermes/execution-admissions/{admission_id}
POST /hermes/execution-admissions/{admission_id}/launch-reservations
POST /hermes/execution-admissions/{admission_id}/runs/start
GET  /hermes/execution-admissions/{admission_id}/runs/{run_id}/context
GET  /hermes/execution-admissions/{admission_id}/runs/{run_id}/context/entities/{entity_type}/{entity_id}
GET  /hermes/execution-admissions/{admission_id}/active-context
GET  /hermes/execution-admissions/{admission_id}/active-context/entities/{entity_type}/{entity_id}
POST /hermes/execution-admissions/{admission_id}/runs/{run_id}/return
```

The retired `/v1/hermes/...` paths are removed without aliases.

## Boundary

These routes do not make Pantheon a runtime. They form a bounded adapter boundary through which an external Hermes binding may:

- read one exact admitted execution envelope;
- reserve one immutable launch snapshot;
- report an external runtime start;
- read only the exact scoped context while the run is active;
- report a bounded normalized return and optional Result Candidate.

The existing gates remain mandatory:

```text
Hermes API key
Hermes actor identity
exact admission ID
exact launch reservation
expected Work Issue version
idempotency key
exact run ID
admitted Context Pack membership
```

```text
admission != runtime start
runtime start observation != dispatch
runtime return != accepted result
runtime success != Evidence
Result Candidate != Evidence
```

## Explicit absence

No endpoint lists pending work, searches global Agency Data, selects a provider, dispatches a task, schedules a retry, starts a process or promotes memory/Evidence.

## Separate final route

The Hermes Project ChangeCandidate route remains in a final consequential tranche. It proposes an Agency Data mutation and therefore must retain its own validation and review boundary.

## Debt reduction

```text
generation-named active artifacts: 0
internal versioned-route files:     2 -> 1
internal versioned declarations:    9 -> 1
```
