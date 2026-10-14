# Governed Method Standard

Status: active support doctrine — standard methodological gymnastics for governed professional work. Repository state: documented non-implemented.

This document defines a reusable method discipline for professional work governed by Pantheon Next.

It does not implement a workflow engine, agent, scheduler, queue, approval engine, memory engine, OpenWebUI plugin, Hermes skill, connector, runtime, UI renderer or external action.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: optional compatible runtime clients expose runtime interaction only, Hermes/the external runtime executes admitted work as PEP, Pantheon Cockpit projects governed state, and Pantheon policy/governance remains the bounded PDP authority.

## Purpose

Pantheon Next must not become a catalogue of case-by-case procedures.

Professional situations vary too much:

```text
architecture;
regulatory analysis;
ABF exchange;
CCTP drafting;
DCE review;
construction-site tension;
Revit model interaction;
client communication;
form filling;
proof review;
memory proposal.
```

Trying to encode every case as a separate workflow would make Pantheon heavy, brittle and misleading.

The purpose of this document is therefore narrower and more durable:

```text
define the common methodological movements that every governed professional output should pass through,
without turning those movements into an automatic runtime.
```

The standard is a thinking discipline, not an execution plan.

## Core doctrine

```text
Pantheon does not do the work.
Pantheon defines the discipline of movement, status, evidence, memory and gates.
Execution tools may perform tasks under Task Contract.
Every output remains candidate until status, evidence and approval allow use.
The human decides.
```

In French project language:

```text
Pantheon ne fait pas le travail.
Pantheon impose la gymnastique : cadrer, admettre, qualifier, composer, produire candidat, éprouver, statuer.
L'outil exécute.
La preuve contraint.
Le statut limite l'usage.
L'humain décide.
```

## What this is

The Governed Method Standard is a tool-agnostic professional method frame.

It defines:

```text
methodological movements;
entry conditions;
output conditions;
stop conditions;
return loops;
status vocabulary;
evidence expectations;
memory discipline;
external-action discipline;
projection into domain packs.
```

It may be used by a domain pack, cockpit page, Hermes profile, prompt, template, review note or adapter document.

## What this is not

This standard is not:

```text
a runtime workflow;
a step runner;
a scheduler;
a queue;
a checklist for every professional case;
a professional authority;
a source validator;
an approval engine;
a memory promotion engine;
a document sender;
a Revit action controller;
a connector permission system.
```

The method lives in Pantheon as governance discipline.

Execution, display, preparation, drafting, extraction, connector calls and model edits remain outside Pantheon unless a separately approved implementation artifact exists.

## The seven movements

The standard method is deliberately compact.

```text
1. Frame
2. Admit
3. Qualify
4. Compose
5. Produce Candidate
6. Test
7. Status

Then: Decide / Transmit / Memorize / Close
```

French shorthand:

```text
Cadrer
-> Admettre
-> Qualifier
-> Composer
-> Produire candidat
-> Éprouver
-> Statuer
-> Décider / Transmettre / Mémoriser / Fermer
```

These are movements, not mandatory linear stages. A situation may loop backward when a source is missing, a contradiction appears, a scope shifts, or a human decision refuses the candidate.

## Movement 1 — Frame

### Purpose

Do not start by answering.

First determine what the request is, what it could affect and whether it is inside the professional perimeter.

### Guiding question

```text
What is being asked, what effect is expected, and what could go wrong if we answer or act too quickly?
```

### Inputs

```text
user request;
message;
email;
conversation fragment;
project context;
selection in a tool;
model state;
document reference;
implicit intention.
```

### Required distinctions

```text
answering vs acting;
explaining vs validating;
drafting vs sending;
preparing vs approving;
reading vs proving;
remembering vs canonizing;
modeling candidate vs modifying a production model.
```

### Possible outputs

```text
request framed;
request ambiguous;
request out of scope;
request requires reformulation;
request requires source admission;
request requires human gate before continuation;
request blocked.
```

### Stop conditions

```text
unclear user intent;
unclear professional perimeter;
unclear requested effect;
possible external action without approval path;
possible canonical memory effect without memory rule;
possible professional validation without authority.
```

## Movement 2 — Admit

### Purpose

Do not treat received material as reliable by default.

A mail, PDF, photo, screenshot, model, note, export, connector item, memory recall or user statement enters the working perimeter only after being admitted with visible limits.

### Guiding question

```text
What is actually available, dated, usable, absent, partial or contradictory?
```

### Inputs

```text
files;
messages;
photos;
plans;
models;
exports;
links;
retrieved excerpts;
user recollections;
connector items;
previous project memory.
```

### Minimum inventory

```text
received items;
referenced but absent items;
source type;
origin;
date;
version;
scope;
known limits;
unknowns;
contradictions;
reviewable perimeter;
non-reviewable perimeter.
```

