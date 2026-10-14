# File-native Pantheon Control Convergence

Status: candidate convergence roadmap — documentation only.

This document records a target architecture, development guardrails and migration method. It does **not** modify current Pantheon doctrine, transfer authority, migrate persistence, authorize a runtime, remove PostgreSQL, select a runtime-memory provider, adopt a vault topology, or deprecate any existing owner by itself.

Parent exploration: `Pantheon-Next#684`.

## 1. Objective

Converge the Pantheon ecosystem toward a smaller and more maintainable architecture while preserving the useful governance invariants already encoded and tested by `pantheon-mvp`.

The durable mental model is deliberately small:

```text
FILES / SOURCES
= professional and workspace content

PANTHEON
= rules and governed boundaries

HERMES
= reasoning and action runtime

HINDSIGHT
= derived retrieval and associations

COCKPIT
= projection and interaction
```

Supporting infrastructure exists only when a demonstrated responsibility needs it:

```text
Hermes runtime-memory capability/provider
= conversational/runtime continuity selected by runtime binding/qualification

Transactional control storage
= only state that genuinely needs atomicity, replay protection,
  concurrency control or durable authorization history
```

The intended simplification is **not**:

```text
replace PostgreSQL with Obsidian
```

It is:

```text
put each responsibility in the simplest owner and storage mechanism
that actually needs the required properties
```

## 2. Verified repository baseline

Checkpoint: 2026-08-22.

```text
Pantheon-Next/main
= 8c15eff5c767c76410db9e0f3a2e388f85ed1aac

pantheon-mvp/main
= d960862dd0e23b7003a0f3e4ee0ea630ffc12af9
```

Observed active work at this checkpoint:

- `Pantheon-Next` PR Pantheon-Next#685 records Hermes memory-provider qualification;
- `Pantheon-Next` PR Pantheon-Next#686 converges source research into one Hermes skill candidate;
- `pantheon-mvp` has no open PR;
- `pantheon-mvp` #333 and #337 provide the first generic read-only filesystem → Card/Collection workspace seam;
- `Pantheon-Next` #684 remains the parent workspace/navigation exploration;
- Pantheon-Next#659 hardens Hindsight before broader durable agency data use;
- Pantheon-Next#660 qualifies LiveSync/CouchDB conflict, offline and backup behavior;
- Pantheon-Next#664 qualifies one consequential policy/gate/PEP green path;
- Pantheon-Next#607/#644 retain the real-environment Project Anatomy qualification path.

This roadmap must be rechecked against current `main`, open PRs, active issues and relevant branches before every implementation tranche.

## 3. Why convergence is needed

The current executable MVP is deliberately broad. It has been useful for discovering, formalizing and testing responsibilities including:

```text
Projects / Agency Data
Information
Source admission
Document extraction
pgvector retrieval
Knowledge
Claims
Relations
Categories
Work Issues
Decisions
Change candidates
Project Anatomy
Professional Documents
Document currentness
exact byte retention
human access
Hermes handoff/admission/results
Cockpit
```

That work is valuable because it produced schemas, transactions, refusal paths and acceptance tests.

The long-term risk is not missing capability. It is duplicate representation and duplicate authority:

```text
PostgreSQL business state
+ workspace files
+ Hindsight derived memory
+ Cockpit projections
+ runtime memory
```

The convergence goal is therefore:

```text
keep the proven invariants
remove duplicate persistence and duplicate retrieval
avoid parallel owners
keep runtime components replaceable
```

## 4. Non-negotiable governance boundaries

The target must preserve at least:

```text
retrieved != truth
memory != Evidence
runtime success != authorization
projection != persistence
folder/path != governed identity
source observation != project truth
file present != Source/Document admitted
edited text != approved state change
```

Add for the file-native direction:

```text
editable file != authorized transition
Hindsight relation != governed relation
tag != relation
tag/status != professional validation
sync success != Evidence
index current != source current
filesystem access != professional authority
```

Any implementation that collapses one of these distinctions is architectural regression even if its tests otherwise pass.

## 5. Target responsibility model

### 5.1 Files and sources

Candidate target:

```text
workspace files
= canonical professional/work content only for owners explicitly migrated
  to file-native persistence
```

The architecture is **file-native**, not Obsidian-native.

Obsidian may be the preferred editor, but replacing Obsidian must not require migration of professional state.

A path is never the durable business identity:

```text
folder != Project identity
path != EntityRef
rename != new professional object
move != new professional object
```

Stable IDs are required whenever a record must survive moves, renames or cross-file relations.

Illustrative only:

