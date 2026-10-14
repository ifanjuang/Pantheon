# Hermes Skills Surface

Status: candidate template only — collection-level index.

Authoritative skill instructions remain in `templates/hermes/skills/<skill-name>/SKILL.md`. This file does not duplicate them; it defines the minimum review contract for the collection.

A Hermes skill is bounded execution guidance for an external runtime. It may reference a Pantheon Competence or Capability Slot, but it is not a Role, tool installation, binding activation, task authorization, Evidence or canonical Knowledge.

## Minimum skill contract

Each `SKILL.md` must identify:

- stable purpose and candidate status;
- governing owner or Capability Slot;
- expected inputs and Context assumptions;
- allowed abstract capabilities and prohibited effects;
- return, provenance, trace and uncertainty requirements;
- escalation behavior for contradictions, missing authorization and capability gaps;
- material upstream or runtime-version assumptions.

## Review sequence

Review separately: abstract function, candidate binding, installation, health, compatibility, safety, activation, task authorization and return/Evidence/human gates. No state implies the next.

Skills in this repository stay declarative. Executable Pantheon adapters belong under the bounded `implementation/` responsibility governed by `docs/governance/NEXT_MVP_REPOSITORY_PLACEMENT.md`; Hermes runtime execution remains external under `docs/governance/HERMES_INTEGRATION.md`. Executable scripts, installers, provider routers, queues and schedulers do not belong in this template surface.

When either repository evolves, check active skills for stale routes or names, changed Claim/Evidence/ChangeCandidate semantics, changed capability and authorization gates, and dependencies presented as adopted merely because they are available.

## Context read budget

Instruction and orientation material is a context cost paid by the runtime that actually loads it. Keep that cost observable without turning a byte target into authority.

Repository-side template review therefore uses two bounded rules:

- the top-level `templates/hermes/*.md` orientation surface is kept under a small CI review ceiling; the ceiling is a regression ratchet, not a Hermes token limit and not proof that every file is loaded at startup;
- each durable convention has one owner. Other templates reference the owner instead of copying the rule body merely for convenience.

A deployed runtime or adapter that declares a mandatory instruction/read set must qualify the real set separately. Record the exact files, per-file bytes and the runtime-observed token/read behavior when measurable. Do not concatenate several mandatory files into one read merely to save tool calls when the runtime can silently truncate outputs; read them separately or use an equivalent complete-read mechanism.

If the selected runtime/read API can silently truncate a mandatory file, qualification must include a complete-read check such as an end sentinel, returned byte count, digest, or another deterministic equivalent supported by that runtime. Absence of complete-read proof is a runtime limitation to surface, not permission to assume the tail was read.

```text
repository size check != deployed runtime observation
file present != file read completely
context loaded != instruction authorized
smaller prompt != permission to drop governance
rule duplicated != rule reinforced
```

When reducing the read set, remove duplication and move explanatory history off the mandatory path before weakening live constraints. Verify the inventory of retained rules/references after the cut; a smaller file is not an improvement if a required boundary disappeared.

Runtime Profile and Runtime Observation support described by open PRs remains candidate until those PRs merge. A textual review is not runtime acceptance against an exact external installation.
