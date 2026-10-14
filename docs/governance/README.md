# Governance Index

Status: active support doctrine — governance entry point and read paths — implemented as documentation.
Boundary profile: active_support_doctrine.

This directory contains Pantheon Next governance references. Read the smallest owner set needed for the task.

```text
Hermes client surfaces handle runtime interaction.
Pantheon Cockpit exposes governed projections.
Hermes Agent executes externally.
Pantheon Next governs consequential status.
The human decides.
```

Pantheon Next is governance-first. It is not an autonomous runtime, general-purpose UI, DMS, memory backend or installer.

## Status spine

Do not infer current state from an old diagram, prototype, or candidate note.

```text
STATUS.md          -> repository posture
WHAT_RUNS.md       -> observed implementation and runtime status
AUTHORITY_INDEX.md -> authority class and repository state
MODULES.md         -> ownership by governance area
CORE_CONCEPTS_MAP.md -> compact concept and owner navigation
CONTRIBUTING.md    -> change discipline and protected paths
```

Supporting vocabulary:

- `STATUS_HEADER_RULES.md`;
- `BOUNDARY_PROFILES.md`;
- `NON_EQUIVALENCE_RULES.md`;
- `GLOSSARY.md`;
- `TERMINOLOGY_BOUNDARIES.md`.

## Short stable path

Before significant repository work, read:

1. `STATUS.md`
2. `WHAT_RUNS.md`
3. `AUTHORITY_INDEX.md`
4. `CORE_CONCEPTS_MAP.md`
5. `MODULES.md`
6. `CONTRIBUTING.md`
7. the specific owner documents required by the task.

Do not read the whole governance corpus by default.

## Repository status or audit

```text
STATUS.md
-> WHAT_RUNS.md
-> AUTHORITY_INDEX.md
-> MODULES.md
-> CODE_AUDIT_POST_PIVOT.md when protected code/artifacts are involved
```

Use this path to distinguish implemented, candidate, external, obsolete and voluntarily absent material.

## Capability, tool, skill, connector or external repository

```text
CAPABILITY_PLACEMENT.md
-> UNIFORM_CAPABILITY_GOVERNANCE.md
-> ADAPTERS_AND_BINDINGS.md
-> EXTERNAL_TOOLS_POLICY.md
-> HERMES_INTEGRATION.md when Hermes executes
-> MODEL_CAPABILITY_PASSPORT.md when model-specific
```

For a concrete external client/tool, use the existing placement/review register rather than creating a new doctrine document unless it owns a genuinely distinct responsibility.

Always keep separate:

```text
abstract capability
candidate binding/client
installation status
health status
activation status
task authorization
Pantheon gates
human approval
```

## Governed professional work

```text
REQUEST_LIFECYCLE.md        -> request/cap lifecycle, proportional activation and Case / Situation intake brief
-> TASK_CONTRACTS.md
-> CONTEXT_PACKS.md
-> HERMES_INTEGRATION.md
-> EVIDENCE_PACK.md
-> APPROVALS.md
-> USER_DECISION_GATE.md
```

Core sequence:

```text
clarify situation
-> bind scope and consequences
-> prepare bounded context
-> execute externally when authorized
-> return candidates and observations
-> qualify Evidence/status
-> human decision
```

## Cockpit and presentation

```text
PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md
-> CARD_STACK_MODEL.md
-> CARD_PROJECTION_DEFINITION_MODEL.md
-> DECISION_SURFACE_SPEC.md when decision review is involved
-> CONTEXT_STACK.md when visible dynamic context is involved
```

Ownership rule:

- Structured Interface owns product composition and root-space meaning;
- Navigation Registry owns executable root identities/order;
- Card Stack owns generic Card / Scene / Deck / Constellation grammar;
- Card Projection Definition owns bounded machine-readable mapping into the renderer;
- decision/context documents specialize their respective projections.

The Cockpit is a governed projection surface, not a second general-purpose chat frontend.

