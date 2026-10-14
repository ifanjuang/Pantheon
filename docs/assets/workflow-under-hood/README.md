# Architecture workflow under the hood

Status: visual support asset — documentation only.
Boundary profile: documentation_only.

This folder contains a static explanatory HTML page showing how a professional architecture workflow may stay simple for the practitioner while exposing the governed under-the-hood steps when needed.

- [`architecture_workflow_under_hood.html`](architecture_workflow_under_hood.html)

Related doctrine:

- [`../../governance/DOSSIER_SITUATION_INTAKE.md`](../../governance/DOSSIER_SITUATION_INTAKE.md)
- [`../../governance/WORKFLOW_FORGING_PROTOCOL.md`](../../governance/WORKFLOW_FORGING_PROTOCOL.md)
- [`../../governance/WORKFLOW_LIFECYCLE.md`](../../governance/WORKFLOW_LIFECYCLE.md)
- [`../../governance/CAPABILITY_PLACEMENT.md`](../../governance/CAPABILITY_PLACEMENT.md)

## Purpose

The asset explains the operating pattern:

```text
Simple surface
→ Dossier Situation Brief
→ Workflow Candidate
→ precise under-the-hood trace
→ candidate outputs
→ evidence and gaps
→ human decision gate
```

It is designed for architecture / MOE practice, especially cases where a client email, attached document, project record, plan version or ERP notice may change a consequential project decision.

## What it shows

- two practitioner-facing workflows:
  - impact review after a client change of occupancy / effectif;
  - governed preparation of an ERP fire-safety notice;
- the visible user path: question, situation intake, sources, impact, questions, candidate deliverables, decision;
- the role sequence:
  - IRIS clarifies;
  - ATHENA structures;
  - ARGOS situates sources and proof;
  - THEMIS qualifies risk and approval boundary;
  - APOLLO checks completeness;
  - ZEUS arbitrates procedure;
  - HEPHAISTOS forges workflow or artifact candidates;
- the detailed runtime path: OCR, PDF cleanup, document classifier, project lookup, plan retrieval, vision plan analysis, PDF annotation, impact matrix, Evidence Pack Candidate;
- stop conditions: contract gap, version gap, missing source, unclear room function, unconfirmed recipient, external action without approval;
- output statuses: candidate, to verify, blocked, draft-only, approval required.

## Boundary

This is not implementation.

It does not create:

- email access;
- OCR;
- computer vision;
- PDF annotation;
- Notion synchronization;
- ERP regulatory validation;
- Registre Probatoire storage;
- automatic memory promotion;
- automatic approval;
- workflow execution;
- external transmission.

The page is an explanatory cockpit mockup. It follows the doctrine:

```text
The Registre Probatoire proves.
The human decides.
```
