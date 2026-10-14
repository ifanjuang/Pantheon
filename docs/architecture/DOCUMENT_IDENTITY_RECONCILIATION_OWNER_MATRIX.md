# Document identity reconciliation — candidate owner matrix

Status: candidate Phase-2 convergence note — documentation only.

Parent roadmap: `docs/roadmaps/FILE_NATIVE_CONTROL_CONVERGENCE.md` in PR Pantheon-Next#687.
Related workspace candidate: `docs/architecture/WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md`.
Executable synthetic proof: PR Pantheon-Next#688.
Parent workspace exploration: issue Pantheon-Next#684.

This note resolves one bounded owner question exposed by PR Pantheon-Next#688:

```text
unqualified workspace package
→ who observes it?
→ who preserves Source provenance when applicable?
→ who proposes an existing Document match?
→ who admits or creates Professional Document identity?
→ who writes the manifest mapping?
→ who projects currentness?
```

It does **not** change current doctrine, adopt a production manifest schema, authorize an Obsidian plugin, migrate a system of record, create a new intake domain, or make any Document admission path executable by itself.

The repository remains authoritative. This matrix is a convergence candidate for review before implementation.

## 1. Verified repository checkpoint

Checkpoint: 2026-08-22.

```text
Pantheon-Next/main
= 8c15eff5c767c76410db9e0f3a2e388f85ed1aac

pantheon-mvp/main
= d960862dd0e23b7003a0f3e4ee0ea630ffc12af9

PR Pantheon-Next#687 previous head
= 303cdfa8df9a350ec0c3219bdee5dd5789ceb439

PR Pantheon-Next#688 fixture head before stack sync
= 3a03c7c17be80ee5253d20726daf5c8a1289a070
```

Relevant observed contracts:

- `docs/governance/SOURCE_INTAKE_ADMISSION.md` is active support doctrine for preserving a Source before semantic/documentary ownership is established;
- `schemas/source_intake_admission.schema.yaml` defines `Source` identity, provenance and Project-link posture, and explicitly excludes automatic canonization, automatic ingestion, semantic extraction, Information creation and system-of-record mutation;
- Source Intake explicitly allows a later handoff to create or bind a Document while preserving `Source admitted != Document created`;
- `schemas/architecture-proof-register/document_family.schema.yaml` defines a stable `document_family_id` UUID across professional versions and explicitly does not persist a universal current version;
- `schemas/architecture-proof-register/indexed_document_version.schema.yaml` defines a distinct `document_version_id`, exact source/hash references and professional status/effect fields, while stating that the latest file is not automatically authoritative;
- `schemas/architecture-proof-register/document_currentness_projection.schema.yaml` remains the purpose-specific calculated currentness projection;
- `docs/domain-packs/architecture/AGENCY_COLLABORATION_AND_VERSION_INTAKE_CONVERGENCE.md` describes contextual intake, a Project Inbox reconciliation projection and unclassified intake without requiring a new canonical lifecycle owner;
- `docs/governance/AGENCY_DATA_SYSTEM_OF_RECORD.md` explicitly does not redefine Document source authority;
- repository searches at this checkpoint did not identify a current executable `pantheon-mvp` contract using `source_intake_admission`, `document_family_id` or `document_version_id` to own workspace-package → Professional Document reconciliation/admission.

The last point is an observed search result, not proof that no historical or external implementation exists. It means this roadmap must not claim a verified executable owner where none has been located in the current repositories.

## 2. Problem statement

PR Pantheon-Next#688 proves both edges around the missing seam:

```text
SCENARIO A
workspace package
+ already admitted document_family_id/document_version_id
→ sidecar may map the existing identities

SCENARIO B
workspace package
+ Markdown
+ no manifest
+ no admitted identity
→ local QUALIFIABLE skeleton
→ no UUID fabricated
```

The unresolved middle transition is:

```text
QUALIFIABLE local package
→ reconcile against existing Professional Document identity
→ or admit a new Professional Document identity
→ then write the mapping
```

The wrong response would be to add another domain object solely because this transition is currently missing.

