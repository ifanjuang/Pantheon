# MVP Fixture Validation Plan

Status: candidate support note — validation plan — documented non-implemented.
Boundary profile: candidate_support_note.

Date: 2026-07-08

This plan defines how the MVP vertical fixture should be validated later.

It adds no validator, command, CI workflow, runtime, database mapping, OpenWebUI feature, Hermes contract, approval engine or memory promotion.

## Inputs

```text
docs/governance/examples/mvp_vertical_fixture/fixture.schema_targets.yaml
schemas/mvp_governed_loop_objects.schema.yaml
docs/governance/examples/mvp_vertical_fixture/SOURCE_RETRIEVAL_PLACEMENT.md
docs/governance/examples/mvp_vertical_fixture/GOVERNANCE_INVARIANTS.md
```

The original `fixture.yaml` remains the narrative fixture. `fixture.schema_targets.yaml` is the validation target subset.

## Validation layers

Future validation should run in three separate layers.

```text
Layer 1: YAML and schema validation
Layer 2: cross-object reference validation
Layer 3: governance invariant validation
```

The layers must remain separate. A schema pass is not evidence, approval, reference integrity or memory admission.

## Layer 1 — YAML and schema validation

Expected future behavior:

```text
1. Parse `fixture.schema_targets.yaml` as multi-document YAML.
2. Ignore comments.
3. Reject empty documents.
4. For each document, read `object_type`.
5. Validate the document against `schemas/mvp_governed_loop_objects.schema.yaml`.
6. Report one result per document.
```

Expected document count for the current fixture target:

```text
7 documents
```

Expected object types:

```text
task_contract: 1
result_candidate: 2
evidence_pack_candidate: 1
decision_record: 2
register_candidate: 1
```

Layer 1 must not interpret governance meaning beyond the schema.

## Layer 2 — cross-object reference validation

Schema validation cannot prove reference integrity.

A later validator should separately check:

```text
all object_id values are unique
all `applies_to` values refer to an existing object_id
all `revision_of` values refer to an existing result_candidate
all `related_evidence_pack` values refer to an existing evidence_pack_candidate
all `created_because_of` values refer to an existing decision_record
all `basis` values refer to existing objects or accepted source refs
source_ref values point to declared or accepted sources
```

Source refs are scope pointers, not evidence.

This is a graph/reference check, not a schema check.

## Layer 3 — governance invariant validation

A later validator should check governance invariants that are too semantic for the schema.

Minimum invariants:

```text
result_candidate.external_action_authorized must be false unless a separate external-action decision exists
approve_for_internal_draft must not imply send_authorization
approve_for_internal_draft must not imply memory_admission
register_candidate_creation must not imply memory_admission
register_candidate.not_memory_until_admitted must be true
register_candidate status must remain pending until a separate register admission exists
retrieval references must remain finding aids, not evidence by themselves
```

These checks protect the Pantheon boundary:

```text
retrieved != truth
source_ref != evidence
retrieval_trace != proof
runtime_success != approval
internal_draft_approval != external_send_authorization
register_candidate != admitted memory
```

## Output shape for future reports

A future validator should produce a report with three independent sections:

```yaml
schema_validation:
  status: pass | fail
  documents_checked:
  errors: []
reference_validation:
  status: pass | fail
  objects_indexed:
  missing_refs: []
governance_invariants:
  status: pass | fail
  invariant_failures: []
```

A complete pass means only:

```text
the fixture target is structurally coherent enough for the next implementation step
```

It does not mean:

```text
truth validated
approval granted
memory admitted
external action authorized
runtime accepted
```

## Manual-first rule

The first validation should be local/manual, not CI.

Reason: the schema is still permissive and status strings remain intentionally loose. A CI gate would create false authority too early.

## Exit criteria before CI

CI can be considered only after all are true:

```text
fixture.schema_targets.yaml has one local validation pass
reference validation rules have at least one passing report
at least one deliberate failing fixture exists
status vocabulary has been reviewed
alias equality policy is decided
Source Manifest and Retrieval Trace placement is documented
```

## Forbidden shortcuts

```text
schema_valid != approved
schema_valid != evidence
reference_valid != truth
governance_invariant_pass != external_action_authorization
fixture_pass != runtime_success
```
