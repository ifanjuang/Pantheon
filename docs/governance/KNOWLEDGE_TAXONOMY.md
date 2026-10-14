# Knowledge Taxonomy

Status: active doctrine — knowledge, context and memory boundary stabilization.

Knowledge is not memory.

Context is not memory.

Evidence is not memory.

Retrieved content is not truth.

Indexed content is not truth.

Repeated content is not truth.

```text
Optional runtime clients may expose interaction and retrieved context.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed knowledge, Evidence and decision state.
Pantheon Next governs.
The human decides consequential effects.
```

## Purpose

This document defines the governance vocabulary used to separate source material, knowledge, context, evidence, memory and doctrine.

It does not implement a knowledge store, an indexer, a retrieval runtime, a vector database, an embedding strategy or a memory promotion engine.

## Core distinction

Pantheon Next separates six concepts that are often confused:

```text
Source material is available information.
Knowledge is organized reference information.
Context is task-bounded information.
Evidence is selected support for a claim or output.
Memory is governed persistent truth.
Doctrine is the rule layer that governs all of them.
```

Each category has a different authority level and lifecycle.

## Canonical categories

Pantheon Next uses the following categories:

```text
Raw Source
Source Reference
Knowledge Item
Retrieved Knowledge
Working Context
Context Pack
Evidence Item
Evidence Pack
Output Candidate
Register Candidate
Registre Probatoire entry
Doctrine
Runtime State
```

These are governance categories.

They are not storage backends.

They are not runtime states.

## Raw Source

A Raw Source is information supplied, uploaded, discovered, retrieved or referenced before review.

Examples include documents, web pages, emails, spreadsheets, repository files, images, meeting notes, chat messages, API results, runtime-client knowledge collections and user uploads.

A Raw Source may be useful.

It is not validated by default.

It may be stale, partial, duplicated, contradicted, sensitive or irrelevant.

## Source Reference

A Source Reference identifies a Raw Source with enough provenance to be reviewed later.

A Source Reference should preserve origin, title or identifier, date or retrieval time when relevant, access context, scope of use and limitation or uncertainty.

A Source Reference is not proof by itself.

It points to something that may support proof.

## Knowledge Item

A Knowledge Item is organized reference information that can be retrieved or consulted.

Examples include runtime-client knowledge entries, domain notes, policy excerpts, project reference documents, documentation excerpts and indexed source chunks.

A Knowledge Item is usable information.

It is not automatically true.

It is not a Registre Probatoire entry.

It is not approval.

## Retrieved Knowledge

Retrieved Knowledge is information surfaced by a retrieval mechanism during a task.

Retrieval does not validate content.

Retrieval only means the system found something that may be relevant.

Retrieved Knowledge must be treated as candidate support, not canonical truth.

It may become Evidence if selected and recorded in an Evidence Pack.

It may become a Register Candidate only when the task, source and approval path allow it.

## Working Context

Working Context is temporary information used during a specific interaction or task.

It may include the current user request, session constraints, temporary assumptions, selected excerpts or current task notes.

Working Context is local and temporary.

It does not persist as a Registre Probatoire entry.

It must not be silently promoted.

## Context Pack

A Context Pack is a bounded package of task-relevant context.

It may be sent to Hermes Agent or another external runtime.

A Context Pack should declare purpose, scope, included references, excluded references, memory status, uncertainty and approval state when relevant.

A Context Pack is not a Registre Probatoire entry.

A Context Pack is not runtime state.

It is a governance artifact for bounded use.

## Evidence Item

An Evidence Item is selected information used to support a claim, output or decision.

It should be traceable to a Source Reference.

It should state what it supports and must not support more than the source actually justifies.

Contradictions between Evidence Items must be preserved, not hidden.

## Evidence Pack

An Evidence Pack records the evidence used for a governed task.

It may include source references, assumptions, tool outputs, risk notes, candidate outputs, limitations, Register Candidates and approval state.

An Evidence Pack supports review.

It does not approve itself.

It does not create memory by itself.

## Output Candidate

An Output Candidate is a result proposed by a model, tool, Hermes Agent, human contributor or external runtime.

It may be an answer draft, review note, patch candidate, diagram candidate, report draft, Register Candidate or risk note.

An Output Candidate is not final by default.

It becomes approved only through the relevant approval path.

## Register Candidate

A Register Candidate is information proposed for durable governed persistence.

It must be explicitly marked as candidate.

It must define claim, scope, source, evidence link, risk, approval state and status.

Register Candidates must not be promoted automatically.

## Registre Probatoire entry

A Registre Probatoire entry is approved persistent knowledge inside Pantheon governance.

A Registre Probatoire entry must have clear scope, provenance, approval state, evidence or review linkage, and a revocation or supersession path.

A Registre Probatoire entry is more authoritative than retrieved Knowledge, but it can still be revised, revoked or superseded.

A Registre Probatoire entry is governed memory, not a raw database dump.

## Doctrine

Doctrine is the rule layer.

