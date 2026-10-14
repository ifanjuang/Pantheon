# Knowledge Ingestion and Memory

Status: candidate governance support doctrine  
Scope: document ingestion, OCR, Markdown conversion, vectorization, general memory and project memory  
Runtime status: non-executable

## Purpose

This document defines how Pantheon Next should govern the ingestion of user-provided knowledge and project documents.

It does not implement OCR, vector search, Drive synchronization, OpenWebUI upload handling or contact synchronization. It defines the boundaries and registers those systems should respect.

## Core rule

```text
Every incoming document is a candidate.
Nothing becomes active memory without scope, source and status.
Nothing becomes general knowledge without review.
Nothing becomes project knowledge without project attribution.
```

## Memory layers

The platform should separate memory into layers.

```text
general memory
  Guides, methods, templates, reference notes, domain rules and reusable knowledge.

domain memory
  Profession-specific knowledge such as architecture, contracts, CCTP method, site reporting, finance follow-up or urban planning.

country memory
  Country-specific forms, administrative sources, public APIs, cadastre, risks, heritage and planning references.

agency memory
  User or agency-specific practices, templates, naming rules, preferred methods, model clauses and internal procedures.

project memory
  Documents, facts, decisions, messages, drawings, quotes, invoices, reports and constraints belonging to a specific project.

derived memory
  Extracted claims, observations, OCR text, Markdown conversions, summaries, embeddings and classifications derived from sources.

validated memory
  Candidate memory that a human or policy has accepted as usable within a defined scope.
```

These layers must not be merged into one uncontrolled vector index.

## Document ingestion pipeline

A future ingestion pipeline should follow this pattern:

```text
receive document
  -> store original candidate file
  -> compute hash
  -> extract metadata
  -> classify document type
  -> classify scope: general, project, mixed or unknown
  -> detect project, contact, organization and topic if possible
  -> OCR if needed
  -> extract text
  -> convert to Markdown
  -> preserve source references
  -> compare against existing knowledge
  -> extract candidate assertions
  -> run Evidence Admission Gate
  -> detect duplicate, update, conflict and dependency candidates
  -> create candidate chunks
  -> vectorize only under the approved scope
  -> wait for validation before activation
```

The original file, converted Markdown, extracted assertions and indexed chunks are distinct objects.

## Candidate tables

```text
knowledge_libraries
knowledge_documents
knowledge_document_versions
knowledge_chunks
knowledge_chunk_status
vector_indexes
vector_embeddings
ingestion_jobs
document_processing_outputs
document_similarity_checks
document_scope_classifications
project_facts
evidence_atoms
evidence_versions
evidence_sources
evidence_dependencies
evidence_conflicts
evidence_status_events
retrieval_traces
external_observations
```

These names are candidates, not final implementation requirements.

## Knowledge libraries

A user or agency may maintain several knowledge libraries.

Examples:

```text
/knowledge/general/architecture/cctp
/knowledge/general/architecture/contracts
/knowledge/general/architecture/site
/knowledge/general/architecture/aor
/knowledge/general/architecture/urbanism
/knowledge/general/architecture/maf
/knowledge/general/architecture/dtu
/knowledge/agency/agency/templates
/knowledge/agency/agency/procedures
/knowledge/countries/FR/cerfa
/knowledge/countries/FR/urbanism
/knowledge/countries/FR/risks
/knowledge/countries/FR/cadastre
/knowledge/countries/FR/heritage
```

Each library should define:

```text
owner
scope
storage provider
root path
confidentiality
indexing policy
activation policy
```

## Operational context corpus

A user or organization may also maintain an operational context corpus: a navigable working corpus used by an execution runtime to retrieve the living thread of work.

This corpus may contain chronology, client or actor notes, call summaries, meeting notes, project notes, proposal records, follow-up traces, reusable concepts, rejected positions and AI drafts.

It is useful because professional work is not only a set of stable facts. It is a flow of sources, exchanges, drafts, decisions, objections, dependencies, deadlines and changing statuses.

The operational context corpus must remain a retrieval and orientation layer. It is not a Registre Probatoire, a source of truth, an approval record, a runtime memory authority or a durable professional position by itself.

Typical structure:

```text
operational_context/
  timeline/
  actors/
  calls/
  meetings/
  projects/
  proposals/
  followups/
  concepts/
  ai_drafts/
  rejected_positions/
  indexes/
```

These folders are examples of organization, not governance classes. File paths and tags may help retrieval, but they do not decide source authority, proof status, validity, approval or action permission.

Minimum metadata for any important operational note:

```text
scope
project_id or dossier_id
source_type
event_date
recorded_at
source_ref
status
confidence or certainty signal
external_effect: none | draft_only | approval_required | sent
AI_generated: true | false
review_status: candidate | to_verify | accepted | rejected | superseded
```

