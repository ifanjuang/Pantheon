# Tripartite Interface Specification

Status: candidate support doctrine — documented non-implemented interface grammar.
Boundary profile: candidate_support_note.

This document defines the operational interface grammar between the exposure surface, the execution runtime, Pantheon governance, and the optional Pantheon MCP policy surface.

It does not implement an API, endpoint, bridge, queue, scheduler, workflow runner, provider router, OpenWebUI extension, Hermes skill, MCP tool, approval engine, memory engine or external action.

Abstract form:

```text
The exposure surface exposes.
The execution runtime executes.
Pantheon governs.
```

## Purpose

The system needs one interface language so OpenWebUI, Hermes and Pantheon do not collapse their responsibilities during real use.

The goal is not to make Pantheon executable. The goal is to make every cross-layer object explicit, status-bearing and auditable.

This specification answers:

```text
What object is passed?
Who produces it?
Who may read it?
What status does it carry?
Can it trigger execution?
Can it leave the professional perimeter?
Can it become memory or proof?
```

## Layers

| Layer | Primary responsibility | Must not become |
|---|---|---|
| Exposure surface | show, select, warn, capture decisions, display gates and candidates | source of truth, runtime, approval engine, memory promoter |
| Execution runtime | run bounded work under a contract and return candidates | governance authority, proof authority, canonical memory authority |
| Pantheon governance | define legitimacy, status, scope, evidence, approval and memory rules | runtime, scheduler, queue, provider router, tool dispatcher |
| Pantheon MCP policy surface | expose doctrine and validation reports as data | host, runtime, connector gateway, approval engine, enforcement proxy by default |
| Human decision plane | accept, refuse, limit, sign or arbitrate | automated side effect |

## Minimal object set

```text
intent_candidate
context_pack
task_contract
policy_decision
governed_execution_handoff
runtime_return
result_candidate
evidence_pack_candidate
memory_or_register_candidate
user_decision_gate
capability_gap
trace_spine
```

All objects are data. No object here is a runtime task, scheduler item, queue message, provider route or automatic approval.

## Trace spine

Every significant object should carry the same trace spine where available:

```yaml
trace_spine:
  conversation_id:
  user_request_id:
  intent_candidate_id:
  task_contract_id:
  context_pack_id:
  policy_decision_id:
  handoff_id:
  runtime_run_id:
  result_candidate_id:
  evidence_pack_candidate_id:
  decision_gate_id:
  final_decision_ref:
```

The trace spine links surfaces. It does not validate anything by itself.

## 1. `intent_candidate`

Produced by: exposure surface, execution runtime or user-facing assistant.

Read by: Pantheon policy check, Hermes preflight, exposure surface.

Purpose: capture what the user appears to ask before it becomes a governed task.

```yaml
intent_candidate:
  intent_candidate_id:
  source_surface: openwebui | hermes | other
  user_request:
  project_ref:
  dossier_ref:
  attached_sources: []
  requested_effect_hint: read_only | candidate_state | internal_state_change | external_effect | canonical_effect | unknown
  proposed_scope:
  uncertainty:
  trace_spine:
```

Rules:

```text
Intent Candidate != Task Contract.
Intent Candidate != authorization.
Intent Candidate may be wrong.
If effect or scope is unclear, the next state is needs_revision or visible gate.
```

## 2. `context_pack`

Produced by: exposure surface or execution runtime.

Read by: Pantheon policy check and Hermes.

Purpose: define the bounded context admitted for a task.

```yaml
context_pack:
  context_pack_id:
  scope:
    project:
    dossier:
    included_sources: []
    excluded_sources: []
  source_inventory:
    present: []
    referenced_but_absent: []
    stale_or_unverified: []
  minimization:
    applied: true | false
    omitted_sensitive_material: []
  contradictions: []
  open_questions: []
  trace_spine:
```

Rules:

```text
Context Pack != proof.
Retrieved context != admitted context until inventoried.
Cross-project material requires explicit scope.
```

## 3. `task_contract`

Produced by: Pantheon-guided drafting, Hermes under policy guidance, or a human reviewer.

