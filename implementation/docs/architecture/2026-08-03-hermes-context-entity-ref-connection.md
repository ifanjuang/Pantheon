# Hermes scoped context connection to EntityRef

Date: 2026-08-03

Status: implementation note — non-authoritative.

## Verified overlap

The immutable Context Pack reader previously repeated the same stable identity operations as the shared primitive:

- trim `entity_type` and `entity_id`;
- reject missing dimensions;
- deduplicate by `(entity_type, entity_id)` while preserving order;
- serialize the admitted identity as the existing dictionary shape.

These operations are now delegated to `EntityRef` and `unique_entity_refs`.

The verification also identified `hermes_launch_context` as a real downstream consumer of the normalized admitted identities. It now consumes `EntityRef` explicitly while keeping dictionary-shaped identities in the immutable launch snapshot.

## Connected consumers

```text
hermes_scoped_context
-> Context Pack identity normalization
-> exact admitted-membership comparison
-> manifest and current-owner read serialization

hermes_launch_context
-> launch snapshot materialization
-> dictionary serialization into immutable snapshot payload
```

No compatibility mapping interface was added to `EntityRef`; each boundary serializes deliberately through `as_dict()`.

## Domain behavior retained

`hermes_scoped_context` remains responsible for:

- resolving the exact execution admission and run;
- requiring the run to be `running`;
- verifying immutable Task Contract and Context Pack identities;
- requiring at least one admitted entity;
- refusing any identity outside the exact Context Pack;
- deciding which entity types are materializable;
- re-reading current owner records;
- applying reviewed field projections;
- bounding rich text;
- keeping source dereference, global search, listing and writes unavailable.

`hermes_launch_context` remains responsible for:

- consuming one already-admitted launch window;
- freezing the bounded bootstrap snapshot;
- preserving launch idempotency and expiry;
- keeping runtime submission and dispatch external;
- rejecting automatic retry after reservation.

The historical domain errors are preserved:

```text
stored Context Pack contains an invalid entity reference
stored Context Pack contains an incomplete entity reference
stored Context Pack contains no admitted entity
requested entity is outside the exact admitted Context Pack
```

## Non-equivalences

```text
valid EntityRef != admitted Context Pack membership
admitted membership != materializable entity
materialized current owner read != admission-time snapshot
launch snapshot != current owner read after launch
launch reservation != runtime dispatch
Context Pack inclusion != Evidence
runtime success != Evidence
read access != write authority
```

## Compatibility

The manifest, entity response and launch snapshot payloads continue to expose dictionary-shaped `entity_ref` values. `EntityRef` is internal representation only and does not become an authorization or persistence model.
