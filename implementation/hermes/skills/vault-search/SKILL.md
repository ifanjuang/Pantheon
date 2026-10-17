---
name: vault-search
description: "Recherche les projets et documents dans les vaults agency."
license: MIT
metadata:
  version: 0.9.0
  author: Agency
  hermes:
    tags: [agency, hindsight, vaults, projects, documents]
    category: productivity
    depends_on: [project-context]
    related_skills: [project-context]
---

# Agency vault search

Organization adapter for the generic `project-context` method. Apply that
skill's project-resolution, document-inspection and Pantheon boundaries first.
This adapter supplies current agency bindings and search tactics; it creates no
project identity, truth, Evidence, approval, governed memory or authorization.

Read [references/organization-profile.yaml](references/organization-profile.yaml)
before choosing a source or tool. Treat it as volatile deployment configuration,
not Pantheon doctrine.

## When to Use

- General or transversal question: search the relevant professional source
  without selecting a project.
- Multi-project question: keep all requested projects in scope and preserve
  their identities separately.
- Situated question with a known project: retain the conversation-local project
  and search only its bounded source scope.
- Situated question with an informal designation: build a bounded candidate set
  from a first name, client, official name, street, commune, code, description
  or distinctive subject.

Ask one targeted question only when choosing between candidates would materially
change the answer, permitted action or consequence.

## Search order

0. When an exact source is already known **within an admitted project scope**,
   inspect it directly through the reviewed reader; no new Hindsight discovery
   is needed. Otherwise, for a named project, dossier or operation, call
   `hindsight-project:recall_project_memory` as the first discovery lead.
   This is the only admitted Hindsight project route; do not substitute Mnemosyne.
1. When identity or source is unresolved, use `vault-read`:
   `find_vault_projects` on the designation, then
   `list_vault_project_sources` on the selected project. Retain ambiguous
   candidates and ask one targeted question only if selection changes the answer.
2. Open an exact Markdown source with `search_vault_markdown` followed by
   `read_vault_markdown_lines`; use Docling for a source file requiring document
   extraction. A router recall is an index lead, not an inspected source.
3. Use Mnemosyne only as a bounded continuity lead after the project-router
   lookup, never as proof that a professional project is absent or present.

### Source coverage and inventory fallback

Apply this same route to every professional document type and representation:
PDF, native office file, Markdown, image, plan, audio, correspondence, form or
attachment. A failed Hindsight lookup is never a reason to ask the user to
search project-platform manually.

When the router does not identify the requested exact source, automatically use
the selected project's `list_vault_project_sources` inventory before declaring a
document absent. Use a focused topic for a normal request. For an explicit
request to list, count or compare all matching documents, request the largest
bounded inventory allowed by the binding. A filename/path match is a candidate
only; it does not establish the document's content or type.

For every material document lookup, return a short coverage receipt before the
conclusion when it changes the result:

```text
Hindsight: matched | no_match | binding_unavailable
NAS source: exact_source_present | candidates_found | inventory_truncated | no_supported_source
Inspection: not_needed | exact_source_opened | partially_read | not_readable
```

State the returned and scanned logical-document counts when the inventory
provides them. `truncated=true` or `scan_complete=false` means the inventory
cannot support an exhaustive absence claim. Do not say "there are only N
documents" unless the inventory is complete; say instead "N documents returned
from the bounded inventory". Do not say a document is absent merely because its
filename did not match the topic.

When an exact source is present on the NAS but absent from Hindsight, label it
`source_present_not_indexed`, open it through the admitted reader or document
binding if needed, and include it in the coverage receipt. This is an indexing
gap, not a user error and not permission to invent its content.

### Session attachments and proposed filing

A document dropped into the chat is session input by default. First identify
what can be supported from the supplied file and keep its status distinct:

```text
attachment_session_only != NAS source
proposed classification != performed filing
Hindsight enrichment != source-file move
```

