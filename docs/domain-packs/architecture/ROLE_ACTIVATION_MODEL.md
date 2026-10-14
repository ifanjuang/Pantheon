# Architecture Role Expression Model

Status: candidate — architecture-domain model for contextual expression of role qualities / facets.
Boundary profile: candidate_support_note.

Filename note: this document keeps its historical filename for now: `ROLE_ACTIVATION_MODEL.md`.

Terminology correction: `activation` is only a visibility shortcut used in earlier drafts. Roles are not switched on or off. Role facets are permanent qualities whose expression varies by context.

Additional terminology correction: a facet is not merely a jurisdiction field. `mission`, `proof`, `memory`, `cost`, `date` or `wording` are often protected fields. The facets are the qualities by which a role perceives, warns, orients, proposes tactics, consults and limits itself around those fields.

This document is not canonical doctrine yet.

It does not implement agents, role executors, role routing, multi-agent loops, workflow runtime, scheduler, queue, message bus, UI, approval engine, memory engine, rite runner, sender, checker, legal review or professional validation.

It defines how architecture-domain role qualities express themselves freely but boundedly, without making every role visible on every request.

## Purpose

The architecture role model must avoid three failures:

```text
1. mechanical activation:
   roles behave like switched modules or scoring functions;

2. uncontrolled expression:
   roles comment freely, expand the response and create noise or hidden authority;

3. wrong meaning of facet:
   facets are confused with sub-domains instead of being understood as role qualities.
```

The corrected model is:

```text
roles are permanent guardians;
jurisdictions are what roles protect;
facets are the qualities that let roles protect their jurisdictions;
context changes how strongly each quality expresses itself;
expression may color, warn, consult, propose, request or block unsafe transitions;
expression must not execute, approve, send, memorize canonically or replace the architect.
```

## Core rule

```text
A role is not activated as a module.
A role exists as a standing guardian.
Its qualities / facets are always present.
The context makes some qualities remain silent, color the answer, become visible, consult another quality, request a rite or ask Zeus for arbitration.
```

## Expression, not action

A role may judge whether one of its qualities should express itself.

A role may not perform consequential action by itself.

Allowed:

```text
color the analysis;
warn;
request evidence;
request clarification;
propose a tactic;
consult another role quality;
request a rite;
ask Zeus for status arbitration;
request or expose a gate;
```

Forbidden:

```text
validate truth;
approve;
send;
file;
commit externally;
promote memory;
accept payment;
approve an avenant;
extend mission;
replace professional judgement;
```

## Role circles as background posture

Role circles remain useful as a visibility and attention model, not as activation switches.

### Core circle

The core circle is permanently present in the background and usually silent.

| Role | Standing jurisdiction | Qualities that may express themselves |
|---|---|---|
| Hestia | Project, phase, mission context, dossier perimeter, baseline situation. | Context sensitivity; no-invention prudence; targeted-question tactic. |
| Athena | Coherence, evidence, contradictions, reasoning, certainty. | Proof sensitivity; contradiction reflex; source-first orientation; overconfidence threshold. |
| Themis | Mission, scope, responsibility, contract, professional boundary. | Responsibility sensitivity; mission-boundary reflex; boundary-first orientation; forbidden-wording prudence. |
| Mnemosyne | Memory, history, prior decisions, previous CR, duplicates, closure. | Recall sensitivity; duplicate reflex; latest-known orientation; memory-promotion prudence. |
| Zeus | Status, arbitration, approval ceiling, gate, promotion. | Threshold sensitivity; approval reflex; gate orientation; blocking tactic. |

### Conditional circle

These roles have permanent qualities, but their expression usually stays quiet unless the protected field appears.

| Role | Standing jurisdiction | Qualities that may express themselves |
|---|---|---|
| Hermes | Handoff, external action, connectors, execution boundary, transmission, trace. | Action sensitivity; prepare-not-send orientation; connector prudence; handoff-boundary reflex. |
| Chronos | Date, delay, index, version, expiry, obsolescence, sequence. | Time sensitivity; freshness reflex; latest-version orientation; OPC-boundary prudence. |
| Ploutos | Cost, budget, quote, invoice, situation, payment, avenant, financial exposure. | Cost sensitivity; payment reflex; market-comparison orientation; no-bon-a-payer prudence. |

### Production circle

These roles express qualities when an output must be shaped.

