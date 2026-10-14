# Architecture Proof Register

Status: candidate support doctrine — architecture-domain proof register.
Boundary profile: candidate_support_note.

This document defines a candidate proof register for architecture practice.

It is documentation only.

It does not implement a SQL schema, migration, Directus cockpit, Postgres table, object storage, pgvector index, provenance graph, queue runtime, scheduler, OpenWebUI action, Hermes skill, connector, approval engine or memory engine.

## Purpose

Architecture practice does not only need documents. It needs proof that can survive time, contradiction, phase changes, contractor disputes, client arbitration, reception, DOE, GPA and later liability questions.

The proof register is the conceptual layer that links:

```text
source document
source version
professional object
claim or decision
Evidence Pack Candidate
governed status
human approval
append-only event
```

It exists to prevent a weak document, missing version, derived chunk or fluent summary from becoming a professional fact.

## Core rule

```text
A document is stored.
A fragment is cited.
An evidence item supports.
A proof register entry records the relationship.
A governed status gives usable authority.
A human decision commits.
```

## Relation to existing doctrine

This document specializes:

```text
DOCUMENT_INTELLIGENCE.md
DOCUMENT_REVIEW.md
DATA_PLATFORM_RECONCILIATION.md
REVIEW_QUEUE.md
```

It does not replace them.

## What the proof register is

A proof register is a governed map of relationships between professional objects and their evidence.

Examples:

```text
CCTP clause -> source document version -> approved PRO package
quote line -> contractor quote version -> ACT comparison finding
service order -> signed instruction -> execution event
meeting decision -> meeting minute -> action item
reserve -> reception PV -> contractor lot -> closure evidence
DOE item -> equipment document -> completeness status
GPA issue -> notification -> contractor response -> closure decision
```

The register does not decide truth by itself.

It makes proof reviewable, scoped and reversible.

## Objects covered first

Candidate first objects:

```text
CCTP clause
quote
quote line
work contract
service order
meeting minute
meeting decision
action item
observation
non-conformity
reserve
reception PV
DOE pack
DOE item
GPA issue
signature event
approval event
verification event
admission event
risk snapshot
planning snapshot
heritage snapshot
```

These are professional objects, not approved physical table names.

## Indexed document versions

Architecture documents evolve by index.

The proof register must distinguish:

```text
document family
indexed version
phase attachment
revision reason
authority effect
supersession behavior
```

A document family is the continuing professional object:

```text
CCTP lot 03
CCAP
contract / marché
architectural plan A101
meeting minute series
DOE pack
reception PV
```

An indexed version is one state of that family:

```text
CCTP lot 03 indice A
CCTP lot 03 indice B
Plan A101 indice C
Quote entreprise indice 02
Marché signé version finale
PV réception signé avec réserves
DOE pack version 2026-05-31
```

Every indexed version should be preserved.

No later index should erase the prior index.

## Index effect classes

Not every index has the same authority.

Candidate index effect classes:

```text
working_revision
minor_correction
coordination_update
modification_candidate
issued_for_review
issued_for_client_approval
issued_for_consultation
issued_for_contract
signed_contractual_version
issued_for_execution
issued_for_site
signed_or_contradictory_record
as_built_record
obsolete_superseded
```

A minor correction and a signed market document are both document versions, but they do not have the same effect.

The register must therefore store not only the index label, but the index effect.

## Phase attachment

Each indexed version must be attached to a phase or operational container.

Candidate phase attachment values:

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

A document may originate in one phase and remain usable later, but its authority must remain tied to the phase and decision that gave it status.

Example:

```text
A CCTP produced in PRO may become part of the DCE, then become contractual only after market signature.
```

The same file content may therefore support different objects at different authority levels.

## Key index versus ordinary revision

Some indices are key indices.

A key index changes the proof or authority state of the matter.

Examples:

```text
signed contract / marché
DCE issued to contractors
client-approved APD
PRO package authorized for consultation
service order issued
reception PV signed
DOE accepted
reserve closure accepted
```

Ordinary revisions may be useful but do not by themselves produce a gate effect.

Examples:

```text
layout correction
internal coordination update
spelling correction
working draft
minor graphic update
unapproved variant
```

Rule:

```text
Every index is stored.
Only a governed key index can change phase status, contractual status, approval status or external-action authority.
```

## Supersession

A later index may supersede an earlier index for future use.

It does not erase its historical proof value.

Example:

```text
CCTP indice B supersedes indice A for consultation.
Indice A may still explain why a prior question was asked or why a contractor response exists.
```

Required distinction:

```text
superseded_for_future_use != deleted
obsolete_for_decision != irrelevant_as_history
```

A proof register must preserve the chain of indices and the reason for supersession.

## Version event shape

A version event should answer:

```text
which document family changed?
what index was created?
why was it created?
which phase does it attach to?
what prior index does it supersede?
what authority level does it carry?
who issued it?
who approved or signed it?
what can now rely on it?
what cannot rely on it?
```

Conceptual shape:

