# Model Capability Passport

Status: active support doctrine — model-specific review specialization under uniform capability governance; documented non-implemented.

Boundary profile: active_support_doctrine.

This document owns only the model-specific review seam needed before a model, model provider, model-serving surface or model-selection adapter supports consequential professional work.

General capability eligibility, passport governance, scoped activation, task authorization, consequential-effect admission, Evidence, approvals, memory and runtime/client placement remain owned by `UNIFORM_CAPABILITY_GOVERNANCE.md`, `schemas/capability_passport.schema.yaml`, `MODULE_ACTIVATION.md`, `TASK_CONTRACTS.md`, `EVIDENCE_PACK.md`, `APPROVALS.md`, `MEMORY.md` and `HERMES_INTEGRATION.md`.

## Owner boundary

A model-specific review answers questions that the universal capability passport does not currently express directly:

```text
which exact model/release is being considered?
how and where is it served?
what data may leave the governed boundary?
what retention/training uncertainty exists?
which modalities and task families were reviewed?
what professional-use ceiling is appropriate?
which known failure modes matter?
when is comparison or extra human review required?
```

It does not authorize a task, activate a capability, select a provider, serve a model, lower an approval ceiling or validate model output.

```text
model available != model reviewed
model reviewed != model activated
model selected != task authorized
model confidence != Evidence
model output != professional validation
```

## Relationship to the universal Capability Passport

`UNIFORM_CAPABILITY_GOVERNANCE.md` remains the rulebook. A runtime, tool or adapter that serves or selects a model still requires the ordinary governed capability path.

The executable `schemas/capability_passport.schema.yaml` is the current universal Capability Passport schema. It currently has no `model` primitive and no fields for model identity, modality, context window, serving posture or model-specific failure modes.

Therefore the structure in this document is a **documentary model-review specialization**, not an extension of that executable schema and not valid schema input by implication.

```text
universal Capability Passport
+ documentary model-specific review
+ applicable Capability Activation
+ Task Contract / Execution Admission
= governed model use candidate
```

If executable model-specific fields are later needed, they require an explicit schema change and migration review. This document does not create that change.

## When the specialization is required

Use a model-specific review when model choice can materially affect:

```text
professional or regulatory interpretation
source-dependent analysis
client-facing or external communication
confidential or sensitive-data processing
repository / governed-record mutation support
code or tool-use reasoning
image / plan / document interpretation
financial, legal, architectural, engineering or safety-relevant judgment
```

Low-risk rewriting, formatting or brainstorming may use a lighter declaration when the applicable Task Contract and capability policy permit it.

## Minimum model-review record

Recommended documentary shape:

```text
model_capability_review:
  model_id:
  display_name:
  version_or_release:
  provider:
  serving_posture: local_only | external_api | self_hosted_remote | organization_hosted | hybrid | unknown
  serving_surface:
  adapter_or_binding_ref:

  review_status: candidate | reviewed | suspended | rejected
  reviewed_at:
  reviewed_by:

  modalities:
  context_window_or_limit:
  reviewed_task_families:
  forbidden_task_families:
  professional_use_ceiling:

  data_exposure_classes_allowed:
  sensitive_data_allowed: false
  retention_or_training_posture:
  source_grounding_expectation:

  known_failure_modes:
  uncertainty_behavior:
  comparison_required_when:
  fallback_model_or_path:
```

`review_status` is review state, not activation state. `reviewed_task_families` records evaluated suitability; it is not task authorization. The applicable universal passport, activation record and Task Contract remain authoritative for an actual use.

## Serving and data posture

Serving posture is a risk input, not a truth or authorization signal.

```text
local model != automatically safe
external model != automatically unsuitable
self-hosted != automatically authorized
provider selected != authority transfer
```

The review should record the smallest relevant data-exposure classes, for example:

```text
public_only
supplied_non_sensitive
project_sensitive
client_private
regulated_or_confidential
secrets_or_credentials
unknown
```

Secrets and unnecessary private material remain excluded by default. Any broader data use must be justified by the applicable Task Contract and policy; this review cannot grant that permission.

## Task-family suitability and professional-use ceiling

Model review should name the task families actually assessed rather than imply general competence. Useful families may include:

```text
rewriting / translation
summarization
source extraction
document review
plan or image interpretation
code generation / review
regulatory research
contractual analysis
professional risk review
client-facing draft support
external-action preparation
```

A professional-use ceiling describes the maximum status the review supports before other governance is applied, for example:

```text
draft_only
candidate_only
to_verify
supporting_analysis
reviewed_support
never_final_by_model
```

Default: `never_final_by_model`.

The model review cannot lower Evidence requirements, approval requirements or human-decision requirements owned elsewhere.

## Known failure modes

Record failure modes relevant to the reviewed model/release and intended modality. Examples include:

```text
hallucinated or fabricated citations
overconfident synthesis
weak numerical reliability
poor table extraction
weak spatial / plan interpretation
weak legal or regulatory freshness
language mismatch
privacy exposure risk
prompt-injection susceptibility through untrusted context
instruction-following that overrides source discipline
```

This is a review prompt, not an exhaustive taxonomy and not proof that unlisted failure modes are absent.

## Comparison and escalation

The review may require comparison or stronger human review when, for example:

```text
the result materially affects professional responsibility
the source set is contradictory
the model is outside a reviewed task family
the modality matches a known weakness
the result supports external communication or consequential action
model/provider posture changes materially
```

Comparison produces another candidate signal; it does not validate the result.

## Runtime and governance handoff

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`.

```text
model download / serving / routing / provider keys / benchmark execution
  -> runtime or adapter concern

model-specific review
  -> Pantheon governance declaration

passport / activation / task admission
  -> their existing Pantheon owners

model execution
  -> admitted external runtime / PEP

result
  -> candidate until Evidence / approval / human-decision rules are satisfied
```

A Cockpit or compatible client may project the review state but does not become its authority or persistence owner.

## Safe fallback

If the required model-specific review is absent, stale or materially incomplete, the safe posture is to narrow the use rather than infer permission:

```text
no new sensitive-data exposure
no widening of reviewed task family
no elevation of output status
no consequential external effect based on model suitability alone
surface the capability gap for review
```

This specialization constrains model suitability. It does not replace the universal capability gate.
