# Hermes public context contract

Date: 2026-08-04

Status: implementation note — non-authoritative.

## Purpose

Remove cross-module use of private functions between Hermes context access and launch preparation without changing runtime behavior.

The bounded public contract is:

```text
admitted_entity_refs
require_admitted_entity
materialize_context_entity
```

## Ownership retained

`hermes_scoped_context` remains responsible for:

- normalizing identities stored in an immutable admitted Context Pack;
- requiring exact Context Pack membership;
- applying the reviewed materializable-type list;
- reading current owner records through bounded projections;
- limiting rich text and source exposure;
- refusing global search, global listing, writes and source dereference.

`hermes_launch_context` remains responsible for:

- consuming one already-admitted launch window;
- freezing an immutable launch snapshot;
- idempotency, expiration and operator-reconciliation posture;
- serializing admitted identities and bounded owner projections into that snapshot.

## Unchanged boundaries

```text
valid entity identity != admitted Context Pack membership
Context Pack membership != materializable entity
materialized owner read != Evidence
launch snapshot != current owner read after launch
launch reservation != runtime dispatch
runtime success != Evidence
read access != write authority
```

No scheduler, queue, provider router, tool selection, autonomous retry, runtime memory or approval behavior is introduced.

## Dependency rule

Hermes modules may consume the public bounded context functions. They must not call private names from another Hermes module.

This is a consolidation of an existing implementation seam, not a new domain concept, persistence model or authorization mechanism.
