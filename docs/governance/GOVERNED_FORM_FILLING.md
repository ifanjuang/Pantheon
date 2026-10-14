# Governed Form Filling

Status: candidate support doctrine — to verify. Governed filling of any structured document (form, CERFA, administrative template) from project records and authorized sources. Candidate until reviewed.

This document defines how a system may prepare a filled document — a CERFA, an administrative form, a structured template — from what a dossier already knows, by retrieving the rest from authorized sources, asking when in doubt, documenting every value's origin, and producing a reviewable draft that a human verifies and signs.

It is documentation only. It does not implement a form filler, PDF writer, OCR, web scraper, API connector, contact synchronization or runtime. Those are adapters outside Pantheon (`ADAPTERS_AND_BINDINGS.md`) executed by the execution runtime under a Task Contract.

```text
The exposure surface exposes.
The execution runtime executes.
Pantheon governs.
```

## Purpose

A professional often has to fill a structured document where most data already exists in the dossier, some must be retrieved, and some is genuinely uncertain. Doing it by hand is slow and error-prone; doing it blindly with AI is dangerous because the document may commit the professional externally.

This workflow answers:

```text
From what a dossier knows, prepare a filled document:
find where to look, verify, retrieve, fill what is sure,
ask where there is doubt, document every source, and save —
producing a draft the human checks and signs, never a submission.
```

