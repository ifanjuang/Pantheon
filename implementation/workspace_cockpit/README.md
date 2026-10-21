# Workspace Cockpit

This is the filesystem Workspace projection owned by Pantheon for local document browsing.

Architecture owner:
[`docs/architecture/WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md`](../../docs/architecture/WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md).

Tracking:
- Pantheon-Next#660 owns the AFFAIRES filesystem/cartouche index and single producer;
- Pantheon-Next#659 owns Hindsight runtime and retain/retrieval qualification.

## Selected target

The selected professional target is now:

```text
NAS / AFFAIRES
      │ mounted on Linux
      ▼
standalone AFFAIRES producer
scan / watcher / reconcile
      │
      ├────────► Hindsight on Linux
      └────────► technical SQLite projection
                         │
                         ▼
                  Workspace Cockpit
                  optional / read-only
```

Hindsight does not own a second filesystem watcher. The standalone Workspace
producer watches/reconciles the mounted NAS path and is the only producer into
Hindsight. The Cockpit reads the persisted SQLite projection with
`--projection-only`; stopping the Cockpit does not stop ingestion.

When a root is produced by its own producer into a separate SQLite index, pass
`--workspace-db NAME=/absolute/index.sqlite3` with `--projection-only`. That
root is then read from its own index while the other roots keep `--state-db`;
the Cockpit presents them as one read-only view and never writes either index.

### Folder navigation

The Cockpit opens at the admitted workspace root and shows only that folder's
immediate children. Selecting a folder loads that indexed folder's immediate
children, with a breadcrumb for returning to any ancestor. Large folders are
paginated. The browser does not receive the complete Workspace card set on
initial load, and navigation reads the producer-owned SQLite projection rather
than recursively scanning the NAS. Folder context and tags remain visible on
folder cards; document metadata, Hindsight status and declared tags remain on
document cards. Producer-local Hindsight tags are labelled as local state or
pending intent, never as a remote read-back. Hindsight remains the
memory/retrieval service, not the folder listing index.

Sibling documents and folders appear in one horizontal Swiper deck for the
currently loaded folder. Selecting a folder requests its immediate children;
breadcrumbs and explicit folder controls provide navigation back to ancestors.
Large folders are paginated. Card details use an explicit accessible control.
Previous/next controls remain available if the pinned Swiper asset cannot load.

The bounded UI endpoints are `/api/workspace-overview` and
`/api/workspace-children`; `/api/workspaces` remains available as a legacy full
projection endpoint for existing local consumers.

The Ubuntu installer bundles pinned Swiper 14.3.0 assets under `static/vendor`.
The browser uses the `/workspace/` base path for assets and API calls; the local
server accepts both that mounted prefix and its root path so Tailscale Serve can
keep `/workspace` without rewriting the application.

### Optional local-tool menu

The Cockpit can be a private entry point without becoming a proxy or an
authentication boundary. Set only URLs that are actually published for the
operator; an unset or malformed entry remains hidden:

```text
WORKSPACE_COCKPIT_HERMES_URL=https://host.tailnet.ts.net/
WORKSPACE_COCKPIT_HINDSIGHT_URL=https://host.tailnet.ts.net:8443/
WORKSPACE_COCKPIT_MNEMOSYNE_URL=
```

Each link opens in a new tab. The menu never exposes the Hermes API and does
not infer a dashboard from a service merely being installed.

A document may still carry an optional enrichment cartouche:

```text
source.ext
.source.ext.md
```

where the hidden Markdown file preserves the complete source filename. Project-platform-synchronized
documents do not require one cartouche per file: the first directory below the admitted
workspace root defines the project scope, and every descendant directory contributes a
cumulative folder tag. Optional `_folder.md` files may stabilize or enrich folder context.

Directories whose name contains the distinct word `Archive` or `Archives` are
excluded recursively by default, case-insensitively. This covers `Archives`,
`_ARCHIVES`, `01-Archives` and `PLANS ARCHIVES`, while a source file such as
`registre-archives.pdf` remains admissible. Neither an excluded directory nor any
descendant is scanned. Additional exact directory names may be configured with
`WORKSPACE_EXCLUDED_FOLDERS`.
The Linux project-platform profile additionally excludes every directory named `RATP` or
`AGENCY_RATP`, recursively (the latter is the current name observed on the NAS).
Files ending in `_archive`, `_bak`, `_backup` or `_old` (with spaces, dots or hyphens
accepted as separators) are also excluded. A missing source is removed from active recall
on the first available scan and its derived Hindsight document is deleted on the second;
the NAS source itself is never changed.
The source scan is restricted to PDF, DOCX, XLSX, PPTX, TXT, Markdown, HTML and
EML. RVT/RFA, logs, images, PSD, DWG, archives and other unsupported formats are
not indexed or sent to Hindsight.

