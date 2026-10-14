# User Decision Gate

Status: active doctrine — governed escalation to human decision.

This document defines when Pantheon Next must stop procedural arbitration, expose disagreement and ask the user for an explicit decision.

It extends `GOVERNANCE_COLLEGE.md`.

It does not add a runtime.

It does not add an agent.

It does not add a message bus.

It does not add orchestration.

It does not add a scheduler, queue, LangGraph runtime, hidden workflow runner, automatic approval system, automatic memory system or autonomous decision loop.

```text
Optional runtime clients may expose interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed decision gates, status and Evidence gaps.
Pantheon Next governs.
The human decides consequential effects.
```

## Core rule

When governed tension exceeds procedural arbitration, Pantheon must expose the discord and request a human decision.

```text
The system must not hide serious conflict behind a smooth answer.
```

A conflict is not a failure.

A conflict may be the most important output of the task.

## Purpose

The User Decision Gate prevents Pantheon from becoming an oracle.

It exists to make unresolved disagreement visible, qualified and actionable.

Pantheon should not answer with false certainty when:

- sources disagree;
- scope is unclear;
- risk is material;
- external transmission is requested;
- professional liability may be affected;
- memory promotion is proposed;
- approval level is unclear;
- role viewpoints conflict in a way that changes the decision.

## Relationship to the Governance College

The Governance College separates responsibilities of judgment.

ATHENA may structure.

ARGOS may challenge sources.

THEMIS may block on risk.

APOLLO may challenge clarity and delivery readiness.

HEPHAISTOS may produce an artifact candidate.

IRIS may prepare transmission.

ZEUS may arbitrate status and next procedure.

If ZEUS cannot produce a safe procedural outcome, Pantheon must ask the user.

```text
ZEUS arbitrates procedure.
The human decides when procedure is insufficient.
```

## Trigger conditions

A User Decision Gate should trigger when any of the following is true.

### Source conflict

Sources are missing, stale, contradictory, unverifiable or outside the authorized scope.

### Scope conflict

The user request requires scope expansion, cross-project transfer, unclear project boundary or access to knowledge not authorized by the Task Contract.

### Professional risk

The output may affect legal, financial, contractual, medical, safety, design, project-management, compliance or professional responsibility.

### External effect

The task would send, publish, deploy, file, transmit, notify, write to an external system, modify a repository, create a client-facing artifact or otherwise affect a third party.

### Delivery ambiguity

A draft is possible but delivery-ready status is doubtful.

### Memory risk

A proposed memory item may be too broad, too sensitive, unsupported, obsolete, contradicted or valid only in a narrow scope.

### Approval uncertainty

The required C0-C5 approval level is unclear or contested.

### Role conflict

Two or more role viewpoints produce incompatible statuses that change the outcome.

Examples:

```text
APOLLO: clear enough to send
THEMIS: transmission risk
ARGOS: source gap
ZEUS: human decision required
```

## Escalation levels

Not every doubt requires user interruption.

Pantheon should distinguish three levels.

### Level 1 — Reserve

The system continues but marks a limitation.

Use when the limitation does not change the safe use of the output.

Example:

```text
Source is undated. Output usable as draft only.
```

### Level 2 — Clarification

The system asks a targeted question because the answer materially affects the output.

Use when work can continue after one missing preference, source or boundary is clarified.

Example:

```text
Should this be written as an internal note or as a client-facing email?
```

### Level 3 — Decision required

The system blocks delivery, transmission, memory promotion or external action until the user decides.

Use when continuing would create governance risk.

Example:

```text
Sending this email may be interpreted as approval of the quote. Human decision required before transmission.
```

## Canonical status

When the gate triggers, the status should be explicit.

Recommended statuses:

```text
human_decision_required
user_clarification_required
source_required
scope_decision_required
approval_level_decision_required
transmission_blocked_pending_decision
memory_blocked_pending_decision
delivery_blocked_pending_decision
```

These statuses are governance signals.

They are not runtime commands.

They do not execute anything.

## User-facing format

A User Decision Gate should be readable by a non-technical professional.

Recommended structure:

