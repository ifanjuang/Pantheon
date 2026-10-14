# Execution Discipline

Status: active doctrine — independently maintained in Pantheon Next.

Historical provenance is preserved in git history; this file has no external source dependency.

This document defines the discipline that applies before, during and after any governed work around Pantheon Next.

It applies to human contributors, AI assistants, Claude, Hermes Agent and future read-only tooling.

It is governance doctrine.

It is not an execution engine.

It is not an autonomous agent loop.

It is not a scheduler, queue, retry system, provider router or self-healing runtime.

```text
Optional runtime clients may expose interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed review and decision state.
Pantheon Next governs.
The human decides consequential effects.
```

## Principle

Pantheon Next does not reward complexity.

Every task must use the smallest safe path that satisfies the request.

```text
read before writing
single-role before workflow
template before new abstraction
candidate before canonical
patch before broad refactor
evidence before assertion
stop before unsafe escalation
human decision before unresolved conflict
```

The goal is not ceremony.

The goal is to prevent uncontrolled assumptions, unnecessary abstractions, hidden mutations and unsupported conclusions.

## Scope

This discipline applies to:

- ChatGPT interventions;
- Claude interventions;
- Hermes Agent executions;
- governance-document migrations;
- candidate skill reviews;
- workflow or Task Contract revision proposals;
- repository documentation changes;
- future code patch proposals;
- external option reviews;
- future read-only Doctor checks.

It does not create runtime behavior by itself.

It defines how work is framed, reviewed, evidenced and stopped.

## Core rule

Before modifying anything or asking Hermes to execute, identify:

```text
user objective
minimum sufficient path
scope boundary
known uncertainty
required sources
approval level
memory impact
evidence requirement
stop condition
next safe action
```

If a visible uncertainty materially affects the result, do not hide it.

Use explicit status markers:

```text
to_verify
partial
non_implemented
implemented_but_not_documented
documented_but_not_implemented
obsolete
contradictory
blocked_until_review
candidate_only
migrated_doctrine
```

## Smallest safe path

Prefer:

```text
single_role_path over workflow
existing doctrine over new doctrine
existing template over generated structure
existing skill or Hermes capability over new skill
small focused patch over broad refactor
read-only diagnosis before mutation
Evidence Pack before confident conclusion
User Decision Gate before forced resolution
```

Do not create a new abstraction unless it gives a clear governance, auditability, safety, evidence or scope benefit.

## Surgical repository changes

When editing the repository:

- touch only files needed for the objective;
- avoid opportunistic cleanup;
- avoid unrelated formatting churn;
- avoid mixing documentation, schema, tests, operations, platform and Docker changes;
- avoid rewriting large docs when a focused migration or additive patch is enough;
- preserve durable rationale in owner documents, tests/contracts, Git history and pull-request discussion; add an exceptional `ai_log` only when consequential context would otherwise be lost or materially ambiguous;
- verify the real diff after important commits.

Documentation-only changes must not claim implementation.

If a change only documents doctrine, say it documents doctrine.

Protected areas require explicit confirmation before modification:

```text
pyproject.toml
schemas/
tests/
operations/
platform/
Docker
.env
CLAUDE.md
```

## Goal-driven work

Before work starts, define success.

Examples:

```text
The file moves from stub to migrated doctrine.
The migrated document does not introduce runtime behavior.
The status, roadmap, governance index and migration mapping are reconciled.
The durable repository record explains the intervention; an exceptional ai_log is added only if otherwise necessary.
No private data enters the repository.
No schema, test, operation or platform file is modified.
```

A task is incomplete if it cannot say what success would look like.

## Single-role before workflow

Not every request needs a workflow.

Use a single-role path when one Pantheon Role can safely handle the work inside a bounded frame.

Examples:

- IRIS rewrites a short draft without sending it;
- ARGOS extracts one fact from a provided source;
- ATHENA structures a simple plan;
- THEMIS classifies an approval level;
- APOLLO checks a short answer for unsupported claims.

Escalate when:

- multiple roles become necessary;
- multiple sources must be reconciled;
- external communication is requested;
- approval level rises;
- memory could be affected;
- file mutation is requested;
- technical, contractual, financial or regulatory exposure appears;
- unresolved contradiction appears;
- the user must decide between materially different options.

Escalation should produce a visible Task Contract revision or User Decision Gate when required.

## Anti-overengineering guardrails

A proposal is overengineered when it:

- creates a workflow where one role is enough;
- creates a new skill where a note, template or existing Hermes capability is enough;
- creates a runtime adapter before the governance boundary is stable;
- creates a dashboard before the status model is clear;
- creates persistent storage before memory doctrine and schemas are stable;
- creates automated execution before approval and evidence paths are stable;
- creates tests for doctrine that is still moving;
- creates a marketplace where a watchlist is enough.

Preferred sequence:

```text
document
example
candidate
review
minimal read-only check
schema alignment
test
implementation proposal
approval
promotion
```

## Evidence discipline

No consequential output should hide its proof standard.

For a consequential answer, patch or migration, record:

```text
files read
sources used
assumptions
limitations
unsupported claims
approval required
next safe action
```

For repository work, record:

```text
files changed
runtime impact
tests run or not run
protected areas untouched or approved
follow-up needed
```

If evidence is missing, say so.

Do not convert uncertainty into confident prose.

A model statement is not evidence.

## Safe partial completion

Partial completion is acceptable when the task is large, risky, underspecified or blocked.

A safe partial result must state:

- what was completed;
- what was not completed;
- why it stopped;
- what risk remains;
- what the next safe action is;
- whether approval is required.

Unsafe partial completion is not acceptable when it silently leaves a file, schema, approval path, migration status or memory state contradictory.

## Stop conditions

Stop or escalate when:

- the requested action exceeds the current Task Contract;
- approval level rises;
- the task would affect external parties;
- the task would mutate protected areas without confirmation;
- evidence is insufficient for a consequential claim;
- sources conflict materially;
- private or identifiable data would enter the repository;
- Hermes would need broader access than granted;
- a runtime client would be treated as memory, governance authority or persistence owner;
- Pantheon would become an execution surface.

Stopping is not failure when continuation would violate governance.

## Hermes execution discipline

Hermes may execute operational work, but only inside a bounded frame.

Hermes should:

- receive a Task Contract when risk requires it;
- use the smallest allowed toolset;
- preserve scope boundaries;
- emit Result Candidates, Evidence Packs, Patch Candidates or Register Candidates;
- emit revision signals when the current path no longer fits;
- stop when approval is required.

Hermes must not:

- canonize memory;
- canonize workflows;
- activate skills as canonical;
- send external communications without approval;
- silently switch to unallowed tools;
- mutate files outside the task frame;
- bypass User Decision Gates;
- treat tool availability as tool authorization.

## Runtime-client and Cockpit exposure discipline

An optional runtime client may expose:

- user intent;
- files and knowledge collections selected by the user;
- Task Contracts;
- candidate outputs;
- technical runtime status.

Hermes WebUI is one optional/proposed runtime client if separately selected and qualified. Its availability does not make it required.

Pantheon Cockpit may project:

- governed Task Contract state;
- Evidence Packs and evidence gaps;
- approval prompts;
- User Decision Gates;
- Register Candidates;
- governed review status.

Neither a runtime client nor the Cockpit becomes:

- a Registre Probatoire entry by display;
- approval authority by itself;
- hidden source of truth;
- automatic promotion mechanism;
- a replacement for the persisted governance owner.

```text
Hermes WebUI available != Hermes WebUI selected
client selected != authority transfer
projection != persistence
runtime display != Evidence
```

## Claude and coding-agent discipline

Claude or another coding agent may assist with repository work.

It must:

- stay inside the assigned scope;
- avoid unrelated refactors;
- avoid inventing implementation details not requested;
- preserve the optional-client / Hermes Agent / Pantheon Cockpit / Pantheon Next boundary;
- use owner documents, tests/contracts, Git history and pull-request rationale as the default durable trace; add an exceptional `ai_log` only when needed to preserve otherwise-lost consequential context;
- state when tests were not run;
- avoid modifying protected areas without confirmation.

If the task becomes broader than expected, the safe output is a diagnostic or bounded follow-up plan, not uncontrolled expansion.

## Review checklist

Before accepting a contribution, check:

```text
Does it solve the stated objective?
Does it touch only necessary files?
Does it avoid runtime drift?
Does it preserve optional-client / Hermes Agent / Pantheon Cockpit / Pantheon Next boundaries?
Does it avoid private or identifiable data?
Does it mark candidate status where appropriate?
Does it specify evidence and approvals where consequential?
Does it avoid unnecessary workflow creation?
Does it update STATUS / ROADMAP / governed indexes when needed without requiring an ai_log by default?
Does it leave a clear next safe action?
```

## Final rule

```text
Use the smallest safe path.
Escalate only when the task requires it.
Never hide uncertainty.
Never let execution convenience override governance.
Never call documentation implementation.
```
