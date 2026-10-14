# MVP Vocabulary Tightening

Status: candidate support note — vocabulary note — documented non-implemented.
Boundary profile: candidate_support_note.

Date: 2026-07-08

This note records vocabulary corrections made after reviewing the MVP vertical fixture sequence.

It adds no validator, command, CI workflow, runtime, database mapping, OpenWebUI feature, Hermes contract, approval engine or memory promotion.

## Corrections

### Avoid generic `approve`

Do not use generic `approve` in `possible_decisions` or `decision`.

Use scoped decisions:

```text
approve_for_internal_draft
authorize_external_send
admit_register_candidate
refuse
request_revision
request_more_evidence
```

Reason: Pantheon must distinguish draft approval, external action authorization and memory admission.

### Avoid `ready_for_execution` in documentation fixtures

Use:

```text
ready_for_governed_processing
```

Reason: `ready_for_execution` sounds like a runtime instruction. These fixtures are documentation only.

### Split Register Candidate creation from memory admission

Do not use ambiguous language such as:

```text
memory_authorization: grant_register_candidate_only
```

Use:

```yaml
register_candidate_creation: allowed
memory_admission: not_granted
```

Reason: creating a Register Candidate is not admitting memory.

### Distinguish report status from section status

Report-level status values:

```text
invalid
structurally_valid
reviewable
reviewable_with_warnings
blocked
```

Section-level status values:

```text
pass
pass_with_warnings
fail
not_checked
```

A section `pass` is diagnostic only. It must not be rendered as global approval.

## Still open

The following remain unresolved and should not be hidden:

```text
status values are not yet enums
alias equality is not enforced
Source Manifest placement is not decided
Retrieval Trace placement is not decided
schema remains permissive
no validator exists
```

## Boundary

Vocabulary tightening improves readability and reduces ambiguity.

It does not create:

```text
validation
approval
evidence
truth
memory admission
external action authorization
runtime acceptance
```
