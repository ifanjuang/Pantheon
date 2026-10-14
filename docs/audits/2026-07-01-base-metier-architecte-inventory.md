# Inventory — `base_metier/architecte/` (B-2, read-only)

Status: validation-only / inventory trace — to verify. Read-only inventory of the
`base_metier/architecte/` corpus to give the maintainer the facts before the B-2
decision (license, provenance, extraction). It records; it **moves, deletes and
decides nothing**. The license determination is a human / legal call, not made here.

Date: 2026-07-01.

```text
OpenWebUI exposes.
Hermes Agent executes.
Pantheon Next governs.
```

## Summary

- Size: **58 MB**, **42 files**. **Not indexed** in `AUTHORITY_INDEX.md` / `MODULES.md`
  (only mentioned in `REPOSITORY_CONSOLIDATION_LANDING_PLAN.md`).
- Contains **executable code** (2 Python skills) — out of the "Pantheon governs, does
  not execute" doctrine; belongs Hermes-side.
- Contains **copyrighted third-party professional PDFs** (MAF, Ordre des Architectes)
  with **no provenance or license declaration** — the real B-2 risk.
- **Binaries are versioned in git** (not in `.gitignore`) — ~55 MB of PDFs in history.
- Three PDFs are **exact duplicates** (same sha256) kept in two locations.

## File-type breakdown

```text
12 pdf · 10 yaml · 9 md · 8 .gitkeep · 2 py · 1 txt
```

Structure: `base_metier/architecte/{knowledge,skills,prompts,workflows,evaluations}`.
`knowledge/` holds `sources/` (original PDFs), `corpus/` (reread Markdown),
`collections/` + `indexes/` + `schemas/` (retrieval config), per its `README.md`.

## Executable content (doctrine issue)

| Script | What it does | External dep | Placement note |
|---|---|---|---|
| `skills/pdf_to_md/convert_pdf_to_md.py` | PDF → Markdown, one file per PDF, preserves page boundaries | **PyMuPDF (`fitz`)** — not declared in any `pyproject.toml` | executes → Hermes-side, not Pantheon |
| `skills/ingest_local_folder/ingest.py` | ingests a local folder (`.pdf/.md/.txt`) into knowledge chunks | **PyMuPDF (`fitz`)** in `extract_pdf()` — undeclared (same as `pdf_to_md`) | executes → Hermes-side, not Pantheon |

Pantheon's doctrine keeps execution outside the governance repo; these two skills
should move Hermes-side (arbitration B-2 / P4.3).

## PDF inventory (9 unique files; provenance/licence to verify)

`size` rounded to MB; `sha256` = first 12 hex. **Licence read below is non-legal**, a
prompt for the maintainer's audit — not a determination.

| Size | sha256 | File | Apparent origin | Licence risk (non-legal) |
|---|---|---|---|---|
| 15 MB | bae7e1fcf164 | `knowledge/sources/MAF_OUTILS_PERMIS_ANNEXES.pdf` | Mutuelle des Architectes Français — "Outils" | **High** — copyrighted member material |
| 11 MB | 2fd4848a53b7 | `knowledge/sources/MAF_OUTILS_PERMIS.pdf` | MAF "Outils" | **High** |
| 11 MB | 3feb17b148b3 | `knowledge/sources/MAF_Outils_CHANTIER.pdf` | MAF "Outils" | **High** |
| 5 MB | b1f10dbc414e | `knowledge/sources/MAF_Outils_CONTRAT.pdf` | MAF "Outils" | **High** |
| 5 MB | 1653469a3f99 | `knowledge/sources/MAF_Outils_CONTRAT_Annexe.pdf` | MAF "Outils" | **High** |
| 2 MB | 714b7f81bc58 | `1113-construire-avec-l-architecte-2019_-_bdef.pdf` | Ordre des Architectes publication | **Medium-High** — copyrighted publication |
| 1 MB | 6fc1ae8c7649 | `ccag_des_marches_publics_de_maitrise_doeuvre.pdf` | CCAG-MOE (official public-procurement clauses) | Low-Medium — official text, reproduction conditions |
| 1 MB | 0ce6e90fe6c6 | `knowledge/sources/Chantier_cahier des clauses administratives générales.pdf` | CCAG (administrative clauses) | Low-Medium — official text |
| 1 MB | e0961496490f | `GLOSSAIRE.pdf` | unknown | **To verify** |

Also present: `knowledge/sources/Code-de-La-Construction-Et-de-l-Habitation.txt`
(official legal code — low risk, public text).

The **MAF and Ordre des Architectes PDFs (~47 MB)** are the ones that most plausibly
carry redistribution restrictions and should be cleared, replaced by a reference, or
removed before any public artifact or vertical slice relies on them.

## Exact duplicates (same content in two places)

```text
714b7f81bc58  1113-construire-avec-l-architecte-2019_-_bdef.pdf   (root + knowledge/sources/)
6fc1ae8c7649  ccag_des_marches_publics_de_maitrise_doeuvre.pdf    (root + knowledge/sources/)
e0961496490f  GLOSSAIRE.pdf                                       (root + knowledge/sources/)
```

The root-level copies duplicate the canonical `knowledge/sources/` ones (~3.5 MB wasted).

## Provenance / licence declaration

**None.** No manifest declares, per source: origin, author, licence, retrieval date or
redistribution right. `README.md` describes the RAG layout; the `collections/*.yaml`
are retrieval config, not provenance. This is the gap the B-2 audit must close.

## Recommendation (mechanical; the licence call stays with the maintainer)

Per arbitration B-2 ("accepted, controlled transition"):

```text
1. Freeze base_metier/architecte/ — build nothing (incl. the B-3 vertical slice) on it
   until qualified.
2. Index it in AUTHORITY_INDEX.md as: external professional corpus / to verify
   (candidate; not authority; not proof).
3. Licence audit (MAINTAINER / legal): clear or remove the MAF + Ordre PDFs; confirm
   the CCAG / Code texts' reproduction conditions.
4. De-version the binaries: .gitignore knowledge/sources/*.pdf + a reconstructible
   sources manifest (filename · declared origin · licence · size · sha256) — this
   inventory's table is the seed. Remove the 3 duplicate root copies.
5. Move the 2 executable skills Hermes-side (they execute).
6. Do NOT ground the B-3 vertical slice on these sources until (3) is resolved.
```

## Boundary

Inventory only. No file under `base_metier/`, `schemas/`, `tests/`, `mcp-server/` or any
protected path is moved, deleted or changed by this document. It records facts and
recommends; the User Decision Gate and the human decide. The licence determination is
explicitly **not** made here.
