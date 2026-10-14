# Governed Document Lifecycle

Status: candidate support doctrine — documented non-implemented.
Boundary profile: candidate_support_note.

This document composes the current source, document, Knowledge, retrieval, Evidence and external-execution owners into one lifecycle view.

It does not create a second document schema, storage model, OCR pipeline, parser, vector database, scheduler, queue, worker, Hermes Skill, client runtime, approval engine or memory engine.

Current machine-readable document/Knowledge record shapes remain owned by `schemas/document_knowledge_slice.schema.yaml` and `DOCUMENT_KNOWLEDGE_SLICE_CONTRACT.md`.

```text
compatible clients capture runtime-facing intent and interaction
Pantheon Cockpit/Cards expose governed projections
external runtimes execute admitted capabilities
Pantheon governs scope, status, provenance and consequential admission
the human decides where a gate requires it
```

## Purpose

The lifecycle answers a bounded set of questions without collapsing source, derivative, Knowledge, retrieval and Evidence into one object:

```text
What source was received or referenced?
What exact version/hash does processing refer to?
What did the user ask to do?
What derived representations were produced?
Which project or Knowledge relationship was proposed or recorded?
What runtime observations exist?
Which projection is active?
What was indexed and in which scope?
What may be retrieved, revoked, reprocessed or superseded?
What Evidence or human decision is still required?
```

Core non-equivalences:

```text
source received != source accepted
source reference != permission
source captured != document classified
user intent != authorized action
runtime interpretation != approved classification
extraction completed != content validated
OCR completed != transcription validated
Markdown generated != source
summary generated != Evidence
Document Card != source
project relationship != Knowledge publication
Knowledge publication != Evidence admission
projection active != index publication authorized
indexed != retrievable in every scope
retrieved != truth
runtime success != authorization
projection != persistence
```

## Ownership and composition

This lifecycle composes existing owners rather than redefining them:

- `DOCUMENT_KNOWLEDGE_SLICE_CONTRACT.md` and `schemas/document_knowledge_slice.schema.yaml` — source document, extraction, document structure, chunks, Project Document Card, Knowledge publication and version-event contract;
- `SOURCE_INGESTION_RETRIEVAL_MODEL.md` — linked/cached/ingested source access, derived representations, retrieval traces and Retrieval -> Evidence Candidate boundary;
- `RAW_DERIVED_GOVERNED_RECORDS.md` — raw/derived/governed/retrieval/provenance/Evidence/approval layers;
- `RAG_INGESTION_PIPELINE.md` and `RAG_INGESTION_AND_EVIDENCE_BOUNDARIES.md` — provider-agnostic ingestion/retrieval boundaries;
- `HERMES_INTEGRATION.md` — bounded external execution;
- `TASK_CONTRACTS.md` and `EXTERNAL_TOOLS_POLICY.md` — scope and capability/tool admission;
- `EVIDENCE_PACK.md` and `EVIDENCE_TOPOLOGY.md` — reviewable proof-chain semantics;
- `APPROVALS.md` and `USER_DECISION_GATE.md` — consequential gates;
- `MEMORY.md` — durable retention boundary;
- Cockpit/Card owners — governed projection only.

If machine-readable structure and this document disagree, the current schema owns field shape while this document owns lifecycle composition semantics.

## Lifecycle objects

The lifecycle may use the following conceptual objects around the schema-owned record families:

```text
Source Origin
Source Capture or exact Source Reference
Intake Intent
Intake Brief Candidate
schema-owned Source Document
schema-owned Extraction Observation
schema-owned Document Structure
schema-owned Chunk set
schema-owned Project Document Card
schema-owned Knowledge Publication
Pipeline/Execution Observation
Projection
Index Publication
Retrieval Trace
Processing Attestation
Evidence Candidate / Evidence Item
Approval or User Decision Gate record
```

Conceptual lifecycle names do not authorize new persisted entities. Before implementation adds a record family, reconcile it against current schemas and implementation modules to avoid a parallel object model.

## Source origin and exact source identity

A source may originate from an upload, local/NAS reference, email/attachment, URL, Drive/repository reference, approved connector or another explicitly admitted source system.

The origin is not the source truth and may change or disappear.

