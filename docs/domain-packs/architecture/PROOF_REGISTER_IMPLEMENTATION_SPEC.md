# Architecture Proof Register Implementation Spec

Status: implementation candidate — documented, not implemented.
Boundary profile: candidate_support_note.

This document defines a compact implementation candidate for the architecture proof register and indexed document version model.

It is a specification only.

It does not create migrations, tables, RLS policies, Directus collections, object storage, OpenWebUI forms, Hermes skills, queues, schedulers, approval systems, memory systems or connectors.

## Purpose

The first implementation slice should be:

```text
document family
-> indexed document version
-> version event
-> phase attachment
-> effect class
-> purpose-specific currentness projection
-> proof entry
-> review trigger
```

The goal is to preserve every document index, attach it to a phase, classify its authority effect and prevent ordinary revisions from becoming contractual authority by accident.

## Source doctrine

This spec depends on:

```text
PROOF_REGISTER.md
INDEX_EFFECT_MATRIX.md
AGENCY_COLLABORATION_AND_VERSION_INTAKE_CONVERGENCE.md
DATA_PLATFORM_RECONCILIATION.md
DOCUMENT_INTELLIGENCE.md
REVIEW_QUEUE.md
```

## Convergence with the generic data-platform document owner

The proof-register vocabulary does not require a second physical document/version store.

The generic data-platform doctrine already names:

```text
doc_documents
doc_document_versions
```

as candidate implementation families. The architecture proof-register concepts specialize those responsibilities rather than duplicating them.

Candidate implementation mapping:

```text
document_family
-> stable professional semantics projected from the logical document owner

indexed_document_version
-> architecture-domain projection of one exact professional document revision

version_event
-> append-only effect/status/authority event attached to that same revision identity

purpose-specific currentness
-> calculated read projection over revision chronology + admitted events + governed basis
```

An implementation may use different physical table names and identifier encodings, but it must expose one identity mapping and must not persist a second competing document family or revision lineage.

```text
implementation table name != new semantic owner
proof-register projection != duplicate document store
```

The current `pantheon-mvp#268` A-stream is a candidate implementation mapping only while its PR stack remains unmerged and under review.

## MVP entities

### document_family

Stable professional document object across indices.

Examples:

```text
CCTP lot 03
Plan A101
CCAP
quote from contractor X
signed market lot 02
reception PV
DOE pack
```

Conceptual fields:

```text
document_family_id
scope_id
document_type
business_object_type
lot_id
phase_origin
canonical_title
status
created_at
```

There is deliberately no persisted `current_authoritative_version_id`.

Rules:

```text
A family groups versions.
A family is not proof by itself.
A professional claim must reference an indexed version.
Currentness is calculated per declared purpose.
```

### indexed_document_version

One preserved index of a document family.

Conceptual fields:

```text
document_version_id
document_family_id
index_label
phase_code
effect_class
revision_reason
source_authority_level
supersedes_version_id
issued_by
issued_at
approved_by
approved_at
signed_by
signed_at
effective_at
hash_sha256
source_file_ref
allowed_use
forbidden_use
status
created_at
```

Rules:

```text
Every index is stored.
No index is erased as normal workflow.
A later index may supersede a prior index for future use.
Supersession does not erase historical proof value.
Index order does not determine professional authority.
```

### version_event

Append-only event describing a status, effect or authority change.

Conceptual fields:

```text
version_event_id
document_version_id
event_type
previous_status
new_status
previous_effect_class
new_effect_class
previous_authority_status
new_authority_status
reason
evidence_refs
actor_ref
occurred_at
```

Event examples:

```text
created
issued
approved
signed
superseded
marked_obsolete
reopened
reclassified_effect_class
```

A version event records a reviewed state transition or supporting event. It is not itself a proof entry or a universal approval.

### purpose-specific currentness projection

Currentness is calculated separately for the requested use.

Candidate purposes:

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

The projection contract is:

```text
schemas/architecture-proof-register/document_currentness_projection.schema.yaml
```

A result must disclose:

```text
purpose
resolved / unresolved / conflicting
exact document version when resolved
qualifying effect/status/authority when applicable
basis references
missing requirements
conflicting references
```

Representative distinctions:

