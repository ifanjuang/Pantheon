# MVP Object Shape Reconciliation

Status: candidate support note — reconciliation note — documented non-implemented.
Boundary profile: candidate_support_note.

Date: 2026-07-07

This note compares the compact vertical fixture with the earlier illustrative MVP object examples.

It adds no schema, validator, runtime, database migration, OpenWebUI feature, Hermes skill, approval engine or memory engine.

## Compared files

```text
docs/governance/examples/mvp_task_contract.yaml
docs/governance/examples/mvp_evidence_pack_candidate.yaml
docs/governance/examples/mvp_decision_record.yaml
docs/governance/examples/mvp_memory_candidate.yaml
docs/governance/examples/mvp_vertical_fixture/fixture.yaml
```

## Main finding

The fixture correctly demonstrates the vertical loop, but it uses a generic object envelope:

```yaml
object: task_contract
id: mvp.vertical.fixture.tc_001
```

The earlier example files use object-specific identifiers:

```yaml
contract_id:
evidence_pack_id:
decision_id:
candidate_id:
```

Both are readable. They should not be treated as schemas yet.

## Reconciliation decision

For the next schema pass, prefer a hybrid shape:

```yaml
object_type: task_contract
object_id: mvp.devis-reprise.tc-001
status: candidate
```

Object-specific aliases may remain as compatibility fields during the example phase:

```yaml
contract_id: mvp.devis-reprise.tc-001
object_id: mvp.devis-reprise.tc-001
```

Reason: `object_type/object_id` makes the vertical chain uniform, while object-specific IDs remain easier for humans reading standalone examples.

## Status alignment

Keep status values descriptive before schemas.

Useful current values:

```text
candidate
ready_for_governed_processing
draft_to_review
reviewable_with_risk
recorded
revised_draft_to_review
pending_register_admission
```

Do not promote these to enums yet. They need one more implementation-facing pass.

## Required links

Future object shapes should preserve these links:

```text
Task Contract -> Source Manifest
Task Contract -> Retrieval Trace
Retrieval Trace -> Result Candidate
Result Candidate -> Evidence Pack Candidate
Evidence Pack Candidate -> Decision Record
Decision Record -> Revised Result Candidate
Decision Record -> Register Candidate
```

Each link should be explicit. No object should infer authority from filename order.

## Decision boundaries to preserve

```text
retrieved != truth
runtime_success != approval
internal_draft_approval != external_send_authorization
register_candidate != admitted memory
```

An internal draft approval is not a send approval.
Register Candidate creation is not Registre Probatoire admission.
A retrieval trace is not proof.
A runtime result is not evidence by itself.

## Register Candidate vocabulary

The final object should use `register_candidate` as the canonical object type.

The older file name `mvp_memory_candidate.yaml` remains acceptable as a readability alias, but schemas should not reintroduce `memory_candidate` as the canonical object type.

## What not to do yet

```text
no schema creation
no enum freeze
no database table mapping
no OpenWebUI component contract
no Hermes execution contract
no validation test
```

## Next step

The next PR may introduce a minimal shape draft for schemas, but only after this reconciliation is accepted.

Recommended first schema candidates:

```text
task_contract
result_candidate
evidence_pack_candidate
decision_record
register_candidate
```

Source Manifest and Retrieval Trace should remain example/support objects until the implementation-facing pass confirms whether they are standalone records or embedded sections of the Evidence Pack.
