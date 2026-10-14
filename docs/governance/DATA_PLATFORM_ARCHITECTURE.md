# Data Platform Architecture

Status: candidate governance support doctrine  
Boundary profile: candidate_support_note.
Scope: Postgres, Directus, storage, connectors, professional data registers  
Runtime status: non-executable

## Purpose

This document defines the candidate data-platform posture for Pantheon Next when it is used as a professional dossier governance layer above ordinary work tools.

It does not define an ERP implementation. It does not define an agent runtime. It does not prescribe a final database schema.

Status note: this document is a candidate, to verify before promotion — a non-executable blueprint. It may name products (Postgres, Directus and others) only because it describes a candidate adapter / platform binding; that does not make those products part of Pantheon doctrine beyond the binding role. See `ADAPTERS_AND_BINDINGS.md`.

It defines a controlled architecture for organizing professional data so that future modules, workflows and domain packs can be proposed, tested, reviewed, activated, disabled and audited.

## Core rule

```text
Postgres records.
Directus exposes controlled records.
Storage keeps files.
Connectors observe and retrieve.
Hermes may execute bounded jobs.
Pantheon governs the status, scope, proof and approval model.
```

A database row is not a decision. A workflow output is not an approval. A generated document is not a transmitted document. A stored memory is not globally reusable by default.

## Why this layer exists

Professional AI work needs more than prompts and retrieval. It needs stable registers for:

- matters, projects or dossiers;
- users, organizations, contacts and roles;
- documents, files, versions and storage locations;
- messages, attachments and source events;
- extracted facts, observations and evidence candidates;
- approvals, decisions and transmission gates;
- workflows, workflow modes, proposed actions and actual executions;
- knowledge libraries, domain packs and project memory;
- audit trails and reversibility metadata.

The data platform is therefore a controlled professional memory and trace layer, not an autonomous operator.

## Layer model

```text
User tools
  - email
  - chat
  - Drive / SFTP / NAS / local folders
  - calendars
  - contacts
  - office documents

Ingestion and connector layer
  - import files
  - read emails and attachments
  - sync contacts
  - query public APIs
  - detect source type and scope

Data platform
  - Postgres tables
  - controlled statuses
  - object links
  - evidence and validation records
  - workflow definitions and runs

Cockpit layer
  - Directus or equivalent admin UI
  - views, dashboards, manual correction
  - permissioned review and approval

Execution support
  - Hermes jobs
  - OCR / Markdown conversion
  - extraction
  - comparison
  - draft generation
  - indexing

Governance layer
  - Pantheon doctrine
  - task boundaries
  - approval policies
  - memory scope
  - audit and rollback expectations
```

## Stable core versus domain packs

The platform must not be designed around one profession only.

The stable core contains reusable objects:

```text
core_projects
core_scopes
core_modules
core_capabilities
core_users
core_organizations
core_contacts
core_party_roles
doc_documents
storage_objects
message_threads
message_items
workflow_definitions
workflow_versions
workflow_runs
workflow_action_proposals
approval_records
audit_events
knowledge_libraries
knowledge_documents
project_facts
external_sources
external_source_queries
```

Domain packs add profession-specific objects.

For an architecture agency, a domain pack may add:

```text
architecture_lots
architecture_cctp_versions
architecture_cctp_articles
architecture_quotes
architecture_quote_lines
architecture_quote_cctp_matches
site_meetings
site_points
site_point_updates
site_progress_by_lot
site_reserves
finance_contracts
finance_change_orders
finance_invoices
finance_payments
form_templates
form_instances
```

For another profession, the domain pack changes while the core governance model remains.

## Directus posture

Directus is a cockpit over the data model. It may be used to:

- inspect records;
- correct classification;
- review proposed actions;
- approve or reject data promotions;
- manage metadata;
- expose dashboards;
- manage low-risk administrative transitions.

Directus must not become:

- the canonical governance doctrine;
- a hidden approval engine;
- a professional decision-maker;
- an uncontrolled workflow runtime;
- the only source of truth for documents and proof.

