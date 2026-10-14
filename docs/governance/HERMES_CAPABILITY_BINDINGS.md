# Hermes Capability Bindings

Status: candidate support doctrine — product-specific optional binding registry.

Machine-checkable selection, activation and compatibility relations remain owned by the existing `CapabilityBinding`, `CapabilityActivation` and `CapabilityCompatibilityObservation` contracts.

This document answers one narrow question:

```text
When Hermes needs a capability that its native runtime does not already satisfy,
which external implementations are worth selecting or testing?
```

It does not install, activate, authorize or route providers.

## Core rule

```text
Hermes native capability sufficient
-> use it
-> no external binding required

capability gap demonstrated
-> select one primary external binding for that function
-> qualify it
-> activate only through existing governance
```

```text
reviewed != selected
selected != installed
installed != activated
activated != task-authorized
runtime success != Evidence
provider selected != Pantheon dependency
```

Pantheon should not add a product merely to make the architecture look complete.

## Binding posture

Use `unbound` whenever no external product is required or when the choice is user/profile specific.

Candidate status vocabulary remains:

```text
external_reference
watch
candidate
to_verify
preferred_candidate
fallback_candidate
rejected
superseded
```

Runtime status remains separate from candidate status.

## Current registry

| Capability slot | Current external-binding posture | Notes |
|---|---|---|
| `web_evidence_intake` | `xberg-io/crawlberg` preferred candidate | Public-web intake with provenance; browser/SSRF/antibot boundaries remain relevant. |
| `curated_source_library` | `unbound` | User/profile-specific optional route. Zotero read-only may be enabled by the user as one external implementation; it is not a default Pantheon binding. |
| `academic_source_discovery` | `unbound` | User/profile-specific optional route. Consensus MCP may be enabled by the user as one external implementation; it is not a default Pantheon binding. |
| `external_connector_gateway` | Nango candidate | Optional scoped API connector gateway; credentials and writes remain separately governed. |
| `observability` | Langfuse preferred candidate | Optional Hermes trace/cost/latency visibility; traces are not Evidence or approval. |
| `document_structural_analysis` | Docling preferred candidate | Existing bounded path; extraction is derivative, not source truth. |
| `document_source_management` | `unbound` | Core source/document owners and local/NAS intake do not require a DMS. Paperless is superseded as a target dependency. |
| `knowledge_retrieval_pipeline` | `unbound` | Native bounded retrieval is sufficient on the current measured lexical slice. Haystack 3.1.0 matched native quality in the bounded qualification and remains watch-only; no canonical RAG framework is required. |
| `external_runtime_memory` | `unbound` | Hermes native memory is a valid baseline. Hindsight is the currently recommended external provider because it has the strongest live qualification in this repository. |
| `structural_repo_analysis` | `Lum1104/Understand-Anything` candidate | Useful structural analysis; generated graph remains derivative. |
| `revit_local_adapter` | Pantheon Revit Gate local-plugin candidate | Local sandbox exception; model mutation remains consequential. |
| `agent_artifact_transfer` | `shehryarsaroya/agenttransfer` to verify | Optional transport/handoff capability; receipts are not proof. |
| `bounded_workflow_runtime` | no default binding | LangGraph remains a reference for a demonstrated stateful-workflow gap, not a second runtime. |
| `document_parsing_rag_ingestion` | no integrated-stack adoption | RAGFlow remains reference/watch only because its bundled agents/workflows/memory/UI duplicate replaceable responsibilities. |

## User-enabled source-research options

The source-research skill remains product-agnostic. Product-specific mappings belong here.

For the optional source-research routes above, the preferred control split is:

```text
environment/profile:
user enables neither / one / both optional bindings

task:
Hermes may invoke only enabled + task-permitted routes
when materially useful
```

This is user opt-in, not automatic adoption and not per-task micromanagement by default.

```text
installed != user-enabled
configured != user-enabled
user-enabled != task-permitted
task-permitted != invoked
enabled != automatically used
```

### Zotero

Zotero may satisfy `curated_source_library` when the user wants their curated research library available to Hermes.

Initial posture is read-only. Prefer stable library / collection / item identifiers over filesystem storage paths.

```text
Zotero collection != governed Case identity
item in library != Evidence
attachment present != inspected source
physical storage path != governed identity
```

### Consensus

Consensus MCP may satisfy `academic_source_discovery` when the user wants external academic discovery available to Hermes.

Its results remain discovery material until original sources are inspected where technically available.

```text
Consensus result != inspected source
generated takeaway != source content
ranking != authority
Consensus synthesis != Evidence
```

Environment-level enablement does not authorize disclosure of private or dossier-specific data. Query minimization and Task Contract/data-exposure constraints still apply.

Neither option creates an automatic promotion path:

```text
Consensus discovery
-> optional source_addition_candidate
-> separate human choice / write authorization if retention is desired

Consensus -> Zotero automatic write = forbidden by default
```

## Native Hermes baseline

A valid deployment may keep these optional slots unbound.

Current Hermes provides native facilities including:

```text
project/context files
MEMORY.md / USER.md
session history/search
runtime tools and skills
```

These are Hermes runtime facilities. They are not Pantheon Knowledge, Evidence or Registre Probatoire state merely because they are available or persistent.

```text
native Hermes sufficient != missing architecture layer
```

## External runtime memory

The machine-checkable selection owner remains:

```text
catalog/bindings/external-runtime-memory-unbound.yaml
```

That record is deliberately `unbound`. No external-memory provider is required by Pantheon.

