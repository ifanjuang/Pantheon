# Pantheon Concept Model Maps

Status: validation-only support map — documented non-implemented.
Boundary profile: validation_only_trace.

This directory maps existing Pantheon concepts to their current owner documents and records their coverage across doctrine, semantics, projection, prototype, implementation and tests.

It creates no new concept owner, ontology, knowledge-graph runtime, documentation generator, Lens engine, Perspective router, resolver, approval engine, memory engine or execution path.

## Files

- `CONCEPT_MATRIX.md` — owner and placement map for the first tested concept set;
- `COVERAGE_MATRIX.md` — maturity and gap map using repository status vocabulary.

## Jurisdiction

These matrices may answer:

- which document currently owns a concept;
- which documents project or expose it;
- whether any external runtime may execute a related capability;
- which human gate remains consequential;
- which coverage layers are implemented, partial, documented non-implemented, to verify or not applicable.

They must not:

- redefine Decision, Gate, Evidence, Source, Runtime, Register, Case, Card or Scene;
- collapse several owner documents into a new canonical owner;
- infer adoption, activation, safety or evidence acceptance;
- select a Lens or Perspective automatically;
- generate doctrine or UI;
- become a runtime knowledge graph.

## Update rule

A matrix row changes only after the cited owner or implementation status changes. A matrix edit does not change the underlying object.

```text
map updated != owner changed
coverage claimed != coverage verified
prototype present != implementation present
runtime observed != binding adopted
```

## Initial scope

The first slice tests the map against:

- Case;
- Source;
- Evidence;
- Gate;
- Decision;
- Register;
- Runtime;
- Card;
- Scene.

`Lens` and `Perspective` remain identified gaps. They are not admitted as owned Pantheon concepts by this directory.
