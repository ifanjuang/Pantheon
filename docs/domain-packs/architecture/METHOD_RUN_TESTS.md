# Architecture Method Run Tests

Status: candidate support examples — compact architecture-domain run tests for Method Cards, Hermes handoff and cockpit density.
Boundary profile: candidate_support_note.

Runtime status: non-executable.

This document tests whether Method Cards, Hermes handoff discipline and the Card Stack cockpit grammar reduce confusion in real architecture-agency situations.

It does not implement a workflow engine, Hermes skill, UI, schema, approval engine, memory engine, connector, scheduler, queue or external action.

## Relationship with `METHOD_DECK.md`

These tests use the visibility tiers defined in `METHOD_DECK.md`.

```text
Tier A — gateway methods.
Tier B — dossier-specialist methods.
Tier C — productive method.
```

The test target is cockpit density, not exhaustive method display.

```text
A run test succeeds when the cockpit shows the smallest useful set.
It fails when every plausible method becomes visible at once.
```

## Purpose

Pantheon Next must not increase the number of things to see.

It must reduce confused decisions.

Each run test asks:

```text
Is it true?
Is it sourced?
Is it inside mission scope?
Can it leave the cockpit?
```

A run test does not prove that the UI works, that Hermes works or that an output is valid. It tests whether the governance grammar is usable.

## Operating model under test

```text
User request
-> Task Contract Candidate
-> minimal method set
-> Hermes bounded execution
-> Result Candidate + Evidence Pack Candidate
-> proof / scope / external-effect check
-> Method Proposal Candidate if a threshold fails
-> visible gate if consequential
-> human decision
```

Hermes is never the professional responsible role.

```text
Role observes.
Method structures.
Competence produces.
Hermes executes.
Evidence supports.
Gate authorizes or blocks.
Human decides.
```

## Visibility budget

A task should normally expose:

```text
1 primary method;
1 guardrail method;
1 verification method;
1 main gate;
2 or 3 critical proofs or gaps.
```

Everything else belongs in the verso, trace or constellation unless it changes proof, scope, memory, status or external action.

## Failure taxonomy

| Failure type | Signal | Default method | Visibility posture |
|---|---|---|---|
| `source_weak` | source partial, stale or unclear | `source_admission` / `probative_review` | Tier A gap |
| `source_conflict` | two sources contradict | `authority_qualification` | Tier B only if explicit |
| `claim_unsourced` | assertion has no support | `assertion_mapping` / `probative_review` | Tier A if consequential |
| `site_observation_weak` | photo or note cannot support a CR point | `site_observation_review` | Tier B only for chantier observation |
| `quote_or_payment_risk` | amount, scope or receivability unclear | `quote_variation_review` | Tier B only for quote/payment context |
| `field_as_claim_weak` | CERFA field lacks support | `cerfa_field_claim_review` | Tier B only for administrative field |
| `scope_risk` | wording may exceed mission | `mission_scope_guard` | Tier A warning or sub-card |
| `external_action_risk` | draft may be sent, filed or transmitted | `external_commitment_guard` | Tier A gate |
| `output_too_vague` | candidate is not actionable | `constrained_generation` under tighter constraints | Tier C only if drafting is the task |

Raw reasoning modes stay behind professional Method Cards unless they change proof, scope, gate or decision path.

## Test Case A — Chantier / compte rendu de visite

### Contract

```text
User intent:
Prepare a usable chantier report from notes, photos and the previous report.

Professional risk:
A weak observation becomes a formal record, instruction or reserve.

Expected candidate:
Draft CR + uncertain points + draft email.

Forbidden final effects:
send email;
issue instruction;
create reserve;
canonical memory;
client or enterprise commitment.

Main gate:
external transmission.
```

### Minimal method set

| Function | Method | Tier | Visibility |
|---|---|---|---|
| Primary | `site_observation_review` | B | field because chantier observation is explicit |
| Guardrail | `mission_scope_guard` | A | sub-card only if wording is engaging |
| Verification | `assertion_mapping` | A | chip / field for report claims |
| Additional verification if triggered | `probative_review` | A | sub-card only if evidence remains weak |
| Gate | `external_commitment_guard` | A | gate |

Trace-only methods may include `source_admission` for intake and `constrained_generation` for drafting.

### Failure signal

```text
A photo is used to describe a defect, but the location is uncertain.
```

### Method Proposal Candidate

```yaml
proposingRole: ARGOS
detectedProblem: visual evidence too weak to support a CR assertion
failedThreshold: source / location confidence
currentMethod: site_observation_review
proposedMethod: probative_review
expectedGain: distinguish observation candidate from report-ready assertion
evidenceDelta: weakens_claim
scopeDelta: none
visibilityDelta: promote Tier A verification from chip / trace to sub-card
gateRequired: true before CR transmission
status: proposed
```

### Executable Hermes handoff

```text
Task Contract:
Check whether the disputed chantier observation is sufficiently supported for a CR assertion.

Context Pack:
photo, previous CR point, site notes, lot concerned, date if available.

Method Card:
probative_review

Allowed outputs:
claim support status;
missing source;
confidence;
uncertainty;
wording candidate with reserve.

Forbidden outputs:
final technical diagnosis;
formal enterprise instruction;
reserve issuance;
external email.
```

### Cockpit success display

```text
Draft CR candidate.
Main gate: external transmission.
Critical gap: photo not localized.
Method chip: site_observation_review.
Verification chip: assertion_mapping.
Promoted verification: probative_review only for the unresolved weak source.
Next action: ask source / correct / block send.
```

