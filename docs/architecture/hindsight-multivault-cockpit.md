# Hindsight multi-vault and Cockpit processing queue

Status: source implementation in progress; no runtime migration has been
applied. Existing project and knowledge banks, producer services, SQLite
indexes and Hermes bindings remain separate until a reviewed migration is
applied.

## Boundaries

- Hindsight keeps its own database and its separate project and knowledge
  banks (names are node bindings).
- A single read-only Hermes MCP endpoint may expose both recall scopes. The
  project tools always require one project scope; knowledge tools never accept
  one. Tool choice follows the user's question, not the convenience of a
  combined endpoint.
- One producer/coordinator is the only writer to the two banks. A host-local
  nonblocking `flock` on the shared queue path rejects a second configured
  coordinator before it starts scanning. It loads a profile for each vault;
  profiles own the source root, bank ID, source tag,
  metadata rules, extraction policy and file-size limit. Credentials stay in
  systemd environment files or credential files, never in the profile or
  Cockpit database.
- The producer/preflight database is separate from Hindsight's database. It is
  the durable source for source fingerprints, queue order, preflight results,
  user corrections, notes, Hindsight operation state, pauses and errors.
- The Cockpit reads and changes queue-control state only through same-origin
  endpoints. It never submits files to Hindsight itself.
- AFFAIRES may configure one project-orientation Knowledge Page per first-level
  project folder. The profile supplies the French `project_overview_prompt`;
  Bibliothèque leaves it unset. The producer waits until an exact project-tagged
  consolidated observation exists, then creates or adopts one page and records
  its async build state in `hindsight_project_overview`. It advances at most one
  project-page lifecycle per reconciliation tick and never blocks file retain
  outcomes on page-generation failures. Hindsight refreshes the page after later
  consolidations. The page is an orientation summary; source documents remain
  authoritative. Prompt edits update a page created by the producer and schedule
  a refresh; an existing page not recorded as producer-managed is adopted without
  rewriting.

## Processing invariant

There is one ordered queue across vaults. Candidate discovery hashes and checks
sources without running an uncached preflight. The producer then processes the
priority head: it checks source stability, marks `ANALYZING`, runs or reuses the
preflight cache, marks `ANALYZED`, and submits that file to Hindsight. Only one
uncached preflight runs per reconciliation pass; lower-priority items wait for a
later pass. A paused vault does not start preflight or upload work. The
multi-vault daemon starts at most one Hindsight file-retain request at a time.
The coordinator lock is host-local and only serializes processes configured to
use the same lock path. Legacy producer units must still be stopped before the
combined coordinator is enabled.

Before every stage transition and before upload, compare the current file
fingerprint with the queued fingerprint. A mismatch supersedes the old queue
item, keeps its audit trail, invalidates the preflight result for ingestion,
and adds a new item at the configured priority. A moved file may retain its
technical document identity only after the existing identity rules resolve it.
The HTTP client reads at most the configured size bound plus one byte, hashes
the exact upload bytes, and refuses to send them if they differ from the
preflight/source fingerprint.

Hindsight outcomes are classified separately:

- **completed**: operation completed and an exact document read-back confirms
  the document in the configured bank;
- **verifying**: conversion completed but exact-document lookup returned 404;
  keep the operation attached and check again on the next pass without resending;
- **retryable error**: request did not reach acceptance, including an API that
  was unavailable before submission; retry with bounded backoff;
- **needs verification**: submission may have been accepted but the response
  or read-back failed for another reason, or Hindsight returned a different
  document identity; inspect the operation/document before any resend;
- **failed**: a terminal, actionable failure; show it in the error list;
- **modified**: source changed during processing; requeue with the new hash.

