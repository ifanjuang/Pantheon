# Spice Reference Distillation

Status: reference distillation — external pattern review, not doctrine by itself.
Boundary profile: external_reference_review.

This document distills useful patterns from `Dyalwayshappy/Spice` for Pantheon Next.

It does not install Spice, create a runtime, create a Hermes skill, create an OpenWebUI plugin, create a decision engine, create an approval engine, create memory behavior or authorize external execution.

Canonical boundaries remain governed by:

- `STATUS.md`;
- `CAPABILITY_PLACEMENT.md`;
- `MODULAR_DOMAIN_REORIENTATION.md`;
- `DOMAIN_PACK_SPEC.md`;
- `EXTERNAL_TOOL_PLACEMENT_REGISTER.md`.

If this reference conflicts with those documents, they win.

## Reviewed object

Spice describes itself as a decision-layer runtime above agents.

Its useful claim is separation between:

```text
decision before execution
execution after approval
outcome after execution
```

This is compatible with Pantheon only if Spice remains a reference, not an authority.

## Placement decision

```text
Decision Zeus: Refusé dans le core.
Status: external reference / to verify.
Repo state: documented non implemented.
```

Spice must not be placed as:

- Pantheon core;
- Pantheon decision authority;
- approval engine;
- memory engine;
- Registre Probatoire source;
- Hermes default orchestrator;
- OpenWebUI hidden workflow runner;
- canonical evidence validator.

Spice may be used as:

- UX reference for decision surfaces;
- methodological reference for pre-execution comparison;
- vocabulary reference for unsupported-semantics reporting;
- inspiration for approval-gated executor handoff;
- inspiration for read-only perception before action.

## Compatible distillation

### 1. Decision Card -> Decision Surface Candidate

Spice's Decision Card pattern is useful because it makes a decision inspectable.

Pantheon should not import the card as authority. It may distill the card into a display pattern:

```text
decision_surface_candidate:
  linked_task_contract:
  linked_context_pack:
  decision_question:
  candidate_options:
  selected_option_candidate:
  rejected_options:
  evidence_refs:
  trade_offs:
  unresolved_tensions:
  required_approval:
  allowed_next_effect:
  forbidden_next_effects:
  status: candidate | to_verify | blocked
```

This object is a review surface. It is not approval, proof or memory.

### 2. `/sources` -> Evidence Pack display

Spice's source inspection pattern maps to Pantheon's Evidence Pack display.

Rule:

```text
sources shown != sources validated
```

A source shown in a decision surface remains an Evidence Item Candidate until governed review qualifies it.

### 3. `/why` -> rationale and objection view

The useful pattern is not private chain-of-thought exposure. The useful pattern is a structured, reviewable rationale:

```text
why_view:
  selected_option:
  decisive_constraints:
  decisive_evidence:
  rejected_trade_offs:
  uncertainty:
  objections:
  what_would_change_the_decision:
```

This supports review without pretending that the system has final authority.

### 4. `/details` -> expanded audit card

A short decision summary should be expandable.

Recommended expansion fields:

```text
expanded_decision_card:
  decision_question:
  scope:
  candidate_options:
  scoring_or_comparison_basis:
  evidence_refs:
  constraint_checks:
  approval_boundary:
  execution_boundary:
  memory_boundary:
  result_candidate_expectation:
  evidence_pack_candidate_expectation:
  outcome_observation_expectation:
```

### 5. `/json` -> raw artifact inspection

Raw artifacts are useful for developers, reviewers and tests.

They must remain raw inspection data, not user-facing truth.

```text
raw_artifact -> debug / audit support
raw_artifact != doctrine
raw_artifact != evidence pack
raw_artifact != proof
```

### 6. `decision.md` -> bounded guidance reference

Spice's `decision.md` is useful as a bounded decision-guidance idea: objectives, constraints, weights, trade-off rules and risk budgets.

Pantheon should not import it as a runtime policy file.

Pantheon already holds this material across:

- Domain Pack source policy;
- evidence expectations;
- risk triggers;
- output statuses;
- delivery gates;
- answering / acting boundary;
- memory rules;
- review angles;
- User Decision Gate.

Distilled rule:

```text
Decision guidance may shape comparison.
It must not grant capability, approval, memory or external authority.
```

### 7. Support contract -> Capability support declaration

Spice reports unsupported score dimensions, constraints or trade-off rules instead of guessing.

Pantheon should keep this pattern.

A module or adapter must declare what it can evaluate:

```text
capability_support:
  supported_source_types:
  supported_checks:
  supported_constraints:
  supported_trade_off_rules:
  unsupported_semantics:
  safe_fallback:
```

Unsupported semantics produce a Capability Gap, not an improvised result.

### 8. Read-only perception -> intake and source audit

Spice's read-only perception is compatible with Pantheon if treated as intake:

```text
read_only_perception:
  may_read:
  may_extract:
  may_compare:
  must_not_write:
  must_not_execute:
  must_not_approve:
  must_not_remember:
```

This maps to pre-analysis intake discipline and source audit.

### 9. Approval-gated executor handoff -> governed execution handoff

Spice's executor handoff is close to Pantheon's governed execution handoff.

Pantheon version must remain stricter:

```text
governed_execution_handoff:
  linked_task_contract:
  linked_context_pack:
  approval_ref:
  requested_effect: read_only | internal_state_change | external_effect | canonical_effect
  target_runtime:
  allowed_inputs:
  forbidden_effects:
  expected_result_candidate:
  expected_evidence_pack_candidate:
  idempotency_key:
  trace_refs:
```

Runtime success is not governance approval.

### 10. Outcome -> Outcome Observation Candidate

Spice records outcomes after execution.

Pantheon should keep the outcome separated from validation:

```text
outcome_observation_candidate:
  acted:
  external_effect:
  canonical_effect: false
  changed_objects:
  unchanged_objects:
  produced_candidates:
  blocked_items:
  follow_up_needed:
  approval_still_required:
  evidence_refs:
```

The important field is `unchanged_objects`, for example:

```text
draft created, email not sent
patch candidate produced, repository not modified
register candidate proposed, Registre Probatoire unchanged
```

## Refused imports

Pantheon must not import:

- Spice as decision-layer runtime;
- `.spice/state` as governance state;
- `.spice/memory` as canonical memory;
- `.spice/approvals` as Pantheon approvals;
- Spice Decision Cards as Evidence Packs;
- Spice outcomes as validation;
- Spice executor handoff as authorization;
- automatic reflection as memory promotion;
- decision evolution as doctrine mutation.

## Recommended Pantheon wording

```text
Spice may inspire Pantheon decision surfaces.
Spice must not become Pantheon's decision authority.
```

```text
Decision surfaces show candidate reasoning, evidence and boundaries.
Pantheon governs status and approval.
Hermes executes bounded tasks.
The human decides.
```

## Optional next work

A future OpenWebUI decision surface could reuse the compatible pattern:

```text
compact summary
-> sources
-> why
-> objections
-> raw artifact
-> approval boundary
-> handoff preview
```

This would remain a display and capture surface, not a runtime.
