# Diagram Design — external editorial diagram binding

Status: external reference — candidate binding / to verify.
Boundary profile: candidate_support_note.

Reviewed source: `https://github.com/cathrynlavery/diagram-design`  
Reviewed upstream commit: `d1376371965f513d99cc9ec388835d255c5c88d5`  
Review date: 2026-10-07  
Licence observed from repository metadata: MIT.

## Purpose

Qualify `cathrynlavery/diagram-design` as a candidate external binding for a small, tool-agnostic editorial diagram-rendering capability.

This review does not vendor, install, activate or auto-update the upstream repository.

```text
external repository reviewed
!= dependency adopted
!= skill installed
!= skill activated
!= task authorized
```

## Observed upstream surface

At the reviewed ref, the upstream skill describes self-contained HTML/SVG diagram generation and a broad visual vocabulary including architecture, architecture delta, flowchart, sequence, state machine, ER/data model, timeline, swimlane, tree, dependency graph, deployment, Gantt, axonometric plan and exploded axonometric views.

The upstream method separates semantic patterns from layout types and explicitly favors lower diagram density and deletion of unnecessary nodes/edges. It can also ingest or interoperate with formats such as draw.io, Mermaid and Excalidraw according to its upstream documentation.

Recent upstream work immediately before the reviewed ref included defensive validation for malformed draw.io geometry, including non-finite, overflowing and cyclic geometry.

These observations justify technical qualification only. They do not establish Pantheon installation or production support.

## Capability placement

Selected abstract capability name:

```text
editorial_diagram_rendering
```

Function:

```text
bounded structured presentation input
-> explanatory visual arrangement
-> HTML / SVG / PNG artifact
```

It does not own:

- source retrieval;
- document or BIM interpretation;
- Project Anatomy identity;
- Evidence;
- professional validation;
- project truth;
- persistence;
- consequential authorization.

The Pantheon blueprint is:

```text
templates/hermes/skills/diagram-projection/SKILL.md
```

The real renderer remains an external runtime-side binding.

## Relationship to existing visual owners

This capability does not replace:

- `visual-focus`, which tells Hermes where to inspect within an existing visual source;
- `pantheon-activity-projection`, which presents observable runtime progress in conversation;
- Pantheon Cockpit card projections, which render governed product state;
- `docs/governance/VISUAL_LANGUAGE.md`, which owns Pantheon's visual metaphor and communication doctrine.

It may replace future ad-hoc one-off diagram rendering work when the same explanatory result can be produced through this single bounded binding.

Static historical D3/SVG assets remain documentation artifacts until separately migrated; this review does not rewrite them.

## APU / BIM boundary

The intended architecture-domain sequence is:

```text
source
-> IFC/Revit/PDF/image adapter or document structure
-> Observation Bundle / structured fragment candidate
-> architecture-project-understanding when semantic qualification is needed
-> reviewed or explicitly candidate structured material
-> diagram projection
-> external renderer
```

Hard distinctions:

```text
diagram != source
diagram != Evidence
rendered relation != governed relation
rendered geometry != governed geometry
candidate shown confidently != candidate accepted
renderer success != professional validation
```

The renderer must not become a second IFC/Revit/PDF understanding path.

## Security and data posture

The preferred first use is local/offline rendering of already-bounded structured content.

Before any runtime activation, verify:

- exact installation mechanism and transitive dependencies;
- whether any rendering/import path performs network access;
- filesystem read/write scope;
- behavior on imported draw.io/Mermaid/Excalidraw content;
- HTML/SVG sanitization expectations for user-supplied or external content;
- deterministic or bounded output behavior;
- rollback/uninstall path;
- compatibility with the selected Hermes runtime;
- ability to pin a reviewed upstream release/ref.

Private project material must not be transmitted externally merely because the renderer supports a convenient integration.

## Candidate binding posture

```yaml
capability: editorial_diagram_rendering
binding: cathrynlavery/diagram-design
reviewed_ref: d1376371965f513d99cc9ec388835d255c5c88d5
license: MIT
placement: external Hermes/runtime binding
install_status: not established
health_status: unknown
activation_status: unavailable
task_authorization_status: unauthorized
auto_install: false
auto_update: false
preferred_for_new_ad_hoc_diagrams: candidate
```

## Adoption criteria

Move beyond candidate only after a bounded runtime qualification proves:

1. pinned installation without hidden auto-update;
2. local render of representative architecture/system/delta diagrams;
3. no unexpected network transmission;
4. bounded filesystem writes;
5. provenance can identify renderer/ref and input basis;
6. candidate/review statuses remain visually distinguishable;
7. no reverse write into Project Anatomy, Evidence or source artifacts;
8. uninstall/rollback is straightforward.

## Decision

`diagram-design` is accepted into the repository as the **candidate external binding** for `editorial_diagram_rendering`.

The generic Pantheon/Hermes blueprint is implemented in this repository. Runtime installation and qualification remain open.

Preserved distinctions:

- external_reference != adopted_dependency;
- binding_selected != dependency_adopted;
- installed != approved;
- projection != persistence;
- runtime_success != evidence.
