# Hermes Knowledge Retrieval Binding

Status: candidate support doctrine — native path sufficient on the measured slice; external binding remains unbound.

## Purpose

Define a bounded candidate Capability Slot for retrieval over already-admitted or already-extracted governed material without coupling Pantheon to a specific retrieval framework.

This document does not install Haystack, LlamaIndex, LangChain, Langflow, RAGFlow or any vector database. It does not create a RAG runtime, memory engine, evidence engine, provider router, queue, scheduler, plugin manager or approval system.

## Boundary

```text
exposed_by: OpenWebUI or another cockpit may show binding and lifecycle state.
executed_by: Hermes or a reviewed external retrieval adapter.
governed_by: Pantheon governs corpus/scope legitimacy, binding status, lifecycle state, evidence expectations and consequential gates.
approved_by: human where installation, sensitive corpus access, activation or consequential downstream effects require it.
forbidden: retrieval output treated as truth, Evidence admission, canonical memory, automatic approval or unrestricted corpus access.
```

## Capability Slot

```text
capability_id: knowledge_retrieval_pipeline
function: scoped retrieval, filtering, ranking/reranking and provenance-linked context assembly over governed material
owner_layer: execution_runtime
executed_by: Hermes / reviewed retrieval adapter
governed_by: Pantheon
binding_status: unbound
preferred_binding: unbound
candidate_bindings: none selected
watchlist_bindings: Haystack, LlamaIndex, selected LangChain components
rejected_default_bindings: Langflow runtime, LangGraph runtime, RAGFlow integrated platform
install_status: absent / not established
health_status: unknown
update_status: unknown
activation_status: unavailable
rollback_status: not_applicable until installation
```

## Why this slot is distinct

The capability is defined without naming a product and remains useful if every current framework is replaced.

```text
document source management
!= document structural analysis
!= document OCR
!= knowledge retrieval
!= evidence qualification
!= memory promotion
```

A document may already be extracted and governed while still requiring retrieval, metadata filtering, ranking, reranking or context assembly for a specific task. Conversely, a parsing/ingestion product may provide retrieval as part of an integrated stack without becoming the only possible implementation of retrieval.

Therefore `knowledge_retrieval_pipeline` is a smaller replaceable capability than an integrated document/RAG platform.

## Allowed effects

```text
read governed corpus references within declared scope
query already-authorized indexes / stores
apply project, dossier, source and metadata filters
retrieve candidate passages or records
rank / rerank retrieved candidates
assemble provenance-linked context
report retrieval limitations and capability gaps
return Result Candidate / Evidence Pack Candidate inputs
```

## Forbidden effects

```text
expand corpus scope by inference
crawl undeclared sources
promote retrieved material to Evidence automatically
promote retrieval output to canonical memory
claim professional truth from retrieval score
approve a Result Candidate
send or mutate external systems merely because retrieval succeeded
silently switch to another corpus or binding
select a model or provider for Pantheon
become a second agent runtime beside Hermes
```

## Candidate bindings

### Haystack

Posture after bounded qualification:

```text
binding_status: watch
preferred: no
installation: not established
health: qualification-lab only
activation: unavailable
```

Reason for continued watch status: Haystack provides modular retrieval, context-engineering, ranking/reranking and pipeline components that may become useful if a concrete gap appears. Product breadth is not itself a reason to adopt it.

Observed qualification on 2026-09-01, using the exact pin recorded in `implementation/qualification/external-pins.json` and the lab under `implementation/labs/haystack_retrieval/`:

```text
bounded scope/provenance lab                  = passed
out-of-scope / stale / revoke fail-closed     = passed
applicable labelled lexical cases             = 6
native expected source at rank 1              = 6/6
Haystack expected source at rank 1            = 6/6
native long-request admitted-source coverage  = 3/3
Haystack long-request admitted-source coverage= 3/3
measured retrieval-quality gain               = none
binding selected                              = no
```

The lab also observed a small CI-local latency difference in favor of the in-memory Haystack path. That observation is not deployment-performance evidence: Haystack used `InMemoryDocumentStore`, while the native lane crossed PostgreSQL, and persistence/restart/resource costs were intentionally outside the slice.

Decision:

```text
current native bounded lexical retrieval is sufficient for the measured need
-> keep knowledge_retrieval_pipeline unbound
-> do not expose Haystack's framework/agent control surface to Hermes
-> retain Haystack on watch only for a later demonstrated capability gap
```

A generic Hermes retrieval handoff remains a separate integration question. It should be implemented only when a concrete retrieval need requires it and should expose one provider-neutral bounded contract regardless of the underlying implementation. The absence of such a handoff is not a reason to select Haystack.

