# Capability Placement

Status: active support doctrine — capability placement, future integration boundaries and non-runtime architecture.
Boundary profile: active_support_doctrine.

This document defines where capabilities should live when Pantheon Next uses replaceable exposure clients, Hermes Agent, Langflow, LangGraph, Langfuse, GraphRAG or another external system.

It does not implement an integration, install a dependency or create runtime behavior.

It does not create a bridge, endpoint, queue, scheduler, provider router, plugin registry, MCP runtime, observability backend, GraphRAG runtime, LangGraph runtime, Langflow runtime, client plugin or Hermes skill.

```text
Replaceable clients expose runtime interaction.
Pantheon Cockpit/Card surfaces project governed state.
Hermes Agent executes.
Pantheon Next governs.
```

## Core rule

```text
A capability belongs where its primary effect belongs.
```

- governance effect -> Pantheon doctrine;
- governed user visibility or decision capture -> Pantheon Cockpit/Card projection;
- runtime conversation/session/control interaction -> a replaceable compatible client;
- external execution -> Hermes or another external runtime under Task Contract;
- deterministic preparation -> Langflow candidate;
- durable interruptible execution -> LangGraph candidate behind Hermes or a governed bridge;
- trace observation -> Langfuse or another observability layer;
- relationship discovery or provenance linking -> GraphRAG / provenance graph candidate.

If a capability changes legitimacy, memory, approval, scope, doctrine or external effect, Pantheon governance remains the authority.

## Kernel invariants

The following rules belong to the Pantheon kernel because they are tool-agnostic. They remain true regardless of the current exposure surface, execution runtime, observability tool, connector gateway or graph layer.

```text
1. Capability installed does not mean capability approved.
2. Runtime completion does not mean governance approval.
3. Transport success does not mean task success.
4. Task success does not mean truth, proof, memory or professional validation.
5. Retrieval does not mean evidence.
6. Trace does not mean Evidence Pack.
7. Runtime state does not mean Pantheon memory.
8. Profile identity does not mean Pantheon Role authority.
9. Scheduled or background execution does not change the status of the output.
10. External communication channel proximity does not lower approval requirements.
11. Canonical effects are never runtime work.
12. Ambiguity stops at a visible gate; it must not be resolved by runtime guesswork.
13. A self-generated intention does not mean a scoped task.
14. An Intent Candidate does not authorize memory, truth, approval or external action.
```

These invariants may be projected into adapters, profiles, skills, dashboards or connectors. They must not be redefined there.

Intent generation is a candidate-producing effect. A runtime, skill, workflow or module may surface an `Intent Candidate`, but that candidate remains inadmissible for execution until a Task Contract, scope, evidence expectation and approval path exist where required.

Related support review:

```text
AUTOTELIC_AGENCY_GOVERNANCE_REVIEW.md
```

## Kernel versus adapter decision

When a new capability or tool version appears, classify the change before adapting it.

```text
Can the rule be stated without naming the tool?
```

- Yes — it may belong to the Pantheon kernel.
- No — it belongs to a binding, adapter, integration note, profile, skill, connector configuration or reference review.

Kernel changes are acceptable during controlled bootstrap when they clarify durable governance. After bootstrap, kernel changes require stricter doctrine review.

Default review outcome:

| Change | Default placement |
|---|---|
| new effect class, new status distinction, new approval or memory invariant | kernel candidate |
| new runtime feature, profile, skill, channel, dashboard field or tool option | adapter |
| new executable configuration | outside Pantheon |
| new proof or approval implication | kernel review before adapter use |
| new autonomous goal-generation or self-directed workflow behavior | kernel review before runtime use |

## Placement by layer

### Pantheon Next

Pantheon owns doctrine, role definitions, Task Contract rules, Context Pack rules, Evidence Pack rules, approval rules, memory promotion rules, scope isolation rules, external tools policy, placement rules, prompt placement rules, integration boundaries, reference reviews, rejected patterns and persistent tensions.

Pantheon must not own an agent runtime, tool runtime, workflow runtime, provider router, scheduler, queue, message bus, plugin manager, skill installer, MCP runtime, observability backend, GraphRAG runtime, LangGraph central runtime, Langflow runtime, client plugin execution or Hermes internal runtime state.

### Pantheon Cockpit and replaceable exposure clients

Pantheon Cockpit/Card owners define governed presentation and decision-capture semantics. Compatible clients may expose runtime conversation, sessions and controls, but client selection does not transfer governance authority.

Allowed exposure posture:

```text
show
select
label
warn
collect decision
request revision
request more evidence
open User Decision Gate
display Evidence Pack
display Task Contract
display candidate status
display scope warning
request Hermes execution under contract
```

