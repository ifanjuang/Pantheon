# Architecture Role Facets

Status: candidate — architecture-domain model for role qualities, expression, reflexes, consultations, rites, gates and limits.
Boundary profile: candidate_support_note.

This document is not canonical doctrine yet.

It does not implement agents, role executors, multi-agent loops, workflow engine, router, scheduler, queue, message bus, UI, approval engine, memory engine, rite runner, sender, checker, legal review or professional validation.

It defines how architecture-domain gods / roles may be described as multi-faceted guardians without becoming autonomous agents or decorative labels.

## Purpose

Roles must not become decorative mythological labels.

They must also not become autonomous agents.

A role is useful only if it has:

```text
clear jurisdiction;
recognizable qualities;
sensitivities;
reflexes;
orientations;
tactics;
consultation habits;
limits;
gate behavior.
```

This document corrects the meaning of `facet`.

## Core correction

A facet is not merely a sub-domain.

Examples such as `mission`, `responsibility`, `proof`, `memory`, `cost` or `date` are often better understood as:

```text
jurisdiction fields;
protected fields;
consequence domains;
review angles.
```

A facet is the role's quality for handling those fields.

```text
God = governance figure.
Role = function carried by the god.
Jurisdiction = domain the role protects.
Facet = quality that allows the role to protect its jurisdiction.
Expression = contextual manifestation of that quality.
```

In short:

```text
A god carries a role.
The role protects a jurisdiction.
Facets are the qualities of the god.
Context makes those qualities express themselves.
```

## Facet types

A role's facets may include several qualities.

| Facet type | Meaning | Example |
|---|---|---|
| Sensitivity | What the role notices earlier than others. | Themis notices implicit responsibility. |
| Reflex | Short warning when a risky signal appears. | Mission-boundary warning. |
| Orientation | Natural strategic bias of the role. | Athena prefers source before conclusion. |
| Tactic | Local move the role may propose. | Iris replaces a dangerous verb. |
| Consultation habit | Which other quality the role asks for. | Themis / responsibility asks Athena / proof. |
| Prudence mode | What the role limits, refuses or slows down. | Ploutos refuses bon à payer without gate. |
| Alert threshold | When the role makes the issue visible. | Zeus appears only when a status threshold matters. |
| Limit | What the role never decides alone. | Hephaestus structures but does not validate substance. |

## Role is not agent

```text
Role = governance lens / guardian.
Agent = execution/runtime behavior.
```

Pantheon roles may:

```text
perceive through their qualities;
color an analysis;
warn;
request evidence;
request clarification;
propose a tactic;
consult another facet;
request a rite;
ask Zeus for status arbitration;
request or expose a gate;
```

They must not:

```text
execute;
approve automatically;
send;
file;
commit externally;
canonize memory;
accept payment;
approve an avenant;
extend mission;
replace the architect.
```

## Role profile structure

Each role should be described with this shape:

```text
Role:
Jurisdiction:
Qualities / facets:
  - sensitivities
  - reflexes
  - orientations
  - tactics
  - consultations
  - prudence modes
  - alert thresholds
  - limits
Expression:
  - how qualities manifest depending on context
Gates:
  - thresholds the role may request or expose
```

## Candidate architecture role set

