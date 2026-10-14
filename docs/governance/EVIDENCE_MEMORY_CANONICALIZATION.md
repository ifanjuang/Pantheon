# Registre Probatoire — evidence canonicalization

Status: candidate support note — documented non-implemented. Reframed under the Registre Probatoire direction (see `GLOSSARY.md`, `REGISTRE_PROBATOIRE_DIRECTION.md`). This is the central document for the `Registre Probatoire`, the evidence register that replaces the former "Registre Probatoire entry".
Boundary profile: candidate_support_note.

Tracking issue: #68.

This note captures the intended governance model for turning sources and evidence into scoped, reviewable, versioned, dated and cited register entries. Certainty uses the `E0–E4` scale owned by `GLOSSARY.md`.

It does not implement a database schema, runtime, connector, queue, approval engine, memory engine, vector store, mem0 integration, Hermes memory integration, automatic promotion rule or automatic dependency resolver.

## Purpose

The goal is not to make the system remember more.

The goal is to make durable memory trustworthy, scoped, traceable, revisable and safe to use in professional work.

A raw source, a retrieved excerpt, a repeated observation, a vector match, a mem0 item or a Hermes runtime note is not a Registre Probatoire entry by itself.

The governed path is:

```text
Raw Source
→ Evidence Candidate
→ Extraction Candidate
→ Register Candidate
→ Human Review / Gate
→ Registre Probatoire entry
→ Optional backend projection
```

Backend projection may target PostgreSQL views, pgvector indexes, mem0, Hermes memory or another future backend. None of those backends is the canonical authority by itself.

## Core distinction

```text
Evidence = what supports a claim.
Hermès memory = what the runtime may reuse later, ungoverned.
Registre Probatoire entry = approved, scoped, evidence-linked, dated and cited record.
```

Evidence can suggest memory.

Evidence does not promote memory.

Memory can be projected to backends.

Backends do not make memory canonical.

## Non-goals

This note must not be read as authorizing:

- automatic Knowledge-to-Memory promotion;
- automatic Evidence-to-Memory promotion;
- mem0 as a Registre Probatoire entry;
- Hermes memory as a Registre Probatoire entry;
- pgvector retrieval as truth;
- OpenWebUI Knowledge as a Registre Probatoire entry;
- direct raw Postgres access for Hermes;
- hidden cross-dossier search;
- automatic contradiction resolution;
- automatic dependency downgrading for critical project facts;
- automatic deletion of historical memory.

## Canonical storage posture

The canonical registry should be considered a governed record layer.

Preferred conceptual posture:

```text
PostgreSQL records the governed registry.
pgvector retrieves by similarity.
mem0 may project usable memory.
Hermes may consume or propose candidates.
Pantheon governs status, scope, evidence and approval.
The human validates consequential promotion.
```

This does not require a specific physical schema yet. Any future schema must preserve the difference between canonical records and backend projections.

## Objects

### Raw Source

A Raw Source is material that exists before governance.

Examples:

- email;
- PDF;
- scanned PDF;
- plan;
- image;
- site photo;
- meeting note;
- report;
- spreadsheet;
- quote;
- contractor message;
- client instruction;
- administrative decision;
- internal note.

Raw Source is not proof by itself.

### Evidence Candidate

An Evidence Candidate is a selected source item or excerpt that may support a claim.

It should carry at least:

```text
source_id
source_type
project_id / dossier_id / scope_id
source_date
received_date
author_detected
interlocutors_detected
origin_channel
page_or_excerpt_reference
source_status
sensitivity
```

Evidence Candidate remains candidate until reviewed or represented in an Evidence Pack.

### Extraction Candidate

An Extraction Candidate is the system's proposed interpretation of evidence.

It may propose:

- a fact;
- a decision;
- a preference;
- a question;
- a hypothesis;
- a temporary choice;
- a contradiction;
- a revocation;
- a dependency;
- an impact.

It must remain distinct from memory.

### Register Candidate

A Register Candidate is a proposed durable memory item.

It must be atomic enough to review and revise.

A Register Candidate should not group unrelated subjects into one claim.

### Registre Probatoire entry

A Registre Probatoire entry is approved, durable evidence with scope, certainty (E0–E4), reviewability and a revocation or supersession path.

A Registre Probatoire entry may be used by future answers only within its declared scope and subject to contradiction checks.

### Backend Projection

A Backend Projection is a synchronized representation of a memory item in another system.

Examples:

```text
pgvector index row
mem0 memory item
Hermes memory excerpt
OpenWebUI display excerpt
provenance graph node
```

Projection is not canon.

The canonical registry remains the authority for status, scope, evidence, revocation and supersession.

## Evidence metadata requirements

Every evidence item that may feed memory should capture:

```text
source_type
source_title
source_date
received_date
effective_date if known
author_detected
interlocutors_detected
organization_detected
project_id
client_id if applicable
dossier_id
phase
lot / trade if applicable
channel
source_excerpt
page_or_location
linked_files
sensitivity
language
```

For architecture work, useful phase values include:

