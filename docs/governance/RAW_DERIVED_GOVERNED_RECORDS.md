# Raw, Derived and Governed Records

Status: candidate data-platform support doctrine  
Scope: separation between raw content, derived content, governed records, retrieval objects, provenance objects, Evidence and approvals  
Runtime status: non-executable

## Purpose

This document defines a layered content model for Pantheon-compatible professional systems.

It does not implement storage, OCR, Markdown conversion, vector search, graph storage, database tables, cockpit collections or workflow execution.

## Core rule

```text
The database does not hold the whole knowledge.
It holds governed handles: identity, scope, status, provenance, links, extracted facts, approvals and decisions.
```

PostgreSQL or any equivalent structured store should not become a dumping ground for every document, transcript, image, email body, OCR artifact, embedding, discussion nuance or professional interpretation.

## Layer model

A professional system should distinguish at least seven layers:

```text
1. Raw content
2. Derived content
3. Governed records
4. Retrieval objects
5. Provenance objects
6. Evidence objects
7. Approval and decision records
```

Each layer has a different responsibility.

## 1. Raw content

Raw content is the material source.

Examples include PDF quotes/invoices/site reports, email bodies and attachments, photos, plans, scans, transcripts, contracts, CCTP, forms and observed API payloads.

Raw content should normally live in a source/storage system such as:

```text
NAS or local controlled folder
Google Drive or another admitted document source
SFTP / S3-compatible storage
client or Cockpit upload staging area
secure document repository
```

The structured record layer records raw-content identity rather than duplicating the whole payload by default.

Candidate governed handles include:

```text
storage_object_id
original_filename
storage_provider
path_or_uri
hash
mime_type
source_system
confidentiality
project_id or scope_id
created_at
imported_at
status
```

```text
storage location != governed identity
source captured != source validated
same filename != same source
```

## 2. Derived content

Derived content is produced from raw content, for example OCR/extracted text, Markdown conversion, cleaned transcript, summary, metadata/table candidates, image description, chunk sets or embedding references.

Derived content is useful, but it is neither the source nor proof by itself.

```text
OCR != truth
Markdown != original
summary != Evidence
embedding != memory
```

Derived content should keep links back to the exact raw source, including source/document identity, digest, page/region when relevant, extraction method/version, confidence/quality signal, timestamp and status.

## 3. Governed records

Governed records are structured records used for control, review and action, such as project, organization, contact, document/message/quote/invoice record, site meeting/point, task, project fact, action proposal, memory candidate and approval/decision record.

They belong in PostgreSQL or another structured governed-record layer and should carry explicit identity, scope, status, source reference, owner/responsible viewpoint, timestamps, review/certainty state and approval state where applicable.

The structured layer should prefer reviewable handles and relationships over large unqualified blobs.

## 4. Retrieval objects

Retrieval objects make material findable. They may include full-text/vector/search/entity/keyword indexes and chunk metadata.

```text
retrieved means found
found != true
retrieval score != authority
```

Retrieval objects inherit source scope and confidentiality. A project source must not become cross-project retrievable merely because an index can return it.

Minimum useful metadata includes document/chunk identity, scope/project/library identity, confidentiality, source page/heading path, status and validity/currentness signal.

## 5. Provenance objects

Provenance objects connect sources, derivatives, claims, decisions and outputs.

Examples:

```text
email -> attachment -> quote
quote line -> CCTP article
missing scope -> action proposal
meeting -> decision
source -> Markdown derivative -> active projection
```

Provenance may be represented relationally, graphically or both.

```text
relation explains connection
relation != validation of the connected claim
```

## 6. Evidence objects

Evidence objects are selected, bounded and reviewable support for a claim or output, such as Evidence Candidate, Evidence Item, Evidence Pack Candidate, Evidence Pack, contradiction candidate or source excerpt with page reference.

Evidence handling should answer:

```text
What is claimed?
Which exact source supports or contradicts it?
Which passage/region matters?
What is the source status/currentness?
What assumptions and contradictions remain?
What decision or approval is required before consequential use?
```

