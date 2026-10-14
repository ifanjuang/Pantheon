# Agency collaboration, exchange and version convergence

Status: candidate support note — convergence only, documented non-implemented.
Boundary profile: candidate_support_note.

This note reconciles the existing architecture-agency document model around one stable artifact/revision lineage, explicit provenance, bounded exchanges, professional review and purpose-specific currentness.

It does not create a new document owner, Exchange ontology, Publication engine, portal, IAM layer, workflow runtime, approval engine, queue, scheduler, synchronization service or automatic classification authority.

It reuses existing owners and boundaries from:

- `AGENCY_DOMAIN_PACK.md`;
- `DOCUMENT_AND_KNOWLEDGE_ORGANIZATION.md`;
- `DOCUMENT_LIFECYCLE_GOVERNANCE.md`;
- `DOCUMENT_PRODUCTION_LIFECYCLE.md`;
- `INDEX_EFFECT_MATRIX.md`;
- `RAW_DERIVED_GOVERNED_RECORDS.md`;
- `SCOPE_ISOLATION.md`;
- `EXTERNAL_TOOLS_POLICY.md`;
- `PANTHEON_GRAPH_MODEL.md`;
- `COCKPIT_ARCHITECTURE.md`;
- `PANTHEON_SYSTEM_OWNERSHIP.md`;
- `schemas/project_change_variant_candidate.schema.yaml`.

The convergence target is intentionally small:

```text
Document / logical artifact
-> Revision / exact Source
-> Relations
-> Exchange inbound | outbound
-> Review / Decision when needed
-> Publication only when exposure must persist
```

This is a reasoning model, not a requirement that every line become a separate database table or canonical object.

```text
rigid identity / provenance / authority
flexible channels / surfaces / usages
```

## 1. Objective

The agency needs to support, without duplicating authority:

- internal collaborative work;
- receipt of project material by email, upload, shared vault, connector, NAS or other approved channel;
- imported studies, client programmes, manufacturer sheets, plans, quotes, reports and correspondence;
- stable logical documents with explicit revisions;
- preservation and exact retrieval of prior revisions;
- comparison and bounded impact review;
- review and visa of exact submitted revisions;
- agency annotations and derived review material without transferring authorship;
- outgoing transmission by email or other channel;
- persistent publication such as a DCE snapshot or a controlled client document collection;
- optional external surfaces such as a project vault, limited Cockpit or dedicated interface;
- reusable Knowledge updates derived from changed sources;
- simple user flows that do not expose governance internals.

The target is not application-to-application truth synchronization and not a universal external portal.

The target is one professional artifact/revision model that survives changes of channel and surface.

## 2. Stable artifact and revision identity

Collaboration is organized around one logical artifact identity rather than copies owned by individual applications or users.

```text
logical artifact
  -> revision 1
  -> revision 2
  -> revision 3
       -> representations / exact source files
```

Examples:

- one CCTP logical document with many working and issued revisions;
- one BET study with indices A, B and C;
- one contractor execution plan with successive submitted indices;
- one quote or offer with successive revisions;
- one drawing family with successive issue states;
- one Knowledge Item with successive editorial revisions.

A surface may display, edit, comment on or transmit an artifact. It does not become the owner of the artifact because the work occurred there.

```text
Obsidian file != artifact identity
email attachment != artifact identity
Cockpit card != artifact identity
PDF export != artifact identity
share link != artifact identity
```

The stable rule is:

```text
shared artifact identity
+ exact revision identity
+ preserved provenance
+ surface-local interaction state
```

not:

```text
application A <-> application B <-> application C truth synchronization
```

## 3. Internal sequence and issuer vocabulary

The system preserves separate version dimensions when relevant:

```text
version_seq
= internal monotonic sequence used by the implementation owner

revision_label
= external professional label carried by the source or issuer

issuer_document_reference
= opaque issuer reference when present
```

Examples include:

```text
A
B
C
A1
00
01
Rev.03
ST-204/EXE-03
```

No universal ordering rule is inferred from external labels or references.

```text
highest-looking revision_label != current authority
latest filename != current authority
reference lexical order != chronology
newer upload timestamp != professional approval
```

`INDEX_EFFECT_MATRIX.md` remains the owner of professional effect classification.

## 4. Exact Source and provenance

A received or produced file is first preserved as exact material with provenance.

Useful provenance may include:

```text
channel
sender / observed actor
received_at or produced_at
message / connector reference
original filename
content digest
exact source capture
project / dossier scope
```

The transport is not the professional meaning.

