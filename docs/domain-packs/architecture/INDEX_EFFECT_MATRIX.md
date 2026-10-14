# Architecture Index Effect Matrix

Status: candidate support doctrine — index effect matrix for architecture documents.
Boundary profile: candidate_support_note.

This document defines a candidate matrix for interpreting document indices / versions in architecture practice.

It is documentation only.

It does not implement a SQL schema, migration, Postgres table, Directus cockpit, document versioning engine, storage backend, approval engine, OpenWebUI action, Hermes skill, queue runtime, scheduler or connector.

## Purpose

Architecture documents evolve by indices.

An index is not merely a number or a suffix in a filename. It is a versioned state of a professional document family, attached to a phase, a purpose, a level of authority and sometimes a legal or contractual effect.

Pantheon must therefore distinguish:

```text
ordinary revision
review issue
approval issue
consultation issue
contractual signed version
execution issue
site record
as-built record
```

The same document content may move through several authority states.

Example:

```text
CCTP produced during PRO
-> issued inside DCE
-> used for ACT analysis
-> becomes contractual only through market signature / contract attachment
```

## Core rule

```text
Every index is stored.
Every index is attached to a phase or operational container.
Every index has an effect class.
Only a governed key index can change phase status, contractual status, approval status or external-action authority.
```

## Index effect matrix

| Effect class | Typical use | Required evidence | May support | Must not support by itself |
|---|---|---|---|---|
| `working_revision` | internal drafting, coordination, incomplete study | author, date, phase, source family | internal review | client approval, consultation, contract, site execution |
| `minor_correction` | typo, layout, non-substantive correction | prior index, correction reason, author | traceability, replacement for internal use | phase gate, contractual change, external instruction |
| `coordination_update` | inter-discipline update, clash or drawing coordination | coordination note, affected lots, prior index | technical review, meeting preparation | external commitment without approval |
| `modification_candidate` | proposed change, variant, draft amendment | change reason, proposer, affected scope, evidence | review queue, client or contractor question | automatic scope change, cost change, OS |
| `issued_for_review` | sent for internal/client/partner review | transmission proof, recipient, deadline | review decision, comments | approval, consultation, execution |
| `issued_for_client_approval` | formal client/MOA validation request | version, transmission proof, approval request | client decision gate | contractual status before approval |
| `approved_phase_decision` | APS/APD/PRO or other phase approval | approval event, approver, date, evidence pack | phase status, next phase preparation | market signature, execution order |
| `issued_for_consultation` | DCE or consultation package | package hash, issue date, recipient/profil, included documents | offer analysis, contractor questions, ACT process | contractual status before attribution/signature |
| `issued_for_contract` | document prepared for contract attachment | attribution decision, final version, contract package | signature preparation | signed contractual authority before signature |
| `signed_contractual_version` | signed market / contract / attachment | signature event, parties, date, scope, source package | contractual status, payment/scope reference, proof register | unilateral modification without change process |
| `issued_for_execution` | execution package approved for work | approval / visa / instruction, affected lots | execution preparation, site coordination | payment, reserve closure, contract amendment |
| `issued_for_site` | site-issued plan, OS, instruction, minute | issue event, recipient, phase, lot, authority level | site action tracking | unbounded external action beyond its approval |
| `visa_status_record` | EXE/VISA decision or comment | submitted version, visa status, comments, reviewer | execution permission or correction demand according to status | general contract modification |
| `signed_or_contradictory_record` | PV, reception, OPR, contradictory observation | participants, signature/contradictory context, date | reception/reserve proof, later dispute evidence | automatic reserve closure |
| `as_built_record` | DOE / recolement / as-built | source as-built document, validation/completeness status | DOE/handover review, maintenance evidence | design approval if not validated |
| `obsolete_superseded` | no longer current for future work | superseding index, reason, date | historical explanation, audit trail | current decision unless explicitly allowed |

## Key index classes

Key indices are indices that can change authority or phase status when approved.

Candidate key indices:

```text
approved_phase_decision
issued_for_consultation
signed_contractual_version
issued_for_execution
visa_status_record
signed_or_contradictory_record
as_built_record when accepted
```

Key indices require stricter evidence.

They should usually generate a proof register entry.

## Ordinary indices

Ordinary indices are still stored and reviewable.

They may explain history, coordination, comments or errors.

They do not change phase or contractual status by themselves.

Candidate ordinary indices:

```text
working_revision
minor_correction
coordination_update
modification_candidate
issued_for_review
```

An ordinary index may become the basis of a key index only through a governed gate.

## Phase attachment matrix

| Phase / container | Common index effects | Gate risk |
|---|---|---|
| `DIAG` | working_revision, issued_for_review, approved_phase_decision | false existing-condition baseline |
| `APS` | working_revision, issued_for_client_approval, approved_phase_decision | premature programme/budget assumption |
| `APD` | working_revision, issued_for_client_approval, approved_phase_decision | wrong freeze of surfaces, cost or materials |
| `PRO` | working_revision, coordination_update, issued_for_review, approved_phase_decision | technical package treated as consultation-ready too early |
| `DCE` | issued_for_consultation, obsolete_superseded | contractor consulted on wrong package |
| `ACT` | issued_for_contract, signed_contractual_version | quote or contract used before signature / attribution |
| `EXE` | issued_for_review, visa_status_record, issued_for_execution | plan used on site without correct visa |
| `VISA` | visa_status_record | visa comment misread as approval |
| `DET` | issued_for_site, signed_or_contradictory_record | site instruction without authority |
| `AOR` | signed_or_contradictory_record | reception / reserve status misread |
| `DOE` | as_built_record, obsolete_superseded | incomplete DOE treated as accepted |
| `GPA` | signed_or_contradictory_record, as_built_record | issue closure without evidence |

## Required fields for a future implementation

Any future implementation should preserve at least:

```text
document_family_ref
index_label
phase_code
effect_class
revision_reason
source_authority_level
supersedes_version_ref
issued_by
issued_at
approved_by
approved_at
signed_by
signed_at
effective_at
allowed_use
forbidden_use
status
```

This is not an approved schema.

## Review queue triggers

A Review Queue item should be generated when:

```text
index_label is missing
effect_class is missing
phase attachment is missing
ordinary revision is used as key index
key index lacks approval or signature
contractual status is claimed without signed contractual version
consultation status is claimed without issued consultation package
execution status is claimed without visa / approval / instruction
reception status is claimed without signed or contradictory record
DOE acceptance is claimed from incomplete pack
superseded index is used as current authority
```

The queue exposes the decision.

It does not apply the decision.

## Forbidden shortcuts

```text
Latest file name is not necessarily current authority.
Highest index is not necessarily the signed version.
PDF export is not necessarily the source document.
Vector result is not a version authority.
Transmission is not approval.
Review is not signature.
Visa comment is not always execution approval.
Reception assistance is not reception pronouncement.
DOE deposit is not DOE acceptance.
```

## Relation to Architecture Proof Register

`PROOF_REGISTER.md` records what supports what.

This matrix helps classify the effect of each indexed document version before it is used as proof.

The matrix does not decide the result.

Pantheon governs the status.

The human commits the decision.

## Boundary phrase

```text
An index records a version.
An effect class qualifies what that version can support.
A governed key index may change status.
A human decision commits the consequence.
```
