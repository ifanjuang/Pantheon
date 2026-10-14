# Governed Autonomy Gradient

Status: active support doctrine — autonomy gradient for governed AI use. Repository state: documented non-implemented.

This document defines how Pantheon Next allows useful AI autonomy without collapsing governance into execution.

It does not implement an agent, router, scheduler, queue, approval engine, memory engine, runtime, connector, plugin, OpenWebUI function, Hermes skill, Revit add-in, schema, test or external action.

Runtime/client/authority placement is inherited from `HERMES_INTEGRATION.md`: optional compatible runtime clients expose runtime interaction only, Hermes/the external runtime executes admitted work as PEP, Pantheon Cockpit projects governed state, and Pantheon policy/governance remains the bounded PDP authority.

## Purpose

Pantheon governance must not become a cage.

A governance framework that gates every micro-step will be correct on paper and unusable in practice.

The purpose of this document is to define where AI may move freely and where it must stop.

```text
The AI should be autonomous where effects are reversible, internal, candidate and traceable.
The AI must be gated where effects are consequential, external, canonical, irreversible or responsibility-bearing.
```

This document complements `GOVERNED_METHOD_STANDARD.md`.

The method standard defines the professional movements:

```text
Frame -> Admit -> Qualify -> Compose -> Produce Candidate -> Test -> Status.
```

The autonomy gradient defines how freely an AI or runtime may move through those movements.

## Core doctrine

```text
Pantheon does not reduce AI autonomy by default.
Pantheon relocates autonomy into reversible, candidate and traceable zones.
AI may explore broadly.
AI may produce freely as candidate.
AI may act locally when bounded, reversible and logged.
AI may not cross truth, memory, approval, transmission or external-action thresholds alone.
```

French project formulation:

```text
L'IA peut chercher, comparer, proposer, simuler, préparer et réviser largement.
Elle ne valide pas seule, n'envoie pas seule, ne mémorise pas seule, ne supprime pas seule et ne transforme pas une sortie en vérité seule.
```

## Autonomy is not binary

Pantheon should not divide behavior into only:

```text
allowed;
blocked.
```

The useful distinction is a gradient:

```text
free exploration;
candidate production;
local reversible action;
consequential action with human gate;
forbidden or out-of-scope action.
```

The autonomy level depends on four factors:

```text
1. Consequence — what can be affected?
2. Reversibility — can it be undone cheaply and safely?
3. Visibility — is it logged, inspectable and attributable?
4. Authority — does it imply truth, memory, approval, transmission or external action?
```

## Autonomy levels

### A0 — Assisted reading

AI may read, summarize, classify and restate material.

Typical operations:

```text
summarize;
extract questions;
list received pieces;
spot missing items;
name contradictions;
translate;
rephrase;
cluster topics;
prepare a source inventory.
```

Allowed autonomy:

```text
high.
```

Required safeguards:

```text
state source basis when consequential;
do not treat summary as proof;
do not promote memory;
do not transmit externally.
```

Default gate:

```text
no gate for internal low-risk reading;
human review when the summary will ground a consequential decision.
```

### A1 — Autonomous exploration

AI may explore a corpus, compare sources, search for gaps and propose angles without asking permission for every step.

Typical operations:

```text
compare documents;
identify risks;
detect inconsistencies;
map dependencies;
produce questions;
return to earlier method movements;
try alternative interpretations;
rank possible next checks.
```

Allowed autonomy:

```text
high, if exploration stays internal and candidate.
```

Required safeguards:

```text
trace explored sources;
mark uncertainty;
separate fact, interpretation and recommendation;
make gaps visible.
```

Default gate:

```text
no gate for internal exploration;
gate before using an exploration result as validated proof, memory or external action basis.
```

### A2 — Autonomous candidate production

AI may produce complete candidate outputs.

Typical operations:

```text
draft email;
draft note;
draft notice;
draft CCTP clause;
draft response;
produce options;
prepare analysis;
prepare Evidence Pack Candidate;
prepare Result Candidate;
prepare method proposal.
```

Allowed autonomy:

```text
high, if the output is clearly candidate and not transmitted automatically.
```

Required safeguards:

```text
candidate status;
source basis;
known limits;
allowed use;
forbidden use;
review requirement when consequential.
```

Default gate:

```text
human review before transmission, validation, canonical memory or consequential use.
```

### A3 — Local reversible action

AI may act in a bounded local workspace when the effect is reversible, logged and not externally binding.

Typical operations:

```text
create a local draft;
modify a scratch file;
prepare a sandbox output;
create a test view;
add review annotations;
prepare a local export candidate;
write a candidate card;
run a local analysis command;
try a Revit sandbox operation on a disposable copy.
```

Allowed autonomy:

```text
moderate to high, depending on profile.
```

Required safeguards:

```text
bounded workspace;
clear profile;
local trace;
rollback or disposable copy;
no silent external transmission;
no production-model assumption;
no canonical memory promotion.
```

Default gate:

```text
no gate for disposable sandbox operations when profile allows it;
human gate before moving the result into a production context.
```

### A4 — Consequential action with human gate

AI may prepare the action, but must not execute it alone.

Typical operations:

```text
send email;
submit form;
deposit permit;
publish document;
sign;
approve;
pay;
create contractual instruction;
change validated project status;
write canonical memory;
modify production model;
save / sync / delete in a consequential workspace.
```

Allowed autonomy:

```text
preparation only.
```

Required safeguards:

```text
explicit human gate;
evidence or source basis;
allowed-use statement;
visible diff when applicable;
trace;
confirmation of scope;
confirmation of recipient / target;
confirmation of irreversible effects.
```

Default gate:

```text
mandatory human approval.
```

### A5 — Forbidden or out-of-scope action

Some actions remain unavailable unless a later doctrine, adapter and explicit approval path promotes them.

Typical operations:

```text
irreversible deletion without recovery;
autonomous signature;
autonomous payment;
autonomous legal or contractual acceptance;
autonomous canonical memory promotion;
autonomous production-model synchronization;
autonomous submission to an authority;
unrestricted code execution;
unrestricted connector operation;
unbounded agent loop.
```

Allowed autonomy:

```text
none.
```

Required safeguards:

```text
refusal;
blocked status;
reason;
possible safe alternative;
human arbitration if the exclusion must be revisited.
```

Default gate:

```text
blocked by default.
```

## Autonomy table

| Level | Name | AI may do | AI may not do alone | Default gate |
|---|---|---|---|---|
| A0 | Assisted reading | Read, summarize, classify | Treat summary as proof | None for low-risk internal use |
| A1 | Autonomous exploration | Search, compare, map risks | Validate findings | Gate before consequential use |
| A2 | Candidate production | Draft complete outputs | Send, approve, canonize | Review before use |
| A3 | Local reversible action | Act in sandbox / local bounded space | Affect production or external target | Gate before promotion |
| A4 | Consequential prepared action | Prepare action package | Execute final effect | Mandatory human approval |
| A5 | Forbidden / out of scope | Nothing beyond explanation | Perform blocked effect | Refusal or arbitration |

## Freedom zones

Pantheon should actively permit AI freedom in these zones:

```text
searching;
reading;
classification;
comparison;
hypothesis generation;
alternative drafting;
option exploration;
internal critique;
source-gap detection;
risk surfacing;
method suggestion;
local simulation;
sandbox action;
trace organization;
preparing review surfaces.
```

These operations are valuable precisely because they do not need constant approval.

They should be bounded by status, trace and reversibility, not by excessive interruption.

## Gate zones

Pantheon must tighten control when the output can affect:

```text
truth;
evidence;
canonical memory;
approval;
responsibility;
mission scope;
client communication;
public authority submission;
contract;
fee / payment;
production model;
external system;
irreversible deletion;
publication;
synchronization;
legal or regulatory status.
```

These are not anti-autonomy zones.

They are places where autonomy changes form:

```text
AI may prepare.
AI may explain.
AI may draft.
AI may assemble evidence.
AI may recommend a status.
AI may open the gate.
The human crosses the gate.
```

## Profiles

Autonomy is profile-dependent.

A profile may raise or lower the permitted level for a context.

### Suggested generic profiles