```yaml
id: project:verger
kind: project
```

No exact frontmatter contract is adopted by this roadmap.

### 5.2 Pantheon-Next

Pantheon-Next remains the normative owner for:

```text
doctrine
schemas
policy classification
validation rules
governance boundaries
controlled vocabulary contracts
promotion / approval / Evidence distinctions
tests of normative invariants
```

Pantheon-Next must not become the business database for real agency projects.

The existing policy service/PDP direction should be reused. Do not create another rules compiler or parallel policy engine merely for file-native work.

### 5.3 Pantheon executable control

The reduced executable responsibility, currently implemented largely inside `pantheon-mvp`, applies Pantheon rules around real operations.

Candidate responsibilities:

```text
TaskContract / ContextPack validation
policy enforcement
bounded write gates
human approval gates where required
workspace read/write adapter
exact-source reads and digests
authentication / technical access adapters
ExecutionAdmission
LaunchReservation
replay / idempotency protection
runtime execution receipts
```

This layer may mutate a professional source when authorized. It does not therefore become the owner of the professional content.

### 5.4 Hermes

Hermes remains the reasoning/execution runtime.

Pantheon constrains boundaries, not internal reasoning.

Pantheon may define:

```text
objective
scope
available sources
allowed tools/effects
forbidden effects
required review/approval
expected result contract
```

Hermes remains free to search, plan, reason, use Skills and compose tools inside those boundaries.

### 5.5 Hindsight

Hindsight is the preferred candidate for:

```text
semantic retrieval
associative recall
entity/relationship discovery
temporal context
derived semantic graph
```

It remains reconstructible from source material and never becomes Pantheon authority.

For consequential work, the preferred path is:

```text
question
→ Hindsight candidate recall
→ source refs
→ exact current source read
→ Pantheon validation/qualification
→ Hermes use
```

Therefore:

```text
Hindsight recall != source
Hindsight relation != governed relation
retrieved != truth
```

A successful Hindsight migration may justify retirement of the duplicate Pantheon chunk/embedding/pgvector path only after comparative acceptance tests.

### 5.6 Hermes runtime memory and the `MNEMOSYNE` terminology boundary

The architecture must **not** hard-code a third-party runtime-memory provider as an owner.

Use the generic responsibility:

```text
Hermes runtime-memory capability/provider
= conversational/runtime continuity
```

Provider selection belongs to runtime qualification/binding and may change without changing this architecture.

If the third-party Mnemosyne provider is selected for a Hermes deployment, that is an implementation/binding fact, not a new Pantheon owner.

The Pantheon `MNEMOSYNE` governance role/name, where used by current doctrine, must not be silently reinterpreted as the executable third-party provider.

The durable separation is:

```text
runtime conversational memory
!= Hindsight workspace retrieval
!= Evidence
!= professional source
```

### 5.7 Cockpit

Cockpit remains a projection and interaction surface.

Reuse the merged generic filesystem Card/Collection seam rather than inventing another navigation engine.

A candidate long-term root UX may converge toward a small set such as:

```text
Pantheon
Affaires
Documentation
Outils
```

Names and topology are not adopted by this roadmap and must not become hard-coded business constants prematurely.

## 6. Source classes — file-native does not mean Markdown-everything

Before migration, every source must be classified by responsibility.

### A. Workspace-authored text/state

Examples:

```text
Project metadata
Notes
working documentation
tag vocabulary
some governed records after explicit migration
```

These are the strongest file-native candidates.

### B. Exact binary/source artifacts

Examples:

```text
PDF
image
recording
IFC
RVT/RFA or other native model files
issued office documents
```

Their exact bytes, digest, provenance and revision may matter independently of any Markdown representation.

Rule:

```text
extracted Markdown != original source
preview != source
OCR != source
summary != source
```

Do not replace an exact binary source with a generated Markdown derivative merely because the derivative is easier to retrieve.

### C. External-system records

Examples may include:

```text
email
Google Drive/Docs
Revit live model state
external document-management systems
optional Paperless records
```

Where an external system is the declared source owner, Pantheon should retain stable references/snapshots/digests only as required by the owner contract.

Do not copy every external record into the vault to create artificial local authority.

### D. Derived artifacts

Examples:

```text
Hindsight memories
embeddings
chunks
parser JSON
OCR output
previews
summaries
inferred relations
```

These should be reconstructible or explicitly source-linked.

```text
derived != authoritative
```

## 7. Canonical content versus authorized transition

File-native persistence must not collapse professional content with execution authorization.