```text
ESQ
APS
APD
PRO
ACT
DET
AOR
administrative
post-reception
litigation / dispute
```

## Speech-act classification

The system should not treat every sentence as a decision.

Evidence should be classified by the nature of the wording.

Suggested categories:

```text
question
hypothesis
supposition
preference
temporary choice
affirmation
decision
validation
annulation
revocation
contradiction
update
reservation / defect
external commitment
```

Examples:

```text
Could we remove the pool?
→ question

We are considering removing the pool.
→ hypothesis / weak preference

We no longer want a pool.
→ probable decision

We validate removal of the pool.
→ strong decision / validation
```

Speech-act classification affects confidence and approval requirements. It does not promote memory by itself.

## Confidence model

Confidence should be explainable, not a single opaque number.

A Register Candidate may carry component scores:

```text
source_confidence
author_confidence
date_confidence
language_confidence
context_confidence
evidence_confidence
coherence_confidence
scope_confidence
```

The final confidence score should explain why the item is candidate, weak, strong or blocked.

Example:

```text
Claim:
The client no longer wants a pool on Project X.

Source confidence: high — direct client email.
Date confidence: high — latest dated source.
Language confidence: medium-high — affirmative wording, but no formal validation word.
Context confidence: high — project and subject detected.
Coherence confidence: medium — conflicts with older pool-related memories.

Status:
Register Candidate — impact review required.
```

## Promotion posture

Confidence supports ranking and triage.

Confidence does not replace review.

Suggested posture:

```text
0–49  weak extraction; keep as evidence or reject
50–69 uncertain; arbitration required
70–84 Register Candidate
85–94 strong Register Candidate
95+   pre-canonical candidate if no contradiction and approval path is satisfied
```

Even strong candidates remain candidates until the required approval is recorded.

## Atomic memory rule

A memory item should contain one claim, decision, preference, hypothesis or derived impact.

Rule:

```text
If two parts can be updated independently, they should be separate memory items.
```

Avoid:

```text
The client no longer wants a pool, so the pool heat pump is abandoned, the terrace must be reviewed and foundations must change.
```

Prefer:

```text
M1 — The client no longer wants a pool.
M2 — The pool heat pump selection is probably obsolete.
M3 — The terrace previously selected for pool compatibility requires revalidation.
M4 — The foundation-depth assumption linked to the pool requires technical arbitration.
```

## Subject model

Memory should be organized by project and subject.

Conceptual hierarchy:

```text
Organization / Agency
→ Client
→ Project
→ Subject
→ Sub-subject
→ Atomic Memory
→ Version
→ Evidence links
→ Dependencies
→ Impacts
```

Example:

```text
Project: Belvedere
Subject: Pool
Sub-subjects:
- program
- pool heat pump
- pool-compatible terrace
- foundation-depth hypothesis
- budget
```

A project memory should not silently become agency memory.

An agency memory should not be contradicted by a project memory without an explicit exception or arbitration.

## Versioning rule

Each subject may have multiple memory versions.

Default display order should be reverse chronological.

```text
newest version first
older versions preserved
superseded versions remain inspectable
revoked versions remain audit-visible
archived versions are inactive, not deleted
```

A version should carry:

```text
memory_id
subject_id
version
status
created_at
source_date
received_date
effective_date
reviewed_at
supersedes
superseded_by
revocation_reason
archive_reason
```

## Dependency model

Some memories depend on other memories or decisions.

Fields to support:

```text
depends_on
impacts
valid_if
invalid_if
supersedes
superseded_by
derived_from
impact_level
revalidation_required
revalidation_reason
```

Dependency types:

```text
program_dependency
technical_dependency
budget_dependency
planning_dependency
contractual_dependency
regulatory_dependency
client_preference_dependency
assumption_dependency
```

## Impact review

When a new memory candidate changes a base condition, dependent memories must be reviewed.

Example:

```text
New candidate:
The client no longer wants a pool.

Impacted memories:
- pool heat pump selection → obsolete probable;
- terrace compatible with pool → revalidate;
- foundation-depth hypothesis tied to pool → critical arbitration;
- pool budget line → archive or revise.
```

Impact statuses:

```text
unaffected
obsolete_probable
revalidate
update_proposed
critical_arbitration
supersede
archive
revoke
```

Critical impacts should never be silently downgraded.

Examples of critical impact areas:

```text
structure
safety
budget
planning / contract
urbanism / planning permission
insurance
professional liability
external communication
doctrine / agency rule
```

## Conflict model

A candidate or canonical memory may conflict with:

- newer evidence;
- older but stronger evidence;
- project memory;
- agency memory;
- system memory;
- statutory or regulatory information;
- a human decision;
- another subject's dependency.

Conflict statuses:

```text
no_conflict
possible_conflict
confirmed_conflict
stale
superseded
requires_arbitration
```

A memory in conflict should not be used as stable truth without surfacing the conflict.

## Use in answers

Before using memory in an answer, the system should check:

```text
1. What is the user asking?
2. Is it project-scoped, agency-scoped, system-scoped or general?
3. Which subject does it touch?
4. Is there a Registre Probatoire entry for that scope and subject?
5. Is there newer evidence or a conflict?
6. Is the memory usable, usable with caution, or blocked?
```

