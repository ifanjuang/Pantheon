# Evidence Memory Development Plan

Status: candidate support note — documented non-implemented.
Boundary profile: candidate_support_note.

Related note: [`EVIDENCE_MEMORY_CANONICALIZATION.md`](EVIDENCE_MEMORY_CANONICALIZATION.md)

Tracking issue: #68.

This plan translates the Evidence → Memory doctrine into a development sequence.

It does not implement a schema, tests, runtime, API, migration, queue, scheduler, approval engine, memory engine, vector store, mem0 integration or Hermes memory integration.

## Development principle

Do not start with mem0, pgvector or a graph UI.

Start with the governed registry.

```text
Registry first.
Projection second.
Automation last.
```

The canonical record must remain independent from any memory backend.

```text
PostgreSQL records the governed registry.
pgvector retrieves by similarity.
mem0 may project usable memory.
Hermes may consume or propose candidates.
Pantheon governs status, scope, evidence and approval.
The human validates consequential promotion.
```

## Recommended build order

```text
1. Governed registry model
2. Status and audit events
3. Evidence → extraction → Register Candidate pipeline
4. Scope, contradiction and dependency checks
5. Impact Review queue
6. Registre Probatoire promotion gate
7. Backend projection layer
8. Dashboard / cockpit views
9. Memory graph visualization
10. Schema hardening and tests
```

This order protects the core governance model before adding backend power.

## Development layers

### Layer 1 — Registry

Purpose: record governed objects and status transitions.

Candidate records:

```text
sources
evidence_items
extraction_candidates
memory_subjects
memory_items
memory_versions
memory_links
impact_reviews
backend_projections
audit_events
```

Layer 1 should not depend on mem0 or Hermes memory.

### Layer 2 — Review pipeline

Purpose: create candidates and route them to the right level of friction.

Pipeline:

```text
ingest source
→ extract metadata
→ create Evidence Candidate
→ propose Extraction Candidate
→ classify speech act
→ compute explainable confidence
→ detect scope and subject
→ create Register Candidate
→ check conflicts
→ check dependencies
→ create Impact Review if needed
→ human review / gate
→ Registre Probatoire entry if approved
```

### Layer 3 — Projection

Purpose: make approved memory usable by execution surfaces without making those surfaces canonical.

Projection targets may include:

```text
pgvector
mem0
Hermes memory
OpenWebUI display excerpts
Memory Graph / provenance graph
```

Projection is explicit, reversible and auditable.

### Layer 4 — Cockpit

Purpose: make status, friction, conflicts and impacts visible.

The cockpit should display:

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

The cockpit must not become a hidden approval engine.

## Candidate record responsibilities

### sources

Records raw input material.

Examples:

```text
email
PDF
scanned PDF
image
plan
meeting note
site report
spreadsheet
quote
client instruction
contractor message
administrative decision
internal note
```

Responsibilities:

```text
source identity
scope identifiers
origin channel
file or connector reference
source date
received date
author / sender
sensitivity
```

### evidence_items

Records selected proof candidates linked to a source.

Responsibilities:

```text
source excerpt
page / location
claim supported
review status
source metadata snapshot
Evidence Pack relation when applicable
```

### extraction_candidates

Records proposed interpretation of evidence.

Responsibilities:

```text
proposed fact / decision / preference / hypothesis / contradiction / impact
speech-act classification
confidence breakdown
source evidence links
reason for candidate status
```

### memory_subjects

Records stable subject threads.

Example hierarchy:

```text
Project Belvedere
→ Pool
  → Program
  → Pool heat pump
  → Pool-compatible terrace
  → Foundation-depth hypothesis
  → Budget
```

Responsibilities:

```text
scope
subject label
parent subject
active status
risk classification
latest active memory pointer if any
```

### memory_items

Records atomic memory objects.

Rule:

```text
If two parts can be updated independently, they should be separate memory items.
```

Responsibilities:

```text
claim
scope
subject
current status
usable status
risk level
confidence summary
review state
```

### memory_versions

Records the history of one memory item.

Responsibilities:

```text
version number
reverse chronological display
source date
received date
effective date
supersession
revocation / archive reason
review / approval details
```

### memory_links

Records relations between memories, evidence and subjects.

Relation types:

```text
depends_on
impacts
valid_if
invalid_if
supersedes
superseded_by
derived_from
conflicts_with
supports
requires_arbitration
```

### impact_reviews

Records the impact queue created by changed assumptions or decisions.

Responsibilities:

```text
trigger memory candidate
impacted memory
impact type
impact severity
recommended action
review decision
resolution status
```

### backend_projections

Records sync state to external memory or retrieval systems.

Responsibilities:

```text
backend_type
backend_reference
projection_scope
sync_status
last_sync_at
out_of_sync_reason
```

### audit_events

Records append-only status and decision events.

Responsibilities:

```text
who / what triggered the event
old status
new status
reason
timestamp
task_id
approval reference when applicable
```

## Friction paths

The system should assign a required path to each candidate.

```text
fast_path
review_path
governance_path
```

### fast_path

Use for low-risk work:

```text
search
summary
classification
metadata extraction
deduplication
non-canonical notes
```

Fast path must not promote a Registre Probatoire entry.

### review_path

Use for:

```text
Register Candidate
uncertain source
light contradiction
non-critical project preference
candidate update
```

Requires visible user review.

### governance_path

Use for consequential memory or action:

```text
Registre Probatoire promotion
project-impacting decision
structure
budget
planning / urbanism
insurance
professional liability
external communication
doctrine / agency rule
cross-project exception
```

Requires explicit gate and audit.

## Status fields

Candidate implementation should separate status fields instead of compressing everything into one field.

Suggested categories:

```text
record_status
review_status
usable_status
conflict_status
impact_status
projection_status
```

Examples:

```text
record_status: active | archived | revoked | superseded
review_status: candidate | under_review | approved | rejected
usable_status: usable | usable_with_caution | blocked | arbitration_required
conflict_status: no_conflict | possible_conflict | confirmed_conflict
impact_status: none | impact_detected | critical_arbitration | resolved
projection_status: not_projected | synced | out_of_sync | projection_blocked
```

## Promotion checks

A Register Candidate cannot be promoted unless the gate can verify:

```text
scope resolved
subject resolved
atomicity checked
evidence linked
source metadata present
speech-act classification present
confidence explanation present
conflict check complete
dependency check complete
impact review complete or explicitly deferred
required approval present
audit event ready
```

Promotion failure should explain which condition blocked promotion.

## Use checks before answering

Before a memory is used in an answer, the execution path should check:

```text
scope match
subject match
record status
usable status
conflict status
freshness / supersession
linked evidence
project memory vs agency memory consistency
backend projection freshness if retrieved from a backend
```

Answer postures:

```text
use normally — canonical, scoped, no conflict
use with caution — candidate or weakly supported
do not use — revoked, superseded or contradicted
arbitration required — conflict or critical impact
```

## Shadow reconstruction integrity cycle

The review pipeline should support an independent reconstruction pass before a
memory or register projection is trusted over time.

The purpose is not to rewrite the current register. It is to rebuild a
candidate view from admitted sources, compare it with the current projection
and expose consequential drift.

### Candidate execution placement

```yaml
integrity_cycle:
  exposed_by: OpenWebUI or another governed review surface
  executed_by: Hermes or another external execution runtime
  governed_by: Pantheon register, evidence, scope and approval rules
  approved_by: human reviewer when a discrepancy changes governed status
  forbidden:
    - destructive register rebuild
    - automatic semantic merge
    - automatic promotion
    - automatic supersession or revocation
    - cross-project reconstruction
    - scheduler inside Pantheon
```

### Review stages

```text
1. Select one explicit scope and source cutoff.
2. Inventory admitted source identities and versions.
3. Decompose changed material into atomic claim candidates.
4. Build a separate shadow projection.
5. Compare it with the current register projection.
6. Classify discrepancies without resolving them.
7. Link each discrepancy to sources, current entries and possible impacts.
8. Return candidate review material and source-completion requests.
9. Apply no governed status change before the required human gate.
```

The source cutoff makes a review reproducible. A later source arriving during
the run belongs to a later review rather than silently changing the result.

### Discrepancy classes