A file may declare a state while Pantheon separately determines whether the transition into that state was legitimately admitted.

Example:

```text
file contains status: approved
!= approval was authorized
```

Separate:

```text
FILE
= declared professional/work state

SCHEMA
= structural validity

POLICY / GATE
= whether a transition is permitted

CONTROL RECORD / RECEIPT
= whether a consequential transition was admitted/executed against
  the expected identity/revision/digest
```

This keeps the source human-readable while preserving:

```text
execution success != authorization
edited text != approved state change
```

## 8. Candidate protection posture

Do not make every workspace write equally heavy.

Phase 2 should evaluate whether current doctrine can express a small distinction equivalent to:

```text
NORMAL
ordinary direct edit

MANAGED
must satisfy declared schema/invariants

PROTECTED
consequential transition requires a Pantheon gate/control record
```

Illustrative only:

```text
working note            -> normal
Project metadata        -> managed
tag/nomenclature file   -> managed
professional Decision   -> protected where consequential
Evidence admission      -> protected
external effect         -> protected
```

These names and assignments are not adopted here.

## 9. Identity and lifecycle contract for file-native records

Before any governed record becomes file-native, the implementation must define deterministic behavior for:

```text
create
read
edit
move
rename
archive
retire
delete
restore
```

Minimum invariants:

1. one stable governed ID resolves to at most one active canonical record in its declared scope;
2. duplicate governed IDs are detected and surfaced, never silently selected by path order;
3. move/rename preserves identity;
4. broken relation targets are visible as broken references, not silently dropped;
5. deleting a file does not automatically mean a governed entity was professionally retired;
6. source deletion does not automatically retire a stable Project Anatomy object;
7. archive and delete remain distinct operations;
8. if historical identity must survive physical deletion, use an existing retirement/tombstone mechanism rather than path inference;
9. path caches/indexes are derived and rebuildable;
10. no business ID is generated solely from current path for a governed owner.

## 10. Workspace write contract

The future Workspace write adapter must be one bounded canonical write path for Hermes/Cockpit-mediated edits.

For managed/protected writes, the contract should require the applicable subset of:

```text
stable target identity
resolved current source path
expected source digest and/or revision
requested bounded change
actor/request provenance
policy classification
gate/decision reference when required
idempotency/correlation identifier
```

Required behavior:

```text
resolve exact current source
→ verify expected identity/digest/revision
→ validate requested new representation
→ verify authorization/gate when consequential
→ perform one bounded atomic-or-fail write
→ re-read exact result
→ verify resulting identity/digest
→ emit technical/control receipt when required
```

Required refusal behavior:

```text
stale expected digest/revision -> conflict, no overwrite
foreign identity/path mismatch -> refuse
schema invalid -> refuse managed/protected write
missing required gate -> refuse
replayed protected operation -> refuse/idempotent result according to contract
partial filesystem write -> never report success
```

Do not add an autonomous merge engine to solve write conflicts.

A direct human edit outside the adapter is an observed source change. If it creates a state that requires governed admission, Pantheon should surface it as unadmitted/drifted rather than pretending the edit did not occur or silently manufacturing approval.

Exact filesystem atomicity mechanics remain deployment-specific; the behavioral contract above is the invariant.

## 11. File schema and migration discipline

Managed/protected file records need explicit schema evolution rather than implicit parser guesswork.

Before production use, decide a minimal machine-readable version marker such as:

```text
schema identity
schema revision/version
```

Requirements:

1. readers must define which historical versions they can read;
2. writers must not silently rewrite an unknown schema version;
3. protected records must not auto-upgrade in the background merely because a new application version starts;
4. migrations must be explicit, reviewable and idempotent;
5. migration tooling must support dry-run/diff before write;
6. a backup/rollback point must exist before bulk migration;
7. failed partial migrations must be detectable and resumable or reversible;
8. schema migration != professional approval;
9. changing serialization must not change stable governed identity.

## 12. Tags, folders, Categories and relations

### Folders

Candidate role:

```text
location / navigation / working scope
```

Never professional identity or authorization.

### Tags

Candidate role:

```text
classification / facets / discoverability / presentation context
```

Reuse/extend the existing Tag Registry before creating another taxonomy owner.

### Category

The current Category/CategoryAssignment implementation is mature, but its independent long-term responsibility is open.

Procedure:

```text
inventory Category consumers/invariants
→ map each to hierarchical Tag/folder/facet capability
→ run acceptance tests
→ decide retain / reduce / retire
```

Only demonstrated equivalence may make Category a deprecation candidate.

```text
possible simplification != Category already obsolete
```

