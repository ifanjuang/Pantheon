# Skill PDF vers Markdown

Objectif : convertir simplement les PDF déposés dans `base_metier/architecte/knowledge/sources/` en fichiers Markdown dans `base_metier/architecte/knowledge/corpus/`.

## Flux minimal

```txt
knowledge/sources/*.pdf
  -> knowledge/corpus/<nom_du_pdf>.md
```

## Règles

- Les PDF sources ne sont jamais modifiés.
- Un PDF produit d'abord un Markdown complet et lisible.
- Les chunks RAG atomiques seront générés dans un second temps.
- Les pages, titres et numéros de chapitres doivent être conservés autant que possible.
- Les tableaux et formulaires sont signalés `needs_review: true` si l'extraction n'est pas fiable.

## Commande prévue

```bash
python base_metier/architecte/skills/pdf_to_md/convert_pdf_to_md.py \
  --input base_metier/architecte/knowledge/sources \
  --output base_metier/architecte/knowledge/corpus
```
