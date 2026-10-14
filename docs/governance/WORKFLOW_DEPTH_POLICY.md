# Workflow Depth Policy

Status: candidate — proportional governance and workflow-depth control.
Boundary profile: candidate_support_note.

This document is not canonical doctrine yet.

It does not implement a router, scheduler, queue, agent loop, background worker, automatic triage system, approval engine, memory engine, user interface or runtime behavior.

It defines a candidate policy for keeping Pantheon workflows useful, fast and proportionate.

## Purpose

Pantheon must not become an usine a gaz.

The system should not launch a full Evidence Pack, source search, context retrieval, contract review, financial review and decision gate for every small user request.

The correct posture is proportional governance:

```text
light by default;
escalate when risk requires it;
show the depth reached;
show what was not checked;
block only when necessary.
```

## Core rule

```text
Pantheon starts at the lowest safe depth.
Pantheon escalates only when requested by the user or required by risk.
Pantheon always states the depth used and the limits of the answer.
```

## Depth levels

### Fast

Fast mode is for ordinary, low-consequence requests.

Use when:

```text
quick wording;
small clarification;
first visual impression;
rough classification;
internal draft;
no external action;
no money;
no insurance;
no legal / contractual decision;
no memory write;
no canonical status.
```

Typical checks:

```text
user input only;
current message context;
obvious missing information;
one short candidate answer;
optional clarification request if target is unclear.
```

Allowed output:

```text
quick candidate;
short note;
draft candidate;
visual observation candidate;
question for missing input.
```

Must display:

```text
Depth: Fast.
Not checked: project history / CCTP / CCAP / DTU / insurance / finance unless explicitly checked.
Status: candidate.
```

### Normal

Normal mode is for project-aware review with bounded context.

Use when:

```text
site observation may affect works;
CR update;
project context matters;
existing open point may already exist;
work may be delayed;
minor financial or scope impact;
internal Notion candidate may be prepared;
external message might be prepared but not sent.
```

Typical checks:

```text
project;
phase;
latest CR;
open observations;
lot likely concerned;
recent photos or notes;
recent mails if available;
CCTP excerpt only if directly relevant;
previous status of the same point.
```

Allowed output:

```text
Context Pack Candidate;
Observation Candidate;
CR Line Candidate;
Review Card Candidate;
Draft Mail Candidate;
Notion Write Candidate;
Capability Gap.
```

Must display:

```text
Depth: Normal.
Checked: bounded context list.
Not checked: full history, all CCTPs, CCAP, insurance, DTU unless triggered.
Status: candidate / to verify / blocked.
```

### Deep

Deep mode is for consequential review.

Use when:

```text
payment;
invoice;
quote for extra works;
insurance;
DTU / standard / compliance;
structure;
waterproofing;
fire / accessibility / safety;
contractual responsibility;
client reproach;
formal notice;
external action;
Notion validated write;
Registre Probatoire or memory promotion;
contradictory sources;
large financial impact;
litigation risk.
```

Typical checks:

```text
Task Contract;
Context Pack;
Evidence Pack Candidate;
latest and prior CRs;
open observations;
CCTP / CCAP / AE;
OS / avenants;
quotes / invoices / previous situations;
insurance certificate;
relevant technical sources;
source authority and version;
formal approval path;
User Decision Gate.
```

Allowed output:

```text
Evidence Pack Candidate;
Financial Review Candidate;
Insurance Coverage Candidate;
Normative Source Check Candidate;
Formal Notice Candidate;
User Decision Gate Candidate;
Review Card Candidate;
Capability Gap.
```

Must display:

```text
Depth: Deep.
Checked: source list.
Missing: source gaps.
Action status: blocked unless approved.
Status: candidate / to verify / needs approval / blocked.
```

## Escalation triggers

Escalate from Fast to Normal when:

```text
project history matters;
there may be an existing open point;
photo target is unclear;
CR update is requested;
Notion candidate write is requested;
lot or enterprise attribution matters;
minor delay or coordination risk appears;
user says “verifie”, “compare”, “regarde si deja inscrit”, “mets a jour le CR”.
```

Escalate from Normal to Deep when:

```text
money is involved;
invoice or quote is involved;
insurance is involved;
DTU / normative source is involved;
structural safety is involved;
waterproofing or consequential technical risk is involved;
formal notice is considered;
client reproach or responsibility is involved;
external email may be sent;
validated Notion write is requested;
canonical memory or Registre Probatoire is requested;
source contradiction is material;
approval path is missing.
```

## User depth commands

The user may override the starting depth using natural language.

```text
“rapide” -> Fast
“analyse rapide” -> Fast
“verifie serieusement” -> Normal
“regarde dans le contexte” -> Normal
“analyse complete” -> Deep
“cherche dans les CCTP / CCAP / DTU / assurances” -> Deep
“prepare mais n’envoie pas” -> Normal or Deep depending risk
“valide / envoie / inscris” -> User Decision Gate required
```

If the requested depth is too shallow for the risk, the system must warn and escalate or block:

```text
User asks: “reponds rapidement que c’est valide.”
System result: Fast not allowed; Deep or approval gate required.
```

## Output compactness

Default output must be short.

Recommended compact formats:

### Photo / observation

```text
Depth:
I see:
Doubt:
Confidence:
Context checked:
Action proposed:
Need from user:
```

### Invoice / quote

```text
Depth:
Document:
Amount:
Form:
Progress:
Justification:
Risk:
Action proposed:
```

### Site report finalization

```text
Depth:
New points:
Updated points:
Delayed points:
Closed candidate:
Clarifications:
Draft CR status:
Mail status:
```

### Client reproach / responsibility

```text
Depth:
Allegation:
Facts found:
Missing evidence:
Risk:
Safe wording:
Forbidden wording:
Next action:
```

Detailed Evidence Pack should be available behind a second layer, not forced into the first answer.

## Progressive disclosure

The exposure surface should show:

```text
summary first;
detail on demand;
sources on demand;
contradictions on demand;
User Decision Gate only when required.
```

A future cockpit may expose this as:

```text
Card -> Details -> Evidence -> Gate
```

## Stop conditions

The system must stop or ask for input instead of deepening endlessly when:

```text
target is unclear;
project is unclear;
photo is insufficient;
source is absent;
recipient is unclear;
approval is missing;
write target is ambiguous;
version status is unknown for consequential source;
runtime or connector is unavailable;
analysis depth requested conflicts with risk.
```

A stop condition should be short:

```text
I can give a fast candidate, but I cannot conclude without X.
```

## Learning loop interaction

Workflow learning must also be proportional.

Do not create a learning candidate for every correction.

Create one when:

```text
the same correction repeats;
a risky output was avoided;
a workflow step is missing;
a user correction reveals a reusable rule;
a status distinction is needed;
a common friction costs time.
```

Do not promote the learning automatically.

```text
correction -> pattern candidate -> review -> strategy candidate -> validation -> baseline
```

## Anti-usine-a-gaz rules

```text
Do not fetch everything when one source is enough.
Do not run Deep when Fast is safe.
Do not produce a long Evidence Pack in the first response unless requested or required.
Do not ask questions when a safe candidate can be produced with clear limits.
Do not continue researching when a decisive gap already blocks the task.
Do not turn every candidate into a Notion write.
Do not turn every observation into a formal warning.
Do not turn every delay into a formal notice candidate.
Do not turn every correction into doctrine.
```

## Final rule

```text
Fast by default.
Normal when context matters.
Deep when consequence matters.
Always visible.
Always bounded.
Always candidate until approved.
```
