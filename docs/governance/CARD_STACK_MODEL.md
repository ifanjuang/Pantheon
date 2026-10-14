# Card Stack Model

Status: candidate support doctrine — generic projection grammar; executable Card rendering exists in the co-located Cockpit candidate, while full Scene/Deck/Constellation semantics remain partial.
Boundary profile: candidate_support_note.

This document owns one bounded responsibility: the generic projection grammar for `Card`, `Scene`, `Deck` and `Constellation`, including when detail becomes a sub-card, how status axes remain separate and how UI intent stays distinct from governed effects.

It does not own Cockpit root spaces, object schemas, lifecycle values, persistence, authorization, Evidence qualification or runtime execution.

```text
governed object or owner record
→ bounded projection
→ Card / collection presentation
→ human review or bounded UI intent
```

```text
Card != source of truth
projection != persistence
UI intent != authorization
runtime success != Evidence
```

## 1. Jurisdiction

```text
PANTHEON_GRAPH_MODEL
= generic grammar for governed nodes and relations

GOVERNANCE_OBJECT_RELATIONSHIP_MAP
= cross-domain responsibility map

CARD_STACK_MODEL
= generic cockpit projection grammar

PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE
= current product spaces and cross-space composition

DECISION_SURFACE_SPEC
= decision-review specialization
```

If this document conflicts with an owner document, the owner document wins.

The Card Stack does not own the lifecycle or schema of any displayed object. In particular it does not redefine Case, Task Contract, Capability, Source, Evidence, Gate, Decision, Register, runtime observation or Workspace identity.

## 2. Core definitions

```text
Governed entity or record
= underlying object with stable identity and owner-defined semantics.

Card
= bounded projection of one identifiable entity, record or declared presentation container.

Scene
= filtered and ordered presentation of Cards for one review purpose.

Deck
= reading/depth organization inside a Scene.

Constellation
= broader relation-oriented projection across Cards or collections.
```

One underlying entity may appear in several projections without becoming several entities.

```text
one identity
many bounded presentations
no identity duplication merely for display
```

These terms are presentation grammar. They do not require the current Cockpit to expose `Scene`, `Deck` or `Constellation` as root labels or persisted object types.

Current product root identities/order and spatial navigation are owned by `PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md` plus the executable Navigation Registry.

## 3. Field-versus-sub-card rule

A Card hierarchy should grow only when review value justifies it.

```text
Field when normal.
Sub-card when it blocks, fails, conflicts, repeats,
is newly proposed, changes scope or requires arbitration.
```

Examples:

| Element | Default projection | Visible sub-card when |
|---|---|---|
| Role or symbolic quality | reference or field | conflict, handoff, missing expertise or arbitration |
| Method | reference | contested, changed, failed or consequential |
| Compétence | reference | missing, proposed, repeatedly productive or failed |
| Risk | field | it blocks or raises the required decision level |
| Scope | field | it changes permitted use, responsibility or output |
| Action | candidate action | a consequential effect is proposed |
| Gate | Gate projection | a consequential threshold is open |
| Decision | Decision projection | a human determination is required or recorded |

A relation is not automatically a Card. A lifecycle state is not a Card family.

Roles, methods, Compétences and rites remain references or bounded projections; their visibility does not activate agents or execution paths.

## 4. Card contract

A Card has a compact reading face and a reviewable detail face or equivalent detail surface.

### Compact face

Prefer the minimum information needed to orient the user:

```text
stable identity or identifiable subject;
object kind / presentation family;
owner-defined status projection;
title;
short summary;
important qualifier, limit or consequence;
relevant tags or relation hint.
```

### Detail surface

Expose enough information for review without inventing authority:

```text
identity and owner;
source or origin where applicable;
exact status axes and their owner;
useful typed relations;
provenance / Evidence references where applicable;
open contradiction, uncertainty or limit;
history / supersession when material;
permitted candidate actions.
```

Front and detail are two projections of the same identity, not separate records.

The current co-located Cockpit candidate implements a front/back Card renderer through `implementation/mvp_vertical/cockpit/rendering/card_renderer.js` and related projection definitions. That implementation is evidence of a candidate renderer, not proof of adoption or production activation.

## 5. Status projection

Process, governance, authorization, evidence and operational posture remain independent.

A Card may display several owner-provided axes, but it must not create a synthetic aggregate that silently collapses them.

```text
process success != governance validation
governance validation != execution
runtime success != Evidence
healthy != safe
approved != activated
activated != task authorized
record present != Register Entry
Register Candidate != Register Entry
```

Exact values remain owned by the underlying object, schema or doctrine.

Presentation color, icon, animation, material or position never changes an owner state.

## 6. Source / Knowledge / Evidence / Register separation

Card proximity must not flatten epistemic status.

```text
Source != Knowledge
Source != Evidence
Knowledge != Evidence
Evidence != Register Entry
record visible != durable retention
```

A reusable Knowledge item may support a scoped assertion only through the applicable Evidence path, with source, authority, freshness and limits preserved.

Project-specific documents, emails, plans, photographs, quotations or reports do not become reusable Knowledge merely because they appear in a Card collection.

A filesystem Workspace projection remains weaker still:

```text
folder != governed identity
file visible != Evidence
Workspace placement != Knowledge classification
```

