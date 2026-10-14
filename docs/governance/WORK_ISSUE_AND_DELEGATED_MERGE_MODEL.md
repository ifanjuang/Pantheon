# Work Issue and Delegated Merge Model

Status: candidate support doctrine — documented non-implemented / to verify.
Boundary profile: candidate_support_note.

Date: 2026-07-18

This document defines the missing work-object boundary between cards, Hermes execution and governed change. It reuses Task Contracts, Context Packs, User Decision Gates and the existing card revision lifecycle.

It does not implement a schema, API, issue tracker, queue, scheduler, Hermes Skill, OpenWebUI Function, worker, merge adapter, test or external action.

```text
The human defines consequential authority.
```

## Minimal vocabulary

```text
Case / Affaire = professional scope
card = projection of governed knowledge
note = information without expected treatment
Work Issue = bounded work to treat
issue comment = discussion about that work
Hermes run = external execution record
Change Proposal = proposed versioned change
merge = application of an authorized proposal
```

Cards remain optional. Work Issues must work when no card is displayed.

## Notes, comments and issues

A note implies no assignment, execution, completion or approval. A comment clarifies an issue and does not change its status by itself.

Create a Work Issue only for work needing durable follow-up, assignment, separate discussion, later resumption, independent review or a visible blocker. An explicitly chosen note or comment may become an Issue Candidate.

Do not create an issue for each reasoning step, file read, source lookup, tool call or retry.

```text
note != Work Issue
comment != status change
request != authorization
Hermes returned != issue resolved
```

Hermes applies these creation rules:

| Origin | Default |
|---|---|
| explicit user request | create or continue one issue |
| necessary child work inside authorized scope | may create a linked child issue |
| new discovered topic | attach a suggestion; do not open automatically |
| contradiction or blocker | mark the current issue waiting and preserve the reason |

A discovered topic becomes an issue only after user confirmation or a previously admitted rule covering that exact follow-up class.

## Minimal Work Issue

```yaml
work_issue:
  issue_id:
  case_ref:
  title:
  description:
  origin: human | hermes_child | promoted_suggestion
  parent_issue_ref:
  primary_card_ref:
  issue_type: research | verification | correction | drafting | decision | action
  priority:
  assigned_to:
  requested_effect: read_only | draft | internal_write | external_effect | canonical_effect
  status: open | in_progress | waiting | review | done | cancelled
  close_reason: answered | merged | duplicate | obsolete | rejected | impossible | cancelled
  task_contract_ref:
  context_pack_ref:
  created_by:
  created_at:
  updated_at:
```

Use one business status on the issue.

Technical execution state belongs to the Hermes run:

```text
not_started | running | returned | partial | failed | cancelled | unknown
```

Review state belongs to the Change Proposal:

```text
draft | pending_review | changes_requested | accepted | rejected | stale
```

The user surface may project only:

```text
À traiter | En cours | Besoin de vous | À relire | Bloqué | Terminé
```

`Bloqué` may be derived from `waiting` plus a blocking reason; it need not be another stored status.

## Hermes writes

Hermes writes through a controlled Pantheon adapter, never by direct PostgreSQL access.

Within an admitted Task Contract, Hermes may:

- create necessary child issues and discovered-work suggestions;
- move an assigned issue to `in_progress`, `waiting` or `review`;
- create and update its Hermes run record;
- attach results, sources, Evidence Pack Candidates and trace references;
- create a card as `candidate` or `pending_review`;
- prepare a Change Proposal against an exact base version;
- mark a resolution candidate;
- execute an exact or conditional merge after authority is recorded.

Pantheon validates actor, transition, scope, effect, base version and idempotency before persistence.

Hermes must not:

- self-authorize a consequential merge;
- broaden the mandate silently;
- treat runtime success as evidence or approval;
- close a sensitive issue merely because a run returned;
- overwrite a newer card version;
- bypass external protections;
- use PostgreSQL as its queue.

## Cards and changes

Hermes may create a durable card record without making it canonical:

| Result | Initial posture |
|---|---|
| uncertain or weakly sourced knowledge | `candidate` |
| consequential fact or decision | `pending_review` |
| transient answer | remain on the issue |

Automatic activation is deferred until real low-risk, reversible cases justify an admitted policy. Every card records its originating issue, run, sources, Case scope and validation state.

```text
card_created != card_confirmed
runtime_return != governed_truth
```

A correction creates a Change Proposal:

```yaml
change_proposal:
  proposal_id:
  issue_ref:
  target_object_ref:
  base_version:
  proposed_patch:
  change_summary:
  evidence_candidate_refs: []
  requested_effect:
  review_status:
  created_by:
  created_at:
```

If the target changed after `base_version`, the proposal becomes `stale`; Hermes cannot overwrite the newer version.

Detailed diff, archive and revision rules remain in `docs/assets/pantheon-control/card_revision_proposal_lifecycle.md`.

## Delegated merge

Merge is an execution effect, not judgment authority.

| Mode | Meaning |
|---|---|
| manual | Hermes prepares; the human applies |
| exact | one identified proposal or pull request is authorized |
| conditional | merge is authorized only if named checks pass |

Do not introduce a merge-authority service or table in the first slice. Record delegation in the existing Task Contract or User Decision Gate and append `merge_authorized` with:

```text
author; target; allowed head/base; required checks;
conflict policy; stale policy; expiry if relevant; single-use posture
```

If a condition fails, Hermes returns `waiting` or `changes_requested`. Authorization is scoped and non-transitive; repository protections and external permissions still apply.

```text
merge executed != merge self-authorized
authorization recorded != conditions satisfied
```

## Minimal PostgreSQL target

Only five missing work tables are proposed:

```text
work_issues
issue_comments
hermes_runs
change_proposals
issue_events
```

Cards, versions and notes connect to their existing or separately reviewed model. Begin with `case_ref`, optional `primary_card_ref` and optional `parent_issue_ref`; add many-to-many relations only after a real need.

Current state stays directly queryable. Record only material events:

```text
issue_created | status_changed | hermes_started | hermes_returned
review_requested | merge_authorized | merge_applied | issue_closed
```

Tool calls, reasoning steps, retries and reads remain in Hermes logs. PostgreSQL is the governed record, not the execution engine.

## Context and Card Stack

The targeted Context Pack contains only the resolved Case when required, current issue and useful comments, pertinent cards with exact versions, decisions, contradictions, required sources, requested effect, approval ceiling, output and stop conditions.

Do not send a whole Case database or document corpus by default.

The Card Stack exposes work without owning it. A card face may show compact indicators:

```text
3 issues open
1 Hermes run in progress
1 proposal to review
```

Discussion, evidence and history belong in detail. Card navigation must not trigger hidden execution.

## Anti-overengineering rules

1. Create an object only for a distinct identity and lifecycle.
2. Prefer a field over a new object.
3. Prefer a derived display state over duplicated stored state.
4. Require real professional cases before generic relations.
5. Keep issue creation explicit except for necessary in-scope child work.
6. Create cards only for durable structured knowledge.
7. Reuse Task Contracts, Context Packs, gates and revision doctrine.
8. Store material history, not every runtime operation.
9. Block stale writes instead of building automatic conflict resolution.
10. Keep queues, workers, retries and scheduling in Hermes.

Before adding a feature, ask:

```text
Does it solve at least three real professional situations?
Can it be a field or be derived?
Can it be added later without difficult migration?
```

If it lacks real cases and can be derived or deferred, do not add it.

## First implementation slice

1. Work Issue, comment and material event storage;
2. controlled transitions and optimistic version checks;
3. targeted Context Pack and Hermes run record;
4. normalized Hermes return;
5. card candidate and Change Proposal;
6. exact and conditional delegated merge;
7. compact Card Stack indicators.

Any schema, API, test, runtime, protected-path or external integration change requires a separate review.

## Final rule

```text
The card exposes current knowledge.
The Work Issue organizes treatment.
Hermes executes within scope.
Pantheon validates writes and authority.
Merge applies only an authorized, current and checked proposal.
```