When useful, propose a project, document family, date/revision candidates and
destination with the supporting indicators and uncertainty. Offer the smallest
materially different choices: keep it only in the session; enrich an admitted
index; or file/reclassify it in the selected workspace. Never copy, move,
rename or classify a NAS source until the user selects a destination and an
admitted write capability authorizes that effect. If no such capability is
active, return a filing proposal rather than implying the file was reclassified.

### Latest document / revision resolution

When the user asks for the latest, current, newest or applicable revision of a
document family, do not use Hindsight relevance rank, retain time, filesystem
mtime, upload time or a cartouche date/index as proof of currentness.

Resolve at most five exact-family candidates. Preserve any validated Workspace
revision projection carried by the candidate:

```text
revision_mode = supersedes | supplements
revision_of   = document_id
```

A structurally resolved explicit `supersedes` relation is a declared lineage edge,
not proof that the declaration is professionally correct. A `supplements` relation
is not replacement and must not suppress the referenced document. Never manufacture
either relation from index/date/name similarity.

Then inspect each candidate through the admitted vault reader or Docling so the
source text is available. Extract from the document content itself, when
explicitly stated:

```text
source_revision
source_document_date
source_revision_history[]
source_supersedes[]
```

Treat these as source observations, not metadata truth. Do not invent a revision
or date when the source text does not state one.

Selection order for one exact document family:

```text
structurally resolved explicit Workspace supersedes relation
> explicit supersedes/replaces statement in the source
> explicit coherent revision history/table in the source
> heuristic ordering by comparable source revision/index
> source document date as heuristic tie-breaker/fallback
```

Rules:

- A structurally resolved Workspace `supersedes` graph is a declared routing
  lineage, not source truth. If it has one unambiguous head and the inspected
  source chronology does not contradict it, use that head as the current
  retrieval candidate. If it has multiple heads, cycles, unresolved targets, or
  conflicts with explicit source supersession/revision-history evidence, return
  the conflict instead of choosing silently.
- If one source explicitly says it supersedes/replaces another candidate, prefer
  the superseding source for this retrieval, but do not automatically write a
  cartouche revision relation from that observation.
- If a source contains an explicit revision history/table, use it to validate the
  current revision token and chronology. A coherent revision history is stronger
  evidence than an isolated date field.
- Comparable isolated revisions (for example A/B/C, 01/02/03, P1/P2/P3,
  REV01/REV02) may order candidates for retrieval convenience, but they do not by
  themselves establish professional currentness or create a revision relation.
- The source document date is a consistency check, not an automatic override.
- If the higher isolated revision carries an earlier source date than the lower
  revision, keep it first only as the index-ranked candidate and emit
  `revision_date_conflict`; keep the other candidate visible.
- If two candidates have the same revision/index, the later explicit source date
  may order them for retrieval, but emit `duplicate_revision`. If their dates
  are also equal or missing, do not silently collapse them.
- If revisions are missing or not safely comparable, an explicit source date may
  order candidates only as `date_fallback`. Do not derive chronology from
  filename ordering or filesystem timestamps.
- If no explicit lineage/source chronology resolves the candidates, return the
  ordered candidate set and state that currentness is unresolved. The first item
  is a retrieval preference, not a professional-currentness assertion.

A "latest" answer should expose the basis used:

```text
selection_basis =
  workspace_supersedes
  | source_supersession
  | source_revision_history
  | heuristic_revision_order
  | date_fallback
  | ambiguous

revision_conflict =
  none
  | duplicate_revision
  | revision_date_conflict
  | incomparable_revision
  | branching_lineage
  | invalid_lineage
  | declared_source_conflict
```

The cartouche may help locate the family and may carry an explicit declared
revision relation, but its descriptive `index` and `document_date` cannot
silently establish currentness.


   If the project router returns no exact candidate but an admitted Workspace/vault path
   or filename is already known, treat this as an indexing gap: validate and
   open that exact local source (Docling for a file needing extraction) rather
   than asking for an upload or declaring the document absent. Distinguish
   `binding_unavailable`, `no_match` and `indexing_gap` in the limitation.
   For an exact Markdown path, use `search_vault_markdown` only to locate lines,
   then `read_vault_markdown_lines` for the bounded passage being cited. Supply
   `project_ref` for the projects vault; never supply one project's path with another
   project's reference. For the knowledge vault leave `project_ref` empty and keep
   the general reference separate from project facts. A search preview,
   Hindsight excerpt or internal `spillover` cache is not an inspected passage.
   Markdown extracted from a PDF is a derivative; use Docling on the original
   PDF when page, graphic, signature or source-original verification matters.

