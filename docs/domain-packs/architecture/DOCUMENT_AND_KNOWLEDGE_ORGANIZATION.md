# Architecture Document and Knowledge Organization

Status: candidate support doctrine — implemented as documentation; external document-card slice observed.
Boundary profile: candidate_support_note.

This document records the architecture-agency organization chosen on 2026-07-19 and reconciled on 2026-07-20 for project originals and the reusable Markdown knowledge corpus.

It specializes `KNOWLEDGE_TAXONOMY.md` and `SOURCE_INGESTION_RETRIEVAL_MODEL.md`. The external `ifanjuang/pantheon-mvp` repository now contains a tested candidate for bounded Docling extraction, PostgreSQL/pgvector persistence, strict NAS intake, read-only OpenWebUI Document Cards, versioned Knowledge publication and conflict-safe mobile Markdown editing. That observation does not install, adopt or activate the binding. This document itself creates no NAS folder, moves or renames no file, installs no editor, promotes no memory and authorizes no external action.

```text
Project originals stay on the NAS.
Reusable knowledge is written in Markdown.
Hermes may derive and propose.
Pantheon governs scope and status.
The human decides consequential promotion.
```

## Selected minimal open-source architecture

The selected target keeps one responsibility per component:

```text
OpenWebUI cockpit
├── PostgreSQL + pgvector
│   ├── cards, issues and document metadata
│   ├── structured CCTP content and versions
│   ├── extracted structure and retrieval chunks
│   └── embeddings and metadata-filtered retrieval
├── NAS
│   ├── immutable project originals
│   └── contractual and delivery exports
└── Hermes
    └── invokes the bounded external adapter and Docling
```

The first observed candidate profile contains only:

```text
OpenWebUI read-only cockpit
external Pantheon MVP adapter
PostgreSQL + pgvector
Hermes
Docling / Docling Serve
NAS
```

These components are intended to be self-hosted. The candidate adapter and OpenWebUI Tool are committed and tested but not installed on the agency environment. Docling is the primary document-understanding engine. It performs local extraction, OCR when required, layout analysis, table recovery and structured export. It is not an editor, source store, project classifier, authority service, evidence approver or memory engine.

The following are deferred until a demonstrated need exists:

```text
Yjs + Hocuspocus       real-time simultaneous co-editing
SilverBullet           optional direct Markdown knowledge surface
Tiptap                 future intelligent structured editor
alternative converters corpus-tested fallback only
separate vector store  only if pgvector is measured insufficient
```

Mobile offline editing is implemented only as an external, uninstalled first-slice candidate: a local PWA shell/cache plus an exact-base-version queued-operation protocol. Stale writes remain conflicts. Real-time CRDT collaboration is still not implemented and is not required before simultaneous co-editing becomes a demonstrated need.

## Source-of-truth allocation

```text
project original or signed/distributed export  → NAS
card, issue, metadata and workflow state       → PostgreSQL
structured CCTP working document and versions → PostgreSQL
editorial reusable Knowledge                  → Markdown
large structured referential                  → PostgreSQL
extracted document structure and chunks       → PostgreSQL
vector index                                  → pgvector
future mobile offline working state           → browser-local cache
card                                          → generated projection
```

A CCTP authored in Pantheon uses a structured open document model with stable identifiers for lots, chapters and clauses. Markdown is an exchange or readable projection for this content, not necessarily its canonical editing form. DOCX and PDF exports are placed on the NAS when they become distributed or contractual project documents.

## Minimal persistence rule

Do not create a permanent visible Markdown copy, JSONL file and asset tree for every source by default.

For an ordinary project document:

```text
NAS original
→ Docling extraction invoked by Hermes
→ structured extraction, chunks, provenance and embeddings in PostgreSQL
→ Project Document Card in Pantheon
```

A Markdown file is created only when the result is intentionally published as reusable editorial Knowledge. Temporary conversion artifacts may exist in a bounded rebuildable cache. Large binary assets are retained only when required for consultation, citation or later processing.

The cache identity is based on:

```text
source digest
+ Docling version
+ selected model versions
+ conversion configuration digest
```

An unchanged source and configuration reuse the existing extraction.

## Two separate spaces

The project documentary space and the reusable knowledge corpus must remain distinct.

```text
project document != Knowledge Item
Markdown note != original source
retrieved passage != evidence
indexed content != Registre Probatoire entry
```

