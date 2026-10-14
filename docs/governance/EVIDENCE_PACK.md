# Evidence Pack

Status: active doctrine — conceptual stabilization.

An Evidence Pack is the governed proof package produced after a task has been executed by an external runtime.

An Evidence Pack is not a runtime log.

An Evidence Pack is not hidden chain-of-thought.

An Evidence Pack is not a runtime state container.

It is a human-auditable dossier of evidence.

This document applies the canonical architecture boundary defined in `README.md` and `STATUS.md` to evidence produced after external execution.

## Purpose

An Evidence Pack explains what was done, on what basis, with which assumptions, with which risks and with which outputs.

It exists to make execution reviewable without making Pantheon Next an execution system.

Pantheon Next receives and governs evidence.

Pantheon Next does not replay, own or orchestrate execution.

## Core principle

Evidence is not activity.

Evidence is governed justification.

A runtime log may describe what happened.

An Evidence Pack must explain why the result can be reviewed, trusted, rejected, revised or escalated.

## Evidence versus log

A runtime log records events.

An Evidence Pack structures proof.

A log may be generated automatically.

An Evidence Pack must remain legible to a human reviewer.

A log may contain low-level technical traces.

An Evidence Pack must contain governance-relevant information only.

## Evidence versus chain-of-thought

An Evidence Pack must not store hidden reasoning traces or raw cognitive process.

It may contain:

- assumptions;
- concise rationale;
- source references;
- risk notes;
- limitations;
- review notes;
- output provenance.

It must not contain:

- hidden chain-of-thought;
- exhaustive internal reasoning;
- private scratchpad content;
- raw model deliberation;
- speculative reasoning treated as fact.

## Minimal structure

Canonical components:

```text
Identity
Linked Contract
Sources
Assumptions
Actions
Rites
Risks
Outputs
Reviews
Register Candidates
Approval State
```

Anything beyond this requires justification.

## Identity

An Evidence Pack must define a stable identifier.

The identifier is a governance identifier.

It is not a runtime trace ID.

It may reference external execution identifiers, but it must not depend on them to remain understandable.

## Linked Contract

An Evidence Pack should link to the Task Contract that authorized the execution boundary.

The Task Contract defines what was legitimate.

The Evidence Pack documents what was produced within that boundary.

If no Task Contract exists, the Evidence Pack must mark this explicitly as a governance gap.

## Sources

Sources identify the material used to support the result.

Sources may include:

- repository files;
- documents;
- user-provided context;
- official documentation;
- command outputs;
- prior approved governance artifacts.

Sources must be specific enough to support review.

Unsupported claims must be marked as assumptions or limitations.

## Assumptions

Assumptions are mandatory when certainty is incomplete.

They make implicit reasoning visible without exposing hidden reasoning traces.

Examples:

```text
repository visibility was partial
Pantheon remains governance-only
Hermes execution details were not inspected
```

Assumptions are not facts.

They are reviewable conditions behind a result.

## Actions

Actions describe what was done at governance-relevant level.

Allowed examples:

```text
read governance files
compared schema with doctrine
updated documentation
created ai_log entry
applied a rite review note
```

Forbidden examples:

```text
worker state transition
queue dispatch
provider route selection
scheduler retry sequence
hidden agent handoff
automatic rite execution
```

Low-level runtime activity belongs outside Pantheon unless summarized as evidence.

## Rites

An Evidence Pack may record rite-related evidence when a rite affects the legitimacy, structure, risk posture, delivery status or register implication of a result.

A rite entry may include:

```text
rite_id
trigger_reason
linked_task_contract
roles_called
inputs_considered
outputs_summary
risks_detected
unresolved_tensions
ZEUS_status
User_Decision_Gate_impact
register_impact
```

Allowed rite evidence includes:

- why the rite was proposed;
- why ZEUS allowed or rejected it;
- which roles were relevant;
- what tensions were exposed;
- what options, contradictions, source gaps or premises were retained;
- what status ZEUS assigned;
- whether a User Decision Gate is required.

Forbidden rite evidence includes:

- hidden chain-of-thought;
- raw role debate;
- private scratchpad;
- autonomous agent transcript;
- runtime worker trace;
- executable workflow state;
- automatic approval event;
- automatic memory promotion event.