Possible answer postures:

```text
Memory used — canonical, scoped, no conflict.
Memory used with caution — candidate or weakly supported.
Memory not used — superseded, revoked or contradicted.
Arbitration required — conflict or critical impact.
```

## Status vocabulary

Evidence statuses:

```text
inbox
under_review
keep
candidate_extraction
save
duplicate
rejected
archived
```

Extraction statuses:

```text
proposed
weak
strong
needs_more_evidence
conflicted
rejected
```

Memory statuses:

```text
candidate
strong_candidate
under_review
pre_canonical
canonical
usable_with_caution
needs_update
revalidate
superseded
revoked
archived
rejected
```

Impact statuses:

```text
impact_detected
obsolete_probable
revalidate
critical_arbitration
update_proposed
archival_proposed
revocation_proposed
resolved
```

Backend sync statuses:

```text
not_projected
pgvector_synced
mem0_synced
hermes_memory_synced
out_of_sync
projection_blocked
```

## Minimum memory record

A governed memory record should include:

```text
memory_id
claim
scope
project_id / client_id / dossier_id where applicable
subject_id
subject_label
version
status
usable_status
risk_level
confidence_summary
source_date
received_date
effective_date
author_detected
interlocutors_detected
primary_evidence_id
secondary_evidence_ids
evidence_pack_id if applicable
derived_from
supersedes
superseded_by
depends_on
impacts
conflicts_with
review_required
reviewed_by
approved_by
approval_level
revocation_path
backend_projection_status
```

## Evidence to memory UI notes

A cockpit may expose one menu entry:

```text
Evidence → Memory
```

Suggested views:

```text
Sources to review
Extraction candidates
Memory candidates
Subjects
Impact queue
Conflicts
Updates
Archived / revoked
Backend sync
```

The fullscreen swipe view should apply to evidence review, not to canonical memory itself.

For each evidence card:

```text
Project / scope
counter
current evidence status
author detected
interlocutors
date
speech-act classification
extraction proposal
confidence explanation
actions
```

Possible actions:

```text
archive
keep
candidate extraction
save
create Register Candidate
request arbitration
link evidence
```

For memory review cards:

```text
validate
modify
reject
supersede
revoke
archive
link more evidence
open impact review
```

## Backend projection

A Registre Probatoire entry may be projected to backends for use.

Projection should be explicit and reversible.

```text
Canonical registry
→ pgvector index for retrieval
→ mem0 for agent-facing memory if enabled
→ Hermes memory excerpt if enabled
→ cockpit display excerpt
```

Projection must never bypass canonical status.

If a memory is superseded, revoked or archived, all projections must be marked out of date until reconciled.

## Example — pool removal

Initial memories:

```text
M1: The project includes a pool.
Status: canonical
Subject: Pool / program

M2: The selected pool heat pump model is X.
Status: candidate
Depends on: M1

M3: The terrace is selected for pool compatibility.
Status: canonical
Depends on: M1

M4: House foundation depth is assumed to align with pool foundations.
Status: canonical technical assumption
Depends on: M1 and structural hypothesis
Risk: structure
```

New evidence:

```text
Source: client email
Claim: The client no longer wants a pool.
Speech act: probable decision
Date: newer than M1
```

New memory candidate:

```text
M5: The client no longer wants a pool.
Status: strong_candidate / under_review
Supersedes: M1 if approved
```

Impact review:

```text
M1 → supersession proposed
M2 → obsolete probable; archive proposed
M3 → revalidate; design arbitration required
M4 → critical arbitration; structural review required
```

No automatic deletion occurs.

The historical path stays visible.

## Architecture-specific considerations

Architecture projects make dependency review critical because one program decision can affect:

- design options;
- technical assumptions;
- structure;
- planning permission;
- cost;
- schedule;
- consultant scope;
- contractor packages;
- client communication;
- professional liability.

Therefore, architecture domain packs should define subject vocabularies and risk triggers for common project subjects such as:

```text
program
planning / urbanism
structure
thermal / energy
water / drainage
facade
roof
openings
terrace
pool
budget
schedule
contractor lot
client validation
administrative authorization
reception / defects
```

## Boundary with data platform work

A future data platform may record evidence, candidates, memory records and projections.

It must not become:

- ERP;
- runtime;
- scheduler;
- queue;
- memory promotion engine;
- approval engine;
- autonomous contradiction resolver.

Recommended phrase:

```text
The database records.
The workflow proposes.
The evidence supports.
The approval validates.
The human decides.
```

## Open questions

- Which status names should become canonical vocabulary versus UI vocabulary?
- Should this note remain support doctrine or become part of MEMORY.md after review?
- What minimum fields are necessary before any schema proposal?
- Which architecture-domain subjects should be defined first?
- Which backend projections are allowed by default?
- What approval level is required for project, agency and system memory?

## Current repo state

Documented non-implemented.

No schema added.

No tests added.

No runtime added.

No database migration added.

No automatic memory promotion added.
