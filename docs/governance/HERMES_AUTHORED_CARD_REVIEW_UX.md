# Pantheon Cockpit — Hermes-Authored Card Review UX

Status: candidate support specification — documented non-implemented.
Boundary profile: candidate_support_note.

This document defines a transverse Cockpit review mode for any content-bearing card whose primary content was authored, rewritten, synthesized, expanded or materially reorganized by Hermes.

It complements:

- `DOCUMENT_PRODUCTION_LIFECYCLE.md`;
- `DOCUMENT_LIFECYCLE_GOVERNANCE.md`;
- `HERMES_PROGRESS_ERROR_RETRY_UX.md`;
- `CARD_STACK_MODEL.md`;
- `PANTHEON_COCKPIT_UX_SPEC.md`;
- `KNOWLEDGE_NAVIGATION_UX.md`;
- `docs/domain-packs/architecture/PROJECT_NAVIGATION_UX.md`;
- `ITERATIVE_DELIBERATION_LIFECYCLE.md`;
- `WORK_ISSUE_AND_DELEGATED_MERGE_MODEL.md`;
- `HERMES_INTEGRATION.md`.

It does not implement a card component, editor, comment system, review engine, workflow engine, queue, scheduler, Hermes Skill, archive service, chunker, embedding model, vector store, database migration or external action.

```text
Hermes may author and revise.
The Cockpit exposes the complete draft and captures corrections.
Pantheon governs version, review, finalization and archive conditions.
The human validates one exact version.
```

## 1. Trigger

The full Draft Card mode applies when Hermes materially contributes to the primary retained content.

### 1.1 Faithful transformation

The following operations do not by themselves trigger the full editorial Draft Card mode:

- OCR;
- transcription;
- format conversion;
- Markdown conversion;
- lossless or near-lossless normalization;
- layout reconstruction;
- section detection;
- chunking;
- embeddings;
- sectorization or folder assignment;
- extraction of explicitly present metadata.

These operations may still require extraction-quality review when confidence is low or the source is consequential.

### 1.2 Material Hermes authorship

The Draft Card mode is triggered when Hermes performs one or more of the following on the retained primary payload:

- drafts a new text;
- rewrites or reformulates substantially;
- synthesizes several sources;
- adds explanatory material;
- develops incomplete notes;
- enriches or expands sections;
- inserts authored passages;
- semantically merges material;
- reorganizes the content in a way that may change interpretation;
- produces conclusions, recommendations, actions or structured narrative;
- converts voice or rough notes into a professional document rather than only a transcript.

```text
OCR completed != Hermes-authored draft
Markdown normalized != Hermes-authored draft
summary written by Hermes = Hermes-authored content
meeting report drafted from a transcript = Hermes-authored content
```

## 2. Transverse Draft Card state

The Draft Card is a temporary state that may apply to multiple card families.

Examples:

- Knowledge card;
- project document card;
- report card;
- notice card;
- meeting-minutes card;
- letter card;
- technical note card;
- method or resource card when its retained text was authored by Hermes.

It is not a permanent visual family.

```text
ordinary card
-> Hermes-authored change requested
-> draft index created
-> Draft Card state
-> review and revisions
-> exact validation
-> finalization
-> ordinary card state restored
```

## 3. Surfacing and priority

A Draft Card must be surfaced before ordinary cards in an `À relire` stack or equivalent priority area.

The primary state is plainly visible:

```text
BROUILLON
```

The card must not be visually mistaken for a finalized document merely because generation completed.

Recommended priority order:

```text
errors blocking review
-> drafts awaiting user review
-> drafts with Hermes revision in progress
-> validated drafts awaiting finalization
-> ordinary cards
```

## 4. Recto

The recto provides a concise review identity.

Candidate fields:

- persistent `BROUILLON` label;
- title;
- card or document type;
- target public index;
- working draft revision;
- `Rédigé avec Hermès` marker;
- last modification date;
- number of open comments;
- source count;
- intended project, phase, Knowledge folder or other destination;
- blocking reason;
- review status;
- current Hermes progress or error state when applicable.

Example:

```text
BROUILLON

Compte rendu de chantier — Verger
Indice A · Brouillon v3
Rédigé avec Hermès

5 sources · 2 commentaires ouverts
Destination : 50_Chantier

Validation requise avant archivage et indexation
```

