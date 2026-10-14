# Workflow Forging Protocol

Status: active support doctrine — workflow candidate forging and pre-launch validation.

Runtime status: non-executable.

This document defines how a professional Workflow Candidate may be generated on the fly without becoming authorized, durable or externally effective by default.

It does not implement a workflow engine, scheduler, queue, bridge, connector, approval engine, memory engine, Registre Probatoire storage, Hermes skill or OpenWebUI plugin.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: compatible runtime clients are optional interaction surfaces, Hermes/the external runtime executes admitted work, and neither client selection nor runtime execution transfers Pantheon authority. Registre admission and consequential human decision remain separately governed.

## Terminology note

`Approach / Démarche` is the governed, reusable way to handle a recurring professional Situation.

`Workflow Candidate` is the proposed executable shape that may be handed to Hermes or another execution runtime after review.

This document keeps `Workflow Candidate` because its subject is the boundary where an Approach may become a runtime-facing candidate. It must not be read as a Pantheon workflow engine.

```text
Approach governs method.
Workflow Candidate proposes execution.
Runtime executes only after governed handoff.
```

## Core rule

```text
A workflow may be forged automatically.
Its authority is never automatic.
```

The workflow is born as a `Workflow Candidate`.

It may be launched only under a declared mode, a declared authority ceiling and a visible approval path.

## Execution topology minimalism

A Workflow Candidate should use the least agentic execution topology that can satisfy the required result and governance boundary.

```text
Boring reliability before expanded execution complexity.
```

Selection precedence:

| Observed need | Preferred candidate topology |
|---|---|
| Known, repeatable transformation | deterministic workflow or script, with bounded LLM interpretation only where needed |
| Dynamic exploration | bounded Hermes / ReAct-style execution with explicit stop conditions |
| Critique or reflection | reflection only when an explicit review rubric exists |
| Large independent partitions | deterministic sharding before multi-agent decomposition |
| Distinct scale, context or permission boundaries | multi-agent only when the separation is demonstrated rather than merely available |
| Long-running work | checkpointed external execution rather than open-ended autonomy |

An increase in topology complexity must be justified by at least one material requirement such as a different permission boundary, tool boundary, memory boundary, model requirement, runtime requirement, context limit or demonstrated scale constraint.

Pre-launch forging must prefer a bounded topology that can stop cleanly:

```text
continue only through already admitted scope;
do not silently widen tools, provider, data scope or effect class;
stop at declared checkpoints;
return blockers or capability gaps instead of improvising authority.
```

Topology selection does not determine output status, Evidence status, approval, memory admission or autonomy. Those rules remain with the Task Contract, `GOVERNED_AUTONOMY_GRADIENT.md`, Evidence, approval, memory and `HERMES_INTEGRATION.md` owners.

## Position in the request lifecycle

```text
raw user request
→ Case / Situation intake brief (`REQUEST_LIFECYCLE.md`)
→ Approach selection
→ Workflow Candidate
→ role review
→ Zeus procedural arbitration
→ User Decision Gate if required
→ governed execution handoff
→ Hermes execution
→ Result Candidate + Evidence Pack Candidate
→ review / approval / rejection
```

The protocol starts only after a minimum situation has been clarified.

If the system cannot build a usable Case / Situation brief (compatibility identifier `dossier_situation_brief`, owned by `REQUEST_LIFECYCLE.md`), the correct output is `pending_clarification`, `pending_source`, `pending_contract_scope` or `blocked`, not an improvised workflow.

## Role sequence

| Stage | Role viewpoint | Function |
|---|---|---|
| 1 | IRIS | clarify the actual request and intended audience |
| 2 | ATHENA | select the Approach family and decompose the task |
| 3 | ARGOS | identify required sources, versions, provenance and evidence gaps |
| 4 | THEMIS | identify risk, approval ceiling, vetoes and external-effect boundaries |
| 5 | HEPHAISTOS | forge the Workflow Candidate and required module chain |
| 6 | APOLLO | review completeness, usability and delivery readiness |
| 7 | ZEUS | arbitrate status, launch mode and next procedure |
| 8 | HUMAN | decide any professional commitment, transmission or durable validation |

The names above are governance viewpoints.

They are not autonomous actors.

A Hermes profile may produce a candidate view aligned with a role, but it does not hold the role's authority.

## Workflow Candidate minimum shape

```text
workflow_candidate:
  id:
  title:
  dossier_situation_brief_ref:
  user_request:
    raw:
    clarified:
    intended_output:
    intended_audience:
  purpose:
  approach_family:
  workflow_family:
  trigger:
  inputs:
    required:
    optional:
    forbidden:
  sources:
    expected:
    available:
    missing:
    superseded_or_uncertain:
  modules:
    required:
    optional:
    unavailable:
  steps:
    - step_id:
      name:
      owner_layer:
      required_inputs:
      expected_output:
      output_status:
      failure_behavior:
  outputs:
    result_candidate:
    evidence_pack_candidate:
    draft_artifacts:
    annotated_artifacts:
    register_candidate_allowed:
  authority:
    launch_mode:
    max_authority_level:
    approval_ceiling:
    external_action_allowed:
    canonical_effect_allowed:
  forbidden_effects:
  capability_gaps:
  blocking_questions:
  non_blocking_questions:
  observability:
    trace_expected:
    idempotency_key_required:
  zeus_status:
  human_decision_required:
```

