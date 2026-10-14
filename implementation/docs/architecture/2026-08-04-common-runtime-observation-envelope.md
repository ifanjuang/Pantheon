# Common runtime observation envelope

Date: 2026-08-04

Status: implementation note — non-authoritative.

## Verified overlap

The local and network document-runtime observers already emit the same three factual dimensions for every observation:

```text
source
observation_source
observed_at
```

They validate these dimensions through `RuntimeObservation` and preserve every remaining field as adapter-owned payload.

The OpenWebUI router receives a raw compatibility payload from its injected provider. The router now wraps that payload with:

```text
source: openwebui
observation_source: openwebui_compatibility_provider
observed_at: request-time UTC timestamp
```

The envelope metadata remains internal. The `/capabilities/openwebui` and `/resources/openwebui` response shapes remain unchanged.

## Deliberately not shared

The following vocabularies remain local to their adapters and probes:

- reachability status;
- readiness status;
- health endpoint status;
- installation status;
- selection status;
- runtime API or CLI status;
- extraction-quality posture;
- OpenWebUI capability availability;
- compatibility claims.

No universal `started/progress/completed/failed` ontology is introduced. A document-source binding observation, a PDP readiness probe, a Docling health probe, a Hermes inventory observation and an OpenWebUI compatibility payload do not carry the same semantics merely because they are observations.

## Compatibility

Both `/documents/observations` bindings retain their existing flat JSON payloads. OpenWebUI retains its existing capability and governed-resource projections. The common envelope is an internal implementation primitive, not a new API object, persistence table or governed identity.

External protocol paths such as Hermes `/v1/skills` and Pantheon policy `/v1/meta` remain external adapter contracts. They are not internal Pantheon route identities.

## Non-equivalences

```text
reported != observed
observed != true
reachable != healthy
healthy != safe
installed != approved
listed != activated
activated != task_authorized
compatibility payload != dependency adoption
observation != activation decision
runtime success != Evidence
```

The envelope does not install, activate, authorize, schedule, dispatch, route providers, promote memory or admit Evidence.
