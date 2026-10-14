# Architecture Method Taxonomy

Status: candidate — terminology and placement taxonomy for architecture-domain methods, approaches, disciplines, strategies, procedures, tactics and reflexes.
Boundary profile: candidate_support_note.

This document is not canonical doctrine yet.

It does not implement a runtime, workflow engine, router, scheduler, queue, UI, memory engine, approval engine, document generator, checker, sender or external action.

It defines a vocabulary correction for architecture-domain governance so that `reflex` remains a narrow term instead of becoming a generic name for every method.

## Purpose

The architecture domain needs several reusable constructs:

```text
CCTP from plans;
site report finalization;
invoice / quote review;
material choice;
document summary;
mission boundary warning;
missing information handling;
formal notice escalation;
source verification;
reply wording.
```

Calling all of them `reflexes` is too broad and creates conceptual noise.

This taxonomy separates:

```text
method;
approach;
discipline;
strategy;
procedure;
tactic;
reflex.
```

## Core correction

```text
A reflex is not a full workflow.
A reflex is not a complete method.
A reflex is not the generic name for every reusable professional pattern.
```

A reflex is a triggered cadrage or rappel when a situation reveals a risk, missing frame, boundary issue or necessary professional caution.

## Definitions

### Method / Méthode

Layer: professional domain frame.

A method defines the professional way of handling a domain.

Examples:

```text
architecture agency method;
site supervision method;
document production method;
contractual review method;
```

A method frames practice. It does not execute, approve, validate or send.

### Approach / Démarche

Layer: reusable governed handling of a recurring situation.

An approach is the main path for a class of work.

Examples:

```text
CCTP from plan approach;
site report finalization approach;
invoice / quote review approach;
material choice approach;
document summary approach;
client response approach;
```

An approach may activate disciplines, procedures, strategies, tactics and reflexes.

### Discipline

Layer: cross-cutting rule that constrains many approaches.

A discipline applies broadly and repeatedly.

Examples:

```text
Missing Information Discipline;
Evidence Discipline;
Source Version Discipline;
Mission / Responsibility Boundary Discipline;
Workflow Depth Discipline;
Memory / Notion Write Discipline;
```

A discipline is not a one-time reaction. It is a standing rule.

### Strategy

Layer: conditional choice of route or priority.

A strategy determines how to proceed when several valid paths exist.

Examples:

```text
local sources before web;
Fast / Normal / Deep depth selection;
ask before infer;
latest CR first;
last known decision first;
client-readable summary versus internal technical summary;
formal notice escalation path;
```

A strategy is selected, not triggered as a warning by itself.

### Procedure

Layer: ordered sequence for a governed output or gate.

A procedure defines steps that must happen in order.

Examples:

```text
form filling resolution loop;
site report finalization sequence;
external email approval path;
Notion write candidate review;
insurance certificate check sequence;
```

A procedure may be executed by the runtime or performed manually, but Pantheon only governs its status, evidence, approval and scope.

### Tactic

Layer: local move inside one case.

A tactic is a small situational maneuver.

Examples:

```text
use limitation wording in a mail;
ask for a BET confirmation before replying;
mark a CR line as “maintained” instead of creating a duplicate;
prepare two reply postures: cannot pronounce / limited orientation;
request a photo from another angle;
```

A tactic is useful, bounded and often wording-level or decision-support-level.

### Reflex / Réflexe

Layer: triggered professional caution.

A reflex activates when something emerges during work and needs cadrage, rappel, warning, boundary marking or escalation.

A reflex may occur:

```text
as a subject emerges during project progress;
when a work item raises a new risk;
when a deliverable being produced reveals a boundary issue;
when a source contradiction appears;
when the system is about to overstate, validate, send, remember or expand scope;
```

A reflex is narrow and interruptive. It does not produce the whole deliverable.

Examples:

```text
mission boundary reflex;
responsibility warning reflex;
missing blocking information reflex;
external action reflex;
source-staleness reflex;
assumption-not-fact reflex;
wrong-lot suspicion reflex;
support-acceptance caution reflex;
formal-notice caution reflex;
```

## Placement examples