## 5. Verso or detailed view

The verso or detailed view exposes the complete document, not only an excerpt.

Required capabilities:

- read the full content;
- navigate headings and sections;
- edit text directly;
- select text and comment;
- comment on a section, table, paragraph, sentence or insertion point;
- compare against sources where available;
- compare versions;
- display unresolved warnings and uncertain passages;
- display source and segment provenance where required;
- request Hermes revision;
- validate an exact version.

The interaction must not depend on hover.

Desktop may use an explicit flip or two-panel surface. Mobile may use tabs, a dedicated full-screen view or a details sheet.

## 6. Direct edits

A direct human edit creates a new Draft Version.

```text
Indice A · Brouillon v3
-> human edit
-> Indice A · Brouillon v4
```

The prior version remains available.

A validation of v3 does not validate v4.

Candidate edit record:

```yaml
human_edit:
  edit_id:
  card_id:
  index_id:
  base_draft_version_id:
  resulting_draft_version_id:
  editor:
  edited_at:
  diff_ref:
```

## 7. Comments and Hermes revision requests

The Cockpit exposes a `Commenter` action.

Candidate request types:

```text
corriger
améliorer la rédaction
clarifier
raccourcir
développer
ajouter des détails
enrichir cette section
ajouter des exemples
réorganiser
ajouter des sources
vérifier la cohérence
ajouter une réserve
insérer un passage
supprimer un passage
```

A comment may target:

- the complete document;
- a section;
- a paragraph;
- a sentence;
- a table;
- a selected text range;
- an insertion point;
- a missing-section placeholder.

Candidate structured request:

```yaml
revision_request:
  revision_request_id:
  card_id:
  target_index_id:
  base_draft_version_id:
  target_anchor:
  request_type:
  user_comment:
  selected_text:
  allowed_context_refs: []
  forbidden_scope_expansion: true
  requested_by:
  requested_at:
```

Flow:

```text
Cockpit comment
-> structured revision request
-> Pantheon scope and policy checks
-> Hermes bounded revision
-> new Draft Version
-> diff displayed in Cockpit
-> new human review
```

```text
comment sent != revision accepted
Hermes revision completed != reviewed
```

## 8. Version and index model

Two axes remain separate.

```text
public index
= edition intended to become active, archived or distributed

working draft revision
= internal iterations before that index is finalized
```

Example:

```text
Indice A · Brouillon v1
Indice A · Brouillon v2
Indice A · Brouillon v3
Indice A · Validé
Indice A · Finalisé
```

A later modification creates a new index while the current index remains active:

```text
Indice A · Actif
Indice B · Brouillon v1
Indice B · Brouillon v2
Indice B · Validé, finalisation en cours
Indice B · Actif
Indice A · Superseded but retained
```

The index system may be configured by project or document family:

```text
A, B, C
01, 02, 03
Rev.0, Rev.1
P01, P02
another governed nomenclature
```

The active index remains visible in:

- the ordinary card;
- source download metadata;
- archive records;
- chunk metadata;
- embedding manifests;
- retrieval results;
- distribution records.

## 9. Exact validation

Human validation applies to one exact tuple:

```text
card
+ target public index
+ Draft Version
+ content hash
+ declared finalization bundle
```

Candidate record:

```yaml
card_review_decision:
  review_id:
  card_id:
  index_id:
  draft_version_id:
  content_hash:
  decision: accepted | corrections_required | rejected
  finalization_bundle_ref:
  reviewer:
  reviewed_at:
  comments: []
```

A corrected version must be reviewed again.

## 10. Finalization request

After validation, the Cockpit displays:

```text
Indice A validé.
Demande de finalisation envoyée à Hermès.
```

A standard visible finalization bundle may include:

- freeze the validated Markdown;
- render PDF and DOCX;
- apply the approved sectorization;
- archive the final output;
- build chunks;
- generate embeddings;
- publish the index;
- verify retrieval.

Candidate request:

```yaml
finalization_request:
  finalization_request_id:
  card_id:
  index_id:
  validated_draft_version_id:
  validated_content_hash:
  operations: []
  destinations: []
  policy_refs: []
  requested_by:
  requested_at:
```

Distribution remains separate unless explicitly included through an applicable external-action gate.

