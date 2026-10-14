# Scope Isolation

Status: active doctrine — memory and context compartmentalization.

Scope isolation is the governance rule that prevents information from leaking between sessions, tasks, dossiers, projects, users, domains and system doctrine.

This doctrine can be projected through folder-, workspace- or session-scoping features in external clients, but it does not import any client filter, plugin or runtime behavior.

It defines Pantheon governance doctrine only.

```text
Optional runtime clients may expose interaction and working-scope controls.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed scope, warnings and decisions.
Pantheon Next governs.
The human decides consequential effects.
```

## Purpose

Pantheon Next must prevent accidental cross-contamination between contexts.

A memory-like item must never be globally reusable by default.

A source uploaded in one client workspace must not silently affect another workspace.

A project fact must not become organization doctrine.

A session assumption must not become project memory.

A retrieved Knowledge Item must not become a Registre Probatoire entry.

Scope isolation makes those boundaries explicit.

## Core rule

Every memory-like or context-like artifact must declare scope.

Default rule:

```text
no global memory by default
```

A scoped artifact may be used only within its declared scope unless a governed review explicitly broadens that scope.

## Scope types

Allowed scope types:

```text
session
task
dossier
project
domain
user
organization
repository
governance
system
```

These scope types are governance categories.

They are not storage backends.

They are not client implementation details.

They are not runtime partitions.

## Scope identity

A scoped artifact should declare:

```text
scope_type
scope_id
scope_label
source
status
evidence_link
approval_state
created_at or observed_at
staleness or review rule
```

For low-risk working context, a lighter record may be acceptable.

For Register Candidates and a Registre Probatoire entry, explicit scope is mandatory.

## Scope hierarchy

A narrower scope must not silently leak into a broader scope.

Examples:

```text
session -> project requires review
project -> domain requires review
domain -> system requires review
user -> organization requires review
client workspace -> project requires mapping
Knowledge Item -> memory requires approval
```

Scope expansion is a governance act.

It is not a retrieval effect.

It is not a UI effect.

It is not a runtime effect.

## Runtime-client workspaces and folders

External runtime clients may provide useful workspace, folder, project, chat or knowledge-collection scoping.

Hermes WebUI is one optional/proposed client that may expose such runtime organization if separately selected and qualified. This doctrine does not require it.

A client workspace can help identify a working perimeter.

A client workspace can help select relevant Knowledge Items.

A client workspace can help separate chats, files and project contexts.

But a client workspace is not a Registre Probatoire entry.

A client workspace is not a governance scope by itself until mapped into a Pantheon scope.

The mapping must be explicit when the distinction matters.

Recommended conceptual mapping:

```text
client workspace/folder -> dossier or project scope
client chat/session -> session scope
client knowledge collection -> Knowledge Item scope
client upload -> Raw Source or Source Reference
client memory-like feature -> Register Candidate at most
```

```text
Hermes WebUI available != Hermes WebUI selected
client scope != governed scope
client selected != authority transfer
```

## Chat scope

A chat is normally session-scoped.

Chat content may support the current task.

Chat content must not become durable memory by default.

A chat observation may become a Register Candidate only when:

- the claim is explicit;
- the scope is defined;
- evidence or user confirmation exists;
- approval rules allow it.

## Project and dossier scope

Project and dossier scope are high-value boundaries.

They prevent one client, project, legal matter, architectural file or technical dossier from polluting another.

Project-scoped material may include:

- project facts;
- project constraints;
- project-specific sources;
- project decisions;
- project Register Candidates;
- project deliverables;
- project Evidence Packs.

Project memory must not become user, organization, domain or system memory without review.

## Domain scope

Domain scope applies to reusable professional or technical knowledge.

Examples:

```text
architecture_fr
software
governance
legal_reference
```

Domain knowledge may inform many projects.

It must not override project-specific evidence.

It must not become system doctrine without governance review.

## User scope

User scope applies to durable user-specific preferences, constraints or recurring patterns.

User-scoped memory must be handled carefully.

It can influence future interactions only when approved and bounded.

It must not become organization doctrine.

It must not become project fact.

It must not become hidden behavioral steering.

## System and governance scope

System and governance scopes are the most protected.

They include:

- Pantheon doctrine;
- approval rules;
- memory policy;
- evidence policy;
- role authority;
- integration boundaries;
- external tools policy.

System or governance scope changes require strong evidence and explicit approval.

