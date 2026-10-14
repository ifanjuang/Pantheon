# Workspace / AFFAIRES cartouche inspector and sync target

Status: selected target architecture; implementation remains bounded by Pantheon-Next#660 and Hindsight qualification by Pantheon-Next#659.

Current decision baseline:

- Pantheon-Next#1129 selected the direct NAS-mounted AFFAIRES topology;
- Pantheon-Next#1131 added the bounded Hindsight source producer and explicit revision-chronology handling;
- Pantheon-Next#1132 added transient, read-only memory reconciliation;
- Pantheon-Next#1133 added the dedicated reconciliation-profile deployment seam;
- Pantheon-Next#1135 qualified the concrete Linux NAS mount and kept the bounded agency reader separate;
- Pantheon-Next#1139 made cartouches optional enrichment and source files first-class in the Hindsight explorer path;
- Pantheon-Next#1144 added project-scoped project-platform/Hindsight ingestion and strict project routing;
- Pantheon-Next#1145 repaired the dedicated reconciliation-profile qualification helper;
- Pantheon-Next#1146 split the standalone AFFAIRES producer from the optional Cockpit process.

The Pantheon-Next#1134 repair attempt was closed without merge and is superseded by merged Pantheon-Next#1145. Configured still does not mean activated, and a reconciliation candidate is not Evidence.

This list records the decisions that define the current target; it is intentionally not a frozen `main` SHA. Always verify the current branch, open PRs and qualification issues before changing the topology.

This document remains the architecture owner for the Workspace Cockpit filesystem projection. It supersedes the earlier productive target based on Obsidian + Self-hosted LiveSync + CouchDB + Ubuntu-local vault mirrors.

Historical LiveSync/Obsidian qualification remains useful capability evidence, especially Pantheon-Next#703, Pantheon-Next#706 and Pantheon-Next#717. It no longer selects the productive AFFAIRES topology.

## 1. Goal

Project the existing professional filesystem into the Cockpit and Hindsight without creating a second document authority.

Selected target:

```text
NAS
└─ AFFAIRES
      │
      │ mounted on the Linux compute host
      ▼
Linux AFFAIRES indexer/sync daemon
      │
      ├─ initial scan
      ├─ filesystem watcher
      ├─ periodic reconcile
      ├─ source/cartouche pairing
      ├─ reconstructible technical index
      │
      ├────────────► Cockpit
      └────────────► Hindsight 0.10.x on Linux
```

The filesystem watcher belongs to the AFFAIRES daemon, not to Hindsight. Hindsight receives bounded producer operations from that daemon.

The professional source root remains **NAS / AFFAIRES** as mounted on Linux. There is **one AFFAIRES indexer/sync daemon** for this route; "Linux" describes where that single owner runs, not a second component.

The daemon is a technical synchronization/indexing component. It is not a business database, professional truth owner, Project identity owner, Evidence owner or approval engine.

## 2. Authority boundaries

Preserve:

```text
source bytes != cartouche interpretation
cartouche != Evidence
retrieved != truth
memory != Evidence
folder != governed identity
sync success != authorization
projection != persistence
```

The source file remains the source for its content.

The Markdown cartouche is an intentional human/derived description of that source. It may improve retrieval and Cockpit presentation but does not rewrite what the source proves.

Pantheon remains responsible for governed identities, decisions and professional authority where applicable.

Hindsight remains derived retrieval/memory.

Cockpit remains projection and interaction.

## 3. User-facing document convention

A normal documented source is represented by a pair in which the cartouche is dot-prefixed and preserves the complete source filename, including its extension:

```text
CCTP_IND_C.pdf
.CCTP_IND_C.pdf.md
```

or:

```text
DPGF.xlsx
.DPGF.xlsx.md
```

A Markdown source is unambiguous as well:

```text
notes.md
.notes.md.md
```

The source may be PDF, DOCX, XLSX, PPTX, Markdown or another admitted professional file type.

The leading dot distinguishes a document cartouche from an ordinary Markdown source. Preserving the complete source filename prevents collisions when several source formats share the same stem, for example `CCTP.pdf` and `CCTP.docx`.

The sidecar is Markdown, not a parallel JSON/YAML business sidecar.

```text
source.ext = source
.source.ext.md = cartouche
```

The cartouche may contain YAML frontmatter because Markdown frontmatter is a convenient carrier, but the user-facing artifact remains one `.md` file.

## 4. Cartouche contract

Machine-readable reserved-field contracts:

```text
schemas/workspace_cartouche.schema.yaml       = pantheon/cartouche/v1
schemas/workspace_folder_context.schema.yaml  = pantheon/folder-context/v1
```

These schemas validate the existing frontmatter vocabulary; they do not create a second JSON/YAML business sidecar or turn cartouche fields into governed authority.

Candidate minimal frontmatter:

```yaml
---
schema: pantheon/cartouche/v1
document_id: doc_...
source: CCTP_IND_C.pdf
project: VERGER
phase: DCE
type: CCTP
index: C
document_date: 2026-09-12
issuer: StructureCo
# Optional and never inferred from index/date/name:
revision_mode: supersedes
revision_of: doc_previous
tags:
  - structure
  - ossature-bois
---
```

Candidate body:

```markdown
# CCTP — Lot 03 Ossature bois

## Résumé
...

## Points importants
...

## Limites / incertitudes
...

## Relations
...
```

Fields are not automatically governed merely because they appear in frontmatter.

In particular:

```text
project hint != governed project_id
folder name != governed project_id
index label != professional currentness
document date != revision order
filename similarity != revision order
summary != source claim
declared revision relation != governed professional decision
```

Optional revision fields are structural declarations only:

```yaml
revision_mode: supersedes | supplements
revision_of: doc_...
```

They are never generated from an index, a date or a filename.

```text
supersedes
= this bundle explicitly declares that it replaces the referenced occurrence

supplements
= this bundle explicitly declares that it adds to the referenced occurrence;
  the referenced occurrence remains independently relevant
```

If neither field is present, Pantheon records no revision relation. It does not guess one.

## 5. Identity

The cartouche carries a stable `document_id` for the filesystem bundle and `schema: pantheon/cartouche/v1`. A missing or incompatible schema makes the card `CHECK`, not `COMPLETE`.

The `document_id` must be unique across the admitted AFFAIRES projection. A copied pair that duplicates an existing `document_id` is rendered `CHECK` with `DUPLICATE_DOCUMENT_ID` and must not be synchronized to Hindsight until resolved.

The cartouche may carry a stable `document_id` for the filesystem bundle.

This identity exists to keep the source/cartouche pair stable across ordinary filesystem moves. It must not silently replace an already governed Professional Document identity where one exists.

When a bundle later maps to a governed Document owner, reuse/resolve that owner rather than create a competing identity system.

### Move

The operator moves both files together:

```text
/DCE/CCTP_IND_C.pdf
/DCE/.CCTP_IND_C.pdf.md

→

/MARCHE/CCTP_IND_C.pdf
/MARCHE/.CCTP_IND_C.pdf.md
```

The stable cartouche identity remains the same.

The path changes.

```text
path != identity
```

### New index / new physical document

If the user intentionally keeps the old file and creates another file:

```text
CCTP_IND_B.pdf + .CCTP_IND_B.pdf.md
CCTP_IND_C.pdf + .CCTP_IND_C.pdf.md
```

they are separate bundle occurrences with separate `document_id` values.

This remains true even when:

- both files carry the same index because of a human naming/indexing mistake;
- the later-issued file carries a lexically lower index;
- the higher index carries an earlier `document_date`;
- the filenames look almost identical.

```text
document_id
= identity of this filesystem document occurrence

index
= descriptive business label

document_date
= descriptive date supplied for the document

revision_mode + revision_of
= explicit declared relationship between occurrences
```

If the corrected bytes overwrite the same intended filesystem occurrence in place, the same `document_id` may remain and the changed source fingerprint drives a Hindsight replacement of that occurrence.

If the old file is preserved and a new physical bundle is created, assign a new `document_id`. Link the two only when the relation is explicitly known:

```yaml
revision_mode: supersedes
revision_of: doc_old
```

or:

```yaml
revision_mode: supplements
revision_of: doc_base
```

Do not infer a hidden version chain from similar names, contents, indices or dates. A contradictory index/date does not override an explicit relation and does not create one when none exists.

## 6. Pairing

Primary pairing rule:

```text
source filename = SOURCE.ext
cartouche name  = .SOURCE.ext.md
+ cartouche declares source: SOURCE.ext
→ paired bundle
```

The filename relation is exact, one-to-one and case-sensitive on Linux. The explicit `source` reference must match the exact source filename and remains a consistency check, not a second identity owner.

Do not infer pairing from a shared stem alone. Do not case-fold the Linux pairing key. If multiple source names collapse to the same case-insensitive / Unicode-normalized portable name, keep them distinct but render `CHECK` because the mounted NAS or another client may not preserve that distinction.

