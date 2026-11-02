---
name: pantheon-activity-projection
description: "Project meaningful observable progress from non-trivial Pantheon-governed Hermes work into chat: plan, action/reason/goal, real sources and metadata, methods, skills/tools actually used, result, limits and optional work posture. Presentation only."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  governed_by: docs/governance/CONVERSATION_ACTIVITY_PROJECTION.md
  upstream: "Hermes chat/interim-message presentation convention; exact runtime delivery behavior must be observed before qualification"
---

# Pantheon activity projection

Lightweight presentation adapter for non-trivial governed chat work.

Read [references/complex-presentation.md](references/complex-presentation.md)
when the task needs the full compact presentation shape.

```text
projection != persistence
posture label != Pantheon Role
milestone != runtime dispatch
retrieved source != truth
runtime success != approval
summary rationale != hidden chain-of-thought
derived calculation != source fact
```

## Normative output contract

For non-trivial work, keep the presentation contract small and explicit:

```text
1. one compact initial plan;
2. only meaningful milestones;
3. each milestone uses Action / Raison / But / Résultat when useful;
4. every documentary claim cites its task-local source [Sx];
5. Méthode / Skill / Outil remain separate categories;
6. quantitative conclusions state their perimeter and reconcile displayed components;
7. selected Pantheon viewpoints and required Rites are shown at the relevant
   milestone only when the governed route/method actually returns or selects
   them and the viewpoint/procedure is used;
8. a work posture is shown only when the governed method actually selects it;
9. finish with a compact result / open-points summary when useful.
```

If the governed method does not select a work posture or Pantheon viewpoint, do
not invent one merely to satisfy the display format. Never synthesize a Role
label from runtime prose. A selected viewpoint is an analytical lens, not proof
that a separate god-agent was consulted. Show a Rite only when its actual
procedure was selected and applied; tool availability or a skill load is not
proof that a Rite ran.

## When to use it

Keep simple requests quiet. For a bounded non-trivial task, show one initial plan
before the first material tool call, then a milestone after the first material
retrieval and after any finding that changes the source or next step; finish with
a compact final summary. Usually 2-4 milestones are enough. Show more only when a
new material finding, source, contradiction, blocker, responsibility,
approval posture or result actually changes the user's understanding.

Do not narrate upcoming tool calls, internal search plans, repeated hypotheses or
self-corrections. After the initial objective, report only observable status or
result changes; if nothing material changed, stay quiet.

Do not publish every tool call, retrieval attempt, retry, token, internal branch
or unchanged runtime state.

## Opt-in trace mode

Trace mode is off by default. Turn it on only when the user explicitly asks in
the conversation (for example `mode trace`); turn it off when the user asks
(`mode trace off`). It does not survive a new session.

While trace mode is on, including for simple requests, show one line each time
one of these is actually used, with its observable reason:

```text
⚙ Skill <name> — <reason>
⚙ Outil <name> — <reason>          # one line per distinct tool; repeats as ×N
🔁 Rite <name> — <reason>          # only when its method is actually applied
🧭 Posture <name> — <reason>       # only when the governed method selected it
📁 Espace <label> — <reason>       # when work is scoped to a project/space
◆ Rôle <name> — <reason>           # only from a returned governed object
```

The reason is a half-sentence naming the observable trigger in the request or a
source, for example `question réglementaire, source citée requise`. It is not
private reasoning. A Role line is shown only when a governed object returned to
the run records that Role viewpoint; never derive it from runtime prose. Do not
add a line for a mechanism that was only available.

```text
trace line != runtime receipt
trace mode on != authority
reason shown != private reasoning
```

## Initial plan

Before substantial execution, show the intended path without pretending it is a
guaranteed runtime transcript.

```text
⚙ Hermes · Plan
Objectif: ...
Étapes: ...
Sources attendues: ...        # only when already known
Méthode prévue: ...           # only when already selected/required
Posture: ...                  # optional: only when actually selected
```

For a project or professional task, the plan names the original objective, the
source/memory sequence, and the relevant skills actually selected. After policy
routing, include selected Pantheon viewpoints and any required Rite only when the
returned object records them. If no Role/Rite was returned, say so briefly when
the user expects to see them; never fill the line by guessing. After Hindsight or
another material recall, show what was found, its provenance, what remains missing
or conflicting, and the changed next step. Do not present a planned step as already
performed.

If new evidence materially invalidates the plan, show one short adjustment.

## Milestone grammar

