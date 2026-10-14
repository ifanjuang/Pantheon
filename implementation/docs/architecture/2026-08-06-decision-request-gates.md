# Decision Requests and Decision records — tranche E

Date: 2026-08-06
Status: executable candidate, not deployed or authorized for production.
Upstream contract: `Pantheon-Next@5e61b39e4d17ddbc58cafda9c4faebb70ccae1ba`.

## Objective

Separate unresolved human attention from recorded human determination.

```text
Decision Request / Gate
→ explicit human response
→ immutable Decision record
```

A WorkIssue in `review` remains a Tâche awaiting review. Accepting or returning
that Tâche uses `/work/issues/{id}/review`. It is projected as `work_review`, not
as a Decision, and does not create a Decision record.

## Reused owners

```text
Decision outcome vocabulary   mvp_governed_loop_objects.schema.yaml
WorkIssue lifecycle            mvp_vertical.work_issues
WorkIssue Project scope        work_issue_scope_links
Project                         agency_projects
Cockpit navigation             navigation registry + projection definitions
```

The existing `decision_record` contract remains the only authority for a human
determination. `DecisionRequest` is a separate Gate and attention item. There is
no semantic `agency_decision` entity; the `agency_` prefix is only the PostgreSQL
namespace for agency-owned tables.

## Persistence

```text
agency_decision_requests
agency_decision_options
agency_decision_records
agency_decision_events
```

Request review material is immutable. A request may only move from `pending` to
`resolved` or `cancelled`, with one exact revision increment. Options, Decision
records and events are immutable and retained.

One pending blocking request may target a WorkIssue. If Project and WorkIssue are
both supplied, the WorkIssue must carry an active explicit Project scope.

## Classification

```text
project_ref = null
→ demande non classée
→ boîte globale Décisions

project_ref = <project>
→ demande classée
→ projection du Projet correspondant uniquement
```

The same `decision-request:{request_id}` identity is never copied into an
agency-level owner. Project classification is a placement rule, not a new type.

## API

```text
POST /decision-requests
GET  /decision-requests
GET  /decision-inbox
GET  /agency/projects/{project_id}/decision-requests
GET  /work/issues/{issue_id}/blocking-decision-request
GET  /decision-requests/{request_id}
POST /decision-requests/{request_id}/resolve
POST /decision-requests/{request_id}/cancel
GET  /decisions/{decision_id}
```

`/decision-inbox` is the read-only global Cockpit projection and enforces
`project_id IS NULL`. The general list route remains an administrative read
surface and does not define the navigation classification.

Canonical writes require the editor key and `X-Pantheon-Human-Actor`. Hermes
cannot create or resolve these records through its runtime key.

## Cockpit

The registry-backed root `space:decisions` contains only pending unclassified
Decision Requests. Requests carrying a `project_ref` appear only in the matching
Project child collection.

The `Décider` action reads the current request and records one human response.
It never submits a Hermes handoff, resumes a Task or applies an external effect.

## Resolution consequences

Every Decision record explicitly records:

```text
work_issue_transitioned = false
runtime_continuation_authorized = false
action_executed = false
result_validated = false
```

A later continuation, revised Task Contract or manual operation must be prepared
separately and retain the Decision reference.

## Boundaries

```text
Decision Request != Decision
global Decisions space != agency Decision authority
unclassified != agency semantic type
Work review != Decision
request visible != approval
Decision recorded != WorkIssue transitioned
Decision recorded != runtime resumed
Decision recorded != action executed
Decision recorded != result validated
retrieved source != Evidence
```

No queue, scheduler, dispatcher, retry engine, runtime, provider router,
automatic approval, Evidence admission or memory promotion is introduced.
