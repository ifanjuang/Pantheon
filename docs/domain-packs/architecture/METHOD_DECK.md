# Architecture Method Deck

Status: candidate support doctrine — architecture-domain Method Cards for governed AI use in agency workflows.
Boundary profile: candidate_support_note.

Runtime status: non-executable.

This document specializes `METHOD_CARD_MODEL.md` for architecture practice.

It does not implement a UI, renderer, workflow engine, method selector, source validator, RAG system, OCR pipeline, PDF tool, email sender, approval engine, memory engine, Hermes skill, connector, schema, test or external action.

## Purpose

Architecture work is consequential because an AI error can become a wrong source, an implicit validation, a mission-scope expansion, a false proof, an unauthorized transmission or a professional commitment.

This deck turns generic Method Cards into professional cards that can be proposed by Roles during Runs.

```text
A method appears because a Role detects a tension.
It does not appear because it is intellectually interesting.
```

## Cockpit budget

A task should normally expose at most:

```text
1 primary method;
1 guardrail method;
1 verification method;
other methods stay in the trace unless they change proof, scope, cost, status, memory or action.
```

## Practical deck posture

This deck is intentionally broader than what the cockpit should show by default.

```text
Deck breadth is allowed.
Cockpit clutter is not.
```

The deck is a reference set for architecture-domain method selection. It should not be rendered as a flat checklist where every card competes for visibility.

### Visibility tiers

| Tier | Method posture | Cards | Cockpit rule |
|---|---|---|---|
| A | gateway methods | `source_admission`, `assertion_mapping`, `mission_scope_guard`, `external_commitment_guard`, `probative_review` | eligible for default task visibility when the corresponding risk is present |
| B | dossier-specialist methods | `authority_qualification`, `contractual_decomposition`, `phase_gate_review`, `site_observation_review`, `quote_variation_review`, `visa_commitment_review`, `reception_risk_review`, `cerfa_field_claim_review` | visible only when the dossier situation matches or a gateway method spawns them |
| C | productive method | `constrained_generation` | visible only when drafting, synthesis or variant generation is itself the requested work or creates risk |

Tier A cards form the practical skeleton of the architecture deck. They answer the recurring governance questions:

```text
What entered?
What does the output claim?
Does it exceed mission or responsibility?
Does it leave the perimeter?
Is the support sufficient for the intended effect?
```

Tier B cards specialize the skeleton for real architecture situations. They should not be preloaded unless the task mentions, receives or produces the relevant object: quote, contract, phase, site observation, visa, reception or CERFA.

Tier C is intentionally separated. `constrained_generation` can produce useful drafts, image prompts, variants or synthesis candidates. It is not a proof, source review, mission guard or external-action gate.

### Selection rule

```text
Start with the smallest useful method set.
Add a specialist method only when a trigger is explicit.
Keep unused methods in the trace, not on the screen.
```

A normal task should start from one of these patterns:

| Situation | Primary method | Guardrail method | Verification method |
|---|---|---|---|
| source enters the task | `source_admission` | `mission_scope_guard` if wording may engage the agency | `probative_review` if a claim will rely on it |
| output contains factual claims | `assertion_mapping` | `mission_scope_guard` if claims imply responsibility | `probative_review` |
| external send / filing / publication | `external_commitment_guard` | `mission_scope_guard` | `probative_review` |
| complementary quote | `quote_variation_review` | `contractual_decomposition` | `probative_review` |
| chantier report | `site_observation_review` | `mission_scope_guard` | `assertion_mapping` |
| CERFA / administrative filing | `cerfa_field_claim_review` | `external_commitment_guard` | `probative_review` |
| EXE / VISA | `visa_commitment_review` | `mission_scope_guard` | `probative_review` |
| reception / reserve lifting | `reception_risk_review` | `mission_scope_guard` | `probative_review` |
| draft / synthesis / image prompt | `constrained_generation` | `mission_scope_guard` if professional posture appears | `assertion_mapping` if factual claims are introduced |

If a second specialist method is needed, the card must record why the first one was insufficient. This prevents method inflation from becoming a disguised workflow engine.

## Role registry discipline

`likely_roles` must only name registered Pantheon Roles from `AGENTS.md`.

A professional human reviewer, architect, maître d'oeuvre, project lead or client representative is not a Pantheon Role.

When human professional judgement is required, use `human_review`, not `likely_roles`.

