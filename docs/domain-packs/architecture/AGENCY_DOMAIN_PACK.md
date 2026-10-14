# Architecture Agency Domain Pack

Status: candidate domain-pack doctrine  
Scope: architecture agency workflows, project registers, site reports, finance follow-up, administrative forms, evidence, retention and knowledge libraries  
Runtime status: non-executable

## Purpose

This document defines a candidate domain pack for architecture agencies practicing maîtrise d’œuvre in France.

It is not a complete product specification. It is not a final database schema. It is a domain-oriented map showing how the generic Pantheon data platform can support architecture practice without hardcoding one office's methods as universal rules.

The pack is intentionally modular. A small agency may activate only affairs, documents and quotes. A construction-phase office may activate site reports, finance follow-up and AOR. Another profession may replace this pack with its own domain objects while keeping the same workflow lifecycle and memory governance.

## Core rule

```text
Architecture work is not a pile of documents.
It is a linked register of affairs, sources, decisions, obligations, evidence, tasks, money and transmissions.
```

A PDF report, a quote, an invoice, a CERFA draft or a site meeting note is a publication or source object. The professional state lives in the structured register.

## French MOE posture

For French architectural practice, the pack should be treated as a professional evidence and operations layer, not as an agency ERP.

The useful reference posture is:

```text
legal and regulatory framework
  -> mission phases and contractual gates

contract and project documents
  -> operation-specific authority

phase approvals and site evidence
  -> professional traceability

raw and derived documents
  -> material source and searchable support

workflow proposals
  -> assistance only

human decisions
  -> professional responsibility
```

The pack should support private and public project contexts, while making public-market rules explicit when they apply.

The CCAG-MOE is relevant only when the public contract expressly refers to it. It should not silently replace private-sector contracts or agency-specific mission agreements.

## Source authority order

The pack should encode the relative authority of sources.

Suggested precedence:

```text
1. Laws, regulations and binding public texts
2. Operation contract and signed amendments
3. Approved phase decisions
4. Contradictory site evidence and signed records
5. Original documents and filed packages
6. Derived documents: OCR, Markdown, summaries, extracted tables
7. Retrieval outputs: chunks, embeddings, semantic matches
```

A vector chunk does not have the same authority as a signed PDF, an approved DOE, a contradictory reception record or an explicit client decision.

Candidate objects:

```text
reference_sources
normative_references
document_authority_levels
document_normative_links
source_snapshots
evidence_packs
```

The system should store not only the document but also its authority source, scope, version and validity.

## Pack modules

Candidate modules:

```text
architecture_affairs
architecture_parties
architecture_documents
architecture_source_authority
architecture_mail_intake
architecture_phase_gates
architecture_cctp_and_quotes
architecture_consultation_and_contracts
architecture_site_meetings
architecture_exe_visa
architecture_finance_followup
architecture_handover_aor_gpa
architecture_forms_and_urbanism
architecture_geo_regulatory_snapshots
architecture_knowledge_library
architecture_contacts_sync
architecture_document_retention
architecture_evidence_quality
```

Each module can be activated, disabled, tested or replaced.

## Affair register

The affair register is the central matter object.

Candidate fields:

```text
affair code
affair name
client / project owner
address
site geometry
administrative identifiers
private/public context
contract references
current phase
current phase gate
current status
mission scope
surfaces
program version
budget target
planning constraints
insurance / MAF references
storage policy
confidentiality level
retention profile
```

Common architecture phases and operational containers:

```text
prospect / opportunity
contract / mission setup
DIAG / existing-condition survey
ESQ if applicable
APS
APD
DP / PC / administrative filing
PRO
DCE package
ACT
EXE / VISA
DET / OPC if included
AOR / reception
DOE / handover
GPA
archive / retention
```

The phase is an organization tool. It is not by itself proof that a task is complete.

## Phase gates and evidence packs

Each important phase should expose a gate.

A gate is not merely a checklist. It is the point where a professional state changes because sufficient evidence has been gathered and an authorized actor has validated the transition.