| Situation | Correct object | Reason |
|---|---|---|
| Produce a CCTP from a plan | Approach | Main reusable professional path. |
| Finish a site report from notes/photos | Approach / Procedure | Main deliverable path with ordered steps. |
| Summarize any document depending on context | Approach | Reusable handling of incoming material. |
| Decide if the answer should be Fast / Normal / Deep | Strategy / Discipline | Route selection governed by risk. |
| Do not invent missing information | Discipline | Standing rule across all approaches. |
| Ask for a missing structural note | Tactic | Local move in one case. |
| Warn that structural advice is outside mission | Reflex | Triggered caution and boundary reminder. |
| Prepare limitation wording in an email | Tactic | Local expression under mission-boundary discipline. |
| Verify insurance activity coverage step by step | Procedure | Ordered review sequence. |
| Prefer local agency sources before external web | Strategy | Priority rule for source retrieval. |

## Corrected architecture operating grammar

Architecture requests should be handled as:

```text
Request
-> Depth
-> Context
-> Approach / Procedure
-> Disciplines
-> Strategies
-> Tactics
-> Reflexes when triggered
-> Candidate
-> Gate
```

Short form:

```text
Request -> Depth -> Context -> Method Objects -> Candidate -> Gate
```

Where `Method Objects` may include approach, discipline, strategy, procedure, tactic and reflex.

## Reflex trigger rule

Use `reflex` only if the object answers:

```text
What has just surfaced that requires cadrage, rappel, warning, boundary marking or escalation?
```

Do not use `reflex` for:

```text
a complete document-production path;
a general review method;
a recurring deliverable pipeline;
a source policy;
a standing discipline;
a step-by-step procedure;
a local wording tactic;
```

## Relationship with roles / gods

Roles are not reflexes.

A role judges or guards a type of consequence:

```text
truth;
evidence;
scope;
memory;
approval;
external action;
responsibility;
```

A role may own reflexes.

This means:

```text
role = standing guardian of a consequence domain;
reflex = triggered signal emitted by that role when a situation requires cadrage, rappel, warning or escalation.
```

A role-owned reflex is part of a role's behavior, but it does not replace the role.

Examples:

```text
Zeus:
  - approval-ceiling reflex;
  - external-action arbitration reflex;
  - status-promotion caution reflex.

Athena:
  - coherence contradiction reflex;
  - weak-proof warning reflex;
  - overconfident conclusion reflex.

Themis:
  - mission-boundary reflex;
  - responsibility warning reflex;
  - forbidden-wording reflex.

Mnemosyne:
  - stale-recall reflex;
  - duplicate-memory reflex;
  - unvalidated-memory-write reflex.

Hermes:
  - handoff-boundary reflex;
  - execution-scope reflex;
  - connector-risk reflex.

Hephaestus:
  - production-readiness reflex;
  - missing-template reflex;
  - deliverable-structure warning reflex.

Iris:
  - expression-without-substance-change reflex;
  - tone-risk reflex;
  - external-wording caution reflex.
```

Example:

```text
Manifestation: user asks for a structural answer.
Situation: possible outside-mission technical validation.
Discipline: mission / responsibility boundary.
Role: Themis guards scope and responsibility.
Role-owned reflex: Themis emits a mission-boundary warning before drafting.
Tactic: offer “cannot pronounce” or “limited orientation” reply.
Gate: user validation before external email.
```

## Migration guidance

Existing documents may still include `REFLEX` in filenames or titles while this taxonomy is being introduced.

Progressive cleanup should:

```text
rename or reinterpret full deliverable paths as Approach / Procedure;
keep Reflex for warning / cadrage / rappel triggers;
use Discipline for standing cross-cutting rules;
use Strategy for route selection;
use Tactic for local move or wording;
make role-owned reflexes explicit when a god/role emits a triggered warning;
avoid renaming implementation artifacts without a separate approved package.
```

This document does not rename files by itself.

## Final rule

```text
Approaches handle work.
Disciplines constrain work.
Strategies choose routes.
Procedures order steps.
Tactics handle local moves.
Roles guard consequence domains.
Reflexes interrupt with necessary cadrage.
Some reflexes are owned by roles.
Gates expose decisions.
The architect decides.
```
