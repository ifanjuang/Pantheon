# Stable Hermes Handoff Routes

Status: implemented migration record.

Date: 2026-08-03.

## Scope

This tranche stabilizes only the Cockpit preparation and submission of one scoped Hermes handoff:

```text
POST /cockpit/hermes-handoffs/preview
POST /cockpit/hermes-handoffs/submit
```

The retired paths are removed without aliases:

```text
POST /v1/cockpit/hermes-handoffs/preview
POST /v1/cockpit/hermes-handoffs/submit
```

## Boundary

Preview prepares deterministic candidates:

```text
Task Contract Candidate
Context Pack Candidate
scope resolution
tag context
preview digest
```

Submission requires an explicit human actor and exact preview references. It may persist the immutable handoff snapshots and create a Work Issue assigned to Hermes.

It does not admit execution and does not create a Hermes run.

```text
preview != submission
submission != admission
admission != runtime start
runtime success != Evidence
```

## Deliberately excluded

The following routes remain in a separate migration tranche:

```text
Cockpit admission creation
Cockpit admission read
Cockpit admission revocation
Hermes execution envelope
Hermes launch reservation
Hermes runtime start
Hermes scoped and active context reads
Hermes runtime return
Hermes Project ChangeCandidate proposal
```

This separation prevents the Cockpit action that frames work from being confused with the human decision that authorizes one bounded runtime opportunity.

## Debt reduction

```text
generation-named active artifacts: 0
internal versioned-route files:     3 -> 2
internal versioned declarations:    14 -> 12
```

## Non-goals

No scheduler, queue, provider router, runtime, automatic approval, automatic Evidence admission or memory promotion is introduced.