```text
latest_received
-> receipt chronology only
-> does not confer professional authority

current_for_consultation
-> requires a consultation-qualified version and its applicable issue/package basis

current_contractual
-> requires contractual effect plus applicable signature/contract basis

current_for_execution
-> requires execution-qualified effect plus applicable approval / visa / instruction basis
```

If the available inputs are insufficient or contradictory, the result is unresolved or conflicting rather than guessed.

```text
latest_received != current_contractual
highest index != current_for_execution
transmission != approval
signed != automatically current for every purpose
```

The projection is read-only calculated state. It is not a new authority object and must not be used as a hidden approval engine.

### proof_entry

Relation saying that evidence supports a claim, status or professional object.

Conceptual fields:

```text
proof_entry_id
professional_object_type
professional_object_ref
claim_or_status
evidence_refs
source_document_family_id
source_document_version_id
source_index_label
source_authority_level
scope_id
phase_code
lot_id
produced_by
reviewed_by
approval_state
allowed_use
forbidden_use
status
created_at
```

Rules:

```text
A proof entry records support.
It does not decide truth alone.
A governed status is required before use.
```

### review_trigger

Condition that should produce a human review item.

Examples:

```text
index_label_missing
effect_class_missing
phase_attachment_missing
key_index_missing_signature
ordinary_revision_used_as_contractual
superseded_index_used_as_current
semantic_result_used_as_proof
approval_missing
hash_missing
scope_ambiguous
```

Rule:

```text
A trigger may enqueue and notify.
A trigger must not apply the change.
```

## Controlled vocabularies

### effect_class

```text
working_revision
minor_correction
coordination_update
modification_candidate
issued_for_review
issued_for_client_approval
approved_phase_decision
issued_for_consultation
issued_for_contract
signed_contractual_version
issued_for_execution
issued_for_site
visa_status_record
signed_or_contradictory_record
as_built_record
obsolete_superseded
```

### phase_code

```text
DIAG
APS
APD
PRO
DCE
ACT
EXE
VISA
DET
OPC
AOR
DOE
GPA
AGENCY_LIBRARY
GLOBAL_REFERENCE
```

### source_authority_level

```text
law_or_regulation
operation_contract
signed_market_document
approved_phase_decision
signed_or_contradictory_site_evidence
approved_client_decision
contractor_signed_response
approved_technical_report
agency_standard
project_working_document
derived_text
semantic_search_result
model_interpretation_candidate
```

## Minimal validation rules

```text
No professional proof without an indexed version.
No contractual authority without a governed key index.
No key index without required evidence.
Superseded does not mean deleted.
If requested_use exceeds allowed_use, create a review trigger.
A semantic result is never proof until source version, index, effect class and scope are explicit.
No single family field may silently collapse all currentness purposes.
```

## Example flows

### CCTP PRO to DCE to contract

```text
Create family: CCTP lot 03.
Create indice A: phase PRO, effect working_revision.
Create indice B: phase DCE, effect issued_for_consultation, supersedes A.
Attach DCE package evidence to indice B.
current_for_consultation may resolve to B.
During ACT, compare quote against indice B.
After signature, mark or create signed contractual version.
current_contractual resolves only from the signed contractual basis.
Contractual proof must reference the signed version, not only the DCE issue.
```

### EXE / VISA

```text
Contractor submits EXE plan indice 01.
Version starts as issued_for_review.
MOE creates visa_status_record.
If execution is allowed with applicable basis, current_for_execution may resolve to that version.
If correction is required, create review/action item and keep version out of execution authority.
```

### Reception reserve

```text
Reception PV is signed with reserves.
Version effect is signed_or_contradictory_record.
Reserve entries reference the signed PV version.
Closure evidence later supports a proof entry.
Reserve closure still requires a governed human decision.
```

## Acceptance criteria for future implementation

```text
all indices are preserved
index effect class is explicit
phase attachment is explicit
key index evidence is enforced or review-triggered
ordinary revisions cannot silently become contractual authority
supersession is auditable
proof entries reference indexed versions
currentness is purpose-specific and basis-disclosing
insufficient currentness inputs resolve as unresolved/conflicting
review triggers do not apply consequential changes
external effects remain gated
```

## Boundary phrase

```text
Implement the record layer only after the authority model is explicit.
Store every index.
Govern the effect.
Calculate currentness for a declared purpose.
Never let the latest filename decide authority.
```