The following separations are mandatory:

```text
source material != derived note
derived note != AI draft
AI draft != sent communication
sent communication != validated decision
operational timeline != proof
tag != authority
runtime recall != Registre Probatoire entry
```

Timeline entries should be chronological pointers, not broad claims. A good entry identifies what happened, when it happened, where the source is, what status it carries and what review remains open.

Example:

```text
2026-06-22 | PROJECT_X | client message | boundary screen / neighbour issue
Status: source received, not verified
Risk: medium to high
Review needed: applicable rule, contract scope, prior source photos, reason for removal, draft response status
External effect: draft only until human approval
```

AI drafts must be stored apart from sources and validated positions. They should carry a visible candidate status and should never be retrieved as evidence unless the task is explicitly to review drafting history.

Progressive retrieval should apply:

```text
quick question -> scoped index + latest active records
focused work   -> project timeline + relevant source records + open candidates
full mission   -> scoped corpus search + contradictions + chronology + Evidence Pack Candidate
```

The governing posture is:

```text
Runtime memory recalls.
The operational context corpus retrieves.
Sources support.
Candidates propose.
Pantheon qualifies status.
The Registre Probatoire alone carries governed reliance.
The human validates.
```

## General versus project classification

The system must classify scope before use.

Examples:

```text
DTU extract, MAF note, CCTP type, contract model
  -> likely general or domain memory.

Quote, invoice, project email, site report, drawing, client note
  -> likely project memory.

Project CCTP later reused as a model
  -> mixed at first; may become general only after explicit extraction, anonymization if needed, and validation.

Site lesson learned
  -> project first; general only after human promotion.
```

A document may be mixed. Mixed status must be visible, not silently resolved.

## Markdown conversion

Markdown is a working representation, not the source of truth.

A Markdown conversion should preserve:

```text
original file reference
hash
page numbers
headings
section hierarchy
figures or tables markers
extraction confidence
OCR warning if applicable
source timestamps
```

Suggested header:

```yaml
---
source_document_id: ...
source_filename: ...
source_hash: ...
source_pages: ...
scope: candidate
project_id: null
knowledge_domain: architecture.site
status: needs_review
created_from: ocr | text_extract | manual
---
```

## Similarity and replacement checks

The system should not accumulate uncontrolled duplicate knowledge.

When a new knowledge document is imported, the system should compare it to existing documents in the same library and nearby libraries.

Similarity outcomes:

```text
duplicate
near_duplicate
same_topic
possible_conflict
unrelated
```

Possible recommendations:

```text
create_new
compare
merge
replace
reject
archive_old
```

No replacement should occur without review.

## Evidence Admission Gate

The ingestion pipeline must include an admission gate between extraction and memory activation.

This pattern is informed by external memory-engine reviews, including `2026-06-06-truememory-memory-patterns.md` (removed; git history).

The gate answers one question:

```text
May this extracted assertion become governed memory?
```

It must not answer only yes or no. It should produce a reviewable gate decision.

Candidate decision vocabulary:

```text
admit
reject
hold_for_review
link_only
```

Candidate scoring dimensions:

```text
novelty
source authority
project impact
professional risk
cost impact
planning impact
technical impact
legal / contractual impact
contradiction potential
dependency potential
temporal permanence
reuse risk
scope clarity
```

Negative signals:

```text
small talk
style preference with no project effect
duplicate wording
unverified model inference
unattributed summary
source missing
project unknown
ambiguous actor
speculative statement
confidential content with unclear scope
```

Candidate output:

```yaml
gate_decision: admit | reject | hold_for_review | link_only
gate_reason: ...
scores:
  novelty: 0.0
  source_authority: 0.0
  project_impact: 0.0
  professional_risk: 0.0
  contradiction_potential: 0.0
  dependency_potential: 0.0
  scope_clarity: 0.0
required_next_action:
  - classify_project
  - attach_source
  - human_review
  - compare_existing
  - detect_dependencies
```

The gate must keep its trace. A future reviewer should be able to see why a candidate was admitted, rejected, held or linked.

```text
unexplained memory is not Pantheon-compatible memory
```

## Memory decision vocabulary

Project memory evolves. A later assertion may update, supersede, invalidate or downgrade an earlier one without making the earlier record useless.

The memory decision vocabulary must therefore be richer than create/update/delete.

```text
ADD          create a new evidence atom
MERGE        combine near-duplicates under one governed atom
UPDATE       add a newer version while preserving history
SUPERSEDE    replace an older valid statement with a newer one
INVALIDATE   mark a statement as no longer valid because its premise collapsed
DOWNGRADE    keep the statement historically visible but remove default active use
LINK_ONLY    do not create a new fact, but connect it to an existing one
DISPUTE      mark a conflict requiring human arbitration
REJECT       do not store as project memory
ARCHIVE      keep for history, exclude from active retrieval by default
```

