# Rite Modes

Status: active doctrine - rite intensity support.

This document defines intensity modes for rites.

It helps avoid applying a full governance method when a lighter review is enough.

It does not implement execution.

It does not create a runtime.

It does not create automatic classification, scheduling, queueing, approval or memory promotion.

```text
Optional runtime clients may expose interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed rite, review and decision state.
Pantheon Next governs.
The human decides consequential effects.
```

## Purpose

A correct rite can still be too heavy.

Rite intensity must remain proportional to risk, scope, evidence need, approval impact, memory impact and external effect.

The mode does not authorize a rite.

ZEUS still authorizes the rite under `RITE_INVOCATION_POLICY.md`.

## Core rule

```text
Choose the smallest rite mode that can safely expose the useful tension.
```

## Modes

Pantheon recognizes three non-executable rite intensity modes:

```text
mode_light
mode_standard
mode_full
```

These are review intensity labels.

They are not runtime modes, task runners or client pipeline states.

## Mode light

Use `mode_light` when:

- the task is low to medium risk;
- only one tension needs quick exposure;
- no external delivery is immediately authorized;
- no memory promotion is proposed;
- no complex source contradiction exists;
- the goal is to avoid over-review.

Expected output:

```text
one trigger reason
one or two findings
ZEUS status
next allowed action
```

For `AUTOCRITIQUE_CONTRADICTOIRE`, light mode normally means:

- separate fact, interpretation and recommendation;
- identify obvious unsupported or overconfident wording;
- perform no independent runtime reproduction unless a cheap decisive check is already authorized.

Forbidden drift:

- turning a light check into a full review;
- producing unnecessary matrices;
- opening additional rites without ZEUS status.

## Mode standard

Use `mode_standard` when:

- the task has meaningful risk;
- output may affect delivery, evidence, approval or memory posture;
- several role viewpoints matter;
- one rite is enough to expose the main tension.

Expected output:

```text
Rite Review Card
relevant retained output
preserved tensions
ZEUS status
Evidence Pack impact
User Decision Gate impact when relevant
next allowed action
```

For `AUTOCRITIQUE_CONTRADICTOIRE`, standard mode normally adds:

- explicit claim reconciliation;
- inspection of admitted sources and produced artifacts;
- fresh observation of accessible decisive checks when proportionate;
- visible `not_observed` or `not_verifiable` status where checks cannot be performed.

Forbidden drift:

- hiding unresolved tensions behind a clean synthesis;
- treating standard review as approval;
- triggering a second rite automatically.

## Mode full

Use `mode_full` only when:

- the task is high risk;
- professional, legal, contractual, external delivery or memory consequences exist;
- evidence quality materially affects the result;
- role tensions are expected;
- User Decision Gate may be required;
- failure would create durable confusion.

Expected output:

```text
complete Rite Review Card
claim or assumption statuses when relevant
source or contradiction ledger when relevant
explicit unresolved tensions
ZEUS closure status
approval impact
memory impact
User Decision Gate recommendation when relevant
next allowed action
```

For `AUTOCRITIQUE_CONTRADICTOIRE`, full mode normally adds:

- `independent_review` posture where feasible;
- fresh reproduction of material completion claims within the authorized boundary;
- diff or artifact reconciliation rather than reliance on the executor report;
- `analogous_occurrence_check` when a structural defect may recur;
- explicit unsearched areas and environmental limits;
- separation between verdict and any later repair task.

Full mode does not require every possible check. It requires every omitted material check to remain visible.

Forbidden drift:

- using full mode by default;
- creating ritualized bureaucracy;
- mistaking detailed review for proof;
- mistaking detailed review for approval;
- treating independent review as higher authority;
- repairing defects inside an independent verdict.

## Default mode by rite

| Rite | Default mode | Escalate to full when | Prefer light when |
|---|---|---|---|
| `RITE_DIVERGENCE_CONTROLEE.md` | `mode_standard` | options imply strategic, professional or memory consequences | only checking whether another option exists |
| `AUTOCRITIQUE_CONTRADICTOIRE.md` | `mode_light` | output affects delivery, doctrine, memory, approval, professional responsibility or material completion claims | internal draft or phrasing check |
| `CONCORDANCE_DES_SOURCES.md` | `mode_standard` | source conflict affects delivery, approval or memory | one claim needs quick source status |
| `PREMISSES_CACHEES.md` | `mode_light` | assumptions may change scope, evidence, approval or memory | only one minor assumption needs marking |
| `REFONDATION_DE_SESSION.md` | `mode_full` | almost always, because reset can erase tensions | rarely; only for a preliminary refoundation warning |

## Mode examples

### Autocritique Contradictoire light

Use when a draft may contain overclaiming but no major external consequence exists.

Output:

```text
risk_found:
correction_needed:
ZEUS_status:
next_allowed_action:
```

### Autocritique Contradictoire standard

Use when a candidate result matters but a separate independent execution is not proportionate.

Output:

```text
claim_reconciliation:
observations_performed:
unobserved_or_unverifiable:
unsupported_claims:
contradictions:
ZEUS_status:
next_allowed_action:
```

### Autocritique Contradictoire full

Use when a result may be sent externally, committed, canonized or used for professional action.

Output:

```text
review_posture: independent_review
claim_reconciliation:
observations_reproduced:
analogous_occurrence_check:
unsearched_areas:
unsupported_claims:
contradictions:
risk_notes:
approval_impact:
memory_impact:
ZEUS_status:
next_allowed_action:
```

### Concordance des Sources light

Use when one claim needs fast classification.

Output:

```text
claim:
source_status:
claim_status:
next_allowed_action:
```

### Concordance des Sources full

Use when several sources support or contradict a deliverable-critical claim.

Output:

```text
claim_to_source_map:
contradiction_ledger:
freshness_note:
claim_statuses:
ZEUS_status:
next_allowed_action:
```

### Refondation de Session full

Use when the old context may pollute the next Task Contract.

Output:

```text
reason_for_refoundation:
preserved_invariants:
discarded_noise:
unresolved_tensions:
preserved_sources:
preserved_user_decisions:
new_Task_Contract_draft:
ZEUS_status:
next_allowed_action:
```

## Mode escalation

A rite may escalate from light to standard or full only when ZEUS records why.

Valid reasons:

- evidence impact is higher than expected;
- approval impact appears;
- memory impact appears;
- external delivery risk appears;
- material completion claims require independent observation;
- a structural defect may have analogous occurrences;
- role tension becomes unresolved;
- User Decision Gate may be required.

Mode escalation must not happen automatically.

## Mode de-escalation

A rite should de-escalate when:

- the trigger was weaker than expected;
- the issue is style-only;
- the claim is low risk;
- direct correction is enough;
- a User Decision Gate or task split is more appropriate than further review.

De-escalation is a valid ZEUS procedural decision.

## Relationship to selection matrix

Use `RITE_SELECTION_MATRIX.md` first to identify a candidate rite.

Use this file second to choose the smallest safe mode.

```text
selection answers: which rite?
mode answers: how much rite?
```

## Final rule

The safest rite is the smallest rite that still exposes the tension that matters.
