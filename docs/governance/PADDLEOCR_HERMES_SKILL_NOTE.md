# PaddleOCR Hermes Skill Placement Note

Status: candidate adapter note — documentation only.
Boundary profile: candidate_support_note.

This document records the placement decision for PaddleOCR as a possible document-extraction adapter.

It does not implement PaddleOCR.

It does not install a dependency.

It does not define a Hermes skill runtime.

It does not define an OpenWebUI plugin, Action, Tool, Function, Pipe, Pipeline or Knowledge importer.

It does not introduce a scheduler, queue, provider router, hidden ingestion runtime, automatic evidence approval or automatic memory promotion.

## Decision

PaddleOCR should be treated as an implementation detail of a Hermes document-extraction skill.

Pantheon Next should not depend on PaddleOCR.

Pantheon Next should define the abstract extraction contract, the candidate envelope, the evidence expectations, the risk gates, the scope rules and the downstream eligibility rules.

Hermes may execute a conforming skill that uses PaddleOCR internally.

The exposure surface may expose upload, selection, status, quality report and review controls.

## Placement

```text
Raw PDF / image / scan
→ exposure surface upload and scope selection
→ Task Contract records allowed source scope
→ Hermes document-extraction skill executes
→ PaddleOCR may perform OCR, layout and table extraction
→ Document Extraction Candidate
→ Evidence Pack Candidate
→ Pantheon status gate
→ reviewed Knowledge / RAG candidate / Evidence Candidate / rejection
```

PaddleOCR is not a governance primitive.

It is one possible adapter behind a generic capability:

```text
Document Extraction Adapter
```

A concrete Hermes implementation may be named:

```text
hermes.skills.document_extract.paddleocr
```

The generic Pantheon rule must not be named after PaddleOCR.

## Why this belongs in Hermes

Document extraction is external execution.

It reads files, runs models, performs OCR, extracts layout, emits Markdown or JSON, writes candidate artifacts and may need fallback strategies.

That is execution-runtime work.

Pantheon governs whether the output is admissible, reviewable, scoped, retrievable, evidence-eligible or memory-eligible.

Pantheon does not parse documents.

Pantheon does not choose OCR internals for a run.

Pantheon does not turn OCR output into truth.

## Abstract contract

A document-extraction adapter should conform to the common envelope:

```text
Task Contract in
→ document extraction adapter
→ { Document Extraction Candidate, Evidence Pack Candidate } out
```

The adapter may extract:

```text
text
layout blocks
tables
figures
page anchors
source references
confidence scores
unreadable zones
quality flags
structured Markdown
structured JSON
```

The adapter must preserve:

```text
source file identity
source file hash
page references
adapter id
adapter version
configuration reference
run timestamp
quality limitations
review recommendation
```

## Candidate manifest sketch

This is a sketch only. The canonical manifest shape remains in `MODULAR_DOMAIN_REORIENTATION.md` until an approved schema exists.

```yaml
module_manifest:
  id: hermes.skills.document_extract.paddleocr
  name: PaddleOCR document extraction adapter
  version: candidate
  owner_layer: execution_runtime
  type: skill
  status: candidate
  activation:
    state: candidate
    scope: task
  task_authorization:
    state: unauthorized
  interface:
    allowed_inputs:
      - raw_source_reference
      - source_file
      - task_contract
      - extraction_profile
    allowed_outputs:
      - document_extraction_candidate
      - evidence_pack_candidate
      - quality_report
    forbidden_outputs:
      - canonical_memory
      - approved_evidence
      - approval_event
      - external_delivery
    envelope: task_contract_in / candidate_out / evidence_pack_out
  governance:
    consequential: true
    risk_level: high
    approval_behavior: review_required_for_consequential_use
    memory_behavior: never_canonical
    scope_behavior: task_or_dossier_bound
  composition:
    talks_only_via_envelope: true
```

## Output candidate sketch

```json
{
  "candidate_type": "document_extraction_candidate",
  "adapter_id": "paddleocr",
  "adapter_version": "x.y.z",
  "source_file": {
    "name": "source.pdf",
    "hash": "sha256:...",
    "mime_type": "application/pdf",
    "page_count": 12
  },
  "extraction": {
    "markdown": "...",
    "structured_json": {},
    "tables": [],
    "layout_blocks": [],
    "figures": [],
    "unreadable_zones": [],
    "confidence": {
      "global": 0.0,
      "text": 0.0,
      "layout": 0.0,
      "tables": 0.0
    }
  },
  "quality_flags": [
    "review_required"
  ],
  "evidence_status": "retrieved_knowledge",
  "memory_status": "not_memory"
}
```

Scores are advisory.

A high confidence score does not approve the extraction.

A low confidence score should raise review pressure.

## Risk gates

Human review is required before consequential use when the extracted document includes:

```text
contract clauses
quotes or invoices
insurance material
legal or regulatory material
technical standards
planning commitments
professional liability exposure
client-specific facts
financial amounts
dates or deadlines
tables with low confidence
unreadable zones
```

OCR output may support search, preparation and review.

OCR output must not become canonical memory, approved evidence, project truth or professional deliverable by itself.

## Modularity rule

PaddleOCR must remain replaceable.

Other adapters may satisfy the same contract:

```text
hermes.skills.document_extract.docling
hermes.skills.document_extract.marker
hermes.skills.document_extract.mistral_ocr
hermes.skills.document_extract.azure_document_intelligence
hermes.skills.document_extract.tesseract
```

Replacement should not require a doctrine rewrite.

Only the adapter implementation and its manifest target should change.

## Relationship to existing doctrine

This note follows:

- `MODULAR_DOMAIN_REORIENTATION.md` for the module manifest and envelope;
- `CAPABILITY_PLACEMENT.md` for the rule that extraction belongs in the execution runtime;
- `RAG_INGESTION_PIPELINE.md` for governed document ingestion;
- `HERMES_INTEGRATION.md` for the Hermes candidate-output boundary;
- `ADAPTERS_AND_BINDINGS.md` for the blueprint-in-Pantheon, adapter-outside model.

If this note conflicts with those documents, those documents win.

## Boundary phrase

```text
PaddleOCR reads.
Hermes executes the skill.
Pantheon governs the candidate.
The validated remains.
```