| Class | Meaning | Default path |
|---|---|---|
| `direct_contradiction` | Two in-scope claims cannot both hold for the same use and effective time. | Review or governance path according to consequence. |
| `temporal_supersession_candidate` | A later claim may replace an earlier one, but the replacement is not yet approved. | Review impact, then explicit supersession if approved. |
| `scope_mismatch` | A claim or recall belongs to another project, user, phase or subject. | Block reuse and request scope correction. |
| `definition_or_unit_mismatch` | Values differ because definitions, tax basis, units or measurement conventions differ. | Clarify; do not merge automatically. |
| `source_authority_mismatch` | The current projection relies on a source whose allowed use is weaker than a competing source. | Expose both and apply source policy through review. |
| `unsupported_current_claim` | A current projection entry has no retrievable admitted support at the review cutoff. | Suspend reliance or request source completion; do not erase. |
| `unrepresented_source_claim` | An admitted source contains a consequential claim absent from the current projection. | Create a Register Candidate and inspect impacts. |

### Cadence profiles

Cadence is an external runtime configuration, not Pantheon behavior.

```text
nightly_incremental
  changed sources and projections only
  intended for low-cost drift detection

milestone_full
  complete in-scope reconstruction at APD, PRO, DCE, ACT, execution or reception review
  intended for consequential dossier checks

on_demand
  bounded review requested by a human or Task Contract
  intended for urgent or disputed claims
```

An incremental pass must use source and page hashes where available so an
unchanged dossier is not repeatedly extracted and embedded. A full pass should
remain reproducible from its source manifest, cutoff and adapter versions.

### Existing external execution profile

The repository now carries one external Hermes night-operations template:

```text
templates/hermes/dashboard-plugins/pantheon-modules/night-operations.template.yaml
```

This existing template is the timing referent. This development plan must not
create a parallel Pantheon schedule.

Its posture is disabled by default:

```text
catalog entry only
no Cron job created by repository presence
no direct recurring-job creation from the Pantheon Modules dashboard
runtime timezone, profile, workdir, scope and finite run limit required
operator review required before any native Hermes activation
```

Once one matching native job exists and its finite repeat is observed, the
Pantheon Modules card may expose separately confirmed controls to pause/resume,
retime it while paused and request one immediate run while enabled. The card
must never create or delete the job, edit its execution scope or silently chain
a timing change into activation or launch.

Reference timings are evaluated in the Hermes host's local timezone. A French
deployment may select `Europe/Paris` only after the host clock and timezone are
observed and confirmed.

| Host-local time | Existing Hermes operation | Initial bound |
|---|---|---|
| `00:30` daily | Backup and restore preflight. | 7 trial runs; 30 minutes maximum |
| `01:00` daily | PDF ingestion and scoped vectorization of changed material. | 7 trial runs; 90 minutes maximum |
| `02:45` daily | Retrieval and index quality review. | 7 trial runs; 45 minutes maximum |
| `03:45` Sunday | Runtime-memory consolidation review. | 4 trial runs; 60 minutes maximum |
| `05:00` daily | Contradiction, incremental shadow-reconstruction and governance-drift review. | 7 trial runs; 60 minutes maximum |
| `06:15` daily | Local morning decision digest. | 7 trial runs; 20 minutes maximum |

The daily `nightly_incremental` integrity pass should bind to the existing
`contradiction_drift_review` operation. It processes one explicit scope and
changed/admitted sources only, builds a separate candidate projection and
returns discrepancy and impact candidates.

A `milestone_full` reconstruction is not a recurring night job. It remains an
explicit Task Contract requested at APD, PRO, DCE, ACT, execution or reception
review. `on_demand` remains one bounded scope and one stated reason.

Each operation owns a maximum runtime and requires its declared prerequisite
receipts. A failed or missing upstream result stays visible and must not
silently advance a later operation. Unfinished work remains external-runtime
state; Pantheon owns no queue, retry worker or timer.

### Mandatory run protections

The following protections are not optional toggles:

```text
one explicit project / user / phase scope
fixed source cutoff and source manifest
source and page identity where available
pre-run snapshot before mutable projection maintenance
append-only run and discrepancy trace
bounded compute, duration and retry budget
fail-closed behavior for missing scope, snapshot or required dependency
no semantic register mutation without the required human gate
```

Optional processing actions may be suspended independently. Mandatory
protections remain active whenever any scheduled or on-demand run is admitted.

### Candidate result shape

