# Information Card Projection

Status: active support doctrine — Information-family projection boundary; executable persistence remains external.

Boundary profile: active_support_doctrine.

## Objective

Define the smallest coherent user-facing projection for useful project content while preserving the distinct authority of Document, ProjectClaim, WorkIssue, Decision and ResultCandidate.

```text
native professional content
or one/many governed Documents
        ↓
Information-family projection
        ↓
project Contenus surface
```

## Existing authority reused

This contract extends the accepted adaptive project lifecycle roadmap. It does not create a second Information ontology or a seventh primary card family.

```text
Information-family card = default project-content projection
Document = documentary/file authority
Information = retained professional content
```

## Backing modes

```text
native
single_document
multiple_documents
```

A native Information has no Document reference.

A document-backed Information cites existing Document identities. It does not copy bytes, hashes, pages, extraction structure or version history into a competing owner.

```text
Document referenced != Document duplicated
Information displayed != Document authority transferred
```

Document references may carry the observed Document version and digest so the projection can report staleness without claiming an immutable snapshot.

## Dates

The contract distinguishes:

```text
source_date
received_at
issued_at
updated_at
business_date
```

`business_date` is the date selected for compact display. It is a projection choice and does not erase the underlying dates.

```text
business date displayed != source chronology collapsed
technical update != professional index
```

## Index and lifecycle

`professional_index` remains distinct from technical revision and lifecycle status.

```text
professional index != technical revision
professional index != lifecycle status
```

Initial lifecycle vocabulary remains:

```text
draft
in_progress
acted
superseded
```

The executable owner may enforce stronger transition rules, including ACTED immutability.

## Media and formats

`media_types` describes actual modes available to the user, for example email, PDF, text, table, photo, audio, DOCX, XLSX, IFC or link.

Several media types may coexist because one Information may aggregate several Documents or combine a Document with retained native content.

```text
media icon != semantic kind
MIME type != business kind
```

## Contacts

Contact references are projection links only. Person and Organization remain owned by their existing Agency Data identities. A free label may be retained when no normalized identity exists.

```text
contact displayed != Person duplicated
contact label != participation authority
```

## Boundaries

This projection must not:

- duplicate Document bytes, hashes, extraction or archive state;
- turn a tag into applicability or truth;
- turn a displayed contact into a canonical Participation;
- turn Hermes output into retained Information automatically;
- admit Evidence or mutate ProjectClaims;
- infer Information relations automatically;
- create variants or branches in this tranche.

```text
Information != Document
Information != ProjectClaim
Information != ResultCandidate
Information != WorkIssue
Information != Decision
projection != persistence
```

## Implementation placement

```text
Pantheon Next governs the projection contract and boundaries.
pantheon-mvp owns PostgreSQL persistence, API and Cockpit projection.
Hermes may prepare bounded candidates only through admitted work.
The human decides consequential retention and ACTED transitions.
```
