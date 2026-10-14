# Pantheon Next — Document OCR Derivation Pipeline

Status: candidate support doctrine — provider-agnostic derivation boundary / documented non-implemented.
Boundary profile: candidate_support_note.

This document owns the governed placement of OCR and document derivations. It does not make Pantheon an OCR runtime, scheduler, queue, provider router, document store, plugin manager or automatic approval system.

It complements `DOCUMENT_LIFECYCLE_GOVERNANCE.md` and the existing Source/document contracts. It does not replace Source, Projection, Trace, Knowledge, Evidence, Claim, ChangeCandidate or Capability Slot models.

## 1. Decision

OCR is an independent capability.

```text
document_source_management
!= document_ocr
!= document_structural_analysis
!= document_classification
!= document_validation
```

A source-management product may expose native OCR, but product bundling does not transfer capability ownership or governance authority.

An admitted OCR or classification task may be orchestrated by Hermes and executed by the selected external runtime or bounded native binding. Native execution does not bypass the Task Contract, provenance requirements or applicable gates.

```text
provider selected != dependency adopted
native execution != task authorized
runtime success != Evidence
```

## 2. Capability slots

### `document_ocr`

```yaml
capability_id: document_ocr
function: produce searchable text and/or an archival searchable representation from an exact captured source version
owner_layer: external runtime
orchestrated_by: Hermes when governed orchestration is required
executed_by: selected external runtime or bounded native binding
exposed_by: Pantheon Cockpit as status, warnings and reviewable derivations
governed_by: Pantheon Next
approved_by: human where remote transmission, activation, consequential replacement or real-dossier use requires approval
```

Candidate bindings may include Tesseract, PaddleOCR, remote document-intelligence services or specialized local VLMs. This is comparative candidate data only.

Adjacent responsibilities remain distinct:

```text
document_source_management = capture/preserve/version/retrieve exact sources
document_structural_analysis = layout-aware blocks/tables/headings/Markdown
document_classification = propose metadata and project/phase links
document_validation = check completeness, consistency and mismatch signals
```

## 3. Canonical derivation chain

```text
exact Source Capture version
├── searchable PDF or PDF/A derivative
├── plain-text derivative
├── layout-aware structural derivative
├── table/equation/image derivative
├── thumbnail or preview derivative
└── index or embedding projection
```

Required invariants:

- the original exact source version remains immutable and superior to every derivative;
- no OCR result silently replaces the original source;
- every derivative points to one exact source version;
- every derivative records producing binding, version, parameters, execution identity, digest and time;
- reprocessing creates a new derivative revision rather than rewriting history;
- deleting an index/projection does not delete the source;
- extraction success does not establish correctness, Evidence or professional validation;
- a provider/runtime identifier is a backing reference, not Pantheon authority.

A candidate derivation therefore needs at least:

```yaml
document_derivation:
  derivation_id:
  source_id:
  source_version_id:
  derivation_kind:
  mime_type:
  produced_by:
    capability_slot: document_ocr
    binding_id:
    binding_version:
    execution_id:
    parameters_profile:
  produced_at:
  digest:
  quality_observations:
    warnings: []
    mismatch_count: 0
    confidence_summary: unknown
  status: candidate
  supersedes_derivation_id:
```

## 4. Validation and silent-failure posture

Extraction success is insufficient. Validation must be able to surface missing pages/regions, changed numbers or units, corrupted tables, altered equations, incorrect reading order, low-confidence/empty sections and double-OCR degradation.

```text
no_warning != verified_correct
confidence_score != truth
visual_match_signal != Evidence
```

Consequential sources may require blocking or human review when mismatch observations exceed the applicable policy threshold.

## 5. Routing profiles

Candidate profiles:

```text
LOCAL_STANDARD
  ordinary readable documents; local binding; no external transmission

LOCAL_ADVANCED
  difficult scans/plans/layouts; specialized local OCR/VLM; explicit resource/confidentiality scope

REMOTE_EXCEPTION
  external provider; explicit provider/document/retention scope; gate before transmission when required
```

Pantheon must not become the provider router. Hermes or another external execution layer may resolve an authorized binding within the admitted Task Contract.