### Entity relations

Tags do not replace typed relations.

A governed relation needs at minimum:

```text
source EntityRef
relation type
target EntityRef
```

A file-native carrier is possible, but must preserve stable EntityRefs, vocabulary validation, scope rules and broken-reference visibility.

Hindsight-inferred relations remain derived/candidate-only.

## 13. PostgreSQL target posture

This roadmap does **not** decide to remove PostgreSQL.

It proposes reducing business persistence only where another source owner is demonstrated.

Candidate residual responsibility:

```text
transactional control state
```

Typical examples:

```text
ExecutionAdmission
LaunchReservation
one-shot authorization consumption
idempotency keys
technical grants/auth state
short-lived locks/reservations
runtime execution receipts
```

These are poor candidates for ordinary file editing because their essential properties are atomicity, concurrency protection and replay safety.

Conversely:

```text
existing SQL table != permanent architectural owner
```

Storage technology remains replaceable. Review PostgreSQL only after the residual requirement is known.

## 14. Synchronization, Hindsight consistency and degraded modes

The source and derived systems do not need synchronous global consistency.

The target consistency rule is:

```text
source file/source system = current declared source state
Hindsight = eventually consistent derived index
Cockpit projection = must identify its source/freshness semantics
control records = exact for governed transition checks
```

Before broader production use, reuse the existing qualification work instead of inventing a new sync subsystem:

- Pantheon-Next#660 owns LiveSync/CouchDB create/edit/rename/delete, offline/reconnect, conflict and backup qualification;
- Pantheon-Next#659 owns Hindsight hardening, ingestion authority, auth/network posture, restore and outage/recovery behavior.

Required degraded-mode behavior:

```text
Hindsight unavailable
→ source browse/read remains possible where otherwise authorized
→ semantic retrieval is visibly unavailable/degraded

Hindsight stale
→ consequential work re-reads exact source before use

Hermes unavailable
→ professional files remain readable/editable by normal human tools

control store unavailable
→ ordinary reads may continue
→ protected/consequential writes fail closed

sync conflict on managed/protected record
→ surface conflict
→ do not silently auto-merge governed state
```

Where useful, expose a freshness marker such as source digest versus indexed digest/timestamp. Do not create a new authority just to display lag.

One durable Hindsight ingestion authority per bank/trust domain should be selected and qualified before enabling competing producers.

## 15. Security and access boundaries

File-native does not weaken access control requirements.

Preserve:

```text
filesystem permission != Pantheon authorization
bank isolation != authorization
technical write access != professional approval
authenticated != authorized for this effect
```

Minimum implementation guardrails:

- only explicitly configured workspace roots are exposed;
- reject traversal, unsafe absolute paths and unapproved symlink escape paths;
- preserve project/trust-domain scope on reads and writes;
- no raw database credentials in browser clients;
- no secrets/tokens in normal project frontmatter;
- Hindsight durable use must respect Pantheon-Next#659 security/hardening posture;
- external runtime memory remains separately bounded from professional source authority;
- sensitive source paths or client secrets must not be committed to Pantheon repositories.

## 16. Backup, restore and disaster recovery

The architecture must identify what requires backup versus rebuild.

### Must be durably protected when used as authority

```text
canonical source/workspace files
exact professional source binaries where applicable
transactional control records required for audit/replay semantics
agency-owned registry instances when they are authoritative
required configuration for resolving trust domains/workspaces
```

### Prefer reconstructible

```text
Hindsight semantic index/memory derived from source
Cockpit projections
path indexes/caches
embeddings/chunks/previews where derivable
```

Before any production owner cutover:

1. capture a verified pre-cutover backup/export of the old owner;
2. verify the new source backup path;
3. document restore order;
4. prove at least one bounded restore/rebuild on synthetic/non-client data;
5. define rollback conditions;
6. keep old owner data available read-only until acceptance and rollback window close.

Hindsight restore/rebuild work should reuse Pantheon-Next#659. LiveSync backup/conflict work should reuse Pantheon-Next#660.

## 17. Required doctrine convergence — phase 2

The architecture in this roadmap intentionally goes beyond several current candidate/support rules. Implementation must not silently violate them.

Before file-native owners replace existing owners, perform explicit doctrine convergence.

### 17.1 `AGENCY_DATA_SYSTEM_OF_RECORD.md`

Current direction still declares PostgreSQL Agency Data as the default native system of record.

Decision required:

```text
Can selected Agency/workspace records use file-native sources of record
while Pantheon governs identity and consequential transitions?
```

### 17.2 `OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md`

