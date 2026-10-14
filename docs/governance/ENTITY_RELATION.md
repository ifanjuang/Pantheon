# Entity Relation

Status: canonical contract for the first explicit Information relations.

## Objective

Represent an explicit, project-scoped relation without creating a second object graph or reusing the spatial APU vocabulary.

```text
EntityRef(from)
-> closed relation type
-> EntityRef(to)
```

The physical key shape is generic. The first admitted scope is deliberately narrower:

```text
from.entity_type = information
to.entity_type   = information
```

Other endpoint types require an explicit contract extension. Availability of the generic columns does not authorize them.

## Canonical vocabulary

Direction is always `from -> to`.

```text
responds_to  = répond à
relies_on    = s’appuie sur
supersedes   = remplace
contradicts  = contredit
```

The vocabulary is closed. `contains`, `derives_from`, `completes` and `compares_with` remain outside this contract.

## Identity and project scope

Each endpoint is an `EntityRef`:

```text
entity_type
entity_id
```

`EntityRef` is an identity carrier only. It does not validate existence, project scope, access, truth or authorization.

The executable owner must therefore verify, before accepting an edge:

1. both endpoint types belong to the admitted closed set;
2. both endpoint identities exist;
3. both endpoint owners resolve to one Project;
4. that Project equals the relation `project_ref`;
5. `from` and `to` are not the same EntityRef;
6. the same active directed edge does not already exist.

A polymorphic database foreign key is not required. This follows the existing `agency_project_claims.backing_entity_type + backing_entity_id` precedent. The loss of native referential integrity must be compensated by the closed type check, the project-scope trigger, domain validation and integrity tests.

## Authority

A human may explicitly create or retire a relation through the governed Cockpit surface.

A runtime or Hermes result may only produce a candidate:

```text
relation_candidate stored
!= canonical relation created
```

The candidate must pass a separate human action before the canonical relation owner is mutated.

Recording the relation does not validate either Information, create Project truth, admit Evidence, promote memory or authorize a Task.

## Lifecycle

The relation identity, endpoints and type are immutable. A correction is represented by retiring the old edge and creating a new one.

```text
active relation
-> explicit retirement event
-> retired relation
```

No review status belongs on the canonical edge. Candidate review remains in the Execution Result lane.

## Boundaries

```text
generic columns != universal graph authority
explicit relation != inferred candidate relation
relation recorded != project fact validated
supersedes relation != Information revision
contradicts relation != contradiction resolved
same project != same authorization scope
retired relation != deleted history
```

## Placement

Pantheon-Next owns the schema, vocabulary and boundaries.

`pantheon-mvp` owns PostgreSQL persistence, project-scope enforcement, APIs, events and Cockpit projections.

Hermes may propose bounded relation candidates but does not own canonical relation creation.