## 11. Finalization progress, errors and retry

Progress, errors, diagnosis and bounded retry follow `HERMES_PROGRESS_ERROR_RETRY_UX.md`.

When Hermes exposes a measurable unit, the Cockpit displays the reported percentage:

```text
Embeddings — 350 / 1 000 chunks — 35 %
```

When Hermes does not expose a measurable percentage, the Cockpit displays the current step or an indeterminate state without inventing a number.

The Cockpit must show explicit errors and partial success:

```text
Indice A archivé
Embeddings en erreur
Indexation non publiée
```

Hermes may automatically diagnose and retry only within the recorded bounded retry policy. A retry may not silently change the binding, model, provider, execution location, data scope, configuration or installation.

The card remains in Draft or Finalizing appearance until the declared required finalization set completes.

## 12. Ordinary card activation

The card returns to its ordinary family appearance only after the required finalization bundle is verified.

Examples:

```text
Knowledge item
-> neutral card + thick gradient outline

project document
-> ordinary project-accent card
```

The index remains visible after ordinary appearance returns.

Partial completion must remain explicit.

A project policy may declare some operations optional, for example indexing. The required set must be visible before validation.

## 13. Structured-card exception

Project, Contacts and Entreprises cards often contain structured fields rather than one retained authored document.

When Hermes proposes an individual field:

```text
field candidate
-> field-level review
```

The complete Draft Card mode applies when the primary payload is a materially authored textual artifact.

Examples:

```text
Hermes extracts one phone number
-> field review

Hermes drafts a complete project presentation or client-facing report
-> full Draft Card review
```

## 14. Status axes

Candidate axes:

```yaml
card_draft_status:
  authorship: faithful_transformation | hermes_material_authorship
  review: required | corrections_requested | accepted | rejected
  finalization: blocked | pending | running | partial | completed | failed
  appearance: draft | finalizing | ordinary
  active_index:
  target_index:
  working_revision:
```

## 15. Responsibility split

### Cockpit

- surfaces the Draft Card;
- displays the complete content;
- supports direct edits and comments;
- displays diffs, versions, index and progress;
- captures exact validation;
- displays errors and partial finalization;
- does not draft, archive, chunk or embed itself.

### Pantheon

- governs authorship classification;
- governs review requirement;
- records index and version lineage;
- validates the exact tuple and finalization bundle;
- governs sectorization, archive and index publication conditions;
- does not edit or execute the pipeline.

### Hermes

- drafts and revises through bounded requests;
- returns new versions and diffs;
- performs authorized finalization operations;
- reports progress, errors and outputs;
- does not validate its own content;
- does not silently overwrite a version or change scope.

### Human

- reviews the complete content;
- edits or comments;
- validates one exact version;
- decides whether unresolved items are acceptable;
- authorizes a new index when later modification is requested.

## 16. Acceptance criteria

The UX is coherent when:

1. faithful OCR or Markdown conversion alone does not trigger the full Draft Card mode;
2. material Hermes authorship does trigger it;
3. every authored draft is surfaced in an `À relire` stack;
4. the recto exposes index, working revision and blocking state;
5. the complete document is readable in the detailed surface;
6. direct edits create a new version;
7. comments generate structured bounded revision requests;
8. Hermes revisions produce new versions and diffs;
9. validation applies to one exact index/version/hash tuple;
10. the finalization bundle is visible before validation;
11. real progress is displayed when Hermes exposes it;
12. percentages are never fabricated;
13. errors and partial success remain visible;
14. bounded retries cannot silently change execution posture;
15. ordinary appearance waits for required finalization;
16. the active index remains visible and prior indices remain retained;
17. structured cards may use field-level review where appropriate;
18. Pantheon remains governance rather than editor or runtime.

## 17. Final decision candidate

```text
Any card whose retained primary content was materially authored by Hermes is
promoted into a visible Draft Card state before validation.

The recto exposes draft identity, index and review status. The detailed surface
exposes the complete content, direct edits, anchored comments, revision requests,
diffs and exact validation.

After validation, Hermes performs the declared bounded finalization bundle and
reports measurable progress, errors, diagnosis and retry state. The card returns
to its ordinary appearance only after the required finalization steps are
verified. The active public index remains visible and earlier indices remain
retained.
```