Required decisions:

```text
When is Markdown itself canonical source?
When is an Obsidian note only a projection?
How are trust domains/vaults/banks declared?
How is one-way Hindsight derivation preserved?
How are source freshness and indexing lag represented without authority transfer?
```

The rule must classify the file's responsibility, not use "Obsidian" as a semantic category.

### 17.3 Category / Tag classification

Do not remove Category before a consumer/invariant equivalence matrix proves it redundant.

### 17.4 Registry ownership

Decide whether agency-specific registry instances, such as the actual agency tag vocabulary, live with agency workspace data while Next retains semantic/schema contracts.

No duplicate `Tags.md` / `tags.json` / MVP-registry authority is permitted.

### 17.5 Control-plane boundary

Preserve:

```text
Pantheon governs
Hermes executes
```

Executable control retained in `pantheon-mvp` is enforcement/adapter state, not a hidden scheduler, queue, provider router or agent runtime.

### 17.6 Runtime-memory terminology and binding

Do not encode the third-party Mnemosyne provider into normative architecture merely because it is observed or preferred in a current Hermes qualification.

Phase 2 should preserve the distinction between:

```text
Pantheon memory/continuity governance role
runtime-memory Capability/provider selection
Hindsight workspace retrieval
```

Provider choice remains replaceable.

## 18. Completeness gate — all 27 current MVP responsibilities

No migration programme should begin until every current responsibility is accounted for. The table below is a **migration hypothesis**, not an authority transfer.

| # | Current responsibility | Default convergence question / hypothesis |
|---|---|---|
| 1 | Project / Agency Data | Test file-native Project/agency records; preserve stable identity/revision where demonstrated necessary. |
| 2 | Information | Test convergence to workspace Note/content plus tags/relations; retain separate owner only for distinct lifecycle need. |
| 3 | Source Admission | Preserve source identity, origin, checksum and provenance even if storage changes. |
| 4 | Document extraction | Prefer replaceable parser adapter + source-linked derivative; avoid second permanent extraction authority. |
| 5 | pgvector Retrieval | Candidate for replacement by Hindsight after comparative acceptance and exact-source recovery proof. |
| 6 | Knowledge | Separate ordinary Documentation from genuinely governed Knowledge; avoid duplicate working-content authority. |
| 7 | Project Claims | Preserve qualification/provenance/gate semantics; evaluate file-native content plus governed admission. |
| 8 | EntityRelations | Preserve governed typed relations; evaluate file carrier with stable EntityRefs; Hindsight remains derived. |
| 9 | Categories | Compare against hierarchical tags/folders/facets; retain only if independent responsibility remains. |
| 10 | WorkIssue | Re-evaluate scope; preserve only durable governed work responsibility actually needed. |
| 11 | WorkIssue Scopes | Preserve bounded scope semantics if WorkIssue survives; do not confuse scope link with semantic relation. |
| 12 | Execution Results | Preserve candidate/result and human review distinction; runtime success never equals accepted result. |
| 13 | Decision Requests / Decisions | Preserve human attention gate and immutable decision semantics; file representation only after protected-write proof. |
| 14 | ChangeCandidates / variants | Preserve bounded proposal/review/apply semantics for consequential mutations; do not force on ordinary notes. |
| 15 | Contradiction Review | Test consolidation into generic typed candidate/review path without losing contradiction-specific evidence. |
| 16 | Project Anatomy | Preserve four-primitive domain contract and qualification boundaries; no automatic migration to Hindsight authority. |
| 17 | Professional Documents | Preserve stable professional document/revision identity; workspace is not automatically the lifecycle owner. |
| 18 | Document currentness | Preserve unresolved/conflicting currentness semantics; never infer authority from newest file alone. |
| 19 | Issuer/external-reference observations | Preserve provenance; candidate for implementation consolidation under Document lifecycle. |
| 20 | Exact byte retention | Preserve exact bytes/digest when contractual/professional need exists; generated Markdown is not replacement. |
| 21 | Human identity/access | Preserve provider-neutral technical identity/access; technical access remains distinct from professional authority. |
| 22 | Document comments | Test convergence to linked workspace Notes/comments where lifecycle permits; comment remains != Decision/Evidence. |
| 23 | Paperless | Keep optional adapter only; never architecture pillar or second document authority by default. |
| 24 | Cockpit → Hermes Handoff | Preserve immutable bounded handoff/context correlation; candidate core of executable control. |
| 25 | Execution Admission | Preserve one bounded admitted runtime opportunity and revocation/expiry semantics. |
| 26 | Launch Reservation | Preserve one-shot/replay/freshness guarantees where consequential execution requires them. |
| 27 | Hermes Result Candidate | Preserve candidate-only return and review boundary; Hermes completion never becomes truth/approval. |

