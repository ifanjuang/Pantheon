# Stable Cockpit shell route migration

Date: 2026-08-03

Status: architecture convergence validation trace.

## Scope

This slice removes the internal `/v1` prefix from the six routes composed directly by `mvp_vertical/cockpit_shell.py`.

```text
GET  /projects/{parent_project_id}/resource-profiles
POST /projects/{parent_project_id}/effects/preview
POST /projects/{parent_project_id}/knowledge/{knowledge_id}/navigation-profiles/preview
POST /projects/{parent_project_id}/knowledge/{knowledge_id}/site-manifests/preview
POST /projects/{parent_project_id}/knowledge/{knowledge_id}/updates/preview
POST /projects/{parent_project_id}/knowledge/{knowledge_id}/updates/apply
```

The old `/v1/projects/...` shell routes are removed in the same change. No aliases are retained.

## Consumers

The mobile editor now uses the stable Knowledge update preview/apply routes.

The following routes remain versioned because they belong to the later Documents and Knowledge API slice:

```text
/v1/projects/{project_id}/knowledge
/v1/knowledge/{knowledge_id}/markdown
/v1/knowledge/{knowledge_id}/edit-requests
```

## Residual Agency correction

The route review identified two active Cockpit consumers left behind by the completed Agency migration:

```text
mvp_vertical/cockpit/context/context_selection.js
mvp_vertical/cockpit/information_view_adapter.js
```

They now use `/agency/...` and explicitly reject regression to `/v1/agency/...` through static tests.

This correction restores consistency with the already merged Agency server contract. It introduces no new Agency route or compatibility layer.

## Preserved behavior

The migration changes route identity only. It preserves:

- read/editor authentication;
- signed Knowledge update preview;
- exact human actor requirement;
- optimistic version checks;
- idempotency;
- proposal-only effect previews;
- proposal-only site manifest and navigation profile previews;
- no network execution from preview endpoints;
- no approval or Evidence promotion.

## Baseline reduction

```text
internal versioned route files:        9 -> 8
internal versioned route declarations: 44 -> 38
generation-named active artifacts:     0
```

## Boundaries

```text
stable route != broader authority
preview success != action authorization
Knowledge update applied != Evidence
resource profile observed != provider adoption
site manifest preview != crawl authorization
navigation profile candidate != skill installation
Agency read success != Evidence
UI state != authorization
```

No runtime, scheduler, queue, provider router, plugin manager, automatic approval, memory promotion or external action is added.

## Deferred slices

```text
cockpit_api.py Documents and Knowledge routes
Document runtime observations
OpenWebUI and Paperless resources
Hermes routes last
```
