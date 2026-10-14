# Claude Adapter for Hermes

Status: candidate template only — assistant-specific adapter.

This file is optional and applies only to Claude-based development or review of the Hermes template. It is subordinate to the repository-root `CLAUDE.md` and to canonical Pantheon governance. It is not a universal Hermes configuration and grants no runtime, model, provider, tool or task authority.

## Read order

Before significant work, read:

1. repository-root `CLAUDE.md`;
2. relevant canonical governance owners;
3. `templates/hermes/DESIGN.md`;
4. the exact agent, skill, handoff and return surfaces involved;
5. current `Pantheon-Next/main`, the relevant `implementation/` consumers and open PRs.

## Working rules

- Keep `Pantheon governance` as semantic governance owner, `Pantheon implementation` as the bounded implementation responsibility under `implementation/`, Hermes as external runtime, Cockpit/OpenWebUI as projection surface and the human as consequential decision-maker.
- Treat the former `pantheon-mvp` name only as historical provenance for imported commits, PRs and issues; do not use it as an active implementation owner or source path.
- Reuse Context, Trace, Knowledge, Claim, Evidence, ChangeCandidate, Competence and Capability Slot before adding a concept.
- Prefer consolidation over a new layer.
- Distinguish facts, interpretation, recommendation and uncertainty.
- Do not infer permission to merge, publish, transmit or execute from technical feasibility.

For template evolution, reject stale internal `/v1` routes and generation-labelled active identities while preserving genuinely versioned upstream protocols. Consequential ChangeCandidates retain provenance, base revision, diff, idempotence and human review.

A Runtime Profile is a descriptive, replaceable external-runtime configuration candidate. It must never be treated as a Pantheon identity, source of authority, approval, activation or task authorization. Runtime Observation may report factual runtime state only with provenance, uncertainty and bounded interpretation.

A loaded `SKILL.md` does not install tools, adopt dependencies, activate a Capability Slot or authorize a task. Executable code remains outside `templates/hermes/`: co-located Pantheon/Hermes adapters belong under the bounded `implementation/` responsibility defined by `docs/governance/NEXT_MVP_REPOSITORY_PLACEMENT.md`, while Hermes runtime code and execution remain external under `docs/governance/HERMES_INTEGRATION.md`.

Record material interventions in the pull-request description. Report incomplete work as incomplete; do not fabricate health, acceptance, approval or Evidence.