Read by: Hermes, MCP policy checks, exposure surface.

Purpose: define the governed boundary of delegated execution.

```yaml
task_contract:
  task_contract_id:
  intent:
  scope:
  roles:
  rites:
  constraints:
  approvals:
  expected_evidence:
  allowed_outputs:
  forbidden_outputs:
  memory_or_register_rules:
  risk_notes:
  trace_spine:
```

Rules:

```text
Task Contract governs execution without owning execution.
Task Contract != workflow graph.
Task Contract != runtime queue.
Task Contract != automatic rite launcher.
```

## 4. `policy_decision`

Produced by: Pantheon policy logic, read-only MCP policy surface, or human governance review.

Read by: exposure surface and Hermes.

Purpose: return the governance posture as data.

```yaml
policy_decision:
  policy_decision_id:
  decision: allow | allow_with_gate | block | needs_revision | needs_evidence | not_applicable
  status: candidate | reviewed | accepted | refused | to_arbitrate
  reasons: []
  required_approval:
  required_user_gate:
  required_evidence: []
  required_context_changes: []
  allowed_effects: []
  forbidden_actions: []
  next_step:
  trace_spine:
```

Rules:

```text
allow != approved.
allow != true.
allow only means the runtime may proceed under the stated contract.
block must return a visible reason and safe next path.
```

## 5. `governed_execution_handoff`

Produced by: exposure surface or bridge adapter after a valid policy posture exists.

Read by: Hermes.

Purpose: provide Hermes with a legitimacy package, not a hidden workflow.

```yaml
governed_execution_handoff:
  handoff_id:
  linked_task_contract:
  linked_context_pack:
  linked_policy_decision:
  target_runtime: execution_runtime
  requested_effect: read_only | candidate_state | internal_state_change | external_effect | canonical_effect
  action_family:
  target:
    kind:
    ref:
  allowed_inputs: []
  forbidden_effects: []
  expected_result_candidate:
  expected_evidence_pack_candidate:
  idempotency_key:
  trace_spine:
```

Rules:

```text
Handoff != scheduler item.
Handoff != provider route.
Handoff != queue message.
If the requested effect is canonical_effect, runtime execution is refused.
```

## 6. `runtime_return`

Produced by: Hermes or another execution runtime.

Read by: OpenWebUI, Pantheon policy checks, human reviewer.

Purpose: separate transport, runtime and governance statuses.

```yaml
runtime_return:
  handoff_delivery_status: not_sent | sent | refused | failed | timeout
  runtime_task_status: not_started | success | partial | failed | blocked | unknown
  governance_result_status: candidate | to_verify | approved | rejected | blocked
  result_candidate_ref:
  evidence_pack_candidate_ref:
  memory_or_register_candidate_ref:
  limits_and_uncertainties: []
  trace_spine:
```

Rules:

```text
Runtime success != governance approval.
Transport success != task success.
Task success != proof.
```

## 7. `result_candidate`

Produced by: Hermes.

Read by: exposure surface, Pantheon review, human reviewer.

Purpose: hold the output without implying validation.

```yaml
result_candidate:
  result_candidate_id:
  task_contract_id:
  output_type:
  status: draft | candidate | to_verify | blocked
  content_ref:
  claims: []
  assumptions: []
  limits: []
  forbidden_interpretations: []
  trace_spine:
```

Rules:

```text
Result Candidate != deliverable.
Result Candidate may support a gate.
Result Candidate must not leave the perimeter as professional position without approval.
```

## 8. `evidence_pack_candidate`

Produced by: Hermes or a validation-only preparation tool.

Read by: Pantheon review, exposure surface, human reviewer.

Purpose: assemble reviewable support without turning it into proof automatically.

```yaml
evidence_pack_candidate:
  evidence_pack_candidate_id:
  task_contract_id:
  sources_used: []
  sources_missing: []
  assumptions: []
  contradictions: []
  risks: []
  limits: []
  artifacts: []
  unresolved_questions: []
  review_required_by: []
  trace_spine:
```

