# RAG Ingestion and Evidence Boundaries

Status: active support doctrine — retrieval/evidence boundary owner.

This document answers one question:

```text
When material has been converted, indexed and retrieved, what has actually been established?
```

It does not select a RAG framework, workspace, vector store, memory provider, client UI or ingestion runtime.

## Core boundary

```text
source can become retrievable
retrieved material can become an Evidence Candidate
Evidence Candidate becomes Evidence only through governed selection
Evidence supports a consequential output only through existing Evidence/approval owners
```

None of these transitions creates truth, approval or Registre Probatoire state automatically.

## Governed chain

```text
Raw Source
-> Source Reference
-> Ingestion / Derivation Candidate
-> Knowledge or retrieval representation
-> Retrieval Unit
-> Retrieved Context
-> Context Sufficiency Check
-> Evidence Candidate
-> Evidence Item
-> Evidence Pack
-> Output Candidate
-> Approval Event when required
-> optional Register Candidate
-> Registre Probatoire entry only after governed promotion
```

Forbidden shortcuts:

```text
uploaded -> validated
converted -> approved
chunked -> Evidence
indexed -> Evidence
retrieved -> truth
citation displayed -> proof
score passed -> approval
benchmark passed -> professional validation
memory -> Evidence
```

## Provider independence

The same boundary applies whether retrieval comes from:

- direct Hermes source/context access;
- the co-located PostgreSQL/pgvector candidate;
- the qualified Obsidian/Hindsight reference composition;
- another selected retrieval engine.

```text
provider changes
!= Evidence rules change
```

Pantheon does not need to know which retrieval product is fashionable. It must know what source/scope/provenance supports a consequential claim.

## Minimum expectations for retrieval-backed consequential output

Where relevant, expose enough information to review:

```text
source identity
source version/date/digest when available
scope
source locator or page/section
retrieval method when material
retrieval limitations
context sufficiency
selected Evidence Items
source conflicts
unanswerable / insufficient-evidence status
approval status when required
```

A single retrieved chunk is insufficient when the claim depends on several pages, a table/chart/image, conflicting sources, freshness, professional judgment or a broader user-defined document boundary.

## Chunking fitness

Chunking fitness means a strategy was evaluated for a defined corpus/task.

It does not establish:

```text
answer correctness
source reliability
professional validation
global superiority of one chunker
```

A chunking benchmark remains a technical observation.

## Long-document and multimodal evidence

Professional documents may require:

- page-level or range-level grounding;
- table/chart/image/figure localization;
- cross-page reasoning;
- conflict markers;
- OCR/layout/table quality flags;
- explicit unanswerable cases.

A fluent answer is not sufficient when the supporting source cannot be localized and reviewed.

## Context sufficiency

Before consequential use, a retrieval path should be able to expose whether context appears:

- sufficiently complete;
- fresh enough for the task;
- adequately sourced;
- invalidated by a newer source or instruction;
- internally conflicting;
- insufficient and requiring escalation.

Context sufficiency is a status signal, not approval.

## Hermes boundary

Hermes may execute bounded conversion, retrieval, ranking, synthesis and Evidence-Candidate preparation.

Hermes must not turn:

- retrieval success into truth;
- benchmark success into professional validation;
- memory recall into Evidence;
- source availability into task authorization;
- a generated citation into proof by itself.

## Pantheon boundary

Pantheon governs the consequential boundary:

- governed scope/identity;
- Task Contracts and admission;
- Evidence status;
- approval status;
- Register promotion;
- User Decision Gates.

Pantheon does not need to own parsing, embeddings, vector search, reranking or memory-provider internals.

## User Decision Gate triggers

Escalation is appropriate when, for example:

- retrieval is partial for a cross-page claim;
- the dossier probably cannot answer the question;
- sources materially conflict;
- a private/professional source would cross a new external boundary;
- a technical score is being used as if it were approval;
- the output has material legal, contractual, financial, safety or professional effect.

## Relationship to source and retrieval owners

`SOURCE_INGESTION_RETRIEVAL_MODEL.md` owns the provider-agnostic source-access, derivation, scope, provenance and retrieval-progression doctrine.

`SOURCE_RETRIEVAL_IMPLEMENTATION_COVERAGE.md` is the descriptive inventory for observed implementation coverage; it does not create doctrine or adoption.

The retained `RAG_INGESTION_PIPELINE.md` path is only a compatibility/profile pointer and owns no independent doctrine.

This document owns only the interpretation after/around retrieval:

```text
ingestion quality
+ retrieval fitness
+ context sufficiency
!= Evidence or approval by themselves
```

## Final rule

```text
Make retrieval replaceable.
Keep provenance reviewable.
Treat retrieved context as candidate support.
Use existing Evidence and approval owners for consequential claims.
```
