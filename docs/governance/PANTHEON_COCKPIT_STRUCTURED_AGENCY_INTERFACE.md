# Pantheon Cockpit — Structured Agency Interface

Status: candidate support doctrine — executable candidate foundations are co-located; live owner integrations, adoption and production activation remain incomplete.
Boundary profile: candidate_support_note.

This document owns the Cockpit product composition boundary: the meaning of the root navigation spaces, spatial movement between their projections, the universal product-level Card anatomy, Context Resolver UX and cross-space presentation rules.

It does not own the records displayed by those projections, their lifecycles, persistence, authorization or runtime execution.

```text
owner records + governed relations + bounded runtime observations
                         ↓
                    Cockpit Cards
                         ↓
                human review / intent
```

```text
Card != source of truth
projection != persistence
retrieved != Evidence
runtime success != authorization
folder != governed identity
```

## 1. Product boundary

Pantheon Cockpit is the user-facing spatial interface over the structured agency system and Pantheon governance surfaces.

```text
Pantheon Next governs.
Hermes or another admitted runtime executes bounded external work.
The Cockpit exposes projections and captures bounded intent.
Owner systems retain authority where declared.
The human decides consequential effects.
```

The Cockpit must simplify use without flattening semantic ownership.

This document therefore owns:

- current root-space product meaning;
- spatial navigation behavior at product level;
- universal front/back Card expectations;
- Context Resolver namespace UX;
- cross-space presentation and scope rules;
- the rule that presentation may compose several owners without becoming one.

It does not replace:

- `CARD_STACK_MODEL.md` for generic Card / Scene / Deck / Constellation grammar;
- `PANTHEON_GRAPH_MODEL.md` for generic node/relation semantics;
- `TASK_CONTRACTS.md` and Execution Admission contracts for task/run legitimacy;
- `EVIDENCE_PACK.md` for Evidence qualification;
- `COMPETENCE_MODEL.md` and Capability owners for reusable-ability and technical-capability boundaries;
- `AGENCY_DATA_SYSTEM_OF_RECORD.md` for Agency Data ownership;
- `DOCUMENT_LIFECYCLE_GOVERNANCE.md` for Document lifecycle semantics;
- `DECISION_SURFACE_SPEC.md` and Decision owners for formal decision review;
- `CATEGORY_CLASSIFICATION_MODEL.md` for Category-backed Knowledge organization;
- the Workspace reader for filesystem projection safety.

If presentation guidance conflicts with an owner contract, the owner contract wins.

## 2. Current root constellation

The executable root identity and order are owned by the co-located Navigation Registry, not duplicated in HTML or inferred from this document.

Current registered roots are:

```text
space:pantheon
space:affaires
space:connaissances
space:workspace
space:outils
space:decisions
```

Their current product sequence is therefore:

```text
Pantheon ↔ Affaires ↔ Connaissances ↔ Workspace ↔ Outils ↔ Décisions
```

The registry is the executable configuration owner for this order. This document owns what those spaces mean to a user and the constraints on their composition.

A change to root identities or order must update the Navigation Registry, Card projection definitions, relevant tests and this product explanation together. No static menu or documentary list may become a competing executable authority.

## 3. Why Workspace is a root and Compétences is not

`Workspace` currently has a demonstrated bounded source: explicitly configured filesystem roots projected as ephemeral read-only Cards.

```text
filesystem path != Project
folder name != Category
folder location != Knowledge
file presence != activation
retrieved file != Evidence
workspace projection != governed identity
```

The Workspace reader predates its root placement and remains independently useful. Root placement is a reversible presentation choice; it does not make folders authoritative objects.

`Compétence` remains a governed semantic concept, not a root merely because users may need reusable abilities.

The current code has a `#` Context Resolver namespace for capabilities, but no live capability provider is attached to that namespace. Existing Capability Passport, Binding, Activation, Compatibility, Task Contract and Execution Admission owners already govern the technical facts needed for a future composed projection.

Therefore:

```text
Compétence != Workspace
Compétence != Tool catalogue
Compétence != Hermes Skill inventory
Capability available != task authorized
```

A public `Compétences` root must not be created until a useful projection can be composed from existing governed owners. It must not require a new competence registry merely to satisfy an old navigation promise.

Future evidence may justify replacing or regrouping `Workspace`; that would be a separate governed Space/product-navigation change with consumer inventory and rollback path.

## 4. Spatial navigation

At root depth, left/right moves among the registered root siblings.

At deeper depth, left/right moves only among siblings in the current collection.

```text
Affaires
  ↓
Project A ↔ Project B ↔ Project C
```

