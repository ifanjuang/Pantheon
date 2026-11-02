# Document inspection

Operational reference for `project-context`. Use it when an agency answer depends on the existence or content of a plan, PDF or other professional document. It does not define a parser binding, Evidence status or professional validation rule.

## Keep document states distinct

A document can be referenced without being available, available without being inspected, and inspected only partially.

```text
mentioned != exact source present
exact source present != relevant content inspected
Hindsight recall != document inspected
Markdown derivative != exact source
metadata != document content
```

A mention in a CCTP, meeting report, CERFA, email or another document proves only that the source is referenced there. Do not infer that the exact file exists in the admitted workspace or that its content has been checked.

## Resolve the exact source when content matters

When the answer materially depends on document content:

1. use the currently admitted workspace/document bindings to resolve the exact source candidate;
2. confirm that the source representation required for the question is actually available;
3. inspect only the document or pages necessary for the question through the currently admitted document-analysis capability;
4. retain the exact source identity and page, section, anchor or other locator when available;
5. expose any inspection limitation before drawing a material conclusion.

Do not hard-code Docling, Marker, OCR or another provider in this reference. The selected binding may change independently of this skill.

## Match inspection to the claim

Use text/structural extraction when the claim depends on clauses, labels, tables, metadata or textual structure.

If the claim depends on geometry, drawing marks, dimensions, annotations, spatial relationships, page layout or other visual content, use an admitted visual/document inspection path rather than treating extracted text alone as sufficient.

If only a Markdown/OCR/parsed derivative is available, it may support discovery and analysis within its limits, but preserve that it is a derivative. Do not silently represent it as inspection of the exact source.

## Handle absence carefully

A Hindsight result containing only `.md` material does not establish that a corresponding PDF is absent. Conversely, a filename in an inventory does not establish that the relevant content was inspected.

Before saying that a requested document or fact is absent, search the admitted project source scope proportionally and distinguish:

- source not found in the searched scope;
- source found but not inspectable through the current binding;
- source inspected but requested content not found;
- source inspection incomplete or uncertain.

```text
not retrieved != absent
file listed != content inspected
parser success != professional validation
inspection result != Evidence admission
```

## Inventory fallback and coverage

An index is a useful continuity surface, not an exhaustive file inventory. When
an exact source is not located in the configured index, inspect the admitted
project/workspace inventory before asking the user to search manually or
declaring the source absent. This applies to every representation: document,
image, plan, recording, form, message or attachment.

Keep the lookup receipt proportionate but explicit whenever it changes the
answer:

```text
index: matched | no_match | unavailable
source inventory: exact_source_present | candidates_found | truncated | no_supported_source
inspection: not_needed | opened | partial | not_readable
```

An inventory that reports a limit or incomplete scan supports only a bounded
statement: report the returned candidates and its limit. It does not support
"only these documents exist" or an absence conclusion. A path/filename match
is a source candidate, never proof of the requested content.

If the admitted inventory call itself errors, do not repeat the same call or
translate the error into a missing-source finding. When an exact source path is
already supplied or returned by an admitted locator for the same scope, try
that exact path once with the admitted reader. Otherwise make at most one
distinct, focused locator lookup, then try its exact result once. Do not guess
paths or widen the source scope silently. If recovery fails, report the source
as inaccessible or unresolved in the attempted route; absence remains
unestablished. Repeat only after a relevant path, scope, mount or service-state
change.

### Recover from reader errors without looping

Read the actual tool error and correct the failed parameter or scope before one
retry. Respect declared limits such as required arguments and maximum page
windows; do not repeat a call rejected for the same reason. If the tool reports
that it is paused after repeated failures, stop calling it in that turn. Use
one different admitted route only if it can answer the same unresolved question;
otherwise return the supported partial result and the specific access limit.
An error, timeout or pause is not evidence that the source or requested content
is absent.

If the exact source is present in the admitted workspace but absent from the
index, state `source_present_not_indexed` and use the suitable admitted
inspection route. This is an indexing gap, not a reason to invent content or
to require an upload of a source already available locally.

## Session attachments and filing proposals

An attachment in the current conversation is session input unless it has been
explicitly admitted into a workspace. It may be inspected proportionately, but
must remain distinct from a NAS/project source.

Hermes may propose a classification and filing destination with the source
indicators and uncertainty that support it. It must not copy, rename, move,
reclassify or retain the attachment as a professional source without a selected
destination and the applicable admitted write authorization.

```text
session attachment != workspace source
classification proposal != filing performed
index enrichment != source-file move
```

## Return with provenance

For material project-document conclusions, keep the document title, source
provenance, revision/index and date visible when available, together with a
clickable link to the exact project file when the admitted interface exposes
one. Never fabricate a link; if none is exposed, provide the exact reader
locator and say so. Distinguish observed content from interpretation, inference
and remaining uncertainty. For transversal Knowledge sources, cite the
returned document title/name and available provenance; a filename or clickable
file link is not required unless the user specifically asks for the original.
