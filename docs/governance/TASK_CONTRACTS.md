# Task Contracts

Status: active doctrine — conceptual stabilization.

A Task Contract defines the governed execution boundary for a task delegated to an external runtime.

A Task Contract is not a runtime task.

A Task Contract is not an execution graph.

A Task Contract is not a scheduler object.

Execution happens outside Pantheon Next.

```text
Optional Hermes WebUI or other compatible clients may expose runtime interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed contract, review and decision state.
Pantheon Next governs.
```

## Purpose

A Task Contract defines:

- intent;
- scope;
- constraints;
- approvals;
- expected evidence;
- allowed outputs;
- forbidden behaviors;
- memory expectations.

Pantheon Next defines what is legitimate.

Hermes Agent decides how to execute within its own runtime, under the contract boundary.

Pantheon Cockpit may project the governed contract, approval request, result status and Evidence Pack state. `nesquena/hermes-webui`, when selected, or another compatible runtime client may expose the runtime interaction around that work, but client display does not become governance authority.

## Core principle

A Task Contract governs execution without owning execution.

Pantheon Next defines:

- what is authorized;
- what is forbidden;
- what evidence is required;
- what approvals are required;
- what memory behavior is allowed.

Pantheon Next never:

- executes;
- schedules;
- dispatches;
- retries;
- routes providers;
- spawns workers;
- orchestrates runtime state.

## Minimal structure

A Task Contract should remain structurally minimal.

Canonical components:

```text
Identity
Intent
Scope
Roles
Rites
Constraints
Approvals
Expected Evidence
Allowed Outputs
Forbidden Outputs
Memory and Register Rules
Risk Notes
```

Anything beyond this requires justification.

## Identity

A Task Contract must define:

- stable identifier;
- owner role;
- creation source;
- revision linkage when applicable.

Identifiers are governance identifiers.

They are not runtime execution IDs.

## Intent

Intent defines the governed objective.

Intent must remain human-readable.

Bad intent:

```text
execute autonomous retrieval workflow
```

Good intent:

```text
review architectural consistency between quote and CCTP
```

## Scope

Scope defines boundaries.

It must define:

- included areas;
- excluded areas;
- authority limits;
- expected domain.

If scope is unclear, execution must not be considered governed.

## Roles

Roles are governance authorities.

Roles are not runtime agents.

Example:

```text
ATHENA
```

In Pantheon governance, this means:

```text
governance review authority
```

It does not mean:

```text
autonomous runtime worker
```

Hermes executes admitted work inside its own runtime envelope, by default the
single `pantheon-governed` profile. A Role is never a runtime identity, and the
absence of a Role-named profile is the normal valid state.

Pantheon does not execute the role.

## Rites

A Task Contract may recommend or require a rite when the task needs a bounded shared method.

A rite recommendation is governance context.

It is not an execution command.

It is not a runtime graph.

It is not a hidden role debate.

Valid uses include:

```text
RITE_DIVERGENCE_CONTROLEE for open-ended option exploration
AUTOCRITIQUE_CONTRADICTOIRE for post-draft review
CONCORDANCE_DES_SOURCES for source comparison
PREMISSES_CACHEES for assumption extraction
REFONDATION_DE_SESSION for resetting a polluted context
```

A Task Contract may define:

- recommended rite;
- trigger reason;
- roles expected to contribute;
- Evidence Pack expectations;
- User Decision Gate conditions;
- approval ceiling;
- memory constraints.

A Task Contract must not define:

- automatic rite execution;
- scheduler behavior;
- queue behavior;
- hidden role loop;
- executable rite order;
- automatic approval after rite completion;
- automatic memory promotion from rite output.

If Hermes executes work associated with a rite, Hermes does so externally under the Task Contract.

Pantheon governs the rite boundary only.

## Constraints

Constraints define non-negotiable limits.

Examples:

```text
human approval required before canonization
no external provider routing
no filesystem mutation
no deployment action
```

Constraints are governance rules.

They are not runtime configuration.

## Approvals

A Task Contract must define approval expectations.

Examples:

```text
C1
C2
C3
```

Approvals govern legitimacy.

They do not trigger execution automatically.

## Expected Evidence

Every governed execution must produce traceable evidence.

Canonical output:

```text
Evidence Pack
```

Expected evidence may include:

- assumptions;
- sources;
- risks;
- limitations;
- review notes;
- produced artifacts;
- rite trigger reason when a rite is used;
- rite output summary when it affects legitimacy.

No execution should become canonical without evidence.

## Allowed Outputs

Allowed outputs define authorized artifact categories.

Examples:

```text
markdown review
risk assessment
schema proposal
evidence pack
context pack
rite review note
```

Allowed outputs are not execution commands.

They are output categories.

## Forbidden Outputs

Forbidden outputs explicitly protect governance boundaries.

Examples:

```text
runtime orchestration
provider routing
automatic deployment
memory canonization
hidden workflow execution
rite runtime execution
```

If a requested output crosses these boundaries, the Task Contract must be revised or rejected.

## Memory and Register Rules

Task Contracts must define runtime-memory and register behavior explicitly.

Default rule:

```text
outputs are not Registre Probatoire entries
```

Admission to the Registre Probatoire requires:

- review;
- approval;
- traceability;
- evidence linkage.

Retrieved knowledge is not a Registre Probatoire entry.

Embeddings are not Registre Probatoire entries.

Agent repetition is not register admission.

High confidence is not register admission.

Rite output is not register admission.

A rite may support a Register Candidate only when the claim is explicit, scoped, evidence-linked and approval-bound.

## Risk Notes

Risk notes make uncertainty visible.

Examples:

```text
partial repository visibility
runtime assumptions not verified
migration doctrine incomplete
rite may be mistaken for executable workflow
```

Governed systems must expose uncertainty explicitly.

## Forbidden drift

Task Contracts must never become:

- workflow graphs;
- execution DAGs;
- scheduler inputs;
- runtime queues;
- orchestration manifests;
- autonomous agent instructions;
- automatic rite launchers.

If a Task Contract becomes executable by itself, governance drift has occurred.

## Relationship to Hermes Agent

Hermes Agent may interpret a Task Contract operationally.

Pantheon Next does not define how Hermes executes internally.

Hermes runtime behavior remains external.

Pantheon governs the contract boundary only.

## Relationship to runtime clients and Cockpit

`nesquena/hermes-webui`, if selected, or another compatible runtime client may expose runtime interaction, technical status and candidate outputs.

Pantheon Cockpit may project governed Task Contract state, approvals, evidence, reviews, recommended rites, rite status labels and Register Candidates.

Neither runtime-client display nor Cockpit projection triggers rites automatically, canonizes governance automatically or becomes the source of truth.

```text
Hermes WebUI available != Hermes WebUI selected
runtime display != approval
projection != persistence
optional client selected != authority transfer
```

## Relationship to schemas

The schema for Task Contracts validates structure.

It must not add runtime meaning.

The schema may validate required governance fields.

It must not define:

- execution order;
- retry behavior;
- worker assignment;
- provider choice;
- scheduling;
- dispatch semantics;
- tool execution;
- rite execution semantics.

## Final rule

A Task Contract exists to constrain execution.

Not to automate it.
