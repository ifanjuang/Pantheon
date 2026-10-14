# Architecture Knowledge Registry Blueprint

Status: candidate support doctrine — blueprint for the architecture knowledge registry (documentation only).
Boundary profile: candidate_support_note.

This document is the Pantheon-side **blueprint** for how an architecture
practice's reusable knowledge is registered and governed. It resolves
arbitration item C ("Knowledge registry location") of
`docs/domain-packs/architecture/HISTORICAL_ARCHITECTURE_RECONCILIATION.md`: the blueprint lives in
Pantheon; the runnable mapping lives outside Pantheon.

It is documentation only. It does not implement a registry runtime, ingestion
pipeline, OCR, vector index, embedding store, graph backend or external
connector. Entries it describes remain candidates until reviewed.

## Purpose

An architecture practice reuses a body of knowledge across projects:
regulations, agency standards, typical construction details, and precedents.
This blueprint describes how such knowledge is **registered as governed
entries** — with a source, an authority level and a status — so it can be
referenced without being silently treated as truth. (Lessons learned and
supplier/product data were considered and rejected as Knowledge families —
see "Two orphans resolved" below.)

## Placement: blueprint in Pantheon, mapping outside

- **Pantheon (this blueprint)** governs the vocabulary, the authority levels, the
  statuses and the boundary. It decides nothing automatically.
- **The runnable mapping** (ingestion, normalization, indexing, retrieval) lives
  outside Pantheon: non-executable templates under `templates/` and/or external
  adapters on the Hermes side. It produces candidates, never canonical truth.

This mirrors the doctrine of the whole repository: Pantheon governs, Hermes and
adapters execute, the proof constrains, the human decides.

## What the registry holds

Status of this section: **to verify — not reconciled with the enforced
`knowledge_family` enum.** See Pantheon-Next#989. Two of the three orphan categories below
are resolved by maintainer decision (2026-09-07); the remainder — the
enum/blueprint reconciliation itself and `precedent` — is still open.

Each registry entry is a governed knowledge item, not a fact. The list below is
illustrative, not a frozen enumeration — entries were examples when first
written, not a closed set to be preserved as-is.

- `regulation` — codes, norms, local urban rules (high authority when official).
- `agency_standard` — the practice's own conventions and templates.
- `construction_detail` — typical or proven details and assemblies.
- `precedent` — prior projects or external references used by analogy. **Still
  open**: no owner assigned yet.

These are candidate categories of this blueprint. They are **not** the vocabulary
a Knowledge item is validated against today: `schemas/document_knowledge_slice.schema.yaml`
defines `knowledge_family` as a closed enum (`referentiels`, `responsabilite`,
`methodologie`, `techniques`, `reglementations`), which
`implementation/mvp_vertical/knowledge.py` enforces on every write. Three of the
four remaining categories above correspond approximately to enum members under
different names; `precedent` still has no storable family and is not resolved
by this update. Authoring a Knowledge item against this list is refused at
write time.

Which vocabulary governs the surviving overlap — and where `precedent` belongs —
remains a maintainer decision recorded in Pantheon-Next#989, deliberately deferred until Pantheon-Next#827
shows which categories real professional work needs.

### Two orphans resolved: neither is a Knowledge family

**`supplier_product` is not Knowledge. It is a Document, scoped to the project
that received it.** A supplier's technical sheet for a specific piece of
equipment is not reusable interpretation cued across projects — it is a
source-backed record tied to one affair, one lot, one piece of equipment. That
is exactly what `AGENCY_DOMAIN_PACK.md` already defines under "Documents and
versions" and its "DOE equipment item" specialized extension
(`equipment_tag`, `system_type`, `serial_number`, `manual_document_id`, …). No
new field, schema or owner is needed: the shape already exists, and the
category is declared out of Knowledge's scope rather than added to it.

**`lesson_learned` does not exist as a category this practice needs.** Declared
out of scope outright, not mapped elsewhere. A post-project feedback item that
does turn out to matter has other existing paths (an Information item, a
Knowledge entry under one of the surviving categories, a Registre Probatoire
entry) depending on what it actually is — `lesson_learned` itself is not a
governed category.

Both were candidate placeholders from this blueprint's first draft, not
categories a maintainer had reviewed and confirmed. Removing them here is that
review, not a reversal of an accepted decision.

`docs/governance/KNOWLEDGE_TAXONOMY.md` remains the governing owner for the
governance-lifecycle categories (`Raw Source`, `Knowledge Item`, `Evidence Item`,
…). It defines no subject-matter family axis, so this blueprint specializes the
architecture domain alongside it rather than extending an axis it owns.

## How entries map to the governance vocabulary

A registry entry reuses the existing axes and the proof register vocabulary
rather than inventing parallel ones:

- **source authority** uses `source_authority_level` (from `law_or_regulation`
  down to `model_interpretation_candidate`).
- **status** uses `proof_status` / `approval_state` from the architecture proof
  register.
- **scope** uses the shared scope vocabulary (project / agency_library /
  global_reference …).

So a regulation entry can carry strong authority, while a model-derived note
stays a low-authority candidate — the same ladder used everywhere else.

## Boundary

- No ingestion engine, OCR, vector or graph backend, embedding store, retrieval
  service or external connector is defined or implied here.
- The mapping that turns sources into registry entries is an adapter outside
  Pantheon; it outputs Task Contract in → Result Candidate + Evidence Pack
  Candidate out, through the chokepoint.
- Registry entries never auto-promote to canonical; promotion is a governed
  human decision, per use, like any other Pantheon canonization.

## Relationship to other documents

- `docs/governance/KNOWLEDGE_TAXONOMY.md` — the general knowledge taxonomy this
  blueprint specializes for architecture.
- `docs/governance/KNOWLEDGE_INGESTION_AND_MEMORY.md` — governed ingestion and
  memory boundary the runnable mapping must respect.
- `docs/domain-packs/architecture/AGENCY_DOMAIN_PACK.md` and
  `docs/governance/DOMAIN_PACK_SPEC.md` — the domain pack the registry serves.
- `docs/domain-packs/architecture/PROOF_REGISTER.md` — the proof vocabulary reused
  by registry entries.
- `docs/domain-packs/architecture/HISTORICAL_ARCHITECTURE_RECONCILIATION.md` — arbitration item C that
  this blueprint resolves.

## Governance references

- docs/domain-packs/architecture/HISTORICAL_ARCHITECTURE_RECONCILIATION.md
- docs/governance/KNOWLEDGE_TAXONOMY.md
- docs/governance/KNOWLEDGE_INGESTION_AND_MEMORY.md
- docs/domain-packs/architecture/AGENCY_DOMAIN_PACK.md
- docs/domain-packs/architecture/PROOF_REGISTER.md