```text
document_version_event:
  document_family_ref
  index_label
  revision_reason
  phase_code
  effect_class
  supersedes_version_ref
  source_authority_level
  issued_by
  approved_by
  signed_by
  issued_at
  effective_at
  allowed_use
  forbidden_use
  status
```

This is not an approved schema.

## Proof entry shape

A proof register entry should answer:

```text
what object is being supported?
what claim or status is being supported?
which source version supports it?
what fragment or document anchor supports it?
which index and phase does it belong to?
who produced it?
who validated it?
what scope contains it?
what authority level does it have?
what can it be used for?
what can it not be used for?
what would make it obsolete?
```

Conceptual shape:

```text
proof_entry:
  professional_object_type
  professional_object_ref
  claim_or_status
  evidence_refs
  source_document_family_ref
  source_document_version_ref
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
  supersedes
  superseded_by
  created_at
  status
```

This is not an approved schema.

## Source authority levels

Candidate authority hierarchy:

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

Rule:

```text
Derived text, semantic retrieval and model interpretation can support review.
They cannot outrank signed, approved or contradictory source evidence.
```

## Status vocabulary

Recommended proof statuses:

```text
candidate
source_incomplete
source_complete_for_task
requires_human_review
requires_more_evidence
requires_client_decision
requires_contractor_response
approved_for_internal_use
approved_for_meeting_preparation
approved_for_transmission_draft
approved_for_contractual_action
accepted_as_project_fact
rejected
obsolete
superseded
```

A status may be strong only inside its scope.

Example:

```text
approved_for_meeting_preparation != approved_for_contractual_action
```

## Phase-gate relation

The proof register should support phase gates.

Candidate gates:

```text
DIAG feasibility / initial programme
APS approval
APD freeze
PRO ready-for-consultation
DCE issued
ACT attribution decision
EXE / VISA status
DET monthly execution status
AOR / reception
DOE acceptance
reserve closeout
GPA issue closeout
```

Each gate should define a minimal Evidence Pack Candidate.

The proof register records whether the evidence exists and which status it has.

A phase gate may rely on several indexed documents, but only if each has the required effect class.

Example:

```text
ACT attribution decision requires more than a quote index.
It requires the relevant offer version, analysis evidence, client or MOA decision, and market signature when contractual status is claimed.
```

## Evidence pack minimums

### CCTP / DCE

Minimum evidence:

```text
source CCTP version
index label
index effect class
lot identification
clause or section anchors
approval state
related normative references when relevant
DCE package identity if issued
```

### Quote / ACT

Minimum evidence:

```text
quote source version
quote index label
quote index effect class
contractor identity
lot identity
quote line anchors
comparison finding if any
client attribution decision if any
contract signature if any
```

### Market / signed contract

Minimum evidence:

```text
market document family
signed market version
signature event
contractor identity
lot identity
amount or contractual scope if relevant
source DCE / offer references
approval or attribution decision
allowed contractual use
```

### Meeting minute / decision

Minimum evidence:

```text
meeting date
attendance or participants
minute version
minute index label
decision text
owner
deadline
later closure event when applicable
```

### Reserve / reception

Minimum evidence:

```text
reception PV
reception PV index or signed version
reception date
effect date
reserve description
lot / contractor
contradictory context when available
closure evidence
closure approval
```

### DOE / handover

Minimum evidence:

```text
DOE pack version
DOE pack index label
required item list
delivered item
equipment or system reference
maintenance / warranty evidence when applicable
acceptance or missing status
```

### GPA issue

Minimum evidence:

```text
issue description
notification or report
related reserve or post-reception defect
contractor response
closure evidence
closure decision
```

## Review queue triggers

A proof register entry may generate a Review Queue item when:

```text
source version is missing
index label is missing
index effect class is missing
phase attachment is missing
source is superseded
hash is missing
approval is missing
authority level is too low for requested use
ordinary revision is being used as key index
key index lacks signature or approval where required
contradictory evidence exists
scope is ambiguous
retention class is missing
signature or timestamp is missing where required
semantic result is being used as if it were proof
urgent claim lacks evidence
```

The queue exposes the decision.

It does not apply the decision.

## Memory boundary

A proof register may support Register Candidates.

It must not promote a Registre Probatoire entry.

Examples:

```text
recurring missing quote item
recurring DOE incompleteness pattern
frequent reserve category
standard agency checklist candidate
```

Promotion requires a separate governed memory decision.

## External action boundary

The proof register must not authorize by itself:

```text
email sending
service order issuance
quote approval
contractor selection
payment validation
reserve closure
DOE acceptance
GPA closure
administrative filing
memory promotion
```

It can support an approval gate by showing evidence.

## Non-goals

This document does not authorize:

```text
creating physical database tables
stabilizing SQL schema names
building a Directus cockpit
building an ERP
running workflow automation
approving documents automatically
cross-affair search by default
using vector search as proof
replacing architect judgement
```

## Boundary phrase

```text
The proof register records what supports what.
It does not decide what is true enough to act.
Pantheon governs the status.
The human commits the decision.
```