An exposure client must not become a Registre Probatoire entry, source of truth, governance authority, runtime authorization source, unrestricted knowledge gateway, free plugin manager, provider router, scheduler, hidden workflow runner, automatic approval surface or automatic memory promoter.

Client-hosted extensions are capability surfaces only. They are not authorized merely because a client can host them.

### Pantheon Bridge candidate

A future bridge may adapt a governed request into bounded external execution. It may check that Task Contract, Context Pack, approval ceiling, memory rule and evidence expectation exist before dispatch.

The bridge is a boundary adapter. It must not become agent runtime, workflow runtime, tool runtime, provider router, queue, scheduler, approval engine, memory promotion engine or hidden orchestrator.

### Governed execution handoff

A governed execution handoff is the boundary object a bridge or exposure surface may prepare before asking an execution runtime to act.

It is not a queue item, worker assignment, scheduler record, provider route, workflow state or executable instruction owned by Pantheon. It is a legitimacy package: the runtime may read it; Pantheon does not run it.

Minimum shape:

```text
governed_execution_handoff:
  handoff_id:
  linked_task_contract:
  linked_context_pack:
  decision_gate:
  approval_ref:
  scope:
  target_runtime: execution_runtime
  requested_effect: read_only | internal_state_change | external_effect | canonical_effect
  action_family:
  target:
    kind:
    ref:
  allowed_inputs:
  forbidden_effects:
  expected_result_candidate:
  expected_evidence_pack_candidate:
  outcome_observation_expected: true
  idempotency_key:
  trace_refs:
```

The handoff is valid only when:

```text
1. the linked Task Contract identifies scope, allowed outputs, forbidden outputs, register rules and approval ceiling;
2. the linked Context Pack exists, or the task explicitly records that no Context Pack is required;
3. the requested effect is classified before dispatch;
4. expected Result Candidate and Evidence Pack Candidate outputs are named;
5. any external effect has an explicit approval path;
6. any canonical effect is refused as runtime work and routed to the governed validation path;
7. an idempotency key and trace references exist for every non-read-only effect.
```

Effect classes:

| Requested effect | Meaning | Pantheon rule |
|---|---|---|
| `read_only` | observe, extract, compare, search, summarize | may proceed when the Task Contract allows it and provenance is preserved |
| `internal_state_change` | create a draft, candidate artifact, candidate status or review item | allowed only as candidate state; not validation |
| `external_effect` | send, publish, file, notify, modify an external system or commit to a third party | requires explicit approval and the User Decision Gate where relevant |
| `canonical_effect` | create or modify doctrine, approval status, a Registre Probatoire entry or another validated state | never executable by the runtime; requires the governed validation path |

The return path must not collapse transport success, task success and governance status. A valid runtime return separates at least:

```text
handoff_delivery_status: not_sent | sent | refused | failed | timeout
runtime_task_status: not_started | success | partial | failed | blocked | unknown
governance_result_status: candidate | to_verify | approved | rejected | blocked
```

A successful runtime response is not proof, approval, professional validation, canonization, transmission authority or memory promotion. It is reviewable evidence and candidate output.

If a bridge or surface cannot produce a valid handoff, the safe result is a visible Capability Gap, not an improvised execution.

#### Handoff preflight outcomes

Before any runtime receives the handoff, the adapter or surface should classify the boundary result as data:

| Preflight outcome | Meaning | Next path |
|---|---|---|
| `allow_read_only` | the requested act is observation or preparation with no state change | dispatch may proceed under the Task Contract |
| `allow_candidate_only` | the requested act creates a draft, note, patch candidate, Evidence Pack Candidate or Register Candidate | dispatch may proceed, but output remains candidate |
| `needs_approval` | the requested act may create an external effect | open or reference the User Decision Gate before dispatch |
| `pending_confirmation` | target, recipient, scope, source version, approval or effect class is ambiguous | ask for or surface confirmation; do not guess |
| `capability_gap` | the runtime, connector, source, permission or proof requirement is missing | return a visible gap object |
| `block` | the requested act would be canonical, forbidden, out of scope or unapproved | refuse and route to revision |

`pending_confirmation` is not failure. It is a safe stop condition. It prevents the system from turning ambiguous user language into unauthorized action.

#### Capability Gap shape

A Capability Gap records that work cannot be safely handed off. It should be explicit enough for a human or administrator to fix the missing condition without pretending the task succeeded.

```text
capability_gap:
  gap_id:
  missing:
  needed_for:
  blocked_effect:
  consequence_if_ignored:
  safe_fallback:
  required_human_or_admin_action:
  status: blocked | degraded | to_configure
  trace_refs:
```

Typical gaps:

