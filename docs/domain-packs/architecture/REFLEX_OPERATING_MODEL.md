# Architecture Method and Reflex Operating Model

Status: candidate — operating model for architecture-domain methods and narrow reflexes.
Boundary profile: candidate_support_note.

This document is not canonical doctrine yet.

It does not implement a runtime, agent router, workflow engine, scheduler, queue, UI, connector, memory engine, approval engine, document generator or automatic action system.

It defines a compact operating model so architecture-domain method objects remain composable, bounded and usable without becoming an usine a gaz.

Filename note: this document keeps its historical filename for now. The term `reflex` is narrowed by `METHOD_TAXONOMY.md` and no longer means every reusable architecture pattern.

## Purpose

Architecture work can multiply into many named paths:

```text
CCTP from plan;
Cerfa from project data;
site report finalization;
photo chantier doubt;
invoice / quote review;
lot and insurance review;
material choice;
client response;
DTU / source check;
Notion observation candidate.
```

The purpose of this model is to reduce them to a shared operating grammar without calling all of them reflexes.

```text
Fewer full workflows.
More reusable method objects.
One decision grammar.
Compact outputs by default.
Deeper proof only when consequence requires it.
Reflex only when a situation requires cadrage or rappel.
```

## Core rule

```text
Every architecture request is handled as:
Request -> Depth -> Context -> Method Objects -> Candidate -> Gate.
```

Where `Method Objects` may include:

```text
Approach;
Discipline;
Strategy;
Procedure;
Tactic;
Reflex.
```

This shape is conceptual only. It is not a runtime sequence owned by Pantheon.

## Six universal objects

### 1. Request

What the user asks.

Examples:

```text
summarize this document;
prepare a CCTP;
finish this site report;
check this invoice;
choose a facade material;
reply to this client;
write this into Notion;
```

The request must identify, or ask for, the expected output.

### 2. Depth

Depth follows `WORKFLOW_DEPTH_POLICY.md`:

```text
Fast    -> short candidate, minimal checks;
Normal  -> bounded project context;
Deep    -> consequential review with Evidence Pack Candidate and gates.
```

Depth must be visible in the answer.

### 3. Context

Context is not the whole dossier by default.

Minimum useful context may include:

```text
project;
phase;
mission scope;
latest decision;
latest CR;
open observations;
lot / enterprise;
received document;
known constraints;
missing information;
```

Context stays candidate until source status is qualified.

### 4. Method Objects

Method objects are reusable governance constructs used to handle the request.

Definitions follow `METHOD_TAXONOMY.md`.

```text
Approach   -> reusable governed handling of a recurring situation.
Discipline -> standing cross-cutting rule.
Strategy   -> conditional choice of route or priority.
Procedure  -> ordered sequence for output or gate.
Tactic     -> local move or wording choice.
Reflex     -> triggered cadrage / rappel / warning when something surfaces.
```

A reflex is narrow and interruptive. It is not a complete deliverable path.

### 5. Candidate

The output remains candidate until the human validates it.

Examples:

```text
Summary Candidate;
CCTP Draft Candidate;
CR Draft Candidate;
Material Choice Candidate;
Invoice Review Candidate;
Mission Boundary Reply Candidate;
Notion Observation Candidate;
```

### 6. Gate

A gate is required when the candidate could create:

```text
external effect;
validated Notion / memory state;
canonical project status;
financial approval;
contractual acceptance;
technical validation;
mission extension;
responsibility implication.
```

Preparing is not sending. Drafting is not validation.

## User-facing intents

The user should not need to name method objects.

Use four simple intents:

```text
Answer   -> explain, summarize, advise internally;
Verify   -> check sources, status, risk, missing information;
Produce  -> prepare a document, CR, CCTP, note, table, mail candidate;
Act      -> write, send, notify, update, validate, file.
```

`Act` always triggers boundary classification before any handoff.

## Method object families

### Approaches

Approaches are main reusable professional paths:

```text
Document Summary Approach;
Plan Reading Approach;
CCTP from Plan Approach;
Cerfa Fill Approach;
Site Report Finalization Approach;
Photo Chantier Observation Approach;
Invoice / Quote Review Approach;
Lot Scope and Insurance Review Approach;
Material Choice Approach;
Client Response Approach;
DTU / Local Source Check Approach;
```

### Disciplines

Disciplines constrain many approaches:

```text
Workflow Depth Discipline;
Missing Information Discipline;
Evidence Discipline;
Assumption Ledger Discipline;
Mission / Responsibility Boundary Discipline;
External Action Discipline;
Memory / Notion Write Discipline;
Source Version Discipline;
```

### Strategies

Strategies choose routes or priorities:

```text
Fast / Normal / Deep selection;
local project sources before external web;
last known decision first;
latest CR first;
ask before infer;
client-readable versus internal technical summary;
formal notice escalation path;
```

### Procedures

Procedures order steps:

```text
form filling resolution loop;
site report finalization sequence;
external email approval path;
Notion write candidate review;
insurance certificate review sequence;
```

### Tactics

Tactics handle local moves:

```text
ask for another photo angle;
mark a CR line as maintained instead of duplicating it;
offer cannot-pronounce versus limited-orientation reply;
insert limitation wording;
ask for BET confirmation;
```

### Reflexes

Reflexes are triggered cadrage / rappel signals:

```text
mission boundary warning;
responsibility risk warning;
missing blocking information warning;
external action warning;
source-staleness warning;
assumption-not-fact warning;
wrong-lot suspicion warning;
support-acceptance caution;
formal-notice caution;
```

