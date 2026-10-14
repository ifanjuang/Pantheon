# Document conversion and structured-extraction convergence

Status: candidate support doctrine — convergence note.
Boundary profile: candidate_support_note.
Date: 2026-08-07.

## Objective

Clarify the already-implemented document path without introducing a parallel `Distillation` authority or a second document model.

This note reconciles the current Pantheon Next doctrine with the verified `pantheon-mvp` implementation and records how additional converters such as Firecrawl AnyDoc may be evaluated later.

## Verified repository state

Observed at preparation time:

```text
Pantheon-Next main: 8227d1c78ca48e5aea04f825d80ecde159fa5434
pantheon-mvp main: 6326412261f51f2d1915f19150805e8dc174fbd0
firecrawl/anydoc main observed at release v0.1.7 lineage
```

The MVP already separates the following responsibilities:

```text
source_documents
→ extraction_runs
→ structured extraction compilation
→ extraction_units
→ retrieval projections / chunks
→ lexical + vector retrieval
→ deterministic hybrid fusion
→ Result / Evidence candidates
→ human decision boundary
```

The current implementation already exposes a replaceable `DocumentConverter` protocol and a `ConvertedDocument` result carrying Markdown, converter-native structured JSON, converter identity/version/configuration, status and quality flags.

The current structured-extraction compiler then compiles the observed conversion into versioned, provenance-bearing units and retrieval projections. It records compilation identity, ordered units, section context, page locators, table structure, diagnostics, quality flags and immutable chunk identities.

Therefore:

```text
new Distillation object not required
new DistilledUnit authority not required
new DistilledDocument authority not required
```

The existing derived-content and retrieval concepts already own these responsibilities.

## Canonical responsibility chain

```text
exact Source
→ DocumentConverter binding
→ ConvertedDocument observation
→ structured-extraction compilation
→ StructuredUnit derivatives
→ RetrievalProjection derivatives
→ scoped indexes / chunks
→ HybridRetrieval candidate
→ governed candidate selection
→ Evidence Candidate when deliberately selected
→ human gate where consequential
```

This chain does not alter the layered authority model in `RAW_DERIVED_GOVERNED_RECORDS.md`.

```text
Source != derivative
ConvertedDocument != source truth
StructuredUnit != governed fact
RetrievalProjection != memory
retrieved != Evidence
hybrid score != confidence
successful conversion != professional validation
```

## Conversion binding boundary

`DocumentConverter` is the existing execution-side seam. A concrete converter is a replaceable binding, not a Pantheon authority object.

Current verified candidates include:

```text
DirectTextConverter
- dependency-free text path

DoclingServeClient
- selected bounded binary-document candidate path in pantheon-mvp
- layout-aware JSON + Markdown
- OCR-capable configuration
```

A future converter may be introduced only by implementing the same responsibility without changing source authority, structured-extraction authority or retrieval authority.

```text
converter available != selected
converter selected != dependency adopted globally
conversion success != verified content
faster conversion != better retrieval
```

## Structured extraction is the normalization stage

The current `pantheon_structured_extraction` compiler is the normalization stage between converter-specific output and retrieval.

Its responsibility is to preserve useful source structure while producing stable retrieval-facing derivatives. It is not a semantic truth extractor and does not create project facts, Knowledge, Decisions or Evidence.

Current normalized concepts include:

```text
StructuredUnit
- content_type
- text
- structural_locator
- page range
- parent heading
- heading level
- section path
- quality flags
- normalized table payload where applicable

RetrievalProjection
- retrieval text
- source unit ordinals
- content type
- structural locator
- page range
- section context
- quality flags
```

This is the canonical place to absorb converter variability before indexing.

If a new converter exposes richer source structure, the preferred order is:

1. map that structure into the existing compiler inputs or extend the compiler deterministically;
2. preserve converter-native payload in `extraction_runs` for audit/reprocessing;
3. extend `StructuredUnit` only when a genuinely new normalized responsibility is required;
4. avoid converter-specific fields leaking into HybridSearch or governed records.

## AnyDoc posture

`firecrawl/anydoc` is a useful watch candidate for the existing `DocumentConverter` seam, especially for native office formats.

Observed strengths:

```text
Rust/local execution;
DOC/DOCX, PPT/PPTX, XLS/XLSX, ODF, RTF, EPUB, CSV and text-PDF coverage;
content-based format detection;
shared document model before Markdown serialization;
embedded-asset retention;
Node, Python, Rust and WASM bindings;
low conversion latency in its published benchmark.
```

