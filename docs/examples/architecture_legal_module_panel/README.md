# Example — Pantheon Cockpit Module Panel — Architecture and Legal Domains

Status: fictional UI example — educational support only.

This example shows how a future Pantheon Cockpit projection may expose governed role participation, domain state, skill eligibility, dependency blockers and Zeus workflow proposals for a sensitive architecture/legal dossier.

It is not an implementation, a development-ready UI specification, legal advice, architectural advice, insurance advice or professional validation.

```text
Hermes clients handle runtime interaction.
Hermes Agent executes externally.
Pantheon Cockpit exposes governed projections.
Pantheon Next governs consequential status.
The human decides where required.
```

## Scenario

A contractor failed before completion. A replacement company submitted a recovery quote. The client asks the architect whether the quote can be approved and whether some items may be charged as extras.

The user wants candidate support for:

- an internal risk note;
- a quote comparison;
- a neutral client-email draft;
- missing-source identification;
- a Register Candidate only if later justified and separately authorized.

Architecture and legal domain packs are both relevant. That raises governance pressure; it does not create professional authority.

## Governed projection

A Cockpit view may project a compact state such as:

```text
Pantheon Module Panel — Fictional Dossier

Task status:
  candidate_task_contract_required

Active domains:
  architecture: project_enabled
  legal: project_enabled

Professional reliance:
  draft_only_until_human_review

Transmission:
  blocked_pending_decision

Retention:
  register_candidate_only_after_separate_authorization
```

The Cockpit projects this state. It does not own the underlying authorization, runtime execution, Evidence or persistence merely because it displays them.

## Domain state

```yaml
domain_activation:
  architecture:
    status: project_enabled
    reason: quote_review_and_architect_client_response
    mandatory_roles: [ATHENA, ARGOS, THEMIS]
    professional_reliance: draft_only_until_architect_review
    blocks_if_disabled:
      - architecture_skill_candidates
      - architecture_domain_templates
      - architecture_external_transmission_as_domain_output

  legal:
    status: project_enabled
    reason: contractual_or_liability_risk_in_quote_validation_wording
    mandatory_roles: [ARGOS, THEMIS, ZEUS]
    professional_reliance: draft_only_until_competent_professional_review
    blocks_if_disabled:
      - legal_skill_candidates
      - legal_note_templates
      - legal_external_transmission_as_domain_output
```

Domain state constrains review and skill eligibility. It does not authorize execution or professional reliance.

## Role readiness brief

A compact preflight may be projected without turning Pantheon Roles into runtime agents.

```yaml
role_readiness_brief:
  ATHENA:
    status: active
    reason: task_needs_decomposition
  ARGOS:
    status: mandatory_for_risk
    reason: evidence_gap
  THEMIS:
    status: mandatory_for_risk
    reason: professional_liability_and_external_effect
  APOLLO:
    status: standby
    reason: client_facing_output_not_yet_ready
  HEPHAISTOS:
    status: active
    reason: artifact_candidates_requested
  IRIS:
    status: standby
    reason: transmission_not_authorized
  ZEUS:
    status: active
    reason: procedural_arbitration_required
```

A Role readiness signal is governance review material, not agent execution.

## Zeus workflow proposal

Zeus may propose procedure; Hermes Agent remains the execution owner.

```yaml
zeus_workflow_proposal:
  workflow_status: proposed
  recommended_path:
    - confirm_task_contract_candidate
    - confirm_architecture_and_legal_domain_scope
    - build_context_pack_from_selected_sources
    - request_source_gap_review_candidate
    - request_quote_comparison_candidate
    - request_risk_boundary_review_candidate
    - prepare_evidence_pack_candidate
    - expose_user_decision_gate_if_transmission_requested
    - keep_retention_blocked_until_separate_authorization

  blocked_paths:
    - direct_client_validation_email
    - external_transmission_without_approval
    - legal_conclusion_without_professional_review
    - architecture_compliance_claim_without_source_review
    - memory_promotion_from_runtime_state
```

## Effective Policy projection

```yaml
effective_policy:
  task_contract:
    required: true
    status: candidate_required

  context_pack:
    required: true
    status: missing
    blocks:
      - hermes_dispatch
      - evidence_pack_completion

  evidence:
    required: true
    status: incomplete
    blocks:
      - consequential_approval
      - delivery_gate
      - register_candidate_review

  approval:
    required: true
    status: missing
    approval_level: professional_review_required

  retention:
    status: blocked
    rule: approve_plus_separate_retention_authorization

  external_transmission:
    status: blocked
    reason: evidence_and_approval_missing
```

This is a projection of policy/state, not a second policy owner.

## Dependency blockers

The Cockpit should expose why an action is unavailable rather than hiding the capability.

```yaml
dependency_blockers:
  hermes_dispatch:
    status: blocked_by_missing_context_pack
    allowed_user_actions:
      - create_context_pack_candidate
      - attach_missing_sources
      - narrow_scope

  approval_prompt:
    status: blocked_by_missing_evidence
    allowed_user_actions:
      - request_evidence_pack_candidate
      - request_source_gap_review

  register_candidate_review:
    status: blocked_by_missing_evidence_scope_or_retention_authorization
    allowed_user_actions:
      - keep_as_runtime_context_only
      - request_register_candidate_later

  external_transmission_gate:
    status: blocked_by_missing_approval
    allowed_user_actions:
      - prepare_draft_only
      - request_user_decision_gate
      - cancel_transmission
```

## Skill candidates

Domain participation may make skills eligible. Eligibility does not authorize execution.

```yaml
skill_candidates:
  eligible_after_task_contract:
    - architecture_devis_analysis_candidate
    - architecture_cctp_review_candidate
    - legal_source_review_candidate
    - legal_issue_framing_candidate

  blocked_now:
    architecture_devis_analysis_candidate:
      reason: context_pack_missing
    legal_note_draft_candidate:
      reason: legal_domain_draft_only_and_source_freshness_missing
    external_client_email_candidate:
      reason: transmission_risk
```

## What the projection should make visible

Visible:

- architecture and legal domains are relevant;
- professional reliance remains draft-only;
- ARGOS and THEMIS are mandatory because risk is present;
- Hermes-side capabilities may become eligible but are not task-authorized merely by display;
- approval is blocked until Evidence requirements are met;
- transmission is blocked until the applicable User Decision Gate is resolved;
- durable retention remains separately governed.

Forbidden implications:

```text
domain active = professional validation
skill eligible = installed or task authorized
workflow proposed = execution started
Evidence Pack Candidate = approval
User Decision Gate visible = user approved
Register Candidate visible = Registre Probatoire entry
projection visible = persisted authority
```

## User Decision Gate excerpt

If the user asks to send a client email, the projection should expose the conflict instead of silently converting preparation into transmission.

```text
User Decision Gate — Client transmission blocked

Conflict:
The recovery quote cannot yet be globally validated from the current source perimeter.

Options:
1. prepare internal note only;
2. prepare neutral clarification email marked draft-only;
3. request missing sources first;
4. request competent legal/professional review;
5. stop transmission.
```

## Boundary

This example is non-executable. It creates no client template, runtime tool, Hermes skill, domain authority engine, memory writer or approval engine.

It demonstrates only how Pantheon Cockpit may project existing governed state while Hermes-compatible clients/runtime remain replaceable.

```text
projection != persistence
runtime success != authorization
client selected != governance authority
```
