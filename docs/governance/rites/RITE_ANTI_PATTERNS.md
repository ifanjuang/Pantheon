# Rite Anti-Patterns

Status: active doctrine - rite misuse and drift prevention.

This document records how rites can be misused.

It protects Pantheon Next from turning governed methods into hidden workflows, agent debates, approval shortcuts or memory shortcuts.

It does not implement any runtime behavior.

```text
Optional runtime clients may expose interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed rite, review and decision state.
Pantheon Next governs.
The human decides consequential effects.
```

## Purpose

Rites are dangerous precisely because they look disciplined.

A poorly governed rite can make drift appear legitimate.

This document records recurring misuse patterns before they become practice.

## Core rule

```text
A rite is a governance method.
It is not a workflow.
It is not proof.
It is not approval.
It is not memory.
It is not execution.
```

## Anti-pattern: Rite as workflow

### Drift

A rite is treated as an executable sequence, hidden process, runtime graph or automatic procedure.

### Symptoms

- runtime-client or Cockpit labels imply the rite is running;
- a Task Contract launches a rite instead of recommending it;
- an Evidence Pack records workflow state rather than governance result;
- a rite triggers the next rite.

### Boundary

A rite may define a governance sequence.

It must not become an executable workflow.

### Correction

Use `RITE_INVOCATION_POLICY.md`.

Require ZEUS authorization and ZEUS closure.

Record only reviewable governance effects.

## Anti-pattern: Rite as agent debate

### Drift

Role viewpoints inside a rite are treated as autonomous agents arguing behind the scenes.

### Symptoms

- raw role debate is stored;
- role names are described as workers;
- users are told that roles have internally discussed;
- hidden disagreement is converted into smooth consensus.

### Boundary

Pantheon Roles are responsibilities of judgment.

They are not autonomous agents.

### Correction

Use `role_viewpoints_involved`, not `roles called`.

Expose only status, tension, risk, evidence need and next procedure.

Do not store hidden chain-of-thought or raw debate.

## Anti-pattern: Rite as proof theater

### Drift

A rite creates a persuasive review artifact that looks like evidence but does not prove the claim.

### Symptoms

- source tables hide unsupported claims;
- citation quantity is treated as confidence;
- retrieved knowledge is treated as evidence;
- a clean Rite Review Card is mistaken for validation.

### Boundary

A rite can organize evidence needs.

It cannot create proof by itself.

### Correction

Assign claim status.

Use `CONCORDANCE_DES_SOURCES.md` only when the source relationship matters.

Preserve unsupported and contradicted claims.

## Anti-pattern: Rite as approval bypass

### Drift

A rite completion is treated as approval.

### Symptoms

- `rite_completed` is interpreted as deliverable approval;
- review output is sent externally without approval;
- User Decision Gate is skipped because a rite produced a recommendation;
- ZEUS status is treated as human validation.

### Boundary

Rite completion is not approval.

ZEUS arbitrates status and procedure, not final truth.

### Correction

Keep approval governed by `APPROVALS.md`.

Open a User Decision Gate when procedural arbitration is insufficient.

## Anti-pattern: Rite as memory shortcut

### Drift

A rite output is promoted or reused as memory because it appears structured and useful.

### Symptoms

- Rite Review Card becomes a Registre Probatoire entry;
- repeated rite outputs become assumed doctrine;
- session refoundation turns discarded material into hidden memory;
- a pattern is retained without evidence link or scope.

### Boundary

Rite output is not memory.

A rite may support a Register Candidate only when scoped, explicit, evidence-linked and approval-bound.

### Correction

Use `MEMORY.md` and `SCOPE_ISOLATION.md`.

Never promote memory from rite output alone.

## Anti-pattern: Rite as context deletion

### Drift

Refoundation is used to erase inconvenient contradictions, failed variants or unresolved user preferences.

### Symptoms

- reset removes unresolved tensions;
- discarded variants disappear without status;
- a user decision is silently omitted;
- old context is treated as invalid rather than historical.

### Boundary

Reset is not deletion.

Refoundation must preserve unresolved tensions.

### Correction

Use `REFONDATION_DE_SESSION.md` with explicit preserved invariants, discarded noise, unresolved tensions and new Task Contract draft.

No contradiction may disappear without status.

## Anti-pattern: Rite as style ritual

### Drift

Rites are invoked for low-risk wording, tone or cosmetic changes.

### Symptoms

- every draft receives full autocritique;
- Apollo or Themis is invoked for style-only work;
- low-risk edits become bureaucratic;
- governance cost exceeds governance value.

### Boundary

No rite for style-only changes unless style affects legal meaning, professional responsibility, external transmission, contractual interpretation, evidence clarity or approval status.

### Correction

Use the rite budget.

Prefer direct editing for low-risk style work.

## Anti-pattern: Rite overuse

### Drift

Rites become default behavior rather than exceptional governance methods.

### Symptoms

- medium-risk tasks use multiple rites by habit;
- low-risk tasks start with a rite;
- rites are invoked because they are available;
- work slows without reducing risk.

### Boundary

Low-risk task means no rite by default.

Medium-risk task means one rite maximum unless ZEUS justifies otherwise.

Three rites or more require User Decision Gate or task split.

### Correction

Use `RITE_INVOCATION_POLICY.md` and record the cost.

If the rite does not change decision quality, evidence quality, risk posture, memory posture or delivery safety, do not invoke it.

## Anti-pattern: Rite chaining

### Drift

One rite leads to another until a hidden workflow is recreated.

### Symptoms

```text
Premisses Cachees
-> Divergence Controlee
-> Autocritique Contradictoire
-> Concordance des Sources
-> Refondation de Session
-> new Task Contract
-> another rite
```

### Boundary

A rite may reveal the need for another rite.

It must not trigger another rite.

### Correction

A second rite requires ZEUS status and explicit reason.

A third rite requires User Decision Gate, task split, scope narrowing or explicit high-risk justification.

## Anti-pattern: UI activity illusion

### Drift

A runtime-client or Cockpit display makes a rite appear to be running or completed as a process.

### Symptoms

- `rite_active` appears like runtime state;
- `rite_completed` appears like approval;
- user sees display status as governance truth;
- UI affordance suggests execution.

### Boundary

Optional runtime clients expose interaction only.

Pantheon Cockpit projects governed rite status and decisions.

Neither executes, approves, closes or canonizes rites by display.

### Correction

Prefer non-runtime labels:

```text
rite_review_open
rite_under_governance_review
rite_review_closed
```

Display ZEUS status separately from client or Cockpit display state.

```text
Hermes WebUI available != Hermes WebUI selected
client selected != authority transfer
projection != persistence
```

## Anti-pattern: Zeus as truth oracle

### Drift

ZEUS closure status is treated as truth validation.

### Symptoms

- `rite_allowed` becomes confidence;
- `rite_completed_with_reserve` is treated as delivery approval;
- `rite_blocked` is treated as factual refutation;
- user preference is overridden by procedural closure.

### Boundary

ZEUS decides status and procedure.

ZEUS does not decide truth.

The human decides when procedural arbitration is insufficient.

### Correction

Keep claim status separate from procedure status.

Use User Decision Gate for value conflict, professional preference, insufficient evidence or strategic arbitration.

## Final rule

The more disciplined a rite looks, the more carefully its authority must be bounded.
