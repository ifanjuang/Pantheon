# Hermes Template Design

Status: candidate template only — owner index; no runtime authority.

`templates/hermes/` versions declarative contracts consumed by an external Hermes installation. This document only indexes ownership and evolution checks. Canonical governance remains in its existing owners.

## Entry surfaces

```text
README.md   orientation and template inventory
DESIGN.md   owner map and evolution checklist
AGENTS.md   external runtime identity adapter
SKILLS.md   collection-level skill contract
CLAUDE.md   optional Claude-specific work adapter
```

Individual instructions remain in `skills/<skill>/SKILL.md`; profiles remain under `hermes/profiles/`.

## Repository responsibilities

- `Pantheon governance`: doctrine, schemas, governed identities, statuses, Evidence rules, approvals, Capability Slots and declarative templates in `Pantheon-Next`.
- `Pantheon implementation`: candidate PostgreSQL/API/Cockpit implementation, projections and adapters under `implementation/`.
- Hermes: external execution, tools, models and runtime mechanics.
- Cockpit/OpenWebUI: user projection and decision surfaces.
- Human: consequential decisions.

The former `pantheon-mvp` repository name is historical provenance for the imported implementation, not an active owner or source path.

Executable Pantheon adapter code remains outside this template directory under `implementation/`, governed by `docs/governance/NEXT_MVP_REPOSITORY_PLACEMENT.md`; external Hermes runtime ownership and execution remain separate under `docs/governance/HERMES_INTEGRATION.md`.

## Owner map

- Pantheon Roles: `docs/governance/AGENTS.md`.
- Repository work rules: root `CLAUDE.md`.
- Pantheon implementation placement: `docs/governance/NEXT_MVP_REPOSITORY_PLACEMENT.md`.
- External Hermes execution boundary: `docs/governance/HERMES_INTEGRATION.md`.
- Agent adapter: `templates/hermes/AGENTS.md`.
- Skill collection contract: `templates/hermes/SKILLS.md`.
- Individual skill behavior: `templates/hermes/skills/*/SKILL.md`.
- Managed profile supplements: `templates/hermes/profiles/*/SOUL.append.md`.
- Handoff and return shapes: `templates/hermes/handoffs/` and `templates/hermes/returns/`.
- Connection candidates: `templates/hermes/connection/`.
- Reproducible external composition contract: `templates/hermes/distribution/`.

The distribution lock pins independently owned components and required acceptance checks. It is an implementation/deployment composition record, not a new governed identity, installer, activation object or task authorization.

This file does not redefine Context, Trace, Knowledge, Claim, Evidence, ChangeCandidate, Competence or Capability Slot. A Runtime Profile is only an external runtime configuration description; it is not a governed identity, an authority source, an approval object or an authorization grant. Runtime Observation remains a factual observation envelope subject to provenance and review.

## Evolution checklist

Review the template when:

- Pantheon governance changes Role, Claim, Evidence, ChangeCandidate, Capability Slot, status or hosting semantics;
- `implementation/` changes Hermes handoff/admission/callback routes, Cockpit projections, ProjectClaim/ChangeCandidate behavior or adapter contracts;
- external Hermes changes profile loading, skill loading, transport, tools, memory, automation, sub-agent or approval behavior.

Check for:

- removed internal `/v1` routes or generation-labelled active identities;
- external protocols whose upstream versioning must be preserved;
- stale distribution component paths or source pins;
- missing composed acceptance checks after adapter changes;
- provenance, base revision, diff, idempotence and human-review gates;
- accidental promotion of installation, health, compatibility, activation, runtime success, retrieval or a selected Runtime Profile into authority or Evidence.

Any Runtime Profile reference must remain descriptive and replaceable. It may report intended runtime configuration or compatibility assumptions, but cannot establish adoption, safety, activation, task authorization or Pantheon authority. Runtime Observation may report observed facts, never conclusions beyond its evidence and provenance.

Repository validation can check structure, references and forbidden patterns. It cannot establish external installation health, compatibility, safety, authorization, result acceptance or Evidence admission.