```text
email != Project Document
attachment != validated document
folder location != professional status
sender address != verified professional authority
```

The same exact Source may support different governed relationships without duplicating bytes, for example:

```text
manufacturer sheet
├── Project Document source in Project A
└── reusable Knowledge source candidate
```

```text
same bytes != same role
same bytes != same access rights
```

## 5. Inbound exchange and intake

An inbound exchange records that material crossed the agency boundary into the working perimeter.

Typical channels include:

```text
email
manual upload
project vault
NAS
Drive / repository
limited external interface
approved connector
```

The channel may vary without changing the document model.

```text
BET by email
BET by project vault
BET by dedicated upload surface
-> same Source / revision admission rules
```

The smallest useful semantics are:

```text
direction = inbound
channel
actor / origin
occurred_at
payload refs
```

This does not require a new canonical `Exchange` owner if existing receipt, Source and provenance records already answer the same questions.

Likewise, where `DOCUMENT_LIFECYCLE_GOVERNANCE.md` lists conceptual `Intake Item`, `Source Origin`, `Intake Intent` and related decomposition, those names remain optional lifecycle decompositions rather than mandatory independent owners. An implementation should collapse them when existing Source, event, task or projection owners preserve the required semantics.

```text
received != admitted
received != classified
imported != validated
retrieved != truth
```

### 5.1 Contextual intake

When the artifact identity is already known, use it directly.

```text
known artifact + deposit new index
-> exact Source capture
-> duplicate check
-> revision admission / reuse
-> comparison when needed
```

No AI identity inference is needed.

### 5.2 Project Inbox

When the project is known but the artifact is not, a Project Inbox may expose reconciliation candidates.

```text
Study_structure_C.pdf
-> probable new revision of Study structure B

Thermal_report.pdf
-> probable new artifact
```

The Inbox is a projection over intake state, not another document owner.

### 5.3 Unclassified intake

When neither destination nor artifact is sufficiently known, the Source remains unclassified until enough context exists.

Inference may propose classification. It must not fabricate professional identity when ambiguity matters.

## 6. Revision preservation and supersession

A new revision does not overwrite the previous source or erase provenance.

```text
document identity
  -> version_seq
  -> revision_label
  -> supersedes_version_id
  -> exact source digest / capture
  -> issuer
  -> received_at / produced_at
  -> status / effect class
```

```text
superseded != deleted
obsolete != never existed
new receipt != universal currentness change
```

Exact duplicate bytes may reuse an existing content revision while preserving a distinct receipt event when that receipt matters.

```text
same digest != same receipt event
same filename != same content
```

## 7. Relations before new objects

Prefer explicit relations over new lifecycle objects whenever no separate identity, lifecycle or authority is required.

Useful relation meanings may include, where already admitted by the relevant owner:

```text
supersedes
references
based_on
derived_from
review_of
responds_to
```

The relation vocabulary must remain governed by its actual owner; this note does not canonize new generic predicates.

The design rule is:

```text
new object only when it needs
- its own stable identity, or
- its own lifecycle, or
- its own authority semantics

otherwise
- relation, attribute or projection
```

This avoids `VisaWorkflow`, `ReviewArtifact`, `ExchangePackage` or other parallel models unless a distinct responsibility is demonstrated.

## 8. Review and visa

Professional review concerns an exact submitted revision.

A visa chain is not one mutable status on the logical document and does not require a monolithic workflow object.

```text
contractor EXE B received
-> review of exact B
-> comments / reservations
-> human visa decision when applicable
-> outbound transmission

contractor EXE C received
-> new exact revision C
-> new review cycle
```

The historical review of B remains attached to B.

`INDEX_EFFECT_MATRIX.md` owns `visa_status_record` semantics and already requires submitted version, visa status, comments and reviewer.

```text
review comment != visa decision
visa comment != execution authority
review completed != contract modification
new revision != previous visa rewritten
```

A runtime may prepare a visa review candidate. The architect remains responsible for the actual visa status, wording, transmission and professional consequence.

A chain may vary by project:

```text
contractor -> agency
contractor -> BET -> agency
contractor -> BET + control office -> agency -> client
```

The model should therefore compose exact revisions, reviews, decisions and exchanges rather than hard-code one universal sequence.

## 9. Agency annotation and derived drawings

A correction drawn by agency on top of a received contractor or BET plan must preserve authorship and provenance.

If agency annotates the received file:

```text
contractor EXE B
issuer = contractor
        |
        | review_of / derived_from
        v
annotated representation agency
```

