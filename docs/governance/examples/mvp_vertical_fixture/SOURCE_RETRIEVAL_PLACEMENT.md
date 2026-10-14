# MVP Source Manifest / Retrieval Trace Placement

Status: candidate support note — placement decision — documented non-implemented.
Boundary profile: candidate_support_note.

Date: 2026-07-08

This note closes the placement question left open by the MVP fixture and schema alignment work.

It adds no schema, validator, command, CI workflow, runtime, database mapping, OpenWebUI feature, Hermes contract, approval engine or memory promotion.

## Decision

Do not promote `source_manifest` or `retrieval_trace` to central governed object schemas in the MVP loop.

Keep the central schema set as:

```text
task_contract
result_candidate
evidence_pack_candidate
decision_record
register_candidate
```

## Source Manifest placement

`source_manifest` is a scope register for a single governed task.

It should be represented as:

```text
embedded or linked from Task Contract
optionally echoed in Evidence Pack metadata
not a proof object
not a memory object
not an approval object
```

Current MVP placement:

```text
Task Contract.scope.declared_sources
Evidence Pack evidence_items[*].source_ref
```

Meaning:

```text
source_ref is a pointer to scoped material, not evidence by itself.
```

## Retrieval Trace placement

`retrieval_trace` is a retrieval audit trail.

It should be represented as:

```text
embedded or referenced from Evidence Pack items
not a central governed object
not a source of truth
not proof by itself
not runtime success
```

Current MVP placement:

```text
Evidence Pack evidence_items[*].retrieval_trace optional field
Evidence Pack evidence_items[*].support_status carries evidence status
```

Meaning:

```text
retrieval_trace helps explain how a claim was found.
support_status explains how the claim is supported.
```

## Why not first-class schemas now

Promoting these objects too early would blur the authority model.

Risks:

```text
source_manifest mistaken for evidence
retrieval_trace mistaken for proof
retrieved passage mistaken for truth
runtime output mistaken for evidence
```

The MVP must keep:

```text
retrieved != truth
source_ref != evidence
retrieval_trace != proof
runtime_success != approval
```

## Future promotion test

`source_manifest` or `retrieval_trace` may become first-class schemas later only if at least one is true:

```text
multiple Evidence Packs need to share one source register
retrieval audit must be compared across runs
a human reviewer needs independent approval of source scope
regulatory traceability requires standalone source/retrieval records
```

Until then, they remain support structures.

## Validator implication

The local validator should not count `source_manifest` or `retrieval_trace` as central objects.

It should check them only as support fields:

```text
Task Contract declared_sources are parseable
Evidence Pack source_ref values refer to declared or accepted sources
Evidence Pack retrieval_trace values remain trace metadata
retrieval_trace is never treated as support_status
```

## Boundary

This decision authorizes no action.

It does not create:

```text
schema
validator
runtime
source registry
memory admission
external action authorization
```