Directus collections should expose readable data objects. The canonical governance definitions remain in the repository until a later implementation explicitly changes that boundary.

## Storage posture

Files should not be treated as database blobs by default.

The platform stores file metadata, hashes, source links, access policy and storage location. The physical file may live in:

```text
local folder
NAS
Google Drive
SFTP
S3-compatible object storage
OpenWebUI upload area
domain-specific secure repository
```

Candidate tables:

```text
storage_providers
storage_mounts
storage_objects
storage_access_policies
file_rename_proposals
```

The same logical object can therefore be deployed locally, on a NAS, on a hosted server, or in a hybrid setting.

## Status discipline

Every important object needs a status. Suggested baseline status families:

```text
candidate
needs_review
verified
active
rejected
superseded
deprecated
archived
```

For outputs and actions:

```text
proposed
approved
rejected
executed
failed
revoked
```

For documents:

```text
received
classified
processed
indexed
validated
published
transmitted
archived
```

No object should silently move from candidate to active memory.

## Data scope discipline

Every reusable fact should be scoped.

Candidate scope levels:

```text
global
domain
country
agency
project
matter
session
task
```

A project fact is not global knowledge. A guide or model may be general knowledge. A project document may become general knowledge only after explicit review, anonymization if needed, and validation.

## Candidate core table families

### Modules and capabilities

```text
core_modules
core_capabilities
module_dependencies
module_installations
```

These describe what the system can do without forcing every user to activate every feature.

### Projects and scopes

```text
core_projects
core_scopes
project_settings
project_storage_policies
```

Projects hold contextual boundaries. Scopes govern reuse and confidentiality.

### Parties and contacts

```text
core_organizations
core_contacts
core_party_roles
external_contact_links
contact_update_proposals
```

The local database keeps the professional role model even when contacts are synchronized with Google Contacts or another provider.

### Documents and messages

```text
doc_documents
doc_document_versions
doc_document_relations
message_threads
message_items
message_attachments
```

Emails and attachments are sources. Documents are classified, versioned and linked to projects, workflows, contacts and evidence.

### Knowledge and facts

```text
knowledge_libraries
knowledge_documents
knowledge_document_versions
knowledge_chunks
project_facts
external_observations
```

The system separates general knowledge from project-specific facts.

### Workflows

```text
workflow_definitions
workflow_versions
workflow_runs
workflow_steps
workflow_test_cases
workflow_action_proposals
workflow_action_executions
```

Workflows are versioned, testable, observable and reversible where possible.

### Approvals and audit

```text
approval_policies
approval_records
audit_events
rollback_records
schema_change_proposals
```

The platform records what was proposed, what was accepted, what was executed and what can be reversed.

## Candidate deployment profiles outside Pantheon

These are candidate external implementation environments only. They do not authorize changes under `operations/`, `platform/`, Docker, `.env` or any deployment, and they are not an implementation plan inside Pantheon.

### Local / NAS profile

```text
Postgres + Directus + workers in Docker
Files on NAS
Backups local and external
Limited remote access
```

This profile prioritizes control and confidentiality.

### Hosted profile

```text
Hosted Postgres or VPS
Hosted Directus
External object storage or Drive/SFTP
Workers deployed as services
```

This profile prioritizes access and collaboration.

### Hybrid profile

```text
Hosted database and cockpit
Sensitive files on user-controlled storage
Connectors per project or per module
```

This profile is likely the most adaptable for professional usage.

## Non-goals for the first implementation

The first implementation should not attempt to build:

- a full ERP;
- a universal schema for every profession;
- an autonomous decision engine;
- automatic external sending;
- automatic memory promotion;
- automatic schema mutation;
- a single vector index containing all project and general knowledge without scope separation.

## First viable platform slice

A useful first slice should include:

```text
core_projects
core_scopes
core_organizations
core_contacts
doc_documents
storage_objects
workflow_definitions
workflow_runs
workflow_action_proposals
approval_records
knowledge_libraries
knowledge_documents
project_facts
audit_events
```

Domain-specific tables can then be added as candidate packs, not as hardcoded doctrine.