Before each upload, the producer commits a `SUBMITTING` intent to SQLite. After
a restart it searches the configured Hindsight bank's recent
`file_convert_retain` operations for the exact document ID and attempt time.
One exact match restores the operation ID and resumes polling without another
upload. Multiple matches require manual verification. An unavailable lookup or
no match after five minutes raises the queue's verification warning; lookup
continues in the background so a late-visible operation can still be recovered.
None of these cases triggers an automatic resend.
Hindsight does not provide a request idempotency key for this endpoint, so this
is a duplicate-avoidance and recovery protocol, not a mathematical exactly-once
guarantee.

For a `VERIFY` row, the Cockpit offers **Vérifier à nouveau**. The request is
stored durably in the shared SQLite queue and consumed by the coordinator. With
a known operation ID it checks that operation and the exact document; without
one it searches recent retain operations for the existing document ID. A remote
lookup failure leaves the request pending. A successful lookup clears only the
request that was consumed, so a newer operator click is preserved. This action
never authorizes a new upload; a `VERIFY` row cannot use the normal retry path.

HTTP validation/authentication/not-found rejections and a refused connection
are safe to retry. Timeouts, connection loss after request transmission, 408,
409, 425, 429 and 5xx responses are treated as uncertain and require operation
recovery or review.

Pausing a vault prevents new claims for that vault. Global pause prevents new
claims everywhere. Work already claimed may finish. Pause state persists across
restarts. A filter-scoped pause button must name the affected vault; the
unfiltered control applies globally.

## States shown in the Cockpit

The dot is a projection of persisted state, not a second state machine:

| State | Meaning | Display |
|---|---|---|
| À traiter | discovered or changed; waiting for preflight | steady yellow |
| Analyse en cours | preflight claim active | pulsing yellow |
| Analysé | current-fingerprint preflight completed | steady blue |
| Mémorisation en cours | Hindsight operation accepted or running | pulsing blue |
| Mémorisé | Hindsight completion confirmed | steady green |
| Échec | terminal processing error | steady red |
| À vérifier | outcome uncertain; safe retry not established | pulsing red |
| Fichier modifié | new source fingerprint detected | steady magenta |
| Stabilisation | source is settling before preflight | pulsing magenta |

Errors remain available in a secondary list with the source, failed stage,
time and concise reason. Terminal failures can be retried; uncertain outcomes
offer a remote verification action only. They are not silently reinserted at the
head of the active queue.

## Cockpit views and controls

- The existing hierarchical card/Swiper view remains optimized for browsing;
  it does not use drag sorting.
- A separate processing-list view shows Affaires and Bibliothèque in one list,
  with a vault badge, current stage, short reason, and queue position. SortableJS
  is attached only to a dedicated drag handle so ordinary pointer/touch motion
  scrolls the page.
- The list has a vault filter and global/vault pause and resume controls. The
  same status dot appears in both views.
- The row disappears from the active list only after confirmed Hindsight
  completion. Failed and uncertain rows go to the error list.
- Priority edits use optimistic UI only until the server acknowledges the new
  revision. The server rejects stale revisions and returns the authoritative
  order. The custom drag handle has touch actions disabled only on the handle;
  the rest of each row remains available for ordinary page scrolling.

## OCR derivative

- A successful explicit OCR creates one content-addressed Markdown file in the
  producer's persistent state directory (`ocr-cache`), outside both source
  vaults and outside the installed code directory. The filename is derived from
  workspace, technical document ID and raw-source SHA-256; the SQLite queue row
  stores its filename and OCR state. Hindsight, Hermes and Cockpit resolve the same
  identity and checksum; callers never submit an arbitrary filesystem path.
- Hindsight receives the Markdown under the stable document ID, with metadata
  identifying the original path, raw checksum, workspace and technical ID. The
  raw PDF remains authoritative and is not modified. The derivative stays after
  confirmed retain so Hermes can read bounded, line-numbered passages through
  `vault-read:read_vault_ocr_markdown`. Cockpit opens the authoritative source file.
