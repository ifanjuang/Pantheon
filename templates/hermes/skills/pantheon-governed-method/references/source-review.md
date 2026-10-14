# Bounded source and coverage review

Read this reference when workspace sources support factual claims, when several
candidates must be compared, or when completeness or conformance is at issue.

## Source-first discipline

Inventory what is available, absent, stale, partial, unreadable or contradictory.
Memory and retrieval provide leads; consequential claims require an exact source
and useful locator opened through an admitted route.

## Bounded Docling reading

For long PDFs, tables or specifications, use Docling progressively:

```text
convert when needed
-> overview of anchors
-> targeted text search
-> smallest relevant anchor reads
```

Do not export an entire Docling document to Markdown for source review. Large
exports can spill to a runtime file that the governed profile cannot and should
not reopen through `terminal` or generic file access. If a result is reported as
persisted or spilled over, stay on the Docling route and repeat the request with
targeted searches and bounded anchor reads. Process one consequential document
at a time and keep only the extracts needed for the coverage matrix.

For a comparison, resolve the reference source and its comparison perimeter
before converting candidates. Do not launch several conversions in parallel.
Complete and classify one bounded read before selecting the next; a tool result
that merely names a document is not a read. Do not announce a provisional
comparison, a future result, or an "in progress" table: return only completed
observations, or state the remaining reads and `ready_with_limits`.

### Docling latency and failure posture

A slow conversion is not an unavailable service. A conversion taking tens of
seconds, or a successful MCP response followed by a pause, remains a normal
Docling route. Do not invent an outage, an estimated recovery delay, or a
fallback merely because a conversion is slower than the other documents.

When a Docling call reports a real transport or service error, retain the exact
failed document reference and:

1. wait only for a recovery delay explicitly returned by Docling, then retry
   the same bounded call once;
2. if the retry fails or no recovery delay was supplied, mark that source
   `unreadable_or_unverified` and complete only the supported portion as
   `ready_with_limits`.

Never use `terminal`, generic filesystem access, a guessed parser, a browser
download, or an alternative PDF extraction route as a Docling fallback. The
governed profile has no such source authority. Do not claim that a comparison is
complete when a material reference or quote remains unreadable.

## Representations and derived analysis

A derived representation is temporary analysis material by default. It never
replaces the original source or becomes durable merely because Hindsight can
recall it.

Retrieve source-grounded Hindsight memory for the exact source before deriving
anything. Use the least costly suitable representation: native text, structured
data, or metadata for orientation; then an admitted method appropriate to the
missing information (for example OCR, structure-aware extraction, a bounded
visual inspection, or transcription). Do not infer evidence from filename or
metadata alone. Do not claim that a vision or transcription capability exists
when no admitted runtime tool exposes it.

Usable retrieved content blocks a new derived analysis. For OCR, any
`ocr:raw`, `ocr:partial` or `ocr:complete` tag also blocks ordinary OCR; only
`force_ocr=true` bypasses it. When no usable representation exists, explain the
selected method and ask whether its result stays in the current session
(default) or enriches the corresponding existing Hindsight document through the
designated producer. Never create an adjacent project file as part of this
route, and never run a broad derived analysis where a bounded question would
suffice.
For any proposed enrichment, list every selected source with its
exact relative path and the observed representation result before requesting
that choice.

The producer owns durable OCR state and re-emits it on every reconciliation so
ordinary source reconciliation cannot erase it. Use low-cardinality tags:

```text
ocr:raw
ocr:partial | ocr:complete
ocr:quality:poor | ocr:quality:fair | ocr:quality:good | ocr:quality:excellent
```

Keep detailed provenance in document metadata, not high-cardinality tags:
`ocr_source_sha256`, `ocr_engine`, `ocr_pipeline_version`, `ocr_completed_at`
and Docling's available confidence grades. Hermes uses tags for routing and
metadata for integrity. A changed PDF has no trusted OCR state until the user
chooses a new action. Re-run an otherwise current OCR only after an explicit
user request recorded as `force_ocr=true` for that operation.

The current governed source tools are read-only and cannot persist a file or an
OCR update. The future bounded retention route must address one already resolved
document through the designated producer; Hermes must not receive arbitrary
bank-write access. Once an authorized writer creates a project file, Hindsight
may index it only after reconciliation is observed.

```text
OCR result != source PDF replaced
Hindsight memory != document storage
file written != Hindsight reconciliation observed
batch retention choice != in-place replacement authority
three representations != three documents
same Hindsight document id != duplicate document
derived analysis != source artifact replaced
```

## Bounded delegated source review

Use `delegate_task` only for an independent, bounded source question that would
otherwise flood parent context. Begin with one child at a time. The parent owns
clarification, synthesis and verification.

Give the child only the needed toolsets:

```text
mcp-vault-read
mcp-hindsight-project
mcp-docling — only after the parent supplies an exact bounded document list
```

Do not give browser, terminal, generic file access, writing, messaging, memory,
Kanban, clarification, unrelated MCPs or further delegation. Provide the
referent, question, admitted scope, language and stop condition. Require structured:

```text
observed_facts
exact_sources_and_locators
contradictions
missing_or_unreadable_material
limits
```

The parent reopens material supporting passages. It may make one corrective
request with the same scope; then it surfaces the gap.

```text
subagent result != source verification
scope gap != permission to broaden sources
```

## Reference-first coverage matrix

Before comparing candidates, normalize perimeter, inclusions, exclusions,
variants, tax basis, date and completeness. Build the coverage matrix from the
reference first, never from candidates found. Give every material reference
line or package exactly one state:

```text
matched_comparable
matched_scope_difference
combined_with_other_scope
alternative_or_variant
missing_candidate
unreadable_or_unverified
not_applicable_with_reason
```

Do not omit an unmatched reference item. A filename, directory or candidate
label does not prove scope coverage; verify material description and amount.
Report matched, missing and unresolved coverage separately.

Never compare a partial aggregate with a broader reference total. Normalize a
common basis before any numerical comparison (scope, unit, date, tax/currency
or any other material measurement basis). A candidate that cannot be tied to a
reference item is `unreadable_or_unverified` or `missing_candidate`, not
"conforme". A matching amount alone is not conformance: the material scope
must also be verified.

Overall conformance requires complete material coverage or an explicit
user-approved exclusion. Otherwise state only bounded, source-located
observations and `ready_with_limits`; do not label any result as conforming,
non-conforming, complete, or exhaustive.
