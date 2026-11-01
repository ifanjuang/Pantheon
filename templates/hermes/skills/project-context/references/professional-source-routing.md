# Professional source routing

Use this reference for a material factual, technical, contractual, regulatory
or professional answer.

## Resolve before inspecting

When a task already identifies an accessible exact source in the admitted project,
read it through `vault-read` without repeating discovery. Otherwise, if the
project identity is ambiguous, resolve it first through
`vault-read:find_vault_projects`; the scoped project recall requires a confirmed
project identity. For a confirmed project, use the configured
`hindsight-vault:recall_project_memory` as the first project memory lead, then
`vault-read` to resolve and inspect candidates. For general references, use
`hindsight-vault:recall_knowledge_memory`; consult its folder listing only to
narrow an unsuccessful or explicitly folder-scoped search. Mnemosyne may provide
conversation continuity, but never proves presence, absence or dossier facts.

If recall supplies a matching document identifier, vault path or filename,
open the candidate next after verifying its project scope. Do not repeat
discovery or list a whole dossier first.
When the identity is materially ambiguous, retain the candidate set and ask one
targeted question rather than silently selecting a project.

For a named source or bounded request, do not call a full source inventory unless
the exact source cannot be resolved or completeness across candidates matters.

For a known source whose Hindsight entry is missing, treat this as an indexing
gap: open it through the admitted local route rather than declaring it absent.
An attachment must resolve to a Docling-visible shared location before document
extraction; otherwise report `source_not_visible_to_docling` and ask for an
admitted source location.

## Sufficiency and representation

For a simple lookup, a sufficiently complete Hindsight/Mnemosyne memory or
conversation context may answer even when the user requests an exact fact, list
or count, provided the relevant content, source identity and requested locator
are already available and the user has not asked to verify the source. Label it
`de mémoire`, identify the source using its returned or previously established
title/name and locator (the filesystem filename is not required), and say that
the document was not reopened. Do not infer completeness or a total from partial
memory. Offer direct verification as an optional next step.

For a professional, technical, contractual, regulatory or compliance opinion,
consult the relevant admitted Knowledge/library reference automatically; do not
ask the user whether to search first. Inspect the exact underlying document when
the recalled item is truncated, ambiguous, incomplete, edition-sensitive, or
when the conclusion depends on its exact criteria, wording, completeness or
applicability. A complete, sufficiently specific Knowledge entry can guide the
comparison without reopening its original only when the task does not depend on
those exact-source properties; attribute the guidance to the returned Knowledge
item, never to an uninspected original. Project-specific facts still require
inspection of the exact project source when material to the conclusion.

If the user asks to verify or quote the original, confirm its edition or
completeness, or rely on current authoritative wording/applicability, inspect
the exact underlying or authoritative source. If the Knowledge entry is
ambiguous, incomplete or possibly stale, retrieve only the missing evidence and
state the limitation. A project fact or clause requires inspection of the exact
project source when it materially supports a professional conclusion. This
does not apply to a simple lookup that is not being used to support such a
conclusion.

Keep retrieval bounded: make one focused recall per needed source family, then
stop when the returned item supports the requested comparison. Make at most one
targeted follow-up for a named missing criterion. Do not repeat near-identical
queries or search alternate phrasings without stating what material information
is still missing; follow any stricter configured recall budget.

If the first Knowledge recall does not identify the reference or leaves a
material criterion unsupported, one different bounded recovery is allowed:
inspect the indexed Knowledge folder list once, then make one focused recall
using the exact relevant folder or a materially different title/acronym. Do not
keep broadening queries indefinitely. A memory preview or folder listing is a
locator, not proof of exact document wording, complete library coverage, or
absence. Report only what the returned scope supports.

Use the least costly admitted representation that can answer the question:
native text or structured data first; a bounded extraction, visual inspection
or transcription only for information not otherwise available. Existing usable
Hindsight content and any applicable representation state block redundant
derivation. A missing or unusable representation is a limitation, not
permission to invent another parser, tool or provider.

## Architectural source formats: IFC, DWG, PDF, JPG

When a project question spans native geometry, drawings and site photographs,
first resolve the same admitted project and exact source versions. Treat
Hindsight as a documentary lead only: the current Workspace source inventory
does not admit IFC/DWG/JPG for Hindsight extraction, and this core-first
change does not activate readers or expand the inventory.

Choose an actually qualified, available **read-only** reader for the source,
not a parser merely inferred from the file extension:

- **IFC:** query the admitted IFC reader (IFClite is a candidate, not proof
  of a live installation). Preserve GlobalId, element placement, representation
  coverage, units, linked-model scope and the snapshot digest.
- **DWG/DXF:** require an admitted CAD reader that reports handles, blocks,
  layers, model/paper space, insertion transformations, XREFs and unit/calibration
  state. This repository has **no qualified DWG reader binding**. If absent,
  report `source_present_not_inspected`, not invented geometry, quantities,
  objects or an implicitly extracted Hindsight memory.
- **PDF:** textual extraction (Docling or the bounded native PDF reader) does
  not inspect the graphics of a plan. For geometry or visual symbols, inspect
  the exact page/region through an admitted visual or takeoff capability;
  preserve the scale witnesses and withhold measurements if unresolved.
- **JPG/JPEG/PNG:** inspect only the exact image/region with an admitted visual
  reader, preserving occlusions and observation time. No native metric dimension,
  as-built completion, work reception or stable-object identity may be inferred
  solely from an uncalibrated photograph.