No session, project, client workspace, runtime output or repeated observation may mutate these scopes automatically.

## Context Packs

Context Packs must preserve scope isolation.

A Context Pack should declare:

- intended scope;
- included scopes;
- excluded scopes;
- source boundaries;
- memory status;
- staleness warnings;
- approval state when relevant.

A Context Pack must not mix scopes silently.

If it combines project memory, domain knowledge and system doctrine, the difference must remain visible.

## Evidence Packs

Evidence Packs should preserve scope.

An Evidence Pack should identify the scope of its sources, assumptions, outputs and Register Candidates.

Evidence from one project must not be reused in another project without review.

A source used as evidence in one task does not become universal evidence.

## Register Candidates

Every Register Candidate must declare scope.

Required fields include:

```text
claim
scope_type
scope_id
source
evidence_link
risk
approval_state
status
```

A Register Candidate without scope must remain invalid or incomplete.

Scope-less memory is a governance risk.

## Registre Probatoire entry

A Registre Probatoire entry must remain scoped.

A Registre Probatoire entry does not mean global memory.

A project-scoped a Registre Probatoire entry governs only that project.

A user-scoped a Registre Probatoire entry governs only that user context.

A domain-scoped a Registre Probatoire entry governs only that domain.

A system-scoped a Registre Probatoire entry requires the highest discipline because it may affect all future behavior.

## Scope expansion

Scope expansion requires review.

Examples:

```text
project fact -> reusable domain rule
user preference -> organization practice
session insight -> project memory
project method -> system doctrine
client workspace context -> canonical project memory
```

Scope expansion should produce an Evidence Pack or review note.

It should identify what changes, why it changes, and what risks follow.

## Scope narrowing

Scope narrowing is allowed when a memory or context item was too broad.

Examples:

```text
system -> domain
domain -> project
project -> dossier
user -> session
```

Scope narrowing may be used as mitigation when overreach is detected.

## Scope conflicts

When two scopes conflict, do not silently merge them.

Escalate or mark the conflict.

Useful conflict states:

```text
scope_conflict
cross_project_conflict
user_project_conflict
domain_project_conflict
system_domain_conflict
stale_scope
unknown_scope
```

A conflict is not a failure.

It is a review signal.

## Deletion and cleanup

Automatic deletion of memory-like items is risky.

Cleanup may be useful for working context, stale candidates or orphaned artifacts, but it must not silently erase governance history.

For governed artifacts, prefer:

```text
revoked
superseded
archived
rejected
expired
```

instead of silent deletion.

If a UI or runtime cleanup mechanism removes items, the governance record must preserve what matters.

## Relationship to runtime clients and Cockpit

Optional runtime clients may expose workspace, folder, chat and knowledge-collection boundaries and may help a user select a working scope.

Pantheon Cockpit may project the governed scope, warnings, evidence gaps and decisions attached to that scope.

Client scope controls must not canonize scope, promote runtime memory into Pantheon memory or delete governed memory without a governance record.

Neither client display nor Cockpit projection is the persistence owner.

## Relationship to Hermes Agent

Hermes Agent may receive scoped Context Packs.

Hermes may produce scoped outputs and scoped Register Candidates.

Hermes must not broaden scope silently.

Hermes must report when a task requires access outside the declared scope.

Hermes runtime state remains outside Pantheon memory.

## Relationship to Knowledge Taxonomy

`KNOWLEDGE_TAXONOMY.md` defines the categories of source, knowledge, context, evidence, memory and doctrine.

This document defines how those categories are scoped.

The two documents must be read together.

## Relationship to Memory

`MEMORY.md` defines memory promotion and a Registre Probatoire entry.

This document adds the rule:

```text
memory is never global unless explicitly approved as global
```

## Forbidden drift

Scope isolation must never become:

- automatic memory promotion;
- hidden user profiling;
- silent cross-project context sharing;
- automatic client-workspace memory canonization;
- UI-driven source of truth;
- runtime-managed a Registre Probatoire entry;
- silent deletion of governance history;
- global memory by convenience.

If client workspace scoping becomes canonical memory without approval, the boundary has failed.

If one project silently changes another project’s context, the boundary has failed.

If a runtime client or Hermes can broaden governed scope without Pantheon approval, the boundary has failed.

## Final rule

Every durable memory-like claim must answer:

```text
What is the claim?
Where is it valid?
Who or what approved it?
What evidence supports it?
When should it be reviewed?
```

Without scope, there is no governed memory.
