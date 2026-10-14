# Repository Review Watcher

Status: candidate governance support doctrine  
Boundary profile: candidate_support_note.
Runtime status: non-executable  
Authority class: candidate / to verify

This document defines a candidate governance manifest for watching repository activity and preparing review notes.

It does not implement a runtime, cron job, webhook endpoint, scheduler, queue, worker, provider router, dashboard integration, database table, Hermes skill, OpenWebUI Action, GitHub App, Notion automation, automatic approval, automatic memory promotion or external action.

## Purpose

Pantheon Next needs a safe way to notice repository movement without turning repository movement into governance truth.

The Repository Review Watcher is a candidate workflow manifest for:

- detecting relevant repository activity;
- comparing it against active governance documents;
- surfacing contradictions, drift and pending decisions;
- preparing a short review note;
- proposing dashboard updates as candidates only.

It is a governance description of the work shape. It is not the work engine.

## Boundary

The watcher may be executed by an external execution runtime under a Task Contract.

Pantheon defines:

- what sources may be read;
- what claims require evidence;
- which statuses may be assigned;
- which outputs are allowed;
- which actions remain forbidden;
- when a User Decision Gate is required.

Pantheon must not define:

- polling cadence;
- webhook implementation;
- worker assignment;
- queue progression;
- runtime retry policy;
- provider routing;
- tool credentials;
- dashboard write mechanics.

Those belong outside Pantheon.

## Relationship to existing doctrine

This candidate follows:

- `STATUS.md` — repository posture and live exceptions;
- `AUTHORITY_INDEX.md` — authority class and repository-state vocabulary;
- `MODULES.md` — workflow and Hermes boundaries;
- `CAPABILITY_PLACEMENT.md` — capability placement by primary effect;
- `MODULAR_DOMAIN_REORIENTATION.md` — Task Contract in -> Result Candidate + Evidence Pack Candidate out;
- `TASK_CONTRACTS.md` — governed execution boundary;
- `HERMES_INTEGRATION.md` — external execution runtime boundary;
- `WORKFLOW_LIFECYCLE.md` — progressive workflow modes.

It also responds to a recurring coordination need: PRs, issues, comments and assistant proposals may move faster than the doctrine indexes.

## Candidate workflow manifest

```text
workflow_id: repository-review-watcher
status: candidate / to verify
initial_mode: shadow
maximum_mode_without_review: assisted
owner_layer: pantheon_governance
execution_surface: external_execution_runtime
exposure_surface: cockpit_or_dashboard
```

### Intent

Detect repository activity that may affect Pantheon governance status, then produce a reviewable classification with evidence.

The watcher answers:

```text
What changed?
Which doctrine does it touch?
Does it create a contradiction, runtime drift, memory drift, approval ambiguity or status confusion?
What decision is expected next?
```

### Triggers

Allowed trigger descriptions:

```text
manual_review_request
time_based_review_signal
event_based_repository_signal
dashboard_followup_signal
```

These are trigger categories only. They are not scheduler, cron, webhook or queue definitions.

The exact trigger mechanism belongs to the external runtime or adapter layer.

### Sources

Allowed source categories:

```text
repository_governance_documents
repository_pull_requests
repository_issues
repository_comments_and_reviews
repository_change_diff
changelog
pilotage_dashboard_cards
```

Source access must remain read-only unless a separate Task Contract explicitly authorizes a candidate write.

### Excluded sources

The watcher must not read or infer from:

```text
client dossiers
private project records
secrets
environment variables
credential stores
unscoped local files
unscoped external dashboards
personal memory outside the task scope
```

If a source is needed but not authorized, the watcher returns a Capability Gap.

## Required Task Contract shape

A Repository Review Watcher run must be framed by a Task Contract when it touches doctrine-sensitive, repository-sensitive or dashboard-sensitive work.

Minimal shape:

```text
identity:
  task_id: repository-review-watcher/<date-or-run-id>
  owner_role: Zeus or delegated governance reviewer
  creation_source: manual | scheduled-signal | event-signal

intent:
  produce review notes for recent repository activity

scope:
  include:
    - selected repository paths
    - selected PRs or issues
    - selected comments or review threads
    - selected dashboard cards if authorized
  exclude:
    - protected paths unless read-only review is explicit
    - external writes
    - client/project data

constraints:
  - read-only by default
  - no merge
  - no automatic issue closure
  - no automatic dashboard status promotion
  - no canonical memory promotion
  - no doctrine mutation without separate reviewed change

approvals:
  dashboard_candidate_update: C1 or higher
  repository_document_change: C2 or higher
  protected_path_change: explicit approval required
  external_action: forbidden by default

expected_evidence:
  - sources read
  - relevant snippets or file references
  - assumptions
  - contradictions
  - affected doctrine
  - proposed status
  - approval gap if any

allowed_outputs:
  - Review Note
  - Result Candidate
  - Evidence Pack Candidate
  - Dashboard Update Candidate
  - Capability Gap
  - Risk Escalation
  - Patch Candidate only if explicitly authorized

forbidden_outputs:
  - final approval
  - canonical status promotion
  - memory canonization
  - runtime implementation
  - scheduler configuration
  - queue or worker definition
  - merge decision
  - external communication
```

