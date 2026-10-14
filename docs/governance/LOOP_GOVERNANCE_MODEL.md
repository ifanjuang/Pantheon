# Loop Governance Model

Status: candidate support doctrine — bounded external execution-loop governance, documented non-implemented.

Review status: candidate / to verify against external execution runtimes, cockpit cards and adapter prototypes.

Runtime status: non-executable.

This document defines how Pantheon Next may govern bounded execution loops without becoming the loop runtime.

It does not implement a loop engine, autonomous agent, workflow engine, scheduler, queue, retry worker, event bus, state machine, checkpoint store, MCP runtime, approval engine, memory engine, OpenWebUI plugin, Hermes skill, Revit add-in, connector or external action.

```text
The exposure surface exposes.
The execution runtime executes.
Pantheon Next governs.
The human decides.
```

## Purpose

Modern AI tools can iterate: try, observe, correct, retry and stop. That power is useful only when the loop is bounded.

Pantheon must not run the loop. Pantheon defines the conditions under which a loop may be launched by an execution runtime, what it may touch, how its progress is observed, which blockers stop it, what evidence it must return and which gates remain human-visible.

Core distinction:

```text
A loop may repeat.
A loop may verify.
A loop may propose.
A loop may not govern.
A loop may not approve.
A loop may not create a Registre Probatoire entry.
A loop may not decide consequential truth.
```

French working formula:

```text
Pantheon ne boucle pas.
Pantheon borne les boucles.
Le runtime boucle.
Zeus qualifie.
L'humain décide.
```

## Candidate shape status

This document contains candidate data shapes.

They are governance-readable shapes, not executable schemas.

Runnable loop contracts live in execution runtimes or adapters.

Machine validation requires a later protected schema review.

```text
Pantheon may define the loop contract shape.
Pantheon must not own the loop runtime.
Hermes may consume the contract.
Hermes must return candidates, blockers, traces and Evidence Pack Candidates.
```

## Placement

A loop belongs to the execution runtime when its primary effect is execution, extraction, checking, drafting, conversion, annotation, preparation or internal candidate production.

Pantheon becomes involved only when the loop may affect:

```text
truth status;
evidence status;
approval;
external action;
Registre Probatoire status;
scope;
professional responsibility;
doctrine status.
```

Governing a loop is not implementing the loop.

## Definition

A bounded loop is a runtime-side procedure that repeats under a declared contract until it reaches a stop condition.

Minimum definition:

```text
Bounded Loop
= task contract + permitted scope + iteration budget + checker + event stream + stop rule + candidate output.
```

It transforms:

```text
Task Contract
-> bounded runtime loop
-> Result Candidate + Evidence Pack Candidate
```

It never transforms directly into:

```text
validated truth;
approval;
external transmission;
Registre Probatoire entry;
doctrine mutation;
professional sign-off.
```

## Loop admissibility test

Before a loop is handed to an execution runtime, the exposure surface, bridge or governing review must be able to answer:

```text
1. Is the task repetitive or decomposable enough to justify iteration?
2. Is the expected result observable?
3. Is the checker independent enough from the maker step?
4. Is the scope explicit?
5. Are forbidden targets and forbidden effects explicit?
6. Is the retry budget explicit?
7. Are blockers and stop rules explicit?
8. Is the output candidate-only unless separately approved?
9. Is any external effect gated before execution?
10. Is any canonical effect refused as runtime work?
```

If any required answer is missing, the safe result is not improvised execution. It is a visible gap, pending clarification, pending source, pending approval or blocked status.

## Loop Contract candidate shape

This is a documentary shape only. It is not an executable schema.

```text
loop_contract:
  loop_id:
  linked_task_contract:
  linked_context_pack:
  purpose:
  target_runtime: execution_runtime
  launch_mode: draft | test | shadow | assisted | active_guarded | active_durable
  requested_effect: read_only | internal_state_change | external_effect | canonical_effect
  allowed_scope:
  allowed_targets:
  forbidden_targets:
  allowed_actions:
  forbidden_actions:
  max_iterations:
  max_duration:
  retry_policy:
  checker:
    kind:
    independence_expectation:
    pass_condition:
    fail_condition:
  blocker_policy:
  stop_rules:
  expected_result_candidate:
  expected_evidence_pack_candidate:
  event_stream_expected: true
  idempotency_key_required:
  trace_refs:
  zeus_gate_required:
  human_decision_required:
```

The shape reuses existing Task Contract, Context Pack, Evidence Pack, capability placement and workflow-forging doctrine. It does not replace them.

## Loop levels

Loops should be classified by dependency depth before launch.

| Level | Meaning | Typical use | Governance posture |
|---|---|---|---|
| `simple_loop` | The same action repeats until a measurable condition is met. | format cleanup, deterministic extraction, export validation. | May run under read-only or candidate-only contract. |
| `dependent_loop` | Each step depends on the previous result. | analyze -> draft -> check -> revise -> re-check. | Requires event stream and checker status. |
| `procedural_loop_with_blockers` | The runtime advances through dependent actions while some branches wait for user, source or capability input. | missing family, missing source, unavailable connector, unresolved parameter. | Requires blocker classification, branch state and visible pending decisions. |
| `consequential_loop` | The loop may approach truth, external effect, memory, approval or professional commitment. | preparing a client transmission, filing, sending, validated register update. | Must stop at a gate before the consequential effect. |

A consequential loop is not forbidden. It is forbidden to let the runtime cross the consequential boundary by itself.

## Event stream

Pantheon must not depend only on the final runtime return. Long or dependent loops need a governance-readable event stream.

The event stream is not proof by itself. It is runtime trace material that may support an Evidence Pack Candidate.

