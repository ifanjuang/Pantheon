# Evidence Topology

Status: active doctrine — reasoning-topology selection and proof-chain preservation.
Boundary profile: active_governance_doctrine.

Evidence Topology defines how Pantheon selects and records the smallest reasoning/execution topology that preserves a reviewable proof chain.

It does not create a runtime, dispatcher, scheduler, queue, swarm controller, graph engine, provider router, agent team, approval engine or memory engine.

```text
Hermes clients handle runtime interaction.
Hermes Agent executes externally under Task Contract.
Pantheon Cockpit may expose governed topology, Evidence and decision state.
Pantheon Next governs consequential status.
The human decides where a gate requires it.
```

## Core rule

```text
The unit of reasoning is not the agent.
The unit of reasoning is the proof chain.
```

Choose topology from the shape of the Evidence problem, not from a preference for single-agent, multi-agent, graph or swarm architectures.

```text
more workers != more truth
runtime topology != governance authority
worker output != conclusion
handoff != approval
runtime state != Pantheon memory
projection != persistence
```

## Current machine contract

Evidence Topology is no longer only a schema proposal. The current repository carries optional topology metadata across three machine owners:

- `schemas/workflow_manifest.schema.yaml` — workflow-level `reasoning_topology_requirements`, `evidence_item_requirements` and `handoff_artifact_requirements`;
- `schemas/task_contract.schema.yaml` — task-level `reasoning_topology`;
- `schemas/evidence_pack.schema.yaml` — result/review-level `evidence_items`, `handoff_artifacts` and `reasoning_topology_record`.

All three schemas explicitly keep topology non-runtime through `x-boundary.topology_dispatch: false`. The Workflow Manifest constrains which topology/evidence/handoff policies a repeatable governed workflow permits; the Task Contract declares the bounded topology for one task; the Evidence Pack records what topology and review material were actually used.

The schemas are authoritative for machine-readable field shapes and enums. This document owns governance meaning and selection discipline.

## Supported topology values

The current Workflow Manifest, Task Contract and Evidence Pack schemas share these topology values:

```text
single_primary_reasoning_context
fanout_extract_then_single_synthesis
parallel_independent_workers
router
sequential_handoff
persistent_role_team_handoff
bounded_hermes_swarm
```

These values are governance metadata. They do not dispatch workers or select a runtime backend.

## Selection discipline

### `single_primary_reasoning_context`

Use when the decisive inference depends on connecting material across sources and fragmentation would weaken the proof chain.

Typical shape:

```text
source A + source B + source C
-> one bounded synthesis context
-> reviewed candidate
```

Prefer this when evidence relationships, contradictions, sequence or scope must be understood together.

### `fanout_extract_then_single_synthesis`

Use when many sources can be inspected independently but final reasoning must compare them in one context.

```text
bounded extractors
-> source-linked Evidence Items
-> one synthesis context
-> reviewed candidate
```

Workers extract; they do not produce final authority-bearing conclusions.

### `parallel_independent_workers`

Use only when tasks are genuinely independent and no hidden cross-source inference is needed.

Parallelism is an execution-efficiency choice, not a reliability claim.

### `router`

Use when the first bounded problem is classification or routing.

A router may classify candidate destination or method. It does not decide truth, approval or professional correctness.

### `sequential_handoff`

Use when each stage produces a bounded artifact that the next stage can review.

A consequential handoff requires an attributable artifact/Evidence boundary, not team chatter or an opaque prose summary.

### `persistent_role_team_handoff`

Use when stable execution lanes own distinct artifacts or stages and continuity is materially useful.

Persistent runtime roles remain execution constructs. They are not Pantheon Roles and their runtime memory is not governed memory.

### `bounded_hermes_swarm`

Use only when distributed execution capacity is demonstrably useful and the Task Contract keeps scope, tools, Evidence requirements and approval gaps explicit.

```text
swarm may multiply hands
swarm must not multiply authority
```