A rite note is evidence context.

It is not proof by itself.

## Risks

Risks must be explicit.

Each risk should identify:

- uncertainty;
- possible consequence;
- mitigation or review path.

Risks prevent output from being treated as absolute authority.

The absence of visible risk is not a sign of quality.

It is often a sign of weak governance.

## Outputs

Outputs identify the artifacts produced.

Examples:

```text
markdown document
schema proposal
review note
Register Candidate
context pack
patch candidate
rite review note
```

Outputs are not automatically canonical.

An output becomes canonical only through the relevant review and approval path.

## Reviews

Reviews capture human or governance-role evaluation.

Reviews may record:

- accepted;
- rejected;
- needs revision;
- superseded;
- escalated.

A review is a governance act.

It is not a runtime callback.

## Register Candidates

An Evidence Pack may include Register Candidates.

A Register Candidate is not a Registre Probatoire entry.

Admission to the Registre Probatoire requires:

- evidence linkage;
- review;
- approval;
- explicit promotion.

Retrieved knowledge is not a Registre Probatoire entry.

Embeddings are not Registre Probatoire entries.

Repeated agent observation is not register admission.

High confidence is not register admission.

Rite output is not register admission.

A rite may support a Register Candidate only when the claim is explicit, scoped, evidence-linked, reviewable and approval-bound.

## Approval State

An Evidence Pack may carry or reference approval state.

Approval state describes governance legitimacy.

It must not trigger execution automatically.

It must not trigger rite execution automatically.

It must not promote memory automatically.

It must not merge, deploy or mutate systems automatically.

## Append-oriented discipline

Evidence should be append-oriented in spirit.

Corrections should be made through revision, supersession or review notes.

Silent rewriting of evidence destroys auditability.

Pantheon Next may later define stricter immutability rules, but the conceptual rule is already active:

```text
Do not rewrite proof invisibly.
```

## Relationship to Hermes Agent

Hermes Agent executes tasks and may produce Evidence Pack Candidates or evidence-relevant outputs.

Pantheon Next governs the expected evidence structure and any admission/review state.

Pantheon Next does not store Hermes runtime state.

Pantheon Next does not replay Hermes execution.

Pantheon Next does not control Hermes workers, queues, tools or provider routing.

If Hermes performs work associated with a rite, the Evidence Pack should summarize the governance-relevant rite output without importing Hermes runtime state.

```text
runtime output != Evidence
Evidence Pack Candidate != admitted Evidence Pack
runtime success != Evidence admission
```

## Relationship to runtime clients and Cockpit

`nesquena/hermes-webui`, when selected, or another compatible client may expose task interaction, candidate outputs and technical runtime status. Hermes WebUI is optional/proposed and does not become a Pantheon requirement merely because it offers near-CLI web access.

Pantheon Cockpit may project governed Evidence Packs, evidence gaps, review status, approval state and linked decisions.

Neither a runtime client nor the Cockpit canonizes Evidence automatically.

Client display does not make evidence complete, approved or authoritative. Cockpit projection does not replace the persisted governance owner.

```text
runtime display != Evidence
projection != persistence
projection != approval
optional client selected != authority transfer
```

## Relationship to schemas

The Evidence Pack schema validates structure.

It must not define runtime execution semantics.

The schema may validate:

- identifiers;
- sources;
- assumptions;
- actions;
- rite summaries;
- risks;
- outputs;
- reviews;
- Register Candidates;
- approval references.

The current protected schema may still expose legacy field names pending the separate schema-cleanup change. That compatibility state does not restore retired terminology as doctrine.

The schema must not define:

- execution order;
- retry behavior;
- worker state;
- queue semantics;
- provider routing;
- scheduling;
- hidden workflow state;
- rite execution semantics.

## Forbidden drift

Evidence Packs must never become:

- observability pipelines;
- runtime traces;
- hidden chain-of-thought archives;
- workflow state stores;
- queue history stores;
- scheduler logs;
- provider routing history;
- rite runtime traces;
- automatic memory promotion records.

If an Evidence Pack becomes necessary to resume execution, governance drift has occurred.

If an Evidence Pack stores hidden rite debate as proof, governance drift has occurred.

## Final rule

An Evidence Pack exists to make execution reviewable.

Not to make Pantheon execute.
