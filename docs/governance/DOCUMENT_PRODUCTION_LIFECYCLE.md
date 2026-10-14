# Pantheon Next — Governed Document Production Lifecycle

Status: candidate support doctrine — documented non-implemented.
Boundary profile: candidate_support_note.

This document complements `DOCUMENT_LIFECYCLE_GOVERNANCE.md` with the reverse path: producing a document from heterogeneous source material rather than only ingesting an already formed document.

It covers candidate production from:

- a list of notes;
- a scanned handwritten or printed draft;
- a voice recording or dictated account;
- a meeting transcript;
- pasted text;
- excerpts selected from existing documents;
- project context;
- Knowledge references;
- corrections supplied over several turns;
- a request to insert or replace text in an existing document.

It does not implement speech-to-text, OCR, document generation, a text editor, a DOCX/PDF renderer, a queue, a scheduler, a Hermes Skill, a Cockpit UI, an approval engine, an archive service or a document management system.

```text
Source material is captured.
Hermes may transcribe, understand, organize and draft.
The Cockpit exposes the draft, sources, gaps and corrections.
Pantheon governs status, scope, classification and release conditions.
The human reviews before sectorization and archiving.
```

## 1. Purpose

Document production is distinct from source ingestion.

```text
ingestion
= derive consultable representations from an existing source

document production
= compose a new candidate document from one or more source materials and instructions
```

The produced document may later enter the ordinary document lifecycle, but it must not be treated as an original external source merely because it has been rendered as a PDF or DOCX.

The production path must answer:

```text
Which notes, scans, recordings, texts and source documents were used?
What did the user ask to produce?
What did Hermes understand about purpose, audience and format?
Which statements came directly from a source?
Which passages were synthesized, reformulated or inferred?
What information is missing or uncertain?
Which draft version was reviewed?
Who requested corrections?
Who approved the content for classification?
Where was the reviewed document sectorized?
Which reviewed version was archived or distributed?
```

## 2. Non-equivalence rules

```text
notes collected != document drafted
audio transcribed != speaker attribution verified
scan OCR completed != handwritten content verified
text inserted != insertion context validated
draft generated != content reviewed
content reviewed != externally approved
draft exported to PDF != archived document
destination proposed != sectorization approved
classified != archived
archived != distributed
reviewed document != Evidence by default
```

A generated document remains a candidate until the required review gate is satisfied.

## 3. Production inputs

A production request may combine several input classes.

### 3.1 Notes

Examples:

- bullet-point observations;
- decisions and questions;
- site notes;
- telephone notes;
- corrections made over several turns;
- incomplete phrases;
- unordered facts.

The system must preserve the original note set or a stable reference to it.

### 3.2 Scanned draft

A scanned handwritten or printed draft is a source capture.

The candidate path is:

```text
original scan
-> OCR or document vision projection
-> uncertain passages exposed
-> structured note candidate
-> draft document candidate
```

The scan remains downloadable. OCR text does not replace it.

### 3.3 Voice recording or dictated account

A voice input may be:

- an audio note;
- a dictated report;
- a meeting recording;
- a site visit account;
- a telephone debrief;
- a voice message.

The candidate path is:

```text
original audio
-> transcription projection
-> speaker and timing observations
-> structured facts, decisions and actions candidates
-> document draft
```

Speaker attribution, names, dates, amounts, measurements, technical references and decisions require visible verification when uncertain.

### 3.4 Text to insert

The user may provide a paragraph or instruction for insertion into an existing document.

The request should identify:

```yaml
insertion_request:
  target_document_id:
  target_version_id:
  insertion_anchor:
  supplied_text_or_instruction:
  expected_role: replace | insert_before | insert_after | append | merge_candidate
  preserve_surrounding_structure: true
```

Hermes should return a patch or revised-document candidate rather than silently overwriting the active document.

### 3.5 Existing sources and context

A draft may use:

- project documents;
- general Knowledge;
- selected retrieval passages;
- previous document versions;
- a template;
- a user-supplied structure;
- current project metadata.

Every consequential source contribution should remain traceable.

## 4. Core production objects

The exact names remain candidates until reconciliation with existing schemas and MVP models.