## Default decision rule

When uncertain:

```text
single context for connected inference
fan-out only for bounded extraction
parallel workers only for independent tasks
role-team handoff only for reviewable artifact stages
swarm only for bounded execution capacity
User Decision Gate for unresolved consequential stakes
```

Do not add orchestration merely to anticipate future complexity.

## Workflow Manifest boundary

A repeatable governed workflow may constrain topology through `reasoning_topology_requirements` and may state when structured Evidence Items or Handoff Artifacts are required.

The Workflow Manifest may declare:

- allowed/default/forbidden topology choices;
- topology-selection policy;
- Evidence and handoff policy;
- approval and memory policy;
- required Evidence Item fields/minimums;
- required Handoff Artifact fields/types.

```text
Workflow Manifest requirement != runtime dispatch
workflow default topology != automatic task selection
evidence requirement != Evidence sufficiency
```

A Task Contract still binds the concrete task, and an Evidence Pack still records the resulting review material.

## Evidence Items

`Evidence Item` is an optional structured claim-support object owned machine-readably by `schemas/evidence_pack.schema.yaml`; workflow-level requirements for such items are owned by `schemas/workflow_manifest.schema.yaml`.

A useful item identifies at least:

- the claim;
- source type and exact source reference;
- scope of support;
- confidence/certainty signal;
- limitations and open questions when material.

```text
retrieved material != Evidence Item
Evidence Item != final conclusion
Evidence Item != approval
```

Workers may return Evidence Items to preserve attributable source locality during fan-out or staged execution.

## Handoff Artifacts

`Handoff Artifact` is an optional bounded artifact passed between staged workers/roles. Its result shape is owned by `schemas/evidence_pack.schema.yaml`; workflow-level handoff requirements are owned by `schemas/workflow_manifest.schema.yaml`.

A consequential handoff should preserve:

- from/to execution lane;
- bounded scope;
- artifact reference;
- assumptions/blockers;
- Evidence references;
- explicit approval gap.

```text
handoff artifact != authorization
handoff completed != next action approved
```

## Topology record in Evidence Pack

`reasoning_topology_record` may record:

- selected topology and reason;
- rejected alternatives when relevant;
- worker outputs/Evidence Items used;
- Handoff Artifacts used;
- contradictions preserved;
- unresolved gaps;
- approval and memory impact.

The record exists for accountability. It must not become a hidden chain-of-thought archive or raw runtime trace.

## Task Contract boundary

A non-trivial Evidence-sensitive task may declare topology in `reasoning_topology`.

The Task Contract may specify:

- selected topology;
- human-readable reason;
- handoff policy;
- Evidence policy;
- memory/approval constraints;
- rejected topologies and topology risks when useful.

```text
Task Contract topology = governed execution constraint
Task Contract topology != runtime dispatch instruction
```

A runtime may choose internal operational means only within the admitted Task Contract and applicable capability/tool bindings.

## Hermes execution boundary

Hermes Agent remains the external execution owner.

Permitted bounded patterns can include:

- one worker with admitted tools;
- fan-out extraction returning attributable Evidence Items;
- staged handoff returning Handoff Artifacts;
- bounded distributed execution returning candidate outputs.

Hermes must not:

- treat worker/swarm completion as approval;
- treat runtime/role memory as Pantheon memory;
- silently expand Task Contract scope;
- replace Pantheon Roles with runtime workers;
- hide required Evidence behind summaries;
- bypass User Decision Gates.

## Interaction and governed projection

A compatible Hermes client may show runtime-facing execution information such as active step, worker progress, pause/cancel controls or runtime blockers when supported.

Pantheon Cockpit/Card owners may project governed information such as:

- selected topology and reason;
- Evidence Items and Handoff Artifacts;
- contradictions and Evidence gaps;
- approval gaps;
- blocked handoffs;
- User Decision Gate state.

```text
visible topology != validation
canvas/conversation != Evidence Pack
projected state != persisted governance record
```