## 7. Typed relations

Cards expose only relations needed for the current review.

Typical projections can include:

```text
parent;
scoped_to;
derived_from;
supported_by;
contradicted_by;
produces;
blocks;
resolved_by;
supersedes;
observes;
proposes_action.
```

`PANTHEON_GRAPH_MODEL.md` remains the generic relation owner. The Card Stack controls presentation selection and density only.

A relation is not created because two Cards are adjacent.

## 8. Review density

The first visible projection should be sufficient for orientation and the next decision, not an exhaustive graph dump.

Prefer:

```text
main subject or candidate output;
material open Gate / blocker;
strongest relevant support or contradiction;
current scope / important limit;
next permitted review action.
```

Secondary sources, relations, role-quality expressions and traces remain accessible through detail or child collections when useful.

```text
answer first != hidden Evidence
compact != incomplete governance
complete enough for review != exhaustive graph
```

## 9. Interaction boundary

One interaction should have one stable presentation meaning within the current product surface. Exact current gestures/navigation are owned by the Structured Agency Interface and executable Cockpit navigation contracts.

Generic interaction rules remain:

```text
open / flip
= inspect another face or bounded detail.

navigate
= move among declared siblings, parents or children.

bounded action control
= express review intent or prepare a candidate action.
```

A UI gesture must not directly perform a consequential effect merely because the control is visible.

```text
user interaction
→ bounded UI intent
→ candidate action / review request where needed
→ applicable human and policy gates
→ exact authorized handoff when permitted
→ external execution where applicable
→ returned result / observation remains separately qualified
```

Forbidden collapse:

```text
card click
→ hidden consequential execution
```

## 10. Role-quality visibility

A Role or symbolic-quality projection is useful only when it changes review.

Show it when it materially affects at least one of:

```text
risk;
wording;
Evidence requirement;
missing information;
next safe action;
consultation;
arbitration;
Gate posture.
```

Otherwise keep it as a reference or field.

```text
role quality expression != agent invocation
warning != Decision
consultation trace != hidden chain-of-thought
Gate request != Gate completion
```

## 11. Scene, Deck and Constellation boundary

`Scene`, `Deck` and `Constellation` remain generic composition terms, not an alternative Cockpit information architecture.

They may describe:

- a filtered review collection (`Scene`);
- depth/reading organization (`Deck`);
- a broader relation projection (`Constellation`).

They must not introduce a second list of product roots such as historical `Work`, `Evidence`, `Assets`, `Trace` or `Reference Space` navigation.

The current root constellation is owned elsewhere and may evolve independently of this generic grammar.

```text
Scene != workflow
Deck != persisted process
Constellation != graph runtime
presentation grouping != governed relation
```

## 12. Current implementation boundary

Observed candidate implementation now includes:

- executable Card projection definitions;
- executable canonical Card rendering;
- front/back presentation;
- current sibling/parent/child collection navigation;
- Card status/tag/limit projection;
- bounded action controls whose consequential availability remains server/governance dependent;
- static historical/illustrative Card Stack prototypes under `docs/assets/card-stack/`.

This does not establish:

- production adoption or activation;
- a separate persisted Scene/Deck/Constellation state model;
- automatic Decision resolution;
- automatic approval or memory promotion;
- hidden runtime effects from display interactions.

```text
implementation present != adopted
CI green != production authorization
renderer present != semantic authority
```

## 13. Owner map

| Concern | Current owner |
|---|---|
| controlled terminology | `TERMINOLOGY_BOUNDARIES.md`, `CORE_CONCEPTS_MAP.md` |
| product root spaces/navigation meaning | `PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md` |
| executable root identity/order | Cockpit Navigation Registry |
| generic relations | `PANTHEON_GRAPH_MODEL.md` |
| cross-domain responsibility | `GOVERNANCE_OBJECT_RELATIONSHIP_MAP.md` |
| Capability | Capability governance owners |
| Compétence composition | `COMPETENCE_MODEL.md` |
| Sources / derived records | `RAW_DERIVED_GOVERNED_RECORDS.md`, `SOURCE_INGESTION_RETRIEVAL_MODEL.md` |
| Evidence | `EVIDENCE_PACK.md` and Evidence owners |
| Gates / approval | `APPROVALS.md`, `USER_DECISION_GATE.md` |
| durable memory / Register | `MEMORY.md` and Register owners |
| Decision review specialization | `DECISION_SURFACE_SPEC.md` |
| executable Card renderer | co-located Cockpit implementation |

## 14. Core invariants

```text
Card != underlying object schema
Card != source of truth
Scene != workflow
Scene != complete graph
Deck != persisted process
Constellation != graph runtime
role card != agent invocation
method selected != reasoning validated
source != Evidence
Knowledge != Evidence
Gate != Decision
Decision recorded != action performed
UI intent != runtime command
runtime success != Evidence
record present != Register Entry
projection != persistence
folder != governed identity
```

## 15. Convergence path

This document remains candidate support while a dedicated generic projection grammar reduces duplication across Cockpit projections and static prototypes.

It must not regain product-root topology, object lifecycles or owner-specific schemas. If the remaining grammar becomes fully captured by executable Card contracts plus the Structured Agency Interface, it should be absorbed and removed rather than kept as a parallel doctrine layer.