```text
Production Request
Production Source Set
Production Brief
Draft Document
Draft Version
Draft Segment Provenance
Review Record
Correction Request
Release Decision
Sectorization Record
Archive Record
Distribution Record
```

### 4.1 Production Request

```yaml
production_request:
  request_id:
  requested_by:
  requested_at:
  purpose:
  document_type_candidate:
  intended_audience:
  requested_format:
  requested_language:
  source_refs: []
  project_context_refs: []
  knowledge_context_refs: []
  template_ref:
  user_instructions:
```

Examples of requested outputs:

- compte rendu de réunion;
- compte rendu de chantier;
- note de synthèse;
- courrier;
- notice;
- rapport;
- texte à insérer dans un document;
- fiche technique;
- brouillon de contrat;
- liste d’actions;
- relevé de décisions.

### 4.2 Production Source Set

```yaml
production_source_set:
  source_set_id:
  request_id:
  source_items:
    - source_ref:
      source_role:
      extraction_or_transcription_ref:
      access_scope:
      review_status:
```

The set preserves the distinction between:

- original material;
- transcription or OCR projection;
- retrieved context;
- user instruction;
- template;
- prior draft.

### 4.3 Production Brief

Hermes may first reformulate the requested document before drafting.

```yaml
production_brief:
  brief_id:
  request_id:
  understood_purpose:
  intended_audience:
  proposed_document_type:
  proposed_structure: []
  facts_to_preserve: []
  decisions_to_preserve: []
  actions_to_preserve: []
  uncertainties: []
  missing_information: []
  proposed_output_formats: []
  review_points: []
  created_by_binding:
  binding_version:
  review_status:
```

The brief is especially useful when the inputs are unordered, handwritten, spoken or incomplete.

```text
Hermes reformulation != final instruction
proposed structure != approved structure
missing information exposed != permission to invent
```

### 4.4 Draft Document and Draft Version

```yaml
draft_document:
  draft_document_id:
  request_id:
  title_candidate:
  document_type_candidate:
  status: drafting | review_required | corrections_requested | reviewed | rejected

draft_version:
  draft_version_id:
  draft_document_id:
  version_number:
  content_ref:
  content_hash:
  created_at:
  created_by_binding_or_actor:
  supersedes_version_id:
  review_status:
```

Every material regeneration or correction creates a new version.

A previous version is not silently overwritten.

### 4.5 Draft Segment Provenance

Where useful, the draft should retain segment-level provenance.

```yaml
draft_segment_provenance:
  draft_version_id:
  segment_id:
  source_refs: []
  transformation: quoted | transcribed | normalized | summarized | synthesized | inferred
  uncertainty:
  verification_required:
```

This is particularly important for:

- meeting decisions;
- contractual statements;
- amounts;
- dates;
- measurements;
- responsibilities;
- regulatory assertions;
- technical prescriptions.

## 5. Candidate production flow

```text
capture source materials
-> transcribe or OCR when required
-> preserve raw projections and uncertainty
-> prepare Production Brief
-> user correction when the brief is materially ambiguous
-> generate Draft Version
-> expose draft, provenance, gaps and warnings
-> human review
-> corrections and new Draft Version when required
-> explicit reviewed status
-> sectorization decision
-> classification into project, Knowledge or another allowed sector
-> archive or distribution decision
-> create final immutable output capture when required
```

The flow may be shorter for a simple low-risk paragraph, but the final classification and archive rule remains explicit for a produced document.

## 6. Mandatory review before sectorization and archiving

A produced document requires human review before it can be sectorized or archived as a finalized document.

In this document, `sectorization` means the consequential assignment of the reviewed output to an organizational destination, for example:

- one or more projects;
- a project phase;
- general Knowledge;
- a Knowledge family;
- a document type or operational sector;
- a contractual or delivery corpus;
- another governed classification perimeter.

The mandatory sequence is:

```text
draft generated
-> review required
-> reviewed or corrections requested
-> reviewed version selected
-> sectorization authorized
-> archive authorized
```

Forbidden shortcuts:

```text
draft generated -> project archive
draft generated -> Knowledge publication
draft generated -> contractual folder
draft generated -> distributed final PDF
Hermes says complete -> reviewed
export succeeded -> archive authorized
```

