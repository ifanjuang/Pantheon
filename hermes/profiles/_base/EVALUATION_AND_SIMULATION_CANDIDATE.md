# Hermes Evaluation and Simulation Candidate

Status: Hermes capability candidate template — not installed, not implemented.

This document describes a possible Hermes-side evaluation and simulation capability. It does not install a tool, create a Hermes skill, add a Pantheon runtime, simulator, evaluator, queue, scheduler, provider router, gateway, observability backend, MCP/A2A layer, automatic approval system, automatic memory system or self-improvement loop.

```text
Hermes clients handle runtime interaction.
Hermes Agent executes externally under Task Contract.
Pantheon Cockpit may expose governed status, Evidence gaps and decision gates.
Pantheon Next governs consequential status.
```

## Purpose

The candidate describes how Hermes might later execute bounded simulations and evaluations for high-risk candidate outputs.

It may support:

```text
pre-execution simulation
trajectory evaluation
post-decision proposal/outcome feedback
guardrail signaling
risk note generation
Evidence Pack Candidate preparation
Improvement Candidate drafting
```

It does not authorize execution, installation, dependency adoption, professional validation, delivery, memory retention or doctrine change.

```text
simulation completed != approval
score produced != policy decision
runtime success != authorization
projection != persistence
client selected != governance authority
```

## Candidate identity

```yaml
capability_candidate: hermes_evaluation_and_simulation
owner_layer: hermes
status: not_installed_candidate
pantheon_role: none
canonical_authority: none
governed_by:
  - docs/governance/HERMES_INTEGRATION.md
  - docs/governance/PRE_EXECUTION_SIMULATION.md
  - docs/governance/TASK_CONTRACTS.md
  - docs/governance/EVIDENCE_PACK.md
  - docs/governance/APPROVALS.md
  - docs/governance/MEMORY.md
  - docs/governance/SCOPE_ISOLATION.md
  - docs/governance/EXTERNAL_TOOLS_POLICY.md
```

## Candidate components

The capability may be decomposed conceptually into:

```text
simulation_runner
persona_suite
scenario_set
trajectory_eval
proposal_outcome_feedback
guardrail_signal
trace_summary
simulation_evidence_summary
improvement_candidate_builder
capability_gap_reporter
```

These are design terms, not implemented classes, tools, workers or services.

### simulation_runner

Runs a bounded simulation against one candidate action or output.

Inputs may include:

```text
candidate_action
candidate_output
simulation_goal
scenario_set
allowed_context
excluded_context
approval_ceiling
memory_rule
```

Outputs may include a `Simulation Result Candidate`, risk status, limitations and recommended next action.

It must not execute a real action, send/publish an output, merge a patch, promote memory or silently broaden scope.

### persona_suite

Defines optional synthetic recipient/stakeholder viewpoints such as:

```text
client_reads_as_approval
contractor_reads_as_scope_validation
reviewer_checks_source_gap
admin_reads_as_submission_ready
professional_checks_liability
```

Personas are scenario devices, not users, agents, Evidence or authority.

### scenario_set

Defines bounded risk situations such as:

```text
recipient_misinterpretation
scope_expansion
source_gap
unsupported_claim
external_effect
memory_overreach
repository_mutation
prompt_or_skill_regression
```

Scenario sets should remain minimal. Expanding beyond the Task Contract requires contract revision.

### trajectory_eval

May inspect the path rather than only final text, including source selection, assumption handling, scope preservation, tool-use sequence, risk escalation, approval boundary and memory boundary.

A trajectory evaluation is a review signal, never final authority.

### proposal_outcome_feedback

May evaluate real reviewed cases after the human decision or bounded effect is known, using the records already owned by the data platform / approval / audit responsibilities rather than creating a second feedback ledger.

The smallest useful comparison keeps references to:

```text
candidate/proposal identity and version
human disposition or decision reference
actual resulting object/effect reference when one exists
later correction/reversal reference when one exists
```

