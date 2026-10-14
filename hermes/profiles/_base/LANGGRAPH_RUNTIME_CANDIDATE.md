# LangGraph Runtime Candidate for Hermes

Status: Hermes runtime candidate template — not installed, not implemented.

This document defines when LangGraph may be considered as an optional execution backend behind Hermes Agent.

It does not install or configure LangGraph, create a Pantheon runtime, authorize workflows, select a provider or grant any client execution authority.

```text
Hermes clients handle runtime interaction.
Hermes Agent executes externally under Task Contract.
Pantheon Cockpit may expose governed status, gates and decisions.
Pantheon Next governs consequential status.
```

## Purpose

LangGraph is a candidate runtime pattern for Hermes when execution needs are too stateful, long-running, interruptible or checkpoint-heavy for a simple linear execution profile.

It remains external and replaceable. Pantheon defines governance constraints; Hermes Agent may use an admitted runtime implementation inside the Task Contract. A compatible Hermes client may expose runtime controls, while Pantheon Cockpit may project governed status and decision gates.

```text
runtime backend selected != authority transfer
client selected != governance authority
runtime success != authorization
projection != persistence
```

## Candidate identity

```yaml
runtime_candidate: langgraph
owner_layer: hermes
status: not_installed_candidate
pantheon_role: none
canonical_authority: none
governed_by:
  - docs/governance/TASK_CONTRACTS.md
  - docs/governance/EVIDENCE_PACK.md
  - docs/governance/APPROVALS.md
  - docs/governance/MEMORY.md
  - docs/governance/SCOPE_ISOLATION.md
  - docs/governance/HERMES_INTEGRATION.md
  - docs/governance/EXTERNAL_TOOLS_POLICY.md
```

## Use when

Consider LangGraph only when a Hermes task demonstrably requires one or more of:

- long-running workflow;
- checkpoint and resume;
- human interrupt during execution;
- multi-step Evidence preparation;
- bounded tool sequence with recoverable state;
- repository analysis with restart or recovery;
- ingestion/retrieval processing with quality gates;
- patch-candidate workflow with tests and controlled retry;
- multi-phase review where intermediate runtime state matters.

Do not add LangGraph merely because graph execution is available. Prefer the simpler existing Hermes execution path when it satisfies the task.

## Do not use when

Do not use LangGraph for:

- simple chat, rewrite, translation or summary;
- one-step file edits or small source checks;
- tasks without a Task Contract or bounded scope;
- work where a linear Hermes path is sufficient;
- work where persisted runtime state creates more governance risk than demonstrated value.

## Required inputs

A LangGraph-backed Hermes run must receive an explicit bounded frame:

```yaml
required_inputs:
  task_contract: required
  context_pack: required
  approval_ceiling: required
  allowed_tools: required
  forbidden_tools: required
  memory_rule: required
  evidence_requirements: required
  output_contract: required
  user_decision_gate_policy: required
```

## Forbidden inputs

A LangGraph-backed Hermes run must never receive:

- raw client database access;
- Pantheon doctrine as mutable runtime workspace;
- authority to promote memory;
- authority to approve its own output.

The following inputs are also forbidden unless explicitly admitted by the applicable Task Contract and policy owner:

- unscoped client/session context or client-internal knowledge stores;
- global vector/retrieval-store access;
- raw global memory;
- unrelated project context;
- protected files outside authorization;
- production credentials;
- write-capable external tools without the required authorization.

## Required outputs

A LangGraph-backed Hermes run must return:

```yaml
required_outputs:
  output_candidate: required
  run_trace_summary: required
  evidence_notes: required
  assumptions: required
  risks: required
  unresolved_interrupts: required
  approval_implications: required
  memory_candidates_if_any: required
  capability_gaps_if_any: required
  next_action_recommendation: required
```

A raw trace dump is not a substitute for an Evidence Pack or Evidence Pack Candidate.

## Runtime state rule