The review must operate on an exact draft version identified by hash or version identifier.

```yaml
review_record:
  review_id:
  draft_version_id:
  reviewer:
  reviewed_at:
  decision: accepted | corrections_required | rejected
  comments: []
  unresolved_items: []
```

If corrections are required, the corrected version must receive its own review status. Approval of version 2 does not automatically approve version 3.

## 7. Sectorization

Sectorization occurs only after review.

```yaml
sectorization_record:
  sectorization_id:
  reviewed_draft_version_id:
  destination_type: project | knowledge | project_and_knowledge | other_governed_sector
  project_links: []
  project_phase_by_link: {}
  knowledge_family:
  document_type:
  title:
  filename_candidate:
  authorized_by:
  authorized_at:
```

For project documents:

- the flat phase structure remains applicable;
- no mandatory subfolder is introduced;
- the final filename rule applies at classification time;
- one reviewed output may link to several projects without duplicating the logical document;
- a rendered final binary may be stored once and referenced from several links where policy permits.

For Knowledge:

- the produced item remains visibly derived;
- its source set and draft lineage remain accessible;
- publication does not promote it to Evidence or durable memory;
- confidential project sources remain permission-gated.

## 8. Archiving

Archiving is a separate decision from sectorization.

```text
reviewed != archived
sectorized != archived
archived != distributed
```

An Archive Record should identify the exact reviewed output:

```yaml
archive_record:
  archive_id:
  reviewed_draft_version_id:
  final_output_source_id:
  archive_destination:
  archive_policy_ref:
  archived_by:
  archived_at:
  content_hash:
  supersedes_archive_id:
```

The archive may contain:

- reviewed Markdown;
- generated DOCX;
- generated PDF;
- another approved final format;
- source attachments where policy requires them.

Rendering a format is an external execution step. Pantheon governs which reviewed version may be rendered and archived; it does not render the file itself.

An archived version is immutable. A later correction creates a new reviewed version and a new archive record. It does not silently replace the previous archive.

## 9. Distribution

External distribution remains distinct from review, sectorization and archiving.

```yaml
distribution_record:
  distribution_id:
  archive_id:            # present when the sent output was archived first
  exact_output_ref:      # required when archive_id is absent, so the sent version stays auditable
    document_version:    # exact index / version that was authorized and sent
    content_hash:        # hash of the rendered artifact actually sent
    rendered_artifact_ref:
  recipients_or_channel:
  distribution_scope:
  authorized_by:
  distributed_at:
  external_trace_ref:
```

At least one of `archive_id` or `exact_output_ref` must identify the exact reviewed version and rendered artifact that was authorized and sent. When Gate G authorizes distribution of an exact reviewed output without archiving it first, `exact_output_ref` (version + hash) keeps the transmission trace auditable.

```text
reviewed != authorized to send
archived != sent
distribution requested != distribution completed
```

Sending, publishing or transmitting a document is an external effect and follows the applicable approval gate.

## 10. Voice account and meeting-report specialization

For a voice-based account or meeting report, the candidate production profile should distinguish:

- verbatim or near-verbatim transcription;
- normalized notes;
- participants and speaker attribution candidates;
- decisions;
- actions;
- owners;
- deadlines;
- reservations;
- questions;
- factual uncertainties;
- passages not understood.

Candidate flow:

```text
voice source
-> transcription
-> structured meeting facts candidate
-> Production Brief
-> account or minutes Draft Version
-> synchronized access to audio/transcript where permitted
-> human review
-> sectorization
-> archive
```

Review is mandatory before a voice-derived report is classified or archived because transcription and synthesis may change names, negations, dates, amounts, technical references, speaker attribution or decision status.

## 11. Scanned-draft specialization

For a scanned draft:

```text
scan original
-> OCR or document vision
-> low-confidence spans marked
-> structure candidate
-> Draft Version
-> comparison with scan
-> human review
-> sectorization
-> archive
```

The Cockpit should allow side-by-side consultation of the original scan and the generated text when the runtime provides page or region alignment.

An unreadable passage must remain marked. Hermes must not silently invent missing text.

