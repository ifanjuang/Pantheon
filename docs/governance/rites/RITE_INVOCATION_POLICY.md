# Rite Invocation Policy

Status: active doctrine - rite invocation, budget and closure policy.

This document defines how rites may be proposed, authorized, bounded, recorded and closed.

It does not implement rite execution.

It does not create a runtime, scheduler, queue, hidden role debate, automatic trigger engine, approval callback or memory promotion pipeline.

```text
Optional runtime clients may expose interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed rite, review and decision state.
Pantheon Next governs.
The human decides consequential effects.
```

## Purpose

Rites are useful only if their invocation is controlled.

Without an invocation policy, rites can drift into implicit workflows, hidden orchestration or ritualized over-review.

This policy answers four questions:

```text
Why this rite?
Who authorized it?
What did it change?
How does it close?
```

If those four answers are not visible, the rite should not be considered governed.

## Core rule

```text
A rite may be proposed by a role.
ZEUS authorizes or rejects it.
The Task Contract records why.
The Evidence Pack records what changed.
An optional runtime client may expose technical interaction.
Pantheon Cockpit may project governed rite status and linked decisions.
None of these executes the rite for Pantheon.
```

## Invocation authority

A rite may be proposed by:

- a Pantheon Role viewpoint;
- ZEUS during procedural arbitration;
- a Task Contract author;
- a human reviewer;
- a prior Evidence Pack review note.

A rite may not be triggered automatically by:

- another rite;
- runtime-client UI state;
- a runtime trace;
- a Knowledge Base retrieval;
- an Evidence Pack entry;
- a Register Candidate;
- a Hermes profile;
- a tool result;
- a scheduler, queue or workflow step.

## Authorization

ZEUS must decide whether the rite is allowed, rejected, deferred, escalated or replaced by a simpler governance action.

ZEUS does not decide truth.

ZEUS decides status and next procedure.

Valid ZEUS statuses:

```text
rite_not_needed
rite_allowed
rite_completed_as_draft
rite_completed_with_reserve
rite_blocked
rite_escalated_to_user
task_split_required
rite_superseded
```

## Task Contract boundary

When a rite is authorized, the Task Contract should state only the governance boundary needed for the review:

```text
rite_id
trigger_reason
selected_mode
review_posture when relevant
admitted inputs
allowed observations
allowed outputs
forbidden outputs
approval ceiling
stop condition
```

The Task Contract must not prescribe an executable role graph, worker assignment, provider route, retry loop or tool sequence.

For `AUTOCRITIQUE_CONTRADICTOIRE`, `review_posture` may be:

```text
self_review
independent_review
```

The posture is governance context, not a runtime topology.

## Independent review boundary

An independent review may be appropriate when a material completion claim, professional deliverable, doctrine change, code change, schema change, migration or external-effect preparation requires observation separate from the executor's report.

The independent reviewer may be another bounded Hermes execution, another admitted runtime projection or a human reviewer.

Separation does not grant higher authority.

```text
independent reviewer != approval authority
separate execution != automatic truth
fresh observation != validated Evidence
review completed != external action authorized
```

The Task Contract must define which artifacts, sources and checks the reviewer may access.

The reviewer must not silently expand the task, repair defects during an independent verdict, invoke another rite or authorize a consequential next step.

A repair found necessary by independent review requires an allowed next action, Task Contract revision or separate task.

## Rite budget

Rites must remain proportional to risk.

Default budget:

```text
low-risk task       -> no rite by default
medium-risk task    -> one rite maximum unless ZEUS justifies otherwise
high-risk task      -> multiple rites allowed if explicitly recorded
three rites or more -> User Decision Gate or task split required
```

A rite has cost:

```text
time_cost
attention_cost
evidence_cost
decision_cost
```

If the rite does not change decision quality, evidence quality, risk posture, memory posture or delivery safety, it should not be invoked.

An independent review is not justified merely because a second model or runtime is available.

## Anti-chaining rule

A rite may reveal the need for another rite.

It must not trigger another rite.

A second rite requires ZEUS status and an explicit reason.

A third rite requires either:

- User Decision Gate;
- task split;
- scope narrowing;
- explicit high-risk justification.

Forbidden chain:

```text
Premisses Cachees
-> Divergence Controlee
-> Autocritique Contradictoire
-> Concordance des Sources
-> Refondation de Session
-> new Task Contract
-> another rite
```

If this chain appears, the system is rebuilding a workflow through rites.

That is governance drift.

## Trigger thresholds

Each rite must have a threshold.

Recommended thresholds:

