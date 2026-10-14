# Memory

Status: active doctrine — Registre Probatoire boundary owner.

Pantheon does not own a conversational-memory engine.

Hermes owns its runtime memory and may use its native facilities or one separately selected external provider. The provider choice is an execution-runtime concern unless it changes a Pantheon governance boundary.

Current Hermes native facilities include bounded persistent `MEMORY.md` / `USER.md`, session history/search and project/context files. They are sufficient for a valid deployment when they satisfy the user's needs.

```text
Hermes native memory sufficient
-> no external memory provider required

external provider selected
-> optional runtime binding
-> not a Pantheon dependency
```

Pantheon governs the `Registre Probatoire`, not Hermes memory.

## Core boundary

```text
memory != Evidence
retrieved != true
remembered != approved
runtime persistence != Pantheon persistence
provider selection != governance authority
```

Hermes memory may store, recall, rank, summarize and propose. It carries no professional authority.

```text
Memory first. Evidence when consequential. Status when deciding. Approval when acting.
```

Nothing remembered or retrieved becomes probative automatically.

## Categories

Pantheon distinguishes:

```text
Knowledge
Context
Session State
Runtime State
Register Candidate
Registre Probatoire entry
```

They must not be collapsed.

### Knowledge

Knowledge is consultable material under existing Knowledge/source owners. It may support reasoning but is not automatically Evidence.

The implementation used to retrieve or display Knowledge may be Hermes-native or external and remains replaceable.

### Context

Context is bounded information assembled for a task. A Context Pack is not memory and does not become durable merely because Hermes consumed it.

### Session State

Session State is transient conversation or task-local information. Hermes may persist conversation history operationally, but that does not create Pantheon durable state.

### Runtime State

Runtime State belongs to the execution runtime.

Examples include:

- Hermes native memory;
- an external Hermes memory provider;
- session/history databases;
- worker/tool execution state;
- temporary caches and provider state.

Pantheon does not treat Runtime State as Evidence or Registre Probatoire state.

## Episodic and associative freedom

Runtime memory may preserve project episodes, observations, hypotheses, unusual details, narrative context and associations without first forcing them into a Pantheon semantic schema.

This is deliberate. Some useful project knowledge is specific, ambiguous or exploratory before it is machine-actionable.

```text
free episode
!= Project Anatomy claim
!= Knowledge publication
!= Requirement
!= Evidence
!= Decision
```

A memory provider may keep a free payload such as:

```text
"The wall appears slightly irregular near the opening.
Compare with the previous visit and the client's earlier remark."
```

without immediately inventing a defect taxonomy, stable project identity or admitted semantic relation.

Where the runtime/provider supports it, a useful episode should keep only a small routing envelope around that free payload, for example:

```text
episode identity
scope
observed / remembered time when useful
free content
source / document / project-object references when known
provider/runtime provenance
```

This list is guidance, not a new Pantheon schema. Fields may remain absent when the runtime cannot establish them honestly.

```text
minimal envelope != structured semantic payload
missing ref != permission to infer one
provider bank/folder != governed identity
```

An episode may point to several existing worlds at once, for example:

```text
photo / image region
plan / document locator
Project Anatomy source representation or stable-object candidate
meeting note / email fragment
external reference
```

Those references improve retrieval and context assembly. They do not admit the episode's interpretation into the referenced owner.

## Structured and free knowledge coexist

Pantheon should not require every useful memory to become structured, and runtime memory should not become a second Project Anatomy or Knowledge graph.

```text
free / episodic / associative
-> preserve singularity, ambiguity and context

structured / governed owners
-> provide stable identity, addressable claims, requirements and durable professional state
```

The two sides may be composed for retrieval, but they keep distinct responsibilities.

```text
Project Anatomy / Knowledge -> runtime context or memory
= allowed bounded retrieval

runtime memory -> Project Anatomy / Knowledge / Requirement / Register
= candidate only
= existing owner must validate/admit the effect
```

In short:

```text
retrieval may be bidirectional
promotion is one-way through governed owners
```

Repeated recall, similarity, model confidence or a dense cluster of associations does not perform that promotion.

## Spatial and visual episodes

Visual/spatial runtimes may remember observations derived from photographs, scans, video or reconstructed geometry, including references to image regions or derived representations.

Examples include:

```text
segmented region
detected object candidate
relative depth observation
surface-orientation observation
camera/view context
multi-view association
point-cloud / reconstruction reference
```

Dense outputs such as masks, depth maps, normal maps, embeddings, point maps or meshes remain source-linked derived runtime representations unless an existing Project Anatomy adapter deliberately distills selected observations into an Observation Bundle.

```text
segmentation != stable identity
object detection != Project Anatomy object
depth prediction != surveyed geometry
normal prediction != professionally measured orientation
multi-view association != identity accepted
derived spatial representation != Evidence
```

A spatial episode may therefore remain free and useful even when no stable object has been resolved yet. Later structured promotion must preserve the exact source/representation provenance and uncertainty rather than rewriting the episode as if it had always been a project fact.

## Provider-agnostic rule

Pantheon does not prescribe Hindsight, Mnemosyne, Mem0 or another memory product.

Hindsight has substantial qualification evidence in this repository and can be a useful optional binding. Mnemosyne and other providers have historical or comparison evidence. None is a Pantheon prerequisite.

```text
qualified provider != mandatory provider
recommended provider != authority
same provider for two functions != same responsibility
```

Workspace/document retrieval and conversational/workstream memory remain conceptually distinct even if one product implements both. Their scopes must stay distinguishable.

The machine-checkable `external_runtime_memory` Capability Binding may remain `unbound` when Hermes native memory is sufficient.

## Register Candidate

A Register Candidate is a proposed durable Assertion. It is not probative.

It should identify at least:

```text
Claim
Scope
Source / Evidence link
Certainty
Risk
Required approval
Status
```

A candidate may originate from user instruction, validated project work, Evidence Pack output, Hermes observation or governance review. Raw model confidence is not sufficient.

## Registre Probatoire entry

A Registre Probatoire entry is durable, reviewed evidence for future consequential use.

It requires:

- a clear scoped claim;
- certainty level;
- exhibits, dates and citations;
- Evidence linkage;
- the required approval;
- reviewability;
- revocation or supersession path.

## Promotion rule

```text
candidate until approved
```

No Hermes profile, memory provider, retrieval engine, workspace, repeated observation or successful runtime operation may promote a Registre Probatoire entry automatically.

Promotion requires the existing Evidence and approval owners.

## Scope rule

Durable Assertions remain explicitly scoped, for example:

```text
user
project
domain
repository
governance
system
```

A project memory or note must not silently become agency/system doctrine. A filesystem folder or provider bank does not define governed identity by itself.

## Status rule

Register governance may use:

```text
candidate
under_review
approved
rejected
deferred
superseded
revoked
archived
```

Those are governance states, not runtime-memory states.

## Final rule

```text
Hermes may remember freely with native or optional external facilities.
Pantheon does not require every useful episode to fit a semantic schema.
Structured owners remain available when stable identity or machine-actionable meaning is useful.
Pantheon cares when memory crosses into consequential context, Evidence, approval or durable governed Assertions.
Memory never crosses that boundary automatically.
```