```text
Discord detected

Object of conflict:
[short explanation]

Role positions:
- ATHENA: [structure or scope view]
- ARGOS: [source view]
- THEMIS: [risk and approval view]
- APOLLO: [clarity and delivery readiness view]
- HEPHAISTOS: [artifact feasibility view]
- IRIS: [transmission view]
- ZEUS: [procedural arbitration status]

Nature of tension:
[source / scope / risk / delivery / transmission / memory / approval]

Severity:
low / medium / high / critical

Options:
1. [option]
2. [option]
3. [option]

Recommended procedure:
[procedural recommendation without replacing the user decision]

Decision effects:
- output:
- evidence:
- approval:
- memory:
- transmission:
```

## Decision options

The system should offer bounded options.

Recommended options include:

```text
continue_as_draft
continue_with_reserve
request_missing_source
ask_third_party_clarification
split_into_variants
narrow_scope
escalate_approval
block_delivery
block_transmission
reject_memory_candidate
allow_memory_candidate_review
```

The options should show consequences.

The system should not ask a vague question when it can present a structured decision.

Avoid:

```text
What do you want to do?
```

Prefer:

```text
Choose one of these procedures.
Each option has a different evidence, delivery and memory consequence.
```

## Professional example

User request:

```text
Prepare an email to the client validating this quote.
```

Detected tension:

```text
The quote includes work not clearly confirmed by the specification.
Sending approval may create professional or contractual ambiguity.
```

User-facing gate:

```text
Transmission blocked pending decision.

Object of conflict:
The quote may include a scope item not confirmed by the CCTP.

Role positions:
- ATHENA: quote comparison should be structured before response.
- ARGOS: missing or unclear source for the disputed item.
- THEMIS: validation email may create contractual risk.
- APOLLO: the email can be made clear, but clarity does not remove the risk.
- IRIS: transmission should wait for approval.
- ZEUS: human decision required.

Options:
1. Draft a neutral clarification email.
2. Draft an internal note only.
3. Block response until the missing source is provided.
4. Prepare two variants for review.

Recommended procedure:
Option 1 or 2. Do not send a validation email in the current state.
```

## Evidence impact

A User Decision Gate should be referenced in the Evidence Pack when it affects legitimacy.

The Evidence Pack may record:

- conflict summary;
- role statuses;
- sources involved;
- missing source or contradiction;
- user options presented;
- user decision;
- resulting approval state;
- impact on output, delivery, memory or transmission.

The Evidence Pack must not include hidden chain-of-thought or raw scratchpad.

## Run Trace impact

A Run Trace View may display the User Decision Gate as a milestone.

Example:

```text
13:42 — contradiction detected
13:44 — User Decision Gate opened
13:47 — user chose request_missing_source
13:48 — delivery blocked pending source
```

This is review trace.

It is not runtime state.

## Memory impact

If a User Decision Gate involves memory, the default posture is conservative.

Memory should be blocked when:

- evidence is incomplete;
- scope is unclear;
- user decision is pending;
- the claim is contradicted;
- the claim is sensitive;
- the claim is valid only for a narrow dossier but proposed broadly.

A user may authorize a Register Candidate review.

The user decision does not automatically create a Registre Probatoire entry.

## Relationship to approvals and projection

A User Decision Gate may lead to an approval request.

It does not itself grant approval.

An optional runtime client may expose technical interaction around the gate.

Pantheon Cockpit may project the governed gate, disagreement, approval state and linked decision.

Hermes may report the conflict.

Pantheon governs the status.

The human makes the decision when required.

```text
Hermes WebUI available != Hermes WebUI selected
client display != approval
projection != persistence
```

## Anti-patterns

Avoid:

```text
forcing a synthetic answer when roles disagree
hiding source conflict behind fluent prose
letting ZEUS decide truth by itself
sending external communication because it is well written
promoting memory because a claim was repeated
asking the user vague questions without options
turning every small doubt into a blocking gate
```

Prefer:

```text
explicit discord
bounded options
procedural recommendation
clear consequence mapping
approval threshold visibility
memory status visibility
```

## Final rule

```text
The roles open angles.
Tensions reveal risk.
ZEUS attempts procedural arbitration.
If decision value remains doubtful, Pantheon exposes the discord.
The human decides.
Only the validated remains.
```