If filesystem events arrive separately during a move/save, use a bounded grace/stability window before declaring a source or cartouche deleted.

## 7. Broken-pair states

### Source + cartouche

Cockpit renders the rich document card from the cartouche and verifies the declared source exists.

### Source without cartouche

The source remains visible.

Render a deliberately different minimal card:

```text
CCTP_IND_C.pdf
PDF

Cartouche manquant

[ Générer le cartouche ]
```

Do not silently invent business metadata from the filename.

A supported source does not require a cartouche to enter the normal bounded Hindsight source route. Below an identified project directory it inherits the strict project scope; a root-level source remains in `PENDING_SCOPE` until identification. In both cases the source keeps technical identity/provenance and no business metadata is invented from its filename.

A cartouche is optional enrichment. When present and valid it may contribute a declared `document_id`, descriptive project/type/phase metadata, source integrity binding and explicit relation declarations, but it is not an admission gate.

### Cartouche without source

Render an explicit source-missing state.

```text
cartouche present != source present
```

Never treat a retained summary as proof that the source still exists.

## 8. Folder context

Optional `_folder.md` may describe a folder when that context has actual value. When present, its frontmatter uses `schema: pantheon/folder-context/v1`. The projection must explicitly distinguish `folder_context_present=true` from `false`; document cartouches such as `CCTP.md` do not satisfy the folder-context check:

```text
VERGER/
└─ DCE/
   ├─ _folder.md
   ├─ CCTP_IND_C.pdf
   ├─ .CCTP_IND_C.pdf.md
   ├─ DPGF.xlsx
   └─ .DPGF.xlsx.md
```

It can provide display/context fields and retrieval hints.

Architecture-agency folder conventions and their optional posture remain owned by `docs/domain-packs/architecture/DOCUMENT_AND_KNOWLEDGE_ORGANIZATION.md`. The inspector must accept another existing organization as usable; it may observe or propose a mapping, but it must not silently reorganize AFFAIRES.

Do not require it for every directory.

```text
_folder.md != Project identity
folder context != professional approval
```

## 9. Cockpit navigation

The existing `implementation/workspace_cockpit` is the component to evolve. Do not add a parallel filesystem Cockpit.

Historical implementations scanned LiveSync filesystem mirrors. The selected implementation indexes the actual AFFAIRES root as mounted by Linux; no local source-tree mirror participates in the productive topology.

Target behavior:

```text
filesystem changes
→ daemon updates reconstructible index

Cockpit navigation
→ reads index
→ does not recursively rescan AFFAIRES on every click
```

The operator starts at the admitted workspace root and sees only its immediate
folders and documents. Opening a folder requests only that indexed folder's
immediate children; a breadcrumb returns to any ancestor, and large sibling
sets are paginated. Folder cards retain their context and tags, while document
cards retain descriptive metadata, declared tags and Hindsight sync state.
Hindsight remains the memory/retrieval surface; the reconstructible index is
the hierarchy/navigation surface.
Sibling items use horizontal Swiper decks. A vertical Swiper moves between
loaded hierarchy levels; opening a folder loads its immediate children.
Breadcrumbs and explicit folder controls provide the same navigation without
gestures, while explicit card controls expose details accessibly.

The index may keep:

```text
path
parent path
basename
kind
document_id
source_present
card_present
source mtime / size / digest state
card mtime / digest
frontmatter projection
summary excerpt
sync state / last error
```

The index is technical cache/state only.

Deleting it must cause a rebuild, not loss of professional knowledge.

### Workspace-health projection

The Cockpit should preserve a report-oriented health view without turning presentation labels into professional status.

Candidate states include:

```text
COMPLETE
source + cartouche are present and structurally coherent

CARTOUCHE_MISSING
source exists but no cartouche is paired

SOURCE_MISSING
cartouche exists but its declared source is absent

CHECK
pair exists but local deterministic checks need attention

SYNC_ERROR
the technical producer has not converged with its target
```

These states support counts, filters and anomaly review. They are local projection vocabulary only:

```text
workspace health != professional currentness
health finding != defect confirmed
SYNC_ERROR != source invalid
COMPLETE != Evidence
```

The view may suggest a correction or explicit Generate action, but it must not auto-fix, rename, merge, archive, relink or rewrite professional material merely because a health check fires.

## 10. One producer

Do not introduce:

```text
Cockpit watcher
+
Hindsight watcher
```

Use one daemon:

```text
AFFAIRES daemon
├─ maintains Cockpit index
└─ emits Hindsight synchronization operations
```

This removes duplicated scans, duplicated event handling and competing delete/rename semantics.

## 11. Watcher + reconcile

Use both mechanisms:

```text
watcher   = responsiveness
reconcile = convergence guarantee
```

Startup performs a full reconcile.

A periodic reconcile catches:

- NAS/SMB events missed during outages;
- daemon downtime;
- event coalescing;
- transient move/save sequences;
- state-cache loss/rebuild.

The watcher must not be considered the source of truth.

## 12. Technical persistence

A small SQLite database or equivalent is acceptable for the daemon.

It may hold technical state such as:

```text
document_id
current path
source/card digests
size / mtime
last_seen
Hindsight source/card ids
last sync state
last error
```

It must not become the only owner of:

- title;
- summary;
- tags;
- limits;
- project meaning;
- document type;
- professional status.

Those human-readable descriptive fields belong in the cartouche when this file-native representation owns them.

## 13. Hindsight boundary

Pantheon-Next#659 owns Hindsight runtime and retain/retrieval qualification.

The selected productive mapping keeps one Hindsight document per eligible professional source:

```text
NAS / AFFAIRES source
→ standalone Workspace producer
→ technical or declared document_id
→ Hindsight files/retain as <document_id>:source
→ parsed source content
→ chunks + derived memories
```

A supported source without a cartouche is eligible when its project scope is identified or explicitly held in the pending-identification queue. A valid cartouche is optional enrichment, not an admission gate.

Pantheon does not create a second retrievable Hindsight `doc_...:card` document. Valid cartouche fields may be copied only as namespaced `cartouche_*` provenance metadata. They are not inserted into source text or extraction context, and descriptive index/date/revision labels are not allowed to establish source chronology.

The historical A/B/C alternatives have converged to one productive route:

```text
A = source + bounded identification context      ← implemented
B = namespaced cartouche provenance metadata     ← implemented when a valid cartouche exists
C = separately retrievable cartouche             ← not selected
```

Do not add C unless measured retrieval quality demonstrates a material need.

### On-demand memory reconciliation

Cockpit may ask Hermes to critique the Hindsight-derived state for one exact
`doc_...:source`, but this remains a read-only candidate path:

```text
Workspace document_id
        │
        ├─ bounded cartouche projection
        └─ exact Hindsight document
              ├─ chunks
              └─ memories filtered by document_id
                         │
                         ▼
             dedicated no-tool Hermes profile
                         │
                         ▼
       transient MemoryReconciliationCandidate-shaped response
```

No new governed owner is introduced by the response shape. The candidate is transient
and is not persisted by this slice.

Hard boundaries:

```text
Hindsight derived state != original NAS source
cartouche relation != source truth
Hermes finding != memory mutation
Hermes finding != Evidence
candidate != accepted correction
```

The reconciliation route must not receive the NAS path or Hindsight `original_text`.
It may receive only sanitized chunks, sanitized memory units, bounded cartouche
projection and an optional bounded user focus.

Hermes must run through a dedicated profile whose API-server tool surface is disabled.
For Hermes 0.21.3 the profile requires `platform_toolsets.api_server: [no_mcp]`; an
empty list alone does not suppress globally enabled MCP servers. No plugins, hooks or
project workspace are admitted for this profile.

Defense in depth requires the Cockpit client to:

1. inspect `GET /v1/toolsets` before every run and fail closed if any toolset is enabled;
2. use Responses with `store:false`;
3. reject any returned `function_call` / `function_call_output`;
4. delete the Hermes session before returning a successful candidate;
5. fail with an explicit residency error when that deletion cannot be proven.

Exact source verification remains a later, separate path:

```text
document_id
→ exact admitted workspace://source?sha256=...
→ Pantheon path/root/hash checks
→ read source in place from the NAS mount
→ compare source against Hindsight
```

Do not collapse that future source-verification path into Hindsight-only reconciliation.

## 14. Context passed to source extraction

The cartouche may supply bounded identification context such as:

```text
document type
project/affaire hint
phase
issuer
stable tags
```

The first Hindsight producer slice deliberately keeps `index`, `document_date`, `revision_mode` and `revision_of` out of the file-retain extraction context. They remain available to Cockpit/reconciliation, but they are not allowed to bias source fact extraction or decide which document is current.