A project-specific contract, estimate, CCTP, DPGF, report, notice, study, letter, email export or reception record remains a project source. It does not become reusable knowledge merely because it was converted, indexed or retrieved.

## Project originals on the NAS

The following shallow phase hierarchy is the recommended agency profile when a human wants a common organization:

```text
00_Gestion/
10_Conception/
20_Autorisations/
30_DCE/
40_Marche/
50_Chantier/
60_Reception/
90_Sinistres/
```

This profile is a navigation convention, not a Pantheon requirement. A deployment may keep another existing filesystem organization without blocking Workspace navigation, bounded Hermes access or qualified retrieval. No mandatory subfolder exists inside these phase folders. When this profile is selected, classification may use the phase folder and the filename convention below.

```text
recommended structure != mandatory structure
folder/path != governed identity
unclassified folder != invalid folder
Hermes classification proposal != filesystem mutation
Cockpit Space != required physical root folder
```

Hermes may propose a mapping, classification, rename or move with its basis and affected references. It must not silently apply that proposal. A consequential filesystem mutation follows the applicable authorization boundary.

The selected filename pattern is:

```text
Projet_indice_phase_distributeur_type_objet_date.ext
```

Field meaning:

```text
PROJET         stable project name or code
INDICE         revision such as A1, B1 or B2
PHASE          phase identifier aligned with the folder
DISTRIBUTEUR   agency-defined issuer or distributor identifier
TYPE           document type such as CONTRAT, CCTP, DPGF, NOTICE, ESTIMATIF,
               ETUDE, COURRIER, MAIL, CR, PV or DOE
OBJET          short human-readable subject
DATE           document date in YYYY-MM-DD when known
ext            original file extension
```

Example:

```text
VERGER_B2_DCE_ARC_CCTP_GROS-OEUVRE_2026-10-15.pdf
```

The original file is preserved. Hermes may propose a classification or rename, but must not silently apply it.

## Reusable Markdown knowledge corpus

The recommended agency human-facing corpus profile uses five first-level families:

```text
KNOWLEDGE/
├── Référentiels/
├── Responsabilité/
├── Méthodologie/
├── Techniques/
└── Réglementations/
```

These folders are navigation aids, not required physical Cockpit roots, authority levels, security boundaries or memory states. Another existing organization remains usable; qualification may propose a mapping without silently reorganizing it.

### Référentiels

Stable lookup material, dictionaries, catalogues and nomenclatures.

Examples:

```text
Dictionnaire des plantes.md
Matériaux courants.md
Acteurs d'une opération.md
Phases et livrables.md
Lots de travaux.md
```

A very large referential, such as thousands of plant records, should remain structured data in an external store such as PostgreSQL. Markdown may expose thematic or editorial views; one file per plant is not the default.

### Responsabilité

Contracts, insurance, duties, liability boundaries and jurisprudence.

Examples:

```text
Marché à forfait.md
Responsabilité du maître d'œuvre.md
Assurance dommages-ouvrage.md
Jurisprudence sur les travaux supplémentaires.md
```

### Méthodologie

Ways of working used by the agency across design, estimating, tendering, construction, reception and claims.

Examples:

```text
Préparer un DCE.md
Analyser une offre.md
Conduire une réunion de chantier.md
Organiser une réception.md
Traiter un sinistre.md
```

### Techniques

Construction systems, materials, landscape, building services, domotics and other technical disciplines.

Examples:

```text
Toitures végétalisées.md
Domotique résidentielle.md
Pathologies des enduits.md
Drainage des espaces extérieurs.md
```

A DTU may be referenced here as technical guidance, but the source document and its legal applicability remain explicit. Mandatory requirements belong under Réglementations.

### Réglementations

Mandatory legal, regulatory and administrative rules.

Examples:

```text
Accessibilité des ERP.md
Réglementation environnementale RE2020.md
Autorisations d'urbanisme.md
Règles de sécurité incendie.md
```

## Markdown naming rule

A knowledge note uses a free, natural subject title:

```text
Titre libre du sujet.md
```

No project name, phase, index, distributor, type prefix or date is required.

Default rules:

```text
one useful stable subject per note;
no mandatory subfolder below the five families;
prefer a title a person would naturally search for;
rename the note when its subject changes materially;
split only when a note becomes hard to consult;
merge duplicates only after review.
```

## Source and provenance boundary

