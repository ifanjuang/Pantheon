# Stable Agency routes

Date: 2026-08-03

Status: applied implementation refactor — internal route identity only.

## Scope

This tranche removes the generation prefix from the global Agency Data HTTP surface and its active Cockpit consumers.

Included:

```text
Agency Data
Project Information
People and Organizations
Project ChangeCandidates
ProjectClaims
Cockpit read/editor/create/decision consumers
static Cockpit demo projection
```

Excluded:

```text
Hermes admitted project ChangeCandidate capability
Project Documents and Knowledge routes
Work Issue and Work Decision routes
Hermes execution and handoff routes
external protocol versions
```

## Route migration

Eighteen mounted endpoints become stable responsibility paths. Because GET and POST share two paths, the architecture baseline records sixteen unique route patterns.

Examples:

```text
/v1/agency/projects                         -> /agency/projects
/v1/agency/schema/project                   -> /agency/schema/project
/v1/agency/projects/{id}/information        -> /agency/projects/{id}/information
/v1/agency/projects/{id}/claims             -> /agency/projects/{id}/claims
/v1/agency/projects/{id}/change-candidates  -> /agency/projects/{id}/change-candidates
```

The old paths are removed in the same change. No compatibility aliases are retained.

## Preserved boundaries

```text
global Agency read != Hermes admitted context
global Agency write != Hermes mutation authority
ChangeCandidate status != Project status
ProjectClaim != Project mutation
ProjectClaim != Evidence
route identity != data revision
```

PostgreSQL remains the Agency Data system of record. Human writer gates, optimistic revisions, idempotence and ChangeCandidate review semantics are unchanged.

## Debt reduction

```text
internal versioned route files:        13 -> 10
internal versioned route declarations: 64 -> 48
```

No runtime, schema, persistence or authority model is added.
