# Urgent Review Triage

Status: candidate support doctrine — urgency qualification rule for review items.
Boundary profile: candidate_support_note.

This document defines how Pantheon Next qualifies urgent fiches before they enter or move inside a review queue.

It is documentation only.

It does not implement a task manager, scheduler, notification system, queue runtime, assignment system, OpenWebUI action, Hermes skill, database table, priority engine or automatic decision system.

In abstract form:

```text
The exposure surface exposes.
The execution runtime executes.
Pantheon governs.
```

## Purpose

Professional work produces many fiches marked urgent.

The failure mode is predictable: everything becomes P0, so nothing is truly prioritized.

Pantheon must therefore distinguish declared urgency from qualified urgency.

Core rule:

```text
Urgency is not a status by itself.
Urgency must be qualified by consequence, deadline, evidence and required decision.
```

Or, for agency practice:

```text
A fiche is not urgent because it says urgent.
It is urgent when it carries a proven deadline, risk, responsibility or blocker.
```

## Triage chain

Every urgent fiche should pass through a short qualification chain:

```text
Fiche received
-> urgency claim
-> consequence check
-> deadline check
-> evidence check
-> decision-needed check
-> next action
-> governed status
```

The goal is not to solve the fiche during triage.

The goal is to decide what kind of attention it deserves.

## Minimum fiche shape

A fiche should expose the following fields before being treated as urgent:

```text
title
matter_or_project
origin
why_urgent
risk_if_not_handled
deadline_or_trigger
evidence_or_source
decision_needed
next_action
owner_or_responsible_role
status
```

If these fields are missing, the fiche starts as:

```text
urgent_claim_unqualified
```

## Urgency classes

Recommended classes:

```text
immediate_blocker
decision_needed_today
evidence_needed
production_needed
awaiting_external_response
unclear_or_duplicate
not_urgent
```

### immediate_blocker

Use when an item blocks work, safety, legal/procedural deadline, contractual progress or a critical client response.

Examples:

```text
site stop or safety issue
administrative deadline today or tomorrow
contractor waiting before continuing work
client decision blocking execution
missing document before formal submission
```

### decision_needed_today

Use when a human decision is required today, but the item does not itself block the whole operation.

Examples:

```text
arbitration needed before meeting
choice between two contractor responses
client position to confirm before email
approval of a draft before transmission
```

### evidence_needed

Use when the item cannot be decided because proof is missing.

Examples:

```text
missing quote version
missing insurance certificate
missing photograph
unclear site report reference
source document not found
```

### production_needed

Use when the decision is known but the output must be produced.

Examples:

```text
email draft
meeting note
site report section
comparison table
client summary
contractor question list
```

### awaiting_external_response

Use when no internal action can resolve the item until someone else answers.

Examples:

```text
contractor confirmation pending
client arbitration pending
engineer response pending
administration response pending
```

### unclear_or_duplicate

Use when the fiche does not yet justify urgent treatment.

Examples:

```text
unclear title
no deadline
no source
duplicate of another fiche
risk not stated
project unknown
```

### not_urgent

Use when the item is useful but does not carry near-term consequence.

## Consequence levels

Urgency depends on consequence.

Recommended consequence levels:

```text
C0 administrative / convenience
C1 internal organization
C2 project progress
C3 client commitment
C4 contractual or financial consequence
C5 liability, safety, regulatory or external filing consequence
```

High consequence does not mean automatic action.

High consequence means stricter review.

## Deadlines

Deadline vocabulary:

```text
today
tomorrow
this_week
before_meeting
before_site_visit
before_submission
before_signature
before_payment
before_work_continues
no_deadline_found
```

A fiche without a deadline may still be important. It is not automatically urgent.

## Evidence threshold

A fiche marked urgent should carry at least one evidence reference:

```text
source document
email
site report
photo
contractor message
client instruction
calendar event
administrative deadline
contractual clause
manual professional note
```

If no evidence is present, the item should be triaged as:

```text
evidence_needed
```

or:

```text
urgent_claim_unqualified
```

## Status vocabulary

Recommended statuses:

```text
urgent_claim_unqualified
urgent_blocker
urgent_today
urgent_this_week
evidence_needed
decision_needed
production_needed
awaiting_external_response
deferred
resolved
obsolete
duplicate
not_urgent
```

These statuses qualify attention. They do not approve action.

## Relationship to Review Queue

`REVIEW_QUEUE.md` defines the governed decision queue.

This document defines how urgent fiches should be sorted before or inside that queue.

A triage result may enqueue a review item, change its priority, request evidence or escalate to a User Decision Gate.

It must not apply the decision itself.

## Priority rule

A practical priority formula may be:

```text
priority = consequence x deadline_pressure x evidence_quality x blocker_status
```

But the formula is only a sorting aid.

```text
A priority score orders work.
It does not validate a claim.
It does not approve action.
It does not promote memory.
```

## Daily agency use

A practical morning triage may use this sequence:

```text
1. qualify unqualified urgent claims
2. identify immediate blockers
3. identify decisions needed today
4. request missing evidence
5. batch production work
6. defer or downgrade unclear items
```

The review should separate triage from execution.

```text
Triage decides what deserves attention.
Execution still requires the proper task, evidence and approval boundary.
```

## Professional boundaries

For architecture practice, urgent triage must not silently authorize:

```text
sending an email
issuing a service order
approving a quote
selecting a contractor
lifting a reservation
validating a payment
filing an administrative document
promoting agency memory
```

Any such action requires its own governed approval path.

## Non-goals

This document does not authorize:

```text
Pantheon as task manager
Pantheon as scheduler
Pantheon as notification engine
Pantheon as assignment system
automatic escalation to P0
automatic external action
automatic approval
automatic memory promotion
hard delete of fiches
```

## Boundary phrase

```text
Urgent is a claim.
Pantheon qualifies the claim.
The human decides the response.
```
