# Document structural-analysis qualification lab

Status: local-only qualification support for Pantheon issue Pantheon-Next#662. It does not install a parser, select a binding, ingest a document, replace a source, admit Evidence, or alter a product/runtime path.

## Purpose

Compare replaceable implementations of the existing `document_structural_analysis` capability on the **same immutable private corpus** without committing client documents or creating a parallel ingestion pipeline.

```text
private immutable source corpus
          │
          ├── Docling profile
          ├── Marker profile
          ├── OpenDataLoader deterministic profile
          └── OpenDataLoader hybrid profile
                    │
                    ▼
          local parser observations
                    │
                    ▼
             qualification.py
                    │
                    ▼
     provider-neutral comparison report
```

The report is qualification evidence only. It never means `preferred_candidate` automatically.

## Existing owners remain unchanged

```text
source document                 = authoritative source identity/provenance
DocumentConverter               = bounded provider-neutral conversion seam
StructuredUnit                  = shared structural normalization responsibility
structured compiler / chunks    = one downstream retrieval path
Evidence / Knowledge owners     = unchanged
Hermes / external runtime       = parser execution when selected and authorized
```

Do not add a parser-specific Source owner, extraction store, chunker, Knowledge owner, RAG authority, or synonymous capability slot.

## Privacy boundary

Real agency corpus files and campaign observations remain local.

Do not commit:

- client filenames or paths;
- document bytes;
- extracted client content;
- Drive identifiers;
- parser outputs containing client content;
- local credentials/configuration;
- machine-specific private locators.

The campaign contract intentionally identifies a private case only by an opaque `case_id`, immutable SHA-256 digest, page count, and non-sensitive structural traits. Unknown fields are rejected, so fields such as `source_path`, `filename`, or `content` cannot silently enter the qualification envelope.

## 1. Freeze the corpus locally

Use a private directory outside the repository, for example:

```bash
OUT="$HOME/pantheon-qualification/document-structural-analysis/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"
```

For every source compute the digest from the exact bytes used by all candidates:

```bash
sha256sum /private/path/document.pdf
```

The same `case_id` and source digest must be reused by every candidate profile. `qualification.py` fails closed if an observation claims another digest.

The Pantheon-Next#662 corpus should cover, where available, multi-level CCTP structure, dense/irregular tables, OCR-only pages, mixed digital/scanned material, administrative headers/footers, forms, technical figures/captions, and at least one deliberately difficult known case.

## 2. Record exact profile identities before execution

Each profile records M1 independently from its run observations:

```json
{
  "profile_id": "docling-baseline",
  "candidate": "docling",
  "release_identity": "<exact release/tag>",
  "implementation_identity": "<package/image/commit and immutable digest where available>",
  "code_license": "<license>",
  "model_terms": "<model/weight/commercial terms or explicit none>",
  "dependency_chain": ["<exact material backend identities>"],
  "supported_formats": ["pdf"],
  "runtime_requirements": ["<CPU/GPU/runtime requirements>"],
  "external_dependencies": [],
  "identity_limitations": []
}
```

A hybrid profile is a separate profile and must name its actual delegated backend chain. `binding selected != dependency adopted`.

Recheck upstream versions immediately before the live run. Repository comments or old campaign records are provenance, not proof of what is installed now.

## 3. Run each parser locally on the same bytes

Parser installation and execution remain external to this repository lab. Pin them in isolated environments appropriate to each tool. Do not compensate for a failed local installation by uploading private client PDFs to an unapproved service.

For each `(profile_id, case_id, attempt)` capture locally:

```text
status
status reason when not complete
observed source digest
configuration digest
canonical output digest when output exists
elapsed wall time
peak RAM / VRAM when measurable
observed page count
warnings/errors
available locator kinds
explicit quality checks
```

Accepted operational statuses are:

```text
complete
partial
blocked
failed
not_executed
```

`not_executed` is not `failed` and is not evidence of incompatibility. Use the status reason to preserve why execution did not occur.

## 4. Inspect quality explicitly

Checks are corpus-case specific. Typical check identities include:

```text
reading_order
heading_hierarchy
paragraph_list_grouping
multi_column_order
header_footer_noise
table_topology
table_spans
table_headers
table_cell_text
table_page_provenance
ocr_coverage
accented_french
page_coverage
caption_linkage
figure_references
structural_locators
bbox_locators
failure_visibility
```

Check results are only:

```text
pass
fail
not_observed
not_applicable
```

Do not collapse these observations into one benchmark score. A fast parser with an unobserved or failed required quality check is not silently preferred.

## 5. Campaign envelope

Minimal local shape:

```json
{
  "campaign_id": "opaque-local-campaign",
  "repository_ref": "<exact Pantheon-Next commit>",
  "profiles": [],
  "cases": [
    {
      "case_id": "case-01",
      "source_digest": "sha256:<64 lowercase hex>",
      "page_count": 10,
      "traits": ["born_digital", "tables"],
      "required_checks": ["reading_order", "table_topology", "page_coverage"]
    }
  ],
  "observations": []
}
```

Each observation must contain all fields accepted by `qualification.py`; inspect the test fixture for a complete synthetic example. The strict envelope is deliberate: campaign observations are evidence of a run, not a place to persist extracted document content.

## 6. Validate and summarize

From the repository root:

```bash
python implementation/labs/document_structural_analysis/qualification.py \
  "$OUT/campaign.json" \
  --output "$OUT/report.json"
```

The report exposes:

- missing profile/case matrix rows;
- operational status counts;
- required check failures and unobserved checks;
- input/output page-count mismatches;
- repeatability mismatches for repeated complete runs under the same config digest;
- medians of observed elapsed/RAM/VRAM values;
- whether the matrix and required observations are complete.

It deliberately does **not** emit source digests or client content into the report and does not automatically select a parser.

## 7. Repeatability

For a reproducibility probe, repeat a case with the same source and configuration digest using attempt `1`, `2`, ... .

If complete runs under the same configuration produce different canonical output digests, the report exposes a repeatability mismatch. A provider may still be usable, but the non-determinism must be understood rather than hidden.

Only hash a canonical parser derivative for repeatability. Do not include timestamps, temp paths, host-specific metadata or other known volatile fields in that digest.

## 8. Final Pantheon-Next#662 decision

After the live same-corpus campaign, inspect the report and the actual derivatives manually. Assign exactly one posture per tested profile:

```text
preferred_candidate
fallback_candidate
watch
rejected
```

Decision order:

```text
quality / silent-loss behavior
-> provenance / source resolution
-> repeatability
-> operational envelope and failure behavior
-> replacement complexity
-> binding posture
```

A candidate displaces Docling only on demonstrated same-corpus benefit. A missing run never counts as a win or loss.

If a winner requires implementation convergence, open one separate narrow implementation PR that reuses `DocumentConverter` and the existing `StructuredUnit` / structured-compilation path. Do not refactor `converter_for()` merely to prepare for hypothetical providers.

## Current execution limitation

The first 2026-09-14 preparation pass established a private same-corpus preflight, but the interactive qualification runtime could not resolve PyPI/GitHub package hosts for parser installation. That is an execution-environment limitation, not a parser result. No Docling/Marker/OpenDataLoader quality score or winner is claimed by this repository lab.

Pantheon-Next#662 remains open until real same-corpus observations support an evidence-backed slot decision.