Do not introduce by default:

```text
DocumentIdentityCandidate as a new canonical owner
ManifestAdmission as a parallel lifecycle
PluginDocument as a business object
HermesDocumentIdentity as an inferred authority
HindsightDocument as a durable identity owner
```

The convergence target is to connect existing Source and Professional Document responsibilities through one bounded executable seam.

## 3. Core convergence decision candidate

Candidate target:

```text
SOURCE INTAKE
= preserves an unqualified Source and provenance when an intake boundary is needed

PROFESSIONAL DOCUMENT
= owns admitted Document Family / Version identity and professional version semantics

PANTHEON CONTROL
= hosts the bounded executable adapter that reconciles and applies the transition
  between Source/workspace observation and Professional Document identity

WORKSPACE ADAPTER / INSPECTOR
= observes exact files/digests and writes a manifest mapping only after an admitted result

HERMES
= optional producer of semantic match candidates when deterministic resolution is insufficient

HUMAN
= resolves ambiguity or consequential creation/linking when required

COCKPIT / INSPECTOR
= projects candidates, unresolved state, admitted mapping and currentness overlays
```

This does **not** create a new Professional Document domain owner inside Pantheon Control.

Pantheon Control is the executable application/PEP seam for an existing domain responsibility:

```text
normative Document contract
→ bounded admission/binding operation
→ admitted Document Family / Version identity
```

The eventual persistence owner for admitted Professional Document records must still be explicitly selected during the corresponding migration. This note does not decide PostgreSQL versus file-native persistence for those governed records.

The bounded adapter must therefore be understood as an **effect/application seam**, not as the storage authority by itself.

## 4. Owner matrix

| Responsibility | Observed current owner / contract | Candidate target owner | Disposition | Boundary |
|---|---|---|---|---|
| Workspace bytes / authored Markdown | Declared workspace/source system | Same declared source owner | KEEP | File existence does not admit a Document. |
| Local folder/file observation | Current workspace projection / future Inspector | Workspace Adapter / Inspector, derived | KEEP / REDUCE | Paths, files and digests are observations, not professional identity. |
| Local `QUALIFIABLE` health | PR Pantheon-Next#688 fixture candidate only | Inspector projection vocabulary | OPTIONAL | `QUALIFIABLE != manifest required`. |
| Local skeleton before admission | PR Pantheon-Next#688 fixture candidate only | Device/workspace-local unresolved carrier | OPTIONAL | No governed UUID, currentness or authority. |
| Source identity + provenance at intake boundary | `SOURCE_INTAKE_ADMISSION` | Existing Source Intake seam | KEEP | `Source admitted != Document created`. |
| Project-link candidates for Source | Source Intake + optional Hermes producer | Existing Source Intake candidate mechanism | KEEP | Candidate score is explanatory only. |
| Explicit Project link for Source | Source Intake bounded operation + human where required | Same | KEEP | Project link does not create Document authority. |
| Existing Document Family lookup | Professional Document identity contract; no verified executable workspace resolver | Professional Document admission/binding adapter in reduced Pantheon Control | MAKE EXECUTABLE | Deterministic lookup may use exact admitted IDs/refs/digests; path alone is insufficient. |
| Ambiguous semantic Document matching | No verified executable owner | Hermes may propose candidates through the same adapter contract | OPTIONAL | Hermes proposal never binds identity. |
| Document Family admission / UUID allocation | Professional Document contract; executable owner not verified | Bounded Professional Document admission operation in Pantheon Control, persisting through the declared Document owner | KEEP DOMAIN / ADD SEAM | UUID allocated only as an admitted domain effect, never by plugin/Hermes/Hindsight. |
| Document Version admission / UUID allocation | `indexed_document_version` contract; executable owner not verified | Same Professional Document admission adapter + declared Document persistence owner | KEEP DOMAIN / ADD SEAM | New bytes/version do not imply currentness or authority. |
| Professional status/effect fields | Indexed Document Version contract | Existing Professional Document owner | KEEP | Not editable manifest truth by default. |
| Purpose-specific currentness | Currentness projection contract | Existing resolver/projection | KEEP | Never copied into manifest as universal current version. |
| Manifest identity mapping | Candidate workspace sidecar | Workspace Adapter after admitted result | OPTIONAL CARRIER | Manifest references identity; it does not create identity. |
| Manifest exact digest/binding | Workspace Adapter / exact source read | Workspace Adapter | KEEP | Stale digest refuses blind application. |
| Project Inbox reconciliation UX | Architecture intake convergence note | Cockpit/Inspector projection over candidate state | REUSE | Inbox is not another owner. |
| Durable follow-up on ambiguity | Existing WorkIssue only when follow-up is actually needed | WorkIssue | OPTIONAL | Reconciliation does not automatically create WorkIssue. |
| Semantic retrieval for candidate discovery | Hindsight candidate | Hindsight derived retrieval only | OPTIONAL | Retrieval may help find candidates; it cannot admit/bind identity. |
| Runtime conversational context | Hermes runtime-memory provider | Same runtime capability | NO DOMAIN ROLE | Memory is not Document identity or Evidence. |