At minimum, processing should be tied to an exact source identity using the strongest available combination of:

```text
stable source/document identifier
source system or root
relative/stable reference
content digest
media type
version or modification marker
observed/captured time
scope and confidentiality
```

```text
same URL != same content
same filename != same source
external location != immutable source identity
Markdown derivative != original source
```

Where the active contract uses a caller-controlled original plus exact reference/digest, this lifecycle must not invent a mandatory duplicate immutable byte store.

## Intake intent

Intake Intent records what the user or caller is trying to achieve before external processing is interpreted as authorization.

Useful intent context may include:

- requested outcome;
- selected project/scope;
- selected Knowledge family where applicable;
- current query or task;
- explicitly selected source/context references;
- requested operations;
- caller identity and time.

A client may make this interaction simple. Client UX does not redefine the persisted contract.

```text
free-form request != execution contract
selected context != authority expansion
client action != persistence effect
```

## Intake Brief Candidate

For ambiguous or consequential intake, an external runtime may return a bounded reformulation before processing:

```text
understood subject
proposed destination
proposed processing profile/operations
uncertainties
verification points
scope/capability gaps
required confirmation posture
```

The brief is a candidate interpretation.

```text
runtime understood subject != source assertion
proposed destination != approved classification
proposed operation != authorized capability
brief accepted != professional validation
```

A direct path may omit a separate brief when user intent and policy already make destination/operations unambiguous. Simplicity must not remove required scope or approval gates.

## Entry modes

The same source boundary may support:

### Unclassified intake

```text
source/ref
-> bounded source identity
-> unclassified candidate
-> interpretation/classification when useful
```

### Project-targeted intake

```text
source/ref
-> document contract
-> explicit project relationship
-> project-scoped Document Card projection
```

A user's explicit project choice may satisfy the classification choice itself. A second confirmation is required only when another policy/gate requires it.

### Knowledge-targeted intake

```text
source/ref
-> derived document structure/chunks as needed
-> Knowledge Publication candidate
-> visible review state
```

Initial generated Knowledge may remain `generated_unreviewed` where the active schema permits it. That is not Evidence admission.

### Project and reusable Knowledge

The same source may participate in project and reusable Knowledge contexts without binary duplication of the original.

```text
one source identity
-> project/document relationship(s)
-> reusable Knowledge publication(s)
```

Each relationship inherits its own scope/access consequences.

## Document structure and derivation

The active machine contract requires a document structure before chunks. Preserve source-located native units/fragments before task- or model-specific chunking.

Derived representations may include:

```text
direct extracted text
OCR text
layout/structure candidate
raw Markdown
normalized Markdown
metadata candidate
summary candidate
chunk set
embedding/index reference
```

Every derivative should preserve method/version and source locality where meaningful.

```text
OCR != truth
normalized Markdown != original
summary != Evidence
fragment qualification != governed project fact
chunk != Evidence
embedding != provenance
```

Prefer native extraction when it is sufficient. Use OCR/visual processing only when required and admitted; availability alone is not justification.

## Project Document Card

The schema-owned Project Document Card is a projection of one document in one project context.

It remains non-authoritative through the closed authority flags in the machine contract.

```text
Card != source
Card != internal fragment
Card != Evidence
Card visible != persisted truth
```

A source or document may have broader relationships than the current Card projection. Projection context does not narrow or broaden underlying authority by itself.

## Knowledge publication

Knowledge publication creates reusable editorial Knowledge from attributable source material. It does not mutate or replace the original source.

The current machine contract owns:

- Knowledge identifier;
- document/chunk references;
- family;
- Markdown digest;
- review status;
- version/timestamps;
- closed non-Evidence/non-memory/non-doctrine authority block.

```text
generated_unreviewed != reviewed
reviewed != Evidence
reviewed != governed memory
Knowledge visibility != source download permission
```

Source download/opening remains subject to the source's own access policy even when a derived Knowledge projection is visible.

## External execution boundary

External runtimes may perform admitted operations such as source inspection, extraction, OCR, layout analysis, conversion, metadata extraction, summarization, chunking, embedding and retrieval.

No particular runtime-side Skill name or provider binding is canonical here.

A consequential execution request should be bounded by the current Task Contract/capability owners and include enough structure to identify:

```text
exact source reference
requested operations
allowed destination/scope
applicable policy
Task Contract reference
caller/request identity
approval ceiling or gate when relevant
```

Runtime free-form context may accompany the request, but must not silently broaden it.

```text
runtime available != selected
selected != authorized
runtime completed != accepted
runtime observation != governance state
```

## Execution observation and progress

Pantheon may record bounded observations of external execution without owning the runtime's internal queue, scheduler, worker graph or checkpoint state.

Useful observations may include:

```text
external run reference
operation/capability slot
binding/version when known
observed status
measurable progress unit
input/output references
warnings/errors
processing attestation references
observed_at/freshness
```

Never fabricate progress.

```text
18 / 42 pages = measurable
73% because a model is “mostly done” = not measurable
```

```text
external runtime unreachable != run failed
last known running != currently running with certainty
external completed != projection accepted
```

Compatible runtime clients may expose runtime-facing progress or cancellation controls when supported. Pantheon Cockpit may expose governed observation/provenance/gate state. Neither surface becomes execution or governance authority by display alone.

## Projection lifecycle

Derived outputs should be versioned rather than silently overwritten.

A projection should retain enough identity to distinguish:

```text
source/document reference
producing extraction/run
projection kind/version
derived content reference/digest
generation status
review status
usage/active state
superseded projection reference when relevant
```

Generation, review and usage are separate axes.

```text
generated successfully != reviewed
reviewed != active
active != source
superseded projection != source deletion
```

## Index publication

Index publication is distinct from document classification and Knowledge publication.

An index publication should identify:

```text
source/projection/chunk-set identity
target index or retrieval binding
target scope
authorization reference
runtime/verification status
revocation state
```

```text
classified != indexed
Knowledge published != indexed
index exists != verified
index verified != result authoritative
index revoked != source deleted
```

Vectorization remains selective. A source does not require embeddings merely because it exists.

## Retrieval and Evidence boundary

A retrieval result should remain traceable to its source and derived representation, with locality and method where available.

A Retrieval Trace explains how material was found. It does not prove a claim.

```text
retrieval result
-> deliberate selection for a scoped assertion
-> Evidence Candidate / Evidence Item
-> Evidence Pack / Gate / Human Decision when consequential
```

```text
retrieved != truth
high score != authority
retrieval trace != proof
processing success != Evidence admission
```

No document pipeline, index, client or runtime may self-promote a retrieval result into accepted Evidence or durable Register memory.

## Processing attestations

Execution logs/manifests may attest that processing occurred under stated conditions.

Useful attestation material may include:

- source/output digests;
- converter/model/binding version where known;
- processed native-unit counts;
- warnings/errors;
- structure/table/layout diagnostics;
- output references;
- duration/resource observations when relevant.

```text
Processing Attestation = evidence that processing occurred as observed
Processing Attestation != proof that extracted meaning is correct
```

Do not collapse runtime attestations into professional Evidence.

## Quality posture

A single confidence score is insufficient for complex document processing.

Quality may instead be expressed through bounded signals such as:

```text
page/native-unit coverage
text coverage
structure preservation
table preservation
source-locality/citation alignment
unreadable-character rate
language consistency
human review status
warnings
```

A numeric value must identify its measurement method when the number is meaningful.

```text
model confidence != ground truth
coverage metric != semantic correctness
```

## Gates

### Gate A — source admissible

Verify source type, identity/integrity, access, confidentiality, retention and allowed scope.

### Gate B — intent/interpretation sufficient

Verify intent, proposed destination/operations, unresolved uncertainty and whether a human decision is required.

### Gate C — processing authorized

Verify Task Contract scope, required capabilities/tools, binding admission, data posture and approval ceiling.

### Gate D — derivative reviewable

Verify output presence, provenance/locality, expected coverage, processing attestations and visible warnings/partial states.

### Gate E — classification or Knowledge publication allowed

Verify target scope/relationship, review state, conflicts/duplicates and any destructive or semantic-merge consequence.

### Gate F — index publication allowed

Verify target scope, source/projection/chunks, retrieval binding, confidentiality/isolation, revocation/reindex posture and required verification.

### Gate G — consequential reliance/admission