### Recommended external provider: Hindsight

When an external memory/retrieval capability is wanted, Hindsight remains the best-demonstrated replaceable provider in this repository. That recommendation must now distinguish two responsibilities:

```text
professional document retrieval
!= Hermes conversational/workstream memory
```

The selected productive professional-document route is:

```text
NAS / AFFAIRES
-> one standalone Workspace producer
-> Hindsight derived document bank
-> strict project-scoped router
-> bounded Hermes / Cockpit consumers
```

Current repository evidence includes direct source retain through the Workspace producer, source/path provenance, strict `scope:project:*` filtering with `all_strict`, source-grounded chunk results, project isolation checks and bounded Cockpit/Hermes read surfaces. Pantheon-Next#659 still owns live deployment hardening and persistence/recovery qualification.

Earlier Obsidian / LiveSync / CouchDB / `hindsight-obsidian-sync` campaigns remain historical capability evidence. They no longer define the productive AFFAIRES materialization or ingestion topology.

Using Hindsight for professional document retrieval does **not** bind the generic `external_runtime_memory` capability automatically. Hermes native memory remains a valid baseline for conversational/workstream continuity, and that machine-checkable binding remains deliberately `unbound` unless a separate decision selects an external runtime-memory provider.

```text
Hindsight document recall != source truth
Hindsight memory != Evidence
document-retrieval provider selected != runtime-memory binding selected
provider selected != authority transfer
```

### Hermes-native alternative

An external provider is not required when native Hermes memory/context satisfies the user.

```text
Hermes native memory/context
= valid zero-extra-provider option
= external_runtime_memory remains unbound
```

This is not a downgrade of the Hindsight qualification. It is the simpler valid path for users who do not need the extra workspace/retrieval behavior.

### Other providers

Mnemosyne has historical proof of cross-session Hermes recall. Mem0, Honcho, OpenViking, Holographic, RetainDB, ByteRover, Supermemory and other providers may be reconsidered when they solve a demonstrated need better.

They are not parallel active recommendations.

```text
historically qualified != current default recommendation
new provider != new Pantheon subsystem
```

Detailed historical provider results remain in dated qualification logs/reference reviews rather than being promoted into permanent architecture.

## Workspace and retrieval

Pantheon does not define a mandatory note application or RAG topology.

The selected productive professional-source path is filesystem-native:

```text
NAS / AFFAIRES
-> Linux-mounted admitted project root
-> one Workspace indexer / sync producer
-> Hindsight derived retrieval
-> project-scoped bounded consumers
```

Cartouches are optional descriptive enrichment. Supported sources do not require one for the normal source route, and no folder, filename, cartouche or Hindsight bank becomes governed Project identity by implication.

Obsidian, Self-hosted LiveSync, CouchDB and `hindsight-obsidian-sync` remain historically qualified optional workspace/synchronization patterns. They may still be useful when a human-authored Markdown workspace is actually wanted, but they are not the selected AFFAIRES route.

A minimal deployment may still use only:

```text
Hermes project/context files
+ explicitly selected source files/folders
+ Hermes native memory/session search
```

All valid replacements preserve the same invariants:

```text
folder != governed identity
retrieval result != truth
sync success != approval
memory != Evidence
projection != persistence
```

## RAG posture

Pantheon does not require a canonical RAG framework.

```text
identified source / scope
-> optional retrieval implementation
-> candidate context with provenance
-> reasoning
-> Evidence only through the existing governed path
```

Embeddings, vector stores, rerankers, graphs and retrieval frameworks remain implementation choices. A task that can be satisfied by Hermes-native context or direct bounded source access does not need an extra RAG layer.

The 2026-09-01 bounded Haystack qualification measured no lexical retrieval-quality gain over the current native path, so Haystack remains watch-only and `knowledge_retrieval_pipeline` stays unbound. Hindsight remains the best-demonstrated external memory/workspace retrieval composition in this repository; LlamaIndex and selected LangChain components remain replaceable watch candidates rather than Pantheon dependencies.

## Document source management

Paperless no longer has a preferred binding role.

Existing source/document owners already preserve professional provenance and bounded local/NAS intake. A DMS may be selected later only for a concrete operational gap such as scanning intake, retention workflow or specialized version-management UX.

Any such DMS remains a replaceable backing/source adapter, never Pantheon classification, Knowledge or Evidence authority.

## Selection criteria

Select an external binding only when at least one concrete need exists:

- native Hermes capability is insufficient;
- required retrieval quality or scale is demonstrated;
- a specific external integration is needed;
- isolation, sharing or persistence requirements exceed native behavior;
- professional workflow requires a specialized replaceable adapter.

Prefer the candidate that:

- has current evidence in the repository;
- adds the least overlapping runtime surface;
- preserves provenance and scope;
- can be removed without migrating Pantheon governance state;
- fails closed around consequential operations.

## Replacement rule

An external binding may be replaced when another implementation satisfies the same capability contract better.

Replacement does not transfer authority and does not retroactively approve the new provider.

```text
provider implementation changes
!= Pantheon governance owner changes
```

## Final rule

```text
Use native Hermes memory when sufficient.
For productive AFFAIRES document retrieval, use the selected direct NAS / Workspace / Hindsight route until a demonstrated need justifies replacement.
Treat Obsidian / LiveSync / CouchDB as historical qualified optional tooling, not the productive AFFAIRES default.
Keep every external provider optional and replaceable.
Pantheon governs the boundary, not the product choice.
```