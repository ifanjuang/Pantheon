# Shared EntityRef Primitive

Status: proposed shared primitive consolidation.

Date: 2026-08-03.

## Accepted primitive

```python
EntityRef(entity_id: str, entity_type: str)
```

The same stable identity behavior was already implemented independently in at least two active paths:

- deterministic Hermes handoff preview and context deduplication;
- Cockpit tag-context projection over server-validated entities.

Both require the same operations:

```text
trim entity_id and entity_type
reject missing identity dimensions
produce a stable tuple key
serialize to the existing dictionary envelope
deduplicate while preserving first-seen order
```

The shared module therefore consolidates existing behavior rather than creating a new semantic layer.

## Boundary

`EntityRef` represents identity only. It does not:

- verify that the owner record exists;
- resolve descendants or sources;
- establish scope membership;
- grant access;
- establish truth or Evidence;
- authorize an effect;
- define a domain status.

Those responsibilities remain in `card_scope`, application use cases, repositories and governance gates.

```text
valid identity shape != existing entity
existing entity != admitted scope
admitted scope != Evidence
EntityRef != authorization
```

## First consumers

```text
mvp_vertical/hermes_handoff_preview.py
mvp_vertical/card_tag_context.py
```

Other modules may migrate only when they use exactly the same identity semantics. This PR does not force every `entity_id` field into the primitive.

## Candidates deliberately rejected in this tranche

### SourceRef

Source references still include multiple schemes and domain-specific capture or Evidence semantics. A common wrapper is premature.

### Revision and ExpectedRevision

Technical schema revisions, Project revisions, Work Issue versions and optimistic-write expectations are not interchangeable.

### IdempotencyKey

HTTP length validation is repeated, but the persistence scope and replay semantics remain use-case specific.

### Pagination

Endpoints use different limits, ordering and cursor/offset assumptions. A universal pagination model would hide meaningful differences.

### ApplicationError

Current errors preserve domain-specific conflict, not-found, stale-write and validation meaning. A generic base class would not remove enough behavior to justify the coupling.

## Exit checks

- two active consumers use the same representation;
- no PostgreSQL, FastAPI, adapter or projection dependency enters the primitive;
- existing payload shapes remain unchanged;
- domain-specific validation and authorization stay outside the primitive;
- full CI remains green.
