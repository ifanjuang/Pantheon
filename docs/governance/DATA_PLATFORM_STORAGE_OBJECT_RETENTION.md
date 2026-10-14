# Storage Object Retention

Status: candidate governance support doctrine  
Scope: exact raw-byte identity, verified physical retention and provider replacement  
Runtime status: non-executable

## Purpose

This document closes one narrow gap between document-version history and raw-file retention.

Pantheon already distinguishes raw content from governed records and already places physical files in replaceable storage. This note does not add a new storage architecture. It makes the existing `storage_objects` responsibility precise enough for a professional document revision to prove that its historical bytes remain retrievable.

## Core split

```text
Storage Object
= identity of exact retained bytes

Storage Location
= one physical place where those exact bytes can be retrieved

Source
= intake/origin identity

Project Document revision
= professional revision identity
```

These identities are related but not interchangeable.

```text
hash recorded != bytes retained
source_ref known != historical bytes recoverable
storage object != Source
storage object != Project Document
storage object != Evidence
```

## Exact-content identity

A Storage Object records one SHA-256 and byte size for one exact byte payload.

`storage_object_id` is opaque. Pantheon does not require the object id itself to be the hash. An implementation may use content-addressed identifiers, UUIDs or another stable identifier while preserving the same semantic contract.

The object digest is not a professional validation. It only identifies bytes.

## Replaceable locations

A Storage Object may have one or more locations.

Each location identifies:

```text
storage_provider_ref
locator
retention_guarantee
location_status
verification
```

The provider reference and locator are opaque. Pantheon does not enumerate, install, route or adopt providers through this contract.

Possible implementation bindings include local/NAS content-addressed copies, provider-versioned objects or immutable object storage. Those are adapter choices outside Pantheon doctrine.

## Verification

A location may be:

```text
verified
unverified
unavailable
```

`verified` means that the location was read and its complete byte content was checked against the Storage Object `content_sha256` using the declared verification method.

The digest is stored once on the Storage Object. A location does not carry a second supposedly canonical digest that could diverge from it.

```text
location verified != content professionally valid
location available != source approved
storage healthy != safe for every use
```

## Movement and replication

Moving or replicating exact bytes does not change Storage Object identity.

```text
NAS location A
      ↓ replicate / migrate
S3 location B

same exact bytes
= same semantic Storage Object
```

A failed or unavailable location remains an operational fact. It does not rewrite the document revision that referred to those bytes.

## Scope and access

Storage Object identity does not own project authorization.

Access remains a separate server-side responsibility. Physical deduplication or replication must not silently widen visibility between projects, organizations or users.

```text
same bytes != same access rights
content deduplicated != scope merged
storage locator visible != resource authorized
```

## Relation to document versions

A professional revision may bind to one exact retained Storage Object in addition to its technical source/version provenance.

The intended implementation invariant is:

```text
Project Document revision
   -> exact technical capture digest
   -> retained Storage Object with same exact digest
   -> at least one verified retrievable location for durable history
```

A revision may exist before durable retention is complete, but production-ready historical retrieval must expose that retention posture rather than treating a digest row as an archive.

## First candidate implementation

The first `pantheon-mvp` binding may use a configured local or NAS retention root with content-addressed layout:

```text
source path
-> SHA-256
-> atomic copy into retention root keyed by digest
-> re-open retained copy
-> full SHA-256 verification
-> record Storage Object + verified location
```

This is a replaceable implementation binding, not canonical Pantheon storage.

A hard link is not sufficient for the retention guarantee because in-place modification of the shared inode can alter both names.

## Boundaries

```text
stored != validated
hash recorded != bytes retained
location known != location verified
storage object != Source
storage object != professional authority
replicated != provider adopted
provider available != task authorized
runtime copy success != Evidence
```

## Exit condition

This doctrine is sufficient for implementation only when the schema and examples lock:

- one exact object digest;
- one or more replaceable locations;
- explicit location verification;
- no provider routing;
- no access-policy ownership;
- no Evidence or approval effect.