A reflex activates when something emerges during project progress, during production of a deliverable, or while a situation is being handled and requires immediate professional caution.

### Role-owned reflexes and coordination

A role is not a reflex.

A role guards a consequence domain. A role may own reflexes that fire when its domain is threatened.

```text
Role -> consequence domain.
Role-owned reflex -> triggered warning from that domain.
```

A role-owned reflex may cause a bounded coordination move:

```text
consult another role;
request a rite;
invoke Zeus for status arbitration;
apply a tactic;
open a gate;
return to the main approach.
```

This coordination is governed by `ROLE_REFLEX_COORDINATION.md`.

Examples:

```text
Zeus -> approval / status / arbitration.
  Reflexes: approval-ceiling warning, status-promotion caution, external-action arbitration.

Athena -> coherence / proof / reasoning.
  Reflexes: contradiction warning, weak-proof warning, overconfident-conclusion warning.

Themis -> scope / mission / responsibility.
  Reflexes: mission-boundary warning, responsibility warning, forbidden-wording warning.

Mnemosyne -> memory / recall / register.
  Reflexes: stale-recall warning, duplicate-memory warning, unvalidated-memory-write warning.

Hermes -> handoff / execution boundary.
  Reflexes: execution-scope warning, connector-risk warning, handoff-boundary warning.

Hephaestus -> production / deliverable structure.
  Reflexes: missing-template warning, production-readiness warning, deliverable-structure warning.

Iris -> expression / external wording.
  Reflexes: tone-risk warning, ambiguity warning, expression-without-substance-change warning.
```

The interface may surface the role behind a reflex when useful, but the output must still classify the actual method object:

```text
Role: Themis
Reflex: mission-boundary warning
Discipline: mission / responsibility boundary
Consulted role: Iris if external wording matters
Tactic: limitation wording
Gate: user validation before external email
```

## Default answer card

Every response should start with a compact card when the task is project-facing.

```text
Depth:
Status:
Request understood:
Method objects used:
Triggered role reflexes:
Consulted roles:
Rite requested:
Zeus arbitration:
What I can say now:
What is missing:
Risk:
Next action:
Gate:
```

Detailed evidence, contradictions, assumptions and source tables should remain second-layer unless Deep depth is required.

## Method object selection rule

Select the fewest method objects that can safely answer the request.

Examples:

```text
User: “résume ce devis”
Method objects: Document Summary Approach + Invoice / Quote Review Approach if money risk is present + Missing Information Discipline.

User: “on met quoi en facade ?”
Method objects: Material Choice Approach + last-known-decision-first Strategy + Missing Information Discipline. Themis mission-boundary reflex only if external output or responsibility risk is implied.

User: “fais le CR chantier”
Method objects: Site Report Finalization Approach + site-report Procedure + Missing Information Discipline + Mission Boundary Discipline + External Action Gate.
Role-owned reflexes: Themis if a line may imply validation / OPC / responsibility; Mnemosyne if a point duplicates an existing memory.

User: “réponds à l’entreprise”
Method objects: Client / Enterprise Response Approach + Mission Boundary Reflex if scope risk appears + External Action Gate.
Role-owned reflexes: Themis + Iris.
```

Do not activate all known method objects by default.

Do not call an Approach a Reflex unless it is only a triggered warning / cadrage / rappel.

## Escalation rule

Escalate only when:

```text
risk trigger appears;
user asks for deeper verification;
source contradiction matters;
external effect is requested;
memory / Notion validated write is requested;
mission boundary is unclear;
financial / contractual / insurance / regulatory / technical consequence appears.
```

Otherwise, keep the answer short.

## Stop rule

Stop instead of over-processing when:

```text
the project is unknown;
the mission scope is unknown and consequence is high;
the source is unreadable;
the target object is unclear;
the official version is unknown for a consequential source;
the user asks for an external action but approval is missing;
a decisive source gap already blocks conclusion.
```

A stop is not a failure. It is a safe status.

## Mission boundary as cross-cutting discipline and reflex

Mission / responsibility boundary is a standing discipline.

It becomes a reflex when a concrete issue surfaces and requires immediate warning.

Every candidate that could be read externally must pass the mission / responsibility check.

```text
Can this be read as validation?
Can this be read as instruction?
Can this widen our mission?
Can this imply technical, financial, planning, insurance or regulatory responsibility?
```

If yes, the output must include limitation wording or be blocked pending human decision.

## Compactness rule

The first answer must be usable in less than one minute.

Recommended first layer:

```text
1. answer / verdict candidate;
2. missing information;
3. risk;
4. next action;
5. gate if needed.
```

Do not present a full Evidence Pack unless the user asks or Deep depth requires it.

## Learning rule

Repeated user corrections may become a Learning Candidate.

They must not automatically become doctrine.

```text
correction -> pattern candidate -> strategy candidate -> reviewed adoption -> baseline.
```

## Final rule

```text
Pantheon does not replace the architect.
It reads, qualifies, links, alerts, prepares and blocks unsafe status transitions.
Approaches handle work.
Disciplines constrain work.
Strategies choose routes.
Procedures order steps.
Tactics handle local moves.
Roles guard consequence domains.
Reflexes interrupt with necessary cadrage.
Some reflexes are owned by roles.
Role-owned reflexes may consult roles, request rites or invoke Zeus.
The architect decides.
```