A deeper horizontal gesture must not silently jump into another root space.

Vertical semantics are:

```text
descend = enter the current Card's declared child collection
ascend  = return to the parent collection
```

Navigation never moves, renames, reclassifies or persists the source record.

Equivalent navigation must remain available by touch, click, trackpad and keyboard. Reduced-motion preferences must not remove access to the same semantic operations.

A location indicator should expose current depth, for example:

```text
Affaires / Verger / Documents
```

## 5. Universal Card product contract

A Card is a stable projection of one identifiable owner or governed object, or a declared presentation container.

```text
one identity
many bounded projections
no identity duplication merely for display
```

Generic Card/Scene/Deck/Constellation semantics remain owned by `CARD_STACK_MODEL.md`.

At product level, a Card should expose a consistent anatomy:

```text
┌──────────────────────────────────────────┐
│ context / index              state rail  │
│                                          │
│ TITLE                                    │
│ summary / decision-useful content        │
│                                          │
│ family/context          tags / metrics   │
└──────────────────────────────────────────┘
```

Front/back meaning remains:

```text
front = minimum useful orientation
back  = detail + provenance + relations + permitted actions
```

Front and back are two faces of one projection, not two records.

Preserve the Card Stack escalation rule:

```text
Field when normal.
Sub-card when it blocks, conflicts, fails, repeats,
is newly proposed, changes scope or requires arbitration.
```

Visual family, identity, tag and status colors remain independent concepts. A color or animation never changes owner state.

## 6. Context Resolver

The Context Resolver is a client interaction/federation layer over bounded providers. It is not the canonical index, a memory engine or an authorization mechanism.

Current namespaces are:

```text
_  Affaires / Projects
#  Capabilities
@  People
*  permitted global federation
```

Current observed implementation state:

- `_`, `@` and a bounded global contribution can be attached by the Agency Data binding;
- `#` is defined by the resolver but currently has no attached live capability provider;
- several providers may contribute to one namespace;
- provider failure is returned as an observation rather than silently converted into a positive result.

Search selection must preserve:

```text
search result != selected
selected != relied upon
relied upon != Evidence
```

Stable identity is preferred over label matching. A display-only candidate without stable identity must not silently become durable context identity.

Browser code must not receive third-party provider secrets merely to perform federated search.

## 7. Tags and presentation qualifiers

Tags are reusable presentation/retrieval qualifiers. They do not establish truth or authorization.

```text
tag != proof
tag != regulatory conclusion
tag != Evidence
tag != authorization
```

The Cockpit may display bounded owner-provided tags, aliases and status projections. It must not create a second canonical tag vocabulary merely because a picker or icon exists.

New vocabulary remains candidate until the applicable owner path accepts it.

## 8. Root-space responsibilities

### Pantheon

Pantheon is the primary conversational/governance surface.

It may project:

- pending change candidates;
- current or recent bounded runtime observations;
- explicit context selection;
- consequential questions requiring human attention.

```text
run visible != run authorized
run completed != result approved
time-based state shown in Cockpit != externally owned time-based execution
```

### Affaires

Affaires projects Project/Agency Data identities and their bounded child collections.

PostgreSQL Agency Data remains the default system of record where declared by its owner doctrine. Cockpit presentation does not transfer ownership.

Project Cards may compose contacts, documents, facts, issues and applicable Knowledge only through their existing owner relations.

```text
Card proximity != relation
Project field != Evidence
external owner record != Pantheon governance record
```

### Connaissances

Connaissances projects reusable references and Category-backed navigation.

```text
Document != Knowledge
Knowledge != Evidence
Knowledge != memory
project-specific material != agency-general Knowledge
```

Project-to-general promotion remains governed by Knowledge owners, not by drag/drop or navigation placement.

### Workspace

Workspace exposes configured human filesystem trees through the read-only Workspace collection seam.

It is deliberately weak semantically: directory structure is useful for navigation but cannot determine governed identity.

The architecture-agency recommended organization profile is owned by `docs/domain-packs/architecture/DOCUMENT_AND_KNOWLEDGE_ORGANIZATION.md`. `Affaires` and `Connaissances` are Cockpit Space projections, not required physical root-folder names. A differently organized tree remains usable and may be mapped or classified without being moved.

Workspace Cards are ephemeral projections and expose no implicit mutation, classification, approval or Evidence action.

### Outils

Outils exposes replaceable technical means and bounded observations such as tools, Skills, bindings, models or runtimes where supported by existing owners.

```text
installed != approved
enabled != task authorized
healthy != safe
update available != update authorized
Tool != Compétence
```

Consequential changes remain governed and externally executed.