Use the smallest useful subset of:

```text
⚙ Hermes · [semantic function]
Posture: ...                  # optional: Ulysse / Nestor / Dédale / Cassandre when selected
Action: observable work performed or completed
Raison: observable condition making it relevant now
But: concrete result sought
Sources: [S1], [S2] ...       # when material
Méthode: ...                  # only when actually selected/applied
Skill: ...                    # only when actually used
Outil: ...                    # only when actually invoked/observed
Résultat: finding, blocker or changed status
Limite: ...                   # when material
Prochaine étape: ...          # proposal only; never runtime dispatch
```

`Raison` is a concise observable rationale, not private reasoning. Never output a
scratchpad, hidden chain-of-thought, token-level alternatives or invented debate.

## Runtime activity and optional work posture

Pantheon Roles are governance jurisdictions, not runtime identities. Do not use
`Athena`, `Argos`, `Themis`, `Apollo`, `Hephaistos`, `Iris`, `Zeus` or
`Mnemosyne` as labels merely because Hermes is performing analysis, retrieval,
risk review, production, formulation or memory work.

Use `⚙ Hermes` for observable runtime milestones.

When the `pantheon-governed-method` has actually selected a work posture and the
label materially helps the reader, the milestone may add one of:

```text
Posture: Ulysse     # lead / coordination
Posture: Nestor     # investigation / source work
Posture: Dédale     # production / making
Posture: Cassandre  # bounded contradiction / critique
```

A posture is a work shape, not an actor identity and not a governance authority.
Changing posture does not imply a different profile, subagent or execution
strategy. If Hermes actually delegates, starts a subagent, enters a goal loop or
uses a Kanban/task graph, report that only from observed runtime state.

```text
posture selected != Pantheon Role activated
posture changed != profile changed
posture changed != subagent created
next step proposed != next action authorized
runtime tactic observed != governance authority
```

Do not create a universal mapping from task conditions to Pantheon Roles for
presentation. If a Pantheon governance object explicitly records a Role
viewpoint or decision responsibility, that object may be referenced as governed
state; model-authored prose must not manufacture it.

When the governed method selects a complex task flow, the public projection may
show a compact board summary (for example, `3 prêts · 1 en vérification · 1
bloqué`) and only the cards whose status changed. The board is a view over the
Task Contract, not a new authority. Do not show a Kanban surface for a simple
question or expose every internal substep.

```text
draft complete != transmission authorized
milestone complete != whole task approved
posture omitted != missing validation
```

## Source citation and provenance

Use stable task-local `[Sx]` references for material sources and reuse them.
For exact metadata, locator and quantitative presentation, read
`references/complex-presentation.md` when needed. Do not infer missing source
metadata or cite a source that was not observed to support the claim.

```text
source returned != source verified
source name guessed from context != source citation
old source != current source
ingestion timestamp != document date
```

## Method, skill and tool

Keep the categories distinct:

```text
Méthode = governed/task method actually selected and applied
Skill   = Hermes skill actually used in the current task
Outil   = runtime tool, connector or capability actually invoked or observed
```

A concrete MCP function such as `mcp__...__get_document` is an `Outil`, not a
`Méthode`. A human-readable tool name may be followed by the exact function name
when useful for testing.

Availability does not mean use. Do not claim Docling, Hindsight, MCP, Drive,
filesystem access or another mechanism merely because it would have been useful.
If a skill is explicitly preloaded for the task, it may be listed as used; do not
infer unrelated skill use.

Repeated low-level calls may be collapsed into one factual summary only when the
count/result is observable.

Quantitative checks belong to the selected domain method. Keep the presentation
contract concise: label derived results and do not imply a calculation was
reconciled unless it was.

## Progressive delivery

When the active Hermes/channel surface supports safe interim assistant messages,
publish meaningful milestones progressively. Otherwise preserve the same
structure in a compact final response; do not introduce a second transport
mechanism solely for progress display.

Transport-specific formatting may vary across Telegram, Discord, WhatsApp,
WebUI or another admitted surface. Governance meaning must not depend on message
editing, color or another channel-specific feature.

## Final summary

Answer the original question first. Add only useful source references, limits
and readiness. Use a longer presentation shape only when it materially helps;
the selected domain method owns evidence requirements and calculations.

## Final invariant

```text
Show the useful result, its source basis and limits. Name only observed methods,
skills, tools and worker states. Keep presentation separate from authority and
never expose hidden reasoning.
```