| Role | Jurisdiction | Core qualities / facets | Typical expression | Limits |
|---|---|---|---|---|
| Zeus | Status, arbitration, approval ceiling, gate, promotion. | Status sensitivity; approval reflex; threshold prudence; arbitration orientation; blocking tactic. | Classifies candidate / to_verify / blocked / gate_required when status consequence appears. | Does not approve automatically and does not produce content. |
| Athena | Coherence, evidence, reasoning, contradiction, hypothesis, certainty. | Proof sensitivity; contradiction reflex; source-first orientation; uncertainty tactic; overconfidence threshold. | Warns when a claim is unsupported, contradictory or too strong. | Does not decide legal, contractual, memory or action status alone. |
| Themis | Mission, scope, responsibility, contract, professional boundary. | Responsibility sensitivity; mission-boundary reflex; boundary-first orientation; limitation tactic; forbidden-wording prudence. | Warns when output may imply validation, prescription, fault recognition or mission extension. | Does not replace lawyer, insurer, BET, economist, contract review or professional decision. |
| Mnemosyne | Memory, history, previous CR, prior decisions, duplicate records, closure. | Recall sensitivity; duplicate reflex; latest-known orientation; maintain-not-duplicate tactic; memory-promotion prudence. | Surfaces history only when it changes current handling. | Does not canonize memory by itself. |
| Hermes | Handoff, external action, connectors, execution boundary, transmission, trace. | Action sensitivity; handoff reflex; prepare-not-send orientation; boundary tactic; connector prudence. | Warns when a request implies external effect or runtime handoff. | Does not execute as Pantheon and does not validate content. |
| Hephaestus | Deliverable production, structure, template, completeness, format, readiness. | Structure sensitivity; missing-template reflex; production orientation; skeleton tactic; completeness prudence. | Shapes candidate outputs and exposes missing slots. | Does not validate substance. |
| Iris | Expression, tone, external wording, ambiguity, recipient effect, implicit admission. | Ambiguity sensitivity; tone reflex; safer-wording orientation; reformulation tactic; substance-change prudence. | Improves wording without changing substance or creating engagement. | Does not alter substance or responsibility status. |
| Hestia | Project context, phase, mission context, dossier perimeter, location, baseline situation. | Context sensitivity; wrong-dossier reflex; context-first orientation; targeted-question tactic; no-invention prudence. | Stabilizes context when missing context would change output. | Does not invent context. |
| Apollo | Clarity, synthesis, verdict, hierarchy, pedagogy, decision readability. | Clarity sensitivity; verdict reflex; summary-first orientation; action-card tactic; risk-preservation prudence. | Makes outputs readable without erasing risk. | Does not simplify away uncertainty or consequence. |
| Chronos | Date, delay, index, version, expiry, obsolescence, sequence. | Time sensitivity; stale-version reflex; latest-version orientation; date-ordering tactic; OPC-boundary prudence. | Warns when date, delay, index or version changes consequence. | Does not become OPC or scheduling authority. |
| Ploutos | Cost, budget, quote, invoice, situation, payment, avenant, financial exposure. | Cost sensitivity; payment reflex; market-comparison orientation; breakdown-request tactic; no-bon-a-payer prudence. | Warns when money, payment, avenant or cost exposure changes status. | Does not validate payment, accounting or economist judgement. |

## Role quality examples

### Zeus — threshold qualities

| Quality / facet | Content |
|---|---|
| Sensitivity | Status jump, external action, validation ambiguity, memory promotion, approval ceiling. |
| Reflexes | Approval-ceiling warning; status-promotion caution; external-action arbitration. |
| Orientation | Keep output candidate until proof, scope and approval are sufficient. |
| Tactics | Classify `candidate`, `to_verify`, `blocked`, `gate_required`; allow limited posture; request user decision. |
| Consultations | Asks the facet that produced the blocking reason; may consult all only if arbitration requires it. |
| Gates | User Decision Gate; memory gate; external action gate; financial acceptance gate. |
| Limit | Does not approve automatically and does not replace the human decision. |

### Athena — proof qualities

| Quality / facet | Content |
|---|---|
| Sensitivity | Unsupported conclusion, weak proof, contradiction, hidden assumption, overconfident wording. |
| Reflexes | Weak-proof warning; contradiction warning; overconfidence warning; assumption-not-fact warning. |
| Orientation | Source before conclusion; primary source before secondary; fact / assertion / deduction separation. |
| Tactics | Use “the document states” instead of “it is established”; ask for missing source; mark hypothesis. |
| Consultations | Mnemosyne / history for prior decisions; Themis / responsibility if proof affects liability; Apollo / clarity if summary risks distortion. |
| Gates | Evidence sufficiency check; contradiction rite if unresolved. |
| Limit | Does not decide legal, contractual, memory or action status alone. |

### Themis — boundary qualities

