# Evolution of Roles, Rites and Spaces

Status: candidate support doctrine — documented non-implemented.
Boundary profile: candidate_support_note.

This document owns only the discipline for introducing, changing, deprecating or superseding Pantheon Roles, Rites, governed Spaces and Card Stack presentation structures.

It does not own:

- Role definitions or jurisdictions;
- Rite lifecycle values or invocation policy;
- Agora semantics;
- Card, Scene, Deck or Constellation definitions;
- underlying object lifecycles;
- Hermes bindings;
- Cockpit schemas or runtime behavior.

Owner documents remain authoritative.

### Broader concept-grammar boundary

`CORE_CONCEPTS_MAP.md` may describe Pantheon as a governed cognitive ecology for navigation: Roles carry standing judgment responsibilities, Rites structure bounded review methods, and governed Spaces separate durable kinds of activity. Governed Objects carry their own identity, state and lifecycle under existing domain owners, while Rules / Contracts / Invariants constrain transitions through their existing owners.

This metaphor does not create a `cognitive_ecology`, `god`, `law`, `object` or `space` registry, schema family, runtime or new authority plane.

```text
concept grammar = navigation
module families = architecture placement
system ownership registry = authority topology
schemas / contracts / tests = enforced invariants
```

The maps are complementary. None may silently redefine another.

```text
Roles judge.
Rites structure method.
Governed Spaces separate durable kinds of activity.
Presentation structures organize bounded exposure.
Hermes executes.
Pantheon governs.
The human decides.
```

## 1. Purpose

Pantheon may evolve, but every new need must first be reconciled against existing concepts.

```text
Context
Trace
Knowledge
Evidence
Claim
ChangeCandidate
Competence
Method
Role
Rite
Governed Space
Scene
Deck
Constellation
Agora
```

Core rule:

```text
Extend before multiplying.
Supersede before duplicating.
Observe before promoting.
```

## 2. Controlled distinctions

### Role

A Role is a standing responsibility of judgment.

A Role is not an agent, prompt persona, executable module, tool router or runtime worker.

Owner references:

- `GOVERNANCE_COLLEGE.md`;
- `docs/domain-packs/architecture/ROLE_FACETS.md`;
- `docs/domain-packs/architecture/ROLE_ACTIVATION_MODEL.md`;
- `docs/domain-packs/architecture/ROLE_REFLEX_COORDINATION.md`.

### Facet or quality

A facet is a stable quality through which a Role perceives, warns, orients, proposes, consults or limits itself around its jurisdiction.

A facet is not a new Role and creates no execution authority.

### Rite

A Rite is a governed method coordinating relevant role viewpoints around a recurring methodological tension.

A Rite is not an agent, workflow, scheduler, queue, approval loop or runtime.

Owner references:

- `docs/governance/rites/README.md`;
- `docs/governance/rites/RITE_INVOCATION_POLICY.md`;
- `docs/governance/rites/RITE_MODES.md`;
- `docs/governance/rites/RITE_EXIT_CRITERIA_AND_CONFLICTS.md`.

### Governed Space

A governed Space is a durable mental and governance distinction between kinds of activity.

Examples:

```text
Governance Reference Space
Project Space
Agora
```

A governed Space may expose objects and decisions but does not inherit authority over their lifecycles.

### Presentation structure

A presentation structure organizes bounded exposure inside the Cockpit.

```text
Scene
= filtered presentation for one review purpose

Deck
= reading and depth order inside a Scene

Constellation
= global relation and project-navigation mode
```

These are owned by `CARD_STACK_MODEL.md`. They are not governed Spaces and must not become backend domains merely because they are visible.

## 3. Stable and flexible elements

