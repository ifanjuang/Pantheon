# Product Differentiation

Status: active doctrine — product differentiation, documentation only.

This document defines the product differentiation of Pantheon Next.

It does not define implementation.

It does not add runtime behavior.

It does not introduce an agent runtime, tool runtime, provider router, scheduler, queue, plugin marketplace, mandatory WebUI or Hermes replacement.

```text
Optional runtime clients may expose interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed Cards, decisions and status.
Pantheon Next governs.
The human decides consequential effects.
```

## Core thesis

Pantheon Next should not differentiate by adding more agents, more workflow complexity or another RAG platform.

Pantheon Next differentiates by turning an AI stack into a governed professional method.

```text
Runtime clients + Hermes provide interaction and execution.
Pantheon provides professional control.
```

Market sentence:

```text
Pantheon is the governed configuration layer between AI tools and professional responsibility.
```

## What Pantheon is not

Pantheon Next is not:

- another chat UI;
- another mandatory WebUI;
- another Hermes;
- another RAG platform;
- another agent builder;
- another visual workflow runtime;
- another provider router;
- another plugin marketplace;
- another autonomous execution system.

If a selected runtime client, Hermes or another external tool already does something well, Pantheon should not rebuild it.

## What Pantheon is

Pantheon Next is:

```text
configuration governance
+ evidence discipline
+ approval method
+ memory discipline
+ professional dossier framing
```

Short version:

```text
Pantheon configures the stack so AI work becomes controllable, traceable and reviewable.
```

## Differentiation pillars

Pantheon should focus on three product pillars.

```text
1. Governed configuration
2. Evidence-first workflow
3. Decision memory
```

Everything else should support one of these three pillars.

If a feature does not improve configuration, evidence, approval, memory, auditability or professional trust, it should not be added.

## Pillar 1 — Governed configuration

Most users can install AI tools.

Few users can configure them into a controlled professional method.

Pantheon should provide the missing configuration layer for optional runtime clients, Hermes and adjacent tools without making any client authoritative or mandatory.

Possible artifacts:

```text
Runtime Client Configuration Guidance
Hermes Profile Pack
System Prompt Pack
Knowledge Naming Guide
Tool Access Policy
Approval Display Conventions
Evidence Pack Display Conventions
Task Contract Templates
Context Pack Templates
Register Candidate Templates
Setup Doctor Checklist
Integration Boundary Checklist
```

Hermes WebUI may be one optional/proposed runtime client when separately selected and qualified. This doctrine does not require it.

These artifacts are not runtime behavior.

They are reviewable configuration doctrine.

### Configuration questions Pantheon should answer

```text
Which knowledge collections are visible?
Which model can call which tools?
Which prompts require sources?
When is validation required?
What is only a candidate?
What can become memory?
What must remain local?
What requires external freshness checking?
What must be logged?
```

### Configuration rule

```text
Pantheon should not execute runtime clients or Hermes.
Pantheon should make their governance-relevant configuration explicit, reusable, reviewable and auditable.
```

## Pillar 2 — Evidence-first workflow

Most RAG systems answer with sources.

Pantheon must distinguish the status of each item.

```text
source
retrieved knowledge
working context
evidence candidate
evidence item
contradiction
uncertainty
output candidate
approval event
memory candidate
canonical memory
```

This distinction is the core product difference.

### Why this matters

Without explicit status, an AI stack easily collapses into:

```text
uploaded = trusted
retrieved = true
chat = memory
tool output = decision
agent success = approval
```

Pantheon exists to prevent that collapse.

### Evidence-first rule

```text
A source can support a claim.
A retrieved chunk can suggest evidence.
Only a governed review can turn it into evidence.
Only approval can turn an output into a decision.
Only memory review can turn a decision into a Registre Probatoire entry.
```

## Pillar 3 — Decision memory

Pantheon should not sell memory as recall.

Normal AI memory asks:

```text
What did the assistant remember?
```

Pantheon decision memory asks:

```text
What was validated?
Why was it validated?
Which sources supported it?
What was rejected?
What became obsolete?
What should not be reused?
```

This is a professional difference.

### Memory rule

```text
Chat is not memory.
Retrieval is not memory.
Repeated use is not memory.
Only approved, scoped, reviewable retention is a Registre Probatoire entry.
```

## Professional dossier modes

Pantheon should not remain purely generic.

It should support professional dossier modes.

