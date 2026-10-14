# What Runs

Status: active support note — repository runtime-status map — implemented as documentation.
Boundary profile: active_support_doctrine.

Date: 2026-10-10 (repository review; not a live host observation)

This file distinguishes repository implementation, external observations, target selection and production adoption. It creates no runtime behavior or authorization.

The authoritative distinction vocabulary is in `NON_EQUIVALENCE_RULES.md`; this document records current implementation status without reproducing that rule list.

## Runs or exists in this repository

| Area | Current status | Meaning / boundary |
|---|---|---|
| Governance/documentation corpus | runs as repository content | Markdown doctrine, support documents, references and logs exist. Documentation does not execute work. |
| GitHub Pages/static assets | static documentation/prototypes | Public/static pages may explain or demonstrate concepts; static publication is not product/runtime availability. |
| Governance and implementation CI | implemented read-only | Repository checks/tests can fail closed on structural/contracts regressions. Green CI is not adoption, approval or professional validation. |
| `mcp-server/` | implemented read-only / partial | Shared Pantheon policy/verification service with bounded consultation/preflight/decision-validation surfaces. It does not execute Hermes work, send, schedule, install, route providers or promote memory. |
| `implementation/` | executable candidate implementation / co-located / not adopted | Co-located implementation contains persistence, APIs, Cockpit and Hermes seams. Co-location does not grant governance authority or production activation. |
| Pantheon Cockpit under `implementation/mvp_vertical/cockpit/` | executable candidate / tested / not adopted | Registry-backed navigation, Card projection/renderer and bounded product projections exist. The Cockpit is not a second general-purpose Hermes chat frontend. |
| Project-platform Workspace (`AFFAIRES`) | executable candidate / single-root NAS catalogue / not adopted | One mounted-NAS producer owns ingestion and its reconstructible SQLite projection; `ARCHIVES/PROJET` is not a Workspace source. Live write admission and restart/move behavior remain to qualify under Pantheon-Next#1156/#660. |
| Catalog/contracts | declarative / CI-checked / to verify per object | Capability/resource/binding/decision candidate records exist. A capability may remain intentionally unbound; a catalog record is not a live registry, installer or authorization. |
| Architecture Project Understanding validation | implemented read-only / partial | Candidate structures can be validated where schemas and checkers exist. Schema validity does not canonize professional state. |
| Hermes native capability observation | optional CLI read-only probe merged in Pantheon-Next#1169 / local usage unverified | `deployment/ubuntu/observe-hermes-runtime --capabilities` observes a configured container/profile without enabling tools; CLI toolset selection is not proof of runtime usability. |

## External/runtime surfaces

| Area | Current status | Meaning / boundary |
|---|---|---|
| Hermes Agent | external execution runtime / target deployment state must be observed separately | Hermes owns runtime interaction/execution capabilities. Pantheon governs consequential status and admission boundaries; repository code does not prove target enforcement. |
| Hermes Web/dashboard | selected interaction baseline | Current target client for chat, sessions and runtime controls. Client operation does not create Pantheon governance state. |
| `willscott-v2/hermes-mobile-pwa` | external client candidate / compatible by source review / not selected or installed by this repo | Thin mobile/PWA client using Hermes dashboard REST/WebSocket/auth surfaces. Replaceable client only; deployment/auth/network posture remains separate. |
| Project-platform NAS / AFFAIRES | selected professional source residency / external storage | Source bytes remain on NAS; project-catalogue availability and identity are distinct. `ARCHIVES/PROJET` is outside the selected Workspace source route. A repository-defined mount does not establish live health or admission. |
| Obsidian workspace | historically qualified optional workspace / not selected for productive AFFAIRES | Optional human Markdown tooling and historical capability evidence only. It does not define AFFAIRES synchronization or ingestion. |
| Hindsight | selected derived-memory/index candidate / prior bounded evidence / live qualification open | The AFFAIRES producer path exists, while durable runtime behavior, recovery and exact deployed exposure remain under Pantheon-Next#659. Memory/retrieval does not become truth or Evidence. |

## Implemented/qualified candidate paths not proven in production