Candidate objects:

```text
phase_gates
phase_gate_requirements
phase_gate_submissions
phase_gate_reviews
verification_events
admission_events
approval_events
evidence_packs
evidence_items
```

Example gates:

```text
program validated
APS submitted
APS approved / admitted
APD frozen
administrative filing submitted
PRO ready for consultation
DCE issued
consultation launched
offer analysis delivered
contract award decision recorded
EXE received
VISA issued
site meeting report published
monthly payment review completed
OPR completed
reception proposed
reception pronounced
DOE submitted
DOE accepted
reserves lifted
GPA issue closed
```

Default rule:

```text
No gate moves from candidate to validated without an evidence pack.
```

## Phase map: deliverables, evidence and gates

### DIAG / existing condition

Candidate deliverables:

```text
surveys
existing-condition report
site photos
existing plans
technical diagnostics
program assumptions
risk and regulatory snapshots
```

Minimum evidence:

```text
source of survey
photo dates
program source
third-party reports
site regulatory snapshots
assumptions list
```

Gate:

```text
feasibility or initial program validated by project owner
```

### APS

Candidate deliverables:

```text
design options
site insertion
plans / volumes
first technical principles
preliminary estimate
preliminary schedule
```

Minimum evidence:

```text
program snapshot
variants compared
estimate source
site and regulatory references
internal review trace
```

Gate:

```text
APS approved or admitted by project owner
```

### APD

Candidate deliverables:

```text
more settled plans / sections / facades
surfaces
constructive principles
materials and systems
cost estimate by lots
maintenance / operation choices
administrative filing basis
```

Minimum evidence:

```text
surface freeze
client arbitrations
cost estimate by lot
normative reference list
administrative filing package
submission receipts if any
```

Gate:

```text
program and budget frozen, administrative filing ready or submitted if applicable
```

### PRO

Candidate deliverables:

```text
detailed drawings
technical details
CCTP
quantities
DPGF / DQE if applicable
cost target
coordination matrix
```

Minimum evidence:

```text
revision history
coordination review
normative references
cost target
lot structure
```

Gate:

```text
ready for consultation or ready for execution depending on mission and contract
```

### DCE / ACT

DCE is an operational container even when it is not a standalone legal mission element.

Candidate deliverables:

```text
consultation package
administrative documents
technical documents
Q&A log
offers received
offer comparison
analysis report
award recommendation
contract finalization records
```

Minimum evidence:

```text
DCE package hash
published or transmitted version
publication or transmission proof
offers received
analysis grid
project-owner award decision
signed contracts
```

Gate:

```text
consultation authorized, then award decision recorded
```

### EXE / VISA

Candidate deliverables:

```text
execution drawings
calculation notes
contractor details
synthesis plans
visa comments
visa register
```

Minimum evidence:

```text
received version
comments by sheet or item
bureau de controle / SPS constraints if applicable
conflict closure trace
visa status
```

Gate:

```text
VISA issued or contractor document returned with comments
```

### DET / OPC / site

Candidate deliverables:

```text
orders of service
site meeting reports
site observations
planning updates
payment applications
change requests
non-conformities
photos
contractor questions
```

Minimum evidence:

```text
signed or transmitted site records
attendance / convening evidence
photos
planning trace
change request decision
payment review trace
```

Gate:

```text
site execution milestone or monthly review validated
```

### AOR / reception

Candidate deliverables:

```text
OPR records
reception proposal
reception minutes
reserve list
defects and observations
DAACT package if applicable
initial DOE collection
```

Minimum evidence:

```text
contradictory OPR
signed reception minutes
company convening evidence
reserve register by lot
effective reception date
municipal receipts if applicable
```

Gate:

```text
reception pronounced by project owner
```

The architect or MOE assists. The project owner pronounces reception. The system must not model reception as an automated MOE act.

### DOE / handover / GPA

Candidate deliverables:

```text
as-built drawings
operation notices
maintenance instructions
equipment sheets
warranties
DOE package
DIUO items if applicable
reserve-lifting proofs
GPA issue records
```

