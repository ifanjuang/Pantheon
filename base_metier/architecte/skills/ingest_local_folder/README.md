# Skill Hermes — ingestion locale d'une base métier

Ce skill est destiné à être exécuté par Hermes sur une machine ayant accès au dossier local du projet.

## Objectif

Transformer les documents déposés dans `base_metier/architecte/knowledge/sources/` en corpus Markdown exhaustif, chunks RAG atomiques, manifestes d'audit et index vectoriels.

## Pipeline

```txt
sources PDF/MD/DOCX
  ↓
extracted/ page par page
  ↓
corpus/ Markdown exhaustif par chapitre
  ↓
chunks/ fiches atomiques RAG
  ↓
indexes/ manifestes + collections
  ↓
vector store Qdrant ou PgVector
```

## Commande prévue

```bash
python base_metier/architecte/skills/ingest_local_folder/ingest.py \
  --base-dir base_metier/architecte \
  --mode exhaustive \
  --vector-store qdrant \
  --collections auto
```

## Règles

- `knowledge/sources/` est intouchable.
- `knowledge/extracted/`, `knowledge/corpus/`, `knowledge/chunks/` sont reconstruisibles.
- Chaque chunk doit conserver `source_document`, `source_pages`, `status`, `review_status`, `collections`.
- Les contenus `validated` doivent être priorisés sur `reviewed`, puis `extracted`, puis `draft`.

## Convertisseurs prévus

- Markdown : lecture directe.
- PDF texte : PyMuPDF.
- PDF complexe : Docling si disponible.
- OCR : uniquement en fallback sur pages non extractibles.

## Sorties attendues

```txt
knowledge/extracted/<document>/page_001.md
knowledge/corpus/<document>/<chapitre>.md
knowledge/chunks/<collection>/<chunk>.md
knowledge/indexes/extraction_manifest.json
knowledge/indexes/vector_manifest.json
knowledge/reviews/<document>_review.md
```