The annotation is a derived review representation of exact B. It is not revision C of the contractor document.

```text
Agency annotation != issuer revision
redline != contractor authorship transfer
annotated PDF != automatic execution instruction
```

If agency instead produces a genuine autonomous drawing or detail, it becomes a separate agency-authored logical document with its own revision lineage.

```text
contractor document
B -> C -> D

Agency detail
01 -> 02
```

A relation may record that agency detail 01 references or responds to contractor B, without merging the two revision chains.

This distinction preserves professional responsibility while keeping graphical review practical.

## 10. Purpose-specific currentness

There is no universal persisted `current_version` that is correct for every professional use.

The same logical document may legitimately have different revisions current for different purposes.

```text
study C = latest received
study B = latest reviewed
study B = current coordination baseline
study A = signed contractual baseline
```

Candidate projections include:

```text
latest_received
latest_reviewed
current_working
current_for_coordination
current_for_consultation
current_contractual
current_for_execution
current_for_site
latest_as_built_candidate
```

These are projections, not new authority objects.

Each resolved projection must disclose the exact revision and its basis. Insufficient or conflicting inputs remain unresolved or conflicting rather than guessed.

```text
latest_received != current_for_execution
latest_reviewed != current_contractual
published != contractual
```

## 11. Revision comparison and impact review

A runtime may compare two exact revisions to produce a bounded comparison candidate.

Useful outputs include:

- changed pages, sheets, clauses or articles;
- added / removed sections;
- changed quantities, amounts, dimensions or performance values;
- changed references;
- changed exclusions or variants;
- uncertainty where extraction is insufficient.

```text
difference detected != significance established
difference detected != project state changed
```

When a new revision is received, explicit old-revision consumers may support downstream review candidates.

```text
BET thermal B
  -> used by CCTP C
  -> used by notice

BET thermal C received
  -> review candidates for the explicit B consumers
```

The historical consumer remains pinned to its original baseline.

```text
impact candidate != required modification
impact candidate != WorkIssue
impact candidate != automatic rewrite
```

Project Anatomy may support navigation where an admitted relation already exists. Do not create a second dependency graph merely for version intake.

## 12. Variants and offers

A new revision continues one artifact identity. A genuine alternative is not forced into that revision chain.

```text
new revision
= continuation of the same artifact

variant
= sibling artifact / alternative proposition
```

Project-change variants reuse the existing Project variant / ChangeCandidate path.

Commercial alternatives may remain sibling offer artifacts with independent revision histories.

```text
base offer
A -> B

variant offer 01
A -> B
```

Quote or offer analyses remain pinned to their exact baselines.

```text
newer offer != selected offer
analysis != attribution
variant != Project branch
```

## 13. Knowledge-source updates

A newer source may affect reusable Knowledge without automatically replacing it.

```text
new source edition
-> compare with prior source
-> find Knowledge Items citing the prior source
-> propose editorial update
-> preserve both source editions and anchors
```

```text
source updated != Knowledge silently rewritten
Knowledge updated != Evidence admitted
```

Historical projects may legitimately continue to reference an older source edition when it was the applicable baseline.

## 14. Outbound exchange

An outbound exchange records that selected material crossed the agency boundary toward another actor or system.

Typical channels include:

```text
email
shared vault
link
limited interface
export / transfer
approved connector
```

The smallest useful semantics mirror inbound exchange:

```text
direction = outbound
channel
actor / recipient
occurred_at
payload refs
```

A simple outbound email does not require a persistent Publication object.

```text
sent != approved
sent != received contractually
link sent != link opened
link opened != acknowledgement
```

If formal transmission, acknowledgement or contractual receipt later needs its own authority semantics, it must be modeled explicitly rather than inferred from transport telemetry.

## 15. Publication only for persistent exposure

Publication is justified only when the agency intentionally maintains an externally consumable resource over time.

Examples:

- one shareable exact document;
- a DCE or consultation package;
- a controlled client collection of meeting reports;
- a project document collection exposed through a limited interface or vault.

Publication is not the same as outbound exchange.

```text
Exchange
= event: something was sent / exposed through a channel

Publication
= persistent exposure: a selected resource remains available
```

The link, vault or UI is a technical access mechanism, not the publication authority itself.

### 15.1 Snapshot publication

Use a snapshot where the issued corpus must remain reproducible.

Typical case: DCE.

```text
DCE publication P1
published_at
published_by
purpose = consultation
manifest
  -> CCTP exact revision
  -> DPGF exact revision
  -> plan A exact revision
  -> plan B exact revision
  -> study exact revision
```

