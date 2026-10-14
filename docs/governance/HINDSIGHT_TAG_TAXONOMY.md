# Hindsight tag taxonomy

Status: candidate implementation contract — project-scoped project-platform qualification.

This document is the canonical tag contract for filesystem documents retained by
the Pantheon Workspace producer in Hindsight. It defines retrieval scope and
navigation hints; it does not turn a folder, filename or memory into professional
truth.

## Principles

```text
tag = retrieval selector
metadata = provenance returned with a result
entity schema = normalized information extracted from content
page / mental model = derived synthesis
```

Only `scope:*` tags define a project-memory boundary. Other tags may narrow a
query but never authorize a cross-project recall.

The first-directory rule is evaluated below the locally configured admitted
project root, never from a broader NAS share that mixes unrelated material.

Ordinary navigation tags use lowercase slugs. Project boundary tags are stricter:
the producer combines a readable slug (maximum 80 characters) with the first
12 hexadecimal characters of SHA-256 over the exact NFKC/case-folded project
name. The project router computes the same token. This prevents two distinct
directory names such as `Projet A` and `Projet-A` from collapsing onto the
same strict retrieval boundary.

## Tags emitted by the Workspace producer

| Pattern | Meaning | Example | Retrieval role |
| --- | --- | --- | --- |
| `workspace:<workspace>` | Linux-visible admitted workspace | `workspace:project-platform` | Origin/navigation |
| `source:<kind>` | Source channel configured for the producer | `source:project-sync` | Origin/navigation |
| `scope:project:<slug>-<12hex>` | Project inherited from the first directory; cartouche context is used only for a root-level document | `scope:project:mediatheque-<12hex>` | **Strict project boundary** |
| `scope:pending-identification` | Document has no identified project | exact fixed tag | Separate identification queue only |
| `folder:<cumulative-path>` | Cumulative folder ancestry | `folder:mediatheque-03-execution-plans` | Drill-down inside an already selected project |
| `project_hint:<project>` | Descriptive project hint carried by the card | `project_hint:mediatheque` | Display/discovery; not a boundary |
| `phase_hint:<phase>` | Descriptive phase hint | `phase_hint:dce` | Display/discovery |
| `family:<family>` | Non-authoritative filename-derived document family | `family:plan-cvc` | Find possible versions |
| `revision_hint:<revision>` | Non-authoritative explicit filename revision marker | `revision_hint:ind-b` | Version discovery only |
| `tag:<subject>` | Optional bounded source/cartouche subject tag | `tag:ossature-bois` | Thematic navigation only |

Folder tags are cumulative. For:

```text
Mediatheque/03 Execution/Plans/Plan CVC IND-B.pdf
```

the producer emits:

```text
scope:project:mediatheque-<12hex>
folder:mediatheque
folder:mediatheque-03-execution
folder:mediatheque-03-execution-plans
```

The project scope is therefore stable even when a user searches only one deep
subfolder.

## Hermes query contract

Hermes must resolve the active project before asking Hindsight for project
material. A normal project-platform project recall uses:

```json
{
  "tags": [
    "source:project-sync",
    "scope:project:mediatheque-<12hex>"
  ],
  "tags_match": "all_strict"
}
```

Rules:

1. A project recall always includes exactly one `scope:project:*` tag.
2. Multiple query tags use `all_strict`; a broad `any` match is not a project
   boundary.
3. `folder:*`, `phase_hint:*`, `family:*`, `revision_hint:*` and `tag:*` may only
   narrow an already project-scoped query.
4. `project_hint:*` never substitutes for `scope:project:*`.
   When a cartouche project disagrees with the first directory, the first
   directory remains the scope and the disagreement is returned as provenance.
5. `scope:pending-identification` is queried only by an explicit identification
   workflow. Its results are never mixed into a project answer or page.
6. A `family:*` or `revision_hint:*` result is a lead to verify against source
   documents. It does not prove latest-version or supersession semantics.