Minimum event vocabulary:

```text
event:
  event_id:
  loop_id:
  step_id:
  event_type: started | progressed | produced_candidate | checker_passed | checker_failed | retry | blocked | resumed | skipped | stopped | escalated
  process_status: waiting | processing | success | partial | failed | blocked | unknown
  governance_signal: none | to_verify | gate_open | approval_required | out_of_scope | blocked
  affected_object:
  changed_objects:
  unchanged_objects:
  evidence_refs:
  trace_refs:
  human_attention_required:
```

Core rule:

```text
Runtime event is not Evidence Pack.
Trace is not proof.
Progress is not approval.
```

## Blocker taxonomy

A blocker is not always a failure. Some blockers suspend a branch while independent work continues.

| Blocker class | Meaning | Runtime behavior | Pantheon posture |
|---|---|---|---|
| `non_blocking_user_input` | A missing input can be supplied by the user without invalidating other branches. | Suspend dependent branch; continue independent work. | Visible question card / pending input. |
| `non_blocking_capability_gap` | Optional tool, source or adapter missing. | Continue degraded path if contract allows. | Visible Capability Gap. |
| `blocking_source_gap` | Required source, version or authority missing. | Stop affected branch. | Pending source / to verify. |
| `blocking_scope_gap` | Mission, authority, target or project scope unclear. | Stop launch or branch. | Pending contract scope / gate. |
| `approval_blocker` | Continuing may create external or consequential effect. | Stop before effect. | User Decision Gate. |
| `canonical_effect_blocker` | Runtime would mutate doctrine, register state, approval status or Registre Probatoire status. | Refuse as runtime work. | Governed validation path only. |
| `safety_blocker` | Forbidden action, unsafe target, unauthorized access or destructive effect. | Stop and report. | Blocked / escalate. |

A blocked branch must name what did not change. This prevents partial success from being misread as full execution.

## Stop rules

Every loop must declare stop rules before launch.

Minimum stop rules:

```text
stop_when_success_condition_met;
stop_when_checker_repeatedly_fails;
stop_when_iteration_budget_exceeded;
stop_when_duration_budget_exceeded;
stop_when_required_source_missing;
stop_when_scope_unclear;
stop_when_approval_required;
stop_when_canonical_effect_detected;
stop_when_forbidden_target_detected;
stop_when_human_decision_required.
```

A loop that cannot stop safely is not admissible.

## Checker gate

A checker gate verifies the candidate result against declared criteria. It is not Zeus and not the human.

The checker may confirm:

```text
structure present;
required fields present;
source references attached;
forbidden output absent;
diff within allowed scope;
test result passed;
format valid;
branch completed or blocked honestly.
```

The checker must not decide:

```text
professional truth;
legal, architectural, medical or financial validity;
approval;
external transmission;
Registre Probatoire promotion;
doctrine promotion;
human intent.
```

## Output discipline

A loop return must separate runtime state from governance state.

Minimum return:

```text
loop_result:
  loop_id:
  runtime_task_status: not_started | success | partial | failed | blocked | unknown
  checker_status: not_run | passed | failed | partial | not_applicable
  governance_result_status: candidate | to_verify | gate_open | approved | rejected | blocked
  result_candidate:
  evidence_pack_candidate:
  event_summary:
  blocked_items:
  changed_objects:
  unchanged_objects:
  approval_still_required:
  human_decision_required:
  trace_refs:
```

Default governance result:

```text
governance_result_status: candidate
```

`approved` must not be produced by the runtime unless it refers to a prior explicit approval record, not to the runtime's own judgment.

## Relationship with cards

The cockpit may display loop state through existing card families. It should not create a new visible card for every event.

Recommended mapping:

| Loop object | Card family |
|---|---|
| Loop run | Run card |
| Loop step | Task card |
| Blocker | Decision / Question, Gate or Capability Gap |
| Candidate output | Record or Action Candidate |
| Checker result | Evidence or Gate detail |
| Event stream | Trace card, collapsed by default |
| Consequential boundary | Gate card |

Create a visible sub-card only when the loop object works, blocks, fails, repeats, is newly proposed or requires arbitration.

## Relationship with workflow forging

A Workflow Candidate may include a Loop Contract candidate when iteration is useful.

But:

```text
Workflow Candidate proposes execution.
Loop Contract bounds iteration.
Execution runtime executes.
Checker checks declared criteria.
Pantheon governs status and gates.
Human decides consequential effects.
```

Forged does not mean authorized. Loop completed does not mean approved.

## Adapter note

Tool-specific loop mechanics belong in adapters.

Examples:

```text
Revit transaction loops;
file conversion retries;
browser automation retries;
repository patch/test loops;
RAG benchmark loops;
form-field resolution loops.
```

The generic doctrine defines the governance envelope. The adapter defines the runnable mechanics.

## Anti-patterns

| Anti-pattern | Why refused |
|---|---|
| Pantheon loop engine | collapses governance into execution. |
| Hidden retry queue | creates runtime behavior and obscures state. |
| Runtime self-approval | confuses process success with governance approval. |
| Agent decides next goal | creates unscoped intent. |
| Trace treated as Evidence Pack | confuses observation with proof. |
| Loop writes Registre Probatoire state | bypasses governed validation. |
| External action inside retry loop | risks repeated unauthorized effect. |
| Checker and maker collapse into one unreviewable judgment | hides verification weakness. |

## Boundary phrase

```text
A loop is an execution pattern.
Pantheon governs its admissibility, scope, evidence, blockers, gates and status.
The runtime carries the iteration.
The human decides what becomes consequential.
```

The validated remains.
