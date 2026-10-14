# Source Intake Admission

Status: active support doctrine — source-admission boundary; external implementation is not adopted by this document.

Boundary profile: active_support_doctrine.

## Objective

Define the smallest governed seam for preserving any incoming source before Pantheon
understands, qualifies or links its professional meaning.

```text
receive
-> preserve source identity and provenance
-> leave unassigned or suggest Project candidates
-> record an explicit Project link only through a bounded operation
-> hand off later processing to Document, Information or other domain owners
```

```text
source preserved != source understood
source stored != source qualified
project suggested != project linked
project linked != source applicable
source linked != Information created
```

## Canonical vocabulary

`Source` is the canonical intake concept.

`Pièce` may be used in the UX when a Source is recognised as documentary material,
for example a plan, CCTP, email, photograph, attestation or contractual piece.

```text
Source
= anything admitted at the system boundary.

Pièce
= business/UX qualification of a documentary Source.

Document
= semantic and technical authority for a documentary record after the applicable
  document contract takes ownership.

Information
= authored, observed or consolidated professional content with its own meaning.
```

Pantheon does not force URLs, runtime events, native text or API observations into
the documentary term `Pièce`.

## Owner boundaries

```text
Pantheon Next
= schema, vocabulary, status and consequential-link doctrine.

pantheon-mvp
= PostgreSQL persistence, API operations and projections.

External source system
= native source identity and bytes when declared authoritative.

Hermes
= optional bounded producer of candidate Project matches or later analysis.

Human
= decides consequential or ambiguous Project linking when required.
```

The contract reuses existing ingestion and document adapters. It does not replace
NAS intake, Paperless bindings, document conversion, extraction or Source Inbox
projections.

## Minimum Source identity

Required:

```text
source_id
source_kind
origin
raw_source_ref
received_at
project_link_status
```

Optional:

```text
project_ref
declared_project_name
candidate_project_refs
source_date
mime_type
checksum
confidentiality
metadata
```

`raw_source_ref` is deliberately opaque. It may point to stored bytes, an external
record, a URL, an email identity or native content. The intake contract does not
require dereferencing that pointer.

## Project-link statuses

```text
unassigned
= no Project link is recorded.

suggested
= one or more candidate Project links exist; none is authoritative.

linked
= one explicit Project link is recorded.

excluded
= the Source is intentionally outside the current project-intake flow.
```

These statuses describe Project linking only. They do not describe parsing,
extraction, review, evidence or document lifecycle.

```text
project_link_status != processing_status
project_link_status != document_status
project_link_status != Information status
```

## Candidate Project references

A candidate keeps:

```text
project_ref
score
basis
producer
created_at
```

The score is bounded to `0..1` and is explanatory only.

```text
high score != confirmed link
candidate produced by Hermes != Project mutation
filename match != Project identity
```

## Source relations

Attachments and contained records are independent Sources connected through the
existing relation authority after inventory.

```text
email Source
-> contains
-> PDF Source
```

They are not embedded mutable child arrays. Each Source keeps its own identity,
provenance, checksum, Project-link posture and later processing lifecycle.

This doctrine records the capability but does not create a second graph or fix a
new relation table before the current graph and document relations are inventoried.

## Bounded operations

The executable owner may expose narrow operations equivalent to:

```text
create Source
read Source
list Sources by bounded filter
update low-consequence metadata
suggest Project links
link Project
unlink Project
exclude Source
restore Source
```

Project linking, unlinking, exclusion and restoration are explicit domain actions,
not a generic unrestricted PATCH.

Every write must preserve actor, idempotency and append-only event history.

## Integration with existing ingestion

Existing paths remain valid:

```text
NAS / upload intake
Paperless source adapter
source_documents and document_versions
Document conversion and extraction
Source Inbox read projection
```

The generic Source identity sits before or beside these paths and references their
native identities. It must not duplicate file bytes, extraction state or Document
versions.

A later handoff may create or bind a Document, but:

```text
Source admitted != Document created
Document created != Information created
Information created != ProjectClaim established
```

## First executable slice

The first slice is complete when:

1. any supported Source can be preserved without a Project;
2. a declared project name can be retained without creating a Project;
3. zero or more Project candidates can be recorded without authority transfer;
4. a human-bounded action can link, unlink, exclude and restore a Source;
5. attachments can be represented as independently identified Sources;
6. the implementation reuses existing Project and Document identities;
7. the slice works without Hermes, APU, IFC, Paperless, Docling or Mnemosyne;
8. no source preservation path automatically creates Information, Evidence or truth.

## Non-goals

This contract does not implement:

- OCR, parsing, chunking or embeddings;
- semantic Information creation;
- Project creation from an approximate name;
- ProjectClaim creation;
- APU mapping or Anatomie du projet;
- Evidence admission;
- memory promotion;
- provider routing, queueing or scheduling;
- automatic external action.
