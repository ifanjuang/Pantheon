# Pantheon Next

> Canonical governance repository for AI-assisted professional work.

[Français](README.fr.md) · [Public site](https://ifanjuang.github.io/Pantheon/) · [Status](docs/governance/STATUS.md) · [What runs](docs/governance/WHAT_RUNS.md) · [Governance index](docs/governance/README.md) · [Contributing](CONTRIBUTING.md)

Pantheon Next owns the doctrine, schemas, statuses and gates used to qualify consequential professional work. It governs provenance, Evidence, scope, approvals, claims, ChangeCandidates and Capability Slots.

It is not an agent runtime, scheduler, queue, provider router, installer, plugin manager, memory engine or automatic approval system.

The repository is also the monorepo host for a bounded executable candidate implementation under `implementation/`. Repository co-location does not transfer governance authority to that code.

This public repository started on 2026-10-14 from a reviewed snapshot of the former private Pantheon-Next repository. Real professional data, agency-specific overlays and intervention logs were left out. References written `Pantheon-Next#<n>` point to that private archive, not to issues here.

## Semantic continuity of a project

Pantheon’s current architectural hypothesis is that a useful global understanding of a project should emerge from **several heterogeneous representations converging on the same governed identities and explicit relations**, rather than from flattening every source into one canonical truth.

```text
drawings / sections / IFC / photos / surveys
        -> source representations + claims about the built object
contracts / amendments / quotes / specifications / certificates
        -> commitments and requirements, with their versions and parties
meeting minutes / formal records / site and technical reports
        -> observed facts, reservations and recorded decisions
communications: emails / messaging / letters
        -> requests, answers and agreements, with sender and date
knowledge vault: regulations / standards / templates / methods
        -> reusable references and interpretation cues

all of the above
        -> stable object identities + explicit relations
        -> bounded Context Pack
        -> Hermes
        -> task-relevant project understanding
```

A project may therefore keep several source-backed claims about the same object at the same time, including conflicting ones. The system should preserve their provenance, revision, status and scope so that contradictions and missing context remain visible instead of being silently resolved.

```text
multiple sources aligned != merged truth
same stable object != one canonical source value
retrieved content != truth
Knowledge cue != requirement applicability
message received != commitment or approval
recorded in minutes != validated by the parties
Hermes interpretation != governed claim or decision
```

Repository qualification already protects the bounded multi-owner context composition path. Automated contradiction detection currently covers scalar Claim values only: geometric and relational contradictions are held and shown, but not detected, so an empty conflict list means no scalar value disagrees rather than nothing disagrees. The live cognitive proof that Hermes can turn this semantic superposition into materially better multidisciplinary project understanding remains open under [Pantheon-Next#986](https://github.com/ifanjuang/Pantheon-Next/issues/986). No new ContextGraph, Lens Engine or métier-specific reasoning owner is assumed by this hypothesis.

## Bitemporal claim history

Alongside semantic continuity, the executable candidate under `implementation/`
already separates two time axes for every `ProjectClaim`:

```text
effective_at    = the explicit business-effective start the source asserts
                  (e.g. "this partition is 200mm as of the DCE index of March 2026")
observed_at     = when the assertion or its support was itself observed
knowledge_time  = when the system came to know it (implicit: recording time)
```

A missing `effective_at` is never silently replaced by `observed_at` or by
recording time. Superseding a Claim never rewrites its predecessor; the prior
row remains, and an as-of read can reconstruct **both** what was believed at a
past business time and what was known at a past system time:

```text
business_and_knowledge_as_of      -> what was believed, as it was known then
business_as_of_current_knowledge  -> what was believed then, under everything known since
```

This is implemented, not a hypothesis: `agency_claims.applicable_project_claims_as_of`
enforces it today. The current read of "what was believed" does not yet extend to
"was this contested at the time" — an as-of read is presently silent on
conflicting Claims from the same period; see [Pantheon-Next#1012](https://github.com/ifanjuang/Pantheon-Next/issues/1012).

```text
observed != effective
current knowledge != knowledge at the time
a later Claim != an erased earlier one
reconstructable belief != professional truth
```

## System boundary

| Component | Responsibility |
|---|---|
| **Pantheon Next governance surfaces** | Governance, doctrine, schemas, status and authorization boundaries. |
| **[`implementation/`](implementation/)** | Bounded candidate implementation: PostgreSQL, APIs, Cockpit projections and adapters; imported from the former `pantheon-mvp` repository. |
| **Hermes Agent** | External task execution, skills, tools and runtime bindings. |
| **Hermes Web/dashboard and compatible clients** | Chat, sessions and runtime interaction. Client selection is replaceable and non-authoritative. |
| **Pantheon Cockpit** | Governed Cards, navigation, decisions and status projections. Projection is not authorization or persistence. |
| **Human** | Consequential review, approval, rejection and signature. |

```text
Pantheon governs.
Pantheon Cockpit projects governed state.
Hermes Agent executes externally.
Hermes clients expose runtime interaction.
The human decides what is consequential.
```

![Pantheon Next system map showing work surfaces, direct and assisted paths, Pantheon governance, human decisions, and the authoritative server](docs/assets/diagrams/pantheon-system-map-en.svg)

The direct path does not require Hermes. The assisted path produces observations or candidates; it does not approve them. See the [public landing page](https://ifanjuang.github.io/Pantheon/) for the authority chain and runtime-status honesty map.

OpenWebUI and Paperless-ngx are refused/retired target integrations with no current target responsibility. Historical references remain provenance and do not restore architecture ownership.

## Repository status

Pantheon Next is canonical but still partial. The repository contains governance doctrine, declarative schemas, validation tests, static documentation, a bounded read-only policy/verification package and a separately bounded candidate implementation subtree.

Before relying on an implementation claim, read:

1. [`STATUS.md`](docs/governance/STATUS.md) — current posture and active exceptions.
2. [`WHAT_RUNS.md`](docs/governance/WHAT_RUNS.md) — what runs, what is static, partial or absent.
3. [`AUTHORITY_INDEX.md`](docs/governance/AUTHORITY_INDEX.md) — authority classes and promotion rules.
4. [`MODULES.md`](docs/governance/MODULES.md) — ownership and runtime boundaries by area.

## Development

The repository root is a governance and documentation workspace. It is intentionally **not** an installable Python package.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

`mcp-server/` remains the bounded governance-side Python distribution:

```bash
python -m pip install -e "mcp-server/.[test]"
python -m unittest discover -s mcp-server/tests -v
```

The install is editable, matching what Governance CI runs. A non-editable
install resolves `pantheon_mcp` from a copy in `site-packages`, so the suite
silently tests a snapshot rather than the working tree.

`implementation/` is a separate Python project containing the executable candidate implementation imported from `pantheon-mvp`:

```bash
python -m pip install -e "implementation[test]"
```

The two project boundaries do not make the repository root distributable and do not collapse governance into execution.

`VERSION` is the governance repository checkpoint version. `CHANGELOG.md`, `mcp-server/` package metadata and release tags must remain aligned unless a reviewed release contract states otherwise.

## Repository map

| Path | Purpose |
|---|---|
| [`docs/governance/`](docs/governance/) | Canonical doctrine, authority, status and boundaries. |
| [`schemas/`](schemas/) | Governed structural contracts. |
| [`tests/`](tests/) | Repository validation and consistency checks. |
| [`mcp-server/`](mcp-server/) | Read-only policy and verification projections. |
| [`implementation/`](implementation/) | Executable candidate implementation; co-located but not a governance authority. |
| [`hermes/profiles/`](hermes/profiles/) | Candidate Hermes profile templates; not installed runtime. |
| [`docs/assets/`](docs/assets/) | Static pages and prototypes; not product availability. |

## Contribution rules

Before significant work, read the active repository documents and open PRs. The repository overrides older prompts and historical plans.

Minimum read path:

```text
docs/governance/STATUS.md
docs/governance/WHAT_RUNS.md
docs/governance/AUTHORITY_INDEX.md
docs/governance/MODULES.md
docs/governance/README.md
CONTRIBUTING.md
```

Changes to schemas, tests, CI, Docker, operations, platform, `mcp-server/` or `implementation/` require protected review. A candidate becomes authoritative only through explicit promotion with a referenced schema, test, verified observation or dated human decision.

## Invariants

```text
installed != approved
healthy != safe
runtime_success != Evidence
retrieved != truth
binding_selected != dependency_adopted
activated != task_authorized
UI status != authorization
repository co-location != authority transfer
```

## License

MIT — see [`LICENSE`](LICENSE).

Copyright © 2026 IFJ Architecture.