The target does not require Obsidian, Self-hosted LiveSync, CouchDB, a LiveSync filesystem mirror, `hindsight-obsidian-sync`, or `document.yaml` as a business sidecar.

Historical qualifications of those components remain useful evidence and are not erased by this migration.

## Current implementation state

The executable code in this directory is being migrated in bounded slices.

Slice 1 (Pantheon-Next#1112) is merged and Slice 2 is implemented as candidate Pantheon-Next#1115.

The current implementation:

- remains read-only for professional source/cartouche material;
- recognizes `source.ext + .source.ext.md` bundles;
- reads optional `_folder.md` context and explicitly exposes whether each folder has one;
- recognizes document cartouches only through the hidden full-source naming rule `.SOURCE.ext.md`;
- treats an ordinary Markdown file such as `notes.md` as a possible source, with `.notes.md.md` as its cartouche;
- does not confuse a document cartouche with the folder cartouche;
- renders complete, cartouche-missing and source-missing states;
- reads only bounded Markdown plus filesystem metadata during reconciliation;
- keeps heavy source bytes unopened;
- exposes a disabled Generate cartouche affordance without introducing a write path;
- serves `/api/workspaces` from the producer-owned persisted projection in productive deployment;
- persists only technical synchronization state in SQLite outside watched roots;
- uses Linux inotify in the standalone producer as an accelerator and a periodic full reconcile as the convergence guarantee;
- keeps the Cockpit HTTP/UI process free of NAS recursion, filesystem watcher ownership and Hindsight producer writes;
- is configured by the Ubuntu deployment against the reviewed AFFAIRES path mounted directly by Linux; no source-tree mirror is required.

The remaining migration owned by Pantheon-Next#660 is:

```text
Slice 1  source.ext + .source.ext.md projection and broken-pair states — merged Pantheon-Next#1112
Slice 2  reconstructible index + watcher + periodic reconcile — candidate Pantheon-Next#1115
Slice 3  same daemon emits bounded Hindsight producer operations
Slice 4  Ubuntu deployment converges from vault mirrors to the reviewed Linux-mounted AFFAIRES root — implemented candidate
```

Do not create a second filesystem Cockpit or an independent Hindsight watcher to bypass this migration.

## Source integrity

A cartouche may optionally bind itself to exact source bytes:

```yaml
source_sha256: <64 hexadecimal characters>
source_size_bytes: <exact source byte length>
```

The checksum is verified only when it is declared. Ordinary AFFAIRES navigation therefore does not hash every large source.

```text
document_id = identity of this filesystem document occurrence
path        = current location
source_sha256 = observed byte identity

index/date/name != revision order
filename pairing != byte identity
declared checksum != verified checksum
verified source bytes != professional truth
```

For `.eml` bundles, `source_sha256` and `source_size_bytes` are required because the RAW message and its Markdown derivative must remain explicitly bound. A missing, invalid or mismatched integrity declaration makes the bundle `CHECK`.

Producer eligibility is separate from parser-format support:

```text
format supported + root-level file without project directory
→ visible in Cockpit
→ hindsight_format_supported = true
→ PENDING_SCOPE
→ scope:pending-identification
→ eligible for ingestion but excluded from normal project recall

format supported + file below a project directory + no cartouche
→ FOLDER_SCOPED
→ deterministic path identity
→ project scope inherited from the first directory
→ cumulative folder ancestry tags
→ hindsight_representation_candidate = source

COMPLETE source format supported
→ hindsight_representation_candidate = source

verified COMPLETE .eml
→ hindsight_representation_candidate = cartouche
```

These fields are only structural candidates for the producer owned by Pantheon-Next#659. They do not select Hindsight's durable A/B/C mapping and do not authorize a retain/write.

## Revision semantics

Indices, dates and filenames are descriptive only. They may contain human errors and must never create a hidden version chain.

Optional explicit relation:

```yaml
revision_mode: supersedes
revision_of: doc_previous
```

or:

```yaml
revision_mode: supplements
revision_of: doc_base
```

Rules:

```text
same index != same occurrence
higher index != newer
later date != replacement
earlier date + higher index != error inferred by Pantheon
similar filename != same document

supersedes
= explicit declaration that this occurrence replaces another

supplements
= explicit declaration that this occurrence adds to another;
  both remain independently relevant
```

No relation fields means no known relation. A missing referenced historical document is exposed as an unresolved/missing relation but does not invalidate an otherwise valid source. Self-reference or malformed relation fields produce `CHECK`.

## Moves, copies and project reclassification

An unchanged source moved inside the same project keeps its technical
`document_id`. The producer patches the complete Hindsight tag set and updates
the current path in Cockpit without retaining or extracting the source again.
An identical simultaneous copy receives a new technical identity.

A move across first-directory project scopes fails closed as
`RECLASSIFICATION_REQUIRED`; the old Hindsight memories remain under their old
project scope. To confirm the move explicitly, add a valid document cartouche
that reuses the displayed technical `document_id` and declares:

```yaml
scope_move_confirmed: true
```

After confirmation, unchanged bytes keep their memories while Hindsight replaces
their complete tag set. Hindsight invalidates and re-consolidates affected
observations under the new project tag; it does not re-extract the source text.
Cockpit remains authoritative for the current filesystem path because Hindsight
0.10.2 can patch document tags but not document metadata such as `source_path`.

If a source is corrected in place and remains the same intended filesystem occurrence, it may keep the same `document_id`; changed bytes then replace the same Hindsight `doc_...:source`. If the old file is retained and a second physical document is created—even with the same index—the new bundle gets a new `document_id` and any relationship must be declared explicitly.

## Authority boundaries

```text
source bytes != cartouche interpretation
cartouche != Evidence
retrieved != truth
memory != Evidence
folder != governed identity
projection != persistence
sync success != authorization
```

The Workspace Cockpit is a projection. It does not become a document authority merely because it can render or edit a cartouche.

Postgres-backed governed Information and existing governed document/extraction owners remain authoritative where their contracts apply.

## Local HTTP surface

The current local HTTP process exposes:

- `/` for the Cockpit interface;
- `/api/workspaces` for the current filesystem projection;
- `/api/health` for service supervision;
- `/api/role-traces/*` as the existing compatibility route for the optional same-origin, read-only observable-stage sidecar.

The browser never receives the Hermes Runs key or internal sidecar keys. The sidecar is in-memory only and cannot create, approve, retry or stop a run.

## Current local execution

The historical fixture remains runnable while the migration is in progress:

```bash
python3 implementation/workspace_cockpit/server.py \
  --root FIXTURE="$PWD/docs/examples/workspace_manifest_inspector/workspace"
```

The container/native installers now require the Linux-visible AFFAIRES mount directly. They do not create, synchronize or maintain a local source-tree copy.

The operator selects `PROJECTS_ROOT` locally. It must be the admitted source
root whose direct children are project directories. The repository does not
encode a NAS hostname, share, project name, or intermediary folder; a broader
NAS share is not an admissible root when it mixes unrelated material.

## Hindsight boundary

The Workspace Cockpit does not itself make retrieved material authoritative.

The first producer qualification implements only the smallest A mapping:

```text
COMPLETE or FOLDER_SCOPED
+ unique cartouche or deterministic workspace-path document_id
+ Hindsight-supported source format
+ source representation candidate
        │
        ▼
same Workspace reconcile owner
        │
        ▼
Hindsight files/retain
document_id = doc_...:source
```

The source file is opened directly from the admitted Linux-visible AFFAIRES root. Pantheon creates no local staging file. The HTTP adapter uses a bounded transient in-memory multipart buffer; the default source bound is 100 MiB, matching Hindsight 0.10.2's default file-conversion batch-size limit.

Only bounded orientation fields are passed as extraction context. A valid optional
cartouche also contributes namespaced `cartouche_*` provenance metadata, including
its declared index, date and explicit revision relation. These declarations are not
inserted into the source text or extraction context and therefore remain visibly
distinct from facts extracted from the document. An absent or invalid cartouche
contributes no enrichment and never blocks a supported source. The cartouche body
and derived summary are not injected as source claims.

This slice does **not** close Pantheon-Next#659's A/B/C comparison:

```text
A = source + bounded descriptive context         ← implemented
B = namespaced cartouche provenance metadata     ← implemented when valid
C = separately retrievable cartouche            ← not selected
```

Verified `.eml` bundles currently project a cartouche representation candidate and therefore remain outside this source-only producer slice.

The daemon records only reconstructible synchronization mechanics in the same SQLite state database:

```text
SUBMITTED / PENDING / PROCESSING
→ poll Hindsight operation
→ COMPLETED

same document_id + changed source fingerprint
→ wait for active operation to finish
→ retain again with the same doc_...:source id
→ Hindsight replaces the document

bundle still present but no longer eligible
→ BLOCKED

bundle absent
→ first available scan: QUARANTINED, source/project recall tags removed
→ second available scan: ARCHIVED, exact derived Hindsight document deleted
→ source returns before deletion: tags restored without duplicate retention
```

The lifecycle is bounded to derived Hindsight state. It pauses when the workspace is
unavailable and refuses a large disappearance affecting more than 25% of at least 20
known sources. It never deletes or changes a mounted source file.

The emitted tag vocabulary and the mandatory project-scoped Hermes query rules are
defined in
[`HINDSIGHT_TAG_TAXONOMY.md`](../../docs/governance/HINDSIGHT_TAG_TAXONOMY.md).

No automatic OCR is part of the AFFAIRES baseline. The reviewed Hindsight deployment posture is:

```text
HINDSIGHT_API_RETAIN_MISSION=<professional-document chronology extraction mission>
HINDSIGHT_API_FILE_PARSER=markitdown
HINDSIGHT_API_FILE_DELETE_AFTER_RETAIN=true
HINDSIGHT_API_FILE_PARSER_MARKITDOWN_OCR_ENABLED=false
HINDSIGHT_API_STORE_DOCUMENT_TEXT=true
```

After a PDF retain completes, the producer performs one read-only quality check on
Hindsight's extracted text. Empty text and characteristic `(cid:…)` corruption are
projected as `OCR_NEEDED` in Cockpit. This is advisory and never blocks the source
document, launches OCR, or replaces the retained source. Marker OCR remains an
explicit per-file operator action; any resulting text is a derived representation,
not the professional source of authority.

A PDF conversion that terminates with an explicit `No content extracted` or
`No text extracted` parser error is classified the same way as `OCR_NEEDED`, rather
than as a generic producer failure. It is not automatically retried or OCR-processed.
A transient document-read failure during the post-retain quality check remains
`CHECK_ERROR` and is retried on the next reconcile without retaining the source again.

The retain mission asks Hindsight to preserve explicit chronology stated by the source itself: document date, revision/index/version token and explicit supersession relationships. It also tells Hindsight to preserve conflicting chronology statements rather than silently resolving them. The producer sends `timestamp: "unset"` for these reference documents so ingestion time is never presented to the extraction model as the document's event date.

Cartouche-declared `index` and `document_date` remain useful Workspace hints, but they are deliberately not sent to Hindsight as the source revision/date. The source content must establish those observations.

So uploaded source bytes are intended to be transient inside Hindsight after file conversion, while extracted document text/chunks and derived memories remain durable Hindsight state.

### Producer configuration

The producer is disabled unless both its URL and bank are configured.

For the native systemd deployment, create `/etc/pantheon-workspace-cockpit.env` with reviewed values such as:

```text
WORKSPACE_HINDSIGHT_URL=http://127.0.0.1:8888
WORKSPACE_HINDSIGHT_BANK_ID=<reviewed-bank-id>
WORKSPACE_HINDSIGHT_PARSER=markitdown
WORKSPACE_HINDSIGHT_MAX_SUBMITS_PER_RECONCILE=4
WORKSPACE_HINDSIGHT_MAX_FILE_MB=100
WORKSPACE_HINDSIGHT_SETTLE_OBSERVATIONS=2
WORKSPACE_HINDSIGHT_SOURCE_KIND=project-sync
```

`WORKSPACE_HINDSIGHT_AUTHORIZATION` may be supplied there when the selected Hindsight exposure requires it. The environment file is optional; absence keeps the producer inactive.

### Optional raw-text representation

By default each source is retained once, as `<document_id>:source`. Setting `WORKSPACE_HINDSIGHT_TEXT_STRATEGY=<name>` (or `--hindsight-text-strategy`; `configure-workspace-producer --text-strategy`) also retains the same source a second time as `<document_id>:text`, through the retain strategy `<name>` that the **bank must define** (for example raw chunks without fact extraction). The second document carries the same tags plus `representation:text`, and is the part a reader can search within minutes while facts are still being extracted.

```text
the raw text is searchable even when no fact was extracted
a failed raw-text retain never blocks, delays or repeats the source retain
sources already indexed before the option was set get their raw text without being extracted again
quarantine, tag updates and deletion apply to both documents; a missing twin is not an error
```

Each projected card gains `hindsight_text_status`, `hindsight_fact_count` and `hindsight_piece_state`:

| `hindsight_piece_state` | Meaning |
|---|---|
| `indexed` | the source is retained and, with the option on, so is its raw text |
| `searchable_text` | the raw text is searchable although the source has no fact yet (or none was extracted) |
| `partial` | retained, but without any fact or without its raw text |
| `extraction_failed` | nothing could be retained |
| `ocr_needed` | no text could be read; manual OCR remains a per-file decision |
| `in_progress` | a retain is waiting or running |

The fact count is read once per source version and only with the option on. A source with no fact is a signal, never an error: it stays listed and its raw text stays searchable. Without the option the producer behaves exactly as before.

```text
filesystem present != professionally validated
retain submitted != retain completed
retain completed != truth
memory != Evidence
technical synchronization != authorization
```

## On-demand Hindsight memory reconciliation

Cockpit may expose one explicit action for a `COMPLETE` source-backed document:

```text
[ Réconcilier avec Hermes ]
Focus optionnel: [...]
```

This first reconciliation slice is intentionally Hindsight-only:

```text
exact Workspace document_id
        │
        ├─ bounded cartouche projection
        └─ Hindsight <document_id>:source
              ├─ exact document identity/hash/count metadata
              ├─ exact document chunks
              └─ memory units filtered by exact document_id
                         │
                         ▼
              dedicated no-tool Hermes profile
                         │
                         ▼
              transient candidate-only result
```

It does **not** read the original NAS source, does not send the source path to Hermes,
does not send Hindsight `original_text` or arbitrary document/memory metadata, and
does not write to Hindsight, Workspace, NAS or a Pantheon governed owner.

The project-scoped Hindsight router uses source-grounded evidence mode. It asks
only for `world` and `experience` facts, disables consolidated observations, and
returns at most eight distinct results. Every returned fact must carry both an
exact `document_id` and `chunk_id`; unsourced observations are omitted. Project
and source tags remain mandatory with `all_strict`, and an optional folder can
only narrow that boundary.

The result categories are bounded to:

```text
missing
inconsistent
too_general
contradictory
organization
```

The optional focus is untrusted orientation text, limited to 2000 characters. The
whole serialized Hindsight/cartouche packet is bounded by
`WORKSPACE_RECONCILE_MAX_CONTEXT_CHARS` (48000 by default).

### Dedicated Hermes profile contract

Do not point this route at the normal Hermes profile. Hermes 0.21.3 does not treat an
OpenAI request `tools: []` as a per-request tool deny-list; the effective tools come
from the profile's `platform_toolsets.api_server`.

The reconciliation profile must be a blank/dedicated profile with no added hooks or
project workspace and this tool posture:

```yaml
platform_toolsets:
  api_server:
    - no_mcp
plugins:
  enabled: []
```

`no_mcp` is material. An explicit empty `api_server: []` list does not suppress
globally enabled MCP servers in Hermes 0.21.3.

Defense in depth:

```text
managed dedicated profile with api_server: [no_mcp]
        +
Cockpit GET /v1/toolsets before every analysis
        +
fail closed if any toolset reports enabled=true
        +
fail closed if Responses output contains a function_call
```

Cockpit calls the Hermes Responses API with `store:false`. Hermes still creates an
internal agent session for the turn, so Cockpit requires the returned
`X-Hermes-Session-Id` and deletes that session before returning a successful
candidate. If session cleanup cannot be proven, the candidate is withheld and the
request returns a residency failure.

Configuration is disabled by default:

```text
WORKSPACE_RECONCILE_HERMES_URL=http://127.0.0.1:8642/p/reconciliation
WORKSPACE_RECONCILE_HERMES_KEY=<profile-specific API_SERVER_KEY>
WORKSPACE_RECONCILE_HERMES_TIMEOUT_SECONDS=120
WORKSPACE_RECONCILE_MAX_CONTEXT_CHARS=48000
```

The URL may target a separately supervised profile or a multiplexed
`/p/<profile>` API surface, but it must resolve to the dedicated no-tool profile.
The API key is profile-specific. The dedicated Hermes profile is also the sole
authority for model selection. Cockpit deliberately does not send a per-request
model override: Hermes ignores bare model requests unless its broader
`direct_model_requests` surface is enabled, which is not appropriate for this
private reconciliation profile.

The Ubuntu operator helper can create or verify that profile without activating a
gateway or changing profile routing:

```bash
export HERMES_RECONCILIATION_API_KEY="$(openssl rand -hex 32)"
sudo -E bash deployment/ubuntu/configure-hermes-reconciliation-profile --apply

# Once a dedicated route has been activated separately, qualify the live surface:
bash deployment/ubuntu/configure-hermes-reconciliation-profile --check \
  --runtime-url http://127.0.0.1:8642/p/reconciliation
```

The helper disables external memory, requires built-in profile memory files to
remain empty, keeps only Hermes' no-bundled-skills baseline, disables dynamic tool
search, empties MCP/plugin bindings, and refuses a reconciliation API key equal to
the default Hermes API key. With `--runtime-url` it also verifies the live
`/v1/toolsets` surface is empty and that the Responses API plus session deletion
endpoint are advertised. It deliberately does **not** start a profile gateway,
enable multiplexing, change routes, or write Cockpit configuration.

```text
configured profile != activated route
runtime route observed != task authorization
```

```text
reconciliation candidate != memory update
declared inconsistency != proven source defect
Hindsight chunk != original source
Hindsight memory != Evidence
Hermes analysis != authorization
candidate returned != candidate persisted
```

Exact NAS-source verification remains a later, separate path through a bounded admitted
source reference. It is deliberately not hidden inside this button.

## Linux NAS mount qualification

From the Linux host that mounts AFFAIRES and runs the Workspace/Hindsight stack:

```bash
python3 deployment/ubuntu/qualify-affaires-linux-mount.py \
  --root /path/to/mounted/AFFAIRES --require-network-mount
```

The probe writes and removes one temporary pair, validates hidden cartouche persistence, exact pairing, rename identity and reconcile rebuild. It also reports whether inotify events propagate through the mount; periodic reconcile remains mandatory even when they do.

## No local source mirror

The professional source tree remains on the NAS.

```text
NAS / AFFAIRES
      │
      │ mounted by Linux
      ▼
/path/to/mounted/AFFAIRES
      │
      ├─ Workspace daemon reads in place
      └─ Hindsight producer reads in place
```

Pantheon does not maintain a second durable copy of `AFFAIRES` on the Linux disk.

Allowed local state is reconstructible or derived:

```text
/var/lib/pantheon-workspace-cockpit/index.sqlite3
Hindsight durable derived-memory volumes
temporary process buffers / bounded transient extraction
```

These are not professional source copies.

For the container deployment set `PROJECTS_ROOT` to the Linux-mounted NAS path. For native systemd installation use `--projects-root /path/to/mounted/AFFAIRES`.

The installer verifies read/traverse access but never rewrites NAS ACLs recursively.


## Active AFFAIRES project catalogue

The productive Workspace source is the reviewed `PROJECTS_ROOT`, whose direct
children are active project directories. `ARCHIVES/PROJET` is not admitted as a
Workspace source and is not scanned, indexed or sent to Hindsight by this path.

The standalone producer derives a bounded catalogue only from direct
first-level directories below `PROJECTS_ROOT` and persists it in the same
technical SQLite projection. The optional Cockpit reads that persisted
catalogue through:

```text
GET /api/project-catalogue
```

The API projects:

```text
name
state = active
root_kind = AFFAIRES
relative_root
routing_status = valid | conflict
automatic_routing_allowed
write_requires_confirmation
```

Active project entries may be automatic routing candidates. Filesystem
availability remains routing context, not governed Project identity or write
authorization.

If multiple direct child directories normalize to the same project name, every
matching candidate is marked `conflict` and automatic routing fails closed.

The user-facing Workspace/Gmail alias remains `AFFAIRES/<project>`; there is
no second Gmail `ARCHIVES/` namespace.

Nested directories named `Archive`, `Archives`, `PLANS ARCHIVES`, etc. remain
excluded recursively inside AFFAIRES.

Important identity boundary:

```text
filesystem path
!= governed project identity
!= permission to rewrite source history
```

The producer-generated technical occurrence id does not establish declared
document identity. Explicitly declared document identity continues to follow
its existing guarded semantics.