## 5. Why Source Intake should not absorb Professional Document identity

`SOURCE_INTAKE_ADMISSION` already defines a deliberately smaller responsibility:

```text
receive
→ preserve source identity and provenance
→ leave unassigned or suggest Project candidates
→ explicitly link Project when bounded
→ hand off later processing to Document / Information / other owners
```

Therefore expanding Source Intake until it owns:

```text
Document Family
Document Version
professional effect
professional currentness
```

would make the intake boundary another monolith.

Preserve:

```text
Source identity
!= Document identity

Project link
!= Document admission

received/preserved
!= classified as professional Document
```

The Source seam should remain useful for email, images, URLs, models, documents and other inputs without inheriting every downstream domain lifecycle.

## 6. Why the manifest should not absorb Professional Document identity admission

A sidecar may eventually carry an admitted mapping:

```yaml
identity:
  document_family_id: <admitted UUID>

represented_version:
  document_version_id: <admitted UUID>
```

But:

```text
writing these strings into YAML
!= creating the governed identities
```

Otherwise any ordinary editor could manufacture a second Professional Document owner.

Required invariant:

```text
manifest mapping accepted
→ IDs must already resolve to the admitted Professional Document owner
  or be returned by one bounded admission operation
```

Direct human creation of a UUID-looking value in the sidecar is therefore an observed/unadmitted state until reconciled; it must not silently become canonical because validation syntax passes.

## 7. Two valid entry paths

Do not force every already-governed workspace package through Source Intake again.

### Path A — existing admitted Document mapping

When the package already carries a valid admitted identity and the exact mapping can be verified:

```text
select package
→ exact local read/digest
→ resolve admitted document_family_id/document_version_id
→ verify scope/binding
→ render COHERENT/CHECK
```

No duplicate Source intake object is required merely to rediscover an identity that is already governed.

### Path B — unqualified material crossing into the governed Document lifecycle

When no admitted Document identity exists:

```text
select package
→ exact local read/digest
→ QUALIFIABLE local state
→ online reconciliation requested
→ preserve/resolve Source provenance when the intake boundary applies
→ determine Project/scope context
→ resolve existing Document candidates
→ admit existing binding or new Family/Version through bounded Document operation
→ persist admitted identity/version through the declared Professional Document owner
→ write manifest mapping through Workspace Adapter
→ re-read exact mapping
→ project currentness separately
```

The Source step may reference the existing file/source without duplicating bytes when the declared source system already owns them.

```text
Source preservation requirement
!= copy every workspace file into another store
```

## 8. Candidate reconciliation algorithm

The algorithm should prefer deterministic evidence and stop on ambiguity.