```yaml
integrity_review_candidate:
  review_id:
  scope:
  source_cutoff:
  source_manifest_ref:
  current_projection_ref:
  shadow_projection_ref:
  adapter_versions: []
  discrepancies:
    - discrepancy_id:
      class:
      subject_ref:
      current_claim_refs: []
      reconstructed_claim_refs: []
      evidence_refs: []
      possible_impacts: []
      consequence_level:
      proposed_path: fast_path | review_path | governance_path
      decision_status: pending_human | no_governed_change_required
  missing_sources: []
  unchanged_claim_count:
  authority_note: candidate comparison only; no register mutation
```

The counts and model output do not prove correctness. Useful evaluation should
measure missed consequential discrepancies, false alerts, source-locator
quality and reviewer acceptance by source type.

### Review-budget rule

The cockpit should not surface every wording difference. It should prioritize
discrepancies that may change cost, scope, quantity, responsibility,
compliance, date, document index, material choice, included service or external
commitment. Lower-consequence differences remain inspectable in the review
report without becoming interruptive decision cards.

## Backend projection rules

### pgvector

pgvector may index sources, evidence, candidates and canonical memories for retrieval.

It must not define truth.

### mem0

mem0 may receive usable memory for agent-facing recall.

It must not become the canonical registry.

### Hermes memory

Hermes memory may help execution.

It must not authorize, approve or canonize memory.

### OpenWebUI

OpenWebUI may expose memory status and review controls.

It must not be treated as a Registre Probatoire entry unless the canonical registry says so.

## Suggested API shape

Candidate endpoints, not implementation commitments:

```text
POST /sources
POST /evidence-items
POST /extraction-candidates
POST /memory-candidates
POST /memory-candidates/{id}/review
POST /memory-candidates/{id}/promote
POST /memory/{id}/supersede
POST /memory/{id}/revoke
GET  /projects/{id}/subjects
GET  /subjects/{id}/timeline
GET  /memory/{id}/evidence-chain
GET  /impact-reviews
POST /impact-reviews/{id}/resolve
GET  /backend-projections/out-of-sync
POST /backend-projections/{id}/sync
```

Any `promote`, `supersede` or `revoke` operation must create an audit event.

## Dashboard impact

The dashboard should distinguish:

```text
Services installed
Base & Memory
Evidence → Memory
Files
Connections
IA & Agents
Surveillance
```

### Services installed

Repos, containers, tools and services.

Examples:

```text
mem0
Docling / PDF parser
OCR engine
Office converter
SearXNG
ComfyUI
Browser worker
Piper
faster-whisper
```

### Base & Memory

Registry and data layer.

Examples:

```text
PostgreSQL
pgvector
Evidence registry
Extraction registry
Memory candidate registry
Registre Probatoire registry
Memory graph
Backend sync
```

### Evidence → Memory

Review and governance workflow.

Examples:

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

## Test scenarios to write later

Do not add tests until explicitly approved.

Candidate test scenarios:

```text
A question does not create a Registre Probatoire entry.
A hypothesis creates a weak candidate.
A direct client decision creates a strong candidate but not automatic canon.
A newer client decision supersedes an older project memory only after review.
A pool removal triggers impacts on pool heat pump, terrace, foundations and budget.
A structural dependency requires governance path.
A project memory cannot contradict an agency rule without exception.
A revoked memory is not used in answers.
A superseded memory remains visible in history.
A pgvector match is blocked if canonical status is revoked.
A mem0 projection out of sync is not treated as canon.
A Hermes memory note cannot promote memory.
```

## Implementation guardrails

Do not introduce:

- hidden memory promotion;
- direct broad Postgres access from Hermes;
- mem0 as source of truth;
- pgvector as source of truth;
- automatic critical impact downgrading;
- deletion of old memory versions;
- cross-project memory use without scope checks;
- one large unversioned memory blob per project;
- UI confirmation that bypasses approval level.

## Open sequencing questions

Before schema work:

- Which fields are mandatory for MVP?
- Which statuses are canonical doctrine versus UI labels?
- Should `memory_items` and `memory_versions` be separate in MVP?
- Should impact review be first-class from day one?
- Which backend projections are allowed in MVP?
- Which architecture subjects should ship first?
- What approval levels are required for agency, project and system memory?

## Current repo state

Documented non-implemented.

No schema added.

No tests added.

No migration added.

No runtime added.

No backend projection added.

No automatic memory promotion added.