## Review note format

Each detected item should be reduced to a small, reviewable unit:

```text
Element detected:
Source:
Affected doctrine:
Evidence:
Risk:
Status proposed: accepted | refused | to verify | to arbitrate | non applicable
Repository state: implemented | documented non-implemented | partial | to verify | obsolete | non applicable
Decision expected:
Next action:
Memory implication:
External-action implication:
```

The note is not a decision. It is a decision support artifact.

## Classification rules

### Accepted

Use only when the proposal is compatible with active doctrine and does not require unresolved arbitration.

Accepted does not mean implemented.

### Rejected / forbidden by doctrine

Use this rejected status when the proposal conflicts with doctrine, especially if it creates:

- hidden runtime behavior;
- scheduler or queue drift;
- automatic approval;
- automatic memory promotion;
- tool authorization by mere availability;
- external action without approval.

### To verify

Use when evidence is incomplete, repository status is unclear, discussions conflict or the proposal depends on unverified tool behavior.

### To arbitrate

Use when a consequential decision exists and the watcher cannot settle it by doctrine alone.

### Non applicable

Use when the item is operational noise or outside the Pantheon governance perimeter.

## Workflow modes

### Shadow

The watcher observes and writes a would-have-done trace.

Allowed:

- detect activity;
- classify risk;
- identify affected doctrine;
- prepare review note;
- prepare dashboard update candidate.

Forbidden:

- write dashboard status;
- modify repository files;
- comment on PRs or issues;
- close or reopen issues;
- promote memory.

### Assisted

The watcher may prepare candidate writes for human review.

Allowed:

- draft a dashboard card update;
- draft a GitHub comment;
- draft a Markdown patch candidate;
- propose an ai_log entry.

Forbidden:

- apply the write without approval;
- claim final doctrine status;
- merge code;
- change protected paths;
- close decisions by silence.

### Active guarded

Not authorized by this document.

A separate review would be required before any low-risk internal write becomes allowed.

### Active durable

Not authorized by this document.

Durable activation would require test cases, shadow traces, failure behavior, disableability, source limits, approval mapping and an external implementation outside Pantheon.

## Dashboard update candidate

When dashboard tracking is used, the watcher may propose this payload:

```text
card_title:
status:
priority:
lot:
authority:
type:
risk:
source:
short_summary:
expected_done:
expected_decision:
next_action:
zeus_decision:
repo_state:
last_review_date:
```

This is a candidate record. It does not replace the repository.

The repository remains the canonical source for doctrine. The dashboard remains a pilotage surface.

## Evidence Pack expectations

A watcher Evidence Pack Candidate should contain:

```text
task_contract_ref:
run_scope:
sources_read:
items_detected:
doctrine_refs:
classification_rationale:
contradictions:
capability_gaps:
risk_escalations:
proposed_outputs:
approval_gap:
memory_candidates:
```

Runtime logs may support the pack, but they are not the Evidence Pack by themselves.

## Decision gate triggers

Open a User Decision Gate when:

- a proposal would promote a candidate document to doctrine;
- an issue or PR comment proposes runtime behavior inside Pantheon;
- a dashboard card would be marked valid / canonical;
- a Register Candidate would be promoted;
- a protected path is implicated;
- comments from assistants disagree on status;
- the same item appears both accepted and refused in different discussions;
- the watcher detects a possible external action.

## Current binding note

Current likely binding, non-normative:

```text
repository host: GitHub
execution runtime: Hermes Agent
pilotage dashboard: Notion
exposure surface: OpenWebUI
```

These product names describe the current environment only. The governance body above should remain valid if the tools change.

## Activation conditions

Before any real run is treated as more than an experiment:

- the Task Contract must be explicit;
- source scope must be explicit;
- protected paths must remain read-only unless approved;
- the output format must be fixed;
- a human reviewer must inspect at least several shadow traces;
- disableability must be clear;
- dashboard updates must remain candidates until approved.

## Rejected collapse

```text
repository activity = governance decision
PR comment = accepted doctrine
assistant proposal = Zeus decision
Hermes done = approved
dashboard status = canonical repository state
runtime trace = Evidence Pack
repeated issue mention = Registre Probatoire entry
cron signal = authorization
webhook payload = approval
```

## Final rule

```text
The watcher notices.
The evidence supports.
Zeus qualifies procedure.
The human decides.
The repository keeps doctrine.
```