The CERFA (permis de construire, déclaration préalable, autorisation de travaux ERP, permis d'aménager) is the first instance. The rule is generic: any administrative form benefits from the same governed filling.

## Core rule

```text
The system fills and proposes. It never decides, submits or signs.
Every field carries its source and a confidence status.
Where it is unsure, it asks. Where it fills, it cites.
The output is an annotated draft. The human verifies and signs.
```

This is a high-consequence workflow: a wrong administrative form has legal, urban-planning and liability effects. External submission and signature are always the human's act, at the highest approval level.

## A document is a claim ledger

The mechanism that makes this governable: each field is a claim with an origin and a status (the claim ledger of `EVIDENCE_PACK.md`).

| Field status | Where the value came from | What the system does |
|---|---|---|
| `known` | a known dossier record (core records / project data) | fill, marked reliable |
| `retrieved` | found on an authorized source | fill + cite the source and its date |
| `inferred` | deduced (e.g. surfaces → housing vs commerce) | fill + comment "to verify" |
| `unverified` | genuine doubt, nothing reliable found | do not fill → ask (User Decision Gate) |
| `entity_to_confirm` | a contact/company found but identity not certain | propose + "confirm this is the right entity" |
| `conflicting` | two sources disagree | surface both, do not pick → ask |
| `to_reconfirm` | a reused dossier fact past its review date | pre-fill but flag for reconfirmation |
| `superseded` | a newer source/rule re-opened a previously filled field | keep history, re-ask |

The rendered draft turns these statuses into inline comments: "known", "source X, to verify", "to fill", "confirm entity". These are the places the human must check.

## The per-field resolution loop with fallback

For each field the system runs a bounded resolution loop. This is the part the user emphasized: try, and if it fails or is uncertain, try another way, then ask — always documenting.

```text
1. Is it known in the dossier?           -> known, fill, cite the record
2. If not, which authorized source?      -> classify the field's domain
3. Retrieve from source A                 -> retrieved, cite source + date
4. If not found or low confidence:
     try source B (a different authorized source)
5. If still not found or sources conflict:
     do not fill -> ask the human (decision gate / Review Queue)
6. Record the outcome on the field:
     value, status, source(s) tried, source(s) used, date, note
7. Save the partial result (resumable; never lost)
```

Rules that bound the loop:

```text
A fallback is another authorized source, not a guess.
A retry must change source or method, not invent a value.
After the allowed sources are exhausted, the answer is "ask", never "assume".
Every attempt — success or failure — is recorded on the field.
```

## Finding the form itself

The earlier sections assume the form is known. It is not always. Before filling, the
workflow must obtain the right form and its current version. A form is either:

```text
provided   -> a template in the dossier's form library (the user supplies it)
discovered -> found on an authorized source, by subject and phase
```

Resolution order:

```text
1. Is the form template provided in the dossier / a supplied form library?  -> use it
2. If not, identify the required form by subject and phase, then locate the
   official template on an authorized source.
3. Verify it is the current official version (forms are periodically updated):
   record the form id, version and date.
4. If the version cannot be confirmed, mark the form `to_reconfirm`; do not fill a
   form whose version is uncertain without flagging it.
```

```text
A found form is a candidate until its identity and current version are verified.
The latest filename is not proof of the latest official version.
```

This matters for families of related forms grouped by phase — for example public
procurement forms in candidature, attribution and execution phases (DC / ATTRI / EXE
series). The system must identify which form applies to which phase and confirm the
current version on the official source; it must not assume a form's purpose from its
code alone. The concrete catalogue (which code means what, for which phase) lives in
the relevant domain pack, dated and source-verified — not hardcoded here.

## Template sources and formats

A document to produce is not always an official fielded form. It can be a `.docx` or
`.pdf`, with form fields or without, and templates may live in a curated list of sites
the practitioner maintains.

### Template sources

```text
provided template library   -> the practitioner's own templates (the first place to look)
curated template site list  -> a whitelist of sites where blank templates are published
discovery                   -> find a template by subject only when the above fail
```

The template site list is a whitelist, governed like any source (`EXTERNAL_TOOLS_POLICY.md`);
the concrete list of sites lives in the domain pack, dated, not hardcoded here. A
discovered template is a candidate until its identity, currency and source are confirmed.

### The source registry is scoped and AI-enrichable as candidate

The list of sources and template sites follows the same model as dossiers and records
(`SCOPE_ISOLATION.md`, `CORE_RECORDS_MODEL.md`):

```text
general sources  -> shared across the practice (official rule sources, official forms)
project sources  -> bound to one dossier (this commune's local plan, this client's portal)
```

A project source does not leak into the general list; a general source is not narrowed
to one project.

The list is not frozen: the system may propose new sources. But adding a source to the
trusted list expands what the system queries and believes — a trust-boundary change,
therefore consequential.

```text
The AI proposes a source. The human validates it. Only the validated is trusted.
A proposed source is a candidate (surfaced via the Review Queue); it is never added silently.
A validated source carries its scope (general or project) and a review-after date;
past that date it returns as to_reconfirm.
A bad source added silently is industrialized false truth — hence: proposing is not trusting.
```

Promotion of a source from candidate to trusted, and broadening a project source to
general, are governed decisions (`APPROVALS.md`), not automatic.

### Format does not change the model, only the risk

The field-as-claim model is identical whatever the format. What changes is how values
are placed and how much must be verified.

```text
fielded   (docx content controls / PDF AcroForm)  -> field names are explicit -> safer
flat      (docx or PDF with no form fields)        -> placement must be inferred -> riskier
```

For a flat template the system must establish a field map — where each governed value
goes. That map is itself a candidate: established once (by template analysis or by the
human), verified, then reusable for that template. A value placed by inferred position
carries a stronger "to verify" flag than a value placed in a named field.

```text
A template without fields is allowed; it is not trusted blindly.
The field map of a flat template is a candidate, verified once, then reused.
The actual docx/PDF reading and writing is an adapter (execution runtime), not Pantheon.
```

## Where to look — the authorized source policy

Which source is allowed for which kind of fact is governed (`EXTERNAL_TOOLS_POLICY.md`); the actual connectors are adapters. The source list is a whitelist first; broaden only with authorization, marking the broader source as lower trust.

Generic source roles (named products belong in the domain pack / bindings, not here):

```text
dossier records            -> known project data, the first place to look
official rule source       -> what document is required, field meaning, thresholds (dated)
official geodata source    -> facts derived from an address (parcel, zone, constraints)
entity registry source     -> company / organization identity, with mandatory verification
contact source             -> internal contact list, then an external contact source
```

A field's domain decides the source order. A regulatory threshold is checked on the official rule source; an address-derived fact on the official geodata source; a company identity on the entity registry, verified.

## Mandatory guardrails

```text
1. Identity verification before keeping a contact or company:
   an external registry may return a near-match. Keep it as entity_to_confirm
   until the right identity (e.g. the right registration number) is confirmed.
2. Dated source for any regulatory value:
   rules change; a threshold or requirement must record the source and its date.
3. No submission, no signature, ever:
   the output is a draft. Filing and signing remain entirely human.
4. Scope isolation:
   the document is filled only from its own dossier's records and authorized
   sources; no cross-dossier data leaks in (`SCOPE_ISOLATION.md`).
5. Save and resume:
   partial work is saved with every field's provenance; a run can stop at a
   doubt and resume without losing what was found.
6. Pre-transmission minimization:
   when querying an external source, send only the minimum needed for that lookup
   (e.g. an address to a geodata source, a name to an entity registry). Do not push
   the whole dossier or unrelated personal data to a third-party source.
```

## Output shape (governed)

```text
filled_document_candidate:
  document_type            # which form/CERFA, classified and source-checked
  scope_id                 # the dossier
  classification:
    selected
    reason
    source_checked         # the official rule source confirming the choice
    status                 # candidate until human-confirmed
  fields:
    - field_id
      value
      status               # known | retrieved | inferred | unverified | entity_to_confirm | conflicting
      sources_tried
      source_used
      source_date
      comment              # the inline "to verify / to fill" note
  open_questions           # everything that needs the human
  attachments_expected     # supporting pieces the form requires
  status: candidate        # nothing is submitted; a draft to verify and sign
  render: annotated PDF/markdown, downloadable
```

## The flow end to end

```text
1. The user asks for a document on a dossier ("prepare the CERFA for project X", "prepare the DC2 for this tender").
2. Classify which document is required; verify the choice on the official rule source; if in doubt, ask.
3. Obtain the form: use the provided template if any, else locate the official one by subject and phase; confirm its current version (date it); if the version is uncertain, flag it.
4. For each field, run the resolution loop with fallback (known -> source A -> source B -> ask).
5. Verify entities; date regulatory values; surface conflicts; run the cross-field consistency pass.
6. Fill tables (e.g. housing vs commerce, surfaces; or tender lots/amounts) from dossier records.
7. Produce the filled-document candidate: annotated, downloadable, with inline comments and a completeness summary.
8. Save with full provenance (resumable); confirmed fields become reusable dossier facts for later documents.
9. The human verifies, completes the asked fields, and signs. Filing stays human.
```

## Modular decomposition into skills

This workflow is not one skill. It is a composition of small, reusable skills, each
declaring a manifest and speaking the envelope (`MODULAR_DOMAIN_REORIENTATION.md`).
The skills are reusable far beyond forms (a source retriever or an entity verifier
serves many workflows).

| Skill | Single job | Reused by |
|---|---|---|
| classify-document | which document is required; verify on the official rule source | any administrative act |
| fetch-form-template | obtain the right template (provided / curated site / discovered), detect its format (docx/pdf, fielded/flat), confirm version, and yield a field map (explicit or inferred candidate) | any form or reusable document, fielded or flat |
| resolve-known | read known values from dossier records | any pre-fill |
| retrieve-source | query ONE authorized source for a field's domain | research, analysis, verification |
| verify-entity | confirm a company/contact identity (right registration number) | contracts, contacts, invoices |
| fill-fields | attach value + status + source to each field | any form |
| raise-doubt | turn an uncertain field into a question (decision gate / Review Queue) | everywhere |
| render-annotated | produce the annotated PDF/markdown with inline comments | any annotated deliverable |
| save-provenance | persist each field's origin (append-only) | everywhere |

Modularity rules (from `MODULAR_DOMAIN_REORIENTATION.md`), applied here:

```text
1. Skills never call each other directly. fill-fields does not call retrieve-source.
   Everything passes through the envelope; the composition orchestrates, the skills
   ignore each other.
2. Each skill returns candidates, not truths: retrieve-source returns
   "value + source + confidence", not "the answer".
3. Graceful degradation: retrieve-source unavailable -> the field becomes unverified
   -> raise-doubt. No silent break.
4. Each skill carries its own risk and approval level in its manifest: retrieve-source
   is read-only/low; submission is never permitted.
```

Reasoning topology: this is a fan-out then synthesis (`EVIDENCE_TOPOLOGY_GATE.md`).
Fields resolve in parallel (independent retrieve-source / verify-entity calls), then
fill-fields synthesizes the document. The decomposition follows a governed topology,
it is not just a convenience.

The composition that sequences these skills is a Workflow Manifest
(`WORKFLOW_SCHEMA.md`), not a hidden runtime. It is governed declaration; execution of
each skill happens in the execution runtime under a Task Contract.

## Placement

| Concern | Layer |
|---|---|
| Field-as-claim, resolution loop, source policy, guardrails, output shape | Pantheon (this document) |
| Which document, which fields, which source order per field type | domain pack (e.g. architecture: the CERFA set) |
| The whitelist of concrete sources and credentials | `EXTERNAL_TOOLS_POLICY.md` + adapters |
| Actual retrieval, entity check, PDF fill, contact sync | adapters outside Pantheon (execution runtime) |
| Showing the draft, asking questions, download, signature | exposure surface |
| Doubts surfaced as decisions | `USER_DECISION_GATE.md`, `REVIEW_QUEUE.md` (candidate) |
| Saved provenance per field | core records + append-only events (`CORE_RECORDS_MODEL.md`) |

Pantheon owns the method and the field-level discipline. It does not retrieve, fill a PDF or call an API.

## Cross-field consistency

Filling field by field is not enough: a form is coherent or it is wrong. After the
per-field loop, a consistency pass checks relationships across fields before the draft
is produced.

```text
totals reconcile (e.g. sum of areas = declared total)
counts agree (e.g. number of housing units vs the units table)
a destination is consistent (housing vs commerce vs mixed) across all fields that imply it
dates are ordered (e.g. acquisition before request)
a value retrieved from a source does not contradict a known dossier value
```

A detected inconsistency does not get auto-resolved. It becomes a `conflicting` flag
and a question, exactly like a per-field doubt. Consistency is checked, never forced.

## Reuse across documents

A dossier produces many documents over time (several CERFA, notices, declarations).
A value confirmed once should not be re-asked blindly on the next document.

```text
A field validated by the human becomes a reusable dossier fact, scoped to the dossier.
A later document pre-fills from that fact as `known`, and shows when it was confirmed.
A reused fact past its review-after date returns as `to reconfirm`, not silently trusted.
A regulatory value is reused only with its date; a newer rule re-opens it.
```

This connects to `CORE_RECORDS_MODEL.md` (project facts) and `MEMORY.md`: reuse is
governed, dossier-scoped, and never turns one document's answer into global truth.

## Completeness and submission readiness

Before the draft is handed back, the workflow states how complete it is — it never
implies readiness it cannot support.

```text
required fields filled vs missing
required attachments present vs expected
fields still unverified or conflicting
entities still to confirm
=> a readiness summary: draft | incomplete | needs-human-input
```

```text
Readiness is described, not asserted.
The system never reports a form as ready to file. Filing readiness is the human's judgement.
```

## Failure and unavailability

Sources fail, time out or rate-limit. That is a normal state, not an error to hide.

```text
A source that fails or times out is recorded as attempted-unavailable on the field.
The field falls back to the next source, then to "ask"; it is never left silently blank.
A source returning an unexpected shape is treated as no-result, not as a value.
The run remains resumable: a later attempt can complete the unavailable fields.
```

## Relation to existing doctrine

- `EVIDENCE_PACK.md` — the field-as-claim ledger and source discipline.
- `USER_DECISION_GATE.md` / `REVIEW_QUEUE.md` — how doubts are surfaced for human resolution.
- `EXTERNAL_TOOLS_POLICY.md` — which sources are authorized and how; whitelist-first.
- `CORE_RECORDS_MODEL.md` — where known data comes from and where provenance is saved.
- `SCOPE_ISOLATION.md` — the document is filled only within its dossier scope.
- `AGENCY_DOMAIN_PACK.md` (candidate) — the architecture instance: CERFA set and per-field source order.
- `MARKDOWN_DOSSIER_WORKFLOW.md` — the annotated-draft and inline-comment pattern.

## Boundary phrase

```text
Find where to look. Verify. Fill what is sure. Ask what is not.
Document every source. Save the work.
The draft is the system's. The signature is the human's.
```
