# Document Intelligence

Status: candidate support doctrine — governed document intelligence boundary and evidence chain.
Boundary profile: candidate_support_note.

This document defines how Pantheon Next frames document intelligence without becoming a document-processing runtime, OCR pipeline, vector database, graph runtime, scheduler, queue or automatic decision system.

It is documentation only.

It does not implement ingestion, OCR, chunking, embeddings, graph storage, review queues, database tables, OpenWebUI actions, Hermes skills, connectors, approvals or memory promotion.

In abstract form:

```text
The exposure surface exposes.
The execution runtime executes.
Pantheon governs.
```

## Purpose

Professional document work is not only retrieval.

The risk is not merely that a system fails to find a passage. The risk is that it turns a weak extraction, obsolete version, partial chunk, inferred claim or convenient summary into an apparent truth.

Pantheon therefore governs the passage from source to decision:

```text
Document Source
-> Ingestion Candidate
-> Fragment Candidate
-> Interpretation Candidate
-> Evidence Pack Candidate
-> governed status
-> human decision
```

The central rule:

```text
A document does not become knowledge.
A fragment may support an interpretation candidate.
An interpretation candidate may enter an Evidence Pack Candidate.
An Evidence Pack Candidate may support a governed status.
Only a governed status can support a decision.
```

## Source posture

A source is a received or referenced object. It may be a file, email, note, drawing, image, contract, report, official publication, standard, template or database record.

A source must not be treated as proof by existence alone.

Required source questions:

```text
What is the source?
Where did it come from?
Who produced it?
Which dossier or scope does it belong to?
Which version is it?
Is it complete?
Is it current?
Is it allowed for this task?
```

## Document status vocabulary

Document processing must carry status before use.

Recommended statuses:

```text
received
ingestion_pending
usable_text
ocr_required
partial_extraction
image_only
source_untrusted
version_unknown
superseded
indexed_candidate
rejected
archived
```

These statuses do not prove the content. They describe the fitness of the source for later work.

## Fragment boundary

A fragment is a bounded excerpt with a source reference.

A fragment should carry enough metadata to be reviewable:

```text
source_id
source_version
fragment_id
page_or_location
section_or_heading
extracted_text
extraction_method
extraction_confidence
scope_id
```

A fragment is not an interpretation. It is source material.

A retrieved fragment is still a candidate until selected and represented inside an Evidence Pack Candidate.

## Interpretation boundary

An interpretation is a claim derived from one or more fragments.

Examples:

```text
obligation detected
risk detected
missing item detected
contradiction detected
deadline detected
actor responsibility detected
approval needed
Register Candidate proposed
```

Interpretations produced by tools or models must start as candidates.

Required interpretation fields:

```text
claim_type
claim_text
source_fragments
scope_id
produced_by
produced_at
confidence_or_limits
status: candidate | rejected | accepted | superseded
```

Confidence is advisory only. It never validates a claim.

## Evidence Pack Candidate

An Evidence Pack Candidate gathers the fragments, interpretations, assumptions, contradictions and missing evidence needed for review.

It should make visible:

```text
supporting fragments
contradicting fragments
missing source material
version risks
scope risks
assumptions
uncertainties
recommended gate
```

It must not hide weak evidence behind a fluent synthesis.

## Governed status

Pantheon governs the status of the result, not the execution that produced it.

Useful statuses:

```text
draft_candidate
source_incomplete
source_complete_for_task
requires_human_review
requires_more_evidence
requires_client_decision
requires_contractor_response
approved_for_internal_use
approved_for_transmission_draft
approved_for_contractual_action
rejected
obsolete
```

A status must remain reversible or supersedable when evidence changes.

## Placement

Document intelligence spans several layers.

| Concern | Belongs in | Boundary |
|---|---|---|
| selecting dossier or documents | exposure surface | user-visible scope |
| extraction, OCR, comparison, classification | execution runtime or deterministic preparation | candidate production only |
| relationship discovery or provenance linking | graph / provenance support layer | connectivity is not proof |
| status, evidence rule, approval and register-admission rule | Pantheon | governance only |
| final decision | human | explicit and logged |

Pantheon may define the contract and status vocabulary. It must not become the extractor, vector index, graph engine, queue, scheduler or connector gateway.

## Registry and graph posture

A registry or graph may support relationships between sources, fragments, claims, evidence, decisions, approvals and Register Candidates.

It may help answer questions such as:

```text
Which claims depend on a superseded source?
Which contradictions are still unresolved?
Which approved decision used this fragment?
Which Register Candidate came from this dossier?
```

But the graph does not decide truth.

```text
Connectivity is not approval.
Similarity is not proof.
Retrieval is not evidence until selected, scoped and represented.
```

## Access boundary

Any storage or database path must follow the dossier boundary.

Recommended doctrine:

```text
The execution runtime does not ask storage what exists.
Pantheon tells the execution runtime what it is allowed to ask.
Storage returns only what the task scope permits.
```

A shared storage backend may exist, but scope must not be shared.

```text
Storage may be mutualized.
The governed perimeter must remain compartmentalized.
```

Normal workflows should use one of these patterns, from safest to more sensitive:

```text
Context Pack export
scoped read-only gateway
scoped read-only views or functions
direct raw access only for diagnostics, never normal work
```

Any future implementation must preserve read scope, source references, evidence status, claim status, approval level and the separation between retrieved knowledge, evidence and a Registre Probatoire entry.

## Memory boundary

Document intelligence may propose Register Candidates.

It must not promote a Registre Probatoire entry.

A Register Candidate must identify:

```text
claim
source evidence
scope
intended reuse
expiration or review trigger
approval required
```

Examples:

```text
project-scoped fact
agency checklist candidate
domain vigilance candidate
rejected pattern
```

Nothing becomes a Registre Probatoire entry because it was repeated, scored, embedded, clustered or retrieved.

## Review queue relation

A document intelligence process may generate review items: duplicates, conflicts, stale facts, low-confidence claims, missing sources or Register Candidates.

The review queue is a decision surface, not an automatic applicator.

A trigger may enqueue and notify. It must not apply.

## Non-goals

This document does not authorize:

```text
automatic document validation
automatic source validation
automatic OCR pipeline
automatic graph construction as proof
automatic CCTP / quote conformity verdict
automatic approval
automatic memory promotion
direct broad database access by an execution runtime
cross-dossier retrieval without explicit approval
hidden scheduler or queue inside Pantheon
```

## Boundary phrase

```text
Pantheon governs the passage from source to decision.
The tools produce candidates.
The human validates what may remain.
```

## First professional slice

The first recommended professional slice is architecture document review:

```text
CCTP / quote comparison
site report / reservation follow-up
contractual document consistency
source-bound professional vigilance
```

See `DOCUMENT_REVIEW.md`.
