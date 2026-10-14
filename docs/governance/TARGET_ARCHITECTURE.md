# Target Architecture — coherence compass

Status: validation-only proposal — current architecture direction — documented non-implemented.
Boundary profile: validation_only_trace.

This document is a direction record, not a runtime or adoption proof. It names the smallest target composition justified by current owners and observed implementation.

## Target composition

```text
USER INTERACTION
  Hermes-compatible client surface
        |
        v
EXECUTION
  Hermes Agent
  native context / files / memory when sufficient
        |
        | governed request / observation boundary
        v
GOVERNANCE
  Pantheon Next
  Task Contracts · policy/admission · Evidence · approval · Register
        |
        +-> Pantheon Cockpit
              governed projections and decision/review surfaces

OPTIONAL REPLACEABLE BINDINGS
  workspace / note client
  synchronization transport
  retrieval / indexing / RAG
  external runtime memory

PROFESSIONAL SOURCES
  exact files / source representations under existing document/source owners
```

Pantheon does not require one particular workspace, synchronization product, RAG stack or memory engine.

## Responsibilities

| Layer | Owns | Does not own |
|---|---|---|
| Hermes-compatible clients | conversation, sessions and runtime interaction | Pantheon governance or professional truth |
| Hermes Agent | external execution, native runtime context/files/memory, tools and skills | approval, Evidence admission or Registre Probatoire promotion |
| Pantheon Next | consequential status, contracts, gates, Evidence/approval/Register rules | general agent runtime, provider routing, chat UI, RAG engine or memory engine |
| Pantheon Cockpit | governed product projections, Cards, navigation, review/decision surfaces | general-purpose chat frontend, source store or memory engine |
| Optional workspace binding | human working notes and editable projections when selected | governed Project identity, Evidence or canonical memory |
| Optional synchronization binding | convergence between selected workspace representations | knowledge authority, memory authority or professional approval |
| Optional retrieval / RAG binding | candidate retrieval, ranking and derived context when selected | truth, Evidence or scope authority |
| Optional external-memory binding | additional conversational/workstream recall when selected | truth, Evidence or automatic durable promotion |
| Source/document owners | exact professional source identity and provenance | semantic truth merely because material exists |

One implementation may provide several external functions, but the responsibilities remain separable and replaceable.

## Core invariants

```text
retrieved != truth
memory != Evidence
runtime success != authorization
projection != persistence
folder != governed identity
sync success != professional approval
provider selected != Pantheon dependency
```

## Zero-extra-provider posture

A valid Pantheon deployment may use Hermes without any external workspace, RAG or memory provider when its native capabilities are sufficient.

Current Hermes provides bounded persistent `MEMORY.md` / `USER.md`, session search and project/context-file loading. Those are Hermes runtime facilities, not Pantheon Knowledge or Evidence authority.

```text
Hermes native context/memory sufficient
-> no external provider required
-> Pantheon governance boundaries unchanged
```

External providers are justified only by a demonstrated capability need.

## Selected source/retrieval route and historical references

Pantheon still does not require one particular workspace, synchronization product, RAG stack or memory engine. For the current professional AFFAIRES deployment candidate, however, one productive route has been selected to avoid parallel producers:

```text
NAS / AFFAIRES
  -> Linux-mounted professional source tree
  -> one Workspace indexer / sync producer
  -> Hindsight derived retrieval / document memory
  -> strict project-scoped Hermes / Cockpit consumers
```

This is a target-selection decision, not authority transfer or production adoption.

```text
selected implementation != architecture prerequisite
retrieval provider != source authority
memory != Evidence
folder/path != governed identity
```

The repository also retains historical qualification evidence for:

```text
Obsidian / Markdown
  -> optional human-authored workspace

Self-hosted LiveSync / CouchDB
  -> historical optional synchronization pattern

hindsight-obsidian-sync
  -> historical designated producer for that reference

Hindsight
  -> replaceable derived retrieval / external-memory provider
```

Those historical components may still be chosen when their capabilities are specifically wanted, but they no longer define the productive AFFAIRES topology. A user may also prefer Hermes-native context and memory when those facilities are sufficient.

## RAG posture

Pantheon does not own or require a canonical RAG stack.

The required boundary is narrower:

```text
identified source / scope
-> optional replaceable retrieval implementation
-> candidate context with provenance
-> task reasoning
-> Evidence only through the existing governed path
```

Vector stores, embeddings, rerankers, knowledge graphs and retrieval frameworks remain implementation choices. They must not become project identity, source truth, Evidence or authorization merely because retrieval succeeds.

A task that can be satisfied from explicitly selected source files or Hermes-native context does not need a RAG layer added merely for architectural symmetry.

## Memory posture

Pantheon governs no conversational-memory engine.

Hermes native memory is a valid baseline. An external memory provider may be selected when greater recall, semantic retrieval, sharing or another demonstrated capability is required.

Hindsight is currently a well-qualified candidate in this repository, but it remains replaceable. Mnemosyne and other reviewed providers are historical/candidate alternatives, not parallel mandatory paths.

Workspace-derived retrieval and conversational/workstream memory remain distinct responsibilities even when one provider can implement both. Separation may be expressed through banks, scopes, stores or an equivalent provider-specific mechanism.

```text
same provider != same responsibility
memory recall != source retrieval
memory persistence != Registre Probatoire
```

The existing Pantheon `external_runtime_memory` Capability Binding may remain unbound when Hermes native memory is sufficient.

## Why OpenWebUI and Paperless are absent

Neither product owns a distinct target responsibility anymore.

Hermes-compatible clients already cover runtime interaction, while existing source/document owners cover exact files and provenance. Keeping OpenWebUI or Paperless as target dependencies would create parallel product paths without a demonstrated necessary capability.

Their historical material remains provenance; compatibility code may be removed when no current consumer depends on it.

## Client posture

Hermes client implementations are also replaceable.

The Hermes web/dashboard is the current baseline. A compatible mobile/PWA client can be selected separately when its API compatibility, authentication and deployment boundaries are verified.

```text
client works != client selected
client selected != Pantheon dependency
```

## Coherence criterion

The architecture is coherent when one bounded professional task can:

```text
start from an identified scope/source
-> use only the context/retrieval capability actually needed
-> pass existing Pantheon admission/policy boundaries when consequential
-> execute through Hermes
-> return reviewable candidates/observations
-> preserve Evidence/approval distinctions
-> project status in the Cockpit when useful
-> leave durable governed state only through the existing owner
```

No additional general-purpose frontend, DMS, scheduler, queue, RAG framework, provider router or memory authority is required by Pantheon itself.

## Final rule

```text
Pantheon specifies governance contracts, not a preferred personal knowledge stack.
Hermes native facilities are sufficient when they satisfy the task.
External workspace, retrieval and memory providers stay optional and replaceable.
Sources, retrieved context, memory and Evidence remain distinct.
Remove superseded mandatory paths instead of replacing them with new mandatory products.
```