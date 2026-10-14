# Task Contract Revisions

Status: reference — independently maintained in Pantheon Next.
Boundary profile: active_support_doctrine.

Historical provenance is preserved in git history; this file has no external source dependency.

This document is an addendum to `TASK_CONTRACTS.md`.

It defines how a Task Contract may be paused, revised, superseded, resumed, reset or closed when the original frame no longer fits the work.

It is governance doctrine.

It is not a workflow engine.

It is not a scheduler.

It is not a retry mechanism.

It does not let Hermes or any runtime mutate its own authority silently.

## Principle

A Task Contract is the visible frame for consequential work.

If the task changes, the frame must change visibly.

If approval level changes, the approval path must change visibly.

If execution is paused, any continuation must have a resume policy.

Canonical rule:

```text
No scope change without a visible Task Contract revision.
No resumed execution without a resume policy.
No approval downgrade without THEMIS review.
No finalization weakening without APOLLO review.
No external effect without explicit approval.
```

A Task Contract revision is not a new runtime event.

It is a governed record of why the work frame changed and what may safely happen next.

## When revision is required

A revision is required when any of the following changes:

- task objective;
- scope;
- allowed inputs;
- forbidden inputs;
- allowed outputs;
- forbidden outputs;
- approval level;
- allowed tools;
- forbidden tools;
- evidence requirement;
- memory impact;
- external visibility;
- file mutation possibility;
- source requirements;
- role viewpoints required;
- Hermes profile or external executor expected;
- resume point;
- fallback or stop condition.

A revision is also required when the current task moves from:

```text
internal → external
suggestion → action
read-only → write
non-persistent → persistent
no memory impact → Register Candidate possible
single-source → multi-source reconciliation
low-risk → professional, contractual, financial or regulatory risk
```

## When revision is not required

A revision is not required for:

- wording improvements inside the same scope;
- formatting changes that do not affect meaning;
- adding a limitation already required by the current contract;
- preserving an output as candidate without changing status;
- asking the user a simple clarification before work starts;
- stopping and reporting without continuation.

Even when no revision is required, the reason may still be recorded in the Evidence Pack.

## Single-role contract

Not every request requires a workflow.

A single-role Task Contract is allowed when one Pantheon Role can safely operate within a bounded frame.

Use it when the task is:

- simple;
- low-risk;
- non-persistent;
- not externally sent;
- not memory-promoting;
- not file-mutating;
- not dependent on source reconciliation;
- not dependent on multiple branches or role tensions.

Examples:

- IRIS rewrites a short message without sending it;
- ARGOS extracts one fact from a provided source;
- ATHENA structures a simple plan;
- THEMIS classifies an approval level;
- APOLLO checks a short output for unsupported claims.

Rules:

```text
Single-role does not mean ungoverned.
Single-role may still need an Evidence Pack if the output is consequential.
Single-role must escalate when complexity, risk, external effect or persistence appears.
```

## Escalation from single-role to workflow

A single-role contract must escalate when:

- more than one Pantheon Role becomes necessary;
- multiple sources must be reconciled;
- external communication is requested;
- approval level rises;
- memory could be affected;
- file mutation is requested;
- technical, contractual, financial or regulatory exposure appears;
- source conflict appears;
- the user asks for action rather than draft or suggestion.

Escalation result:

```text
current frame pauses
revision reason is recorded
new required frame is proposed
approval impact is exposed
Evidence Pack fragment is created
human validation is requested when required
```

Hermes or any external runtime must pause if the approved frame no longer covers the task.

## Revision signal

A revision signal is a structured warning that the current Task Contract no longer fits.

It may come from:

- Hermes Agent;
- a Pantheon Role viewpoint;
- THEMIS risk review;
- APOLLO quality gate;
- ARGOS source review;
- a user clarification;
- an external tool policy check;
- an Evidence Pack gap.

A revision signal may recommend:

```text
continue_unchanged
pause_for_arbitration
escalate_to_workflow
add_review_step
remove_step
change_dependencies
reset_to_baseline
stop_and_report
```

Forbidden behavior:

```text
signals must not mutate Task Contracts
signals must not change approval levels
signals must not resume execution
signals must not canonize memory, skills or workflows
signals must not override THEMis/APOLLO/user gates
```

## Role signal triggers

Some Role Signals may require a contract revision.

| Signal | Typical trigger | Effect |
|---|---|---|
| THEMIS veto | unsafe action, missing approval, contractual exposure | pause; revision required if approval level or scope changes. |
| APOLLO stop gate | unresolved contradiction, unsupported claim, missing limitation | pause; revision or reset if finalization is blocked. |
| THEMIS risk warning | risk rises during work | visible warning or revision if approval level changes. |
| ARGOS source gap | required source missing or conflicting | pause; revision to add source step or stop. |
| HEPHAISTOS capability gap | method or skill robustness at risk | revision to add review, test or Hermes-side candidate; never auto-activate a skill. |
| clarification request | ambiguity materially changes route | revise if structure, scope or approval changes. |
| handoff signal | active role viewpoint changes | revise only if inputs, outputs, approvals or evidence change. |
| IRIS format issue | output structure needs correction | no revision unless substantive judgment changes. |