The internal documents may evolve later without mutating P1.

```text
published snapshot != live folder
later working revision != prior DCE silently changed
package hash / manifest != contractual signature
```

### 15.2 Controlled collection publication

Use a collection where the exposed set is intentionally allowed to evolve.

Typical case: client meeting reports.

```text
Client CR collection
  -> CR 15 exact revision
  -> CR 16 exact revision
  -> CR 17 exact revision
```

A new internal CR does not become visible merely because it exists. It enters the external collection only when the applicable agency action publishes it.

```text
created != published
published != approved unless approval is separately established
```

### 15.3 Share links

A share link is a replaceable access mechanism over a publication or exact published item.

A bounded implementation may support:

```text
opaque token
view
download
bundle download
optional expiry
revocation
```

Do not expose internal storage locators or make link possession a professional role.

```text
share link != user account
share link != project authority
share link != Evidence
```

## 16. Internal Pantheon and mediated external surfaces

Direct Pantheon use belongs to the internal agency perimeter in the current agency deployment posture.

External participants are not required to become Pantheon users and should not receive the full internal Cockpit.

They may interact through the simplest surface appropriate to the project:

```text
email
project Obsidian / document vault
share link
limited Cockpit projection
dedicated project interface
other approved mediated surface
```

The external surface is bounded and replaceable.

```text
external surface != Pantheon
surface capability != authority
vault membership != professional approval
technical access != professional role
```

This agency internal-only direct-access posture is an agency deployment decision. It does not require the Pantheon kernel to encode one universal organization-specific IAM rule.

## 17. Identity, role, access and authority

Keep four dimensions independent:

```text
identity
= who is this actor?

professional role
= what does the actor represent in the operation?

technical access
= which resources / operations may the actor reach through the selected surface?

professional authority
= which consequential decisions may the actor legitimately make?
```

```text
professional role != technical permission
technical permission != professional authority
button availability != approval authority
authenticated != authorized
```

A BET may be allowed to submit its study without being able to validate the architect's CCTP.

A client may be allowed to consult selected meeting reports without receiving any internal Pantheon capability.

Pantheon must not become an IdP, general IAM/RBAC engine or permission router.

## 18. Scenario — BET study received by email

```text
BET email
-> attachment Study C
-> inbound exchange / receipt provenance
-> exact Source capture
-> known Study artifact or reconciliation candidate
-> professional revision C
-> comparison B <-> C when useful
```

A valid state may remain:

```text
latest_received = C
current_for_coordination = B
```

The BET does not need a Pantheon account for this flow.

## 19. Scenario — execution-plan visa with annotation

```text
contractor sends EXE B
-> inbound exchange
-> exact revision B
-> agency review
-> agency annotated derivative of B when useful
-> human visa decision when applicable
-> outbound exchange of review / visa material
-> contractor sends EXE C
-> new inbound exchange
-> exact revision C
-> new review cycle
```

B, its review and its annotation remain historically pinned. C does not rewrite them.

## 20. Scenario — DCE publication

```text
working project documents
-> review / applicable decisions
-> exact versions selected
-> publication snapshot DCE P1
-> optional share link / bundle
-> outbound exchange of the link or package
```

A later CCTP working revision does not silently alter DCE P1.

```text
latest_working != current_for_consultation
publication snapshot != signed contract
```

## 21. Scenario — client CR collection

```text
CR 15 produced
-> review / agency publication action
-> collection contains CR 15

CR 16 produced
-> not externally visible yet
-> agency publication action
-> collection now also contains CR 16
```

The collection evolves by explicit inclusion while each exposed item remains tied to an exact revision.

## 22. Scenario — programme client and manufacturer sheet

A programme received from a client may enter through email or file import:

```text
programme source
-> inbound exchange provenance
-> exact Source
-> Project Document / Information qualification as applicable
-> extracted requirements as claims / candidates
```

```text
programme received != Project automatically modified
extracted requirement != accepted design decision
```

A manufacturer sheet may remain project-specific, reusable Knowledge support, or both through separate governed relations to the same Source.

```text
manufacturer sheet != regulatory proof by default
stored != validated
```

## 23. User-facing simplicity

Routine actions should expose the next useful operation rather than the internal ontology.

Examples:

```text
Import this attachment
Deposit new index
Compare with previous
Review / annotate
See impacts
Open coordination version
Publish DCE
Share document
Add to client CR collection
```

Do not force users to choose internal status vocabulary when the context can determine it safely.

