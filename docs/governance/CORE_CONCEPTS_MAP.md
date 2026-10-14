# Core Concepts Map

Status: active support doctrine — navigation concept map only — implemented as documentation.
Boundary profile: active_support_doctrine.

This is the compact navigation and ownership entry point for Pantheon Next concepts. It is not a schema, runtime, registry, workflow engine, plugin manager, retrieval engine or approval engine.

```text
Hermes client surfaces handle conversation and runtime interaction.
Hermes Agent executes externally.
Pantheon Cockpit exposes governed projections.
Pantheon Next governs consequential status.
The human decides.
```

No interface, workspace, retrieval engine or memory provider becomes authority merely because it works or displays information.

## Core flow

`Case` is the governed system concept. A filesystem folder, note workspace or UI collection is only a projection or working scope unless an existing owner explicitly binds it to governed identity.

```text
User request
-> Case / Situation clarification
-> Task Contract Candidate
-> scoped Sources / Knowledge selection
-> Context Pack
-> Hermes execution when authorized
-> Output Candidate
-> Evidence Pack Candidate
-> review / approval
-> delivery or User Decision Gate
-> optional Register Candidate
-> Registre Probatoire entry only after governed promotion
```

```text
retrieved != truth
memory != Evidence
runtime success != authorization
projection != persistence
folder != governed identity
```

## Governed cognitive ecology

Pantheon can be understood as a governed cognitive ecology rather than a central brain or a multi-agent execution team.

This is a navigation model only. It creates no new authority class, runtime object, schema family or lifecycle.

The purpose is to keep several kinds of attention, method, context, state and constraint distinct enough to disagree, correct one another and remain attributable without collapsing them into one autonomous actor.

### Map 1 — concept grammar

```text
WHO judges?                 -> Pantheon Role
HOW is review structured?   -> Rite
WHERE does activity belong? -> governed Space
WHAT carries governed state?-> governed Object
UNDER WHICH CONSTRAINTS?    -> existing Rules / Contracts / Invariants

WHO executes?               -> Hermes or another admitted runtime
WHO closes consequence?     -> the human when consequential decision is required
```

The mythological vocabulary is a human memory aid, not an ownership system. `ATHENA`, `ARGOS`, `THEMIS`, `ZEUS` and the other Roles name standing responsibilities of judgment; they are not autonomous agents.

`Rules / Contracts / Invariants` is deliberately descriptive rather than a new machine category. Schema validation, policy requirements, approval rules and PEP enforcement remain distinct mechanisms with their existing owners.

### Map 2 — responsibility families

`MODULES.md` groups responsibilities for navigation:

```text
Governance Kernel
Governed State and Professional Semantics
Admission and Consequential Effects
Execution and Integration
Interaction, Projection and Workspace
```

This answers where a responsibility sits in the architecture. It does not define its authority owner.

### Map 3 — authority envelope

`PANTHEON_SYSTEM_OWNERSHIP_REGISTRY.json` records machine-readable ownership dimensions such as:

```text
semantic_owner
implementation_owner
transition_owner
persistence_owner
runtime_owner
projection_owner
```

This answers who owns each responsibility dimension. It is orthogonal to the concept grammar.

For example, `ProjectClaim` may be read as a governed Object, placed in Governed State, while its semantic, transition, persistence and projection responsibilities remain separately owned.

### Map 4 — governed flow

Objects also participate in bounded transitions:

```text
Source / observation
-> candidate
-> Claim or other governed state where admitted
-> Evidence where deliberately admitted
-> review / decision
-> authorized effect
-> new observations
```

A later observation can re-enter the ecology without rewriting prior history or promoting itself to truth.

Core non-collapse rules:

```text
Role judges an Object != Role owns that Object
Rite structures review != Rite is a workflow runtime
Space exposes an Object != Space owns its lifecycle
Rule constrains an effect != Rule executes the effect
candidate relation != governed relation
confidence != authority
```

### Extension-before-creation test

Before introducing a new concept, first ask:

```text
standing responsibility of judgment? -> test Role / facet / consultation
recurring bounded review method?      -> test Rite / existing mode
durable activity distinction?        -> test governed Space / existing Scene or projection
identity + state + lifecycle of its own? -> test governed Object / existing owner extension
constraint only?                      -> extend an existing Rule / Contract / Invariant owner
calculation only?                     -> Capability / implementation
presentation only?                    -> projection / Scene / Deck
```

If none of these requires a new identity, extend the existing owner instead of multiplying concepts.

## Object ownership map

| Concept | Responsibility | Must not become |
|---|---|---|
| Raw Source | available source material | proof |
| Knowledge Item | organized consultable reference | truth |
| Retrieved Knowledge | surfaced candidate support | Evidence by itself |
| Context Pack | bounded task context | memory or proof |
| Task Contract | governed task boundary | runtime task or approval |
| Hermes execution | external execution under contract | governance authority |
| Output Candidate | proposed result | approved deliverable |
| Evidence Pack | reviewable proof package | runtime log or approval |
| Approval | explicit governance decision | runtime success flag |
| Register Candidate | proposed durable Assertion | Registre Probatoire entry |
| Registre Probatoire entry | approved scoped durable Assertion | raw database or runtime memory |
| Pantheon Role | governance viewpoint | autonomous agent |
| Rite | bounded shared method | workflow runtime |
| Domain Pack | professional constraints | professional authority |
| Capability / Skill Candidate | eligible external capability | installed or task-authorized capability |
| Effective Policy | computed governance posture | execution engine |
| Pantheon Cockpit | governed projection and decision surface | source of truth or runtime |
| Hermes client surface | conversation/runtime interaction with Hermes | Pantheon governance surface by implication |
| Workspace / note binding | optional human working representation | governed identity, Evidence or mandatory Pantheon component |
| Retrieval / RAG binding | optional candidate context retrieval | truth, scope authority or mandatory Pantheon component |
| Hermes runtime memory | native or optional external recall owned by Hermes | Evidence, Register or Pantheon persistence |
| User Decision Gate | visible consequential decision point | automatic approval |