```text
source_absent
recipient_unconfirmed
approval_missing
runtime_unavailable
connector_not_authorized
write_scope_forbidden
idempotency_key_missing
evidence_expectation_unmet
adapter_version_unreviewed
background_result_unlinked
channel_effect_unclassified
automation_scope_expired
memory_candidate_unscoped
```

A gap is preferable to a fabricated result, a silent downgrade or a partial external action.

#### Idempotency discipline

Every non-read-only handoff needs an idempotency key. The key does not make an action safe; it prevents accidental repetition when a user, bridge or runtime retries.

```text
idempotency_key = task_contract_id + decision_gate_id + target_ref + requested_effect + approved_revision
```

Without such a key, external effects should remain blocked or draft-only. This protects against duplicate emails, duplicate Notion cards, duplicate comments, repeated filings, repeated patch application and repeated Register Candidate creation.

#### Outcome Observation Candidate

The runtime return should include a short Outcome Observation Candidate. This is not a runtime log. It is a governance-readable statement of what changed and what did not.

```text
outcome_observation_candidate:
  acted: true | false
  external_effect: true | false
  canonical_effect: false
  changed_objects:
  unchanged_objects:
  produced_candidates:
  blocked_items:
  follow_up_needed:
  approval_still_required:
  evidence_refs:
```

The key field is often `unchanged_objects`. For example: draft created, email not sent; patch candidate produced, repository not modified; Register Candidate proposed, Registre Probatoire unchanged.

#### Intent Candidate

An Intent Candidate records a runtime, skill, module or workflow proposing what should happen next. It is not a Task Contract and not authorization.

Minimum candidate shape, not an approved executable schema:

```text
intent_candidate:
  id:
  origin_runtime:
  origin_module:
  observed_context:
  proposed_intention:
  proposed_task:
  target_scope:
  affected_truth_claims:
  affected_memory:
  possible_external_effect:
  possible_canonical_effect:
  evidence_required:
  approval_required:
  admissibility_status: candidate | to_verify | needs_approval | rejected | blocked
  decision_owner:
  created_at:
  resolved_at:
  trace_refs:
```

Before it may become a scoped task, the candidate must pass an admissibility review. If it affects truth, memory, scope, approval, doctrine, a Registre Probatoire entry, professional responsibility or external action, it must stop at a visible gate.

### Hermes Agent

Hermes owns external execution. Hermes may host profiles, skills, tools, toolsets, workers, controlled terminal operations, repository read and patch candidates, source audit work, file conversion work, document extraction work, browser or search work, Evidence Pack candidate preparation, Register Candidate proposal and Capability Gap signaling.

Hermes may also surface Intent Candidates when it detects a possible next step, missing skill, workflow branch or capability gap. Such candidates are not task authorization.

Hermes must return candidates. Hermes must not approve, canonize, promote memory, mutate doctrine, merge code directly or bypass approvals.

### Langflow candidate

Langflow may support deterministic preparation: source extraction, redaction preparation, Context Pack skeletons, Evidence Pack skeletons, document chunking review, format normalization and repeatable preprocessing.

Langflow must not grant approval, own a Registre Probatoire entry, execute Pantheon Roles, run the Governance College, hide workflow authority or resolve dossiers autonomously.

### LangGraph runtime candidate

LangGraph may be considered only for external long-running, interruptible or checkpoint-heavy execution behind Hermes or a governed bridge.

LangGraph state is Runtime State. It is not Evidence Pack, a Registre Probatoire entry, approval or doctrine.

### Langfuse candidate

Langfuse may observe model, tool and execution traces. It may record metadata useful for audit support. It must not become Evidence Pack, a Registre Probatoire entry, approval record, doctrine source or runtime authority.

### GraphRAG or provenance graph candidate

A graph layer may support relationship discovery, provenance linking and contradiction review. It may link sources, claims, chunks, entities, Task Contracts, Context Packs, Evidence Items, Evidence Packs, Output Candidates, Register Candidates, a Registre Probatoire entry, approvals, contradictions and run references.

The graph must not decide truth. Connectivity is not approval. Retrieval from a graph is not evidence until selected and represented in an Evidence Pack.

## Placement matrix

