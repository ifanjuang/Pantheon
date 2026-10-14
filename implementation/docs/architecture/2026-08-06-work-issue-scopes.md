# WorkIssue scopes — tranche D

Date: 2026-08-06
Status: executable candidate, not deployed or authorized for production.
Upstream contract: `Pantheon-Next@97719b4e1adc1b6177ca469b6252ad8660ccaac1`.

## Objective

Project one governed `WorkIssue` identity into every context it explicitly
concerns, including an agency context without a Project, without creating a
second Task model or widening the Information relation vocabulary.

```text
WorkIssue identity and lifecycle
→ aggregate-owned scope links
→ Project / Information / agency / contact / future Decision or APU views
```

## Reused owners

```text
WorkIssue lifecycle       mvp_vertical.work_issues
Work Card metadata        work_card_metadata
Project                    agency_projects
Information                agency_information_cards
Person / Organization      Agency Data directory owners
Cockpit activity           existing Work activity projection
```

`decision` and `apu_object` are present in the closed contract but fail closed
until their reviewed owner tables exist in tranches E and H.

## Persistence

```text
work_issue_scope_links
work_issue_scope_events
```

An active scope is unique by `WorkIssue + EntityRef`. One active primary scope
is allowed per WorkIssue. Scope meaning is immutable; links are retired instead
of deleted. Scope events are append-only and every material scope effect moves
the WorkIssue optimistic version exactly once.

A primary scope is presentation and retrieval posture only. It does not own the
WorkIssue and does not grant a different authorization ceiling.

## API

```text
POST /work/issues
GET  /work/issues/{issue_id}/scopes
GET  /work/scopes/{entity_type}/{entity_id}/issues
POST /work/issues/{issue_id}/scopes
POST /work/issues/{issue_id}/scopes/{scope_link_id}/retire
POST /work/issues/{issue_id}/scopes/{scope_link_id}/replace-primary
```

Canonical writes require the editor key and `X-Pantheon-Human-Actor`. The Hermes
key cannot use these endpoints. Runtime scope remains owned by Task Contract,
Context Pack and Execution Admission.

## Legacy case_ref posture

The existing exact read remains available:

```text
GET /work/issues?case_ref=...
```

No silent migration infers `Project scope` from `case_ref`. Existing records must
receive an explicit reviewed scope before entering the multi-context projection.
This avoids turning an old lookup field into project authority and avoids a
permanent dual-ownership rule.

The active Cockpit Project loader now reads the exact Project EntityRef scope:

```text
GET /work/scopes/project/{project_id}/issues
```

## Boundaries

```text
scope link != semantic Entity Relation
case_ref equality != Project ownership inferred
scope visible != Context Pack widened
scope linked != task authorized
same WorkIssue in two views != duplicate WorkIssue
agency task != Project invented
runtime success != Evidence
```

No queue, scheduler, dispatcher, retry engine, provider router, runtime,
automatic approval, Evidence admission, memory promotion or Project mutation is
introduced.