| Role | Standing jurisdiction | Qualities that may express themselves |
|---|---|---|
| Hephaestus | Deliverable structure, template, readiness, completeness, format. | Structure sensitivity; missing-template reflex; production orientation; completeness prudence. |
| Iris | External wording, tone, ambiguity, recipient effect, implicit admission. | Ambiguity sensitivity; safer-wording orientation; reformulation tactic; substance-change prudence. |
| Apollo | Clarity, synthesis, verdict, hierarchy, pedagogy, decision readability. | Clarity sensitivity; verdict reflex; summary-first orientation; risk-preservation prudence. |

## Modes of expression

This model does not require fixed scoring levels.

Output may describe expression qualitatively when useful.

| Mode | Meaning | Visibility |
|---|---|---|
| Silent | The quality remains inherent but does not affect this answer. | Not shown. |
| Coloring | The quality subtly influences caution, wording or structure. | Usually not shown. |
| Visible | The quality produces a warning, reservation, missing source or tactic. | Show briefly. |
| Consultative | The quality needs another quality's view to avoid a bad answer. | Show only if it changes output. |
| Arbitral | The quality requires Zeus or a gate because status or approval ceiling is involved. | Show clearly. |

These modes are descriptive, not a numerical scoring system.

## Expression threshold

A quality should be visible only if its expression changes at least one of:

```text
status;
risk;
wording;
evidence requirement;
missing information;
next action;
consultation;
rite request;
Zeus arbitration;
gate;
```

If a quality only comments, decorates or restates the obvious, it remains silent.

## Self-judgement rule

Each role may judge the expression of its own qualities.

This means:

```text
Hestia judges whether context uncertainty matters;
Athena judges whether proof/coherence affects the claim;
Themis judges whether mission/responsibility affects the wording or status;
Mnemosyne judges whether memory/history changes the handling;
Hermes judges whether a handoff or external effect is implied;
Chronos judges whether time/version/delay matters;
Ploutos judges whether money/payment/avenant exposure matters;
Hephaestus judges whether production structure is insufficient;
Iris judges whether wording creates external ambiguity;
Apollo judges whether the output is unreadable or lacks a decision card;
Zeus judges whether status or approval ceiling must be arbitrated.
```

Self-judgement is bounded by the role's jurisdiction and limits.

It is not self-authorization.

## Quality-to-quality consultation

Consultation should happen between qualities, not whole roles.

Good:

```text
Themis / responsibility sensitivity consults Athena / proof sensitivity.
Iris / external wording prudence consults Themis / responsibility sensitivity.
Ploutos / payment reflex consults Themis / contract boundary sensitivity.
Chronos / version freshness consults Mnemosyne / latest-known orientation.
Hermes / external-action sensitivity consults Zeus / gate orientation.
```

Too broad:

```text
Themis consults Athena.
All roles review the request.
The gods discuss until they agree.
```

A consultation is legitimate only if the consulted quality may change:

```text
status;
proof requirement;
formulation;
risk classification;
next action;
gate;
```

Consultation should normally remain limited to 1-3 quality links.

## Natural expression examples

### Hestia — context qualities

Protected fields:

```text
project;
phase;
mission context;
dossier perimeter;
location;
situation baseline;
```

Qualities:

```text
context sensitivity;
wrong-dossier reflex;
context-first orientation;
targeted-question tactic;
no-invention prudence;
```

### Athena — proof qualities

Protected fields:

```text
proof;
coherence;
contradiction;
hypothesis;
certainty;
method of verification;
```

Qualities:

```text
proof sensitivity;
contradiction reflex;
source-first orientation;
hypothesis-marking tactic;
overconfidence threshold;
```

### Themis — boundary qualities

Protected fields:

```text
mission;
responsibility;
contract;
perimeter;
forbidden wording;
mission complement;
```

Qualities:

```text
responsibility sensitivity;
mission-boundary reflex;
boundary-first orientation;
limitation-wording tactic;
forbidden-wording prudence;
```

### Mnemosyne — memory qualities

Protected fields:

```text
history;
previous decision;
previous CR;
duplicate point;
stale memory;
candidate memory;
closure;
```

Qualities:

```text
recall sensitivity;
duplicate reflex;
latest-known orientation;
maintain-not-duplicate tactic;
memory-promotion prudence;
```

### Hermes — handoff qualities

Protected fields:

```text
external action;
handoff;
connector;
execution boundary;
transmission;
trace;
```

Qualities:

```text
action sensitivity;
handoff-boundary reflex;
prepare-not-send orientation;
effect-classification tactic;
connector prudence;
```

