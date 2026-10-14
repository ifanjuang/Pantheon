# CLAUDE.md

This repository is Pantheon Next.

## Doctrine

Hermes Web/dashboard exposes chat, sessions and runtime controls.
Hermes Agent executes externally.
Pantheon Next governs consequential state, Evidence, decisions and professional status.
Pantheon Cockpit projects governed Cards, navigation, decisions and status.

Pantheon Next is a governance, documentation and policy system. Its governance core must not become an autonomous agent runtime.

The repository may host bounded surfaces that consume the governance core — never the reverse (see Repository structure).

## Repository structure (monorepo with hard boundaries)

Pantheon Next is a monorepo with explicit internal responsibility boundaries. Its zones are:

- the governance core — doctrine, canonical schemas, validation contracts and governance status. Its artifacts are pure: no doctrine, schema or governed document gains authority from executable implementation. CI checks under `.github/scripts/` may reuse bounded read-only validators exposed by `mcp-server/` rather than duplicate pure validation logic; that is validation-time reuse, not a doctrinal dependency, and it never executes professional work;
- `mcp-server/` — the bounded read-only policy / validation surface. It serves and validates governance data and read-only verifications, returning verdicts as data. It is a connection point for external runtimes and exposure surfaces. It verifies; it does not execute a capability and is not the UI;
- `implementation/` — the co-located executable candidate implementation imported from the former `ifanjuang/pantheon-mvp` repository. It contains PostgreSQL persistence, APIs, Cockpit projections and bounded integration adapters. It may consume governed contracts. It does not own Pantheon doctrine, approve effects, admit Evidence or become authoritative because it shares the repository;
- external runtimes and deployments — Hermes Agent, selected external services and private deployment/storage surfaces remain separately installed, activated and governed. Repository presence is not deployment.

The authority/dependency direction is one-way:

```text
canonical governance surfaces
        ↓ consumed by
mcp-server/ and implementation/
        ↓ integrated with
external runtimes / private deployment
```

Reverse authority transfer is forbidden. `implementation/` may demonstrate a better implementation and motivate a reviewed governance change, but executable code does not silently redefine doctrine or schemas.

Repository placement follows `docs/governance/NEXT_MVP_REPOSITORY_PLACEMENT.md`. The former sibling-repository decision is superseded: implementation is now co-located under `implementation/`, while responsibility and authority remain separated.

## Non-negotiable boundaries

The governance core must not recreate:

- Execution Engine;
- Agent Runtime;
- Tool Runtime;
- LLM Provider Router;
- internal scheduler;
- central LangGraph runtime;
- message bus;
- mandatory agent queue;
- auto-promoted memory;
- self-evolution auto-merge;
- free plugin manager;
- hidden workflow runtime.

The in-repo zones are bounded, not free:

- `mcp-server/` stays read-only / validation / candidate-preparation, centered on governance policy and verification. It does not execute a capability, route a provider, send externally, schedule, queue or promote memory, and it does not become the UI;
- `implementation/` may contain executable candidate behavior, persistence, product projections and integration adapters. Its execution success is implementation evidence only. It may not bypass Task Contracts, policy gates, approval boundaries, Evidence admission or governed identity rules;
- `docs/assets/pantheon-control/` stays an orientation point plus a closed inventory of validation-support artifacts. It is not a second product Cockpit, fallback UI, runtime probe or project-data surface. The executable candidate Cockpit belongs under `implementation/`;
- a future additional executable surface must converge on an existing implementation responsibility or obtain a reviewed placement decision. Do not create a parallel runtime path merely because the monorepo permits another directory.

A consequential effect still routes through the governance check (the chokepoint). No module or implementation path bypasses it.

## Core non-equivalences

```text
repository co-location != authority transfer
implementation success != authorization
schema conformance != professional approval
projection != persistence
workspace folder != governed identity
retrieved data != truth
memory != Evidence
installed != approved
healthy != safe
```

## Work rules

Before proposing or changing governance or implementation architecture, read the relevant current source of truth first, inspect current `main`, recent commits, branches, PRs, issues, schemas, tests and registries, and check whether parallel work already covers the responsibility.

Before proposing or changing workspace organization, Obsidian/vault layout, project folders, `Affaires`, `Connaissances`, folder manifests, Hermes Obsidian skills, optional second-brain behavior or Hermes-assisted reclassification, read the current owners together:

- `docs/domain-packs/architecture/DOCUMENT_AND_KNOWLEDGE_ORGANIZATION.md` for the optional architecture-agency organization profile;
- `docs/architecture/WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md` for manifestability and local workspace-package health;
- `docs/governance/PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md` for Cockpit Space projection;
- `docs/governance/OBSIDIAN_HINDSIGHT_WORKSPACE_MODEL.md` for the qualified external workspace/retrieval composition and the optional Hermes Obsidian skill / second-brain boundary.

Preserve arbitrary filesystem organization as usable. A recommended folder convention is not mandatory, a path is not governed identity, a missing manifest is not an error by default, a Cockpit Space is not a required physical root folder, an Obsidian/second-brain skill is not a workspace prerequisite, and a Hermes classification proposal is not authorization to move or rename files.

Before creating a new Markdown governance document under `docs/governance/`, first verify that no existing canonical, active or candidate owner can absorb the responsibility. Prefer updating, merging, promoting or archiving existing doctrine. A new `candidate support doctrine` document must name a genuinely distinct responsibility, identify its relationship to the existing concept/authority owner and state its intended convergence or retirement path. Generated reports and required conformance fixtures are intervention or validation artifacts, not doctrine expansion.

Before creating a new executable component under `implementation/`, verify that no existing component, adapter, projection or service can absorb the responsibility. Prefer convergence over parallel paths.

Before significant parallel work, announce the repository paths that may be changed. A rename announces both the old and new path. When two active announcements overlap, divide or sequence the shared paths before modification.

The announcement is a coordination signal only. It is not a lock, does not grant authority and does not reserve a responsibility.

Markdown governance documents are authoritative over code unless code exposes a demonstrably better implementation. In that case, propose the governance/contract reconciliation explicitly; do not silently treat code as doctrine.

Do not claim that a component is implemented if it is only documented.

Always distinguish:

- implemented;
- documented but not implemented;
- implemented but not documented;
- partial;
- obsolete;
- contradictory;
- to verify;
- non implemented.

Use owner documents, schemas/contracts/tests, Git history and pull-request rationale as the default durable trace of repository work. This repository keeps no `ai_logs/`; do not create one. Pre-publication history lives in the private Pantheon-Next archive.

## Runtime policy

Hermes Web/dashboard is the selected chat, sessions and runtime-interaction baseline. Compatible runtime clients remain optional and replaceable; client selection does not transfer Pantheon authority.
Hermes Agent is the external execution runtime.
Pantheon Cockpit is the governed projection surface for Cards, navigation, decisions and status; projection is not authorization or persistence.
Pantheon Next governance surfaces are the governance source of truth.
`implementation/` contains bounded executable candidate implementation.
The human decides what is consequential.

Hermes profiles may produce candidates under Task Contract.
They must not approve, canonize, promote memory, bypass approvals or merge changes.

Client extensions, actions and integration adapters are execution or interaction surfaces only. Repository implementation or client availability does not make them installed, adopted, approved or authorized.

OpenWebUI and Paperless-ngx are refused/retired target integrations with no current target responsibility. Historical references remain provenance only and must not be used to restore them as architecture owners.

PostgreSQL persistence, Cockpit projections and adapters under `implementation/` are implementation responsibilities. Persistence is not Evidence; a projection is not governed identity; successful execution is not authorization.

## Repository migration policy

This repository is the self-contained canonical governance repository and monorepo host for bounded implementation surfaces. Its historical governance predecessor is retired and is not a source dependency.

The former `ifanjuang/pantheon-mvp` repository is the historical source of the implementation imported at cutoff `d960862dd0e23b7003a0f3e4ee0ea630ffc12af9`. After the monorepo migration is admitted, it is not a second active implementation trajectory. Keep it available for historical PR/issue/original-commit references until archival is explicitly reviewed.

Do not reintroduce runtime folders into the governance core. Executable candidate artifacts belong under the existing `implementation/` boundary unless a distinct reviewed responsibility requires another placement.

Do not duplicate Cockpit, persistence, policy enforcement, memory, adapter or schema responsibilities across zones. Temporary compatibility paths created by a future migration must have an explicit retirement path.

The compatibility debt created by the initial `pantheon-mvp` import is closed on active surfaces: committed schema vendoring was removed in favor of canonical root contract consumption, Hermes distribution resolves components from one monorepo root, and Architecture Audit owner identities are responsibility-based (`Pantheon governance` / `Pantheon implementation`). Historical repository names remain valid only where they identify provenance, former PRs/issues or original commits. Do not reintroduce vendored governance snapshots, a second implementation source path or repository-name owner identities.

Real professional data, secrets and environment-specific deployment authority remain outside the public repository.