Verify Evidence sufficiency and any required User Decision Gate before legal/contractual/regulatory/safety reliance, external effect, Evidence admission, memory/Register promotion or destructive replacement.

These gates describe governance conditions. They are not runtime steps and do not automatically approve anything.

## Responsibility split

### Pantheon governs

Pantheon governs lifecycle vocabulary, scope/provenance requirements, status distinctions, source/document/Knowledge consequences, capability/tool admission, gates, projection/index governance, Evidence boundaries and human-decision requirements.

Pantheon governance does not perform OCR, conversion, model inference, chunk generation, embedding computation, connector I/O, vector-store operations or external runtime scheduling.

### External runtimes execute

An admitted runtime may inspect/process/retrieve under a bounded Task Contract and return candidates, references and observations.

It must not silently expand scope, self-approve a classification, hide provenance/warnings, activate unavailable bindings, overwrite governed history, promote Evidence/memory or treat runtime completion as authorization.

### Clients and Cockpit expose different surfaces

Compatible runtime clients may expose runtime interaction.

Pantheon Cockpit/Card owners may expose governed source/projection/status/Evidence/gate views and capture permitted human decisions.

```text
client control != governance authority
Cockpit projection != persistence
visible summary != source
visible decision control != automatic approval
```

Browser/client surfaces must not receive privileged runtime secrets merely to bypass governed backend/admission boundaries.

### The human decides consequential choices

Human decision remains explicit where required for conflict resolution, destructive merge/replacement, consequential reliance, external effects, Evidence/Registre promotion, binding adoption/activation/update or rollback choices.

## Versioning, idempotency and rollback

For schema-owned document/Knowledge writes, use the version/idempotency contract in `DOCUMENT_KNOWLEDGE_SLICE_CONTRACT.md` and its machine schema.

A later extraction or projection should append/supersede rather than silently rewrite historical source-linked outputs.

```text
reprocess != overwrite source
new projection != delete prior projection
index revocation != source deletion
offline replay != overwrite permission
```

Rollback should generally select/reinstate a prior governed version or revoke a derived/index publication, not mutate history into pretending the later processing never occurred.

## Current implementation posture

This document is governance composition only.

### Pantheon implementation under `implementation/`

Current executable Pantheon slices, when present, live under `implementation/`. Their existence does not make every lifecycle capability implemented, adopted or active. Implementation claims must be established from the exact current modules, tests and schema/contracts at the current SHA.

Historical `pantheon-mvp` commits or PRs remain provenance only; they are not a second active implementation owner.

Do not infer implementation from old PRs, external repository snapshots, candidate binding lists or historical roadmap text.

Before claiming that intake, parsing, OCR, document structure, persistence, retrieval, indexing, progress or cancellation is implemented/adopted/active:

1. inspect current `main` at an exact SHA;
2. inspect the relevant current `implementation/` modules and tests;
3. inspect current schemas and contracts;
4. distinguish fixture/demo/external observation from adopted behavior;
5. preserve `implemented != adopted != activated`.

## Acceptance criteria for this doctrine

The lifecycle remains coherent when:

1. source identity and access are explicit before derived processing;
2. source, derivative, Document Card, Knowledge publication, retrieval and Evidence remain separate;
3. current schema-owned document structure exists before chunks;
4. derived outputs preserve attributable source locality;
5. generated Knowledge can remain visibly unreviewed without becoming Evidence;
6. external execution remains bounded by Task Contract/capability/tool policy;
7. runtime observations remain observations, not governance truth;
8. progress is only quantified from measurable executor data;
9. projection/classification/Knowledge publication/index publication remain distinct;
10. reprocessing/versioning is non-destructive;
11. retrieval can trace back to source/projection/locality;
12. processing attestations remain distinct from professional Evidence;
13. consequential reliance/admission remains gated;
14. no named client, parser, OCR/VLM, embedding model, vector store or runtime binding becomes a business-model dependency;
15. no Pantheon queue, scheduler, model host, installer or automatic approval path is introduced by this document.

## Final rule

```text
Preserve the source.
Version the derivatives.
Keep project documents, Knowledge, retrieval and Evidence distinct.
Let external runtimes execute only admitted work.
Project governed state without turning the projection into authority.
Require human decision where consequence requires it.
```