## Authority ladder

```text
Raw Source
-> Source Reference
-> Evidence Item
-> Evidence Pack
-> Approval
-> Register Candidate when a durable Assertion exists
-> Registre Probatoire entry after governed promotion
```

No retrieval score, model confidence, runtime completion, repeated memory or interface state short-circuits this ladder.

## Execution and presentation

Pantheon does not absorb Hermes execution and Hermes clients do not absorb Pantheon governance.

```text
Task Contract / Context Pack
-> Hermes Agent executes externally
-> Hermes returns candidates and observations
-> Pantheon qualifies consequential status
-> Pantheon Cockpit may project governed state
-> Hermes-compatible clients may continue runtime conversation and control
```

Hermes clients remain replaceable. Pantheon requires their boundary behavior, not a specific frontend product.

## Knowledge, workspace, retrieval and memory

These responsibilities remain separate:

```text
Source / Document owners
  exact professional source identity and provenance

Pantheon Knowledge
  governed consultable knowledge objects and their status

Optional workspace / note implementation
  human working notes and editable projections

Optional retrieval / RAG implementation
  candidate context selection and ranking

Hermes runtime memory
  native MEMORY.md / USER.md / session history or one selected external provider
```

A valid deployment may use only Hermes-native context/files/memory where that is sufficient. External workspace, synchronization, retrieval or memory products are optional bindings.

The repository currently contains useful qualification evidence for Obsidian, LiveSync/CouchDB and Hindsight. Those are reference implementations, not Pantheon prerequisites or architectural owners.

```text
recommended != required
qualified != adopted
provider selected != Pantheon dependency
```

## Roles, rites and methods

```text
Roles judge.
Rites structure bounded method.
Agora may expose deliberation.
ZEUS arbitrates governed status and procedure.
The human decides.
```

A Role Signal may request review or escalation. It must not execute, approve or promote memory.

## Capabilities

```text
capability detected
-> binding eligible
-> binding selected / activated where governed
-> task-authorized through existing contract/admission owners
-> Hermes may execute externally
-> result remains candidate until qualified
```

Canonical owners include:

- `CAPABILITY_PLACEMENT.md` and `UNIFORM_CAPABILITY_GOVERNANCE.md` for placement and common governance;
- Capability Passport contracts for exact-release eligibility;
- Binding and Activation contracts for selected runtime bindings;
- `TASK_CONTRACTS.md` and Execution Admission for task legitimacy;
- `HERMES_INTEGRATION.md` for external execution boundary;
- `HERMES_CAPABILITY_BINDINGS.md` for product-specific optional Hermes bindings;
- `PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md` for Cockpit product composition;
- `CARD_STACK_MODEL.md` for generic Card / Scene / Deck / Constellation projection grammar.

Detected, installed, activated and task-authorized remain distinct states.

## External systems

External tools are reviewed before becoming a selected binding or client.

```text
Watch
-> Reference Review / placement review
-> distill, reject or retain as candidate
-> select only through an existing owner
-> Task Contract before consequential execution
```

A reviewed UI, runtime, DMS, workspace, RAG engine, memory system or connector does not become Pantheon architecture merely because it works technically.

OpenWebUI and Paperless are superseded integration candidates, not current target owners. Obsidian/LiveSync/CouchDB remain useful historical qualification evidence and optional tooling, but they no longer define the selected productive AFFAIRES route. Hindsight remains the selected derived retrieval/memory candidate and is still replaceable.

## Stable reading path

Read this map, then only the owners relevant to the task:

```text
repository state       -> STATUS.md, WHAT_RUNS.md, AUTHORITY_INDEX.md
vocabulary             -> TERMINOLOGY_BOUNDARIES.md, GLOSSARY.md
execution              -> TASK_CONTRACTS.md, HERMES_INTEGRATION.md
context                 -> CONTEXT_PACKS.md, CONTEXT_STACK.md
cockpit product         -> PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md
card grammar            -> CARD_STACK_MODEL.md
knowledge               -> KNOWLEDGE_TAXONOMY.md
optional Hermes binding -> HERMES_CAPABILITY_BINDINGS.md
Evidence                -> EVIDENCE_PACK.md
approval                -> APPROVALS.md, USER_DECISION_GATE.md
memory / Register       -> MEMORY.md
external tools          -> EXTERNAL_TOOLS_POLICY.md, EXTERNAL_TOOL_PLACEMENT_REGISTER.md
reference workspace     -> OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md
```

## Final rule

```text
Every Pantheon concept has one job.
Product choices stay replaceable when Pantheon does not own the responsibility.
Every durable promotion uses an existing governed owner.
Every external effect keeps an explicit boundary.
No recommended tool is promoted into a platform prerequisite without a demonstrated invariant that requires it.
```