7. Tags do not establish approval, validity, authorship, document authority or
   permission to act.
8. An unchanged move inside one project preserves the document identity and
   memory units while replacing the complete folder tag set. A move across
   `scope:project:*` boundaries is held as `RECLASSIFICATION_REQUIRED` until a
   valid cartouche reuses the displayed document identity and explicitly sets
   `scope_move_confirmed: true`.
9. Hermes-facing recall returns at most eight source-grounded `world` or
   `experience` facts. Each fact must expose an exact `document_id` and
   `chunk_id`. Consolidated observations without that provenance may support a
   separate exploratory workflow but cannot be returned as documentary proof.

If Hermes cannot resolve a unique project, it asks for the project or offers
candidate scopes. It must not fall back to a bank-wide document recall.

## Pages and mental models

Every project page or mental model uses the same strict scope selector as Hermes:

```text
scope:project:<slug>-<12hex>
```

A page may additionally select a folder or phase, but it cannot remove the
project tag. Suggested projections are:

- overview;
- chronology;
- documents and possible versions;
- document relations and unresolved references;
- decisions, risks and actors.

Pages are derived summaries. Material claims remain traceable to the exact
Hindsight document, source path and, when available, PDF page.

### Native project-page contract

Pantheon uses Hindsight's native knowledge page backed by a mental model. It
does not write a second summary file into the project tree and does not ask a
Hermes cron session to regenerate the page. This avoids duplicate documents in
normal project search and leaves refresh state, history and source provenance in
the memory system that produced the synthesis.

Create the page lazily when a project is first opened or explicitly requested;
do not pre-create one page for every directory. The first projection is one
compact project overview. Split chronology, financial review or schedule into
separate pages only when the overview has become too large to remain useful.

The page source query asks for these bounded sections:

1. object and current objectives;
2. actors and stated responsibilities;
3. contractual and administrative frame;
4. dated chronology;
5. lots, estimates, offers and comparison gaps;
6. schedule and milestones;
7. confirmed decisions;
8. risks, contradictions and open questions;
9. exact source references and freshness limits.

Use this trigger posture with Hindsight 0.10.2 or later:

```json
{
  "tags": [
    "source:project-sync",
    "scope:project:<slug>-<12hex>"
  ],
  "trigger": {
    "mode": "delta",
    "fact_types": ["world", "experience", "observation"],
    "exclude_mental_models": true,
    "refresh_after_consolidation": true,
    "min_refresh_interval_seconds": 1800,
    "tags_match": "all_strict"
  }
}
```

The two tags above are filters, not display labels. Do not add `type:*`,
`derived:*` or other descriptive tags unless the source memories carry the same
tag, because the default strict matching would otherwise make the page empty.
Including all three documentary fact types prevents the page from silently
ignoring source facts that have not become consolidated observations. Excluding
mental models prevents one derived page from becoming evidence for another.

Automatic refresh is freshness maintenance, not approval. The page remains a
candidate orientation aid and never becomes Evidence or a professional source.
Before producing a consequential mail, report, contractual position or cost
conclusion, Hermes reopens the cited source documents and reports missing or
contradictory material.

Hindsight's staleness check detects newer in-scope memories but not deletion by
itself. A successful Workspace deletion or project-scope move must therefore
queue an explicit refresh of the affected page after source reconciliation.
Until that hook is qualified, deletion leaves the page `ready_with_limits` and
requires a manual refresh. Use the dry-run refresh endpoint during qualification
and reject a refresh that retrieved no source facts for a non-empty project.

## Information that is not a tag

Do not create unbounded tags for dates, extracted people, every document
reference or free-form facts. Use:

- metadata for source path, checksum, ingestion provenance and filename hints;
- entity schemas for normalized document types, actors and relation types;
- memories for extracted facts and dates;
- explicit document relations for `cites`, `responds_to`, `supersedes`,
  `supplements` or `attachment_of` when evidence exists.

This keeps the tag set small enough for reliable Hermes filtering.
