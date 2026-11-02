---
name: pantheon-governed-method
description: "Use for non-trivial governed work that must be framed, sourced, composed, tested and assigned an explicit readiness status. Coordinates existing Hermes skills and read-only Pantheon policy tools proportionately; it is not a workflow engine or a domain-specific procedure."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  governed_by: docs/governance/GOVERNED_METHOD_STANDARD.md
  policy_contract: mcp-server/docs/HERMES_INTEGRATION_CONTRACT.md
  related_skills: [pantheon-request-intake, pantheon-activity-projection, architectural-issue-framing]
  upstream: "agentskills.io SKILL.md standard; exact Hermes runtime compatibility must be qualified before admission"
---

# Pantheon governed method

General coordination adapter for non-trivial professional work. It selects the
smallest justified method and returns a bounded, sourced readiness statement.
It never derives authority from a project name, document label, installed tool
or model confidence.

```text
viewpoint != autonomous agent
retrieved != true
candidate complete != approved or transmitted
```

## Core movement

Use only the movements that add value; loop back when a material source,
contradiction, scope, risk or completion condition changes.

```text
1. Frame / Cadrer
2. Admit / Admettre
3. Qualify / Qualifier
4. Compose / Composer
5. Produce Candidate / Produire candidat
6. Test / Éprouver
7. Status / Statuer
```

Classify by material conditions, not by object names. A normal composition has
at most one primary method, one guardrail method and one verification method.
Pantheon governs; Hermes executes; the human decides consequential effects.

## Load only what the task needs

- For every non-trivial task, read [references/interaction.md](references/interaction.md)
  and apply its visible plan and milestone rules. For agency project facts or
  documents, also load `project-context`; for non-trivial chat work, load and
  apply `pantheon-activity-projection`. Do this before the first material
  retrieval or source call. Simple, bounded factual questions stay lightweight.
- Read [references/source-review.md](references/source-review.md) when factual
  claims depend on workspace sources, candidates must be compared, completeness
  must be established, or a source-review child may be useful.
- Read the `pantheon-distributed-work` skill when the task may benefit from
  bounded parallel readers, persistent specialist Bots, or durable Kanban
  coordination. It selects a runtime work shape; it does not create a profile
  or activate a Pantheon Role or Rite.
- Read [references/execution.md](references/execution.md) for consequential
  policy routing, Task Contracts, Context Packs, production, verification,
  source-preflight receipts or final readiness.

Do not load every reference merely because the skill was selected. For a simple
bounded factual review, `source-review.md` plus the relevant portions of
`execution.md` are normally sufficient.

Use a policy route once for the materially unchanged request. If its `next_action`
requires a changed request candidate, revise the candidate once using the returned
conditions and route that changed candidate before source discovery; do not silently
skip the instruction or repeat an unchanged route. When its returned object selects
Role viewpoints, Rite requirements or doctrine keys, follow the returned next action
as applicable, consult only the selected doctrine needed for the task, and use those
viewpoints in the analysis. Surface selected viewpoints in the visible plan; a Role
is an analytical lens, not a separate agent or independent opinion unless a real
worker was dispatched and returned. Name a Rite only after its prescribed procedure
was actually applied. If the route returns none, state briefly that no Role/Rite was
selected when that explains their absence; never invent one. Call Task Contract,
Evidence Pack, Context Pack or validation tools only when their returned object
will be used by the next step or a governing rule requires it; their availability
alone is not a reason to call them. A bounded review can keep a compact source
receipt without creating unused skeletons.

## Route to one domain owner when justified

For a material agency project task with competing source versions or many possible
inputs, use the existing `project-context` skill for bounded source selection
before choosing the specific reasoning owner. For any project-specific factual
answer, comparison or professional conclusion based on project records, load
`project-context` even when the exact document is already known; it chooses whether
memory alone is enough or direct source inspection is needed. It adds no separate agent/profile,
Context Pack authority or mandatory workflow graph. Do not preload all domain
Skills merely because a project has several document types.

When the user explicitly asks for an architect's opinion, project implications,
sufficiency or the points that matter in a document or situation, use
`architectural-issue-framing` as a short framing step before selecting any
deeper domain owner. It identifies the principal project issue and priorities;
it does not replace the owner skill or turn a simple factual question into a
full review.

Select by the reasoning required, not by the requested file format:

- `construction-cost-review` only when the requested work requires economic
  analysis: scope/lot coverage, exclusions, variants, normalization, tax-basis
  reconciliation or price comparability. A simple request to recall or extract
  one remembered amount does not activate this review; use `project-context`
  and `vault-search` first, and return qualifying Hindsight memory when
  sufficient;
- `site-report-review` for site observations, prior minutes, photographs,
  decisions, reservations and open-point continuity;
- `administrative-form-review` for CERFA or another filing form whose fields
  must each be supported and uncertainty-preserving;
- `technical-standard-review` for DTU or another technical standard whose
  exact edition, applicability and normative force must be established;
- `construction-schedule-review` for works sequencing, dependencies,
  constraints, milestones, buffers and replanning.

`source-research` owns bounded research. Drafting, reports and correspondence
are production forms: the selected domain owner supplies the supported content,
then `external-commitment-guard` is used when an external effect is possible.
An overall project analysis composes only the owners actually triggered; it is
not a separate catch-all skill. If a required owner is unavailable, mark that
dimension `not_reviewed` instead of improvising expertise.

## Universal stop rules

- Do not widen admitted scope silently.
- Do not turn memory, search hits or filenames into source authority.
- Do not claim a check, role, skill, tool or delegated child that was not used.
- Do not conceal missing coverage, contradictory material or an unreadable
  consequential source.
- Do not transmit, publish, persist canonical memory or cause another external
  effect without the applicable explicit authorization.
- Treat a user deadline as a work budget: reserve time to verify and synthesize,
  stop optional discovery when the budget is used, and return a bounded partial
  result with its remaining gaps. A prompt deadline is not a runtime kill switch.

Finish with the smallest useful result, sources, limits, readiness and next safe
action. Use only: `ready`, `ready_with_limits`, `needs_revision`,
`needs_user_input`, or `blocked`.
