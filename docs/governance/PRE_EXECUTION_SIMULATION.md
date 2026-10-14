# Pre-Execution Simulation

Status: active support doctrine — specialized pre-execution stress test within the governed method — documented non-implemented.
Boundary profile: active_support_doctrine.

This document specializes Movement 6 — `Test` of `GOVERNED_METHOD_STANDARD.md` for cases where a candidate should be stress-tested through bounded simulation before consequential use.

It owns the simulation-specific method seam only. Generic Task Contract, Evidence, approval, memory, User Decision Gate, Hermes/runtime and Cockpit rules remain with their existing owners.

## Core rule

```text
Simulation may reveal failure modes.
Simulation does not authorize the real action.
```

A simulation result is candidate review material. It may affect status, Evidence expectations or the need for a human decision, but it is not approval, proof, memory or execution authority by itself.

## Parent-method placement

`GOVERNED_METHOD_STANDARD.md` owns the generic method movement:

```text
Produce Candidate -> Test -> Status
```

Pre-execution simulation is one optional Test technique when ordinary review is insufficient to expose material consequence.

Use the smallest test that can reveal the relevant failure mode. Do not turn simulation into a mandatory ritual for every request.

## When simulation is justified

Consider bounded simulation when a candidate may carry material risk such as:

```text
recipient misinterpretation
unsupported or weakly supported claim
contradictory reply
scope expansion
external transmission or write
professional liability
privacy or sensitive-context leak
memory or Registre overreach
repository or protected-file mutation
prompt, skill or workflow regression
provider / gateway configuration change
high-risk automation proposal
```

A fluent or technically successful candidate is not sufficient reason to skip this test when consequence is material.

## Simulation request seam

`TASK_CONTRACTS.md` owns the delegated task boundary. When simulation is non-trivial, the Task Contract or equivalent governed review note should bound at least:

```text
candidate_action_or_output
simulation_goal
risk_level
allowed_context
excluded_context
scenario_set
approval_ceiling
memory_rule
expected_result_summary
```

The simulation request must not silently broaden project, source, private-data, provider or repository scope.

## Scenario set

Useful bounded scenario families include:

```text
recipient_misinterpretation
source_gap
contradictory_reply
scope_expansion
unsupported_claim
professional_liability
external_effect
memory_overreach
privacy_leak
repository_mutation
provider_or_gateway_drift
prompt_or_skill_regression
unanswerable_question
```

Scenario sets are test devices, not users, Roles, Evidence or authority.

Prefer the smallest scenario set that can expose the material risk.

## Hermes execution seam

Pantheon does not execute simulations.

A future Hermes-side capability candidate is described in:

`hermes/profiles/_base/EVALUATION_AND_SIMULATION_CANDIDATE.md`

That profile owns candidate execution-shape detail such as runner, persona/scenario support, trajectory evaluation, guardrail signals and runtime return formatting. It does not acquire Pantheon authority.

```text
Task Contract bounds the simulation.
Hermes may execute the admitted simulation externally.
Simulation output returns as candidate material.
Pantheon owners determine what that material means.
```

Runtime/client completion, a guardrail pass or a good score never authorizes the real consequential action.

## Simulation Result Candidate

A reviewable simulation result should make visible at least:

```text
simulation_id
linked_task_contract
simulation_goal
candidate_tested
scenario_set_used
result_status
risks_detected
limitations
approval_impact
memory_impact
external_effect_impact
recommended_next_action
```

The shape is documentary, not an executable schema.

Recommended result statuses remain:

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

`ready_for_external_execution` means the **simulation run** is sufficiently bounded for external runtime execution. It never means the real candidate action is authorized.

## Interpreting evaluation signals

Simulation may include scores, trajectory checks or guardrail signals. Interpret them only as review signals:

```text
evaluation score -> review signal
guardrail pass -> risk signal only
trajectory check -> execution-quality signal
simulation pass -> candidate confidence only
simulation failure -> possible escalation trigger
```

Never collapse them into:

```text
approval
Evidence by themselves
delivery authorization
memory promotion
doctrine mutation
provider-routing authority
```