No new role is promoted by this deck.

## Common fields

Each professional card should define:

```text
id:
name:
purpose:
likely_roles:
human_review:
trigger:
minimum_output:
evidence_delta:
scope_delta:
gate_triggers:
hermes_profile_hint:
forbidden_outputs:
stop_condition:
failure_modes:
visibility:
```

## Core professional method cards

### source_admission

Purpose: prevent a received source from becoming trusted by default.

Likely roles: ARGOS, ATHENA.

Human review: required when the source may support a professional conclusion, filing, contractual position or external instruction.

Trigger: a document, mail, quote, plan, photo, CR, PLU extract, CERFA, report or notice enters the task.

Minimum output: source type, issuer, date, version, project scope, authority class, applicability, risk and recommended next step.

Evidence delta: qualifies_source, raises_question.

Scope delta: clarifies_scope.

Gate triggers: source supports a consequential claim, or source is outdated, partial, derived or contradicted.

Hermes profile hint: doc-intake, evidence-review.

Forbidden outputs: source validation, professional conclusion, external transmission, canonical memory.

### authority_qualification

Purpose: decide which source has candidate priority when sources conflict.

Likely roles: ARGOS, THEMIS, ZEUS.

Human review: required when the retained source affects professional posture, client decision, filing, payment, visa, reception or mission scope.

Trigger: sources give different values, clauses, dates, amounts, statuses or decisions.

Minimum output: conflicting sources, conflicting values, relative authority, source retained as candidate, source downgraded, uncertainty, question if arbitration is required.

Evidence delta: resolves_conflict, changes_confidence, raises_question.

Scope delta: clarifies_scope.

Gate triggers: retained source affects payment, visa, reception, filing, client decision, enterprise instruction or memory promotion.

Hermes profile hint: evidence-review.

Forbidden outputs: final contractual interpretation, payment approval, source canonization, external instruction.

### assertion_mapping

Purpose: turn a candidate output into reviewable assertions.

Likely roles: ARGOS, ATHENA, APOLLO.

Human review: required when mapped assertions will be reused in client-facing, administrative, contractual or technical professional material.

Trigger: a report, email, note, visa, form, analysis, CR entry or synthesis contains factual or professional claims.

Minimum output: assertion, source reference, source status, confidence, contradictions, risk if false, allowed reuse scope.

Evidence delta: adds_source, weakens_claim, changes_confidence.

Scope delta: clarifies_scope if assertions imply mission posture.

Gate triggers: unsourced assertion supports consequential output.

Hermes profile hint: evidence-review, governance-review.

Forbidden outputs: validated truth, final proof, external transmission.

### contractual_decomposition

Purpose: decompose a contractual issue into clauses, lots, amounts, inclusions, exclusions and required decisions.

Likely roles: THEMIS, ARGOS, ZEUS.

Human review: required before any client recommendation, enterprise instruction, claim response, payment posture or mission-scope position.

Trigger: quote, amendment, CCTP / CCAP clause, situation, invoice, claim, delay or scope dispute.

Minimum output: contract corpus, lot, clause reference, expected prestation, claimed prestation, included/excluded/changed/unclear status, financial implication, question or gate.

Evidence delta: adds_source, resolves_conflict, raises_question.

Scope delta: clarifies_scope, detects_out_of_scope, requires_mission_gate.

Gate triggers: avenant, client decision, enterprise instruction, payment validation, claim rejection, mission extension.

Hermes profile hint: architecture-domain, evidence-review, governance-review.

Forbidden outputs: final contractual decision, order to enterprise, financial approval.

### mission_scope_guard

Purpose: detect wording or action that may exceed mission scope or imply responsibility.

Likely roles: THEMIS, ZEUS.

Human review: required whenever the candidate wording may bind the architect, the agency, the client, an enterprise or an administrative filing.

Trigger: validate, approve, order, confirm, accept, guarantee, certify, fault, responsibility, payment, conformity, visa, OPC or insurance implication.

Minimum output: engaging wording or action, possible commitment, mission boundary, risk, safer formulation candidate, gate required or not.

Evidence delta: weakens_claim, opens_gate.

Scope delta: detects_out_of_scope, requires_mission_gate.

Gate triggers: external transmission, visa, client validation, enterprise instruction, fault recognition, mission extension, insurance-related statement.