## Hermes client surfaces

The official Hermes Web/dashboard is the current baseline for runtime conversation, sessions and controls. Compatible clients such as mobile/PWA surfaces remain replaceable external clients and must follow Hermes-supported contracts and deployment/authentication boundaries.

Pantheon does not require a particular third-party chat frontend. OpenWebUI is a superseded integration path, not a current owner.

Reference: `HERMES_INTEGRATION.md` plus the external tool placement/review records when a concrete client is evaluated.

## Workspace, documents and Knowledge

```text
OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md
-> document lifecycle/source owners
-> KNOWLEDGE_TAXONOMY.md
-> RAG_INGESTION_AND_EVIDENCE_BOUNDARIES.md when retrieval/evidence boundaries matter
```

Obsidian is the human Markdown workspace direction. It is not the professional source authority, governed Project identity, Evidence store or Registre Probatoire.

Professional files may use the bounded local/NAS source-ingestion path without requiring a separate DMS product. Paperless is a superseded optional candidate, not a current architecture dependency.

## Knowledge, Evidence and memory

```text
KNOWLEDGE_TAXONOMY.md
-> EVIDENCE_PACK.md
-> EVIDENCE_TOPOLOGY.md when needed
-> APPROVALS.md
-> MEMORY.md
```

Keep these distinctions:

```text
source != knowledge
knowledge != Evidence
retrieved != truth
Evidence != approval
runtime memory != Registre Probatoire
runtime success != authorization
```

## Roles, rites, spaces and methods

```text
AGENTS.md
-> GOVERNANCE_COLLEGE.md
-> ROLE_SIGNALS.md
-> METHOD_TAXONOMY.md
-> rites/README.md
-> EVOLUTION_OF_ROLES_RITES_AND_SPACES.md when changing identities/boundaries
-> USER_DECISION_GATE.md
```

Roles judge; Rites structure bounded method; presentation structures expose; the human decides. Roles and mythological names do not imply autonomous agents.

## Architecture domain

Start from `docs/domain-packs/architecture/`, then read only the relevant project-understanding, proof, document-review or method owner. Schemas validate structure; they do not provide professional validation.

## External references and inspirations

```text
WATCHLIST.md or SKILL_WATCHLIST.md
-> REFERENCE_BOUNDARIES.md
-> reference review when needed
-> DISTILLATION_REGISTRY.md or REJECTED_PATTERNS.md
-> EXTERNAL_TOOL_PLACEMENT_REGISTER.md
```

```text
observe -> understand -> decide -> preserve
```

A watchlist/review item is not an installation, activation or adoption decision.

## Repository layer boundary

```text
Pantheon governance
  doctrine, contracts, status and read-only verification

Pantheon implementation
  bounded executable candidate behavior under implementation/

Hermes runtime
  external execution and runtime interaction surfaces

Pantheon Cockpit
  governed projections only

Obsidian workspace
  human-authored Markdown and editable working projections

External adapters/clients
  replaceable connectors, extraction tools, memory providers and UI clients

Professional sources
  exact source material and provenance under the relevant source/document owner
```

Repository placement does not establish adoption, activation, authorization or Evidence status.

## Anti-sprawl rule

Before creating a permanent document:

1. identify the existing owner;
2. state the observed responsibility the owner cannot express;
3. define authority/repository status;
4. identify convergence or retirement path;
5. prefer extending or simplifying the owner over adding a parallel model.

A roadmap, log, diagram, prototype or historical integration path does not become authority through repetition.

## Boundary rule

No governance document may introduce hidden execution, autonomous approval, an internal scheduler/queue/provider router, automatic memory promotion, automatic external sending, a plugin marketplace or another general-purpose agent runtime.

```text
Pantheon defines governed contracts and consequential status.
Hermes executes externally.
Clients remain replaceable.
The Cockpit projects governed state.
Obsidian supports human workspace work.
The human decides.
```