Do not hide distinctions that affect professional consequence.

```text
simple interaction != collapsed semantics
```

## 24. Performance and graceful degradation

Prefer deterministic facts before model inference:

```text
explicit artifact context
content digest
exact prior revision
known project / issuer / lot
stable metadata
```

Reuse derived processing when exact source digest and processing configuration are unchanged.

Keep large binaries in the approved storage layer while governed records retain identities, hashes, provenance, status and links.

Optional surfaces and runtimes must degrade gracefully:

```text
Obsidian unavailable
-> email / another surface can carry the exchange

share surface unavailable
-> publication identity and exact selected revisions remain

Hermes unavailable
-> stored artifacts and revisions remain accessible

real-time co-editing unavailable
-> optimistic concurrency remains functional
```

No optional client, memory provider or runtime becomes the owner of document identity or professional authority.

## 25. Non-goals

This note does not introduce:

- a new document database;
- a second knowledge graph;
- a canonical generic `Exchange` object;
- a `VisaWorkflow` object;
- a generic `ReviewArtifact` hierarchy;
- a generic branch runtime;
- a new memory store;
- direct external access to the full internal Pantheon surface;
- application-to-application synchronization as authority;
- a Pantheon IAM / RBAC engine;
- automatic replacement of prior revisions;
- automatic impact propagation;
- automatic Knowledge promotion;
- automatic approval or visa;
- automatic external publication;
- mandatory Obsidian, OpenWebUI, Hindsight or Hermes dependency.

## 26. Future implementation acceptance criteria

A bounded implementation should prove, where the corresponding capability is actually implemented:

1. one logical document retains multiple exact revisions;
2. exact duplicate bytes do not create false content revisions;
3. separate receipt events can be retained for duplicate bytes;
4. external labels / references do not control chronology or authority;
5. contextual intake can bind an explicit artifact without AI identity guessing;
6. ambiguous intake remains candidate / unresolved rather than silently bound;
7. email-only external participants can participate without a Pantheon account;
8. prior revisions remain retrievable after supersession;
9. comparison remains pinned to exact revisions and establishes no professional consequence by itself;
10. downstream impact candidates preserve their exact baseline and do not rewrite consumers;
11. purpose-specific currentness can resolve to different revisions;
12. unresolved currentness remains explicit;
13. review and visa records remain attached to the exact submitted revision;
14. a new submitted revision creates a new review cycle rather than mutating historical review;
15. an agency annotation of an external plan remains derived from / reviewing that exact external revision;
16. an autonomous agency drawing remains a separate logical document with its own revisions;
17. outbound exchange can be recorded without creating persistent Publication;
18. a DCE publication can preserve an immutable exact-version manifest;
19. a client document collection can evolve only through controlled inclusion;
20. a share link can be revoked without changing the underlying professional document identity;
21. an external surface can be removed or replaced without changing Pantheon authority;
22. technical access remains separate from professional role and authority;
23. a Project variant reuses the existing Project variant / ChangeCandidate path rather than a generic branch;
24. commercial variants can remain sibling artifacts with their own revision histories;
25. Knowledge update candidates preserve prior and newer source provenance;
26. disabling optional runtimes or surfaces does not remove stored versions or change authority.

## 27. Convergence decision

The repository already contains the principal owners required for document identity, revision history, provenance, comparison, currentness, Knowledge links, Project relations and human-governed consequence.

The preferred path is therefore:

```text
reuse document identity and revision owners
reuse exact Source capture and retention
reuse provenance and existing relation owners
reuse purpose-specific currentness
reuse existing Review / Decision / index-effect semantics
reuse Project variant / ChangeCandidate when applicable
model inbound and outbound exchange as bounded events / provenance where needed
create persistent Publication only when durable exposure has its own lifecycle
keep external surfaces mediated and replaceable
keep direct Pantheon use inside the current agency internal perimeter
```

Do not add a collaboration-platform ontology, a parallel version model, a universal portal model or a workflow object for every professional sequence.

The practical agency cycle is:

```text
RECEIVE
-> PRESERVE
-> QUALIFY
-> WORK / REVIEW
-> DECIDE when consequence requires it
-> PUBLISH or TRANSMIT when needed
-> RECEIVE the next external response
```

The same cycle covers email intake, studies, client programmes, manufacturer sheets, DCE publication, client CR collections, visa loops and annotated execution plans without requiring all participants to use the same software.

```text
one artifact
many revisions
many channels
many surfaces
explicit provenance
purpose-specific currentness
one governed consequence path
```
