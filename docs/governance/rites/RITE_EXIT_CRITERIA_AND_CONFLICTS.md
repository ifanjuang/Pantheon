# Rite Exit Criteria and Conflicts

Status: active doctrine - rite closure and conflict policy.

This document defines how rites must close and how conflicts between rites must be handled.

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

A rite that cannot close becomes a loop.

A set of rites that pull in opposite directions can become hidden orchestration.

This document prevents both failures.

## Core rule

```text
A rite must end with a visible ZEUS status.
A rite must produce a bounded review result.
A rite must not leave procedure open by implication.
```

## Global exit requirement

Every invoked rite must close with:

```text
rite_id
trigger_reason
ZEUS_status
outputs_retained
tensions_exposed
Evidence_Pack_impact
User_Decision_Gate_impact
memory_impact
next_allowed_action
```

A rite is not closed if it only produces prose.

A rite is not closed if it only produces options.

A rite is not closed if it only detects risk.

A rite is closed when ZEUS assigns a status and the next allowed action is explicit.

## ZEUS closure statuses

Valid closure statuses:

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

These are procedure statuses.

They are not truth statuses.

They are not approval statuses.

They are not memory statuses.

## Exit criteria: Rite de Divergence Controlee

This rite may close only when one of the following exists:

- shortlist produced;
- decision blocked;
- User Decision Gate opened;
- task split required;
- divergence judged unnecessary by ZEUS;
- scope narrowed enough to continue without divergence.

Mandatory retained output:

```text
option_clusters
shortlist_or_block_reason
non_obvious_defensible_option when relevant
traps_detected
ZEUS_status
next_allowed_action
```

Failure to close:

- continuing to generate options;
- widening scope without decision value;
- treating shortlist as validation;
- avoiding User Decision Gate when options imply different values or risks.

## Exit criteria: Autocritique Contradictoire

This rite may close only when the candidate receives one of the following outcomes:

- acceptable as draft;
- acceptable with reserve;
- requires correction;
- blocked for delivery;
- requires source support;
- requires User Decision Gate;
- replaced by narrower Task Contract.

Mandatory retained output:

```text
claim_separation
unsupported_claims
contradictions
risk_notes
correction_actions
ZEUS_status
next_allowed_action
```

Failure to close:

- critique becomes general caution;
- every issue is framed as blocker;
- clear prose hides unresolved contradiction;
- critique is mistaken for proof.

## Exit criteria: Concordance des Sources

This rite may close only when each decision-critical claim has a status.

Recommended claim statuses:

```text
unsupported
source_needed
sourced_coherent
sourced_but_contradicted
usable_for_draft
blocked_for_delivery
```

Mandatory retained output:

```text
claim_to_source_map
contradiction_ledger
freshness_note
unsupported_claims
claim_statuses
ZEUS_status
next_allowed_action
```

Failure to close:

- source volume is treated as proof;
- contradictory sources are smoothed away;
- freshness is confused with authority;
- a claim is cited beyond what the source supports.

## Exit criteria: Premisses Cachees

This rite may close only when assumptions are classified.

Recommended assumption statuses:

```text
explicit_user_constraint
inferred_but_unconfirmed
confirmed_by_source
requires_user_confirmation
irrelevant_to_next_step
blocks_task_contract
```

Mandatory retained output:

```text
explicit_request
hidden_assumptions
assumption_statuses
scope_impact
Task_Contract_impact
ZEUS_status
next_allowed_action
```

Failure to close:

- inferred assumption becomes fact;
- every missing preference becomes blocker;
- scope expands silently;
- user intent is invented.

## Exit criteria: Refondation de Session

This rite may close only when the old frame and new frame are both explicit.

Mandatory retained output:

```text
reason_for_refoundation
preserved_invariants
discarded_noise
unresolved_tensions
preserved_sources
preserved_user_decisions
new_Task_Contract_draft
ZEUS_status
next_allowed_action
```

Failure to close:

- reset deletes contradictions;
- discarded variants disappear without status;
- a user decision is silently lost;
- context history becomes hidden memory;
- refoundation is used as cosmetic cleanup.

## Rite conflict rule

Different rites may pull in different directions.

Examples:

```text
Divergence Controlee opens the option space.
Autocritique Contradictoire reduces or blocks candidates.
Concordance des Sources slows decisions until source status is clear.
Premisses Cachees narrows the problem before action.
Refondation de Session cuts the frame and restarts.
```

When two rites conflict, ZEUS must not smooth the conflict into a synthetic compromise by default.

ZEUS must choose one of:

```text
prioritize_one_rite
sequence_with_explicit_reason
split_task
open_User_Decision_Gate
block_until_evidence
refound_session
```

A conflict between rites is a governance signal.

It is not an error.

It must remain visible when it affects delivery, approval, evidence, memory or human choice.

## Conflict examples

### Divergence versus Autocritique

Divergence asks for more options.

Autocritique asks whether the candidate is safe.

ZEUS must decide whether the task is still in exploration or has entered review.

### Concordance versus Delivery

Concordance may block delivery because sources are missing or contradictory.

APOLLO may still make the output clear.

Clarity must not override missing evidence.

### Refoundation versus Memory

Refoundation may preserve invariants and discard noise.

MEMORY rules still decide whether anything becomes a Register Candidate.

Reset must not become memory promotion.

### Premises versus User Decision

Premises may reveal that the user must choose between interpretations.

ZEUS must not choose the interpretation when human preference or professional judgment is required.

## User Decision Gate escalation

A User Decision Gate is required when:

- two rites produce incompatible procedural recommendations;
- a rite exposes a conflict of value;
- evidence remains insufficient but the user wants to proceed;
- refoundation would discard a user-valued direction;
- options imply materially different professional risks;
- memory, delivery or external transmission depends on unresolved judgment.

## Relationship to Evidence Packs

An Evidence Pack should record closure criteria when a rite affects output legitimacy.

It should not store hidden reasoning or raw role debate.

It should store:

```text
closure_status
claim_statuses when relevant
assumption_statuses when relevant
preserved_tensions
next_allowed_action
```

## Final rule

A rite is complete only when it has status, retained output, preserved tensions and an explicit next allowed action.
