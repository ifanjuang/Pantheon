# MVP Validation Report Shape

Status: candidate support note — expected report shape — documented non-implemented.
Boundary profile: candidate_support_note.

Date: 2026-07-08

This note explains how to read `validation_report.example.yaml`.

It adds no validator, command, CI workflow, runtime, database mapping, OpenWebUI feature, Hermes contract, approval engine or memory promotion.

## Purpose

The future validator should produce a report before any CI gate is considered.

The report should not collapse structure into authority.

```text
schema_valid != approved
schema_valid != evidence
reference_valid != truth
governance_invariant_pass != external_action_authorization
fixture_pass != runtime_success
```

## Report status vocabulary

Use report-level status values that do not sound like approval.

Recommended values:

```text
invalid
structurally_valid
reviewable
reviewable_with_warnings
blocked
```

Avoid:

```text
approved
accepted
safe
trusted
canonical
```

The example uses:

```yaml
status: reviewable
```

Meaning: the fixture target is coherent enough to discuss or pass to the next implementation step. It is not approved evidence, admitted memory or authorized action.

## Section status vocabulary

Section statuses are diagnostic, not governance decisions.

Recommended values:

```text
pass
pass_with_warnings
fail
not_checked
```

A section `pass` must never be rendered as global approval.

## Required sections

A future report should contain three independent sections:

```yaml
schema_validation:
reference_validation:
governance_invariants:
```

Each section has its own status, warnings and failures.

A schema pass must not hide reference warnings.
A reference pass must not hide governance failures.
A governance pass must not authorize external action.

## Why warnings matter

Warnings are not cosmetic. They identify boundaries that remain intentionally open.

Current expected warnings:

```text
status strings are not enum-validated yet
additionalProperties remains permissive
alias equality is not enforced by schema
source_ref values are not resolved against a canonical source registry yet
```

These warnings are part of the governance state.

## Future failing fixture

Before CI, create at least one deliberately failing fixture.

Recommended failures:

```text
result_candidate.external_action_authorized: true without external-action decision
register_candidate.not_memory_until_admitted: false
missing referenced object in applies_to
approve used as send_authorization or retention authorization
register_candidate_creation used as memory_admission
```

This prevents a validator from becoming a ceremonial pass-through.

## Boundary

A validation report may say:

```text
structurally coherent
references resolved
invariants checked
reviewable
blocked
```

It must not say by itself:

```text
truth proven
client action approved
memory admitted
external send authorized
runtime healthy
runtime safe
```

## Next step

The next PR may define a deliberate failing fixture and the expected failing report.

Still no CI until the failure mode is visible.