Derived review metrics may include:

```text
acceptance
material override
abstention / held / unresolved
reformulation or reclassification
proposal-to-decision duration
later correction or reversal
```

Metrics should be recomputed from the referenced proposal and actual outcome where possible. Do not treat a manually stamped outcome label as stronger than the underlying records when they disagree. Report the evaluated class, time window and sample size so small or heterogeneous samples are not presented as a universal model score.

An override is a disagreement signal to inspect, not automatically a model error: the proposal may have been underspecified, the human may have changed scope, new Evidence may have arrived, or the correct professional action may genuinely be to abstain. Read material disagreements individually before proposing a reusable change.

This feedback may support an `Improvement Candidate`, but it must not automatically rewrite prompts, skills, policies, doctrine, routing, model bindings or memory. Persistent acceptance is not approval authority; persistent disagreement is not permission to bypass the human gate.

Existing proposal, approval, execution and audit records remain owned by their current Pantheon/data-platform contracts, including `docs/governance/DATA_PLATFORM_ARCHITECTURE.md`. This candidate only describes a derived evaluation view over those records.

```text
metric != truth
override != model error
acceptance != Evidence
feedback observation != memory promotion
correlation != authorization
```

### guardrail_signal

Reports a possible violation of declared policy, scope, memory, privacy, external-tool or approval constraints.

A guardrail signal is a risk note, not policy authority.

### trace_summary

May summarize governance-relevant observations:

```text
what was tested
which scenarios were used
which governed sources were considered
which risks appeared
what was excluded
what remains uncertain
```

It must not expose hidden chain-of-thought, scratchpads, secrets, provider credentials, unredacted private payloads or full runtime logs as proof.

### simulation_evidence_summary

Formats attributable observations so they may support an Evidence Pack Candidate:

```text
candidate -> scenario -> observed failure mode -> risk -> limitation -> approval implication
```

Simulation output is not Evidence merely because it was generated and does not approve its Evidence Pack Candidate.

### improvement_candidate_builder

May propose bounded changes such as revised wording, additional source requirements, a User Decision Gate trigger, an Evidence checklist item, prompt constraint, skill anti-pattern or rejected-pattern note.

It must never automatically promote prompts, activate skills, change workflows/doctrine/providers, promote memory or merge repository changes.

### capability_gap_reporter

Reports when the bounded simulation cannot safely proceed, for example missing allowed source, approval ceiling, scenario set, excessive scope, disallowed private data, unavailable external evaluator or a risk that cannot be safely simulated.

## Required input envelope

```yaml
required_inputs:
  task_contract: required
  candidate_action_or_output: required
  simulation_goal: required
  risk_level: required
  approval_ceiling: required
  memory_rule: required
  allowed_context: required
  excluded_context: required
  scenario_set: required
  evidence_requirements: required
  user_decision_gate_policy: required
```

Optional inputs may include a persona suite, guardrail checks, trajectory criteria, an admitted external-evaluation reference, expected output schema and example failure modes.

## Forbidden inputs and authority

A Hermes evaluation/simulation run must never receive:

- memory promotion authority;
- doctrine mutation authority;
- approval authority;
- authority to perform the real consequential action it is simulating;
- raw client database authority;
- provider secrets as evaluation material.

The following material is also forbidden unless explicitly admitted by the applicable Task Contract and policy owner:

- unscoped client/session context or client-internal Knowledge stores;
- global retrieval/vector-store access;
- unrelated project context;
- unrestricted production traces;
- unredacted confidential payloads;
- protected files;
- production credentials required only for an explicitly authorized external evaluation binding;
- repository write-capable tools.

## Required outputs

```yaml
required_outputs:
  result_status: required
  candidate_tested: required
  scenario_set_used: required
  risks_detected: required
  limitations: required
  approval_impact: required
  memory_impact: required
  external_effect_impact: required
  evidence_summary: required
  recommended_next_action: required
```