A knowledge note may cite a PDF, regulation, contract model, email, study or web source. The source remains separate and superior to the note.

Machine metadata should not clutter the filename. A supporting registry may retain:

```text
source reference;
source digest;
scope and confidentiality;
extraction method and version;
page or section references;
review status;
validity and supersession;
index and embedding references.
```

This metadata is support material. It does not turn the note into evidence or governed memory.

## Candidate ingestion path

When a PDF is supplied for possible knowledge reuse, the bounded path is:

```text
original PDF on NAS or approved source system
→ linked or cached source reference
→ text/OCR/Markdown derivative candidate
→ proposed family and free subject title
→ duplicate, scope and safety checks
→ Markdown Knowledge Item with visible review status
→ optional human review
→ selective indexing or vectorization
```

Hermes may execute extraction, segmentation, classification, publication and retrieval under an explicit bounded handoff. Pantheon governs source scope, status, provenance expectations and gates. A Markdown surface such as SilverBullet may expose the corpus, but no particular product is adopted by this document.

## Optional human validation

Human validation is not required merely to create or publish a Knowledge Item.

An automatically published note should expose one of these review states:

```text
generated_unreviewed;
needs_review;
reviewed;
superseded.
```

Automatic publication is allowed when:

```text
the original source remains preserved;
provenance is retained;
the destination family is declared;
the note does not silently overwrite or merge an existing note;
the note remains Knowledge rather than Evidence or governed memory.
```

Human review is required before:

```text
destructive replacement or semantic merge;
promotion to Evidence or the Registre Probatoire;
consequential reliance on contractual, legal, regulatory or safety content;
external action based on the extracted content.
```

A `generated_unreviewed` note remains searchable and usable for discovery. Its status must remain visible when it influences a professional answer.

## Card projections

Cards are generated consultation views. They are not new source files, storage objects or authority objects.

```text
NAS original / Markdown note / structured referential
→ bounded projection
→ card displayed for the current consultation
```

### Project Document Card

A Project Document Card projects one NAS source without duplicating it.

Minimum visible fields:

```text
parent_project_id;
project display name;
phase;
distributor;
document type;
subject;
index;
date;
link to the original;
analysis status.
```

Candidate actions remain bounded:

```text
open;
summarize;
compare;
propose extraction.
```

### Knowledge Card

A Knowledge Card projects reusable knowledge. Its default source is one Markdown subject. The family `Référentiels` is a knowledge family, not a separate authority class.

Minimum visible fields:

```text
free subject title;
family;
short summary;
principal source references;
freshness or review signal.
```

Candidate actions remain bounded:

```text
consult;
search nearby knowledge;
cite a source;
propose an update.
```

### Structured referential projection

A large structured referential may generate specialized Knowledge Cards directly from PostgreSQL or another approved external store. A plant catalogue can therefore expose one Knowledge Card per plant without creating one Markdown file per plant.

```text
Knowledge Card
├── editorial subject backed by Markdown
└── referential record backed by structured data
```

The distinction concerns source shape and consultation mode:

```text
editorial knowledge
= an explained subject intended to be read;

referential knowledge
= a normalized record or catalogue intended to be looked up, filtered and compared.
```

Both remain Knowledge Items.

### Card boundary

```text
Document Card parent_project_id required
card != source
card != duplicate document
card != Evidence
card != Registre Probatoire entry
card action != external-action authorization
card status != source validity
```

The card may expose a proposal from Hermes, but consequential acceptance remains human.

## Placement test

Use these questions in order:

```text
Is it specific to one project?
→ keep it in the project NAS space.

Is it mainly a dictionary, catalogue or nomenclature?
→ Référentiels.

Is it about obligations, contracts, insurance or liability?
→ Responsabilité.

Is it a reusable way of working?
→ Méthodologie.

Is it about how something is built, installed, diagnosed or maintained?
→ Techniques.

Is it a mandatory legal, regulatory or administrative rule?
→ Réglementations.
```

If a subject genuinely spans two families, choose the dominant consultation purpose and link to it from another note if useful. Do not duplicate the whole note.

## Non-equivalences

```text
folder placement != truth
strict filename != provenance complete
Markdown conversion != source replacement
knowledge publication != evidence admission
vectorization != memory
Hermes automatic publication != human validation
Knowledge publication != Evidence or Register promotion
NAS presence != connector activation
documentation in this repository != deployed organization
```