No client or projection gains authority from displaying or controlling runtime state.

## Memory boundary

Worker state, role-team continuity, checkpoints, swarm state, repeated observations and topology traces are not governed memory.

A durable claim may become a Register Candidate only through its existing owner path with explicit scope, attributable Evidence, contradictions/limitations and required authorization.

```text
runtime continuity != durable memory
memory != Evidence
Register Candidate != admitted Register record
```

## Scope and tool boundary

Distributed topology does not broaden scope.

If a worker needs material or an effect outside the Task Contract, return a scope/capability gap or revise the contract through the applicable gate.

Tool availability is not tool authorization. Every external tool remains governed by Task Contract, capability admission and `EXTERNAL_TOOLS_POLICY.md`.

## User Decision Gate

Topology selection or a topology change may require a User Decision Gate when it materially changes:

- scope;
- professional/legal risk;
- cost or delay;
- external transmission or mutation;
- memory/retention implication;
- Evidence sufficiency;
- approval ceiling.

The gate exposes the consequential choice; it does not automatically approve it.

## Governance College boundary

Pantheon Roles review tensions, Evidence sufficiency, risk, status and procedure.

Runtime workers collect, extract, check or prepare candidates.

```text
Governance College != multi-agent runtime
Pantheon Role != worker profile
review pressure != execution lane
```

## Red flags

Reject topology designs that rely on:

```text
multi-agent by default
more agents therefore more reliable
summary-only handoff for decision-critical work
worker final conclusion as authority
team chat as Evidence
runtime trace as Evidence Pack
worker checkpoint as approval
role memory as governed memory
swarm as judgment
conductor/router as Zeus
client canvas as validation
topology metadata as executable dispatch
```

## Review checklist

Before adopting a non-trivial topology, verify:

1. Does the decisive inference require connecting evidence across sources?
2. Can extraction safely be distributed without distributing judgment?
3. Would summary-only handoff lose decisive source locality or contradiction?
4. Is parallelism materially useful rather than ornamental?
5. Are staged handoffs artifact-bound and reviewable?
6. Does the topology create external-effect, scope, cost, delay or memory risk?
7. Are every worker/tool/context boundary covered by the Task Contract?
8. Are Evidence Items/Handoff Artifacts sufficient for the claimed review path?
9. Is any human/professional decision still explicitly gated?
10. Is the simpler topology sufficient?

## Examples and validation

Illustrative historical examples live under `docs/examples/evidence_topology/`. They demonstrate topology concepts but are not current schema-conformance fixtures unless separately migrated and validated.

Current schema-owned examples/tests elsewhere in the repository validate the active machine contracts. Historical roadmap, bridge, reconciliation, schema-candidate and changelog addenda that were previously concatenated into this file remain available through Git history; they are not parallel current authorities.

## Relationships

This doctrine composes existing owners rather than replacing them:

- `WORKFLOW_SCHEMA.md` and `schemas/workflow_manifest.schema.yaml` — repeatable workflow topology/Evidence/handoff requirements;
- `TASK_CONTRACTS.md` and `schemas/task_contract.schema.yaml` — bounded task topology;
- `EVIDENCE_PACK.md` and `schemas/evidence_pack.schema.yaml` — Evidence/review result shapes;
- `HERMES_INTEGRATION.md` — external execution boundary;
- `APPROVALS.md` and `USER_DECISION_GATE.md` — consequential decisions;
- `MEMORY.md` — durable retention boundary;
- `SCOPE_ISOLATION.md` — scope separation;
- `EXTERNAL_TOOLS_POLICY.md` — tool admission/effects;
- `GOVERNANCE_COLLEGE.md` — role-based review, not distributed execution.

## Final rule

```text
Preserve the proof chain before distributing work.
Use the smallest topology that keeps Evidence attributable and reviewable.
Hermes may multiply execution capacity.
Pantheon does not multiply authority.
```
