# Deliberate Failing MVP Fixture

Status: candidate support note — failing fixture note — documented non-implemented.
Boundary profile: candidate_support_note.

Date: 2026-07-08

This note explains `failing_external_action.fixture.yaml` and its expected report.

It adds no validator, command, CI workflow, runtime, database mapping, OpenWebUI feature, Hermes contract, approval engine or memory promotion.

## Purpose

The fixture proves that a future validator must not stop at schema validity.

The deliberate failure is:

```text
result_candidate.external_action_authorized: true
```

while the available decision record still says:

```text
send_authorization: not_granted
external_action: not_authorized
```

## Expected outcome

The expected report is:

```text
schema_status: pass
reference_status: pass
governance_status: fail
status: blocked
```

This means the object shape is parseable and structurally coherent, but the governed run is blocked.

## Why this matters

A validator that only checks schema would allow a dangerous false pass.

Pantheon must preserve:

```text
schema_valid != approved
schema_valid != evidence
reference_valid != truth
governance_invariant_pass != external_action_authorization
fixture_pass != runtime_success
```

## Future use

Before adding CI, the first local/manual validator should demonstrate both:

```text
fixture.schema_targets.yaml -> reviewable
failing_external_action.fixture.yaml -> blocked
```

No CI gate should be introduced until both paths are visible.
