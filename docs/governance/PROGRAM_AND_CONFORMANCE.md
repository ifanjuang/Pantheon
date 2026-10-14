# Program & Conformance

Status: candidate support doctrine — Project Anatomy prescriptive intent.
Authority: Project Anatomy V0.2 schemas and PROJECT_ANATOMY_MODEL.md.

This document adds no extraction, OCR, vision, solver, scheduler, workflow or
conformance engine. It defines how prescriptive intent remains separate from
observed project state.

    OpenWebUI exposes.
    Hermes Agent executes bounded tasks.
    Pantheon Next governs.
    The human decides consequential effects.

## Purpose

A project may begin with a client programme before any drawing exists. Programme
intent must remain expressible, versioned and comparable with observations
without being mistaken for a measured fact or an automatic compliance result.

## Active carriers

The active contract uses:

    program
    requirement
    classification_scheme
    stable_object
    attribute_claim
    relation_claim
    source_representation

A requirement is prescriptive intent. An attribute or relation claim is an
assertion about a source representation or stable project object.

    required != observed
    programme intent != project truth
    comparison result != professional decision

## Programme

A program records a typed, layered source of intent. Several programmes may
coexist when their scope and source authority are explicit.

The programme source remains versioned by the document/version owners. Project
Anatomy references that source; it does not own document chronology.

An email or new brief may propose a changed requirement, but no programme change
is applied automatically. The new source version and the resulting candidate
requirements follow the normal review and decision path.

## Requirements

A requirement may constrain:

- an exact stable object;
- an exact related target;
- an object-family selector;
- a governed classification scheme/value;
- a namespaced attribute;
- a count or existence condition.

Typical operators include minimum, maximum, exact count, required existence and
required relation. The exact executable vocabulary belongs to
requirement.schema.yaml.

## Classifications

classification_scheme registers a governed external or agency vocabulary.
Classification values are carried by namespaced attribute claims, not by a
parallel classification object.

Examples include:

- classification.ifc;
- classification.revit_category;
- classification.agency.room_function;
- classification.fire_erp;
- classification.accessibility.

A regulatory classification may support a conclusion only through the existing
Evidence and approval owners.

    classified != compliant
    source label != stable identity

## Composite and multi-level objects

A composite unit, zone or system is a stable_object with the appropriate broad
object_family. Membership, containment and cross-level continuity are expressed
through relation_claim. Source occurrences on several plans remain separate
source_representation records linked through candidate identity.represents
claims.

No special group, spatial-node or inline-match authority is required.

## Conformance projection

Conformance is calculated by comparing requirements with reviewed claims. A gap
is a candidate result that may open or support an existing WorkIssue or
DecisionRequest; it is not persisted as a second deviation authority.

Possible human outcomes include:

- amend the design;
- amend the programme;
- accept a bounded variance with the required authority and justification;
- request more source material.

## Invariants

1. Prescriptive intent and observed state remain separate.
2. Source provenance is preserved per claim.
3. A requirement or classification never proves compliance by itself.
4. A comparison never self-resolves a professional consequence.
5. Stable identity is never inferred solely from a label or classification.
6. Project Anatomy does not absorb Evidence, Decision or approval lifecycles.

## Governance references

- docs/domain-packs/architecture/PROJECT_ANATOMY_MODEL.md
- docs/domain-packs/architecture/PROJECT_ANATOMY_BASELINE_DECISION.md
- docs/domain-packs/architecture/PROOF_REGISTER.md
- docs/governance/APPROVALS.md
- docs/governance/GLOSSARY.md
- schemas/architecture-project-understanding/