| Area | Current status | Remaining proof |
|---|---|---|
| Hermes policy/PEP integration | co-located candidate / internal decision-client assembly exists / target enforcement not established | The Cockpit can assemble the real Pantheon decision client for one internal consequential Knowledge path. This does not establish mandatory invocation in the selected Hermes/runtime deployment. Demonstrate the target-runtime boundary, authenticated/qualified decision references and actual deployment configuration separately. |
| Internal consequential-write chokepoint | implemented candidate, production enforcement unverified | The inventory reviews 92 entry points and records their per-owner PEP wiring or local repair. Required policy-client injection is explicit in supported write compositions, and effect identity/scope/content are rebound by their implementation owners. See `implementation/GOVERNANCE_STATUS.md`, `HERMES_INTEGRATION.md`, the mutation inventory and their tests for exact behavior. Live PDP configuration, issuer authentication and deployed effect enforcement remain unverified; a valid decision or returned receipt does not demonstrate a committed effect. |
| Direct AFFAIRES Workspace route | executable candidate / source-card-index architecture implemented | Pantheon-Next#660 remains open for real mounted-NAS event ordering, restart/network convergence and proof that exactly one productive producer owns the route. |
| Hindsight AFFAIRES producer | executable candidate / bounded | Pantheon-Next#659 remains open for exact deployed runtime identity/exposure, producer↔Hindsight behavior, restart/outage/restore, bank isolation and backup/restore. |
| Hindsight memory reconciliation | implemented transient candidate / no governed write | Pantheon-Next#1145 repaired the dedicated Hermes-profile qualification helper on main. Configured still does not mean activated, runtime observation does not authorize a task, and the candidate is not Evidence. |
| Pantheon Cockpit adoption | executable candidate / not adopted | Live deployment, data bindings and operational acceptance remain separate decisions. |
| Hermes external dashboard/plugin helpers | existing templates and candidates where present | Installation/enablement and live target state must be observed externally. |


The signed Knowledge UPDATE path now has an explicit top-level PostgreSQL transaction (Pantheon-Next#1170); its regression test demonstrates persisted revision and replay on a test database. No live deployment is inferred.

## Refused target integrations and historical provenance

### OpenWebUI

```text
architecture_status: refused
current_target_role: none
implementation_adapter_status: removed from executable candidate
replacement responsibilities:
  runtime interaction -> Hermes Web/dashboard + compatible Hermes clients
  governed projections -> Pantheon Cockpit
```

The product-specific executable adapter has been removed after consumer verification. Native document/Knowledge APIs and Cockpit projections remain under `mvp_vertical`.

Residual non-executable templates, documentation or compatibility pointers may still exist pending their own incoming-link audit; their presence is historical/reference material, not target architecture.

### Self-hosted LiveSync / CouchDB

```text
architecture_status: retired
current_target_role: none
implementation_workflows: removed
deployment_baseline: removed
historical evidence: Git history / issues only
replacement responsibilities:
  professional source residency -> NAS / AFFAIRES
  scan/watch/reconcile -> standalone AFFAIRES producer
  derived recall -> Hindsight
  optional projection -> Pantheon Cockpit
```

Self-hosted LiveSync, its headless CLI path and CouchDB are no longer active qualification or Ubuntu deployment dependencies. Their former S1–S6 qualification material remains available through Git history. Retirement does not make Hindsight, Obsidian or Cockpit a source authority.

### Paperless-ngx

```text
architecture_status: refused
current_target_role: none
implementation_adapter_status: retired
replacement responsibilities:
  exact source/provenance -> existing Source/document owners
  local/NAS intake -> direct NAS / AFFAIRES Workspace route
  optional Markdown authoring -> replaceable workspace tooling
```

The Paperless client, gateway, ingestion binding, Compose paths, catalog resource, SQL binding migration, Hermes Paperless skill and dedicated document-runtime observer path have been retired after consumer audit. No replacement DMS abstraction was introduced.

The `document_source_management` capability remains provider-agnostic and may be intentionally unbound. Obsidian does not become a DMS or source authority.

```text
source capture != Evidence
folder/path != governed identity
provider selected != authority transfer
```

## Voluntarily absent from Pantheon core

```text
Pantheon internal general-purpose agent runtime
second general-purpose chat frontend
required DMS product
hidden autonomous approval engine
automatic durable-memory promotion engine
scheduler
queue
provider router
plugin marketplace
automatic external sender
unrestricted connector gateway
ERP
production data platform authority
```

External runtimes may contain their own schedulers, queues or provider mechanics. Their existence does not transfer those responsibilities into Pantheon.

## Current target composition

```text
Hermes Web/dashboard
  + optional replaceable Hermes mobile/PWA client
        |
Hermes Agent
        |
Pantheon governance/admission boundaries
        |
Pantheon Cockpit for governed projections

NAS / AFFAIRES -> durable professional source tree
        |
Linux mount -> one Workspace indexer/sync owner
        |                     \
        |                      -> Hindsight derived recall
        -> Cockpit projection

Obsidian -> optional historical/human tooling
LiveSync/CouchDB -> retired; Git history only
Hermes runtime memory -> separate optional runtime continuity
Professional source files -> existing Source/document owners
```

See `TARGET_ARCHITECTURE.md` for the directional map and `CORE_CONCEPTS_MAP.md` for ownership navigation.

## Protected-path rule

`implementation/`, `mcp-server/`, schemas, tests, CI, Docker/environment material and other protected paths require their normal review discipline. A documentation decision to refuse a dependency does not authorize deleting protected implementation code without consumer/test verification.

## Next reconciliation

The next bounded protected audit is the residual OpenWebUI compatibility/reference surface. It must distinguish provenance from active incoming links and remove only superseded paths whose consumers are demonstrably gone.

Do not create a replacement chat frontend, DMS, observer, registry or runtime merely to preserve historical shape.

## Final rule

```text
State what exists.
State what is selected.
State what is only historical provenance.
Do not confuse any of those with production adoption or authorization.
```