### Chronos — time qualities

Protected fields:

```text
date;
delay;
index;
version;
expiry;
obsolescence;
sequence;
```

Qualities:

```text
time sensitivity;
stale-version reflex;
latest-version orientation;
date-ordering tactic;
OPC-boundary prudence;
```

### Ploutos — financial qualities

Protected fields:

```text
cost;
budget;
quote;
invoice;
situation;
payment;
avenant;
financial exposure;
```

Qualities:

```text
cost sensitivity;
payment reflex;
market-comparison orientation;
breakdown-request tactic;
no-bon-a-payer prudence;
```

### Hephaestus — production qualities

Protected fields:

```text
deliverable structure;
template;
completeness;
granularity;
format;
readiness;
```

Qualities:

```text
structure sensitivity;
missing-template reflex;
production orientation;
skeleton tactic;
completeness prudence;
```

### Iris — wording qualities

Protected fields:

```text
tone;
ambiguity;
external wording;
recipient effect;
implicit admission;
readability;
```

Qualities:

```text
ambiguity sensitivity;
tone reflex;
safer-wording orientation;
reformulation tactic;
substance-change prudence;
```

### Apollo — clarity qualities

Protected fields:

```text
summary;
verdict;
hierarchy;
decision readability;
pedagogy;
action card;
```

Qualities:

```text
clarity sensitivity;
verdict-missing reflex;
summary-first orientation;
action-card tactic;
risk-preservation prudence;
```

### Zeus — threshold qualities

Protected fields:

```text
status;
approval ceiling;
gate;
arbitration;
promotion;
blocking;
```

Qualities:

```text
threshold sensitivity;
approval-ceiling reflex;
gate orientation;
blocking tactic;
no-auto-approval prudence;
```

## Simple operational mechanism

No scoring engine is required.

Use this reasoning discipline:

```text
1. Identify the main approach.
2. Identify relevant protected fields.
3. Let roles judge which of their qualities materially affect the answer.
4. Keep silent qualities invisible.
5. Let expressed qualities color, warn, propose, consult, request or escalate.
6. If status, approval, memory or action is touched, ask Zeus or open a gate.
7. Return to the main approach and produce a candidate output.
```

This is a reasoning discipline, not a runtime loop.

## Minimal response trace

Default first layer:

```text
Status:
Relevant quality expressions:
Risk:
Next action:
Gate:
```

Example:

```text
Status: candidate, external reply not authorized yet.
Relevant quality expressions:
- Themis / responsibility sensitivity: warning — possible prescription outside mission.
- Iris / safer-wording orientation: tactic — reformulate as clarification request.
- Hermes / external-action sensitivity: gate — email remains draft.
Risk: external answer could imply technical validation.
Next action: prepare limited reply candidate.
Gate: user validation before sending.
```

If no quality expression materially changes the response:

```text
Status:
Risk:
Next action:
```

Do not force a role trace.

## Tolerance and freedom

The expression model gives freedom inside bounds.

Free or guided:

```text
order of checks;
level of detail;
choice of table, note, paragraph or card;
number and wording of questions;
recipient-appropriate tone;
which silent qualities stay implicit;
which tactic best fits the situation;
```

Strict:

```text
truth validation;
canonical memory;
approval;
external action;
financial acceptance;
mission extension;
responsibility admission;
technical validation;
```

## Anti-patterns

```text
Do not make roles switch on/off as modules.
Do not confuse protected fields with role qualities.
Do not force numerical quality levels.
Do not let every role express itself.
Do not let expression become hidden chain-of-thought.
Do not let a quality act outside its role limit.
Do not let a visible warning become approval.
Do not let Zeus approve automatically.
Do not let a tactic become doctrine without review.
```

## Relationship with existing documents

This document depends on:

```text
ROLE_FACETS.md
ROLE_REFLEX_COORDINATION.md
METHOD_TAXONOMY.md
WORKFLOW_DEPTH_POLICY.md
```

It corrects the earlier mechanical reading of `ROLE_ACTIVATION_MODEL.md` while keeping the historical filename for compatibility.

It should be treated as the current interpretation of that file.

## Final rule

```text
A role is a standing guardian.
A jurisdiction is what the role protects.
A facet is a role quality.
A context makes qualities express themselves more or less.
A quality may color, warn, propose, consult, request a rite or ask Zeus.
It may not validate, send, memorize canonically, approve or replace the architect.
Zeus governs thresholds.
The human decides.
```