Rules:

```text
A Role Signal does not modify the Task Contract by itself.
ZEUS arbitrates procedure after a signal requiring revision.
THEMIS retains veto power over revisions that would reduce safety.
APOLLO retains the stop gate over revisions that would weaken finalization quality.
IRIS may format and transmit signals but does not decide revision.
Hermes pauses on any signal marked pause-required.
```

## ZEUS arbitration

ZEUS arbitrates the procedure, not the truth.

After a revision signal, ZEUS may recommend:

- continue unchanged;
- pause for user validation;
- add a review step;
- remove an unnecessary step;
- change dependencies;
- escalate from single-role to workflow;
- reset to baseline;
- request more sources;
- request THEMIS review;
- request APOLLO review;
- reject the requested trajectory;
- trigger a User Decision Gate.

ZEUS must not:

- lower approval without THEMIS clearance;
- bypass THEMIS veto;
- bypass APOLLO gate;
- activate skills;
- canonize workflows;
- promote memory;
- decide the substantive truth when evidence remains contested.

If the disagreement exceeds procedural arbitration, the correct output is a User Decision Gate.

## Revision record

A Task Contract revision is the visible revised frame.

Minimum fields:

```text
parent_task_contract
revision_id
status
reason
source_signal
arbitration_summary
changes_requested
approval_impact
evidence_impact
memory_impact
outputs_preserved
outputs_discarded
resume_policy
limitations
next_safe_action
```

Allowed revision statuses:

```text
pending_approval
approved
rejected
superseded
reset_to_baseline
closed_without_resume
```

A revision may preserve previous outputs as candidate material.

It must not silently treat previous candidate outputs as approved deliverables.

## Resume policy

A resume policy defines whether and how work may continue after a pause or revision.

Minimum fields:

```text
mode
resume_from
preserve_outputs
discard_outputs
replay_required
evidence_fragment_required
stop_conditions
approval_required_before_resume
```

Allowed modes:

| Mode | Use |
|---|---|
| `continue_current_step` | No material change; continue under the same frame. |
| `resume_from_step` | Restart from a named step after revision. |
| `after_human_validation` | Wait for explicit approval before resuming. |
| `replay_from_checkpoint` | Rerun from a prior known-safe point. |
| `reset_to_baseline` | Discard session override and return to known baseline. |
| `stop_and_report` | Stop and return diagnostic only. |

Rules:

```text
No resume without explicit resume point.
No resume after C4/C5 escalation without required approval.
No resume if required source conflict remains unresolved.
No resume that silently discards evidence.
No resume that converts candidate output into approved output.
```

## Reset to baseline

Reset to baseline discards a session-specific deviation and returns to a known frame.

It is allowed when:

- generated task path became too broad;
- complexity exceeds the need;
- risk increases without value;
- the user asks to return to standard behavior;
- ZEUS rejects the generated option;
- THEMIS blocks the adapted path;
- APOLLO rejects evidence feasibility;
- source gaps make the current trajectory unreliable.

Rules:

```text
Reset does not erase evidence.
Reset does not canonize the discarded path.
Reset does not delete user-provided sources.
Reset may still require a new Task Contract if work continues.
```

## Evidence requirements

Every material revision must add an Evidence Pack fragment.

Minimum fields:

```text
previous_task_contract
source_signal
arbitration_result
changes_requested
approval_impact
steps_added_or_removed
dependencies_changed
outputs_preserved
outputs_discarded
resume_policy
limitations
next_safe_action
```

If the revision was triggered by Role Signals, the Evidence Pack must identify the relevant signals and how they were addressed.

If the task returns to single-role or baseline, the Evidence Pack must state why.

If the work stops, the Evidence Pack must state what remains unresolved.

## Hermes boundary

Hermes may:

- emit revision signals;
- pause when a contract no longer fits;
- execute a revised Task Contract after required approval;
- return partial outputs and evidence fragments;
- report that a required capability is missing.

Hermes must not:

- revise its own Task Contract silently;
- resume after approval escalation without approval;
- promote a session workflow to canonical workflow;
- promote memory;
- activate skills as canonical;
- send external communications without approval;
- treat a revision signal as authorization.

## OpenWebUI boundary

OpenWebUI may expose:

- the current Task Contract;
- revision reason;
- role signals;
- approval impact;
- resume options;
- User Decision Gate when required.

OpenWebUI must not become the approval authority by itself.

OpenWebUI must not canonize memory or silently resume work.

## Final rule

```text
The Task Contract is the frame.
A revision changes the frame.
A resume policy controls continuation.
Hermes executes only within the approved current frame.
OpenWebUI exposes the decision.
Pantheon governs the status and procedure.
The human decides when governance reaches a decision gate.
```