## 12. Text insertion specialization

A text insertion request produces a patch candidate or new draft version.

The Cockpit should expose:

- target document and version;
- insertion anchor;
- original surrounding text;
- proposed inserted text;
- resulting local context;
- warnings about duplication, contradiction or structural break;
- exact diff.

The insertion is reviewed before it becomes the active reviewed version.

For a minor, non-consequential internal draft, a policy may allow immediate insertion into a new unreviewed version. That version still cannot be sectorized as final or archived without review.

## 13. Cockpit experience

The primary Cockpit actions may remain simple:

```text
Créer un document
Ajouter des notes
Ajouter un scan
Ajouter un enregistrement vocal
Ajouter un texte
Choisir un document cible
Demander à Hermès de reformuler
Générer un brouillon
Relire
Demander des corrections
Valider la version relue
Sectoriser
Archiver
Distribuer
```

Suggested production card:

```text
Document en préparation

Objet : Compte rendu de réunion de chantier
Sources : 8 notes, 1 enregistrement vocal, 2 documents projet
État : relecture requise
Version : 3
Points à vérifier : 4
Destination proposée : Projet Verger — 50_Chantier
Archivage : bloqué jusqu’à validation

[Voir le brouillon] [Comparer aux sources] [Corriger] [Valider la relecture]
```

The Cockpit may display Hermes progress using the observation rules from `DOCUMENT_LIFECYCLE_GOVERNANCE.md`.

It must not present a completed generation run as a reviewed document.

## 14. Hermes execution boundary

Candidate Capability Slot:

```yaml
capability_slot: governed_document_production
abstract_function: >-
  transform heterogeneous captured material and bounded context into a versioned
  document draft with visible provenance, gaps and review requirements.
candidate_binding:
  executor: Hermes
  skill: pantheon-document-production
implementation_status: documented non-implemented in Pantheon Next
installation_status: not installed by this document
activation_status: not authorized by this document
```

Candidate Skill operations:

```text
inspect_production_sources
transcribe_audio
run_ocr_or_document_vision
prepare_production_brief
structure_notes
draft_document
revise_draft
apply_text_patch_candidate
render_output_candidate
get_run_status
request_cancel
```

Hermes may execute these operations under a bounded request.

Hermes must not:

- mark its own draft reviewed;
- authorize sectorization;
- archive a draft as final;
- distribute a document without the applicable gate;
- invent missing information silently;
- hide source uncertainty;
- overwrite a reviewed or archived version silently.

## 15. Pantheon governance boundary

Pantheon governs:

- source and instruction scope;
- production purpose and destination posture;
- review-required status;
- version lineage;
- source and segment provenance expectations;
- missing-information and uncertainty visibility;
- sectorization eligibility;
- archive eligibility;
- distribution approval requirements;
- final-output identity and rollback visibility.

Pantheon does not:

- transcribe audio;
- run OCR;
- synthesize text;
- edit documents;
- render DOCX or PDF;
- store runtime queues;
- schedule generation;
- send the document;
- approve the content automatically.

## 16. Gates

### Gate A — Production sources acceptable

Checks:

- source capture and access;
- integrity;
- confidentiality;
- allowed context;
- transcription or OCR posture;
- source-set completeness.

### Gate B — Production Brief sufficient

Checks:

- purpose;
- audience;
- document type;
- expected structure;
- missing information;
- verification points;
- no silent scope expansion.

### Gate C — Draft reviewable

Checks:

- exact Draft Version;
- non-empty content;
- source and transformation trace where required;
- warnings and uncertainties visible;
- requested sections present;
- no unresolved rendering or extraction failure hidden.

### Gate D — Human review completed

Checks:

- exact version reviewed;
- named or authenticated reviewer according to policy;
- decision recorded;
- unresolved items handled or explicitly accepted;
- corrected versions re-reviewed.

This gate is mandatory before sectorization and archiving.

### Gate E — Sectorization authorized

Checks:

- Gate D passed;
- destination explicit;
- project links and phases explicit;
- Knowledge family explicit where applicable;
- title, type and filename candidate coherent;
- permissions valid;
- duplicate or conflict posture visible.

### Gate F — Archive authorized

