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
7. a work posture is shown only when the governed method actually selects it;
8. finish with a compact result / open-points summary when useful.
```

If the governed method does not select a work posture, do not invent one merely
to satisfy the display format. Never synthesize a Pantheon Role label from runtime prose.

## When to use it

Keep simple requests quiet. For a bounded non-trivial task, normally show one
initial plan, 2-4 meaningful milestones, then a compact final summary. Show more
only when a new material finding, source, contradiction, blocker, responsibility,
approval posture or result actually changes the user's understanding.

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

When a source materially supports or limits a milestone, assign stable task-local
references and reuse them consistently.

```text
[S1] <observed title>
     Indice/révision: <observed value or non identifié>
     Date du document: <observed value or non identifiée>
     Origine: <observed repository/vault/location>
     Page/section: <observed locator when useful>
```

Keep document metadata distinct from ingestion/runtime metadata. A Hindsight
creation/update timestamp is not the document date unless the source contract
explicitly says so.

Every factual claim attributed to another document requires its own `[Sx]`
reference before or with that claim. Do not mention a CCTP, DPGF, contract,
estimate or other source as support if only a different source has been cited.

Include metadata only when it is present in the source or returned by the
qualified retrieval path. Never infer a missing title, date, index, revision,
author or version from context.

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

## Quantitative consistency

Before a quantitative conclusion, reconcile every displayed component that
materially affects that conclusion.

State the perimeter explicitly, for example:

```text
travaux seuls
travaux + aléas
travaux + aléas + études
```

Show the formula when inclusion/exclusion changes the answer. Keep source values
separate from derived arithmetic and label rounded values as derived.

Keep monetary bases coherent. Label each component `HT`, `TVA`, `TTC` or
`non identifié` from the source or from an explicit derivation. Never add an HT
amount directly to a TTC amount. When a percentage such as an aléa is applied,
show the percentage, its base and whether that base is HT or TTC before naming
the derived amount.

If two reasonable perimeters produce different conclusions, do not choose one
silently. Report both and identify the missing scope decision.

Before recommending an envelope as `prudente`, `haute` or as covering identified
uncertainties, reconcile the scenario it claims to cover. Its upper bound must
not be lower than a displayed high-case total that is inside that stated
perimeter. If the recommendation intentionally excludes a component, state that
exclusion beside the recommendation.

Any allowance, market range, contingency percentage or impact amount that is not
present in an identified source must be labelled as an assumption or derived
estimate. Do not present it at the same evidentiary level as a sourced amount.

```text
component listed separately != component excluded from global budget
rounded total != source-stated total
calculation correct != contractual perimeter established
HT amount + TTC amount != coherent total
reasonable allowance != sourced project fact
prudence label != reconciled high-case coverage
```

## Progressive delivery

When the active Hermes/channel surface supports safe interim assistant messages,
publish meaningful milestones progressively. Otherwise preserve the same
structure in a compact final response; do not introduce a second transport
mechanism solely for progress display.

Transport-specific formatting may vary across Telegram, Discord, WhatsApp,
WebUI or another admitted surface. Governance meaning must not depend on message
editing, color or another channel-specific feature.

## Final summary

When useful, close non-trivial work with only the categories actually present:

```text
Plan / réalisation
✓ ...
✕ ...

Sources
[S1] ...
[S2] ...

Méthodes
- ...

Skills utilisés
- ...

Outils utilisés
- ...

Parcours responsabilité / exécution
... only when actually established/observed ...

Résultat
...

Ouvert
...
```

Do not manufacture a complete-looking path, source set, method or tool list.
Do not claim that no data was extrapolated when the answer contains derived
rounding, arithmetic or interpretation; identify those elements as derived.

## Professional source-verification acceptance shape

For a real professional source-verification task, use only corpus facts actually
retrieved during that run, regardless of the dossier or deliverable type:

```text
Plan
Objectif: vérifier l'affirmation demandée à partir des pièces applicables.

Sources
[S1] <document réel> — <indice observé> — <date observée/non identifiée>
[S2] <second document réel if actually used>

Action: identifier la pièce pertinente.
Raison: l'affirmation nécessite une source identifiable.
But: déterminer le document applicable, son indice, sa date et son périmètre.
Outil: <outil réellement invoqué>
Skill: <skill réellement utilisé>
Résultat: <constat réellement supporté>.

Calcul dérivé, si nécessaire
Périmètre: <explicit>
Base monétaire: <HT/TTC/non identifié>
Formule: <displayed source components>
Résultat calculé: <derived result>
Hypothèses: <none or explicitly labelled derived assumptions>
```

If a work posture has actually been selected, it may be shown around the same
factual content. Otherwise keep the direct Hermes presentation. Do not invent
Pantheon Role theatre.

This is a general presentation shape, not a dossier-specific workflow or a claim
about any real corpus.

## Final invariant

```text
Show what changed, why it matters, what was sought and what was observed.
Cite only real sources and observed metadata.
Give every supporting document its own source reference.
Name only methods, skills and tools actually selected or used.
Reconcile quantitative components and monetary bases before drawing a quantitative conclusion.
Make materially changed next steps explicit without inventing dispatch or Pantheon Role state.
Never expose hidden reasoning and never turn presentation into authority.
```