Normalize useful inspected results to the **existing** APU Observation Bundle
Candidate contract when a structured project claim is requested. A source
representation may remain unlinked to any stable object. A photo, IFC GUID, DWG
handle and PDF label sharing a subject are not automatically the same governed
object. Preserve differing source revisions, measurements and physical/design
states separately; do not rank a universal winner by recency, memory recall
frequency or agreement between formats.

If the reader is unavailable or only metadata is discoverable, answer with
known source presence and the specific inspection gap; do not treat that as a
failure of project identification. Use APU projections, WorkIssues and Decisions
only through their existing admitted boundaries. Inspection, Hindsight retain,
APU application and authorized consequential effects are separate operations.

## Source families and preflight

```text
dossier/client/address/budget/date/status/planning -> AFFAIRES
technical/standard/regulatory/legal/method question -> DOCUMENTAIRES
dossier fact tested against a transversal rule -> AFFAIRES + DOCUMENTAIRES
```

Keep the vault roles distinct in the return:

- `knowledge` supports transversal concepts, methods, standards and references.
  Cite the returned document title/name and its available provenance (such as
  collection/folder, publisher or source context, and version/date when
  returned). A filename is optional. A memory-only answer must say `de mémoire`
  and must not imply the source file was opened.
- `projects` supports facts and records about a specific dossier. Cite the
  document title, provenance, revision/index and date when available, plus a
  clickable link to the exact project file when the admitted interface provides
  one. Do not fabricate a link or turn a raw path into an unsupported URI; if
  the reader exposes no clickable link, give its exact source locator and say
  that no clickable link was returned.

For a project fact tested against a transversal reference, report both sources
separately. Record the actual binding, exact reference, locator and limitation
for every material source family. A search result, filename or memory lead
without source inspection leaves the preflight incomplete when the claim
requires document inspection. Use the source-preflight receipt shape when the
task needs a material professional conclusion.

Always disclose the evidence mode without waiting to be asked: say `de mémoire`
when the answer relies on recall and the source was not reopened; say `vérifié
dans [source, locator]` when directly inspected. For partial reading, qualify
the statement as verified only in the passages actually read. In mixed answers,
label recalled context and verified findings separately. Keep this disclosure
concise; it is a provenance label, not a request for permission to answer.

Before returning a material budget, status, obligation or recommendation,
surface missing support, freshness, contradiction and capability limits. Use
`source-research` only after local sources have no sufficient support or an
authoritative current external source is needed; minimize project detail before
any external query.

## Mixed project and reference claims

For a question that tests a project condition against a general rule, keep the
two claim families separate through retrieval, inspection and the final answer:

| Claim | Source family | What it can establish |
|---|---|---|
| What is specified, observed, decided or recorded for this project | `projects` | The project record, with title, provenance, revision/date and clickable file link when exposed; not facts beyond the inspected scope |
| What an admitted Knowledge entry represents | `knowledge` | The returned summary/criteria and available provenance, cited by source title/name; not exact wording of an uninspected original |
| What a law, regulation, standard or current authoritative reference says | `knowledge` or the current official source | The inspected text, edition/date, scope and conditions; not project compliance by itself |
| Whether the project condition satisfies the applicable rule | Both, plus applicability facts | A bounded comparison candidate; not professional approval or certification |

Do not treat project memory as the project source: use recall to locate the
record, then inspect the exact project document for a material project fact.
A Knowledge entry can be used as the comparison basis when the requested
question is about that stored guidance; it does not establish exact wording,
edition, completeness or current applicability of its underlying source. For
those claims, inspect the exact passage in the original or current authoritative
reference.

When two inspected sources appear inconsistent, compare the same claim and
conditions before calling it a contradiction. Check that they concern the same
object, location, material, phase, date, revision, units and scope. Classify the
result as one of:

```text
apparent_difference       # different scope, condition, unit or time
project_reference_gap     # project value is known; applicable rule is not established
reference_project_gap     # rule is known; project fact or applicability is missing
stale_or_superseded       # one source may no longer describe the applicable state
direct_conflict           # same claim and conditions, incompatible statements
```

Never resolve a `direct_conflict` by retrieval rank, recency alone, source count,
or a blanket rule that one source family always wins. Project records establish
what was specified or decided; they do not override applicable law or establish
technical compliance. A standard or general reference does not rewrite the
project record, and a standard's applicability may depend on law, contract,
edition, date and project conditions. Use the relevant source hierarchy only
after identifying the actual question and applicable instruments. If that
cannot be established from inspected sources, preserve both readings and mark
the conclusion `to_verify` or `to_arbitrate`.

For a material mixed-source answer, use a compact comparison with these fields:

```text
project statement | exact source + locator + status
reference statement | exact source + edition/date + locator
applicability | matched conditions and missing conditions
relationship | one of the classifications above
result | what is supported, what remains unresolved, and the next verification
```

Do not merge a project value and a general rule into one unqualified number or
sentence. If the difference affects safety, legal compliance, contract,
responsibility or an external instruction, stop at the unresolved gate and
identify the competent reviewer or exact source needed. Keep the non-selected
source visible; arbitration changes the next status, not the historical record.

For a consequential decision, external action, protected mutation, durable
retention or professional conclusion, obtain the selected Pantheon routing
before the effect. It proposes a path and readiness; it neither opens the
source nor creates authorization. A requested artifact destination must be
explicitly selected before writing; do not create parallel copies silently.

```text
mentioned != exact source present != relevant content inspected
Hindsight recall != document inspected
local access != external disclosure authorization
known path != source absent
indexing gap != permission to invent content
retrieval route != authorization
available destination != selected destination
```