Checks:

- exact reviewed version;
- final render hash;
- archive destination;
- retention policy;
- supersession link;
- no silent replacement.

### Gate G — Distribution authorized

Checks:

- archive or exact reviewed output selected;
- recipients or channel;
- confidentiality;
- external-action approval;
- transmission trace expectation.

## 17. Status model

Candidate orthogonal dimensions:

```yaml
production_status:
  source_preparation: pending | ready | incomplete | failed
  brief_status: pending | proposed | corrected | accepted
  generation_status: pending | running | succeeded | failed
  review_status: required | corrections_requested | accepted | rejected
  sectorization_status: blocked | pending | authorized | applied
  archive_status: blocked | pending | archived | superseded
  distribution_status: not_requested | pending_approval | authorized | sent | failed
```

The UI should state the blocking reason plainly.

Example:

```text
Sectorization blocked: draft version 3 has not been reviewed.
Archiving blocked: no reviewed version selected.
Distribution blocked: external-action approval absent.
```

## 18. Repository placement

### Pantheon Next

Owns:

- this candidate governance model;
- distinctions between source, draft, review, sectorization, archive and distribution;
- gates and conformance expectations.

### `ifanjuang/pantheon-mvp`

Candidate executable ownership:

- Cockpit production UI;
- draft and review persistence;
- source-set display;
- version diff;
- sectorization and archive request surfaces;
- OpenWebUI integration;
- end-to-end product scenarios.

### Hermes-side executable runtime

Candidate executable ownership:

- transcription;
- OCR and document vision;
- note structuring;
- drafting and revision;
- patch generation;
- rendering adapters;
- progress and output manifests.

## 19. Delivery sequence

### Phase 0 — reconciliation

- inspect existing document-generation, editor, version and archive models;
- identify existing template and document-output capabilities;
- avoid creating a parallel draft/version model where an owner already exists.

### Phase 1 — notes and text draft

- Production Request;
- source set;
- Production Brief;
- Markdown Draft Version;
- mandatory review status;
- no archive or distribution.

### Phase 2 — scanned draft and voice

- scan OCR or document vision adapter;
- audio transcription adapter;
- uncertainty display;
- source comparison;
- review gate.

### Phase 3 — sectorization and archive

- reviewed-version selection;
- project and Knowledge destinations;
- final filename and phase;
- immutable archive record;
- no silent replacement.

### Phase 4 — text insertion and document revision

- target-version anchor;
- patch candidate;
- exact diff;
- new Draft Version;
- re-review when material.

### Phase 5 — output rendering and distribution

- DOCX/PDF or other rendering bindings;
- final output hash;
- archive binding;
- separately approved distribution action.

## 20. Acceptance criteria

The candidate model is coherent when:

1. a user can request a document from notes, scan, voice, text or existing sources;
2. every original material remains preserved or referenced;
3. transcription and OCR remain derived projections;
4. Hermes may reformulate purpose and structure before drafting;
5. missing information and uncertainty remain visible;
6. every material correction creates a new Draft Version;
7. a generated draft cannot mark itself reviewed;
8. human review is mandatory before sectorization;
9. human review is mandatory before archiving;
10. the exact reviewed version is identified;
11. sectorization can target one or more projects or general Knowledge;
12. project phases remain flat without mandatory subfolders;
13. archival identity is content-addressed and non-destructive;
14. distribution remains a separate external action;
15. a voice-derived account exposes transcription and attribution risks;
16. a scanned draft exposes unreadable or low-confidence passages;
17. text insertion produces a patch or new version rather than silent overwrite;
18. Cockpit generation progress does not imply review completion;
19. Pantheon remains governance rather than editor, renderer, archive service or sender;
20. executable production behavior remains external.

## 21. Final decision candidate

```text
Pantheon may govern the production of a document from notes, scans, voice,
existing sources or supplied text without becoming the document-production runtime.

Hermes may understand the request, transcribe, structure, draft and revise through
bounded external capabilities.

Every generated document remains a versioned draft until an exact version has been
reviewed by a human.

No produced document may be sectorized, classified as final or archived before that
review. Archiving and external distribution remain separate governed decisions.
```
