# Professional source routing

Use this reference for a material factual, technical, contractual, regulatory
or professional answer.

## Resolve before inspecting

When a task already identifies an accessible exact source in the admitted project,
read it through `vault-read` without repeating discovery. Otherwise use
`hindsight-project:recall_project_memory` as the first project lead,
then `vault-read` to resolve and inspect candidates. Mnemosyne may provide
continuity after the router; it never proves presence, absence or dossier facts.

If recall supplies a matching document identifier, vault path or filename,
open the candidate next after verifying its project scope. Do not repeat
discovery or list a whole dossier first.
When the identity is materially ambiguous, retain the candidate set and ask one
targeted question rather than silently selecting a project.

For a known source whose Hindsight entry is missing, treat this as an indexing
gap: open it through the admitted local route rather than declaring it absent.
An attachment must resolve to a Docling-visible shared location before document
extraction; otherwise report `source_not_visible_to_docling` and ask for an
admitted source location.

## Sufficiency and representation

An orientation answer may rely on a clearly labelled memory lead when no exact
fact, current status, calculation, recommendation, rule or action is asked.
Otherwise inspect the exact source and retain an exact locator.

Use the least costly admitted representation that can answer the question:
native text or structured data first; a bounded extraction, visual inspection
or transcription only for information not otherwise available. Existing usable
Hindsight content and any applicable representation state block redundant
derivation. A missing or unusable representation is a limitation, not
permission to invent another parser, tool or provider.

## Architectural source formats: IFC, DWG, PDF, JPG

When a project question spans native geometry, drawings and site photographs,
first resolve the same admitted project and exact source versions. Treat
Hindsight as a documentary lead only: the Workspace may inventory IFC/DWG/JPG
files without retaining their binary or visual contents in Hindsight.

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

Keep the project source and external rule distinct in the return. Record the
actual binding, exact reference, locator and limitation for every material
source family. A search result, filename or memory lead without source
inspection leaves the preflight incomplete. Use the source-preflight receipt
shape when the task needs a material professional conclusion.

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
| What is specified, observed, decided or recorded for this project | `projects` | The project record, within its date, revision, issuer and validation status |
| What a law, regulation, standard or professional reference says | `knowledge` or the current official source | The cited text, edition/date, scope and conditions; not project compliance by itself |
| Whether the project condition satisfies the applicable rule | Both, plus applicability facts | A bounded comparison candidate; not professional approval or certification |

Do not treat project memory as the project source: use recall to locate the
record, then inspect the exact project document for a material project fact.
Likewise, a standards recall locates a reference but does not establish its
wording, edition or applicability; inspect the exact passage.

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