### Possible outputs

```text
corpus admitted;
corpus partial;
corpus contradictory;
corpus not usable;
source absent;
source stale;
source requires confirmation;
perimeter to clarify.
```

### Stop conditions

```text
essential source absent;
source date unknown when date matters;
version conflict;
contradiction not arbitrated;
source cannot be read;
source authority unclear;
professional perimeter absent.
```

### Memory rule

```text
An admitted item is not canonical memory.
```

### External-action rule

```text
No external action may rely on a merely admitted corpus without later testing and gate.
```

## Movement 3 — Qualify

### Purpose

Classify what is being used.

Available information must not be confused with valid evidence.

### Guiding question

```text
What kind of thing is each item, and what authority may it have?
```

### Useful source classes

```text
official source;
project source;
client statement;
contractual source;
professional source;
regulatory source;
model state;
trace;
user memory;
runtime output;
hypothesis;
evidence candidate;
validated evidence;
contradiction;
unknown.
```

### Possible outputs

```text
sources classified;
confidence level visible;
uncertainties visible;
contradictions visible;
evidence expectations identified;
source authority bounded;
source not admissible for the requested use.
```

### Stop conditions

```text
one source is treated as more authoritative than it is;
runtime trace is treated as proof;
retrieval is treated as evidence;
memory recall is treated as verified fact;
user statement is treated as official record;
source conflict is hidden.
```

## Movement 4 — Compose

### Purpose

Professional work often contains mixed tensions.

Do not treat a composed situation as a simple question.

### Guiding question

```text
Which subjects, constraints, dependencies and risks are actually entangled here?
```

### Composition operations

```text
decompose the situation;
name distinct subjects;
identify dependencies;
identify tensions;
cross sources;
compare constraints;
separate facts, interpretations and recommendations;
mark risk families;
form hypotheses as candidates.
```

### Possible outputs

```text
problem decomposed;
subjects separated;
dependencies visible;
tensions visible;
risk families visible;
hypotheses candidate;
point blocked;
point to arbitrate;
route to production candidate.
```

### Stop conditions

```text
professional domains are mixed without separation;
important constraint omitted;
responsibility implication hidden;
contradiction unresolved;
risk family ignored;
output would overstate certainty.
```

## Movement 5 — Produce Candidate

### Purpose

Only produce after the situation has been framed, admitted, qualified and composed enough for the requested depth.

The output is useful, but still not final by default.

### Guiding question

```text
What can be produced without lying about its status?
```

### Candidate output types

```text
answer candidate;
analysis candidate;
note candidate;
email candidate;
notice candidate;
option candidate;
method candidate;
form-fill candidate;
modeling candidate;
Revit action candidate;
Evidence Pack Candidate;
Result Candidate;
Outcome Observation Candidate.
```

### Output rule

Every output should be able to answer:

```text
1. What is it?
2. What does it rely on?
3. What may be done with it?
```

### Possible outputs

```text
draft candidate;
analysis candidate;
option candidate;
action prepared;
evidence candidate;
not transmissible;
ready for review;
ready for testing;
blocked before production.
```

### Stop conditions

```text
output would look final without proof;
output would imply validation;
output would authorize action;
output would alter memory;
output would hide limits;
output would collapse alternatives too early.
```

## Movement 6 — Test

### Purpose

Before use, test the candidate against consequence.

This is where Pantheon asks whether the output can create false truth, bad memory, unapproved external effect, illegitimate scope expansion or unauthorized action.

### Guiding question

```text
What can go wrong if this candidate is used?
```

### Required tests

```text
truth risk;
evidence risk;
memory risk;
scope risk;
approval risk;
external-action risk;
professional-responsibility risk;
tool/runtime trust risk;
source sufficiency risk;
reversibility risk.
```

### Possible outputs

```text
usable with stated limits;
usable only after review;
requires more evidence;
requires human arbitration;
requires approval gate;
blocked;
refused;
return to Frame;
return to Admit;
return to Qualify;
return to Compose.
```

### Stop conditions

```text
false truth risk not bounded;
external action not approved;
source insufficient;
proof absent;
memory status unclear;
scope changed;
professional authority missing;
runtime completed but task status not validated.
```

## Movement 7 — Status

### Purpose

A candidate without status is dangerous.

The output must be explicitly marked so it is not reused, transmitted, memorized or acted upon as more authoritative than it is.

### Guiding question

```text
What is the status of this result, and what is its allowed use?
```

### Status vocabulary

```text
candidate;
to verify;
to complete;
to arbitrate;
blocked;
refused;
validated;
transmissible;
not transmissible;
authorized for external action;
not authorized for external action;
memory candidate;
validated memory;
obsolete.
```

### Possible outputs

```text
status explicit;
allowed use explicit;
proof attached or proof gap visible;
approval level identified;
next action visible;
human gate opened;
item closed.
```

