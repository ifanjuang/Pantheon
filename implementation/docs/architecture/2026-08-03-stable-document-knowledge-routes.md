# Stable Document and Knowledge route migration

Date: 2026-08-03

Status: architecture convergence validation trace.

## Scope

This atomic slice removes the internal `/v1` prefix from the bounded Document, Knowledge, edit-request and original-preview routes owned by `mvp_vertical/cockpit_api.py`.

```text
GET  /projects/{parent_project_id}/documents
GET  /documents/{document_id}
GET  /documents/{document_id}/chunks
GET  /projects/{parent_project_id}/knowledge
GET  /knowledge/{knowledge_id}
GET  /knowledge/{knowledge_id}/markdown
POST /documents/{document_id}/knowledge
PUT  /knowledge/{knowledge_id}
POST /knowledge/{knowledge_id}/edit-requests
PUT  /edit-requests/{request_id}/proposal
GET  /edit-requests
POST /edit-requests/{request_id}/apply
GET  /documents/{document_id}/markdown
GET  /documents/{document_id}/preview-link
GET  /previews/{document_id}/original
```

The direct `PUT /knowledge/{knowledge_id}` remains deliberately retired and returns HTTP 410. Moving it to the stable route does not restore the direct-write capability.

All old `/v1/...` route declarations are removed in the same change. No aliases are retained.

## Active consumers

The following consumers are migrated atomically:

```text
mvp_vertical/cockpit/data/cockpit_data_loader.js
mvp_vertical/cockpit/actions/card_actions.js
mvp_vertical/cockpit/demo_bootstrap.js
mvp_vertical/mobile_editor/app.js
mvp_vertical/mobile_editor/sw.js
```

The Cockpit project bundle reads stable Document and Knowledge collections. The chunk inspector reads the stable Document chunk route. The static demo simulates the stable paths. The mobile editor uses stable project Knowledge, Markdown and edit-request routes.

## Preview-link boundary

Signed preview links now target:

```text
/previews/{document_id}/original
```

The signature payload, expiry, bounded source resolution, inline disposition and no-store headers are unchanged.

```text
signed link != public document
preview access != Evidence
original available != professionally validated
```

## Mobile cache boundary

Removing `/v1` invalidated the previous service-worker shortcut that excluded all API paths through one prefix.

The service worker now:

- uses a new technical cache revision;
- explicitly bypasses known API roots;
- caches only the static editor shell;
- avoids persisting authenticated Document, Knowledge, Agency, Work, Hermes or resource responses.

This is cache policy, not authorization.

## Preserved behavior

The migration preserves:

- bearer-key separation between read, editor and Hermes access;
- bounded Document and Knowledge reads;
- exact project scoping;
- Knowledge publication provenance and idempotency;
- signed project-scoped UPDATE gate;
- direct Knowledge PUT retirement;
- edit-request queue/proposal/apply separation;
- preview-link expiry and source-root confinement;
- derived Markdown status headers;
- no automatic Evidence or memory promotion.

## Baseline reduction

```text
generation-named active artifacts:     0
internal versioned route files:        8 -> 7
internal versioned route declarations: 38 -> 24
```

## Boundaries

```text
Document card != source of truth
chunk indexed != verified
Knowledge generated != Evidence
edit proposal != applied edit
Hermes proposal != human approval
preview link != unrestricted file access
write persisted != professional validation
UI state != authorization
```

No runtime, scheduler, queue, provider router, plugin manager, automatic approval, memory promotion or external action is added.

## Deferred slices

```text
Document runtime observations
OpenWebUI capability/resource projections
Paperless gateway
Hermes handoff, admission and return routes last
```
