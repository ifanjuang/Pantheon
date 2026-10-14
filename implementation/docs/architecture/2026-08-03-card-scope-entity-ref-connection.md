# Card scope connection to EntityRef

Date: 2026-08-03

Status: implementation note — non-authoritative.

## Verified overlap

`card_scope.py` previously normalized the same two stable identity dimensions already owned by `EntityRef`:

```text
entity_type
entity_id
```

It also maintained a local `(entity_type, entity_id)` tuple for ordered deduplication of explicit context selections.

This structural behavior is compatible with the shared primitive and is now delegated to it.

## Responsibilities retained by Card scope

The connection does not move the following responsibilities into `EntityRef`:

- authoritative owner lookup;
- supported Cockpit context types;
- Project Contacts identity rules;
- descendant resolution;
- source-ref derivation;
- owning case resolution;
- Cockpit-space allowlist;
- conversion of owner failures into `CardScopeError`.

```text
valid EntityRef != existing owner record
existing owner record != admitted scope
admitted scope != Evidence
scope resolution != authorization of an effect
```

## Compatibility

The public dictionaries returned by:

```text
validate_entity_ref
resolve_explicit_context
resolve_declared_descendants
```

retain their existing shapes. Whitespace normalization is now consistent with the handoff and tag-context consumers.

## Explicit non-goals

This tranche does not:

- generalize entity prefixes;
- create a generic repository;
- move PostgreSQL reads into the primitive;
- change Context Pack semantics;
- alter Hermes admission or execution;
- adopt `SourceRef`, `Revision`, `Pagination` or generic application errors as shared primitives.