LangGraph state is runtime state. It is not:

- a Registre Probatoire entry;
- Evidence;
- approval;
- doctrine;
- source truth;
- user decision;
- Pantheon Role Signal;
- Governance College deliberation.

If runtime state contains a potentially durable claim, it may only support a Register Candidate proposal through the existing Evidence/retention path.

## Interrupt rule

A LangGraph interrupt may request human input. It does not grant approval.

A compatible Hermes runtime client may expose an interrupt and runtime controls such as pause/resume/cancel. When the interrupt reaches a consequential governance boundary, Pantheon Cockpit or another existing governed projection may expose the User Decision Gate.

Every consequential interrupt should identify:

- what is blocked;
- why human input is required;
- Evidence/candidate material visible so far;
- available options;
- material risk of each option;
- effect on output, memory, approval and delivery.

If the issue is a governed conflict, escalate to the existing User Decision Gate rather than resolving it inside the graph.

## Checkpoint rule

A checkpoint preserves external execution continuity. It does not validate the work.

A resumed run must preserve:

- original Task Contract identity;
- context scope;
- approval ceiling;
- allowed tools;
- memory rule;
- Evidence requirements;
- unresolved tensions.

If those constraints materially change, revise or replace the Task Contract through its existing owner path.

## Tool rule

Tools used by a LangGraph-backed Hermes run remain governed by `EXTERNAL_TOOLS_POLICY.md` and the Task Contract.

Allowed tool access must be explicit. Write-capable effects require their applicable authorization. A graph edge cannot grant tool authority by itself.

## Memory rule

LangGraph memory or checkpoint state must not be treated as Pantheon memory.

Allowed runtime uses may include:

```text
runtime state summary
Register Candidate proposal material
source freshness note
scope-limited recall inside the current run
```

Forbidden:

```text
automatic Registre Probatoire entry
cross-project memory reuse without scope admission
silent durable user-preference storage
auto-promotion from repeated state
graph memory as source of truth
```

## Evidence rule

Run traces may support Evidence preparation. They are not Evidence by themselves.

A useful return maps:

```text
claim -> governed source or observed action -> output effect -> limitation -> risk
```

Runtime logs should be reduced to governance-relevant attributable observations rather than treated as proof.

## Runtime interaction and governed projection

A compatible Hermes client may expose runtime-facing information such as:

- run status;
- current-step summary;
- interrupt reason;
- pause/resume/cancel controls;
- unresolved runtime risks.

Pantheon Cockpit or existing Card projection owners may expose governed information such as:

- Evidence/candidate status;
- approval gaps;
- User Decision Gates;
- governed blockers and review status.

Neither surface may:

- host LangGraph as Pantheon core;
- approve an output because it is displayed;
- convert runtime/checkpoint state into governed memory;
- grant unbounded source or Knowledge access;
- hide unresolved risk behind progress UI;
- treat projected state as persistence.

## Anti-patterns

Reject:

- central LangGraph runtime for Pantheon;
- LangGraph as Governance College;
- graph nodes as Pantheon Roles;
- graph completion as approval;
- checkpoint as governed memory;
- run trace as Evidence Pack;
- a client-side hidden graph runner treated as Pantheon authority;
- background graph jobs without Task Contract;
- cron/scheduler ownership inside Pantheon;
- graph-managed provider routing;
- graph-managed skill installation;
- graph-managed memory promotion.

## Minimal sandbox test

A first Hermes sandbox test, if approved, should use:

```text
fictional task
read-only or low-risk tools
no production credentials
no protected files
no governed memory writes
no automatic external effects
small bounded graph
explicit interrupt
Evidence Pack Candidate return
```

A successful sandbox run remains runtime evidence about the experiment; it does not establish adoption, professional correctness or authorization for broader use.

## Final rule

```text
Hermes may use LangGraph when it demonstrably improves bounded execution.
LangGraph remains replaceable and never becomes Pantheon authority.
```