### Failure condition

```text
The observation is stated as fact.
The send action is available without gate.
The user sees every possible method and misses the gate.
```

## Test Case B — Devis complémentaire

### Contract

```text
User intent:
Analyze the quote and prepare an answer to the client.

Professional risk:
A draft answer becomes implicit validation, payment advice or enterprise instruction.

Expected candidate:
Candidate opinion + draft MOA email.

Forbidden final effects:
approve quote;
recommend payment as final;
send email;
instruct enterprise;
create amendment as validated.

Main gate:
client transmission.
```

### Minimal method set

| Function | Method | Tier | Visibility |
|---|---|---|---|
| Primary | `quote_variation_review` | B | field because quote is explicit |
| Guardrail | `mission_scope_guard` | A | sub-card if wording may engage agency |
| Verification | `probative_review` | A | chip / sub-card if proof is weak |
| Specialist if triggered | `contractual_decomposition` or `authority_qualification` | B | one sub-card only |
| Gate | `external_commitment_guard` | A | gate |

`source_admission` may run in trace. `constrained_generation` may draft the email but should remain trace-only unless the draft introduces risky wording.

### Failure signal A — source contradiction

```text
The quote amount differs from a payment situation or prior signed amendment.
```

```yaml
proposingRole: ARGOS
detectedProblem: quote amount conflicts with payment situation or amendment
failedThreshold: source precedence
currentMethod: quote_variation_review
proposedMethod: authority_qualification
expectedGain: identify which source may be used as candidate priority
evidenceDelta: resolves_conflict
scopeDelta: clarifies_scope
visibilityDelta: promote one Tier B specialist from trace to sub-card
gateRequired: false internally, true before recommendation
status: proposed
```

### Failure signal B — risky wording

```text
Nous validons ce devis complémentaire.
```

```yaml
proposingRole: THEMIS
detectedProblem: wording may imply agency approval
failedThreshold: mission scope / external commitment
currentMethod: constrained_generation
proposedMethod: mission_scope_guard
expectedGain: produce safer wording candidate
evidenceDelta: weakens_claim
scopeDelta: requires_mission_gate
externalActionDelta: opens_gate
visibilityDelta: promote Tier A guardrail to sub-card
gateRequired: true before send
status: needs_human_gate
```

### Cockpit success display

```text
Candidate opinion.
Amount / scope conflict only if present.
Mission-scope warning only if risky wording exists.
MOA transmission gate.
Next action: ask decomposition / correct wording / send after gate / block.
```

### Failure condition

```text
The draft uses approval language.
Hermes recommends payment as final.
Contract, quote, source and generation methods all appear as equal cards.
The gate is buried in details.
```

## Test Case C — CERFA / dépôt administratif

### Contract

```text
User intent:
Prepare the CERFA for DP/PC filing.

Professional risk:
A weak field value becomes a signed administrative claim.

Expected candidate:
Completed form candidate + uncertain fields list.

Forbidden final effects:
file application;
mark signature-ready;
mutate canonical project data;
claim administrative certainty without source.

Main gate:
administrative filing.
```

### Minimal method set

| Function | Method | Tier | Visibility |
|---|---|---|---|
| Primary | `cerfa_field_claim_review` | B | field / sub-card because CERFA is explicit |
| Guardrail | `external_commitment_guard` | A | gate |
| Verification | `probative_review` | A | sub-card if source is weak |
| Specialist if triggered | `phase_gate_review` | B | only if filing changes phase status |
| Support | `assertion_mapping` | A | trace or field if multiple factual claims appear |

`source_admission` may run in trace for form version intake. It becomes visible only if form version, issuer, parcel source or project identity is uncertain.

### Failure signal

```text
A surface field is filled from a plan label, but the calculation source is missing.
```

```yaml
proposingRole: ARGOS
detectedProblem: administrative field is insufficiently supported
failedThreshold: field-as-claim proof
currentMethod: cerfa_field_claim_review
proposedMethod: probative_review
expectedGain: distinguish candidate value from filing-ready value
evidenceDelta: raises_question
scopeDelta: none
externalActionDelta: opens_gate before filing
visibilityDelta: promote verification method to sub-card
gateRequired: true before filing
status: needs_human_gate
```

### Cockpit success display

```text
CERFA candidate.
Surface field uncertainty.
Filing gate.
Next action: confirm calculation / correct / block filing.
```

### Failure condition

```text
Field values look final without source.
Hermes silently fills missing data.
The filing button is available without gate.
Uncertainty appears only in trace.
All form-related methods appear as equal visible cards.
```

## Cross-test success criteria

Pantheon succeeds if:

```text
the user sees one clear decision surface;
weak sources do not become proof;
drafts do not become external actions;
methods do not become validation;
Hermes never acts outside the handoff;
gates are visible before consequential effects;
Tier B methods appear only when explicitly triggered;
Tier C generation never masks proof or approval gaps.
```

## Cross-test failure criteria

Pantheon fails if:

```text
too many cards hide the gate;
Hermes reruns without bounded contract;
the method is visible but useless;
raw reasoning modes dominate the UX;
a draft implies approval;
a source conflict is hidden;
an external action is available before gate;
candidate memory is promoted without evidence;
specialist methods appear as default checklist items.
```

## Final invariant

```text
A run test exists to prove that Pantheon reduces professional confusion.
It does not prove that the runtime works.
It does not validate the UI.
It does not authorize execution.
It does not create doctrine by itself.
```

The validated remains.