### Figures from a source

Open a figure when the passage read refers to one (« figure 28 », « voir
schéma ») or a caption on that page names the subject; search for figures
elsewhere only when the user asks to see one. Then call `read_vault_pdf_figures` on the exact original PDF, with
its path as recall or the inventory cites it, and the page or a few words of the
passage or caption. It returns each crop with
its page and caption as an image you can see.

Before showing a figure, compare it with the question. Show at most two, each
with the document, page and caption; when unsure it matches, show it and say
why; drop one clearly unrelated, and never show an uncaptioned crop as if it
were named. When nothing matches, say no figure was found; never describe or draw a
figure in its place. A figure is a reading aid, not Evidence, and its values are
cited only when its caption or the page text states them.
For a recent project or information possibly awaiting synchronization, use one
distinct Mnemosyne recall only when a freshness concern is observed and it can
change the result. Attribute memory-only information to recent conversation and
mark it unconfirmed until an admitted business source supports it.

For a material professional factual answer, the applicable source lookup is
mandatory before final synthesis: `projects` for dossier facts,
`knowledge` for transversal professional facts, and both for a mixed
question. A memory lead never satisfies this requirement. If the required
binding is unavailable, return the limitation rather than substituting model
recall.

Never report that Hindsight is unavailable solely because a recall or search
returned no match. Availability is established by the active MCP catalogue and
connectivity test; an empty result is a search outcome and may indicate an
indexing gap or an overly narrow query.

Never report a project absent solely from an empty Hindsight result. Distinguish
`no_name_match_in_mirror`, `source_present_not_indexed`,
`project_present_source_not_found`, `source_inventory_truncated`,
`source_present_but_not_readable`, and `source_inspected_requested_fact_not_found`
within the scope actually checked. Do not silently substitute another project
or infer that a missing permit file means no permit work has occurred.

Do not turn a generic remembered checklist into a regulatory conclusion. Each
technical, legal, contractual or standards requirement must be tied to an exact
document or section returned by the admitted source path, or be labelled
`à vérifier` with the missing reference stated.

```text
subject match != selected project
recall snippet != exact document
conversation memory != business source
fast memory lead != confirmed answer
document opened != Evidence admitted
```

## Source routing

- Use the `projects` vault for project records, clients, contracts, correspondence,
  permits, plans, schedules and administrative material.
- Use the `knowledge` vault for transversal technical, regulatory, legal, contractual
  and professional references. Its Hindsight lead is
  `hindsight-knowledge:recall_knowledge_memory`; open the cited document with
  `vault-read` before relying on it.
- Use both when a project-specific fact must be tested against a transversal
  rule. Keep their contributions distinguishable.
- For a mixed-source conclusion, treat project recall and standards recall as
  discovery leads, then inspect the exact project source and the exact
  applicable reference. Compare claim, scope, date/revision, units and
  applicability; classify an apparent difference, missing applicability fact,
  stale source or direct conflict. Never let retrieval rank or a blanket
  project-vs-standard precedence rule erase the other source. If the actual
  legal/contractual hierarchy is not established, report `to_verify` or
  `to_arbitrate` with both source locators and the next check.
- For a mixed document/compliance question, open the exact projects-vault source
  first, then consult only the admitted transversal source needed for the rule
  family. If none is available, label the item `à vérifier`.
- Use the live source only when the user requests current state or indicates a
  change may not yet be indexed. Do not silently merge live and indexed state.

## Documents and plans

Apply the generic document-inspection reference. A Markdown derivative or recall
mention does not prove that a PDF exists or that its relevant visual content was
inspected. Use the configured document-analysis binding only for the exact
sources and pages needed. Preserve source identity and locator.