Doctrine governs roles, workflows as governance manifests, Task Contracts, approvals, evidence, memory, tools, integrations and knowledge categories.

Doctrine is not produced automatically from retrieval, execution or repeated use.

Doctrine changes require explicit governance review.

## Runtime State

Runtime State belongs to an execution system.

Examples include Hermes internal state, worker state, queue state, tool cache, provider trace, scratchpad, retry state and transient client UI state.

Runtime State must not be treated as a Registre Probatoire entry.

Runtime State may be summarized into an Evidence Pack only when it matters for review.

The runtime internals themselves should not become Pantheon memory.

## Authority model

Pantheon Next does not use a single flat truth bucket.

A useful authority order is:

```text
Doctrine governs.
Approvals validate.
Registre Probatoire entry persists.
Evidence supports.
Task Contracts bound work.
Context Packs scope work.
Knowledge Items inform work.
Raw Sources provide material.
Runtime outputs propose candidates.
```

This order is functional, not absolute.

A higher layer can still be revised if evidence and approval justify it.

## Client knowledge-store rule

Knowledge collections exposed by a runtime client are Knowledge Items or Raw Sources depending on their review state.

They are not a Registre Probatoire entry by default.

They may support retrieval, drafting, evidence discovery and task scoping.

They may become Evidence Items when selected and recorded.

They may become Register Candidates when explicitly proposed.

They do not become memory because they were uploaded, indexed, embedded, retrieved, cited or repeatedly used.

```text
client selected != authority transfer
knowledge available != knowledge adopted
retrieved != true
```

## Hermes output rule

Hermes Agent may return Output Candidates, Evidence Packs, Patch Candidates or Register Candidates.

Hermes output is not a Registre Probatoire entry.

Hermes execution state is not a Registre Probatoire entry.

Hermes confidence is not approval.

Hermes completion is not approval.

## Retrieval rule

Retrieval is a selection mechanism.

Retrieval is not validation.

Useful retrieval states include:

```text
retrieved
relevant
partially_relevant
irrelevant
stale
contradicted
unverified
sensitive
superseded
candidate_evidence
```

## Evidence conversion rule

A Knowledge Item becomes Evidence only when it is selected to support a specific claim, decision or output.

That conversion should identify source, supported claim, support scope, limitations, contradictions, freshness and confidence when relevant.

Evidence must not exceed the source.

## Memory promotion rule

A Register Candidate becomes a Registre Probatoire entry only through governed promotion.

Promotion requires candidate status, scope, provenance, evidence or justification, approval level appropriate to impact and revocation or supersession path.

Automatic promotion is forbidden.

Repeated use is not promotion.

Model confidence is not promotion.

Tool output is not promotion.

User convenience is not promotion.

## Revocation and supersession

Knowledge, evidence and memory can become obsolete.

Pantheon should be able to mark information as:

```text
active
candidate
deprecated
superseded
revoked
contradicted
archived
rejected
```

Revocation is not deletion by default.

A revoked item may remain useful as history, but not as current authority.

## Sensitive knowledge

Some knowledge is private, confidential, privileged or security-sensitive.

Sensitive knowledge must be scoped carefully.

It must not leak into public outputs, broad Context Packs, unredacted Evidence Packs, runtime prompts, external tools, logs or Register Candidates without approval.

Sensitivity is a governance property, not just a storage property.

## Contradiction handling

Contradictions must be visible.

Pantheon should not collapse contradictory sources into false consensus.

When sources conflict, mark the source conflict, affected claim, stronger and weaker evidence, unresolved uncertainty and required review or escalation.

## Confidence

Confidence is a review signal.

It is not authority.

A high-confidence candidate may still be wrong.

A low-confidence candidate may still identify a real risk.

Confidence must not bypass evidence or approval.

## Domain scope

Domain knowledge can be general, project-specific, user-specific or organization-specific.

The narrower the scope, the more carefully it must be labeled.

Example scopes:

```text
general
organization
user
project
dossier
task
session
```

Narrow scope must not be generalized without review.

A project fact is not automatically a general rule.

A user preference is not automatically organizational doctrine.

## Relationship to Scope Isolation

`SCOPE_ISOLATION.md` defines how these categories are bounded by session, task, dossier, project, domain, user, organization, repository, governance and system scope.

Knowledge taxonomy defines what an item is.

Scope isolation defines where it is valid.

## Forbidden drift

Knowledge taxonomy must never become:

- knowledge store implementation;
- vector database design;
- retrieval runtime;
- automatic memory promotion engine;
- hidden ontology engine;
- self-updating doctrine;
- runtime state store;
- source of truth bypassing approvals;
- replacement for Evidence Packs;
- replacement for Task Contracts.

If retrieval becomes truth, the boundary has failed.

If indexing becomes memory, the boundary has failed.

If runtime state becomes a Registre Probatoire entry, the boundary has failed.

## Final rule

Knowledge informs.

Context bounds.

Evidence supports.

Memory persists.

Doctrine governs.
