# Stable Work routes

Date: 2026-08-03

Status: applied implementation refactor — internal route identity only.

## Scope

This tranche completes the Work half of architecture-convergence step F. It removes the generation prefix from the Work Issue read surface and the human Work Decision surface.

Included:

```text
exact Work Issue listing by case_ref
Work Decision read
human validate decision
human refuse-for-rework decision
Cockpit Work loader
static demo Work projection
Cockpit Information and Work action adapter
```

Excluded:

```text
Document and Knowledge routes
resource profiles
Knowledge update and preview routes
Hermes handoff, admission, execution and return routes
external protocol versions
```

## Route migration

```text
/v1/projects/{project_id}/work-issues
    -> /work/issues?case_ref={exact_case_ref}

/v1/work-issues/{issue_id}/decision
    -> /work/issues/{issue_id}/decision

/v1/work-issues/{issue_id}/decision/validate
    -> /work/issues/{issue_id}/decision/validate

/v1/work-issues/{issue_id}/decision/refuse
    -> /work/issues/{issue_id}/decision/refuse
```

The list route is owned by the Work responsibility. A Project identifier may be supplied as the exact `case_ref`, but the route does not infer Project ownership, traverse parents or broaden scope.

The old paths are removed in the same change. No compatibility alias is retained.

## Preserved boundaries

```text
Work Issue != Project
case_ref match != inferred project ownership
Work Decision card != new decision model
human validation != Evidence admission
result candidate != accepted result
runtime_success != Evidence
route identity != schema or data revision
```

The human editor gate, actor requirement, optimistic Work Issue version and idempotence remain unchanged. Hermes receives no new authority.

## Incidental convergence correction

The shared Cockpit action module still referenced the retired `/v1/agency/information/...` paths after the Agency route migration. Because the same module owns Work decisions, this tranche aligns those three Information calls with the already-authoritative `/agency/information/...` routes. No Agency behavior or contract changes.

## Debt reduction

```text
internal versioned route files:        10 -> 9
internal versioned route declarations: 48 -> 44
```

No workflow engine, scheduler, queue, runtime, schema, persistence or automatic approval layer is added.