For each row, Phase 0 must record exact tables/modules/APIs/schemas/tests/consumers before any code is removed.

## 19. Migration method

Use a strangler/convergence migration. Do not rewrite the system in one step.

### Phase 0 — complete responsibility inventory

For all 27 responsibilities, produce:

```text
current doctrine owner
current executable owner
tables/files/modules/APIs
canonical content
identity semantics
invariants
transaction requirement
provenance requirement
projection consumers
retrieval/index requirement
tests
real deployment usage
proposed target owner decomposition
```

Completion criterion:

```text
27/27 responsibilities accounted for
+ no unexplained duplicate authority
+ no consumer left unmapped
```

### Phase 1 — architecture roadmap

This PR.

No runtime/persistence change.

### Phase 2 — doctrine convergence

Modify Pantheon-Next rules explicitly where the target would otherwise contradict current doctrine.

Requirements:

- one responsibility cluster at a time;
- exact owner/consumer inventory first;
- preserve governance non-equivalences;
- update schemas/tests when machine-checkable invariants change;
- no implementation merge that depends on an unmerged doctrine change.

### Phase 3 — bounded synthetic file-native fixture

Build one non-production fixture proving:

```text
stable IDs independent of paths
arbitrary folder hierarchy
schema/version validation
duplicate-ID refusal
move/rename identity preservation
normal vs consequential write boundary
exact digest/revision conflict refusal
workspace → Card/Collection projection
Hindsight one-way derivation
Hindsight stale/outage behavior
```

No production owner migration.

### Phase 4 — retrieval convergence

Compare Hindsight against existing Pantheon retrieval using representative agency/project questions.

Measure at least:

```text
useful retrieval
project/trust-domain isolation
source citation quality
exact-source recovery
stale-index behavior
outage behavior
rebuildability
```

Only demonstrated equivalence/superiority allows retirement of duplicate Pantheon semantic indexing.

### Phase 5 — migrate low-consequence content owners

Candidate order after doctrine approval and fixture acceptance:

```text
Project/workspace metadata
Notes / Information-like working content
Documentation / ordinary Knowledge-like content
agency tag vocabulary
simple explicit relations
```

Preferred transition:

```text
old owner read-only compatibility
→ new source owner active
→ migrate consumers
→ reconciliation report
→ acceptance tests
→ rollback window
→ old persistence retirement
```

Avoid indefinite dual-write synchronization.

### Phase 6 — governed records

Only after write/gate/control-record semantics are proven, evaluate file-native representation for:

```text
Decisions
Claims
Qualifications
ChangeCandidates
other protected governed records
```

Content may be file-native while transition admission remains transactional/governed separately.

### Phase 7 — specialist owners

Explicitly review before touching:

```text
Project Anatomy
Professional Documents/currentness
exact byte retention
human identity/access
external adapters
```

These responsibilities have distinct invariants and must not be swept into a generic "everything is Markdown" migration.

### Phase 8 — reduce `pantheon-mvp`

Remove business persistence and duplicate retrieval only after consumers and invariants migrate.

Candidate residual responsibilities include:

```text
policy enforcement
workspace adapter
execution/admission safety
auth adapters
exact-source/storage adapters
Cockpit projections
```

Do not rename/split the repository merely to match the target diagram.

### Phase 9 — residual transactional-store review

After business-table removal, inventory residual PostgreSQL use.

Only then decide:

```text
keep PostgreSQL
or
replace residual control storage with a simpler transactional technology
```

No DB migration for aesthetics.

## 20. Required artifact for every responsibility migration PR

Every migration PR must include or link one **Responsibility Migration Sheet** with:

```text
responsibility name
current doctrine owner
current executable owner
current persistence
current consumers
current tests
source-of-record before
source-of-record after
identity mapping
schema/version mapping
invariants retained
invariants intentionally removed + reason
transaction/concurrency needs
provenance mapping
read compatibility path
write path
cutover sequence
rollback sequence
reconciliation procedure
acceptance tests
decommission criteria
open uncertainty
```

A migration PR is not ready if any field affecting authority is "TBD" without an explicit blocking decision.

## 21. Cutover and compatibility rules

### No permanent dual write

A compatibility period may use:

```text
old owner = read-only compatibility
new owner = sole write owner
```

Do not create a durable bidirectional sync engine between old PostgreSQL business tables and file-native sources.