Hermes profile hint: governance-review.

Forbidden outputs: responsibility decision, external send, canonical memory.

### external_commitment_guard

Purpose: separate a prepared candidate from an action that affects outside parties.

Likely roles: ZEUS, THEMIS, IRIS.

Human review: required before any external effect.

Trigger: send email, file dossier, deposit form, publish CR, issue visa, notify enterprise, update external tracker or request payment.

Minimum output: action candidate, recipient, object of transmission, approval required, evidence required, duplicate risk, action state.

Evidence delta: opens_gate.

Scope delta: requires_mission_gate if professional commitment is possible.

Gate triggers: any external effect.

Hermes profile hint: governance-review.

Forbidden outputs: automatic send, automatic filing, automatic merge, automatic memory promotion.

### probative_review

Purpose: check whether an output is sufficiently supported for its intended effect.

Likely roles: ARGOS, APOLLO, ZEUS.

Human review: required when proof posture may support a decision, filing, visa, payment, reception, claim, memory promotion or professional advice.

Trigger: output may justify decision, memory, transmission, payment, visa, reception, claim or professional advice.

Minimum output: claims reviewed, sources checked, missing evidence, contradictions, confidence, allowed reuse scope, remaining questions.

Evidence delta: changes_confidence, weakens_claim, opens_gate.

Scope delta: clarifies_scope if use context is limited.

Gate triggers: proof gap affects consequential output.

Hermes profile hint: evidence-review.

Forbidden outputs: proof validation, Registre Probatoire entry, external approval.

### phase_gate_review

Purpose: prevent phase progress from being treated as validated state without evidence and authorized decision.

Likely roles: ZEUS, THEMIS, APOLLO.

Human review: required before a phase is represented as validated, filed, accepted, closed or ready for external reliance.

Trigger: APS, APD, DP/PC, PRO, DCE, ACT, EXE/VISA, DET, AOR, DOE, GPA or archive state changes.

Minimum output: phase, expected deliverables, available evidence, missing evidence, actor who may validate, status candidate/ready/blocked/validated externally.

Evidence delta: adds_source, changes_confidence, opens_gate.

Scope delta: clarifies_scope.

Gate triggers: phase state changes, filed package, client approval, consultation launch, visa, reception, reserve lifting.

Hermes profile hint: architecture-domain, governance-review.

Forbidden outputs: phase validation, filing, client approval record, canonical memory promotion.

### site_observation_review

Purpose: qualify site observations before they become report points.

Likely roles: ARGOS, ATHENA, APOLLO.

Human review: required before the observation becomes a formal reserve, instruction, responsibility statement or site report conclusion.

Trigger: photo, site note, oral report, enterprise message or repeated observation may enter a CR or reserve list.

Minimum output: observation, location, date/source, lot, previous CR link, status, severity, recommended wording, question if weak.

Evidence delta: adds_source, weakens_claim, raises_question.

Scope delta: clarifies_scope if observation implies instruction.

Gate triggers: reservation, formal notice, enterprise instruction, responsibility implication.

Hermes profile hint: doc-intake, evidence-review, architecture-domain.

Forbidden outputs: final technical diagnosis, enterprise order, formal reserve issuance without gate.

### quote_variation_review

Purpose: review additional, modified or disputed quotations without silent approval.

Likely roles: THEMIS, ARGOS, ATHENA.

Human review: required before any recommendation, approval posture, refusal, avenant, order or payment-related action.

Trigger: complementary quote, variante, moins-value, plus-value, revised estimate or enterprise claim.

Minimum output: quote identity, lot, amount, object, contractual basis, technical basis, financial coherence, missing detail, candidate status.

Evidence delta: adds_source, resolves_conflict, raises_question, changes_confidence.

Scope delta: clarifies_scope, detects_out_of_scope, requires_mission_gate.

Gate triggers: client recommendation, avenant, order, payment, refusal.

Hermes profile hint: architecture-domain, evidence-review, governance-review.

Forbidden outputs: approval, enterprise instruction, client decision, final financial validation.

### visa_commitment_review

Purpose: review EXE / VISA wording and status before it can imply validation beyond the intended posture.

Likely roles: THEMIS, ZEUS, APOLLO.

Human review: required before any visa wording, reserved comment, external send or technical-position statement.

Trigger: EXE document, technical detail, product sheet, method statement, shop drawing or note is prepared for visa or comment.