Optional outputs may include `trajectory_evaluation_candidate`, `guardrail_signal`, `capability_gap`, `improvement_candidate` and `user_decision_gate_recommendation`.

## Output status vocabulary

```text
not_required
proposed
blocked_by_scope
blocked_by_approval
ready_for_external_execution
completed_no_material_risk
completed_with_reserve
risk_detected
source_gap_detected
scope_gap_detected
external_effect_risk_detected
memory_risk_detected
inconclusive
failed
superseded
```

These are candidate/governance-facing statuses, not hidden Hermes runtime truth and not approval states.

## Example output skeleton

```yaml
simulation_result_candidate:
  linked_task_contract: example-task-contract-id
  candidate_tested: client_email_candidate_v1
  result_status: risk_detected
  scenario_set_used:
    - recipient_misinterpretation
    - scope_expansion
    - source_gap
  risks_detected:
    - may imply professional validation
    - may exceed available evidence
    - may require User Decision Gate before transmission
  limitations:
    - simulated from bounded fictional context
    - no real contract interpretation performed
  approval_impact: transmission_blocked_pending_review
  memory_impact: no_memory_by_default
  external_effect_impact: no_send_without_approval
  recommended_next_action: revise_candidate_or_open_user_decision_gate
```

## Task Contract example

```yaml
task_contract:
  task_id: hermes-simulation-example-001
  task_type: pre_execution_simulation
  candidate_action: send_client_email
  risk_level: high
  approval_ceiling: no_external_transmission
  simulation_goal: detect whether the candidate email may imply validation
  allowed_context:
    - selected_quote_excerpt
    - selected_cctp_excerpt
    - reception_status_note
  excluded_context:
    - other_projects
    - unrelated_client_files
    - unverified_legal_conclusions
  scenario_set:
    - client_reads_as_approval
    - contractor_reads_as_scope_validation
    - later_dispute_uses_email_as_evidence
  expected_outputs:
    - Simulation Result Candidate
    - Evidence Pack Candidate entry
    - User Decision Gate recommendation if risk remains
  memory_rule: no_memory_by_default
```

## Execution discipline

A future admitted sandbox should use the smallest scenario set, read-only bounded context, no automatic external effects, no governed memory write, no prompt/skill/workflow promotion and a clear Evidence Pack Candidate return.

A successful sandbox demonstrates only the tested runtime behavior. It does not establish adoption, professional correctness or broader authorization.

## Runtime interaction and governed projection

A compatible Hermes client may expose runtime-facing state such as simulation requested/status, candidate tested, scenario progress and cancel/pause controls when supported.

Pantheon Cockpit or existing Card owners may expose governed state such as:

```text
scenario summary
risk summary
limitations
Evidence Pack Candidate reference
approval gaps
recommended decision options
User Decision Gate
```

No client or governed projection may provide a control that bypasses the Task Contract, treat a simulation pass as approval, auto-send after a pass, auto-retain repeated results or auto-promote an optimization after a score threshold.

## Anti-patterns

Reject:

- Hermes simulation as approval;
- simulation pass as approval or delivery permission;
- score threshold as prompt promotion;
- guardrail pass as policy approval;
- trace summary as Evidence Pack by itself;
- synthetic persona as real-user proof;
- Improvement Candidate as automatic update;
- client-side simulation bypassing Task Contract;
- external evaluator installation by implication;
- provider gateway adoption by convenience.

## Minimal sandbox test

A first sandbox test, if separately approved, should use:

```text
fictional task
read-only bounded context
no production credentials unless strictly required by an admitted binding
no protected files outside the Task Contract
no external write
no governed memory writes
small scenario set
clear Simulation Result Candidate
Evidence Pack Candidate return
User Decision Gate recommendation when risk remains
```

The sandbox output remains a candidate for Pantheon review before any broader adoption.

## Final rule

```text
Hermes may test a candidate.
Hermes must not validate it.
Pantheon governs what the test means.
The human decides when risk remains material.
```
