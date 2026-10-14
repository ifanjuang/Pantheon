# Source and Retrieval Implementation Coverage

Status: candidate support note — descriptive inventory, no doctrine change.
Observed repositories:

```text
Pantheon-Next: main at fde7e856cd04c56e718d2bb133e65262c80d5d52
pantheon-mvp: main at 666bd32301f5ffd247756f4a859bf1667d884fb6
observation date: 2026-08-07
```

## Purpose

Record the current coverage between the governed source/retrieval model and the external candidate implementation without creating a new `Knowledge Pipeline`, runtime, connector framework, memory engine or authority layer.

The existing owners remain:

```text
SOURCE_INGESTION_RETRIEVAL_MODEL.md
HERMES_KNOWLEDGE_RETRIEVAL_BINDING.md
RAW_DERIVED_GOVERNED_RECORDS.md
EVIDENCE_PACK.md
ANSWER_VERIFICATION_GATE.md
NON_EQUIVALENCE_RULES.md
```

This inventory is observational. Repository code remains authoritative for implementation state and the governance corpus remains authoritative for doctrine.

## Executive conclusion

The ecosystem already covers the architecture commonly presented as:

```text
source
→ extraction
→ chunks
→ embeddings
→ vector retrieval
→ lexical retrieval
→ hybrid fusion
→ candidate generation
```

It covers it through separated responsibilities rather than one adopted RAG product:

```text
Pantheon Next governs scope, provenance, status, Evidence boundaries and gates.
pantheon-mvp implements bounded candidate persistence, extraction, retrieval and projections.
Hermes remains the intended external executor and binding host.
Cockpit / OpenWebUI expose projections and review surfaces.
The human decides consequential reliance and promotion.
```

No new top-level abstraction is required merely to describe this path.

## Coverage matrix

### 1. Source declaration and scope

Governance posture:

```text
source access is bounded by Case, Situation, scope and confidentiality;
linked, cached and ingested are operational postures, not authority levels;
Source != Evidence.
```

Observed candidate implementation:

```text
implemented:
- Task Contract loading and validation;
- ingestion limited to explicitly declared sources;
- source-path perimeter checks before database mutation;
- dossier and contract identity retained on chunks;
- optional NAS-mounted document intake;
- source digest and version records.
```

Coverage: `implemented candidate`.

### 2. Original and derived representations

Governance posture:

```text
original source remains superior to OCR, extracted text, Markdown, chunks and embeddings;
derivatives retain method, version, source location and inherited scope;
extraction success != source truth.
```

Observed candidate implementation:

```text
implemented:
- source_documents;
- document_versions;
- extraction_runs;
- extraction_observations;
- document_extraction_bindings;
- source and configuration digests;
- converter identity and version;
- Markdown and structured JSON outputs;
- quality flags and review status;
- optional Docling Serve binding.
```

Coverage: `implemented candidate`, with live binding still deployment-dependent.

### 3. Chunking and structural provenance

Governance posture:

```text
chunk set is a derived representation;
chunk != source;
chunk != Evidence.
```

Observed candidate implementation:

```text
implemented:
- bounded text chunking;
- structured extraction compilation;
- source reference and chunk ordinal;
- source digest;
- page range where available;
- structural locator;
- parent heading and section path;
- quality flags.
```

Coverage: `implemented candidate`.

### 4. Embeddings and vector persistence

Governance posture:

```text
vectorization is selective;
embedding != memory;
vector store availability != adoption.
```

Observed candidate implementation:

```text
implemented:
- deterministic embedding seam;
- PostgreSQL vector extension;
- vector column on bounded chunks;
- pgvector-backed candidate retrieval.

current limitation:
- the active embedder is deterministic local feature hashing;
- it proves the replaceable vector path and zero-exposure test seam;
- it does not establish production semantic quality;
- no production embedding provider or model is adopted.
```

Coverage: `implemented candidate` for the bounded vector path, not an adopted semantic embedding service.

```text
vector path implemented != semantic quality established
placeholder available != production binding selected
embedding available != data exposure approved
```

### 5. Scope-first vector retrieval

Governance posture:

```text
scope and confidentiality filters precede retrieval;
retrieval returns source-linked candidates;
retrieved != true.
```

Observed candidate implementation:

```text
implemented:
- SQL perimeter filtering before vector ranking;
- retrieval limited to the Task Contract dossier and declared sources;
- distance returned with each candidate chunk;
- Retrieval Trace URI;
- contract, ingestion and source audit identity;
- structural provenance returned separately from ranking.
```

Coverage: `implemented candidate`.

The current code names this branch `semantic` in hybrid metrics. That label identifies the vector branch; it does not upgrade the placeholder embedder into a production semantic binding.

### 6. Keyword and hybrid retrieval

Governance posture:

```text
structured identifiers and native search should be preferred where available;
full-text search precedes or complements vector retrieval;
ranking and reranking remain replaceable execution capabilities.
```

Observed candidate implementation:

```text
implemented:
- PostgreSQL full-text query path with websearch_to_tsquery('simple', query);
- to_tsvector('simple', body) matching and ts_rank_cd ordering;
- Task Contract dossier and declared-source filters before lexical ranking;
- deterministic lexical tie-breaking by source and chunk;
- deterministic weighted Reciprocal Rank Fusion;
- configurable candidate_k, top_k, rrf_k and branch weights;
- vector rank, lexical rank and fused score retained separately;
- hybrid retrieval connected to the candidate runner;
- small labelled métier relevance set merged through pantheon-mvp PR #256;
- six exact queries with expected source rank and two observation-only limits;
- planted undeclared-source and other-dossier markers for both retrieval paths.

not established:
- French accent, morphology and domain-synonym quality beyond that fixture;
- independent reranking binding;
- production comparison across embedding or search bindings.
```

Coverage: `implemented candidate` for lexical retrieval, weighted hybrid RRF and the bounded métier acceptance set; broader relevance quality and reranking remain to verify separately.

Current defaults:

```text
rrf_k = 60
vector branch weight = 1.0
lexical branch weight = 1.0
```

```text
hybrid score != confidence
hybrid score != Evidence quality
hybrid result != truth
```

### 7. Candidate generation and refusal

Governance posture:

```text
retrieval output may inform a Result Candidate or Evidence Pack Candidate;
runtime success != Evidence;
result candidate != approved result.
```

Observed candidate implementation:

```text
implemented:
- bounded question runner;
- deterministic candidate and refusal paths;
- candidate YAML stream;
- refusal when scope or contract conditions are not met;
- source-linked retrieval traces in candidate material.
```

Coverage: `implemented candidate`.

### 8. Verification and Evidence boundary

Governance posture:

```text
retrieval result
→ deliberate selection for a scoped assertion
→ Evidence Candidate
→ gate or human decision where consequential.
```

Observed candidate implementation:

```text
implemented candidate:
- terminal human decision stand-in;
- explicit approve, refuse, request revision and request more evidence outcomes;
- human identity required;
- separate Register Candidate proposal;
- explicit retention authorization required;
- no automatic durable promotion.

not established as adopted integration:
- live Pantheon Evidence admission service;
- adopted answer-verification gate endpoint;
- end-to-end Hermes handoff under an activated Capability Slot.
```

Coverage: `implemented stand-in / partial integration`.

The currently qualified Hermes `0.20.0` laboratory surface contains only:

```text
pantheon_context_manifest
pantheon_context_entity
```

The real agency/NAS acceptance remains open in `pantheon-mvp` issue #227. A bounded `pantheon_context_search` tool may be specified only after that two-tool baseline is accepted on the real target and must resolve its perimeter from the admission and Task Contract.

### 9. Knowledge and document projections

Governance posture:

```text
Cockpit cards are projections;
UI state != authorization;
server contracts remain authoritative.
```

Observed candidate implementation:

```text
implemented:
- Project Document projection;
- Knowledge item persistence;
- source-chunk links;
- review statuses;
- append-only Knowledge events;
- optimistic version checks and idempotency fields;
- Hermes edit-request seam;
- Cockpit APIs and schema-driven card surfaces.
```

Coverage: `implemented candidate`.

### 10. External adapters

Governance posture:

```text
adapter available != source of truth;
installed != approved;
healthy != safe;
activated != task authorized.
```

Observed candidate implementation:

```text
implemented or declared as optional candidate seams:
- Docling;
- Paperless;
- OpenWebUI;
- read-only mounted document root.

not established:
- generic connector framework;
- live Google Drive ingestion;
- generic multi-source retrieval resolver;
- production source cockpit;
- adopted Hermes retrieval binding.
```

Coverage: `specific optional adapters`, not a generic integration platform.

## What already exists

The following must not be proposed as new concepts:

```text
source identity and access posture;
derived representation candidate;
retrieval trace;
Evidence Candidate boundary;
Capability Slot for knowledge retrieval;
Result Candidate and refusal path;
Knowledge projection;
human decision gate;
Register Candidate promotion boundary;
PostgreSQL lexical retrieval path;
weighted hybrid RRF path.
```

## Confirmed gaps

The current review identifies five concrete gaps worth treating separately:

```text
1. broader representative relevance evaluation only when the current fixture is insufficient;
2. production semantic embedding binding and its data-exposure decision;
3. optional reranking binding, only if measured relevance requires it;
4. adopted Hermes handoff for knowledge_retrieval_pipeline;
5. conformance evidence linking MVP outputs to active Pantheon schemas and gates.
```

The first three are execution-quality or replaceable binding questions. The fourth is an integration boundary. The fifth is verification evidence. None requires a new authority object.

## Recommended sequence

```text
A. Preserve current concepts and owners.
B. Maintain the merged bounded métier set as executable acceptance evidence.
C. Separate required scope/provenance invariants from observed relevance quality.
D. Correct only defects demonstrated by those cases.
E. Complete Hermes 0.20.0 agency/NAS acceptance Pantheon-Next#227 with the current two-tool surface.
F. Specify and test pantheon_context_search against the existing Capability Slot.
G. Benchmark a production embedding, reranker or PostgreSQL extension only if measured results require it.
H. Update this inventory from verified code and CI evidence.
```

Initial required invariants for the métier set:

```text
zero result outside the Task Contract dossier and declared sources;
contract, ingestion and source provenance retained;
deterministic fused ordering;
no duplicate candidate after fusion.
```

Initial quality observations:

```text
expected source rank for exact technical queries;
French accent and morphology behaviour;
semantic-paraphrase limitation of the placeholder;
no production threshold inferred from fixture results.
```

`ranx` or `ir_measures` may later be used as development-only metric libraries when the labelled set is large enough to justify MRR, nDCG or statistical comparison. They are not production runtime dependencies.

## External reference posture

```text
pgvector / pgvector-python
  current implementation reference for PostgreSQL hybrid retrieval and optional
  cross-encoder reranking.

Vespa rag-blueprint
  methodology reference for labelled queries and retrieval/ranking evaluation;
  not a selected engine.

ranx / ir_measures
  optional development-only metric and fusion comparison tools.

ParadeDB
  watch candidate if native PostgreSQL full-text quality or performance becomes
  a measured limitation; no installation or AGPL adoption decision is made.

Qdrant, Weaviate, OpenSearch and Elasticsearch
  useful implementation references; no second store or search service is
  justified by the current evidence.
```

## Non-goals

This inventory does not authorize:

```text
Pantheon becoming a RAG runtime;
Pantheon hosting embeddings or vector search as a doctrine requirement;
Hermes owning PostgreSQL, indexes or production ranking policy;
MCP retrieving private project documents;
adoption of LangChain, Haystack, LlamaIndex, RAGFlow, ParadeDB or another search engine;
a generic connector manager;
a memory engine;
a provider router;
a scheduler or queue;
automatic Evidence admission;
automatic approval or durable promotion;
automatic tuning of production retrieval weights;
external embedding calls without a reviewed data-exposure decision.
```

## Invariants

```text
coverage documented != adoption
implemented vector path != semantic quality
implemented candidate != activated capability
retrieval score != evidence quality
hybrid retrieval != truth
source projection != source authority
successful extraction != verified content
Cockpit display != authorization
Hermes execution != Pantheon decision
benchmark passed != production adoption
```
