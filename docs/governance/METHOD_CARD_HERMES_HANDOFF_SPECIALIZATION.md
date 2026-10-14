# Method Card Hermes Handoff Specialization

Status: candidate support doctrine — documented non-implemented / to verify.
Boundary profile: candidate_support_note.

Date: 2026-06-30

This document specializes the governed execution handoff for Method Cards.

It does not replace `CAPABILITY_PLACEMENT.md`, `TASK_CONTRACTS.md`, `EVIDENCE_PACK.md`, `APPROVALS.md`, `USER_DECISION_GATE.md` or any canonical governed execution handoff doctrine.

It does not implement a runtime, Hermes skill, OpenWebUI Function, bridge, connector, scheduler, queue, provider router, approval engine, memory engine, schema, test or external action.

## Purpose

A Method Card can help select a professional method before an execution runtime is asked to produce a Result Candidate.

The Method Card does not authorize execution by itself.

It adds method discipline to an already valid governed execution handoff.

Canonical handoff doctrine remains in:

```text
docs/governance/CAPABILITY_PLACEMENT.md
```

This document answers only one question:

```text
What extra information does a Method Card contribute when the target runtime is Hermes?
```

## Placement

A Method Card belongs to governance and method selection.

Hermes belongs to execution.

The handoff boundary stays:

```text
Task Contract
+ Context Pack if required
+ selected Method Card
+ requested effect classification
+ expected Result Candidate
+ expected Evidence Pack Candidate
+ decision gate
→ Hermes execution request candidate
```

Pantheon does not execute this package.

An exposure surface or adapter may display, assemble or transmit the package only when the governing Task Contract and approval path allow it.

## What the Method Card adds

A Method Card may add:

```text
method_id
method_name
professional_intent
situation_fit
expected_reasoning_pattern
primary_checks
minimum_sources
known_failure_modes
stop_conditions
output_shape_constraints
review_angle
escalation_trigger
```

It must not add:

```text
new approval authority
new source of truth
automatic memory promotion
runtime permission beyond the Task Contract
external-action authorization
canonical status
professional validation
```

## Minimal Method Card handoff fields

The Method Card portion of a governed handoff should be small.

```text
method_card_handoff:
  method_ref:
  method_status: candidate | active_support | deprecated | to_verify
  selected_for:
  professional_context:
  expected_output_shape:
  minimum_evidence_expectation:
  specific_stop_conditions:
  specialist_escalation_trigger:
  visible_user_gate:
```

This shape is a documentation template, not a schema.

The full handoff remains the governed execution handoff defined by `CAPABILITY_PLACEMENT.md`.

## Validity conditions

A Method Card may be included in a Hermes handoff only if:

```text
1. the Task Contract exists or the task is explicitly lightweight/read-only;
2. the requested effect class is already known;
3. the Method Card fits the dossier phase, source state and risk level;
4. the output remains a Result Candidate;
5. the expected Evidence Pack Candidate is named;
6. ambiguities are routed to a visible gate;
7. external effects are not allowed without explicit approval;
8. canonical effects are refused as runtime work.
```

## Method-specific stop conditions

A Method Card should stop or downgrade the handoff when:

```text
source basis is insufficient for the method;
professional phase is unclear;
required document type is absent;
method would imply advice outside scope;
method would create validation by phrasing;
method would invite Hermes to guess missing facts;
method would hide uncertainty;
method would produce an external-action-ready output without gate;
method conflicts with another selected method;
```

Safe outcomes:

```text
continue as read-only candidate;
downgrade to question list;
request missing evidence;
route to specialist review;
open User Decision Gate;
block handoff;
```

## Evidence Pack Candidate additions

When a Method Card is used, the Evidence Pack Candidate should record:

```text
method_ref
why_this_method
sources_required_by_method
sources_available
sources_missing
assumptions_allowed
assumptions_blocked
method_limitations
review_angle_used
escalation_not_triggered_or_triggered
```

This does not replace Evidence Pack doctrine.

It only makes method choice reviewable.

## Compact architecture examples

### Example 1 — Devis complémentaire

```text
Situation:
A contractor submits an additional quote during works.

Primary Method Card:
scope_delta_review

Method contribution:
compare contract scope, site instruction, quote line items and visible change of scope.

Hermes may produce:
Result Candidate: structured analysis of quote status.
Evidence Pack Candidate: contract refs, quote refs, missing facts, risk notes.

Stop condition:
if the quote implies approval, payment validation or instruction to contractor without User Decision Gate.
```

### Example 2 — Compte rendu de chantier

```text
Situation:
A site visit note must separate observations, reservations and decisions.

Primary Method Card:
site_observation_to_reserve_filter

Method contribution:
separate observed facts, contractor statements, architect interpretation and decisions requiring client validation.

Hermes may produce:
Result Candidate: draft report sections.
Evidence Pack Candidate: photos, date, attendees, source notes, unresolved points.

Stop condition:
if the draft turns an observation into acceptance, waiver, payment approval or instruction without explicit gate.
```

### Example 3 — CERFA / administrative filing

```text
Situation:
A form field must be filled from project documents.

Primary Method Card:
field_as_claim_resolution

Method contribution:
resolve each field as a claim with source, confidence, missing value and fallback.

Hermes may produce:
Result Candidate: field table and draft values.
Evidence Pack Candidate: per-field source refs and uncertainties.

Stop condition:
if a field value is guessed, outdated, unsupported or submission-ready without review.
```

## Bad handoffs

Bad:

```text
Use the best method and prepare the answer.
```

Reason:

```text
No Task Contract, no method ref, no evidence expectation, no effect class, no gate.
```

Bad:

```text
Use the devis method and validate whether the client must pay.
```

Reason:

```text
Asks the runtime for professional/legal validation. Hermes may produce a candidate analysis, not a final obligation.
```

Bad:

```text
Generate the chantier report and send it.
```

Reason:

```text
Combines drafting and external action. Sending requires explicit approval and a visible User Decision Gate.
```

## Review checklist

Before a Method Card handoff to Hermes is admissible, check:

```text
Task Contract exists or lightweight exception is explicit.
Method Card is named.
Method status is known.
Requested effect is classified.
Output remains candidate.
Evidence Pack Candidate expectation is stated.
Method-specific stop conditions are visible.
External effects are gated.
Canonical effects are refused as runtime work.
User-facing uncertainty is preserved.
```

## Boundary

The Method Card helps select and constrain a method.

Hermes may execute the bounded request externally.

Pantheon governs status, proof, scope, approval, memory and external action.

The human decides.

```text
Method selected != execution authorized.
Hermes success != approval.
Candidate output != professional validation.
Evidence Pack Candidate != final proof.
Draft ready != authorized to send.
```