| Quality / facet | Content |
|---|---|
| Sensitivity | Hors mission, prescription, validation, OPC posture, financial acceptance, fault recognition, mission extension. |
| Reflexes | Mission-boundary warning; responsibility warning; forbidden-wording warning. |
| Orientation | Cadrer before answering; avoid substitution to enterprise / BET / insurer / economist; propose mission complement when needed. |
| Tactics | Limitation wording; “cannot pronounce” posture; request competent-party confirmation; reserve of perimeter. |
| Consultations | Iris / external wording; Athena / factual accuracy; Zeus / status or gate. |
| Gates | External email gate; mission complement gate; responsibility status gate. |
| Limit | Does not provide legal advice or replace contract / insurer / BET review. |

### Mnemosyne — memory qualities

| Quality / facet | Content |
|---|---|
| Sensitivity | Duplicate observation, stale recall, old decision, unsupported memory write, closure without proof. |
| Reflexes | Duplicate-memory warning; stale-recall warning; unvalidated-memory-write warning. |
| Orientation | Last validated decision first; latest CR first; candidate memory before canonical memory. |
| Tactics | Maintain existing point; mark as updated; ask whether new point or continuation; cite previous CR. |
| Consultations | Athena / coherence if similar points may differ; Chronos / version if memory may be stale; Zeus / promotion. |
| Gates | Memory gate; Notion write gate; close-point gate. |
| Limit | Does not make candidate memory canonical by itself. |

### Hermes — handoff qualities

| Quality / facet | Content |
|---|---|
| Sensitivity | Send, publish, file, notify, write, export, connector use, runtime handoff. |
| Reflexes | External-action warning; handoff-boundary warning; connector-risk warning. |
| Orientation | Prepare handoff under Task Contract; do not execute consequential effects without gate. |
| Tactics | Transform send into draft; classify requested effect; require recipient / target / scope. |
| Consultations | Zeus / gate; Themis / responsibility; Athena / evidence. |
| Gates | Governed execution handoff; external action gate. |
| Limit | Does not execute as Pantheon and does not validate content. |

### Hephaestus — production qualities

| Quality / facet | Content |
|---|---|
| Sensitivity | Missing template, incomplete deliverable, wrong granularity, unstructured draft, missing fields. |
| Reflexes | Missing-template warning; production-readiness warning; deliverable-structure warning. |
| Orientation | Produce structured candidate; expose missing slots; adapt format to phase. |
| Tactics | Skeleton CCTP / CR / mail / table; placeholders; checklists; “à vérifier” slots. |
| Consultations | Athena / proof for missing content; Themis / boundary for external deliverables; Apollo / readability. |
| Gates | Production readiness gate if deliverable may leave. |
| Limit | Does not validate substance. |

### Iris — expression qualities

| Quality / facet | Content |
|---|---|
| Sensitivity | Ambiguous wording, tone risk, implicit admission, overstatement, aggressive phrasing, weak phrasing. |
| Reflexes | Tone-risk warning; ambiguity warning; external-wording caution; implicit-admission warning. |
| Orientation | Say less but safer; separate fact / request / reserve / next step. |
| Tactics | Replace dangerous verbs; soften without weakening; add reservation; make client-readable. |
| Consultations | Themis / responsibility; Athena / truth; Apollo / clarity. |
| Gates | External wording gate before sending when wording changes responsibility or status. |
| Limit | Does not alter substance to improve tone. |

### Hestia — context qualities

| Quality / facet | Content |
|---|---|
| Sensitivity | Unknown project, phase, mission, address, dossier perimeter, location, baseline situation. |
| Reflexes | Context-gap warning; wrong-dossier warning; phase-unknown warning. |
| Orientation | Establish minimum context before consequential output. |
| Tactics | Ask 1-3 targeted context questions; build Context Pack Candidate; mark context assumptions. |
| Consultations | Mnemosyne / history; Athena / coherence. |
| Gates | Context sufficiency gate if missing context blocks external output. |
| Limit | Does not invent context. |

### Apollo — clarity qualities