### Reconciliation before retirement

Before removing an old owner, generate a deterministic report covering at minimum:

```text
record count / object identity coverage
missing IDs
duplicate IDs
field/value mismatches
unmapped relations
unmapped provenance
consumer migration status
```

### Rollback

Rollback must specify whether it means:

```text
return reads to old read-only owner
restore source backup
reverse a schema migration
re-enable old executable module
```

Rollback must never silently create two writable owners.

### Compatibility expiry

Every temporary compatibility adapter/path needs an explicit removal criterion. "Temporary" without a deletion condition becomes permanent complexity.

## 22. Acceptance test matrix

Each migrated responsibility should select the relevant cases below.

### Identity/lifecycle

```text
create valid record
move record
rename record
duplicate stable ID
missing stable ID where required
broken relation target
archive vs delete
restore
```

### Validation/schema

```text
valid current schema
valid older readable schema
unknown schema version
invalid managed record
migration dry-run
partial migration interruption
```

### Concurrency/write safety

```text
expected digest matches
expected digest stale
simultaneous competing writes
idempotent retry
replayed protected operation
partial write/failure
re-read result digest mismatch
```

### Governance

```text
ordinary direct edit
managed invalid edit
protected edit without gate
protected edit with valid gate
expired/foreign/replayed gate
runtime success without professional approval
```

### Retrieval/derived state

```text
Hindsight current
Hindsight stale
Hindsight unavailable
source changed after recall
cross-project/trust-domain leakage attempt
inferred relation not canonicalized
```

### Sync/operations

```text
create/edit/rename/delete across qualified sync path
offline edit + reconnect
simple sync conflict
backup restore
Hindsight rebuild
service restart
```

### Security

```text
path traversal
absolute foreign path
symlink escape
unauthorized workspace root
technical access without professional authority
secret-bearing input/log redaction where applicable
```

Acceptance must include negative/adversarial cases, not happy-path-only tests.

## 23. Development verticals — keep implementation focused

Do not attack all 27 responsibilities in parallel.

Recommended sequence after Phase 2 doctrine convergence:

### Vertical A — read model

Reuse current filesystem projection and prove arbitrary hierarchy, stable projection behavior and no business inference.

### Vertical B — one managed file-native object

Use a synthetic Project/Note-like fixture to prove:

```text
stable ID
schema/version
exact read
move/rename
Cockpit projection
Hindsight derivation
```

No consequential transition.

### Vertical C — one bounded managed write

Prove optimistic digest/revision conflict handling and one canonical Workspace write path.

### Vertical D — one protected transition

Reuse existing policy/gate/PEP structures to prove:

```text
candidate change
→ exact source digest
→ valid human/gate decision
→ bounded write
→ control receipt
→ re-read
```

No broad professional owner migration yet.

### Vertical E — first real owner migration

Only after A-D pass, select one low-consequence responsibility from the 27-row matrix for real migration.

This sequence should prevent the architecture programme from becoming a simultaneous rewrite of files, policy, Cockpit, memory and PostgreSQL.

## 24. Operational dependencies and blockers

These issues are not all global blockers. They are prerequisites only when the corresponding capability enters a production tranche.

```text
Pantheon-Next#684
workspace/navigation parent convergence

Pantheon-Next#659
required before treating durable Hindsight as security/restore-qualified
for broader real agency workspace data

Pantheon-Next#660
required before relying on LiveSync/CouchDB as the multi-client
production synchronization path

Pantheon-Next#662
owns replaceable document structural-analysis qualification;
do not invent another parser pipeline here

Pantheon-Next#664
relevant prerequisite before a protected external-effect/control vertical
claims one bounded green consequential path

Pantheon-Next#607 / Pantheon-Next#644
own Project Anatomy real-environment qualification;
file-native convergence must not redefine the four-primitive core

Pantheon-Next#666
reminds this programme to converge existing doctrine rather than
create a new candidate doctrine layer for every concern
```

PR Pantheon-Next#685/runtime-memory qualification remains separate from this architecture. A provider choice must not become a hard-coded owner.

## 25. Observability without a new observability platform

The migration needs enough visibility to diagnose drift, not another subsystem.

Minimum useful signals where applicable:

```text
current source identity/path/digest
schema/version validity
last successful source write
last Hindsight indexed observation/digest when available
control/gate disposition for protected transition
consumer using legacy vs new read path
reconciliation mismatches
```

Prefer existing logs/status surfaces and bounded read-only diagnostics.

Do not adopt a new tracing platform merely because migration benefits from a few counters/status fields.

