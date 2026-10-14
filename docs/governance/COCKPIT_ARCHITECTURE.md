# Pantheon Cockpit Architecture Map

Status: validation-only architecture map — documented non-implemented.
Boundary profile: validation_only_trace.

This document maps the existing owners that compose the Pantheon Cockpit. It does not create a new cockpit ontology, UI framework, renderer, state machine, resolver, runtime, approval engine, memory engine or authority layer.

## Purpose

The Cockpit is the product composition of existing governed objects and projection grammars.

```text
Governance owners
→ projection grammars
→ product composition
→ future deterministic current-state projections
```

This map clarifies jurisdiction before any new cockpit document is proposed.

## Three layers

### 1. Governance owners

These documents own the underlying objects, status, scope, evidence, authority or durable records.

| Subject | Current owner or owner family |
|---|---|
| Case, Situation and Task Contract | `CORE_CONCEPTS_MAP.md`, `TASK_CONTRACTS.md` and their referenced owner documents |
| Capability, Resource, Binding and placement | `UNIFORM_CAPABILITY_GOVERNANCE.md`, `CAPABILITY_PLACEMENT.md`, `ADAPTERS_AND_BINDINGS.md` |
| Source and derived records | `RAW_DERIVED_GOVERNED_RECORDS.md` |
| Evidence | `EVIDENCE_PACK.md`, `EVIDENCE_TOPOLOGY.md` |
| Gate and approval boundary | `APPROVALS.md` and the applicable gate doctrines |
| Decision record | decision schemas and decision owner documents, including `HandoffDecision` contracts where applicable |
| Register and durable retention | `MEMORY.md` and Register owner documents |
| Runtime and control-plane status | `WHAT_RUNS.md`, `PANTHEON_CONTROL_PLANE_BOUNDARY.md` and runtime-adapter owner documents |
| Governed relations | `PANTHEON_GRAPH_MODEL.md` |

The Cockpit may expose these objects. It does not redefine their lifecycle, schema or authority.

### 2. Projection grammars

| Projection concern | Current owner |
|---|---|
| Card, Scene, Deck and Constellation | `CARD_STACK_MODEL.md` |
| Dynamic visible context composition | `CONTEXT_STACK.md` |
| Consequential decision review and capture | `DECISION_SURFACE_SPEC.md` |
| Generic governed relations | `PANTHEON_GRAPH_MODEL.md` |

```text
projection != object ownership
visible != verified
recorded != current
interaction != execution
```

### 3. Product composition

`PANTHEON_COCKPIT_UX_SPEC.md` owns the current product-facing candidate for:

- professional cockpit purpose;
- cabinet and technical-administration modes;
- high-level navigation;
- visible request lifecycle;
- workflow-proposal review;
- decision capture and governed handoff preparation.

It remains candidate and non-executable.

## Current composition

```text
PANTHEON_COCKPIT_UX_SPEC
  uses CARD_STACK_MODEL
  uses CONTEXT_STACK
  specializes consequential review through DECISION_SURFACE_SPEC
  projects relations defined by PANTHEON_GRAPH_MODEL
  displays objects owned by their governance documents
```

No document in this composition may silently become the owner of another document's object.

## Existing concepts

```text
Card
= stable projection of one governed entity or record.

Scene
= bounded filtered and ordered presentation for one review purpose.

Deck
= vertical reading and depth order inside a Scene.

Constellation
= global relation view and project-switching surface.

Context Stack
= dynamic visible composition of task-bounded context cards.

Decision Surface
= display and capture form for a consequential human decision requirement.
```

## Remaining gaps

The following areas are not yet owned by a stable dedicated document or implementation:

1. detailed interaction grammar:
   - tap;
   - long press;
   - horizontal sibling navigation;
   - vertical depth navigation;
   - focus, keyboard and accessibility behavior;
   - back, breadcrumbs and history;

2. stabilized visual language:
   - anatomy tokens;
   - compact and expanded variants;
   - spacing and density;
   - typography and iconography;
   - contrast and non-color status cues;
   - motion and transition constraints;

3. `Cluster` as a purely visual grouping construct;

4. deterministic current-state projections:
   - Current Decision;
   - Current Gate;
   - Current Runtime status;
   - Current Scene or View composition;

5. optional documentation-graph metadata for ownership and dependency analysis.

## Creation gate for future Cockpit documents

A new Cockpit document is justified only when all conditions are met:

```text
missing owner demonstrated;
existing owner documents reviewed;
non-duplication recorded;
new jurisdiction bounded;
status and authority class declared;
no runtime or approval behavior implied;
human review required before promotion.
```

A future document must not be created merely to reorganize terminology already owned elsewhere.

## Resolver sequence

The correct sequence is:

```text
Current Decision Resolver
→ Current Gate projection
→ current runtime/status projections
→ future Current View composition
```

`Current View` must not be designed first. It depends on deterministic owner-aligned current-state projections.

## Documentation Graph posture

The repository already contains authority indexes and a governed object-relation grammar. A future documentation graph may use bounded metadata such as:

```text
owns
extends
depends_on
uses
supersedes
projects
```

This map does not introduce those fields as a mandatory repository standard. Any migration requires a separate proposal, validator design, compatibility review and human approval.

## Boundaries

```text
Cockpit Architecture Map != new doctrine owner
Card Stack != ontology
Scene != exhaustive graph
Decision Surface != approval engine
Context Stack != memory
Graph relation != execution edge
recorded decision != current applicable decision
runtime success != evidence
UI request != Hermes command
merged != promoted
```

No code, schema, test, renderer, OpenWebUI component, Hermes skill, connector, scheduler, queue, runtime action or external effect is introduced.