| Profile | Intended context | Default ceiling |
|---|---|---|
| `Explore` | Thinking, research, internal analysis | A2 |
| `Draft` | Producing candidate text or documents | A2 |
| `Sandbox` | Disposable local workspace or test copy | A3 |
| `Project work` | Real project workspace, non-final | A3 with stricter trace |
| `Production` | Client-facing, official, contractual or model-of-record context | A4 |
| `Locked` | Sensitive, legal, contractual, irreversible or central model context | A0–A1 unless explicitly unlocked |

Profiles are not universal permissions.

They define a default ceiling. The actual gate still depends on consequence, reversibility, visibility and authority.

## Revit projection

The Revit connector is a useful stress test for this gradient.

A permissive V0 may be useful in a sandbox, but it must not imply production autonomy.

Suggested mapping:

| Revit operation | Default autonomy |
|---|---|
| Ping connector / read document state | A0 |
| Read active view / selection / visible elements | A0–A1 |
| Capture active view / visual context pack | A1–A2 |
| Explain selected elements | A1–A2 |
| Produce modeling strategy candidate | A2 |
| Add annotation or review parameter in sandbox | A3 |
| Create / modify model geometry in sandbox copy | A3 |
| Create / modify production model geometry | A4 |
| Delete elements in production model | A4 or A5 depending profile |
| Save / sync central model | A5 by default |

Minimal V0 requirement:

```text
If Revit autonomy exceeds A1, it must be local, visible and logged.
If Revit autonomy reaches A3, it must be bounded by profile and reversibility.
If Revit autonomy reaches A4, it must stop at a human gate.
If Revit action is A5, the plugin must refuse or require explicit future arbitration.
```

## Relationship to Governed Method Standard

The method standard answers:

```text
What movement are we in?
What is the condition of output?
What status should the result have?
```

The autonomy gradient answers:

```text
How far may the AI move without stopping?
What kind of movement requires a gate?
What can be done locally, reversibly and as candidate?
What must stay preparation-only?
```

Together:

```text
Method = discipline of work.
Autonomy = freedom envelope.
Gate = boundary of consequence.
```

## Relationship to Task Contract

A Task Contract should declare the requested autonomy ceiling when the task may involve tool execution.

Example fields, as method-level vocabulary only:

```text
autonomy_level: A0 | A1 | A2 | A3 | A4 | A5
profile: Explore | Draft | Sandbox | Project work | Production | Locked
allowed_effects:
forbidden_effects:
trace_required:
rollback_required:
human_gate_required:
```

This is not an executable schema.

Any future schema belongs in `schemas/` and requires explicit protected-path approval.

## Required trace by autonomy level

| Level | Minimum trace |
|---|---|
| A0 | Source or context reference when consequential |
| A1 | Sources explored, gaps and uncertainty |
| A2 | Candidate output, basis, limits, allowed use |
| A3 | Local target, profile, action log, rollback / disposable-copy note |
| A4 | Full action package, diff or target, evidence, human approval record |
| A5 | Refusal reason, safe alternative or arbitration request |

Trace does not make an action approved.

```text
Trace explains.
Evidence supports.
Approval validates.
The human decides.
```

## Anti-patterns

### Over-gating

```text
Every summary requires approval.
Every exploration step asks permission.
Every candidate draft is blocked.
The user must validate before the AI can compare sources.
```

This makes Pantheon unusable.

### Under-gating

```text
The AI sends because it drafted.
The runtime edits because it can.
The connector is installed so it is authorized.
The trace exists so it is evidence.
The memory was recalled so it is true.
```

This collapses governance into execution.

### False sandbox

```text
A workspace is called sandbox but affects a real project, shared file, central model, client-visible document or external system.
```

A sandbox is valid only if its effects are bounded and reversible.

## Boundary reminder

This document defines autonomy posture only.

It creates no:

```text
agent loop;
runtime;
queue;
scheduler;
approval engine;
memory engine;
connector gateway;
OpenWebUI plugin;
Hermes skill;
Revit add-in;
permission system;
schema;
test;
external action.
```

```text
Autonomy is useful inside reversible, candidate and traceable space.
Governance is mandatory at consequential thresholds.
Execution stays in the appropriate tool.
Pantheon governs the boundary.
```