## 26. Performance guardrails

File-native must not degrade into full-vault scanning on every interaction.

Implementation should preserve:

```text
bounded directory reads for navigation
lazy/recursive Card Collections rather than whole-vault materialization
metadata parsing only when needed
rebuildable derived indexes for lookup/search
Hindsight for semantic retrieval rather than repeated brute-force file scans
```

Performance criteria should be measured on representative workspace sizes before production cutover. Do not introduce a cache as authority to solve performance.

## 27. Complexity budget

Future-proofing means replaceability and explicit contracts, not more services.

Do not create by default:

```text
new microservice
new business database
new relation graph
new memory layer
new workflow engine
new scheduler/queue
new rules compiler
new Card authority
new bidirectional sync engine between business owners
new global event bus
```

Before adding an abstraction, demonstrate that the responsibility cannot be represented by an existing owner plus a schema, adapter, control record or test.

## 28. Success criteria

Convergence is successful when:

1. humans can understand/edit ordinary professional/work content directly from files where those files are the declared owner;
2. stable governed identity does not depend on paths;
3. exact binary/professional sources retain required bytes/provenance independently of generated text;
4. Hindsight can be rebuilt without losing professional state;
5. Hindsight can be replaced without changing Pantheon authority;
6. runtime-memory provider can be replaced without changing professional records;
7. Hermes can be replaced without migrating professional records;
8. Cockpit can be rebuilt from declared sources plus bounded governed/control read models;
9. no business concept has two concurrent writable authoritative persistence paths;
10. consequential transitions remain provably gated even when their content is file-native;
11. PostgreSQL remains only where its transactional properties are demonstrated as useful;
12. useful MVP tests are preserved or replaced by equivalent acceptance tests;
13. 27/27 inventoried responsibilities have an explicit retained/moved/reduced/retired decision;
14. temporary compatibility paths have been removed or have explicit remaining owners/removal criteria;
15. backup, restore, reconciliation and rollback have been proven for migrated owners;
16. everyday architecture remains understandable as:

```text
Files/Sources = content
Pantheon = rules
Hermes = action
Hindsight = retrieval
Cockpit = view
```

## 29. Explicitly out of scope for this PR

This documentation tranche does not:

- modify `AGENCY_DATA_SYSTEM_OF_RECORD.md`;
- modify `OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md`;
- change canonical memory doctrine;
- select Mnemosyne or another runtime-memory provider as a Pantheon owner;
- deprecate Category;
- move the Tag Registry;
- rename vaults or banks;
- change Hindsight configuration;
- change Hermes runtime configuration;
- modify PostgreSQL schemas;
- modify `pantheon-mvp`;
- authorize file-native writes;
- implement a Workspace write adapter;
- change Decision/Evidence/Claim authority;
- migrate Project Anatomy;
- migrate Professional Documents/currentness;
- remove pgvector;
- change Cockpit roots;
- rename `pantheon-mvp`;
- approve a PostgreSQL-to-SQLite migration;
- implement LiveSync/CouchDB;
- harden Hindsight itself.

## 30. Next action after this roadmap

The next tranche is **doctrine convergence and the 27-responsibility migration inventory**, not production migration.

Required first outputs:

### A. Doctrine delta matrix

```text
current rule
→ target rule
→ invariant retained
→ affected schemas/tests/consumers
→ migration dependency
```

At minimum for:

```text
AGENCY_DATA_SYSTEM_OF_RECORD.md
OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md
Category/Tag classification doctrine
Registry operational ownership
runtime-memory terminology/binding boundary
```

### B. 27-responsibility owner matrix

For each row in section 18:

```text
KEEP
REDUCE
MOVE
REPLACE
OPTIONAL
UNDECIDED
```

with target owner, persistence need, invariant/tests to preserve and migration prerequisites.

Only after the applicable doctrine changes are reviewed/merged and the relevant owner rows are no longer ambiguous should implementation move professional owners away from the current PostgreSQL model.

## 31. Closure posture

This roadmap closes the architecture-definition question only at the **candidate target and development-handoff** level.

Still intentionally open:

- exact vault topology;
- exact file/frontmatter schemas;
- exact protection vocabulary;
- final runtime-memory provider selection per deployment;
- which Category requirements survive the Tag comparison;
- which governed records should actually become file-native;
- exact Project Anatomy/Professional Document persistence outcomes;
- final residual PostgreSQL scope;
- final repository naming.

Those choices must be resolved from repository evidence, doctrine deltas, the 27-responsibility matrix and bounded experiments rather than frozen here in advance.
