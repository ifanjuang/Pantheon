# Stable Hermes Project ChangeCandidate Route

Status: implemented migration record.

Date: 2026-08-03.

## Scope

This tranche stabilizes the final internal versioned route:

```text
POST /hermes/execution-admissions/{admission_id}/projects/{project_id}/change-candidates
```

The retired `/v1/hermes/...` path is removed without an alias.

## Consequential boundary

This route does not write Project attributes. It allows an admitted external Hermes runtime to deposit one Project ChangeCandidate only when:

- the Project is present in the exact active Context Pack;
- the requested Project revision is still current;
- every declared source reference is already admitted;
- a Hermes API key and actor identity are present;
- an idempotency key is supplied.

The returned object remains explicit:

```text
project_mutated = false
execution_authorized = false
human_apply_required = true
evidence_admitted = false
```

```text
candidate created != Project mutated
candidate created != approved
source_ref != Evidence
runtime authority != human apply authority
```

Only the separate human Agency ChangeCandidate review gate may apply an accepted candidate.

## Baseline result

The temporary decreasing baseline now records:

```text
generation-named active artifacts: 0
internal versioned-route files:     0
internal versioned declarations:    0
```

The baseline file and CI guard remain active until the final convergence audit. Zero debt does not by itself prove code usage, modularity, performance or final architecture closure.

## Non-goals

No direct Agency Data mutation, runtime, scheduler, queue, provider router, automatic approval, automatic Evidence admission or memory promotion is introduced.