Minimum output: document identity, issuer, index, object, review perimeter, comments, reserved points, wording risk, visa status candidate, gate required.

Evidence delta: adds_source, weakens_claim, opens_gate.

Scope delta: clarifies_scope, requires_mission_gate.

Gate triggers: visa issuance, acceptance-like wording, technical conformity statement, responsibility shift.

Hermes profile hint: architecture-domain, governance-review.

Forbidden outputs: final visa, technical guarantee, enterprise instruction, external send.

### reception_risk_review

Purpose: identify evidence, reservations and responsibility posture before reception or reserve lifting.

Likely roles: ZEUS, THEMIS, ARGOS, APOLLO.

Human review: required before reception posture, reserve omission, reserve lifting, fault recognition or external notification.

Trigger: OPR, reception, reserve list, reserve lifting, GPA issue or handover.

Minimum output: works/lot, observed state, evidence, reserve candidate, severity, responsible party candidate, missing confirmation, implication, gate required.

Evidence delta: adds_source, weakens_claim, opens_gate.

Scope delta: clarifies_scope, requires_mission_gate.

Gate triggers: reception, reserve omitted, reserve lifted, GPA issue closed, formal statement sent.

Hermes profile hint: evidence-review, governance-review, architecture-domain.

Forbidden outputs: pronouncing reception, lifting reserve, recognizing fault, external notification without approval.

### cerfa_field_claim_review

Purpose: treat each sensitive form field as a claim requiring source, confidence and review status.

Likely roles: ARGOS, ATHENA, ZEUS.

Human review: required before client signature, administrative filing, external transmission or canonical project-data update.

Trigger: CERFA, DP/PC field, surface, parcel, address, applicant identity, work description or regulatory checkbox.

Minimum output: field, value candidate, source, confidence, contradiction, comment, missing information, review requirement.

Evidence delta: adds_source, raises_question, changes_confidence, opens_gate.

Scope delta: clarifies_scope.

Gate triggers: administrative filing, client signature, external transmission.

Hermes profile hint: doc-intake, architecture-domain, evidence-review.

Forbidden outputs: filing, signature-ready claim without review, canonical project data mutation.

### constrained_generation

Purpose: generate drafts or creative variants while preserving source, mission, style and forbidden-effect constraints.

Likely roles: ATHENA, HEPHAISTOS, THEMIS, IRIS.

Human review: required before external use or when the draft expresses professional advice, project position, mission boundary, factual assertion or commitment.

Trigger: draft email, notice, CR wording, client explanation, design variants, image prompts, synthesis or presentation text.

Minimum output: constraints used, forbidden elements, source dependence, style/tone, draft candidate, review points, external-action status.

Evidence delta: none by default; raises_question if the draft introduces unsupported claims.

Scope delta: detects_out_of_scope if generation overstates mission or authority.

Gate triggers: external use, professional assertion, change of project position.

Hermes profile hint: architecture-domain, governance-review if external.

Forbidden outputs: external send, final approved wording, unsupported factual assertion, mission expansion.

## Review conclusion — 2026-06-29

Accepted:

```text
The deck may remain broad as a reference deck for architecture-domain Method Cards.
Tier A gateway methods should carry most cockpit visibility.
Tier B specialist methods should appear only on explicit dossier triggers.
Tier C productive generation must stay separate from proof and gate methods.
```

Refused:

```text
Flat display of every Method Card in ordinary tasks.
Treating a method sequence as a workflow engine.
Treating a productive generation method as proof, validation or approval.
```

To verify:

```text
Use PR Pantheon-Next#238 run tests to check whether the Tier A / B / C split reduces cockpit noise.
Review the mobile prototype with real architecture prompts and long French labels.
Check whether some Tier B methods should move into example-only material if they rarely trigger.
```

To arbitrate:

```text
Whether this deck stays candidate support doctrine or is split later into:
1. a compact active architecture cockpit deck;
2. an extended reference deck;
3. run-test examples.
```

## Relationship with reasoning modes

Raw reasoning modes remain governed by `REASONING_MODES_LIBRARY.md`.

This deck translates some of them into professional method cards suitable for cockpit visibility.

## Core invariant

```text
Architecture Method Cards guide professional AI work.
They produce candidates, questions and gates.
They do not validate, approve, send, remember or execute.
```

The validated remains.