Rules:

```text
Evidence Pack Candidate != proof by itself.
Trace != Evidence Pack.
Retrieved excerpt != evidence until admitted and scoped.
```

## 9. `memory_or_register_candidate`

Produced by: Hermes or a review step.

Read by: Pantheon governance and the human reviewer.

Purpose: propose something that may be retained, scoped or rejected.

```yaml
memory_or_register_candidate:
  candidate_id:
  candidate_type: runtime_memory_candidate | registre_probatoire_candidate | evidence_log_candidate
  claim:
  source_refs: []
  evidence_pack_candidate_ref:
  scope:
  expiry:
  approval_required:
  forbidden_to_generalize: true
  trace_spine:
```

Rules:

```text
Runtime memory belongs to the runtime.
Pantheon governs Registre Probatoire status, evidence linkage, scope and approval.
Memory candidate != canonical memory.
Register candidate != Registre Probatoire entry.
```

## 10. `user_decision_gate`

Produced by: exposure surface from a policy decision or Pantheon gate.

Read by: human.

Purpose: make the next consequential choice explicit.

```yaml
user_decision_gate:
  gate_id:
  gate_type: scope | evidence | approval | external_action | memory_or_register | arbitration
  decision_required:
  options:
    - allow_read_only
    - create_draft_only
    - request_more_evidence
    - limit_to_active_project
    - refuse_external_action
    - keep_candidate
    - escalate_to_arbitration
  default_safe_option:
  consequences:
  trace_spine:
```

Rules:

```text
A gate captures a decision.
A gate is not the decision-maker.
Silence never means approval.
```

## 11. `capability_gap`

Produced by: any layer when safe execution cannot be framed.

Read by: exposure surface, operator, human reviewer.

Purpose: prevent improvisation.

```yaml
capability_gap:
  gap_id:
  missing:
  needed_for:
  blocked_effect:
  consequence_if_ignored:
  safe_fallback:
  required_human_or_admin_action:
  status: blocked | degraded | to_configure
  trace_spine:
```

Rules:

```text
Capability Gap is a safe stop condition.
It is not failure if it prevents unauthorized action.
```

## Interface flows

### Read-only review

```text
User request
-> intent_candidate
-> context_pack
-> task_contract
-> policy_decision: allow
-> governed_execution_handoff: read_only
-> Hermes execution
-> result_candidate + evidence_pack_candidate
-> OpenWebUI display
-> human review
```

### Draft-only preparation

```text
User request
-> intent_candidate
-> policy_decision: allow_with_gate
-> user_decision_gate: create draft only
-> Hermes prepares candidate
-> result_candidate status: draft
-> no external send
```

### External action request

```text
User request to send / publish / file / notify
-> intent_candidate requested_effect: external_effect
-> task_contract required
-> evidence expectation required
-> approval required
-> user_decision_gate required
-> Hermes may act only after explicit approval and idempotency key
```

### Canonical effect request

```text
User request to approve / canonize / promote / validate final truth
-> requested_effect: canonical_effect
-> runtime execution blocked
-> governed validation path only
-> human decision required
```

## Mandatory UI distinctions

OpenWebUI or any exposure surface should display the following separately:

```text
scope
requested effect
approval level
evidence expectation
candidate status
runtime status
governance status
memory / register behavior
human decision required
```

Forbidden display collapse:

```text
runtime success = approval
retrieval = proof
candidate = deliverable
memory stored by runtime = Pantheon memory
MCP tool listed = authorized tool
health check green = safe to use
```

## Adapter note

Tool-specific wiring belongs outside Pantheon doctrine or in adapter documents. This specification defines the port. OpenWebUI, Hermes and MCP adapters plug into it without redefining the rules.

## Status summary

```text
Accepted: one interface vocabulary for the three layers.
Refused: Pantheon as runtime or hidden orchestrator.
To verify: exact adapter mapping for OpenWebUI v0.10.0 and Hermes v0.17.0.
To arbitrate: whether this document should become active support doctrine after review.
Repo state: documented non-implemented.
```