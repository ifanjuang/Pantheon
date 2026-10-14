# Card Projection Definition Model

Status: active support doctrine — implementation-bounded.
Boundary profile: active_support_doctrine.

## Purpose

A Card Projection Definition describes how an already governed entity may be exposed by the Cockpit. It does not define the underlying business object, lifecycle, authority, truth, Evidence status, authorization or execution.

```text
owner object + owner schema
→ authoritative projection
→ Card Projection Definition
→ card model
→ Cockpit renderer
```

This model complements `CARD_STACK_MODEL.md`.

```text
CARD_STACK_MODEL
= generic Card / Scene / Deck / Constellation projection grammar

Card Projection Definition
= machine-readable mapping for bounded configurable Card projections
```

## Scope

A definition may declare:

- stable projection identity and revision;
- applicable entity types;
- card role and presentation family;
- mappings for identity, title, summary, category, index and date;
- tag source fields and visible subject limit;
- bounded detail-field selection;
- references to owner-projected actions and relations;
- static presentation text for projection-only entities such as navigation spaces.

A definition must not contain:

- SQL, endpoint URLs or transport rules;
- lifecycle transitions;
- approval, authorization or permission decisions;
- provider, runtime or binding selection;
- Evidence or truth qualification;
- hidden execution instructions;
- complete business-object schemas.

## Ownership

Pantheon-Next owns the definition contract and its boundaries.

Operational definition instances are co-located with the Cockpit implementation under `implementation/mvp_vertical/cockpit/registries/`. The executable Navigation Registry owns root identity and order; Card Projection Definitions own presentation mapping only.

The authoritative object projection remains owner-controlled for entity data, status, available actions, relations and permissions.

```text
projection definition valid != object valid
field visible != field editable
action visible != action authorized
renderer compatible != semantically adopted
projection definition != navigation authority
```

## Minimal contract

A definition can contain:

```yaml
schema_id: cockpit.card_projection_definition
revision: 1
definition_id: navigation-space
entity_types: [cockpit_space]
card_role: container
presentation_family: project
identity:
  id_field: entity_id
  title_field: title
summary:
  static: Bounded navigation space.
detail:
  static_rows: []
actions:
  source: server_projection
relations:
  children_source: navigation_registry
```

Mappings may be field-based or static, but static values are limited to projection-only metadata. They must not override an owner-projected status, authorization, Evidence posture or consequential decision.

## Current implementation boundary

The first navigation pilot has converged into the co-located Cockpit candidate. Root cards are now derived from the executable Navigation Registry and corresponding Card Projection Definitions rather than from a root list repeated in this document.

The definition layer may configure presentation mapping, but the following remain outside its authority:

- root identity and order;
- Project, Information, Work, Decision or Evidence business rules;
- status calculation;
- available-action calculation;
- child collection assembly;
- API loading and authorization;
- renderer-specific layout algorithms.

```text
registry root set != projection definition set
Card mapping != business rule
Card visible != authorized effect
```

## Evolution rule

A new configurable field is admitted only when:

1. at least two projections need the same mapping concept, or current implementation proves a stable need;
2. the field has a clear owner and boundary;
3. moving it to configuration reduces hard-coded duplication without hiding business logic;
4. validation remains deterministic;
5. rollback does not require data migration.

## Core invariants

```text
card projection definition != underlying object schema
projection configuration != workflow
projection relation source != relation authority
static label != lifecycle state
visible action != authorized action
registry-selected definition != dependency adoption
Navigation Registry != Card Projection Definition
Cockpit rendering != execution
```