| Capability | Pantheon | Exposure client / Cockpit | Hermes | Langflow | LangGraph | Langfuse | Graph / GraphRAG |
|---|---|---|---|---|---|---|---|
| Doctrine | owns | displays governed excerpts only | receives constraints | receives constraints | receives constraints | observes refs | links refs |
| Task Contract | owns | displays / captures candidate | consumes | consumes | consumes | traces id | links id |
| Context Pack | owns rules | selects / displays governed projection | consumes | may prepare candidate | consumes | traces id | links scope |
| Governed execution handoff | owns rules | prepares / displays / captures approval under governed surface | consumes under contract | no | may consume only behind runtime | observes refs | links refs |
| Intent Candidate | owns admissibility rules | displays / captures decision | may propose | may propose candidate | may pause | observes refs | links intent |
| Evidence Pack | owns rules | displays | produces candidate | may skeletonize | may support long run | observes traces | links evidence |
| Approval | owns rules | captures explicit action without granting authority itself | reports need | never grants | may interrupt | observes | links decision |
| User Decision Gate | owns format | exposes | reports conflict | never resolves | may pause before gate | observes | links conflict |
| Register Candidate | owns rules | displays / review surface | may propose | may propose candidate | may pause | observes | links claim |
| a Registre Probatoire entry | owns | displays scoped excerpt | consumes approved excerpt | never owns | never owns | observes ref | may link approved item |
| Source audit | defines rules | displays result | executes | may preprocess | only if long | observes | enriches provenance |
| Repository patch candidate | defines rules | requests / displays | executes candidate | not default | if long / interruptible | observes | links change |
| RAG ingestion candidate | defines boundaries | selects sources through governed projection | executes or delegates | may run deterministic flow | if long | observes | indexes / links |
| UI action | defines legitimacy | hosts thin projection/action request | receives request | no | no | observes | no |
| Workflow long run | defines boundary | displays status | executes | may be subflow | checkpoint runtime | observes | links milestones |

## Rejected collapses

```text
client extension = Pantheon runtime
client knowledge surface = Registre Probatoire entry
client selection = governance authority
Hermes profile = Pantheon Role authority
Hermes completion = approval
Langflow flow = governed decision
LangGraph checkpoint = memory
Langfuse trace = Evidence Pack
GraphRAG relation = proof
MCP availability = tool authorization
plugin installed = capability approved
operations file = governing spec
handoff delivered = task validated
runtime success = governance approval
pending confirmation = failure
capability gap = permission to improvise
background task completed = approved output
scheduled run = renewed approval
messaging-channel yes = valid approval by itself
self-generated intention = scoped task
Intent Candidate = authorization
```

## Operations boundary

```text
Spec first.
Operations second.
Execution elsewhere.
```

No file under `operations/` may be created or modified before a governing documentation spec has been explicitly validated.

The governing spec must define the scope, status, authority, required evidence, approval conditions, external-action limits, human responsibility and exit criteria for the operational procedure.

`operations/` may only translate validated governance into procedural guidance. It must not invent doctrine, promote candidates, define runtime behavior, bypass approval, create hidden workflow authority or become a scheduler, queue, execution engine, approval engine or memory mechanism.

Until a governing spec is validated, any proposed `operations/` content remains a candidate discussion item outside `operations/`.

## Architectural pattern references

External architectural pattern catalogues may be used as vocabulary aids, not as Pantheon doctrine.

They can help name architectural forces such as orchestration, microkernel, plugin systems, middleware, pipelines, gateways, shared repositories, event flows, observability layers or provenance graphs.

Naming a pattern does not authorize Pantheon to implement it.

If a pattern implies execution, routing, scheduling, queueing, plugin loading, durable work, automatic approval, automatic memory promotion or external side effects, it belongs outside Pantheon.

Pantheon may govern the boundary of such a pattern through Task Contracts, manifests, roles, evidence, statuses, approvals, memory rules and action boundaries.

Reference catalogues such as architectural metapatterns are non-normative. They help identify placement risks; they do not override Pantheon governance documents.

## Evolution phases

### Phase 1 — documentation and templates

Allowed now: placement doctrine, prompt placement doctrine, bridge contract doctrine, non-executable templates and AI logs.

Not allowed by this phase: runtime bridge, executable client extension, Hermes skill installation, Langflow deployment, LangGraph runtime, Docker or operations changes.

### Phase 2 — thin exposure to Hermes

Future candidate: a replaceable thin client action or Pantheon Cockpit request surface, Pantheon Bridge candidate, Hermes profile and skill under Task Contract, Evidence Pack Candidate return and User Decision Gate display.

### Phase 3 — external preparation and observability

Future candidate: Langflow headless preparation flows, Langfuse trace metadata, read-only provenance graph and Hermes skill candidates for source audit and evidence building.

### Phase 4 — durable interruptible external execution

Future candidate: LangGraph behind Hermes or bridge, human interrupt exposure through a replaceable client or Pantheon Cockpit, checkpoint / resume under unchanged Task Contract and Evidence Pack Candidate return.

## Final rule

```text
Pantheon does not own the engines.
Pantheon owns the rules that decide what an engine may do,
what its output is worth,
and what may remain.
```