Minimum evidence:

```text
DOE completeness matrix
as-built links
notices and warranties
open/closed reserve status
photos of reserve lifting
handover correspondence
```

Gate:

```text
DOE accepted, reserves lifted, GPA issues closed
```

## Parties and roles

Architecture work depends on roles changing by project.

Candidate objects:

```text
organizations
contacts
affair party roles
mission roles
lot roles
contractor roles
consultant roles
administration roles
client roles
external reviewer roles
```

Examples:

```text
maitre_ouvrage
architect / MOE
mandataire
co-traitant
BET structure
BET thermique
bureau de controle
SPS
OPC
contractor
subcontractor
supplier
municipality
urban planning service
concessionnaire
syndic
insurer
MAF contact
legal counsel
```

The local database must keep a professional copy of contact and organization information even when synchronized with Google Contacts.

Google Contacts is a contact source and optional synchronization target. It does not replace the project-role model.

## Documents and versions

The architecture pack must treat document versions as first-class objects.

Mandatory metadata candidates for every document version:

```text
document_uuid
document_type
deliverable_type
phase_code
affair_id
lot_id nullable
discipline_code nullable
title
language
version_seq
revision_label
supersedes_version_id
status
approval_state
produced_at
received_at
effective_at
valid_until
issuer_org_id
document_owner_org_id
author_person_id nullable
signer_ids
approver_ids
sha256
byte_size
mime_type
original_filename
storage_uri
page_count nullable
canonical_file_id
source_doc_version_id nullable
source_snapshot_id nullable
source_url nullable
source_system nullable
derived_from_job_id nullable
page_anchor_range nullable
clause_anchor nullable
ifc_guid nullable
parcel_ref nullable
contract_ref nullable
permit_ref nullable
cerfa_number nullable
norm_ref_ids
signature_required
signature_level
certificate_ref nullable
timestamp_ref nullable
confidentiality_level
contains_personal_data
retention_class
legal_hold
destruction_after nullable
access_scope
```

This metadata model is inspired by the same kind of separation used by IFC document metadata: the document is represented by identity, ownership, revision, location, validity, confidentiality and status, not by forcing the full binary content into the structured register.

## Specialized document extensions

Some document types need specialized fields.

Drawing sheet:

```text
sheet_number
sheet_title
scale
north_ref
discipline
drawn_by
checked_by
cartouche_json
```

IFC / BIM model:

```text
ifc_schema_version
mvd_or_ids
model_units
software_origin
spatial_reference
model_hash
bim_exchange_requirement_id
```

Reception minutes:

```text
reception_date
effect_date
contradictory_flag
reservation_count
reserve_deadline_by_lot
project_owner_decision_ref
```

DOE equipment item:

```text
equipment_tag
system_type
serial_number
maintenance_interval
warranty_end
manual_document_id
```

CERFA / administrative form:

```text
cerfa_number
form_version
filing_authority
filing_date
receipt_ref
missing_attachment_count
```

LRE / notification:

```text
provider
submission_proof_ref
receipt_proof_ref
refusal_proof_ref
legal_retention_until
```

## Raw, derived and indexed content

The original document must not be replaced by OCR, Markdown, a re-exported IFC, a visualization PDF or an AI summary.

Pipeline posture:

```text
immutable original
  -> technical rendering if needed
  -> text extraction / OCR only when needed
  -> Markdown candidate
  -> chunks
  -> scoped retrieval index
  -> evidence selection
  -> approval if used for consequential output
```

Rules:

```text
native text before OCR
OCR as fallback, not reflex
Markdown must preserve legal and technical numbering
chunk by clause, article, lot, form, sheet, observation, reserve or equipment where possible
large binaries stay in object storage
only descriptive metadata for point clouds and heavy binaries should be indexed by default
```

## Documents and naming

The pack should support both user-readable folders and machine-readable naming.

Recommended project folder pattern:

