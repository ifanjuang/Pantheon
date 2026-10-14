# ProjectClaim migration note

This repository is still a pre-production executable candidate. The schema initializer therefore removes obsolete consequential Project keys from `agency_projects.attributes` instead of carrying a dual-write compatibility layer.

Removed legacy JSONB keys:

```text
budget
surface_terrain
surface_existante
surface_projet
emprise
parcelles
plu_zone
permit_number
permit_date
reception_date
erp_type
```

New writes for those meanings belong to `agency_project_claims` and are projected back onto the Project read model. Descriptive `attributes` remain for flexible, non-source-backed information.

This cleanup does not delete Information cards, Evidence, Knowledge or source documents.