Primary review risks if Haystack is reconsidered:

```text
index or document-store scope broader than Task Contract
external embedding/generation provider leakage
pipeline state confused with Pantheon state
retrieval score treated as evidence quality
agent/tool features expanding beyond the retrieval slot
framework dependency adopted by implication
```

Any future Haystack binding must expose one retrieval contract, not the whole framework control surface.

### LlamaIndex

```text
binding_status: watch / compare
```

Evaluate when a concrete retrieval vertical requires comparison of indexing, metadata filtering, retrieval composition, local deployment or document-store integration.

Only the required packages and components should be installed inside the adapter. LlamaIndex agents, workflow state and memory are outside this slot.

### LangChain

```text
binding_status: watch / compare
```

LangChain is broader than this slot. Selected core, loader, splitter, retriever or Docling-integration packages may be used inside a bounded adapter, but LangChain must not become the default provider abstraction, tool registry, agent runtime, prompt authority or memory layer.

```text
component reused != framework adopted
library present != runtime selected
```

## Relationship to Docling

Docling belongs primarily to `document_structural_analysis`.

```text
Docling
  exact source -> structured derivative

knowledge_retrieval_pipeline
  governed derivative/corpus -> scoped retrieved candidates
```

Docling may expose optional chunking or retrieval helpers, but those features do not collapse extraction, retrieval and Evidence qualification into one slot.

## Relationship to RAGFlow

RAGFlow is retained as an integrated external RAG product reference, not the preferred binding for this narrow slot.

Its parser, retrieval, model, agent, workflow, memory, MCP and UI surfaces overlap several independently replaceable responsibilities:

```text
document structural analysis
knowledge retrieval
agent runtime
memory
workflow runtime
user interface
```

A future benchmark may show that RAGFlow performs one function well. That function must still be exposed through the relevant Capability Slot rather than adopting the whole platform by implication.

```text
integrated platform available != integrated platform adopted
RAGFlow result != Evidence
RAGFlow agent success != Pantheon authorization
```

## Relationship to Langflow

Langflow is suitable as a visual prototype laboratory only.

A prototype may be exported or exposed to Hermes as one bounded tool with declared inputs, outputs and effects. Langflow must not remain a hidden second orchestrator, model router, memory owner or approval surface in the production path.

```text
visual flow != governed workflow
flow deployed != task authorized
```

## Relationship to LangGraph

LangGraph retains its `bounded_workflow_runtime` placement and is refused as a default Pantheon or Hermes runtime.

A specialized existing LangGraph application may be called behind one capability contract only when a demonstrated stateful-workflow gap cannot be solved more simply by Hermes and a bounded adapter.

```text
retrieval state != workflow authority
workflow checkpoint != Evidence
human-in-the-loop node != Pantheon approval
runtime success != approval
```

## Evidence posture

Retrieval produces candidates and provenance links, not Evidence admission.

Minimum useful return shape:

```text
query_ref
scope_ref
corpus_ref
binding_ref
binding_version
retrieved_items[]
source_refs[]
ranking_method
reranking_method
filters_applied[]
known_limits[]
produced_at
```

The downstream Evidence gate decides whether cited source material is admissible for the professional claim at hand.

## Lifecycle posture

```text
candidate binding
-> installation proposal
-> approved_for_sandbox where required
-> installed by Hermes/operator
-> health observed
-> benchmarked on synthetic or authorized corpus
-> scoped activation
-> task authorization remains separate
```

```text
installed != approved
healthy != safe
benchmark_pass != production adoption
binding_selected != dependency_adopted
activation != task_authorization
retrieved != evidence
```

## MVP boundary

The bounded Haystack lab is implemented only as qualification evidence. It does not alter the product retrieval owner, create an activated CapabilityBinding or justify a `pantheon-mvp` dependency.

The measured slice currently supports the simpler outcome:

```text
Pantheon native bounded retrieval
-> sufficient for the tested lexical need
-> external knowledge_retrieval_pipeline binding remains unbound
```

A future product vertical is justified only after a concrete gap is demonstrated, for example a required retrieval/reranking quality improvement that the native path does not provide. Any such vertical must preserve the provider-neutral boundary:

```text
already-extracted governed project corpus
-> exact scoped retrieval contract
-> optional replaceable implementation
-> Hermes candidate answer
-> provenance-linked Evidence Pack Candidate
-> human review
```

Until such a gap exists, adding a provider-specific Hermes search surface, second store or broader RAG runtime would be unnecessary duplication.
