# Architecture

Status: active doctrine — independently maintained in Pantheon Next — implemented as documentation.
Boundary profile: documentation_only.

Historical provenance is preserved in git history; current architecture follows observed owners and executable boundaries rather than historical product choices.

## Doctrine

```text
Hermes-compatible clients handle runtime interaction.
Hermes Agent executes externally.
Pantheon Cockpit exposes governed projections.
Pantheon Next governs consequential status.
The human decides.
```

Pantheon Next is governance-first. It defines authority, contracts, Evidence expectations, approvals, allowed transitions, Register rules and integration boundaries. It must remain simpler than the runtimes and clients it governs.

## Layered anatomy

```text
Hermes-compatible clients
  chat, sessions, runtime controls and attachments

Hermes Agent
  external execution runtime
  native context/files/memory when sufficient
  executable skills and tools
  candidate and observation emission

Pantheon Next
  governance source of truth
  Task Contracts and Context Packs
  Evidence and approval rules
  governed identities and relations
  capability placement / binding / activation rules
  Knowledge and Registre Probatoire boundaries

Pantheon Cockpit
  governed projections
  Cards, status, decision and review surfaces
  not a second general-purpose chat frontend

Optional replaceable bindings
  workspace / notes
  synchronization
  retrieval / RAG
  external runtime memory
  connectors and specialist adapters
```

No placement line transfers authority by itself.

```text
retrieved != truth
memory != Evidence
runtime success != authorization
projection != persistence
folder != governed identity
provider selected != Pantheon dependency
```

## Runtime boundary

Pantheon Next must not reimplement Hermes subsystems such as the agent loop, prompt assembly, provider resolution, executable tool registry, terminal, browser, session storage or runtime memory.

Hermes may execute bounded work after the applicable contract, policy and approval path. A successful run returns candidates and observations; it does not approve itself or canonize Evidence or memory.

Reference: `HERMES_INTEGRATION.md`.

## Client boundary

The user-facing runtime client is not a Pantheon authority.

The Hermes Web/dashboard surface is the current baseline. Compatible Web/PWA/mobile clients may be selected as replaceable clients when their authentication and API boundaries are verified.

Pantheon does not require OpenWebUI.

The Pantheon Cockpit remains distinct because its responsibility is governed projection, not generic conversation/runtime control.

## Workspace, retrieval and memory boundary

Pantheon does not prescribe a personal knowledge stack.

A valid deployment may use Hermes-native capabilities only:

```text
project/context files
explicit source files/folders
MEMORY.md / USER.md
session history/search
```

When richer workspace, synchronization, retrieval or external-memory behavior is useful, those capabilities are attached through replaceable bindings.

The currently best-demonstrated external reference is:

```text
Obsidian / Markdown
-> Self-hosted LiveSync / CouchDB when synchronization is needed
-> filesystem vault mirror
-> hindsight-obsidian-sync
-> Hindsight
-> bounded Hermes consumers
```

That composition is qualified and recommended when an external workspace/retrieval stack is desired. It is not a Pantheon prerequisite.

```text
qualified recommendation != mandatory dependency
workspace note != governed Project
Hindsight recall != truth
Hermes memory != Evidence
```

Professional source files keep their own source/provenance owners. A local/NAS ingestion path may preserve exact source identity without requiring a DMS.

Paperless is therefore not a required architecture component.

Reference: `HERMES_CAPABILITY_BINDINGS.md`, `OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md`, `MEMORY.md` and the document/source lifecycle owners.

## RAG boundary

Pantheon does not own or require a canonical RAG framework.

```text
identified source / scope
-> optional retrieval implementation
-> provenance-bearing candidate context
-> task reasoning
-> Evidence only through existing governed owners
```

Direct Hermes source/context access is valid when sufficient. Hindsight is the strongest qualified external retrieval recommendation currently present in the repository. Other retrieval implementations may replace it without changing Pantheon governance.

Embeddings, vector stores, rerankers and knowledge graphs remain implementation details unless an existing governed contract explicitly owns their persisted state.

## Task Contracts

Reference: `TASK_CONTRACTS.md`.

A Task Contract bounds purpose, scope, allowed/forbidden capabilities, outputs, approval ceiling, memory impact and Evidence expectations.

```text
Task Contract != runtime task
contract valid != effect authorized
runtime success != approval
```

## Evidence and approval

References: `EVIDENCE_PACK.md`, `APPROVALS.md`, `USER_DECISION_GATE.md`.

Consequential results remain reviewable. Evidence Packs expose relevant sources, assumptions, actions, limitations and outputs. Approval remains a distinct governed decision.

No interface click, runtime completion, health check, retrieval score or model agreement is approval by implication.

## Memory and Register

Reference: `MEMORY.md`.

Runtime memory, workspace notes, retrieved context, Knowledge and the Registre Probatoire remain distinct.

```text
workspace note != governed memory
runtime memory != Registre Probatoire entry
retrieval != promotion
```

Durable governed Assertions use the existing Register Candidate and promotion path.

## Capabilities and external tools

References: `CAPABILITY_PLACEMENT.md`, `UNIFORM_CAPABILITY_GOVERNANCE.md`, `ADAPTERS_AND_BINDINGS.md`, `EXTERNAL_TOOLS_POLICY.md`.

Before adding a runtime, client, connector, retrieval engine, memory provider, skill or tool:

1. verify whether Hermes native behavior or an existing owner already covers the need;
2. classify the abstract Capability Slot only when a distinct capability exists;
3. evaluate the concrete binding separately;
4. preserve selection, installation, activation and task authorization as distinct states;
5. keep the binding replaceable.

Pantheon must not create a parallel registry, installer, provider router, RAG subsystem or memory engine merely to manage an optional external product.

## Current convergence decision

```text
Required architecture responsibility
  Hermes interaction/execution
  Pantheon governance
  governed Cockpit projections where useful
  professional source/provenance owners

Valid minimal runtime choice
  Hermes native context/files/memory

Qualified recommended external enrichment
  Obsidian + LiveSync + Hindsight reference composition

Replaceable alternatives
  other compatible clients, workspace tools, retrieval engines and memory providers
```

OpenWebUI and Paperless are not target architecture components. Obsidian and Hindsight remain actively useful because they are demonstrated and qualified, but they are recommendations rather than prerequisites.

## Final rule

```text
Require responsibilities, not product names.
Reuse native Hermes behavior when sufficient.
Prefer the demonstrated Obsidian/Hindsight composition when its extra capabilities are wanted.
Keep clients and providers replaceable.
Keep sources, retrieval, memory, Evidence and authorization distinct.
```