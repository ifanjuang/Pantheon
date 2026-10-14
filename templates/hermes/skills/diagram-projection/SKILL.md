---
name: diagram-projection
description: "Create explanatory diagram artifacts from bounded structured input without turning layout, labels, inferred links or rendered geometry into project truth. Use an admitted external editorial-diagram binding when available; otherwise return a diagram-spec candidate."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  governed_by: docs/governance/VISUAL_LANGUAGE.md
  candidate_binding: "cathrynlavery/diagram-design"
  reviewed_upstream_ref: "d1376371965f513d99cc9ec388835d255c5c88d5"
---

# Diagram projection

Non-executable Hermes skill blueprint for turning already-bounded structured material into explanatory diagrams.

Pantheon governs source status, Project Anatomy, Evidence and consequential decisions. Hermes may prepare a diagram or diagram specification through an admitted runtime binding. Rendering is presentation only.

```text
structured source / governed projection / candidate set
-> bounded diagram specification
-> external editorial diagram renderer when admitted
-> HTML / SVG / PNG presentation artifact

diagram != source
diagram != Evidence
rendered relation != governed relation
layout geometry != governed geometry
projection != persistence
```

## Purpose

Use diagrams when topology, sequence, dependency, phase, change or spatial organization is materially clearer visually than in prose or a table.

Typical useful classes include:

- architecture/system map;
- architecture delta;
- flowchart, sequence and state machine;
- dependency graph;
- timeline and Gantt;
- swimlane and process;
- hierarchy/tree;
- data model/schema;
- axonometric explanatory view when the source geometry is already available and the result is clearly non-authoritative.

Do not create a diagram merely because a rendering binding is available.

## Input boundary

Use only the task-bounded material supplied or retrieved through an authorized source path.

Preserve when available:

- project or dossier reference;
- exact source references, versions, digests or indices;
- stable object references only when already governed and supplied;
- candidate/source-representation identifiers when the data is not yet governed;
- requested diagram purpose and audience;
- declared scope and coverage;
- status distinctions such as observed, proposed, derived, reviewed or unknown.

Never invent a stable object, source revision, professional status or relation to make a diagram look complete.

## Diagram specification

Before rendering, prepare the smallest useful diagram specification.

A specification may contain:

```yaml
diagram_type:
purpose:
basis:
  project_ref:
  source_refs: []
  snapshot_refs: []
scope:
nodes:
  - ref:
    label:
    status:
relations:
  - from:
    to:
    kind:
annotations: []
limitations: []
authority:
  is_source: false
  is_evidence: false
  is_project_fact: false
  mutates_project_anatomy: false
```

This is a presentation handoff shape, not a canonical Pantheon schema and not a persistence model.

Node and relation references must reuse supplied identifiers where possible. Renderer-local identifiers may be created only for layout and must stay renderer-local.

## Rendering binding

The currently reviewed candidate binding is `cathrynlavery/diagram-design` at upstream commit
`d1376371965f513d99cc9ec388835d255c5c88d5`.

The binding is external and replaceable. Repository review does not install it, activate it, authorize network access, or make its output authoritative.

Use the renderer only when the current task admits this exact tool as well as the runtime exposing it; follow its native diagram grammar instead of adding a Pantheon renderer. When tool admission is absent or availability is unknown, return the diagram specification (or a simple native presentation) and note the missing rendering capability. Do not install a replacement automatically.

```text
binding reviewed != binding installed
binding installed != binding task-authorized
renderer success != source verification
renderer output != Project Anatomy mutation
```

## Architecture Project Understanding boundary

Architecture Project Understanding remains upstream when semantic qualification is required.

Preferred flow:

```text
PDF / image / IFC / Revit observation
-> document_structure / Observation Bundle Candidate
-> architecture-project-understanding when applicable
-> reviewed/candidate structured material
-> diagram-projection
-> presentation artifact
```

Do not ask the renderer to become an IFC/Revit/PDF understanding authority.

For unreviewed APU material, visually preserve candidate status and limitations. A diagram must not make candidate relationships look accepted merely through confident layout.

## Delta diagrams

For before/after or revision comparison:

- preserve both exact bases;
- distinguish added, removed, changed and unresolved items;
- do not infer deletion from missing partial coverage;
- separate source-observed change from interpretation;
- keep professional applicability unresolved when source precedence is unresolved.

```text
not found in snapshot != deleted
different source values != approved change
newer timestamp != applicable revision
```

## Spatial and axonometric diagrams

A rendered plan or axonometric view is explanatory unless the exact geometry and calibration contract explicitly establishes otherwise.

```text
diagram coordinate != measured coordinate
axonometric rendering != BIM geometry
visual proximity != governed adjacency
layout containment != project containment
```

Use source-derived geometry only within its declared precision and coverage. Do not manufacture dimensions, areas, levels, openings or room boundaries.

## Output posture

Return or store only the presentation artifact requested by the task plus enough provenance to identify its basis.

Where practical, retain:

- diagram type;
- source/project refs;
- renderer/binding identity and version/ref;
- generation timestamp;
- limitations;
- candidate/review status when relevant.

Do not create a second project-data store merely to support diagram rendering.

## Forbidden effects

This skill must not by itself:

- admit or modify Evidence;
- create or mutate Project Anatomy stable identity;
- approve a relation, requirement, compliance result, cost, reservation or professional conclusion;
- persist a diagram as canonical project state;
- alter IFC, Revit, PDF or source documents;
- install or update the external renderer;
- transmit private project material to an external destination without authorization;
- infer missing objects from partial coverage;
- trigger another consequential effect because a rendered diagram appears complete.

## Final rule

```text
Pantheon and its governed sources own meaning and status.
The diagram specification selects what to explain.
The renderer arranges it for humans.
Rendering never upgrades authority.
```