Revision declarations may later be used by a dedicated reconciliation/view layer, but they must not authorize deletion or be promoted into source evidence merely because the cartouche contains them.

Do not silently feed a speculative/derived summary into source extraction as though it were source fact.

```text
context for orientation != source evidence
```

## 15. Emails and illustrative attachments

A logical source does not always equal one physical attachment.

For an email:

```text
email body
+ inline images
+ ordinary illustrative photos
→ one logical multimodal Hindsight document where appropriate
```

A genuinely autonomous attached document may become its own source/cartouche bundle after classification.

Do not create a standalone Hindsight document for every decorative/illustrative photo by default.

## 16. File eligibility

Initial automatic Hindsight eligibility:

- PDF with native text;
- DOCX;
- XLSX;
- PPTX;
- TXT/MD/HTML where useful.

No automatic OCR.

For a scanned PDF/image requiring OCR:

```text
visible in Cockpit
→ OCR needed / unavailable state
→ explicit user/Pantheon action
→ derived OCR result
```

Do not NAS-wide OCR automatically.

Initially exclude from automatic Hindsight retain:

- RVT/RFA/RTE;
- PSD/PSB;
- unsupported/heavy binaries;
- lock files;
- temporary files;
- backup/autosave/cache/log artifacts.

A specialized BIM extraction path may be added later only when demonstrated necessary.

## 17. Cockpit generation action

`Générer le cartouche` is an explicit user action.

Candidate sequence:

```text
observe exact source
→ create stable bundle/cartouche skeleton
→ exact technical metadata
→ optional Hermes semantic enrichment
→ render as draft cartouche
→ re-read/validate
```

Hermes may propose:

- full title;
- summary;
- tags;
- important points;
- limits;
- semantic relations.

Hermes must not populate `revision_mode` or `revision_of` merely from filename similarity, index ordering, dates or inferred chronology. A revision relationship must come from an explicit human declaration or another specifically admitted authoritative relation source.

Hermes must not invent:

- file digest;
- source existence;
- governed Project identity;
- Evidence;
- professional currentness;
- approval.

Generation success does not automatically make the cartouche professionally validated.

## 18. Current Pantheon data owners

The repository already has Postgres-backed governed Information and document/extraction structures.

This file-native cartouche must not silently duplicate those authorities.

Observed current distinctions remain:

```text
source_documents
= governed/ingested source representation in the MVP store

Information
= canonical Postgres-backed Information object

AFFAIRES cartouche
= filesystem-native descriptive representation
```

Where a cartouche is later promoted/mapped into a governed object, use an explicit mapping/admission path.

Do not make Cockpit rendering itself persistence.

## 19. Historical topology

The following are no longer required by the selected AFFAIRES target:

```text
Obsidian
Self-hosted LiveSync
CouchDB
headless LiveSync filesystem mirror
hindsight-obsidian-sync
document.yaml as the default business sidecar
```

They may remain in historical qualification records or optional unrelated workflows.

Do not interpret their historical qualification as a requirement to retain them.

## 20. Migration of the current Workspace Cockpit