A retrieved chunk becomes Evidence material only through the applicable Evidence-selection/review path.

## 7. Approval and decision records

Approval and decision records attach responsibility to consequential transitions, for example project attribution, retention promotion, classification, publication, external transmission or revocation.

```text
preparing != approving
recording != deciding
runtime completion != authorization
```

These records belong in the governed record layer, not in runtime/client state.

## Where subtleties live

Subtleties do not belong to one universal store.

| Subtlety | Appropriate owner |
|---|---|
| exact legal/professional wording | raw source + readable derivative |
| layout nuance | raw source + layout metadata |
| long discussion context | transcript/source + summary candidate |
| important meeting nuance | notes + selected governed extracts |
| project-specific fact | governed project fact owner |
| reusable method | Knowledge or retention candidate owner |
| semantic similarity | retrieval index |
| causal/relational context | provenance graph/relations |
| support for a claim | Evidence owner |
| professional/consequential decision | approval/decision owner |

## Conversation handling

A conversation should not be flattened into structured storage as one authoritative record.

Use three levels:

```text
1. Raw transcript/source
2. Structured summary candidate
3. Governed extracts
```

Governed extracts may become project facts, tasks, retention candidates, workflow-build requests or decisions through their applicable owner paths. Raw transcript and summary remain source/derived content.

## Document handling example

Incoming contractor quote:

```text
raw content
  PDF quote in governed project source storage.

derived content
  extraction/OCR, Markdown, table candidates, chunks.

governed records
  document record, quote candidate, contractor/lot/amount candidates.

retrieval objects
  scoped searchable chunks/index entries.

provenance objects
  email -> attachment -> quote -> lot -> CCTP version -> analysis.

Evidence objects
  selected source excerpts linked to exact claims.

approval records
  human/consequential decisions on attribution, status and external effects.
```

## Knowledge handling example

User supplies a professional guide:

```text
raw content
  original source retained in its admitted storage.

derived content
  extracted text/Markdown, summary candidate, chunks.

governed records
  Knowledge publication candidate, family/scope/review status.

retrieval objects
  scoped index entries only under applicable policy.

provenance objects
  original -> derivative -> active publication version.

Evidence objects
  exact excerpts only when deliberately selected for a task claim.

approval records
  consequential classification, merge, reliance or retention decisions where required.
```

## Structured-store boundary

PostgreSQL or an equivalent structured layer is well suited to identities, statuses, scopes, links, metadata, governed facts/candidates, approvals, decisions, provenance edges, workflow states, action proposals and audit events.

It should not be assumed to contain every large binary, image, raw embedding, unbounded transcript, unreviewed memory dump or all semantic nuance.

Small controlled payloads may be stored directly where appropriate; that implementation choice does not collapse the layer model.

## Governed projection posture

Pantheon Cockpit/Card owners or another bounded governed projection may expose governed records and selected derivatives for review.

A projection may help the user inspect metadata, correct classifications, review extracted facts, open the original source, compare derivatives, navigate provenance, inspect Evidence status and take governed decisions.

```text
projected database row != professional truth
projection != persistence
client selected != governance authority
```

Runtime clients may provide interaction, but they do not become systems of record or Evidence owners by displaying content.

## Relation to retrieval/RAG

RAG is retrieval support, not memory or Evidence authority.

```text
RAG retrieves possible support.
Evidence selection qualifies support for a scoped claim.
Approval/decision owners determine consequential reliance or action.
```

## Boundary with implementation

This doctrine requires no specific technology.

Replaceable implementations may use structured databases, file/object storage, Markdown derivatives, full-text/vector indexes, relational/graph provenance, governed Cockpit projections and external Hermes-side extraction/conversion resources.

Concrete products or providers remain bindings, not Pantheon authority.

## Operating principle

```text
Do not ask one layer to do every job.

Files preserve materiality.
Readable derivatives preserve inspectability.
Indexes preserve findability.
Graphs/relations preserve connections.
Structured stores preserve governed handles.
Evidence Packs preserve proof chains.
Approvals and decisions preserve responsibility.
```