Possible modes:

```text
Architect dossier mode
Legal dossier mode
Medical or health dossier mode
Expert report mode
Administrative dossier mode
Research synthesis mode
```

Each mode should define:

- expected source types;
- required checks;
- freshness expectations;
- output templates;
- validation thresholds;
- memory rules;
- non-deliverable conditions.

## Example — Architect dossier mode

Possible tasks:

```text
analyse devis vs CCTP
note de synthèse réglementaire
compte rendu chantier assisté
réponse mairie / ABF
analyse contradiction pièces écrites / plans
préparation réception / réserves
suivi avenants
```

For each template, Pantheon should define:

```text
required sources
freshness checks
risk level
output format
approval level
memory rule
```

## Freshness and source aging

Professional users do not only need sources.

They need to know whether a source is still usable.

Pantheon should track:

```text
source_date
upload_date
index_date
last_verified_date
freshness_status
external_check_required
superseded_by
```

Recommended statuses:

```text
current_verified
current_likely
stale_possible
stale_confirmed
metadata_insufficient
external_check_required
```

## Responsibility status

Do not expose only model confidence.

Expose professional responsibility status.

Useful statuses:

```text
usable_for_draft
requires_source_check
requires_human_review
blocked_by_missing_source
blocked_by_contradiction
validated_for_delivery
not_for_delivery
```

These statuses are clearer for professionals than probability scores.

## Contradiction ledger

Most AI systems smooth contradictions.

Pantheon should preserve them.

A contradiction ledger should record:

```text
claim
source_A
source_B
conflict_type
severity
resolution_status
human_decision
```

This is a differentiator for serious dossiers.

## Setup Doctor

Pantheon should eventually provide a Setup Doctor as a checklist first, optional tool later.

Questions:

```text
Is the selected runtime client configured correctly?
Are tools too broad?
Are knowledge collections scoped?
Can the model browse everything?
Is runtime memory enabled where it should not be?
Are system prompts aligned with source discipline?
Are Evidence Pack outputs visible?
Are Hermes profiles candidate-only?
Are approval thresholds explicit?
```

The Setup Doctor must not become an auto-installer or hidden runtime.

## Audit-ready export

Professional users need to justify conclusions.

Pantheon should be able to define an audit-ready export containing:

```text
Task Contract
sources used
sources rejected
retrieved excerpts
contradictions
assumptions
review actions
validation event
final output
memory candidate decision
```

Possible outputs:

```text
Evidence Pack
Dossier audit bundle
Decision log
Source appendix
```

## AI usage register

A practical product artifact:

```text
Which AI tools are used?
For which professional tasks?
With which data?
With which models?
With which human oversight?
With which limits?
```

This can support internal governance and risk discussion without pretending to be compliance software.

## Adoption maturity levels

Pantheon should support progressive adoption.

```text
Level 0 — chat with documents
Level 1 — scoped Knowledge
Level 2 — Task Contract
Level 3 — Evidence Pack
Level 4 — approval and memory governance
Level 5 — audit-ready professional method
```

This gives users a path without forcing the full architecture at the start.

## What not to use as differentiation

Avoid differentiating on:

```text
more agents
more autonomy
more workflows
more RAG
more plugins
more tools
more hidden automation
```

These are crowded, risky and easy to copy.

Pantheon should differentiate through method, not spectacle.

## Relationship to runtime clients, Hermes and Cockpit

An optional runtime client answers:

```text
Where does the user interact with the execution runtime?
```

Hermes Agent answers:

```text
Who performs the technical work?
```

Pantheon Cockpit answers:

```text
Where are governed Cards, status, Evidence gaps and decisions projected?
```

Pantheon Next answers:

```text
Under what rules can that work be trusted, reviewed, retained or rejected?
```

Hermes WebUI may satisfy the optional runtime-client role if separately selected and qualified, but its selection does not transfer Pantheon authority.

## Product promise

```text
Use AI faster without losing the dossier method:
source control, evidence discipline, human validation and retained decisions.
```

## Final position

```text
Pantheon does not replace the stack.
Pantheon makes the stack professional.
```

Or:

```text
Pantheon is the missing governance configuration layer between AI tools and professional responsibility.
```

## Status

Product doctrine only.

No implementation.

No dependency added.

No mandatory WebUI.

No Hermes tool.

No runtime.

No scheduler.

No queue.

No provider router.

No automatic memory promotion.