## 6. Source-management provider boundary

A source-management provider is optional. When one is selected, it may preserve versions, expose search or run native OCR, but those facilities remain subordinate to the same source/provenance and policy rules.

```text
provider OCR text != source truth
provider metadata != governed classification
provider search hit != Evidence
provider task success != professional validation
provider absent != document ingestion unavailable
```

The current selected architecture therefore requires no DMS product. Bounded local/NAS sources remain a valid source path, and Obsidian remains a human Markdown workspace rather than a professional source authority.

## 7. Classification and mutation path

Classification produces a candidate, not an immediate authoritative write.

```text
Classification Candidate
-> validation observations
-> ChangeCandidate with base revision and provenance
-> human review where required
-> authorized mutation
-> runtime observation
-> updated Cockpit projection
```

A successful API write is not approval and does not promote the result to Knowledge or Evidence.

## 8. Runtime boundary

Batching, model residency, GPU utilization, retries, queues and concurrency belong to Hermes or the selected external inference runtime.

Pantheon may observe only task states needed for decision and traceability, for example `requested`, `admitted`, `running`, `candidate_output_available`, `review_required`, `failed` and `cancelled`.

Pantheon does not schedule OCR jobs, maintain a GPU queue, select providers automatically or infer authorization from runtime throughput.

## 9. Cockpit projection

The Cockpit may project source availability, preferred derivative, OCR state, binding family when useful, warnings, mismatch status, classification-candidate state, review reason and links to original/derivative.

```text
projection != persistence
UI status != authorization
```

The UI must not dictate the backend model or expose provider queues and OCR internals by default.

## 10. Current executable seam

The co-located candidate implementation under `implementation/` already demonstrates a bounded Docling/structured-extraction path with exact source linkage, revisioned compilation, ordered extraction units, diagnostics and retrieval chunks.

That existing slice is not a universal OCR/derivative authority. Extension requires demonstrated need and must reuse its deterministic compilation responsibility rather than creating a second cleaner/pipeline.

## 11. Optional Obsidian conversion and selected AFFAIRES ingestion posture

The direct NAS-mounted AFFAIRES route selected by Pantheon-Next#660 supersedes the earlier productive Markdown-only Hindsight producer path. Obsidian remains optional human-facing tooling; it is no longer the materialization or ingestion owner for professional AFFAIRES.

Current split after Pantheon-Next#1131/#660:

```text
exact PDF / office source = preserved professional source on NAS / AFFAIRES
Hindsight native file retain = selected for eligible AFFAIRES sources through the bounded Workspace producer
automatic OCR = disabled on the productive AFFAIRES route
OCR-AI / L3-N0X/obsidian-marker = selected optional/manual workspace PDF-to-Markdown convenience surface
Docling = preferred document_structural_analysis candidate under Pantheon-Next#662
SourceDown = historical prior workspace choice, not the current selected daily conversion surface
```

The 2026-09-06 Obsidian/Marker operator choice remains historical provenance for optional Markdown authoring. It no longer decides Hindsight ingestion for AFFAIRES.

```text
Marker workspace selection != structural-analysis qualification
Marker conversion success != professionally validated
Marker Markdown != original source
Markdown present != source replacement
no Markdown derivative != source unavailable
native file retain selected != source authority
one productive AFFAIRES producer != one source format
```

The ordinary productive Hindsight path is now:

```text
NAS / AFFAIRES source
-> exact Workspace source/cartouche pairing
-> one bounded Workspace Hindsight producer
-> Hindsight files/retain for an eligible source representation
-> parsed source content
-> Hindsight derived chunks / memories
```

For scanned PDFs or images that need OCR:

```text
source remains visible in Cockpit
-> OCR needed / unavailable state
-> explicit user/Pantheon action
-> derived OCR result
```

Do not run NAS-wide OCR automatically. Do not create a second concurrent producer for the same AFFAIRES source merely because an optional Obsidian/Marker derivative exists. The selected single-producer invariant is about ownership of synchronization, not about forcing every source through Markdown.