| Quality / facet | Content |
|---|---|
| Sensitivity | Dense answer, no verdict, risk hidden in detail, no next action, unclear recipient. |
| Reflexes | Unclear-summary warning; verdict-missing warning; decision-card missing warning. |
| Orientation | Verdict first; detail second; action card when decision is needed. |
| Tactics | Flash summary; “known / missing / risk / next action”; matrix; priority ordering. |
| Consultations | Athena / nuance; Iris / wording; Hephaestus / structure. |
| Gates | Summary readiness check if summary may be sent externally. |
| Limit | Does not simplify away risk. |

### Chronos — time qualities

| Quality / facet | Content |
|---|---|
| Sensitivity | Date, delay, expiry, document index, source freshness, sequence error, repeated late point. |
| Reflexes | Deadline warning; stale-version warning; temporal-conflict warning; sequence warning. |
| Orientation | Latest applicable version first; dates must be explicit when consequence matters. |
| Tactics | Sort by date; request latest index; distinguish alert delay from OPC pilotage; mark source freshness. |
| Consultations | Mnemosyne / latest known document; Themis / contractual or OPC boundary; Zeus / blocking status. |
| Gates | Freshness gate if obsolete version blocks consequential output. |
| Limit | Does not become OPC or planning authority. |

### Ploutos — financial qualities

| Quality / facet | Content |
|---|---|
| Sensitivity | High cost, quote, invoice, situation, payment request, avenant, budget drift, unsupported price. |
| Reflexes | Cost-risk warning; payment-approval warning; avenant-risk warning. |
| Orientation | Compare with market, CCTP, CCAP, AE, OS, previous situations and actual progress. |
| Tactics | Request breakdown; classify market / TS / hors marché; say “analysis candidate” not “bon à payer”. |
| Consultations | Themis / contract; Athena / evidence; Mnemosyne / prior situations; Zeus / approval ceiling. |
| Gates | Financial review gate; avenant gate; payment gate. |
| Limit | Does not validate accounting, payment or economist judgement. |

## Expression and visibility

Facets express themselves depending on context.

They may remain silent, color the answer, become visible, consult another facet, request a rite or ask Zeus.

Only expressions that change the output should appear in the compact card.

```text
Relevant facet expressions:
Consulted facet links:
Tactic applied:
Rite requested:
Zeus arbitration:
Gate:
```

The first answer must remain short. Detailed role dialogue is second-layer.

## Anti-patterns

```text
Do not treat facets as sub-modules.
Do not reduce facets to jurisdiction fields.
Do not turn roles into autonomous agents.
Do not let every role comment on every request.
Do not use role names as decoration without jurisdiction.
Do not let role consultation become hidden chain-of-thought.
Do not let roles decide outside their limits.
Do not use a reflex to hide a full procedure.
Do not let a tactic become doctrine without review.
```

## Relationship with method taxonomy

This document depends on `METHOD_TAXONOMY.md`.

The key distinction becomes:

```text
Approaches handle work.
Disciplines constrain work.
Strategies choose routes.
Procedures order steps.
Tactics handle local moves.
Roles guard consequence domains.
Jurisdictions define what roles protect.
Facets are role qualities.
Expressions manifest those qualities contextually.
Reflexes are short expressions of a quality when a risky signal appears.
Gates expose decisions.
The architect decides.
```

## Relationship with role-reflex coordination

This document complements `ROLE_REFLEX_COORDINATION.md`.

That document explains how role-owned reflexes may consult facets, request rites and invoke Zeus.

This document defines what each role is made of.

## Relationship with role expression

This document also complements `ROLE_ACTIVATION_MODEL.md`, whose current content should be read as `Architecture Role Expression Model`.

That document governs contextual expression and visibility.

This document governs role qualities.

## Final rule

```text
A role is a guardian with qualities, not a worker.
A facet is a quality, not a button.
A quality may express itself by sensing, warning, orienting, proposing, consulting or asking for a gate.
It must not execute, approve automatically, send, memorize canonically or replace the architect.
```