Current implementation facts after the Slice 1 candidate (Pantheon-Next#1112):

- `implementation/workspace_cockpit/server.py` remains read-only;
- it projects `source.ext + .source.ext.md` bundles and optional `_folder.md` context;
- it exposes `COMPLETE`, `CHECK`, `CARTOUCHE_MISSING`, `SOURCE_MISSING` and `FOLDER`;
- bounded Markdown is read, while heavy source bytes are not opened for ordinary projection;
- temp/lock/Revit-backup files are filtered and heavy professional binaries remain visible;
- the Generate cartouche affordance is visible but has no write route in this slice;
- it still scans on request rather than through the selected reconstructible index;
- Ubuntu deployment must mount only the reviewed AFFAIRES root already mounted by Linux; historical LiveSync vault mirrors are retired from the active path.

Migration sequence:

### Slice 1 — source/cartouche projection — implemented candidate Pantheon-Next#1112

- recognize source.ext + .source.ext.md pairs;
- parse bounded frontmatter/body;
- expose complete, missing-card and missing-source states;
- preserve safe same-directory source references;
- keep the UI read-only; a visible Generate affordance does not authorize a write.

### Slice 2 — index/reconcile — implementation candidate Pantheon-Next#1115

- build a reconstructible SQLite technical index outside watched roots;
- keep the current Cockpit snapshot in memory so `/api/workspaces` does not rescan AFFAIRES per request;
- perform a startup reconcile and periodic full reconcile;
- use Linux inotify only as a responsiveness accelerator;
- coalesce filesystem event bursts through a bounded debounce window before reconcile;
- preserve source/cartouche `document_id` when the operator moves both files together;
- expose `folder_context_present` so a folder explicitly reports whether `_folder.md` exists;
- do not treat a missing `_folder.md` as invalid because folder context remains optional;
- keep the state database reconstructible and non-authoritative.

### Slice 3 — Hindsight producer

- one producer from the same daemon;
- explicit eligible formats;
- source retain;
- optional cartouche retain based on Pantheon-Next#659 A/B/C result;
- delete/update reconciliation;
- no automatic OCR.

### Slice 4 — deployment convergence

- mount the actual reviewed AFFAIRES root directly from the Linux-visible NAS path, read-only unless an explicit governed cartouche-write posture is enabled;
- retire CouchDB/LiveSync/vault-mirror requirements from the active Workspace Cockpit baseline;
- keep historical tooling only if another demonstrated workflow still uses it.

## 21. Performance acceptance

Ordinary folder navigation must not depend on hashing or parsing every source file in AFFAIRES.

Expected:

```text
open Cockpit folder
→ index lookup / bounded immediate children
→ render
```

Heavy hashing, parsing and Hindsight retain happen asynchronously in daemon reconciliation, not in the UI request path.

Qualification should measure at least:

- initial cold scan;
- warm folder navigation;
- 1 changed cartouche;
- 1 changed PDF;
- move of a source/cartouche pair;
- daemon restart;
- NAS unavailable then restored.

## 22. Security and safety

Reject:

- symlink escapes outside admitted roots;
- relative source refs escaping the bundle/root;
- arbitrary server path reads from browser input;
- public unauthenticated write actions;
- secret values in cartouches;
- automatic consequential writes based solely on a filesystem event.

The generated cartouche action requires an explicit user request and whatever existing admission/authorization path applies to the actual write surface.

## 23. Done criteria

The target is qualified when:

- one source + one Markdown cartouche is the normal user-facing document bundle;
- no separate JSON/YAML business sidecar is required;
- complete and broken pairs are represented explicitly;
- Cockpit shows folders/files without full-tree rescans on each navigation;
- the technical index is reconstructible;
- watcher + periodic reconcile converge after restart/outage;
- source + cartouche moves preserve stable bundle identity;
- one daemon owns both Cockpit indexing and Hindsight synchronization;
- unsupported/heavy/temp files do not enter Hindsight automatically;
- OCR is explicit only;
- Hindsight source/card provenance remains distinguishable;
- no folder/path is silently promoted into governed Project identity;
- no cartouche/retrieval result is promoted into Evidence automatically;
- current Postgres/governed owners remain authoritative where applicable.

Tracking: Pantheon-Next#660 for filesystem/Cockpit producer, Pantheon-Next#659 for Hindsight runtime and retain/retrieval qualification.


## Linux-mounted NAS qualification

The productive topology is qualified from the Linux host that runs the Workspace daemon and Hindsight.

```text
Linux host
├─ mounted NAS path /.../AFFAIRES
├─ Workspace Cockpit/indexer/sync daemon
└─ Hindsight 0.10.x
```

The mount qualification must exercise the mounted path itself:

```bash
python3 deployment/ubuntu/qualify-affaires-linux-mount.py \
  --root /path/to/mounted/AFFAIRES --require-network-mount
```

The probe verifies:

- dot-prefixed cartouche round-trip on the mounted filesystem;
- exact source/cartouche projection;
- rename while preserving `document_id`;
- reconstructible reconcile state;
- Linux inotify propagation when provided by the mount.

An absent inotify event is a degraded performance signal, not a correctness failure, because periodic reconcile remains the convergence guarantee.

```text
mount visible != mount healthy
inotify observed != convergence proof
reconcile success != professional validation
```

## Source residency invariant

The NAS-mounted AFFAIRES tree is the only durable professional source tree in this topology.

```text
NAS source
→ Linux mount
→ read in place

NAS source
↛ local AFFAIRES mirror
↛ LiveSync mirror
↛ Hindsight source authority
```

Local Linux persistence may contain only reconstructible technical state or derived memory. It must not silently become a second professional file repository.

An on-demand Hermes analysis must not be implemented by copying the whole file tree locally or exposing unrestricted NAS browsing to the model. Exact source access, when enabled, must be bound to an explicitly admitted source reference and read from the mounted source in place.
