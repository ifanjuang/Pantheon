# Rites

Status: active doctrine - shared governance procedures.

Rites are bounded governance procedures used to coordinate Pantheon Roles around a recurring methodological tension.

They are not agents.

They are not Pantheon Roles.

They are not Hermes profiles.

They are not a runtime.

They are not a scheduler, queue, message bus, workflow engine, provider router, plugin manager, skill installer, MCP layer, observability backend or hidden debate system.

```text
Optional runtime clients may expose interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed rite, review and decision state.
Pantheon Next governs.
The human decides consequential effects.
```

## Core distinction

Pantheon Roles carry stable responsibilities of judgment.

Rites organize temporary procedures shared by several roles.

Task Contracts bound what may be done.

Evidence Packs make the result reviewable.

ZEUS arbitrates status and next procedure.

The human decides when procedural arbitration is insufficient.

```text
Roles judge.
Rites coordinate.
Task Contracts bound.
Evidence Packs prove.
ZEUS states procedure.
The human decides.
```

## Why rites exist

Some governance moves recur across multiple roles:

- divergent exploration before convergence;
- autocritique after a convincing draft;
- source concordance before delivery;
- premise extraction before planning;
- session refoundation when context is polluted.

Keeping these moves inside one role would create oversized roles and duplicated doctrine.

A rite makes the method explicit, reusable and reviewable without creating a new autonomous actor.

## Invocation policy

Rites are governed by `RITE_INVOCATION_POLICY.md`.

A rite is safe only when four answers are visible:

```text
Why this rite?
Who authorized it?
What did it change?
How does it close?
```

Core invocation rule:

```text
A rite may be proposed by a role.
ZEUS authorizes or rejects it.
The Task Contract records why.
The Evidence Pack records what changed.
An optional runtime client may expose technical interaction.
Pantheon Cockpit may project the governed rite status and linked decision.
None of these executes the rite for Pantheon.
```

## Anti-chaining rule

A rite may reveal the need for another rite.

It must not trigger another rite.

A second rite requires ZEUS status and an explicit reason.

A third rite requires either:

- User Decision Gate;
- task split;
- scope narrowing;
- explicit high-risk justification.

Forbidden chain:

```text
Premisses Cachees
-> Divergence Controlee
-> Autocritique Contradictoire
-> Concordance des Sources
-> Refondation de Session
-> new Task Contract
-> another rite
```

If this chain appears, the system is rebuilding a workflow through rites.

That is governance drift.

## Rite budget

Rites must remain proportional to risk.

Default budget:

```text
low-risk task      -> no rite by default
medium-risk task   -> one rite maximum unless ZEUS justifies otherwise
high-risk task     -> multiple rites allowed if explicitly recorded
three rites or more -> User Decision Gate or task split required
```

A rite has cost:

```text
time_cost
attention_cost
evidence_cost
decision_cost
```

If the rite does not change decision quality, evidence quality, risk posture, memory posture or delivery safety, it should not be invoked.

## Anti-patterns and closure

Rites are also governed by:

- `RITE_ANTI_PATTERNS.md` - records recurring misuse patterns such as rite as workflow, rite as agent debate, rite as proof theater, rite as approval bypass, rite as memory shortcut, rite as context deletion, rite overuse, rite chaining and UI activity illusion.
- `RITE_EXIT_CRITERIA_AND_CONFLICTS.md` - defines closure criteria per rite, claim and assumption statuses, conflict handling between rites and User Decision Gate escalation rules.

Core anti-drift rule:

```text
A rite must end with status, retained output, preserved tensions and an explicit next allowed action.
```

## Selection and modes

Rites are also supported by ergonomic selection and intensity doctrine:

- `RITE_SELECTION_MATRIX.md` - maps governance symptoms to candidate rites, anti-risks and required outputs.
- `RITE_MODES.md` - defines `mode_light`, `mode_standard` and `mode_full` to keep rite intensity proportional.

Core selection rule:

```text
A symptom may suggest a rite.
It does not trigger the rite.
ZEUS decides whether the rite is allowed.
```

Core mode rule:

```text
Choose the smallest rite mode that can safely expose the useful tension.
```

## Examples and adoption

Rites are also supported by fictional examples:

- `RITE_EXAMPLES.md` - tests how rites behave in realistic situations without creating prompts, schemas, runtime-client components or Hermes skills.

Core examples rule:

```text
Examples test usability.
They do not authorize execution.
They do not add new doctrine beyond the active rite policy.
```

## Relationship to the Governance College

The Governance College separates responsibilities of judgment.

A rite may temporarily involve several role viewpoints from the college, but it does not make them agents and does not create a runtime conversation.

A role keeps its responsibility.

A rite defines trigger, review sequence, outputs, anti-triggers and evidence expectations.

## Relationship to Agora

Agora is a visible deliberation space.

A rite is a bounded procedure.

Agora may receive the output of a rite, request a rite, or expose unresolved discord after a rite.

A rite must not replace Agora when human legitimacy, values, professional preference or explicit user arbitration are required.

Useful distinction:

```text
Agora deliberates.
Rites structure method.
ZEUS arbitrates status.
The human decides.
```

## Distilled external methods

Pantheon may distill narrow techniques from external method repositories without importing their runtime, naming, authority model or whole skill catalogue.

Distillation is allowed only when the technique strengthens an existing owner and does not create a duplicate Role, Rite or governed Space.

Current mapping for unknown-finding techniques:

```text
blindspot pass
-> enriches PREMISSES_CACHEES before commitment
-> enriches AUTOCRITIQUE_CONTRADICTOIRE after a convincing candidate exists

test blindspots
-> enriches AUTOCRITIQUE_CONTRADICTOIRE
-> asks what passing checks do not establish

assumption test
-> reusable bounded Method / Skill
-> may be requested from PREMISSES_CACHEES or AUTOCRITIQUE_CONTRADICTOIRE
-> result must remain supported-within-scope, refuted or inconclusive

reference hunt
-> ARGOS-aligned research Method / Skill
-> source found != Evidence admitted

context audit
-> convergence/maintenance Method for instruction surfaces
-> not a new Role or Rite by default
```

These techniques do not self-trigger Rites and do not inherit Pantheon authority.
A runtime skill implementing one of them remains a candidate external execution method under the existing Task Contract, capability and skill-admission owners.

## Initial rite catalogue

- `RITE_INVOCATION_POLICY.md` - define invocation, budget, anti-chaining, closure and Rite Review Card policy.
- `RITE_ANTI_PATTERNS.md` - preserve known rite misuse patterns and corrective boundaries.
- `RITE_EXIT_CRITERIA_AND_CONFLICTS.md` - define closure criteria, rite conflicts and User Decision Gate escalation conditions.
- `RITE_SELECTION_MATRIX.md` - help choose a candidate rite from a governance symptom without triggering it automatically.
- `RITE_TRIGGER_CATALOGUE.md` - candidate: express the front edge of the rites as a deterministic `signal -> metathought question` catalogue (owned spec, served read-only externally, question never verdict).
- `RITE_MODES.md` - help choose rite intensity without creating runtime modes.
- `RITE_EXAMPLES.md` - provide fictional usage examples without adding execution authority.
- `RITE_DIVERGENCE_CONTROLEE.md` - widen options before convergence while separating generation from critique.
- `AUTOCRITIQUE_CONTRADICTOIRE.md` - review a draft or candidate as if it came from a third party.
- `CONCORDANCE_DES_SOURCES.md` - compare source support, freshness and contradictions before relying on a claim.
- `PREMISSES_CACHEES.md` - expose hidden assumptions before planning or deciding.
- `REFONDATION_DE_SESSION.md` - reset a polluted session into a new bounded Task Contract.

## External inspiration boundary

The first version of `RITE_DIVERGENCE_CONTROLEE.md` is inspired by the external divergent-ideation pattern from `uditakhourii/adhd`.

Pantheon distills the method only.

Pantheon does not import the package.

Pantheon does not adopt its name as public doctrine.

Pantheon does not install a skill, runtime, provider integration, scheduler or agent loop.

## Rite lifecycle

A rite may be:

```text
proposed
active
under_review
deprecated
rejected
superseded
```

A rite can become active doctrine only when it preserves the core boundary:

```text
method without runtime
coordination without agent multiplication
review without auto-approval
evidence without hidden chain-of-thought
memory candidate without automatic promotion
```

## ZEUS closure statuses

Every invoked rite must close with a ZEUS status.

A rite cannot remain open by implication.

Valid statuses:

```text
rite_not_needed
rite_allowed
rite_completed_as_draft
rite_completed_with_reserve
rite_blocked
rite_escalated_to_user
task_split_required
rite_superseded
```

These are procedure statuses.

They are not truth statuses, approval statuses or memory statuses.

## Minimal rite structure

Each rite should define:

```text
id
status
purpose
triggers
anti-triggers
role viewpoints involved
inputs
governance sequence
outputs
Evidence Pack impact
User Decision Gate impact
memory impact
failure modes
forbidden drift
```

## Rite Review Card

When a rite affects output legitimacy, delivery posture, memory posture or user arbitration, it should produce a Rite Review Card.

A Rite Review Card is not a schema.

It is a documentation format.

Recommended format:

```text
rite_id:
trigger_reason:
proposed_by:
authorized_by:
role_viewpoints_involved:
inputs_considered:
outputs_retained:
tensions_exposed:
blocked_claims:
ZEUS_status:
User_Decision_Gate:
Evidence_Pack_impact:
memory_impact:
next_allowed_action:
```

Forbidden content:

- hidden chain-of-thought;
- raw role debate;
- private scratchpad;
- autonomous agent transcript;
- runtime worker trace;
- executable workflow state;
- automatic approval event;
- automatic memory promotion event.

## Runtime-client projection boundary

Optional runtime clients may expose interaction around a rite but do not own rite status, authority or approval. Hermes WebUI is one optional/proposed client if separately selected and qualified.

Pantheon Cockpit may project governed Rite Review Cards, tensions, status and linked User Decision Gates.

```text
Hermes WebUI available != Hermes WebUI selected
client selected != authority transfer
projection != persistence
rite visible != rite authorized
```

## Forbidden drift

Rites must never become:

- autonomous workflows;
- hidden role debates;
- agent loops;
- tool dispatch plans;
- schedulers;
- queues;
- executable DAGs;
- LangGraph runtime substitutes;
- approval callbacks;
- memory promotion pipelines;
- client-specific governance plugins;
- Hermes skill auto-installers.

If a rite becomes executable by Pantheon itself, governance drift has occurred.

## Final rule

A rite is a governed method.

It can organize role viewpoints.

It cannot execute work.

It cannot approve itself.

It cannot make memory canonical.