| Element | Stable by default | May evolve progressively | Higher-threshold change |
|---|---|---|---|
| Role | jurisdiction and limits | facets, expression thresholds, consultations | create, split, merge or retire |
| Rite | purpose, triggers, anti-triggers, closure and retained outputs | modes, examples, guides and bindings | change purpose, authority boundary or output class |
| Governed Space | durable activity distinction and scope | labels, navigation and projections | create, merge, rename or remove |
| Presentation structure | interaction meaning and owner grammar | layout, density, ordering and disclosure | extend Card Stack grammar |
| Hermes binding | bounded implementation contract | tools, transport and verification technique | broaden scope, data exposure or effects |
| Cockpit projection | faithful display of owner-defined objects | grouping, labels and interaction detail | introduce a semantic object or status axis |

```text
new subject != new Role
new tool != new Role
new screen != new governed Space
new card != new governed Space
new filter != new governed Space
new Rite revision != new Rite by default
binding change != semantic change
```

## 4. Extension-before-creation test

Before proposing a new Role, Rite or governed Space, answer:

```text
What observed recurring problem is not covered?
Which owner documents were checked?
Why is extension insufficient?
What is the smallest semantic commitment?
Who owns its meaning?
Which consumers would depend on it?
What does it explicitly not do?
How can it be removed or superseded?
```

Reduce or reject a proposal that mainly supplies:

- a more attractive metaphor;
- a duplicate name;
- a UI grouping without semantic need;
- a runtime convenience;
- a prompt persona;
- a tool-specific abstraction;
- an approval shortcut.

## 5. Change levels

### Editorial change

Examples:

- wording;
- spelling;
- explanatory example;
- non-semantic navigation label.

Required handling:

```text
owner review
-> confirm no identity, status or authority change
```

### Guidance change

Examples:

- expression threshold;
- consultation guidance;
- Rite mode guidance;
- projection behavior;
- selection heuristics.

Required handling:

```text
bounded governance review
-> representative examples
-> overlap and drift check
```

### Semantic change

Examples:

- Role jurisdiction;
- Rite purpose, triggers or retained outputs;
- creation or removal of a governed Space;
- new authority boundary;
- new canonical status axis.

Required handling:

```text
ChangeCandidate where supported
-> explicit owner review
-> consumer inventory
-> migration and rollback plan
-> promotion decision
```

## 6. Role evolution

Normal sequence:

```text
observed recurring judgment responsibility
-> reconcile existing jurisdictions
-> test facet clarification
-> test consultation, Method, Competence or Rite coverage
-> define uncovered responsibility and limits
-> test representative cases
-> review overlap and authority risk
-> candidate status
-> explicit promotion, revision or rejection
```

Create a Role only when the responsibility:

- recurs across situations;
- requires a stable judgment jurisdiction;
- cannot be safely expressed as a facet;
- cannot be handled by a Method, Competence, Rite or bounded consultation.

Split a Role only when two responsibilities require materially different evidence, escalation or limits and cannot remain understandable through facets.

Merge Roles when their practical jurisdictions are indistinguishable and separation creates repeated consultation, duplicate doctrine or UI noise.

Retirement must identify where each retained responsibility moves. Historical references remain attributable.

## 7. Rite evolution

The owner Rite lifecycle remains:

```text
proposed
active
under_review
deprecated
rejected
superseded
```

Normal sequence:

```text
observed recurring methodological tension
-> check Rite catalogue
-> test existing mode or guide extension
-> define triggers and anti-triggers
-> define involved viewpoints, outputs and closure
-> test fictional and real bounded cases
-> review cost, evidence value and chaining risk
-> candidate review
-> activate, revise, reject or supersede
```

Create a distinct Rite only when the tension, review sequence or retained output is materially different.

Place a Rite `under_review` when it repeatedly:

- fails to change decision or evidence quality;
- creates proof theatre;
- chains with other Rites;
- duplicates another Rite;
- loses retained outputs;
- expands scope through its binding;
- is confused with approval.

Operational guides and Hermes bindings may evolve faster than the governed Rite.

## 8. Governed Space evolution

Create a governed Space only when users must preserve a stable distinction between kinds of activity, for example:

```text
reusable governance reference
!=
project-specific work

visible human deliberation
!=
bounded procedural review
```

Before creation, test whether the need is only:

- a Scene;
- a Deck;
- a card projection;
- a filter;
- progressive disclosure;
- a project selector;
- a bounded Agora discussion.

