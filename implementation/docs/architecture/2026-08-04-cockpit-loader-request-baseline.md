# Cockpit loader request baseline

Date: 2026-08-04

Status: measured optimization record — non-authoritative.

## Scenario

The reproducible Node harness executes one representative Cockpit sequence against the real `cockpit_data_loader.js` with a deterministic fake transport:

```text
load Agency project list once
load Project schema three times for the same token
load one Project bundle once
```

The Project bundle continues to read five independent bounded resources in parallel:

```text
Information
Documents
Knowledge
Work Issues
pending Project ChangeCandidates
```

## Before

Main commit before optimization: `89d95b4d2daf0cd49902ed4797cfa9a7cfada3dd`.

```json
{
  "total_requests": 9,
  "unique_paths": 7,
  "schema_requests": 3,
  "project_bundle_requests": 5
}
```

## After

The loader keeps one in-flight/resolved Project-schema promise for the current read token.

```json
{
  "total_requests": 7,
  "unique_paths": 7,
  "schema_requests": 1,
  "project_bundle_requests": 5
}
```

Measured change:

```text
total requests: -2 / -22.2%
Project-schema requests: -2 / -66.7%
Project-bundle requests: unchanged
```

The measurement is produced by:

```text
tools/measure_cockpit_loader_requests.js
```

and locked by:

```text
tests/test_cockpit_loader_performance_baseline.py
```

## Cache boundary

- cache lifetime is one `PantheonCockpitDataLoader` instance;
- cache identity is the exact current read token;
- another token triggers another authorized read;
- `forceRefresh: true` triggers an explicit authorized reread;
- a rejected request is evicted and remains retryable;
- the server response remains the source of truth;
- no schema authorization is inferred from cache presence.

## Deferred optimization

The five Project-bundle requests are parallel and each represents a distinct server-owned read. This measurement alone does not justify combining them into a new backend model. A future bundle projection requires separate PostgreSQL/API measurements proving a connection or latency bottleneck.

## Non-equivalences

```text
fewer requests != broader authority
client cache != source of truth
cached schema != authorization
authenticated once != authorized forever
parallel request success != coherent transaction
measurement improvement != permission to create a new backend ontology
```