This shape is documentary.

It is not an executable schema.

Any schema addition under `schemas/` requires protected-path review.

The added `approach_family` field is explanatory. It distinguishes the governed professional method from the runtime-facing `workflow_family`. It does not create a schema field until a protected-path schema review explicitly does so.

## Launch modes

| Mode | Meaning | Typical use |
|---|---|---|
| `draft` | the workflow is described but cannot run | design / review |
| `test` | runs on provided examples or sample material only | validation before live use |
| `shadow` | observes real inputs and produces would-have-done traces | risk-free calibration |
| `assisted` | creates candidates, questions and drafts for user validation | default professional mode |
| `active_guarded` | may execute low-risk internal writes under explicit policy | mature internal workflow |
| `active_durable` | stable, monitored, versioned and disableable workflow | only after proof and review |

Default for professional Case work:

```text
launch_mode: assisted
external_action_allowed: false
canonical_effect_allowed: false
```

## Authority ceilings

The candidate must declare its maximum effect before launch.

```text
read_only
propose_only
internal_draft_write
internal_controlled_write
storage_write
external_draft
external_action
canonical_effect
```

Rules:

- `external_action` requires User Decision Gate and explicit approval.
- `canonical_effect` cannot be performed by the runtime.
- Registre Probatoire mutation is not a runtime effect.
- Memory promotion is not a workflow side effect.
- A draft email remains `external_draft`, not `external_action`.

## Pre-launch Zeus arbitration

ZEUS arbitrates procedure, not truth.

Possible statuses:

| Zeus status | Meaning |
|---|---|
| `ready_for_read_only_launch` | observation / extraction may proceed under Task Contract |
| `ready_for_assisted_launch` | candidate outputs may be generated, with human review |
| `pending_clarification` | user intent, audience or project target unclear |
| `pending_source` | required source, version or proof missing |
| `pending_contract_scope` | mission boundary unclear |
| `risk_review_required` | Themis risk requires attention before launch |
| `approval_required_before_launch` | even launching may create or imply an effect requiring approval |
| `blocked` | proposed workflow would create false truth, unauthorized action, wrong memory or canonical mutation |

A workflow that cannot declare its effect class is blocked.

## Example — ERP effectif impact review

```text
workflow_candidate:
  title: Impact review from client email and changed effectif
  approach_family: incoming_document_impact_review
  workflow_family: incoming_document_impact_review_runtime_candidate
  trigger: email + attachment
  purpose: identify project impacts without external commitment
  modules:
    required:
      - email_reader
      - attachment_extractor
      - OCR
      - document_classifier
      - version_detector
      - project_lookup
      - contract_scope_checker
      - plan_retrieval
      - vision_plan_analysis
      - impact_matrix_builder
      - evidence_pack_builder
    optional:
      - PDF_annotation
      - draft_email_generator
  outputs:
    result_candidate: impact_matrix
    evidence_pack_candidate: required
    draft_artifacts:
      - internal_note
      - draft_email_not_sent
    annotated_artifacts:
      - plan_extract_candidate
  authority:
    launch_mode: assisted
    max_authority_level: external_draft
    approval_ceiling: C3_or_C4_to_confirm
    external_action_allowed: false
    canonical_effect_allowed: false
  forbidden_effects:
    - send_email
    - validate_ERP_notice
    - mutate_Registre_Probatoire
    - promote_memory
    - confirm_client_instruction_as_approved
  zeus_status: ready_for_assisted_launch
  human_decision_required: true
```

## Example — fire-safety notice preparation

```text
workflow_candidate:
  title: Governed ERP fire-safety notice preparation
  approach_family: regulated_notice_candidate_preparation
  workflow_family: regulated_notice_runtime_candidate_preparation
  trigger: user request
  purpose: prepare notice candidate and missing-information list
  required_preflight:
    - contract_scope_check
    - latest_plan_confirmation
    - project_identity_check
    - ERP_type_category_effectif_check
    - previous_notice_check
  authority:
    launch_mode: assisted
    max_authority_level: external_draft
    external_action_allowed: false
    canonical_effect_allowed: false
  zeus_status: pending_source_or_ready_for_assisted_launch
  human_decision_required: true
```

## Refused shortcuts

```text
unclear user request -> workflow launch
runtime memory -> approved assumption
Notion row -> proof
OCR text -> verified source
vision detection -> regulatory validation
PDF annotation -> professional conclusion
draft email -> sent email
workflow success -> Registre Probatoire mutation
Hermes done -> Pantheon approved
```

## Boundary

The protocol governs the status of Workflow Candidates.

It does not make Pantheon a workflow engine.

The execution runtime executes only after a governed handoff, and returns candidates for review.