Its internal shared model is informative because it normalizes headings, paragraphs, lists, tables, notes and assets before serialization.

It must not become the Pantheon canonical document model merely because that model is convenient.

Current reasons to keep it unselected:

```text
repository/library is still young and rapidly changing;
no OCR for image-only/scanned PDFs;
open spreadsheet-format fidelity issues can change displayed numeric meaning;
open hidden-row/column semantics can expose source content differently from the user-visible workbook;
presentation boundary and Markdown escaping issues remain under active correction;
no Pantheon corpus benchmark proves a retrieval-quality gain over the current Docling path.
```

Therefore the current posture is:

```text
AnyDoc = candidate DocumentConverter binding for evaluation
AnyDoc != adopted dependency
AnyDoc != replacement for Docling
AnyDoc != source-management runtime
AnyDoc != retrieval engine
AnyDoc != Evidence producer
```

## Paperless boundary

Paperless remains an optional `document_source_management` binding and does not enter the conversion/normalization authority chain.

Valid relation:

```text
NAS / Paperless / another source binding
→ exact source capture
→ admitted conversion
→ structured extraction
→ retrieval
```

Invalid collapse:

```text
Paperless document == Pantheon Document
Paperless OCR == source truth
Paperless search hit == Evidence
Paperless selected == converter authority
```

## HybridSearch boundary

The current MVP already provides:

```text
scope-first PostgreSQL lexical retrieval;
vector retrieval through the replaceable embedding seam;
deterministic weighted Reciprocal Rank Fusion;
separate lexical rank, vector/semantic-branch rank and fused score;
Task Contract dossier + declared-source filtering before ranking.
```

Structured extraction must improve the inputs to this path, not create a competing retrieval pipeline.

The active local feature-hashing embedder proves the vector path and zero-exposure seam but does not establish production semantic quality. Converter evaluation must therefore separate:

```text
conversion fidelity;
normalization fidelity;
chunk/retrieval quality;
embedding quality;
ranking quality.
```

A faster converter must not be credited for ranking improvements caused by a different embedding, and a stronger embedding must not hide structural losses introduced during conversion.

## Evaluation gate for an additional converter

Before adding an AnyDoc binding to `pantheon-mvp`, run the existing path and candidate path on the same bounded corpus and keep downstream normalization/retrieval configuration fixed.

Minimum representative cases should include:

```text
DOCX CCTP / notice;
PPTX presentation with titled and untitled slides;
XLSX DPGF / estimatif with percentages, currency, formulas, hidden rows/columns and merged cells;
text PDF;
scanned PDF as an explicit unsupported/fallback case;
RTF or legacy DOC where useful to the agency corpus.
```

Measure separately:

```text
text completeness;
heading/section preservation;
table-cell fidelity;
displayed numeric fidelity;
page/slide/sheet provenance;
quality-warning coverage;
structured-unit stability;
retrieval expected-source rank on the existing métier set;
latency and resource use.
```

Adoption is justified only if the new binding demonstrates a material advantage while preserving or improving provenance and retrieval quality.

## Preferred routing if later justified

A future explicit routing policy may select converters by capability profile, for example:

```text
plain text / Markdown
→ DirectTextConverter

native office document proven safe by corpus tests
→ candidate office converter such as AnyDoc

PDF, scan, image or layout-sensitive material
→ Docling / OCR-capable structural-analysis binding
```

The routing policy must remain explicit, testable and server-authoritative. It must not be inferred from provider availability alone.

## Non-goals

This convergence note does not authorize:

```text
a new Distillation domain object;
a new database authority table solely for distillation;
AnyDoc installation or activation;
replacement of Docling;
a second retrieval store;
a new vector database;
a reranker;
a production embedding provider;
Paperless promotion to document authority;
automatic Evidence admission;
automatic professional validation.
```

## Completion criteria for this convergence slice

This slice is complete when:

```text
1. Pantheon documentation explicitly recognizes structured extraction as the normalization stage;
2. downstream work reuses DocumentConverter / ConvertedDocument / structured extraction rather than creating parallel concepts;
3. AnyDoc remains a measured candidate until corpus evidence justifies a binding;
4. HybridSearch continues to consume normalized retrieval projections with provenance intact;
5. no governance state is inferred from conversion or retrieval success.
```
