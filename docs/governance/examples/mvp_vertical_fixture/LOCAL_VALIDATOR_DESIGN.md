# MVP Local Validator Design

Status: candidate support note — validator design — documented non-implemented.
Boundary profile: candidate_support_note.

Date: 2026-07-08

This design describes how a future local/manual validator should behave.

It adds no validator, command, CI workflow, runtime, database mapping, OpenWebUI feature, Hermes contract, approval engine or memory promotion.

## Purpose

The first validator must be local/manual and report-only.

It must not become:

```text
approval engine
truth engine
memory engine
external action gate
runtime health checker
scheduler
queue
provider router
```

## Inputs

Primary expected inputs:

```text
docs/governance/examples/mvp_vertical_fixture/fixture.schema_targets.yaml
docs/governance/examples/mvp_vertical_fixture/failing_external_action.fixture.yaml
schemas/mvp_governed_loop_objects.schema.yaml
docs/governance/examples/mvp_vertical_fixture/GOVERNANCE_INVARIANTS.md
```

Expected reference reports:

```text
docs/governance/examples/mvp_vertical_fixture/validation_report.example.yaml
docs/governance/examples/mvp_vertical_fixture/failing_external_action.expected_report.yaml
```

## Non-goals

```text
no CI gate
no automatic merge blocker
no runtime execution
no OpenWebUI card rendering
no Hermes execution
no database persistence
no memory admission
no external action authorization
```

## Processing layers

The validator should run three independent layers.

```text
Layer 1: YAML and schema validation
Layer 2: cross-object reference validation
Layer 3: governance invariant validation
```

The final report must expose all three sections separately.

A schema pass must not hide reference warnings.
A reference pass must not hide governance failures.
A governance pass must not authorize external action.

## Layer 1 — schema validation

Expected behavior:

```text
parse multi-document YAML
reject empty documents
require object_type, object_id and status
validate central objects against schemas/mvp_governed_loop_objects.schema.yaml
ignore source_manifest and retrieval_trace as central objects unless a future schema exists
report one result per document
```

Expected object counts for the positive fixture:

```text
task_contract: 1
result_candidate: 2
evidence_pack_candidate: 1
decision_record: 2
register_candidate: 1
```

Expected object counts for the deliberate failing fixture:

```text
task_contract: 1
result_candidate: 1
evidence_pack_candidate: 1
decision_record: 1
```

## Layer 2 — reference validation

The validator should build an object index:

```text
object_id -> object document
```

Then check:

```text
object_id uniqueness
applies_to exists
revision_of exists and points to result_candidate
related_evidence_pack exists and points to evidence_pack_candidate
created_because_of exists and points to decision_record
basis values point to existing governed objects or accepted source refs
source_ref values point to declared or accepted sources
```

Source refs are scope pointers, not proof.

## Layer 3 — governance invariants

The validator should implement invariant IDs from `GOVERNANCE_INVARIANTS.md`.

Initial invariant IDs:

```text
no_external_action_from_draft
internal_draft_does_not_authorize_send
register_candidate_creation_is_not_memory_admission
register_candidate_must_remain_pending
human_decision_required
retrieval_is_not_evidence
```

Each invariant failure should include:

```yaml
id:
severity: warning | blocking
object_id:
field:
observed:
expected:
reason:
```

## Expected outcomes

Positive fixture:

```text
schema_status: pass
reference_status: pass_with_warnings
governance_status: pass_with_warnings
status: reviewable
```

Deliberate failing fixture:

```text
schema_status: pass
reference_status: pass
governance_status: fail
status: blocked
```

## Report authority

The validator may report:

```text
invalid
structurally_valid
reviewable
reviewable_with_warnings
blocked
```

It must not report:

```text
approved
accepted
safe
trusted
canonical
```

## Required report boundary

Every report should include:

```yaml
does_not_mean:
  - truth_validated
  - approval_granted
  - memory_admitted
  - external_action_authorized
  - runtime_accepted
```

## Exit criteria before CI

CI may be considered only after:

```text
local validator design is accepted
positive fixture produces expected reviewable report
failing fixture produces expected blocked report
status vocabulary is stable enough for first enum proposal
alias equality policy is documented
Source Manifest / Retrieval Trace placement is documented
```

## Still forbidden after local validator

Even after a local validator exists:

```text
schema_valid != approved
reference_valid != truth
governance_invariant_pass != external_action_authorization
reviewable != safe
blocked != rollback
validator_success != runtime_success
```