```text
1. Re-read exact package.
2. Verify expected package/source digest.
3. Resolve declared Project/scope if available.
4. Search admitted Professional Document identities using exact identifiers first.
5. Use exact source refs/digests/external refs where legitimate.
6. If one deterministic admitted match exists, prepare that binding.
7. If several plausible matches remain, return candidates; do not mutate.
8. Hermes may rank/explain ambiguous semantic candidates if requested.
9. Human resolves ambiguity where policy requires.
10. If no existing family matches and creation is explicitly admitted,
    allocate a new Document Family identity through the Document operation.
11. Admit the represented/new Document Version through the same domain seam.
12. Persist the admitted result through the declared Professional Document owner.
13. Revalidate source/package digest before applying the manifest mapping.
14. Write the bounded mapping through the Workspace Adapter.
15. Re-read and verify.
16. Project currentness from its existing resolver; do not infer it locally.
```

This sequence deliberately separates:

```text
candidate discovery
!= identity binding

identity binding
!= new identity creation

admission adapter
!= persistence authority

new version admission
!= professional currentness

manifest write success
!= professional approval
```

## 9. Decision table

| Observed situation | Allowed candidate outcome | Forbidden shortcut |
|---|---|---|
| Manifest maps one valid existing Family + Version and digest matches | Reuse mapping | Allocate replacement UUIDs because path changed. |
| No manifest, exact external/governed reference resolves one Family + same admitted Version | Bind existing IDs after scope/digest checks | Create duplicate Family. |
| Existing Family resolved, exact content is a genuinely new version candidate | Admit a new Version under that Family | Create a new Family merely because filename/index changed. |
| Several Family candidates plausible | Return unresolved candidates / request human resolution | Pick highest semantic score automatically. |
| No existing Family found, human explicitly confirms a new professional Document | Admit new Family then initial/new Version through bounded Document operation and declared owner persistence | Plugin generates UUID and writes it directly. |
| No existing Family found, no explicit/admitted creation | Remain unresolved/QUALIFIABLE | Treat folder name as identity. |
| Offline / admission service unavailable | Keep local unresolved skeleton | Manufacture IDs for later reconciliation. |
| Package digest changed after candidate preparation | Mark stale / refuse application | Apply mapping based on old content. |
| Hindsight finds a likely related document | Show as candidate context | Convert Hindsight relation into governed binding. |
| Hermes confidently proposes a match | Show proposal + basis | Treat model confidence as admission. |

## 10. Human and policy boundary

Not every deterministic identity binding needs an extra ceremonial confirmation.

Candidate posture:

```text
exact already-admitted identity
+ exact expected scope/basis
+ non-consequential binding allowed by policy
→ may be applied through bounded operation without redundant confirmation
```

But:

```text
ambiguous existing identity
new Professional Document creation
scope conflict
professional status/effect mutation
currentness/effect consequence
→ human/policy gate as required
```

The exact classification must be established by the applicable policy/doctrine convergence before implementation.

Do not encode a blanket rule that every manifest write is protected, and do not encode a blanket rule that Document identity creation is an ordinary local edit.

## 11. Hermes boundary

Hermes is useful for questions such as:

```text
Does this look like a new index of an existing CCTP?
Which existing Document families are semantically plausible?
What human-readable title/type appears appropriate?
What ambiguity prevents a confident match?
```

Hermes may return:

```text
candidate family refs
candidate type/title metadata
match rationale
uncertainties
recommended human question
```

Hermes must not return an authoritative effect such as:

```text
create this UUID and consider it admitted
mark index D as current_for_execution
approve this Document
promote this Source to Evidence
```

The executable adapter, not Hermes, resolves admitted identifiers and applies authorized effects.

## 12. Hindsight boundary

Hindsight may improve candidate discovery after it is qualified for the relevant trust domain:

```text
package/source text
→ Hindsight related candidates
→ exact admitted source/Document refs
→ deterministic current read
→ reconciliation candidate
```

But:

```text
Hindsight recall != admitted Document lookup
Hindsight relation != governed relation
Hindsight freshness != source freshness
```

Consequential reconciliation must re-read the exact current source/record from its declared owner.

## 13. WorkIssue boundary

Do not create a new persistent reconciliation task object by default.

If one user action can resolve the mapping synchronously:

```text
candidate
→ review/apply
```

is enough.

Use the existing WorkIssue responsibility only when the reconciliation genuinely needs durable follow-up, for example:

```text
waiting for clarification
cross-person assignment
separate document review
blocked external information
resume later
explicit review trail
```

```text
unresolved reconciliation candidate
!= automatically a WorkIssue
```

## 14. Project Inbox boundary

Reuse the Project Inbox concept as a projection, not a domain owner.

Candidate presentation:

```text
PROJECT INBOX

CCTP/
  package digest ...
  no admitted Document mapping
  candidate: CCTP DCE — family <ref>
  candidate: CCTP travaux — family <ref>

[ Review mapping ]
[ New document ]
[ Leave unqualified ]
```

The same candidate state may be projected in the Obsidian Inspector Card without creating two persistence paths.

```text
Project Inbox
= reconciliation view

Inspector
= local/workspace view

candidate state / admitted owner
= shared underlying contract
```

## 15. Phase-2 delta matrix

| Current rule / observed state | Candidate target rule | Invariant retained | Contracts / consumers affected | Migration dependency |
|---|---|---|---|---|
| Source Intake preserves Source and may later hand off to Document. | Keep Source Intake small; make handoff explicit to one Professional Document admission/binding seam. | `Source admitted != Document created`. | `SOURCE_INTAKE_ADMISSION`, source adapters, Project Inbox. | Inventory real Source persistence/API first. |
| Professional Document schemas define Family/Version identity but no verified workspace admission adapter was found. | Add one bounded executable Professional Document admission/binding adapter inside reduced Pantheon Control; persistence remains with the declared Document owner. | Stable Family/Version identity; runtime does not own professional semantics. | Document schemas, future adapter/API, Cockpit/Inspector. | Decide executable persistence owner and operation contract. |
| Workspace projection sees folders/files only. | Allow deterministic observation + unresolved `QUALIFIABLE` candidate state. | `folder/path != governed identity`. | Workspace Adapter, Inspector, Cockpit Card projection. | PR Pantheon-Next#688 fixture acceptance. |
| A sidecar may eventually reference Document IDs. | Sidecar mapping may only reuse or consume IDs returned by admitted Document operation. | `manifest valid != identity admitted`. | Manifest candidate, Workspace write contract. | Production manifest schema still undecided. |
| Semantic matching owner is absent. | Hermes/Hindsight may propose existing candidates; adapter/human resolves. | `retrieved/model output != truth/authority`. | Hermes handoff/context, Hindsight retrieval, Inspector. | No new runtime owner required. |
| Currentness is calculated separately. | No change. | `latest/index != professional currentness`. | Currentness resolver, Card overlays. | None for identity seam. |
| Project Inbox is conceptual projection. | Reuse as one UI over reconciliation state. | `projection != persistence`. | Cockpit, Inspector. | Projection contract can follow executable seam. |
| Agency Data default SoR is PostgreSQL for listed agency records and excludes Document source authority. | Do not route Professional Document identity through Agency Data merely for convenience. | Domain authority remains explicit. | Agency Data API/Cockpit context only. | Separate later Agency Data file-native decision. |

This matrix is deliberately narrow. It does not complete the 27/27 responsibility inventory from the parent roadmap.

## 16. Candidate executable semantic operations

Do not freeze endpoint names yet. The executable seam needs effects equivalent to:

```text
resolve existing Professional Document binding
admit new Document Family when explicitly allowed
admit new Document Version under an existing/admitted Family
bind exact Source/workspace representation to admitted Version
return unresolved/ambiguous candidates without mutation
```

Prefer a small command-style contract over unrestricted CRUD/PATCH.

Required inputs should include the applicable subset of:

```text
Project/scope identity
exact Source or workspace reference
expected source/package digest
existing candidate Family/Version refs when supplied
user intent: bind existing | create new | undecided
actor/request provenance
idempotency key
policy/gate reference when required
```

Required outputs should distinguish:

```text
resolved_existing
admitted_new_family
admitted_new_version
ambiguous
unresolved
stale
refused
```

These names are illustrative response semantics, not an adopted schema.

## 17. Required refusal behavior

The future seam must refuse or remain unresolved when:

```text
expected digest is stale
candidate identity does not exist
candidate scope conflicts with requested scope
more than one candidate remains materially plausible
new identity creation is not admitted
replayed non-idempotent request is detected
manifest path escaped the configured workspace root
sidecar tries to assert currentness/approval as identity-admission input
Hermes/Hindsight candidate is presented without exact owner resolution
```

No implicit fallback to path-derived identity.

## 18. Acceptance tests before implementation adoption

### Existing identity

```text
existing Family + Version + exact digest
→ mapping succeeds
→ no new UUID allocated
```

### Move/rename

```text
package path changes
→ admitted Family/Version IDs remain unchanged
```

### New version of existing family

```text
existing Family
+ new exact content admitted as new version
→ one new document_version_id
→ same document_family_id
→ no currentness inferred
```

### Ambiguous family

```text
two plausible admitted Families
→ ambiguous
→ zero identity mutation
→ human resolution available
```

### New family

```text
no match
+ explicit admitted "new professional Document"
→ new Family ID allocated by Document adapter
→ Version admitted separately
→ admitted record persisted by declared Document owner
→ mapping written afterward
```

### Offline

```text
no admission service
→ unresolved skeleton may exist
→ zero governed UUID allocated
```

### Stale basis

```text
candidate based on digest A
current package digest B
→ stale/refused
→ no manifest identity write
```

### Source boundary

```text
Source admitted
→ no automatic Document Family creation
```

### Manifest boundary

```text
syntactically valid UUID typed manually into sidecar
+ no admitted owner record
→ CHECK/INVALID-unadmitted mapping
→ never canonicalized automatically
```

### Currentness boundary

```text
newest-looking index D admitted
→ current_for_execution remains unresolved/whatever resolver says
→ never inferred from D
```

### AI/retrieval boundary

```text
Hermes score = high
or Hindsight relation = strong
→ candidate only
→ zero automatic binding
```

### Already mapped package

```text
valid admitted mapping already present
→ verify directly
→ do not create duplicate Source intake object merely to rediscover it
```

## 19. Implementation ordering after doctrine review

Recommended order:

```text
1. Accept/revise this owner matrix in Pantheon-Next#687.
2. Merge/retarget PR Pantheon-Next#688 fixture after Pantheon-Next#687.
3. Inventory the real executable/persistence owner for Source Intake and Professional Documents.
4. Specify the minimal command/result contract for Document admission/binding.
5. Add synthetic adapter tests for existing-match / ambiguous / new-family / stale cases.
6. Only then design the production manifest schema fields that consume admitted identity.
7. Only then implement the Obsidian Inspector action against the adopted adapter.
```

Do not implement the plugin's `Generate` button as an identity allocator before step 4.

## 20. Explicit non-goals

This note does not:

- adopt `document.yaml` as a production schema;
- make all Markdown folders manifestable;
- require Source Intake for every already-governed file;
- decide the final persistence technology for Professional Documents;
- move Professional Documents into Agency Data PostgreSQL;
- create a new Project Inbox persistence owner;
- create a new durable `DocumentIdentityCandidate` object;
- authorize automatic AI identity matching;
- change currentness semantics;
- change Evidence or Decision semantics;
- implement a runtime, queue, scheduler or memory path;
- authorize production migration.

## 21. Exit criteria for this responsibility cluster

This Phase-2 cluster is ready for an executable contract PR only when review agrees that:

```text
1. Source Intake remains Source/provenance owner only.
2. Professional Document remains Family/Version identity owner.
3. One reduced Pantheon Control adapter applies the bounded reconciliation/admission effects without becoming the persistence authority by itself.
4. Plugin/Cockpit/Project Inbox remain projections/adapters, not identity owners.
5. Hermes/Hindsight remain candidate producers only.
6. Manifest mapping is written after admission and checked against exact digest.
7. Currentness remains separate.
8. No new canonical lifecycle object is required merely to bridge these responsibilities.
```

If any of these assumptions fails against a newly discovered executable owner or production requirement, update the matrix before implementation rather than adding a parallel path.