```text
RITE_DIVERGENCE_CONTROLEE
-> only when several viable options exist and premature convergence is a material risk.

AUTOCRITIQUE_CONTRADICTOIRE
-> only when output may affect delivery, approval, memory, doctrine, professional responsibility, external transmission or a material completion claim.

CONCORDANCE_DES_SOURCES
-> only when a claim depends on sources or may affect proof, delivery, approval or memory.

PREMISSES_CACHEES
-> only when an implicit assumption can change scope, procedure, evidence, approval or memory.

REFONDATION_DE_SESSION
-> only when continuing the current context creates more confusion than restarting from a clean Task Contract.
```

## No rite for style only

A rite must not be invoked for style-only changes unless style affects:

- legal meaning;
- professional responsibility;
- external transmission;
- contractual interpretation;
- evidence clarity;
- approval status.

## Observation and scope

A rite may request fresh observation only inside the admitted Task Contract boundary.

Examples include opening an artifact, inspecting a diff, re-running a named check or comparing a claim with an admitted source.

Observation does not authorize mutation.

A structural defect may justify an `analogous_occurrence_check`, but the search scope and unsearched areas must remain visible.

Finding another occurrence does not extend the task automatically.

```text
search result != scope authorization
runtime success != Evidence
not observed != passed
```

## Closure requirement

Every invoked rite must close with a ZEUS status.

A rite cannot remain open by implication.

A rite cannot close itself, approve itself, promote memory or authorize external action.

Closure must identify:

```text
rite_id
trigger_reason
authorized_by
selected_mode
review_posture when relevant
observations_performed
material_unobserved_or_unverifiable
ZEUS_status
next_allowed_action
Evidence Pack impact
User Decision Gate impact
memory impact
```

## Rite Review Card

When a rite affects output legitimacy, delivery posture, memory posture or user arbitration, it should produce a Rite Review Card.

A Rite Review Card is not a schema.

It is a documentation format that may be embedded in an Evidence Pack, surfaced by an optional runtime client as interaction context, or projected by Pantheon Cockpit as governed review state.

Recommended format:

```text
rite_id:
trigger_reason:
proposed_by:
authorized_by:
selected_mode:
review_posture:
role_viewpoints_involved:
inputs_considered:
observations_performed:
unobserved_or_unverifiable:
outputs_retained:
tensions_exposed:
blocked_claims:
analogous_occurrence_scope:
ZEUS_status:
User_Decision_Gate:
Evidence_Pack_impact:
memory_impact:
next_allowed_action:
```

Forbidden content:

- hidden chain-of-thought;
- raw role debate;
- private scratchpad;
- autonomous agent transcript;
- runtime worker trace;
- executable workflow state;
- automatic approval event;
- automatic memory promotion event.

## Refoundation safeguard

`REFONDATION_DE_SESSION.md` must be handled with special caution.

Reset is not deletion.

Refoundation must preserve unresolved tensions.

Discarded variants remain historical context, not a Registre Probatoire entry.

No contradiction may disappear without status.

No user decision may be discarded silently.

## Runtime-client and Cockpit display boundary

Optional runtime clients may display technical interaction and rite review context. Hermes WebUI is one optional/proposed client if separately selected and qualified.

Pantheon Cockpit may project governed rite review status, tensions, Evidence gaps and User Decision Gates.

Prefer display labels that do not imply autonomous execution.

Recommended display labels:

```text
rite_proposed
rite_not_needed
rite_review_open
rite_under_governance_review
rite_review_closed
rite_rejected
rite_superseded
rite_escalated_to_user_decision_gate
```

A surface may also display `self_review`, `independent_review`, `not_observed` or `not_verifiable` as review context.

These labels do not confer authority.

```text
Hermes WebUI available != Hermes WebUI selected
client selected != authority transfer
projection != persistence
rite visible != rite authorized
```

## Hermes boundary

Hermes may execute work associated with a rite only when a Task Contract authorizes the external execution.

Hermes execution remains external.

Pantheon does not run the rite.

Pantheon governs the rite boundary, evidence expectation, approval implication and memory implication.

A Hermes skill implementing a rite is a replaceable runtime projection.

```text
skill installed != rite authorized
rite executed != claim validated
binding selected != dependency adopted
```

## Failure modes

- rite over-activation;
- rite chaining;
- rite used for style-only work;
- independent review treated as higher authority;
- executor report trusted without proportionate observation;
- reviewer repairs work while claiming an independent verdict;
- analogous search silently expands scope;
- ZEUS closure omitted;
- client or Cockpit display mistaken for execution or approval;
- Evidence Pack summary mistaken for proof;
- role viewpoints mistaken for runtime agents;
- Refoundation used to erase contradictions;
- rite output treated as memory.

## Forbidden drift

This policy must not become:

- runtime policy engine;
- automatic rite trigger engine;
- UI dependency graph;
- scheduler;
- queue;
- hidden orchestration layer;
- executable DAG;
- automatic test runner;
- approval callback;
- memory promotion pipeline.

## Final rule

A rite is safe only when its reason, authorization, bounded observation, effect and closure are visible.