These table families are conceptual registry families, not approved database tables. Any schema candidate requires a separate approved change under `schemas/`.

## Operating principle

```text
Build the system that lets workflows and domain structures be proposed, tested, reviewed and stabilized.
Do not hardcode the profession before the platform can govern change.
```

The database is not the authority by itself. It is the maintained register through which authority, evidence, scope and approvals remain visible.

---

## Absorbed: Data Platform Index (2026-07-07)

Formerly `docs/governance/DATA_PLATFORM_ARCHITECTURE.md`; absorbed verbatim during the governance cleanup (pass B). Headings demoted one level; content unchanged.

Original status: candidate navigation support doctrine  
Scope: Postgres / Directus / storage / workflow / knowledge / architecture-agency domain pack  
Runtime status: non-executable

### Purpose

This index links the first data-platform documents introduced for Pantheon Next.

The documents below define a candidate doctrine for a modular professional data platform. They do not implement a database, Directus project, workflow runtime, OCR pipeline, vector index, email connector, Google Contacts sync or storage connector.

### Read order

Read in this order:

1. `DATA_PLATFORM_ARCHITECTURE.md`
2. `DATA_PLATFORM_RECONCILIATION.md`
3. `RAW_DERIVED_GOVERNED_RECORDS.md`
4. `DATA_PLATFORM_ARCHITECTURE.md`
5. `WORKFLOW_LIFECYCLE.md`
6. `KNOWLEDGE_INGESTION_AND_MEMORY.md`
7. `AGENCY_DOMAIN_PACK.md`

### What each document does

#### `DATA_PLATFORM_ARCHITECTURE.md`

Records the candidate status of the data-platform layer.

It makes explicit that the layer is not implemented and does not create a Postgres schema, Directus project, workflow runtime, OCR pipeline, vector database, connector setup, architecture-agency ERP, automatic approval system or automatic memory promotion.

#### `DATA_PLATFORM_RECONCILIATION.md`

Reconciles the data-platform candidate layer with existing Pantheon placement doctrine.

Core boundary:

```text
Govern the data platform from Pantheon.
Do not build the data platform inside Pantheon.
```

It defines which parts belong in Pantheon doctrine and which belong in implementation layers such as storage, Directus, external connectors, Postgres schema proposals or execution runtimes.

#### `RAW_DERIVED_GOVERNED_RECORDS.md`

Defines where information actually lives when it should not all be forced into Postgres.

Core boundary:

```text
The database does not hold the whole knowledge.
It holds the governed handles: identity, scope, status, provenance, links, extracted facts, approvals and decisions.
```

It separates raw content, derived content, governed records, retrieval objects, provenance objects, evidence objects and approval records.

#### `DATA_PLATFORM_ARCHITECTURE.md`

Defines the overall data-platform posture:

```text
Postgres records.
Directus exposes and controls.
Storage keeps files.
Connectors observe and retrieve.
Hermes may execute bounded jobs.
Pantheon governs the status, scope, proof and approval model.
```

It distinguishes stable core objects from domain packs and sets the boundary between registry, cockpit, storage, connectors and execution support.

#### `WORKFLOW_LIFECYCLE.md`

Defines progressive workflow authority:

```text
off -> draft -> test -> shadow -> assisted -> active_guarded -> active_durable
```

It establishes the rule that a workflow starts as a proposal and earns durability through tests, observation, review and explicit authorization.

#### `KNOWLEDGE_INGESTION_AND_MEMORY.md`

Defines document ingestion and memory separation:

```text
general memory
agency memory
country memory
project memory
derived memory
validated memory
```

It covers uploaded documents, OCR, Markdown conversion, similarity comparison, vectorization discipline, project facts, public API observations, form preparation and contact memory.

#### `AGENCY_DOMAIN_PACK.md`

Defines a candidate architecture-agency pack:

```text
projects
parties
mail intake
quotes
CCTP
site meetings
site reports
finance follow-up
administrative forms
knowledge libraries
contacts sync
```

It translates architecture practice into modular, testable, non-autonomous data registers.

