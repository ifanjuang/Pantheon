# Workflow Manifest

Status: active doctrine — conceptual stabilization.

A Workflow Manifest is a governed declaration.

It is not an execution graph.

It is not a scheduler object.

It is not a queue definition.

It is not a hidden orchestration layer.

It describes how a class of work should be governed, reviewed, evidenced and approved.

It does not make Pantheon Next execute that work.

```text
Optional runtime clients may expose interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed workflow, review and decision state.
Pantheon Next governs.
The human decides consequential effects.
```

## Naming and compatibility

This file keeps the historical name `WORKFLOW_SCHEMA.md` for repository compatibility.

The canonical concept is `Workflow Manifest`.

A Workflow Manifest is a governance artifact.

It is not a runtime workflow.

Clarification is preferred over renaming until schema references and governance references are reconciled.

## Purpose

A Workflow Manifest defines reusable governance expectations for a recurring class of work.

It may describe:

- intended use;
- domain scope;
- entry criteria;
- role viewpoints;
- required Task Contracts;
- expected Evidence Packs;
- approval expectations;
- allowed outputs;
- memory rules;
- risk review requirements;
- completion criteria.

It must remain human-readable.

## Core principle

A workflow in Pantheon Next is not what runs.

A workflow is what governs the legitimacy of a repeated process.

Hermes Agent or another external runtime may decide how to operate.

Pantheon Next defines the governance envelope only.

## Minimal structure

A Workflow Manifest should remain structurally small.

Canonical components:

```text
Identity
Purpose
Scope
Entry Criteria
Governed Phases
Role Viewpoints
Task Contract Requirements
Evidence Requirements
Approval Requirements
Allowed Outputs
Memory Rules
Risk Notes
Completion Criteria
```

Anything beyond this requires justification.

## Identity

A Workflow Manifest must define a stable identifier and a clear title.

The identifier is a governance identifier.

It is not a runtime job identifier.

It is not a graph node identifier.

## Purpose

Purpose explains the type of work the workflow governs.

Good purpose:

```text
review quote and CCTP consistency before issuing a recommendation
```

Bad purpose:

```text
run a multi-agent autonomous execution graph
```

## Scope

Scope defines where the workflow applies.

It must define:

- included domains;
- excluded domains;
- authority limits;
- expected inputs;
- expected outputs.

If scope is unclear, the workflow cannot govern reliably.

## Entry criteria

Entry criteria define when the workflow may be used.

Examples:

```text
source documents are available
user intent is clear
protected areas are identified
approval level has been estimated
```

Entry criteria are governance checks.

They are not runtime triggers.

## Governed phases

A Workflow Manifest may describe phases.

Phases are review and governance stages.

They are not executable steps.

A phase may describe:

- purpose;
- responsible role viewpoint;
- expected input;
- expected output;
- evidence expectation;
- approval expectation;
- risk condition.

A phase must not describe:

- worker scheduling;
- queue progression;
- provider routing;
- retry policy;
- runtime state transition;
- tool dispatch.

## Role viewpoints

A workflow may request candidate viewpoints from the canonical Pantheon Roles owned by `AGENTS.md`.

Examples:

```text
ATHENA for planning and decomposition
ARGOS for source review
MNEMOSYNE for continuity, version/supersession review and retention-placement proposals
THEMIS for risk
APOLLO for quality
ZEUS for arbitration of status/procedure
IRIS for formulation
HEPHAISTOS for implementation candidates
```

Roles provide governance perspectives.

They are not autonomous workers inside Pantheon Next.

A Workflow Manifest must not create another canonical Role by naming a lifecycle function or metaphor.

## Task Contract requirements

A Workflow Manifest may require one or more Task Contracts.

The Task Contract defines the governed execution boundary.

The Workflow Manifest does not replace the Task Contract.

The Workflow Manifest does not authorize execution by itself.

## Evidence requirements

A Workflow Manifest must define the expected Evidence Pack pattern.

It may require:

- assumptions;
- source references;
- risk notes;
- output references;
- review notes;
- register candidates;
- approval references.

Evidence requirements make the workflow auditable.

They do not create an observability backend.

## Approval requirements

A Workflow Manifest may define expected approval levels.

Approvals validate legitimacy.

Approvals do not make Pantheon execute.

Approval escalation is required when scope, risk, memory effect or external effect increases.

## Allowed outputs

Allowed outputs define artifact categories.

Examples:

```text
review note
risk assessment
context pack
patch candidate
register candidate
Evidence Pack
```

Allowed outputs are not commands.

They are governance categories.

## Register rules

A Workflow Manifest must define register expectations. Runtime memory remains external; the governed durable object is the Registre Probatoire.

Default rule:

```text
workflow outputs are not a Registre Probatoire entry
```

The workflow may propose Register Candidates.

Only the applicable governed review and approval path can promote a Registre Probatoire entry.

## Risk notes

A Workflow Manifest must expose risk conditions.

Examples:

```text
source uncertainty
scope ambiguity
protected area touched
external runtime dependency
memory promotion requested
runtime drift risk
```

Risk notes are part of governance.