### Stop conditions

```text
status absent;
allowed use unclear;
proof gap hidden;
approval path unclear;
external-action status unclear;
memory rule absent.
```

## Final effects — Decide / Transmit / Memorize / Close

The seven movements produce governed candidates and explicit statuses.

They do not themselves authorize final effects.

### Decide

The human accepts, refuses, modifies, escalates or arbitrates.

```text
The system may prepare the decision surface.
The human decides.
```

### Transmit

Sending, publishing, depositing, signing, synchronizing, saving, deleting, uploading, filing, paying or modifying an external system requires an external-action gate when consequential.

```text
Prepared is not sent.
Drafted is not transmitted.
Runtime-ready is not approved.
```

### Memorize

A useful trace or candidate may support future work, but it is not canonical memory by default.

```text
Trace is not memory.
Recall is not proof.
Memory candidate is not validated memory.
```

### Close

Closing is a governed result.

```text
archive;
reject;
mark obsolete;
record refusal;
record no action;
record not applicable.
```

Closing prevents stale candidates from remaining silently alive.

## Return loops

The method is not a linear workflow.

Normal loops include:

```text
Test finds missing source -> return to Admit.
Qualify finds contradiction -> return to Admit or Frame.
Compose finds mixed requests -> return to Frame.
Produce Candidate exposes risk -> return to Compose.
Status is to arbitrate -> human decision gate.
Decision refuses -> produce revised candidate or Close.
Transmission blocked -> return to Test or Status.
Memory refused -> Close or keep trace only.
```

Return loops are not errors. They are the visible sign that the method is working.

## Conditions of passage

A movement may pass forward only when its output is explicit enough for the next movement.

Minimum passage conditions:

| From | To | Condition |
|---|---|---|
| Frame | Admit | The request and expected effect are sufficiently understood. |
| Admit | Qualify | The received and missing corpus is inventoried. |
| Qualify | Compose | Source classes, confidence and contradictions are visible. |
| Compose | Produce Candidate | The problem is decomposed enough for the requested output. |
| Produce Candidate | Test | The candidate output states what it is and what it relies on. |
| Test | Status | Consequence risks have been checked or explicitly left open. |
| Status | Decide / Transmit / Memorize / Close | Allowed use and required gate are explicit. |

If a condition fails, the correct movement is not to guess. It is to stop, mark the gap, or loop back.

## Standard output contract

Any governed output should include or imply:

```text
output_type;
status;
scope;
source_basis;
evidence_basis;
known_limits;
risk_flags;
allowed_use;
forbidden_use;
required_gate;
next_action;
memory_rule.
```

This is a method-level contract, not an executable schema.

A future schema, if any, must live under `schemas/` and requires explicit protected-path approval.

## Relationship to Task Contract

This method does not replace the Task Contract.

It explains the discipline before, during and after task execution.

```text
Governed Method Standard -> how to think and qualify the work.
Task Contract -> what a tool/runtime is asked to do.
Result Candidate -> what the runtime returns.
Evidence Pack Candidate -> what supports the candidate.
Gate -> whether and how the candidate may be used.
```

## Relationship to domain packs

Domain packs specialize this standard without replacing it.

A domain pack may define:

```text
profession-specific vocabulary;
source classes;
typical risk families;
professional stop conditions;
expected evidence;
output status names;
review angles;
transmission gates;
memory rules;
templates.
```

A domain pack must not become a case-by-case procedure catalogue.

It should apply the same movements to a professional field.

Example for architecture:

```text
Frame -> identify mission, phase, client intent, requested effect.
Admit -> inventory plans, photos, regulations, mails, model state, contracts.
Qualify -> distinguish official sources, project sources, client statements, hypotheses.
Compose -> separate PLU, ABF, structure, cost, use, aesthetics, delay and responsibility.
Produce Candidate -> note, notice, option, mail, CCTP clause, Revit action candidate.
Test -> check regulatory, contractual, proof, memory and external-action risks.
Status -> mark candidate, to verify, to arbitrate, transmissible after validation, blocked.
```

## Relationship to method cards

Method cards may expose one movement, a sequence of movements or a reusable professional reflex.

They must not imply that the method executes itself.

```text
Method card = visible method proposal or reminder.
Governed Method Standard = underlying discipline.
Execution runtime = where work is performed.
Human gate = where consequential use is decided.
```

## Boundary reminder

This document is doctrine and method discipline only.

It creates no:

```text
workflow engine;
automation;
agent loop;
connector;
OpenWebUI plugin;
Hermes skill;
Revit add-in;
approval engine;
memory engine;
queue;
scheduler;
schema;
test;
external action.
```

```text
The method lives in Pantheon.
The work may be exposed by the surface.
The task may be executed by the runtime.
The output remains candidate until governed.
The human decides.
```