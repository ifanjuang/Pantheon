# Stable OpenWebUI projection routes

Date: 2026-08-03

Status: architecture convergence validation trace.

## Scope

The read-only OpenWebUI compatibility router now exposes stable responsibility-based paths:

```text
GET /capabilities/openwebui
GET /resources/openwebui
```

The former internal paths are removed without aliases:

```text
GET /v1/system/capabilities/openwebui
GET /v1/system/resources/openwebui
```

## Separation retained

The two projections answer different questions:

```text
/capabilities/openwebui
  -> bounded abstract capability observations

/resources/openwebui
  -> generic governed-resource / Tool Card projection
```

Neither route changes OpenWebUI, activates a binding, authorizes a task or establishes authority.

## Preserved distinctions

```text
available != installed
installed != healthy
healthy != safe
observed != approved
activated != task_authorized
projection != source of truth
UI status != authorization
```

Unknown capability identifiers remain rejected rather than projected into the vocabulary.

## Baseline reduction

```text
generation-named active artifacts:     0
internal versioned route files:        5 -> 4
internal versioned route declarations: 22 -> 20
```

## Boundaries

This slice changes route identity only. It adds no OpenWebUI installation, network probe, provider routing, runtime command, plugin management, approval, Evidence, memory promotion or external action.

## Deferred slices

```text
Paperless gateway
Hermes handoff, admission, active-context and return routes last
```