The relevant Evidence semantics remain with `EVIDENCE_PACK.md`; approval semantics remain with `APPROVALS.md` and `USER_DECISION_GATE.md`.

## Paired baseline/candidate governance-damage accounting

When a governance layer, prompt, policy, Skill or other candidate can change task utility, an aggregate candidate score is insufficient. The test should expose whether the intervention repaired failures or destroyed behavior that already worked.

Use this technique only where a meaningful baseline exists. Before observing outcomes, freeze the exact baseline, exact candidate, representative case set and evaluation rule. Run both on the same cases under materially comparable conditions.

For every paired case, classify the transition explicitly:

```text
baseline pass -> candidate fail = damage
baseline fail -> candidate pass = rescue
baseline pass -> candidate pass = pass survival
baseline fail -> candidate fail = unchanged failure
```

Report the raw counts and denominators. Where the denominator is non-zero, the useful derived signals are:

```text
governance_damage_rate = pass_to_fail / baseline_passes
rescue_rate            = fail_to_pass / baseline_failures
pass_survival_rate     = pass_to_pass / baseline_passes
```

Keep abstention, refusal, timeout, transport failure and other liveness outcomes visible separately when they matter. A runtime failure must not be silently scored as a governance failure or governance success; the report should say which layer failed.

```text
same aggregate score != same regressions
runtime liveness != governance quality
candidate abstention != task success
```

Do not tune the frozen candidate after inspecting these paired outcomes and then report the same evaluation as if it were prospective. A material change creates a new candidate/version and therefore a new comparison. This keeps evaluation useful for falsification rather than turning observed failures into hidden benchmark optimization.

The method creates no acceptance threshold by itself. Damage, rescue and survival remain review signals; the applicable Task Contract, Evidence, approval and User Decision Gate owners determine what consequence follows.

```text
paired evaluation != approval
governance improvement != zero regressions
frozen comparison != permanent benchmark
```

## Improvement Candidate

A simulation may produce an Improvement Candidate describing:

```text
observed_failure
simulation_scenario
candidate_affected
proposed_change
expected_benefit
risk_note
affected_scope
approval_requirement
rollback_or_supersession_path
```

An Improvement Candidate is a proposal for review. It must not automatically:

```text
merge repository changes
promote prompts
activate skills
change workflows or doctrine
change providers
promote memory
```

Provenance for the external pattern is maintained by `DISTILLATION_REGISTRY.md`; this document does not need to repeat vendor/reference history.

## Handoffs to existing owners

Simulation-specific method stops at the candidate result and its local interpretation.

Downstream responsibilities stay separated:

- `EVIDENCE_PACK.md` owns whether and how attributable simulation observations support an Evidence Pack Candidate;
- `APPROVALS.md` owns approval legitimacy and ceilings;
- `USER_DECISION_GATE.md` owns consequential human escalation;
- `MEMORY.md` and `SCOPE_ISOLATION.md` own durable-retention boundaries;
- `HERMES_INTEGRATION.md` owns runtime/client/PDP/PEP/Cockpit placement;
- `GOVERNED_METHOD_STANDARD.md` owns the generic Test -> Status movement.

```text
simulation result != Evidence admission
simulation pass != approval
simulation repetition != Registre Probatoire entry
runtime success != authorization
projection != approval
```

## Safe outcomes

A simulation may support outcomes such as:

```text
continue_as_draft
continue_with_reserve
request_missing_source
narrow_scope
split_into_variants
revise_candidate
run_bounded_followup_simulation
open_user_decision_gate
block_delivery_or_transmission
reject_memory_candidate
review_improvement_candidate
```

The applicable owner determines the actual governed status and gate.

## Boundary

`active_support_doctrine` boundary profile applies.

This document does not create a simulator, evaluator, workflow runner, scheduler, queue, provider router, observability backend, MCP/A2A layer, approval engine, memory engine or self-improvement loop.

It does not authorize Hermes, a client or Pantheon Cockpit to execute or approve the real action because a simulation passed.

```text
Simulation stress-tests the candidate.
Evidence owners qualify attributable observations.
Status and approval owners govern consequential use.
The human decides where required.
```
