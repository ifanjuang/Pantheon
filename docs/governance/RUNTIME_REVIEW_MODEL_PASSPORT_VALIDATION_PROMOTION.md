# Runtime Review + Model Passport Validation Promotion

Status: validation-only — implementation partial: human-fillable templates exist; schema-backed/read-only validator and MCP validation remain non-implemented.

This document promotes the next governance step for:

```text
docs/governance/EXTERNAL_TOOLS_POLICY.md
docs/governance/MODEL_CAPABILITY_PASSPORT.md
```

It defines how those two support-doctrine objects may become validation-checkable without turning Pantheon Next into a runtime, model router, scanner, installer, provider gateway, scheduler, queue, approval engine or memory engine.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`; validation here does not transfer authority to a client, runtime or provider.

## Current implementation boundary

The human-fillable scaffold step has been completed. The repository currently contains:

```text
templates/external_runtime_review_candidate.yaml
templates/model_capability_passport_candidate.yaml
templates/validation_report_candidate.yaml
```

The model template keeps its legacy filename but now contains the documentary `model_capability_review_candidate` shape owned by `MODEL_CAPABILITY_PASSPORT.md`. It is separate from the executable universal Capability Passport schema.

Those templates materialize the L0–L3 vocabulary, candidate-only boundaries and review fields described below. They remain declarative scaffolds: template presence is not schema validation, a validator, an MCP tool, approval, runtime execution or production activation.

The protected validation step remains unimplemented. There is currently no dedicated schema for these three candidate objects, no validation test/validator implementing the L0–L3 checks, and no MCP validation functions for them.

## Decision summary

Accepted:

```text
Promote External Runtime Threat Model Review toward read-only validation.
Promote the documentary Model Capability Review toward read-only validation.
Use human-fillable candidate templates before protected validation work.
Use the MCP Policy Server only as a read-only policy / validation surface if implementation is later approved.
Keep schemas, validation tests and MCP validation functions blocked until explicitly approved.
Keep all runtime execution outside Pantheon.
```

Refused:

```text
No runtime scanner.
No automatic sandbox.
No model router.
No benchmark runner.
No provider selection engine.
No runtime-client configuration.
No Hermes skill.
No automatic adapter installation.
No automatic approval.
No memory promotion.
No external action.
```

To verify:

```text
Whether existing MCP policy-server conventions are sufficient for these checks.
Whether schema-backed validation is needed immediately or later.
Whether Hermes adapters should carry these declarations as metadata.
Whether Pantheon Control should display validation status.
```

To arbitrate:

```text
Whether to modify schemas/.
Whether to modify tests/ for schema-backed/read-only validation.
Whether to modify mcp-server/.
Whether validation should be soft advisory or blocking before adapter use.
```

## Promotion target

The target is not implementation.

The target is this governed capability:

```text
Given a Runtime Review Candidate or Model Capability Review Candidate,
Pantheon can classify whether the declaration is complete enough to be reviewed,
and whether it should be accepted, refused, sent to verification or sent to arbitration.
```

For the model-specific object, "accepted" means the review record is complete/coherent enough for its documentary purpose. It does not activate the model, authorize a task or lower any universal Capability Passport, Task Contract, Evidence or approval requirement.

The expected output remains data:

```text
Validation Candidate
Completeness Report
Risk Classification
Missing Fields
Gate Recommendation
Human Decision Required
```

No validation check may produce:

```text
runtime execution
model selection
provider routing
external transmission
canonical approval
memory promotion
professional validation
```

## Validation levels

Use four levels:

```text
L0 — document exists
L1 — required fields present
L2 — field values are internally coherent
L3 — gate/review recommendation can be produced
```

Meaning:

| Level | Meaning | Allowed result |
|---|---|---|
| L0 | A review record exists. | candidate only |
| L1 | Required fields are present. | completeness report |
| L2 | Values do not contradict declared scope, risk and effect. | to_verify / blocked / needs_review |
| L3 | A gate or review recommendation can be stated. | candidate recommendation only |

L3 is still not approval. It is a recommendation for a visible gate or review path.

## Candidate object — runtime review

A Runtime Review Candidate is checkable when it declares at least:

```text
runtime_name
reviewed_ref
system_role
binding_status
exposure_posture
privileged_capabilities
data_access
external_effects
memory_effects
model_effects
scheduling_effects
host_control_surface
untrusted_content_paths
prompt_injection_posture
permission_granularity
auditability
pantheon_gate_required
approval_ceiling
evidence_expectation
safe_default
decision
repo_state
```

Validation may identify:

```text
missing mandatory field
unknown exposure posture
unclear host-control surface
unclear external effect
unclear memory effect
unclear approval ceiling
incompatible decision / risk posture
runtime power treated as normal skill
insufficient safe default
```

## Candidate object — model-specific review

A Model Capability Review Candidate is checkable when it declares at least:

```text
model_id
display_name
version_or_release
provider
serving_posture
serving_surface
modalities
context_window_or_limit
review_status
reviewed_at
reviewed_by
data_exposure_classes_allowed
sensitive_data_allowed
retention_or_training_posture
source_grounding_expectation
reviewed_task_families
forbidden_task_families
professional_use_ceiling
known_failure_modes
uncertainty_behavior
comparison_required_when
fallback_model_or_path
```

These are model-suitability review fields. `review_status` is not Capability Activation and `reviewed_task_families` is not task authorization. Universal capability, activation and task/run legitimacy remain with their existing owners.

Validation may identify:

```text
missing mandatory field
unknown serving posture
sensitive-data posture not justified
professional-use ceiling inconsistent with known failure modes
reviewed task family contradicted by a declared weakness
external model with unclear retention/training posture
model treated as final validator
review state confused with activation or task authorization
```

## Gate recommendation vocabulary

Read-only validation may return only these recommendations:

```text
allow_read_only
allow_candidate_only
needs_approval
needs_more_evidence
needs_human_review
needs_security_review
needs_adapter_review
block
```

For a Model Capability Review Candidate these recommendations remain advisory outputs of the validation proposal; they do not themselves populate activation, Task Contract or approval state. The template uses a narrower `review_recommendation` vocabulary for the model-specific review record.

The recommendation is not enforcement unless an approved external runtime honors an applicable Pantheon policy decision through its PEP boundary.

## MCP Policy Server promotion path

If implementation is later approved, the MCP Policy Server may expose read-only validation functions such as:

```text
validate_external_runtime_review
validate_model_capability_review
classify_runtime_review_gate
classify_model_review_gate
```

The earlier proposal names are retained below as legacy proposal aliases so existing repository checks and historical references remain intelligible during this documentary rename:

```text
validate_model_capability_passport
classify_model_passport_gate
```

Preferred proposal names are the `*_model_capability_review` / `*_model_review_*` forms above. Neither preferred nor legacy names create MCP tools by themselves, and no such functions currently exist in the repository.

The functions, if later implemented, must:

```text
read candidate data
check required fields
check coherence rules
return a candidate report
never execute runtime work
never route providers
never select a model
never approve
never promote memory
never send externally
```

## Schema promotion path

Schema-backed validation is useful, but blocked until explicitly approved.

Allowed current state:

```text
human-fillable templates present
no dedicated schemas for these three candidate objects
no schema-backed/read-only validation tests or validator
no MCP validation functions
```

If approved later, the schema work package should create separate declarative contracts for:

```text
external_runtime_review_candidate
model_capability_review_candidate
validation_report_candidate
```

A future `model_capability_review_candidate` schema would remain distinct from `schemas/capability_passport.schema.yaml`; adding a `model` primitive or model-specific fields to the universal Capability Passport is a separate migration decision.

Any schema must include boundary metadata equivalent to:

```text
candidate_only: true
canonical_effect: false
runtime_effect: false
external_action: false
memory_promotion: false
```

## Template promotion path

The human-fillable template step is complete. Current scaffolds are:

```text
templates/external_runtime_review_candidate.yaml
templates/model_capability_passport_candidate.yaml
templates/validation_report_candidate.yaml
```

The model template path is retained for compatibility, but its current root object is `model_capability_review_candidate`. Templates are not schemas and not validators. Their existence does not authorize the protected validation step.

## Control / dashboard projection

Pantheon Control or any exposure surface may later display:

```text
review exists / missing
model-specific review exists / missing
completeness level L0-L3
risk class
host-control surface
data exposure
approval ceiling from the applicable universal governance object
gate/review recommendation
human decision required
```

The display does not validate. It projects status.

## Repository state after partial promotion

```text
Validation-only proposal retained.
Three human-fillable templates implemented as non-executable scaffolds.
No dedicated schema for the three candidate objects.
No schema-backed/read-only validator.
No MCP validation function.
No runtime.
No runtime-client configuration.
No Hermes skill.
No external action.
No memory promotion.
```

Historical proof of the template step is retained in the private Pantheon-Next archive.

## Required next explicit approvals

Before protected validation implementation, obtain explicit approval for any of:

```text
schemas/ changes
tests/ changes
mcp-server/ changes
operations/ changes
platform/ changes
Docker changes
.env changes
```

## Boundary phrase

```text
The universal passport declares capability constraints.
The model review qualifies model-specific suitability.
The validator reports.
The gate recommends.
Zeus arbitrates status.
The human decides.
```