### Boundary statement

These documents are intentionally not an implementation. They prepare a future implementation by defining:

- what should be represented;
- which objects need statuses;
- which actions require approval;
- where workflow authority may increase;
- how general memory and project memory stay separate;
- how a professional domain pack may be added without freezing the system around one user or one office.

### Operating principle

```text
Build the platform that governs change before building the workflows that perform work.
```

This keeps Pantheon Next aligned with its governance-first posture.

---

## Absorbed: Data Platform Status (2026-07-07)

Formerly `docs/governance/DATA_PLATFORM_ARCHITECTURE.md`; absorbed verbatim during the governance cleanup (pass B). Headings demoted one level; content unchanged.

Original status: candidate support status note  
Scope: data platform candidate documents introduced for Pantheon Next  
Runtime status: non-executable

### Purpose

This document records the current status of the data-platform candidate layer.

It exists so the new Postgres / Directus / workflow / knowledge / architecture-agency documents can be tracked without prematurely promoting them to canonical active doctrine in `STATUS.md`.

Read with:

- `DATA_PLATFORM_RECONCILIATION.md` for boundary placement;
- `DATA_PLATFORM_ARCHITECTURE.md` for reading order;
- `MODULAR_DOMAIN_REORIENTATION.md` for domain-pack placement;
- `CAPABILITY_PLACEMENT.md` for capability placement.

### Current posture

The data-platform layer is a candidate governance support layer.

It is not implemented.

It does not create:

- a Postgres schema;
- a Directus project;
- a workflow runtime;
- an OCR pipeline;
- a vector database;
- a Google Drive connector;
- an SFTP connector;
- a Google Contacts sync;
- a Gmail intake workflow;
- an architecture-agency ERP;
- an automatic approval system;
- automatic memory promotion.

### Candidate documents

The current candidate set is:

- `DATA_PLATFORM_ARCHITECTURE.md` (this document, carrying the absorbed index and status notes);
- `WORKFLOW_LIFECYCLE.md`;
- `KNOWLEDGE_INGESTION_AND_MEMORY.md`;
- `AGENCY_DOMAIN_PACK.md`.

### Candidate value

These documents clarify how Pantheon Next may later govern:

- modular professional data registers;
- stable core objects versus domain packs;
- user-suggested workflows;
- test, shadow and assisted workflow modes;
- general knowledge versus project memory;
- file ingestion, OCR, Markdown conversion and vectorization boundaries;
- contact and organization synchronization boundaries;
- architecture-agency objects such as projects, CCTP, quotes, site reports, finance follow-up and administrative forms.

### Reconciled boundary

```text
Pantheon does not become the data platform.
Pantheon governs the legitimacy, status, scope, memory and approval rules of data-platform behavior.
```

```text
The database records.
The workflow proposes.
The evidence supports.
The approval validates.
The human decides.
```

### Boundary rule

```text
Candidate platform doctrine does not authorize runtime implementation.
```

Any future implementation must still pass through:

- schema proposal;
- module activation review;
- workflow lifecycle review;
- approval policy definition;
- evidence and memory boundary review;
- connector legitimacy review;
- security and confidentiality review.

### Next review questions

Before promotion into active doctrine, the repository should clarify:

1. Which core table families are truly stable enough to become schema candidates?
2. Which architecture-agency objects belong in the first domain pack slice?
3. Which workflows should be modeled first: quote intake, site report preparation, finance follow-up or knowledge ingestion?
4. Which storage profile should be treated as the first reference profile: local/NAS, hosted, or hybrid?
5. How should Directus be described: cockpit candidate, admin UI candidate, or schema-exposure candidate?
6. What connector gateway posture should be used for Gmail, Google Drive, Google Contacts and public APIs?
7. What level of schema detail belongs in governance docs versus future implementation docs?

### Promotion condition

The candidate set may be promoted only when it preserves the existing Pantheon boundary:

And when it keeps the reconciled data-platform boundary intact:

```text
Govern the data platform from Pantheon.
Do not build the data platform inside Pantheon.
```