A governed Space proposal must define:

```text
space_id
purpose and scope
underlying objects projected
entry and exit meaning
relation to existing Spaces
owner documents
allowed exposure
forbidden decisions and effects
merge or retirement path
```

Merge Spaces when users cannot explain their distinction, objects are duplicated without review purpose, or navigation reflects only historical implementation structure.

A rename preserves underlying identities and relations. A label change does not migrate authority.

Removing a Space removes a projection environment, not the governed objects it displayed.

## 9. Presentation-structure evolution

Scene, Deck and Constellation evolve under `CARD_STACK_MODEL.md`.

Normal changes include:

- ordering;
- density;
- labels;
- responsive layout;
- progressive disclosure;
- bounded relation visibility.

A presentation change must not:

- define a backend schema;
- invent a lifecycle;
- collapse status axes;
- authorize execution;
- promote Evidence or memory;
- create a governed Space by implication.

```text
new layout != new ontology
card visible != object authorized
UI status != authorization
```

## 10. Consumer inventory and migration

Before semantic deprecation, merge or supersession, inspect active consumers:

```text
Task Contracts
schemas and registries
Method and Competence guides
Rite definitions and Review Cards
Hermes bindings
Cockpit cards and navigation
API projections
persistence records
active tests
status and authority indexes
active documentation
```

A migration must state:

```text
old identity
successor identity or removal reason
scope of change
effective point
consumer updates
historical attribution
rollback path
```

Do not preserve obsolete identities through permanent compatibility aliases without a documented removal condition.

## 11. Relations and forbidden collapse

Allowed relation:

```text
Role quality observes a tension
-> proposes a Rite
-> ZEUS authorizes or rejects
-> Hermes may execute an admitted binding
-> candidates and observations return
-> a governed Space or presentation structure exposes them
-> governed status or a human decision closes the consequence
```

Forbidden collapse:

```text
Role visible -> Role executed
Rite selected -> Rite authorized
Rite completed -> output approved
Space displays status -> Space owns status
Scene orders work -> Scene defines workflow
Agora discussion -> Decision recorded
binding installed -> task authorized
```

## 12. Promotion criteria

A candidate may become active only when:

- its semantic owner and boundaries are explicit;
- no existing concept adequately covers it;
- overlap and terminology are reviewed;
- examples demonstrate recurring usefulness;
- failure modes and anti-patterns are stated;
- consumers and migration impact are known;
- Pantheon gains no runtime or automatic authority;
- ZEUS and human-decision boundaries remain intact;
- documentation, implementation and projection statuses remain distinct.

```text
documented proposal != active doctrine
active doctrine != runtime implementation
runtime implementation != task authorization
usage observation != Evidence promotion
```

## 13. Anti-patterns

Do not:

- create a god for each professional topic;
- turn facets into sub-agents;
- turn Rites into workflows or automatic chains;
- classify Scene, Deck or Constellation as governed Spaces;
- turn visible Spaces into backend domains;
- let Cockpit cards dictate schemas;
- make a runtime binding canonical doctrine;
- use mythology to conceal ownership or authority;
- treat repeated use as approval;
- infer implementation from documentation status.

## 14. Compact decision rule

```text
Need a new judge?
-> consider a Role only after facet, consultation, Method, Competence and Rite tests fail.

Need a recurring discipline?
-> consider a Rite only after existing Rite, mode and guide tests fail.

Need a durable mental environment?
-> consider a governed Space only after Scene, Deck, filter and projection tests fail.

Need a different presentation?
-> extend Card Stack structures without adding ontology.

Need execution?
-> it belongs to Hermes or another approved runtime.
```

## 15. Final rule

```text
Roles evolve by rare jurisdiction change and careful facet clarification.
Rites evolve through governed methodological review and explicit lifecycle status.
Governed Spaces evolve only when a durable activity distinction is necessary.
Presentation structures evolve without acquiring semantic authority.

Extend before multiplying.
Supersede before duplicating.
Observe before promoting.
Keep execution outside Pantheon.
Keep consequential decisions human.
```