```text
/projects/{PROJECT_CODE}_{PROJECT_NAME}/
  00_admin/
  01_client/
  02_studies/
  03_authorizations/
  04_dce/
  05_act/
    cctp/
    quotes/
    analysis/
  06_exe_visa/
  07_det/
    site_reports/
    photos/
    payment_applications/
    invoices/
    change_orders/
    orders_of_service/
  08_aor/
    opr/
    reserves/
    doe/
    reception/
    daact/
  09_finance/
  10_bim_cad/
  11_emails/
  99_archives/
```

Recommended file pattern:

```text
{DATE}_{PROJECT_CODE}_{PHASE}_{TYPE}_{LOT}_{ORGANIZATION}_{REFERENCE}_{VERSION}.{EXT}
```

The system should propose file renames and final storage paths. It should not silently rename or move high-value documents without authorization.

## Mail intake: quote, invoice, project message

Incoming email can become a controlled source event.

Candidate flow:

```text
email received
  -> message record
  -> attachment records
  -> sender and signature extraction
  -> contact / organization matching
  -> document type classification
  -> affair attribution proposal
  -> storage proposal
  -> candidate domain object creation
  -> evidence and risk check
  -> human review
```

Possible classifications:

```text
quote
invoice
change-order request
payment application
technical question
client decision
contractor decision request
site update
administrative notice
insurance / MAF notice
legal notice
notification / LRE
spam / announcement / non-project
```

The system may propose attribution. It should not silently bind a document to an affair if confidence is insufficient.

## CCTP, DCE and quote analysis

Quotes are not isolated PDFs. They should be linked to affair, lot, contractor, source email, storage object, DCE package and CCTP baseline.

Candidate objects:

```text
architecture_lots
architecture_disciplines
architecture_cctp_versions
architecture_cctp_clauses
architecture_dce_packages
architecture_dpgf_or_dqe_items
architecture_consultations
architecture_offers
architecture_offer_analysis
architecture_quotes
architecture_quote_lines
architecture_quote_cctp_matches
architecture_quote_anomalies
architecture_normative_references
```

Quote analysis may detect:

```text
missing CCTP article
partial coverage
variant not requested
exclusion
quantity mismatch
unit mismatch
ambiguous wording
validity missing
insurance or administrative information missing
normative reference mismatch
DCE version mismatch
price abnormality candidate
```

The analysis is a candidate professional comment. It is not a decision to accept, reject or negotiate the quote.

## Consultation, contracts and orders of service

Candidate objects:

```text
consultations
consultation_lots
consultation_publication_events
consultation_question_answers
offers
offer_documents
offer_analysis_reports
award_decisions
work_contracts
contract_amendments
orders_of_service
notification_events
```

The system should distinguish:

```text
consultation package issued
offer received
offer analyzed
award recommendation prepared
project owner award decision recorded
contract signed
order of service issued
work started
```

In public procurement contexts, Pantheon should keep exports, identifiers, timestamps and evidence from the buyer profile or relevant platform. It must not replace that official platform.

## EXE / VISA / BIM / CAD

Candidate objects:

```text
execution_document_submissions
visa_registers
visa_reviews
visa_comments
synthesis_issues
bim_models
ifc_entities
bim_exchange_requirements
bcf_issues
cad_standards
project_bep
```

Rules:

```text
EXE and VISA are distinct.
A received contractor drawing is not a visa.
A visa comment is not a contractor correction.
A BIM or CAD convention is a project or agency standard, not a universal national rule.
IFC model records should preserve schema version and model hash.
```

## Site meetings and reports

A site report is not the source object. It is a published view of a living register.

Candidate objects:

```text
site_meetings
site_meeting_participants
site_notes
site_minutes
site_observations
site_points
site_point_updates
site_tasks
site_progress_by_lot
site_non_conformities
site_reserves
site_expected_documents
site_report_snapshots
site_report_publications
site_next_meeting_preparation
photo_assets
```

Core rule:

```text
A site report is a temporary publication of the current site register.
```

A point should live across multiple reports.

Example:

```text
CR03: point created, contractor response expected.
CR04: still open, delay noted.
CR05: marked as completed by contractor, to verify on site.
CR06: closed after verification.
```

The system may generate next-meeting preparation from:

```text
open points
overdue tasks
points requiring verification
missing documents
unanswered contractor questions
pending client decisions
financial alerts
unclosed reserves
open non-conformities
missing DOE items
```

Published minutes and reports require approval before transmission.

## Kanban and Gantt views

Kanban and Gantt should be views over structured tasks, not separate truth sources.

Candidate task statuses:

```text
backlog
todo
in_progress
to_verify
blocked
done
cancelled
superseded
```

Candidate planning fields:

```text
planned_start
planned_due
actual_start
actual_end
progress_percent
dependency links
lot
responsible organization
source point
phase gate
```

A workflow may propose status changes. It should not close professional site points without review unless explicitly authorized by policy.

## Finance follow-up

Construction progress has a financial trajectory.

Candidate objects:

```text
finance_budgets
finance_budget_lines
finance_contracts
finance_contract_lines
finance_change_orders
finance_change_order_lines
finance_payment_applications
finance_payment_application_lines
finance_invoices
finance_payments
finance_deductions
finance_penalties
finance_retentions
finance_final_account
finance_alerts
finance_meeting_preparation_items
```

Core rule:

```text
A financial row is not just an amount.
It is an engagement, a modification, a payment request, a validation state and a trace.
```

The system should distinguish:

```text
quote received
quote retained
contract / market
change order
payment application
invoice
payment
retention / deduction / penalty
final account
```

Alerts may include:

```text
invoice without contract
invoice exceeds revised contract
change order invoiced but not validated
payment application inconsistent with previous situation
amount mismatch HT / VAT / TTC
financial progress ahead of site progress
missing client validation
penalty candidate requiring review
```

These alerts prepare review. They do not approve or reject payment.

## AOR, reception, DOE and GPA

Reception, DOE and GPA deserve dedicated objects.

Candidate objects:

```text
opr_sessions
opr_items
reception_proposals
reception_minutes
reception_signatures
reserve_registers
reserve_items
reserve_lifting_proofs
doe_packs
doe_items
doe_completeness_matrix
diuo_items
daact_filings
gpa_issues
gpa_issue_updates
handover_events
```

Rules:

```text
Reception is pronounced by the project owner.
The reception date starts major legal and contractual timelines.
Reserves are tracked by lot, responsible organization, deadline and closure proof.
DOE is a pack with completeness status, not a single folder.
GPA issues are not ordinary site points; they live after reception and require warranty tracking.
```

## Administrative forms, urbanism and public-source data

The pack may support project fact gathering and form preparation.

Candidate objects:

```text
project_facts
external_sources
external_connectors
external_source_queries
external_observations
source_snapshots
address_records
parcel_records
site_geometry
planning_snapshots
risk_snapshots
heritage_constraint_snapshots
form_templates
form_fields
form_field_mappings
form_instances
form_instance_values
administrative_filings
filing_attachments
attestations
```

Use cases:

```text
pre-fill CERFA draft
prepare missing field list
query public source candidates
store dated source snapshots
attach source timestamps
flag uncertainty
prepare administrative completeness review
```

A generated form is a draft until reviewed.

Public API or web-source results are observations before they are project facts.

## Retention, signatures and notifications

Candidate objects:

```text
retention_classes
retention_rules
legal_holds
signature_events
timestamp_events
certificate_refs
notification_events
lre_events
access_logs
```

Minimum posture:

```text
preserve originals
hash important files
record signature level when applicable
record timestamp evidence when applicable
document retention classes
keep construction-liability evidence for at least the relevant liability horizon
keep logs according to a documented policy
support legal hold when a dispute or claim exists
```

Signature level should be configurable by document class:

```text
simple
advanced
qualified
seal
timestamp
LRE / qualified electronic registered delivery evidence
```

The pack must not assume that application approval is equivalent to a qualified electronic signature.

## Knowledge library

An architecture user may provide their own knowledge base:

```text
best-practice guides
CCTP methods
CCTP article models
DTU references and permitted extracts
MAF notes
contract templates
site report templates
AOR procedures
urban-planning notes
BIM / CAD conventions
DOE matrices
retention policies
agency naming rules
```

The system should ingest, OCR, convert to Markdown, compare, classify and index these documents only under the approved scope.

General knowledge, agency knowledge and project knowledge must stay separated.

## Access scopes and cockpits

The pack should distinguish at least:

```text
global reference
agency library
affair
external affair portal
```

Candidate cockpit views:

```text
affairs: phase, gates, late evidence, expected approvals
livrables: versions, hashes, signatures, proof gaps
chantier: meetings, orders, observations, non-conformities, reserves, photos
consultation / markets: DCE, offers, analysis, contracts
DOE / GPA: completeness, warranties, reserve lifting, closure timers
references: standards, agency templates, regulatory snapshots
decisions: project-owner approvals and pending decisions
my lot: contractor-limited view for published documents, visas, reserves and DOE requests
evidence quality: documents without hash, source, retention class, approval or classification
```

Directus or another cockpit may expose these views. It does not become the authority.

## Workflow examples

### Incoming quote workflow

Initial mode: test or shadow.

```text
trigger: incoming email with attachment
steps:
- classify document as quote candidate
- detect affair
- detect contractor
- detect lot
- save original candidate
- propose file name and storage path
- extract metadata and lines
- compare to CCTP if available
- check DCE version if available
- create action proposals
```

Blocked until approval:

```text
final affair attribution
final quote record
final storage move
client or contractor email
quote acceptance or rejection
```

### Site report workflow

```text
trigger: meeting notes, transcript or manual request
steps:
- parse notes into candidate points
- retrieve previous open points
- propose status updates
- identify missing responsible parties
- generate next-meeting preparation
- draft report
- prepare PDF candidate
```

Blocked until approval:

```text
published report
email to participants
closing points
binding decisions
```

### Finance follow-up workflow

```text
trigger: invoice, payment application or change-order request
steps:
- classify financial document
- match contractor and contract
- extract amounts
- compare to contract and validated change orders
- flag anomalies
- prepare meeting questions or client note
```

Blocked until approval:

```text
payment approval
penalty application
contractor dispute email
client transmission
```

### Knowledge drop workflow

```text
trigger: user drops a document in chat or storage inbox
steps:
- classify general/project/mixed
- detect existing similar knowledge
- OCR and convert to Markdown
- propose library or project folder
- propose indexing scope
```

Blocked until approval:

```text
activation as general knowledge
replacement of existing guide
project-to-general promotion
```

### Reception and reserve workflow

```text
trigger: OPR notes, reception meeting or reserve-lifting proof
steps:
- create candidate OPR items
- propose reserve items by lot
- link photos and observations
- prepare reception minutes candidate
- track reserve deadlines
- prepare reserve-lifting review
```

Blocked until approval:

```text
reception pronounced
reserve closed
GPA issue closed
notification sent
```

## Minimal first architecture pack

A first useful slice should include:

```text
affairs
organizations
contacts
affair party roles
documents
document versions
storage objects
messages
attachments
lots
phase gates
evidence packs
quotes
invoices
site meetings
site points
reserve register
workflow proposals
knowledge libraries
project facts
approvals
audit events
provenance edges
```

This enables knowledge ingestion, quote intake, simple finance follow-up, site-point tracking, reserve tracking and evidence quality review without building a full ERP.

## Non-goals

The architecture agency pack should not initially attempt to:

- automate professional judgment;
- replace accounting software;
- replace legal review;
- replace official urban-planning verification;
- replace buyer profiles or official public procurement platforms;
- replace signature or LRE trusted services;
- auto-send site reports;
- auto-approve quotes, invoices, change orders or payments;
- pronounce reception;
- close reserves without review;
- infer universal practice from one agency's habits.

## Operating principle

```text
The pack models professional objects so that workflows can help maintain them.
It does not turn professional responsibility into automation.
```