This rule matters because professional project truth is temporal.

```text
obsolete does not mean useless
superseded does not mean deleted
historical does not mean active
```

## Evidence atoms and dependencies

Project memory should be decomposed into evidence atoms, not stored as broad memory blobs.

Weak memory:

```text
Client talked about terrace, swimming pool, foundations and heat pump.
```

Governed decomposition:

```text
E1: The client no longer wants a swimming pool.
E2: The pool heat-pump choice depends on the swimming-pool assumption.
E3: The terrace option was initially designed to remain compatible with a pool.
E4: A foundation-depth assumption had been considered in relation to the pool.
E5: The terrace design must be reviewed if the pool assumption is abandoned.
```

Each atom should have its own:

```text
scope
source
status
confidence
authority level
validity interval
dependencies
```

Dependency edges should support:

```text
depends_on
supports
contradicts
supersedes
invalidates
downgrades
requires_review_of
is_source_for
is_derived_from
```

Candidate edge record:

```yaml
edge_id: ...
project_id: ...
from_evidence_id: ...
to_evidence_id: ...
relationship: depends_on | invalidates | supersedes | contradicts | supports | downgrades | requires_review_of
confidence: 0.0
source_id: ...
created_by: human | policy | extraction | model_candidate
status: candidate | accepted | disputed | rejected
```

A vector search can retrieve related fragments. A dependency graph can say:

```text
This premise collapsed, therefore these downstream assumptions require review.
```

## Worked example — abandoned swimming pool

Input event:

```text
The client no longer wants a swimming pool.
```

This should not be stored as a simple preference.

Expected extraction:

```yaml
assertion: The client no longer wants a swimming pool.
type: decision_change
project_scope: active_project_required
actor: client
status: candidate_until_source_attached
impact: high
```

Expected graph review:

```text
Find active or candidate memories containing:
- pool
- swimming-pool equipment
- pool heat pump
- terrace compatible with pool
- foundations coordinated with pool
- drainage related to pool
- garden / landscape options tied to pool
```

Expected memory decisions:

```text
ADD decision: pool abandoned
DOWNGRADE previous pool assumption
INVALIDATE pool heat-pump selection if no independent use remains
REVIEW terrace compatibility assumptions
REVIEW foundation-depth assumptions linked to pool
REVIEW drainage / network / outdoor lot assumptions
KEEP historical design trace
```

Expected Evidence Pack:

```yaml
active_decision:
  - client abandoned swimming pool
impacted_assumptions:
  - pool heat pump
  - terrace compatibility
  - foundation-depth coordination
  - drainage / external works
status:
  pool: inactive
  heat_pump: invalidated_candidate
  terrace: requires_review
  foundations: requires_review
human_action:
  - confirm source
  - update project assumptions
  - notify affected lot review if needed
```

## Chronology discipline

Chronology must be explicit. Semantic retrieval must not decide event order.

Every evidence atom should include, when available:

```text
source_date
event_date
document_date
received_at
extracted_at
validated_at
valid_from
valid_until
superseded_at
phase_index
revision_index
```

The system should be able to answer:

```text
What was true on this date?
What became true later?
Which version was active when this email was sent?
Which assumption was active when the quote was reviewed?
Which site-report issue appeared first?
When did it disappear from reports?
When was it treated as resolved?
```

```text
chronology is not an embedding problem
```

## Vectorization discipline

Vector indexes must respect scope.

Suggested index families:

```text
general_domain_index
agency_index
country_index
project_index
mixed_candidate_index
```

A project document should not be retrievable in another project unless it has been explicitly promoted to general or agency memory.

Chunk metadata should include:

```text
document_id
project_id
library_id
scope
status
source_page
heading_path
confidentiality
validity status
```

Retrieval without scope filters is not Pantheon-compatible.

Scope filtering must occur before ranking.

```text
first scope
then search
then rank
then compose evidence
```

Target retrieval path:

```text
L0 — active project and actor scope
L1 — task contract and requested output status
L2 — exact search / FTS / BM25 inside scope
L3 — semantic search inside scope
L4 — source authority and validity filter
L5 — dependency and contradiction graph
L6 — chronology / active-at-date resolver
L7 — Evidence Pack composer
```

## Evidence Pack visibility

Memory injection must not be opaque.

When memory influences an answer, the system should expose a visible Evidence Pack, at least in review mode.

Candidate Evidence Pack summary:

