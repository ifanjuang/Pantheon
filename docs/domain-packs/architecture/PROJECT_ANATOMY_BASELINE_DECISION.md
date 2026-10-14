# Project Anatomy — V0.2-only baseline decision

Status: architecture decision — active baseline.
Date: 2026-08-09.
Authority: PROJECT_ANATOMY_MODEL.md and the reviewed schemas.

## Observed context

Project Anatomy V0.1 was developed and tested only in sandbox. It was never
deployed in production, never became the authority for persisted project data
and has no operational consumer to preserve.

## Decision

Project Anatomy V0.2 is the sole first-installation and emission baseline.

The active repository contains no V0.1:

- schema or example;
- dossier adapter or compatibility registry;
- read or write path;
- SQL carrier or data migration;
- API or projection branch;
- vendored implementation contract.

Sandbox databases created before this decision are disposable and must be
recreated from the current baseline. They are not migrated or rewritten as if
historical V0.2 provenance had existed.

Git history remains the record of the discarded design. Historical design is not
an active contract.

## Active model

The project-world core remains:

    stable_object
    source_representation
    attribute_claim
    relation_claim

Prescriptive intent remains a separate requirement. Supporting provenance and
governance reuse their existing owners.

    source occurrence != stable identity
    candidate relation != validated identity
    runtime success != Evidence
    projection != authority

## Reopening rule

Compatibility may be reintroduced only through a separate architecture decision
that identifies a real persisted dataset or operational consumer, proves why a
bounded import cannot handle it and preserves provenance without creating a
second owner.