- An explicit OCR rerun for an already memorized document atomically replaces
  the current source revision's Markdown. The queue marks it `MODIFIED` to show
  that the Hindsight memory may be stale; rerunning OCR does not silently delete
  or recreate a Hindsight document. New source checksums produce distinct
  artifacts, so a recalled historical memory can still resolve its derivative.
- Retained versions consume local storage. A cleanup policy must preserve any
  version still referenced by a Hindsight source and must never follow links
  outside the cache root.

## Durable model

Use the existing producer SQLite as the common database and add narrowly scoped
tables rather than creating one table per UI feature. The current source adds
`processing_queue` and `processing_controls`; vault profiles remain in a
credential-free JSON configuration file:

- `processing_queue`: stable document identity, vault key, source path, source
  SHA-256, priority rank, preflight/Hindsight statuses, operation ID, concise
  error, timestamps and row revision;
- `processing_controls`: global/vault pause state and update timestamp.

Preflight cache, source identity, metadata corrections and notes stay in their
existing tables. They are linked by vault/workspace and stable document ID;
cache entries are reusable only when their source hash and preflight version
match. The queue should not duplicate full metadata JSON or extracted text.

### Stage workers and queue independence

The shared row is consumed by separate bounded stage lanes, not three user-facing
lists. The preflight consumer runs in its own single worker thread, claims rows in
the shared priority order, requires the configured stable-source observations,
checks the source hash, and publishes `ANALYZED` or `FAILED` on that row. A
completed preflight wakes the coordinator immediately; Hindsight does not wait
for its next long periodic scan. A failed item stays visible and does not stop
later preflight requests. Restart recovery returns an interrupted `ANALYZING`
claim to `TO_PROCESS`.

OCR uses one asynchronous worker and persists its state on the same row.
Hindsight submissions remain one-at-a-time, independently of the OCR lane. OCR
completion wakes the coordinator immediately. A document cannot be submitted
while its own OCR is pending, but unrelated documents can advance. The deployment
must bound concurrency on any shared inference server (for Ollama, one parallel
generation and a bounded native request queue); the producer does not infer
activity from the list of loaded models. Pause controls stop new work at every lane, while
in-flight work is allowed to finish. All lane errors remain per-document and
retryable rather than terminating the coordinator.

The filesystem scan is still performed by the coordinator before it can enqueue
newly discovered files. A kernel-level blocked CIFS read can therefore delay
discovery/reconciliation, although it no longer stops already queued preflight
work or Cockpit reads. Eliminating that last coupling requires a separately
bounded scanner process and is a distinct follow-up.

## Rollout sequence

1. Add a `combined` read-only MCP mode while preserving the existing project and
   knowledge modes for rollback. Configure the two bank IDs and source tags
   independently; never let a missing knowledge-bank setting fall back to the
   project bank.
2. Create a coordinator/profile format and common queue schema. Migrate current
   per-vault indexes with backups and explicit table-by-table preservation; do
   not clear either Hindsight bank as part of this migration.
3. Merge the current producer indexes into a new SQLite output, then use
   `configure-workspace-multivault-producer --check` to validate the profile,
   roots, bank separation and output database. Its `--apply` installs the
   coordinator inactive and does not start ingestion. Keep the producer SQLite
   outside the source mounts and credentials outside the profile JSON.
4. Replace the two legacy producer units only after backing up their SQLite
   indexes and confirming both vault roots and distinct Hindsight bank IDs.
5. Keep the existing Cockpit browsing view and metadata editor; use its
   separate sortable queue view, vault filter and pause/retry controls against
   the shared coordinator database.
6. Point Hermes skills at the selected vault tools, then canary one file in each
   bank. Only after checking hashes, metadata propagation, operation read-back,
   failure recovery and both queues should the old workers be disabled.

The combined MCP mode, shared queue source, profile loader, coordinator lock,
priority-ordered preflight and Cockpit list are implemented in source. They do
not switch live Hermes bindings, install the new runtime modules, or change
running services. A reviewed database migration and confirmation that legacy
producer units are stopped remain open before production rollout.