```yaml
evidence_pack:
  project_id: ...
  task_contract_id: ...
  active_decisions: 0
  candidate_facts: 0
  contradictions: 0
  downgraded_assumptions: 0
  source_documents: 0
  excluded_memories:
    - reason: wrong project
    - reason: superseded
    - reason: unvalidated
    - reason: confidential beyond task scope
```

The reviewer should be able to inspect:

```text
what entered the context
what was excluded
why it was excluded
which facts are active
which facts are candidates
which facts are disputed
```

## Chat drop workflow

Dropping a document into a chat should create an ingestion candidate, not an active memory item.

Expected response pattern:

```text
I detected the probable document type.
I detected the probable scope.
I found possible matching projects or libraries.
I found similar existing documents if any.
Here are the proposed actions.
Nothing has been activated yet.
```

Example for a general guide:

```text
Document type: site best-practice guide.
Probable scope: general agency knowledge.
Similar document: Guide chantier agency v2, similarity 0.74.
Proposed actions:
- convert to Markdown;
- compare with existing guide;
- keep as candidate;
- index only after validation.
```

Example for a project quote:

```text
Document type: contractor quote.
Probable scope: project.
Probable project: VERGER, confidence 0.91.
Probable company: HK, confidence 0.86.
Proposed actions:
- classify as project document;
- propose file rename;
- create candidate quote record;
- extract quote metadata;
- compare with CCTP if available.
```

## Project facts

Project facts are structured facts about a project.

Candidate table:

```text
project_facts
- project_id
- fact_key
- label
- value_text
- value_number
- value_date
- value_json
- unit
- source_type
- source_id
- confidence
- status
- valid_from
- valid_until
```

Examples:

```text
terrain_address
commune_code_insee
cadastral_parcels
project_owner_name
surface_existing
surface_created
urbanism_zone
risk_clay
heritage_nearby
planning_form_candidate
```

A project fact should answer:

```text
Where did it come from?
Which project does it belong to?
When was it last checked?
Who validated it?
Can it be reused?
```

Project facts are useful for simple structured values. Evidence atoms are better for claims, decisions, contradictions, dependencies and temporal validity.

```text
project_fact = value to reuse
evidence_atom = assertion to govern
```

## External observations

Public API results are observations before they are project facts.

Candidate tables:

```text
external_sources
external_connectors
external_source_queries
external_observations
source_packs
country_profiles
country_source_catalog
knowledge_refresh_rules
```

External observations should include source, query time, payload reference, freshness and status.

They may become project facts only through mapping and validation.

## Form preparation

Administrative forms should be handled as structured templates.

Candidate tables:

```text
form_templates
form_fields
form_field_mappings
form_instances
form_instance_values
```

A form instance should show:

```text
filled fields
candidate fields
missing fields
conflicting fields
source facts
last source refresh
human review status
```

A generated form is a draft until validated.

## Contact and organization memory

The system may sync with Google Contacts or another contact system, but Postgres keeps the professional relationship model.

Candidate tables:

```text
core_organizations
core_contacts
core_party_roles
external_contact_links
external_organization_links
contact_update_proposals
```

Google Contacts is a contact source and synchronization target. It is not sufficient to represent project roles, lots, responsibilities, quote senders, invoice senders or site meeting responsibilities.

Contact creation and updates should be proposed before execution.

## Naming and classification support

File and folder names should help classification but must not be the only source of truth.

Recommended file pattern:

```text
{DATE}_{PROJECT_CODE}_{TYPE}_{LOT}_{ORGANIZATION}_{REFERENCE}_{VERSION}.{EXT}
```

Examples:

```text
2026-05-31_VERGER_QUOTE_02-MASONRY_HK_DEV-2026-014_V01.pdf
2026-05-31_VERGER_INVOICE_03-PLUMBING_BPC_FAC-2026-044_V01.pdf
2026-06-04_VERGER_SITE-REPORT_CR08_AGENCY_V01.pdf
2026-06-04_VERGER_CHANGE-ORDER_02-MASONRY_HK_AVT-01_V01.pdf
```

The system should propose renames, not silently apply them.

## Security and confidentiality

Rules:

```text
Project data stays project-scoped.
General knowledge must not contain confidential project data unless explicitly allowed.
OCR output is not automatically reliable.
Vectorized data inherits the highest confidentiality of its source.
Rejected or deprecated knowledge should remain traceable but not used by default.
Memory injection must be visible when it affects a professional answer.
Project memory must not become agency or general memory without review.
```

## Operating principle

```text
The system must know where a document belongs before it uses the document.
The system must know what a memory depends on before it treats that memory as active.
```

This applies to uploaded guides, project documents, quotes, invoices, site notes, CCTP models, MAF notes, DTU extracts, public API results and administrative forms.