The earlier SourceDown and Obsidian/LiveSync/Hindsight qualification logs remain historical provenance and are not rewritten to pretend those earlier operator choices never existed.

## 12. Workspace metadata and human notes

The Workspace/Cockpit may observe or derive document metadata without serializing every field into Markdown.

Keep three classes distinct:

```text
reconstructible observation
= filename, MIME, digest, filesystem timestamps, parser-derived structure, detected index/date/type candidates

human-authored workspace material
= notes, comments, corrections, intentionally authored summaries or Markdown knowledge

derived cache/projection
= generated summary, essentials, extracted index/date candidates, optional Markdown representation
```

For index/date/reference extraction, preserve what was actually observed and where it was observed before any professional admission:

```yaml
extracted:
  issuer_reference_candidates:
    - value: A-203
      source_locator: title_block
  index_candidates:
    - value: D
      source_locator: title_block
  date_candidates:
    - value: 2026-08-28
      label_observed: Date
      role_candidate: issue_date
      source_locator: title_block
```

```text
detected index != admitted Document version
highest-looking index != purpose-specific currentness
date printed in document != receipt date
date printed in document != effective date
human note != extracted fact
derived summary != Evidence
```

No new production `document.yaml` or workspace-metadata schema is adopted by this posture. Reuse the existing Workspace Manifest Inspector candidate, Professional Document owners and `document_knowledge_slice` structure contract. Persist only non-reconstructible human material or explicitly useful derived cache when justified; routing remains calculated where existing owners can calculate it.

A derived summary may retain its exact source basis, for example:

```yaml
derived_summary:
  text: Plan architectural du RDC...
  based_on_digest: <exact source digest>
  generation_status: generated_unreviewed
```

When the exact source digest changes, the old summary is stale rather than silently current.

## 13. Markdown, Hindsight and Project Anatomy

Do not make Markdown or Hindsight the universal interchange format for structured project state.

Use Markdown when it has direct human/workspace value:

```text
human-authored notes
reviewable summaries
meeting notes
reusable editorial Knowledge
optional Marker/OCR derivative
optional reconstructible project narrative such as Projet.md
```

The selected productive Hindsight path remains one-way:

```text
NAS / AFFAIRES source
-> Workspace Hindsight producer
-> Hindsight derived bank
-> bounded read/recall consumers
```

The earlier Obsidian Markdown -> `hindsight-obsidian-sync` path remains historical capability evidence only; it is not a second productive producer for AFFAIRES.

```text
Hindsight recall != truth
memory != Evidence
Hindsight ingestion != governed persistence
```

Do not manufacture Markdown copies solely to push these structures through Hindsight:

```text
document_structure
Observation Bundle
Project Anatomy stable_objects
Project Anatomy attribute_claims
Project Anatomy relation_claims
governed Professional Document/currentness records
```

When document analysis produces project semantics, use the existing path:

```text
exact source
-> document structural/semantic analysis when needed
-> canonical Observation Bundle
-> existing review/application path
-> Project Anatomy
-> bounded Hermes/Cockpit projection
```

Hermes may read admitted Project Anatomy through its bounded Project Anatomy context seam. An optional `Projet.md` may summarize that state for human consultation and Hindsight recall, but it remains a reconstructible projection and must not become the only persistence path or a second project-knowledge authority.

```text
Projet.md != Project Anatomy
projection != persistence
source observation != project truth
```

## 14. Structural-analysis qualification sequence

The workspace convenience choice does not pre-judge Pantheon-Next#662. Structural-analysis providers remain compared on one frozen agency corpus through the existing `document_structural_analysis` responsibility.

Current posture:

```text
Docling = preferred candidate / bounded implementation path
Marker = candidate to qualify for structural analysis
other candidates = remain under Pantheon-Next#662 as recorded there
```

Before replacing the structural-analysis binding or adding parser-specific downstream code, record exact identities, source/config/output digests, structured JSON availability, hierarchy/reading-order/table/assets behavior, reconversion behavior, provenance quality and operational cost.

No new adapter is justified until the comparison demonstrates a gap the existing structural-analysis and deterministic compilation responsibilities cannot cover.