### Docling tool routing

For a passage of a PDF, call `vault-read:read_vault_pdf_pages` first, with the
path as recall cites it and the page or a few words of the passage: it reads the
PDF's own text in a second, and returns a scanned page as an image. Convert with
Docling only when that text is missing or a table's structure is needed.

When the requested answer depends on the content of a PDF, DOCX, PPTX, XLSX or
image, use the configured Docling MCP binding through this bounded sequence:

```text
exact source path or URL
-> is_document_in_local_cache(document_key) when a document_key is already known
-> convert_document_into_docling_document(source) when conversion is needed
-> get_overview_of_document_anchors(document_key)
-> search_for_text_in_document_anchors(...) when a term or section is targeted
-> get_text_of_document_item_at_anchor(...) for the smallest relevant extract
```

For Hermes MCP calls, the conversion argument is exactly `source`:

```json
{"source": "<knowledge-root>/<document>.pdf"}
```

Do not call `get_prompt`, `list_prompts`, `read_resource` or `list_resources` as
a substitute for document conversion or content inspection. Those are MCP
introspection/resource operations and do not open an arbitrary local PDF. Do
not invent `filepath` or `file_path` for the Hermes conversion wrapper; if the
selected binding exposes a different schema, inspect that schema before calling
it rather than guessing.

The same rule applies to Hindsight resource/introspection calls: use
`get_document` for an identified document and `get_knowledge_page` for an
identified knowledge page. A `read_resource` result is not a document
consultation and must not be cited as one.

The `source` path is resolved by the Docling service, not by the model. Use the
operator-configured NAS root shared with that service or another reviewed
shared mount. A WebUI upload path under `/home/hermeswebui/.hermes/webui/attachments`
is not assumed to be visible there. If no shared path or URL exists, report a
Capability Gap and request a supported source location; do not retry the same
conversion with guessed paths.

Opening `http://127.0.0.1:8020/mcp` in a browser is not a document test. It is a
machine-to-machine MCP endpoint and requires an MCP request body. Validate the
binding with Hermes MCP diagnostics, then invoke the document tool with its
required arguments.

### Workspace files

An attached file shown by Hermes WebUI is a candidate input, not automatically
a Docling-visible path. Before conversion, resolve the attachment to one of
 these forms:

```text
shared Workspace/vault path visible to Docling
or
supported URL reachable by Docling
```

The current local deployment shares the `/srv/pantheon/obsidian*` roots with
Docling. A virtual UI label such as `/workspace`, or an attachment path under
`/home/hermeswebui/.hermes/webui/attachments`, must not be guessed or passed to
Docling unless the deployment explicitly mounts it there. If the attachment is
not shared, report `source_not_visible_to_docling` and ask for a Workspace/vault
path or an explicit upload-to-shared-workspace step. Do not silently copy a
private attachment into a professional vault, and do not retry with another
invented path.

## Limits and return

- At most two recall calls across all bindings for one question.
- For a single professional lookup, use at most one project-router recall, one
  bounded project inventory and one Mnemosyne continuity recall. Repeating an
  identical query is not a search strategy.
- Open at most five candidate documents unless the user requests an exhaustive
  inventory.
- Stop widening retrieval when remaining unknowns cannot change the permitted
  conclusion.
- Cite the exact path or document ID for each material project fact.
- Expose contradictions, freshness limits and missing source confirmation.
- For every proposed omission or compliance gap, cite the exact project-document
  locator and the exact knowledge-vault reference when available. Otherwise label
  it `à vérifier` and state which reference is missing.
- End a material review with two to four optional, bounded follow-up paths when
  useful (for example: inspect a specific lot, verify a named standard, compare
  a revision or prepare a checklist). Label these as proposals; do not execute
  them or imply that they are required unless the user chooses one.
- Do not return unrelated personal contact data.
- Consult Pantheon only at the consequential boundaries defined by the generic
  skill; do not call it mechanically for ordinary lookup.