### Décisions

Décisions projects human-attention requests and formal Decision objects without collapsing them.

```text
human attention != formal Decision
Decision Request != Decision
Decision recorded != effect executed
appearance in Décisions != copied owner record
```

Decision/Work Issue blocking follows the current Decision Request contract and does not imply automatic runtime continuation.

## 9. Cross-space composition

A Card may compose fields from several bounded sources when attribution remains visible.

Conceptually:

```text
owner identity
+ owner relations
+ governed qualification
+ runtime observations
+ derived/search data
        ↓
Cockpit projection
```

Physical co-location does not collapse ownership:

```text
same database != same authority
cached value != current owner value
projection != ownership transfer
```

A relation is not created because two Cards appear next to each other.

## 10. Hermes interaction boundary

Eligible Cards may expose a Hermes question or candidate-action control.

The interaction must remain scoped to the current object, declared descendants/relations and explicit user additions. UI context cannot widen authorization by itself.

```text
question sent != action authorized
handoff prepared != execution admitted
execution admitted != professional approval
technical receipt != Evidence
```

A historical answer remains tied to the context snapshot used to produce it. Changes in sources do not silently revalidate the answer.

## 11. Implementation ownership

The current co-located candidate implementation lives under `implementation/mvp_vertical/cockpit/` and adjacent bounded seams.

Observed executable foundations include:

- one live/demo boot chain;
- Navigation Registry loading and validation;
- Card projection definitions and rendering;
- spatial navigation and child-collection assembly;
- Context Resolver provider federation;
- read-only Agency Data projection seams;
- Category-backed Knowledge navigation foundations;
- Decision Request projection foundations;
- Tool Card/capability projection foundations;
- read-only Workspace collection projection and API routes;
- bounded handoff/candidate-action surfaces.

These are candidate implementation facts, not proof of adoption, production activation or live external availability.

The frontend must continue to reuse those seams rather than introduce a second Cockpit application or hard-coded root topology.

## 12. Current qualification matrix

| Concern | Current observed state |
|---|---|
| root identities/order | executable and tested candidate; Navigation Registry owned |
| header root menu | derived from Navigation Registry and Card definitions |
| Card projection definitions/renderer | executable and tested candidate |
| spatial navigation | executable and tested candidate |
| Context Resolver core/federation | executable candidate |
| `_` / `@` Agency Data providers | bounded read-only binding exists |
| `#` capability provider | namespace exists; live provider absent |
| Workspace collection reader | executable and tested read-only candidate |
| Workspace root projection | executable and tested candidate |
| Category-backed Knowledge navigation | executable foundation |
| Decision Request projection | executable foundation |
| Tool Card projection | executable foundation; live canonical capability feed incomplete |
| live Agency Data deployment | not established by repository tests alone |
| live Hermes transport | not established by repository tests alone |
| live Notion collaboration | not established |
| production adoption/activation | not established |

```text
CI green != production authorization
implementation present != activated
runtime reachable != capability admitted
```

## 13. Change discipline

Root-space changes are product/navigation changes with governance consequences because they shape user mental models.

Before adding, removing, renaming or merging a root:

1. identify the recurring user distinction;
2. check whether a Card, collection, filter or Scene is sufficient;
3. inventory registry, Card definitions, routes, tests and active documentation;
4. preserve underlying object identities and owners;
5. state migration and rollback behavior;
6. qualify the resulting implementation and documentation together.

A root must not exist solely to mirror historical implementation structure or an unimplemented aspiration.

## 14. Remaining demonstrated gaps

The current topology does not require a new owner to be useful.

Remaining gaps include:

- no live composed capability provider for the `#` Context Resolver namespace;
- no demonstrated need for a separate public `Compétences` root after owner convergence;
- live external Agency Data, Hermes and collaboration environments remain deployment-dependent;
- some owner projections remain foundations rather than complete professional verticals;
- product adoption and production activation remain separate decisions.

If a professional vertical later demonstrates that reusable abilities need a first-class root, compose it from existing owners first and then reassess the root constellation.

## 15. Forbidden collapses

```text
user-friendly UI != flattened semantics
search != context admission
Card != source of truth
card comment != canonical Knowledge
Hermes answer != professional validation
Document view in Décisions != Decision record
runtime host observed != healthy/safe
model discovered != task-authorized
role reference != runtime agent
Capability candidate != admitted Capability
Capability admitted != task authorized
Tool installed != Capability admitted
Workspace folder != governed identity
Workspace file != Evidence
projection != persistence
```

The Cockpit may make Pantheon simpler to operate. It must not make consequential distinctions disappear.