They are not failure handling logic.

## Completion criteria

Completion criteria define when a workflow output is reviewable.

Examples:

```text
Evidence Pack produced
risks recorded
approval state recorded
outputs listed
register candidates marked as candidates
```

Completion does not mean canonization.

Completion does not mean approval.

Completion does not mean external execution succeeded unless evidence supports that claim.

## Governed composition

A Workflow Manifest may be composed on demand rather than written by hand. HEPHAISTOS may forge a Workflow Manifest Candidate for a specific cap that has already been made explicit through `REQUEST_LIFECYCLE.md` and the applicable Task Contract owners, using capabilities declared in `CAPABILITY_REGISTRY.md`.

Composition reuses existing governance rather than adding machinery. It follows a retrieve / reuse / revise / retain loop:

```text
retrieve  candidate capabilities and prior manifests for the cap
reuse     a prior governed manifest when one fits
revise    the manifest as a governed Task Contract revision when the task boundary changes
retain    only what review keeps; superseded material follows existing archive/retention owners
```

Archive is a lifecycle status, not deletion. A superseded manifest does not keep acting merely because it remains preserved for provenance.

A forged manifest is a candidate. forged != authorized.

### Two gates

Composition is bounded by two governance gates.

```text
Pre-execution eligibility gate — ZEUS may arbitrate when status/procedure is disputed
  Before any step runs: are the capabilities admitted for this cap and scope?
  Is the Task Contract sufficient? Is the approval ceiling (C0–C5) declared?
  Decision: allow / allow_with_gate / block / needs_revision / needs_evidence.

Post-execution evidence gate
  After the runtime returns, the raw result is a Result Candidate.
  An Evidence Pack Candidate is assembled; answer verification (V0–V4) and
  probative certainty (E0–E4) are assessed. Nothing is delivered, canonized or
  promoted to a Registre Probatoire entry on the strength of completion alone.
```

The first gate decides whether the governed execution opportunity is admitted. The second qualifies what the returned result means. Neither gate executes work, approves by itself or promotes a register entry.

### Per-step signatures

Each forged step carries a governance signature, not an execution signature:

```text
capability_id (from CAPABILITY_REGISTRY)
declared scope and forbidden scope
required Task Contract
expected Evidence Pack shape
approval ceiling (C0–C5)
register behavior (Register Candidate only unless approved)
refusal tests
```

A signature records what governance expects of a step. It does not run the step.

### Boundary

Governed composition adds no forge engine, compiler, scheduler, queue, provider router or runtime. HEPHAISTOS may prepare a candidate recipe or artifact structure; the execution runtime executes outside Pantheon under Task Contract; Pantheon governs the cap, proof and status; the human engages where consequence requires authority.

```text
forged != authorized
completed != approved
returned != a Registre Probatoire entry
```

## Relationship to Task Contracts

A Workflow Manifest governs a class of work.

A Task Contract governs a specific task.

A Workflow Manifest may guide Task Contract drafting.

It must not replace task-specific scope, evidence or approval decisions.

## Relationship to Evidence Packs

A Workflow Manifest defines expected proof patterns.

The Evidence Pack records the actual Evidence produced for a specific task.

The workflow does not approve its own evidence.

## Relationship to the Registre Probatoire

A Workflow Manifest may allow Register Candidate proposals.

It must not allow automatic memory promotion.

## Relationship to Hermes Agent

Hermes Agent may use a Workflow Manifest as contextual guidance.

Pantheon Next does not define how Hermes executes internally.

Pantheon Next does not install, schedule or run workflows.

## Relationship to runtime clients and Cockpit

An optional compatible runtime client may expose workflow descriptions, approval prompts, evidence and outputs.

Pantheon Cockpit may project governed workflow status, Evidence gaps, approvals and linked decisions.

Neither client display nor Cockpit projection makes the workflow canonical, executes it for Pantheon Next, grants approval or transfers authority.

```text
client selected != authority transfer
client display != authority
projection != persistence
```

## Relationship to schemas

The machine contract exists at:

```text
schemas/workflow_manifest.schema.yaml
```

It validates the declared Workflow Manifest structure. Current qualification work, including the bounded multi-source research manifest, uses that schema as a structural referent.

The schema may validate fields such as:

- identity;
- scope;
- phase declarations;
- role references;
- Evidence requirements;
- approval requirements;
- memory rules;
- risk notes.

It must not define:

- execution order as runtime semantics;
- scheduling;
- queueing;
- retry behavior;
- worker assignment;
- provider routing;
- tool dispatch;
- hidden graph state.

```text
schema_valid != authorized
schema_present != runtime implemented
```

## Forbidden drift

Workflow Manifests must never become:

- execution DAGs;
- LangGraph definitions;
- scheduler inputs;
- queue definitions;
- provider routing plans;
- tool-call plans;
- autonomous agent plans;
- hidden orchestration specs;
- self-evolution loops.

If a Workflow Manifest becomes necessary to run the system as an internal Pantheon execution graph, governance drift has occurred.

## Final rule

A Workflow Manifest exists to govern repeatable work.

Not to execute it.
