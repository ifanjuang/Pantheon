# Watchlist

Status: active support doctrine — observation and triage only.

This document defines how Pantheon Next watches external systems, technical patterns and ecosystem movements without adopting them by default.

It does not add dependencies.

It does not approve implementation.

It does not define runtime integration.

It does not authorize a scheduler, queue, provider router, tool runtime, MCP layer, plugin manager, observability backend, GraphRAG runtime, LangGraph runtime, autonomous agent team, automatic memory system, automatic skill installer or hidden workflow runner inside Pantheon Next.

```text
Hermes clients handle runtime interaction.
Hermes Agent executes externally.
Pantheon Cockpit exposes governed projections.
Pantheon Next governs consequential status.
```

## Purpose

The Watchlist is the observation layer for external references that may later be distilled into Pantheon governance vocabulary.

It answers:

```text
Should this reference keep being watched, distilled, rejected or archived?
```

It is broader than `SKILL_WATCHLIST.md`.

`SKILL_WATCHLIST.md` watches skill ecosystems and `SKILL.md`-style capability packages.

This document watches frameworks, methods, runtimes, observability systems, memory systems, cockpit surfaces, professional verticalization patterns, connector patterns and governance-adjacent ideas.

## Core rule

```text
Observation is not adoption.
Interest is not approval.
Popularity is not governance value.
Capability is not legitimacy.
```

A watched reference remains external until a separate governed decision changes its status.

## Watchlist record format

A watch record should remain small and reviewable.

Recommended fields:

```text
reference_name
reference_type
source_url_or_identifier
observed_date
capability_summary
pantheon_interest
risk_surface
allowed_distillation
forbidden_import
related_governance_docs
status
review_notes
```

## Status values

Recommended statuses:

```text
observe
pattern_candidate
method_review_required
boundary_required
distill_to_registry
distill_to_skill_watchlist
distill_to_hermes_candidate
reject_runtime_drift
reject_memory_drift
reject_external_effect_risk
reject_authority_drift
archive
```

## Watched domains

| Domain | Examples | Watch reason | Primary risk |
|---|---|---|---|
| Agent and workflow runtimes | LangGraph, CrewAI, AutoGen-style systems | interruption, state, handoff, external execution patterns | Pantheon becomes runtime |
| Observability and evaluation | LangSmith, Langfuse, eval platforms | traces, scores, annotations, regression review | traces become proof or approval |
| Graph RAG and knowledge graphs | GraphRAG, graph memory systems | provenance, corpus structure, contradiction maps | graph becomes truth or memory |
| Skill ecosystems | Agensi, Shokunin, `SKILL.md` repositories | skill anatomy, checks, anti-patterns | marketplace or auto-install drift |
| Contract-driven development | contracts-skill, specification preflight patterns | acceptance, verification, drift checks | technical contract becomes governance authority |
| Runtime clients and UI surfaces | Web/PWA/mobile clients, dashboard patterns, card/review surfaces | user action capture, exposure safety and governed projection patterns | client or cockpit becomes authority |
| Connectors and gateways | MCP servers, provider gateways, app connectors | scoped access, tool policy, least capability | plugin manager or provider router drift |
| Local-first memory and RAG | Glia-like shared memory, SQLite/vector memory | privacy, continuity, retrieval scope | shared memory becomes a Registre Probatoire entry |
| Coding agents | SmallCode, terminal agents, patch agents | patch discipline, controlled execution | coding runtime inside Pantheon |
| Professional verticalization | legal, medical, architectural or regulated-domain assistants | domain playbooks, review gates, source discipline | professional agent becomes authority |
| Prompting and reasoning methods | ReAct, debate, reflection, LLM-as-judge | method discipline and review signals | method becomes hidden orchestration |
| OpenBIM and IFC evolution | IFC5/IFCX, IFC JSON serializations, parsers, geometry analysis and workflow tools | future-proof adapter mappings, spatial analysis and inspectable BIM workflows | external schema, parser or workflow becomes Pantheon ontology or authority |

## Current RAG and document-evaluation watch items

These records are observation and triage only. They do not approve installation, integration, client mutation, Hermes activation or Pantheon runtime behavior.

| Reference | Type | Pantheon interest | Primary risk | Status |
|---|---|---|---|---|
| `contextschema-py` | post-retrieval context validation | context sufficiency, freshness, provenance and invalidation checks before action | context score becomes approval authority | pattern_candidate |
| `chunk-norris` | RAG chunking evaluation | empirical comparison of chunking strategies before ingestion | retrieval score treated as proof or global KB doctrine | pattern_candidate |
| `MMLongBench-Doc` | long-document multimodal benchmark | evidence pages, source modalities, cross-page questions and unanswerable questions | benchmark score treated as professional validation | reference_review |
| Medium RAG 10M+ article | large-scale RAG architecture signal | retrieval/evidence/citation reliability vocabulary | near-zero hallucination claim treated as proof | observe |
| Reddit r/RAG discussions | practitioner weak signal | recurring RAG pain points and failure vocabulary | anecdote becomes doctrine | observe |
| `agent_memory_curator_agent` | memory admission-control reference | structured Register Candidate emission and curation reports | curator becomes a Registre Probatoire entry authority | pattern_candidate |
| `skillsgate` | skill manager / marketplace surface | skill inventory UX and compatibility surface | plugin manager, installer and marketplace drift | boundary_required |

## Current Claude Code ecosystem watch items

These records are observation and triage only. They do not approve Claude Code, Claude Code resources, Hermes bindings, MCP servers, hooks, skills, plugins, sandboxes, memory layers or observability tools.

| Reference | Type | Pantheon interest | Primary risk | Status |
|---|---|---|---|---|
| `hesreallyhim/awesome-claude-code` | Claude Code ecosystem catalogue / awesome list | Map skills, hooks, MCP servers, sandboxes, memory/context persistence, observability, cost monitoring and security tooling into Capability Slot review without adopting dependencies. Route `SKILL.md`-style resources to `SKILL_WATCHLIST.md`; route execution candidates to `HERMES_CAPABILITY_BINDINGS.md`; route operational-state patterns to `PANTHEON_CONTROL_PLANE_BOUNDARY.md`. | Catalogue treated as trust registry, install queue, plugin marketplace, MCP catalogue, provider router plan, proof of safety or evidence of approval. | boundary_required |

## Current deliberation and agent-safety watch items

These records are observation and distillation inputs only. They do not select
dependencies, runtimes, security authorities or execution strategies.

| Reference | Type | Pantheon interest | Primary risk | Status |
|---|---|---|---|---|
| `0xNyk/council-of-high-intelligence` | multi-perspective deliberation method / optional runtime experiments | independent problem restatement, method diversity, anonymized cross-review, anti-conformity, dissent-preserving synthesis, compromises and kill criteria | persona roster becomes Pantheon Role; Council becomes fifth execution strategy/runtime; consensus/vote becomes Decision or Evidence | method_review_required |
| `0xNyk/agent-security` | deterministic repository/content safety tripwires | non-executing static pre-vet before deeper external Skill/repository qualification; explicit claim ceiling and UNKNOWN posture | scanner CLEAN becomes safety/admission proof; tool becomes PEP/security authority; upstream scripts imported without gap comparison | method_review_required |

Detailed bounded review: `reference_reviews/0XNYK_COUNCIL_AGENT_SECURITY.md`.

## Current IFC / OpenBIM watch items

Observed 2026-09-06 while converging Project Anatomy and Hermes context. These records do not select an IFC runtime, parser, serialization, schema generation, geometry engine or workflow UI. IFC remains a source language / adapter profile; Project Anatomy remains the project-understanding model.

| Reference | Type | Pantheon interest | Primary risk | Status |
|---|---|---|---|---|
| `buildingSMART/IFC5-development` | official IFC 5 alpha examples and evolving TypeSpec / IFCX direction | track future schema composition and keep IFC mappings replaceable rather than binding Project Anatomy to IFC 4.3 | preliminary examples treated as stable production schema or imported as Pantheon ontology | observe |
| `buildingsmart-community/ifcJSON` | IFC4/4.3 JSON serialization and round-trip design reference | historical reference for JSON representation, distributed exchange and schema mapping | inactive 2021 repository treated as current IFC future direction or selected interchange runtime | archive |
| `GeometryGym/GeometryGymIFC` | active C# multi-version IFC parser / generator | candidate reference for future .NET/Revit-side parsing where a demonstrated adapter need is not covered by the selected binding | parser library becomes canonical project identity, schema authority or mandatory Pantheon dependency | method_review_required |
| `IfcOpenShell/voxelization_toolkit` | voxel-based building geometry analysis toolkit | robust derived spatial analysis for volume, reachability, exterior/interior and later Pantheon-Next#949-style perception/spatial qualification | derived voxel result treated as surveyed geometry, compliance truth or Project Anatomy fact | pattern_candidate |
| `louistrue/ifc-flow` | node-based IFC manipulation and analysis application using IfcOpenShell/Pyodide | workflow and UX patterns for inspectable IFC filters, relationships, quantities, spatial queries and transformations | application workflow becomes Pantheon orchestration; IFC mutations bypass governed effects; AGPL application absorbed as core dependency | boundary_required |
| `ifcquery/ifcplusplus` | legacy C++ IFC parser / geometry library | historical parser reference only | upstream explicitly describes the project as more-or-less archived; new Pantheon work would bind to a superseded implementation | archive |

Distillation posture:

```text
IFC schema/version != Pantheon ontology
IFC id != stable project identity
parser success != project truth
geometry analysis != professional measurement
workflow execution != authorization
external reference != dependency selection
```

The next IFC-specific review should be driven by a demonstrated adapter or Knowledge need. It should prefer mapping profiles and source provenance over adding IFC entity classes to the Project Anatomy core.

## Triage path

A watched reference may move through the following path:

```text
external reference
→ watch record
→ boundary review
→ method review or skill watch review
→ distillation registry entry
→ candidate doctrine update or Hermes candidate constraint
→ approval decision when required
```

A reference may also be rejected immediately if it crosses a forbidden boundary.

## Routing to other documents

| If the reference is about | Route to |
|---|---|
| External system boundaries | `REFERENCE_BOUNDARIES.md` |
| Ecosystem positioning | `ECOSYSTEM_MAP.md` |
| Extracted governance pattern | `DISTILLATION_REGISTRY.md` |
| Rejected architectural pattern | `REJECTED_PATTERNS.md` |
| Skill package or `SKILL.md` ecosystem | `SKILL_WATCHLIST.md` |
| Prompting, reasoning or evaluation method | `EXTERNAL_TOOLS_POLICY.md` |
| Persistent architectural tension | `TENSIONS_AND_RISKS.md` |
| Runtime capability or tool use | `EXTERNAL_TOOLS_POLICY.md` |
| Hermes-side execution candidate | `HERMES_INTEGRATION.md` and Task Contract review |
| Runtime client/exposure pattern | `EXTERNAL_TOOLS_POLICY.md` and generic MCP exposure verification where applicable |
| Governed Cockpit/Card projection pattern | `PANTHEON_COCKPIT_STRUCTURED_AGENCY_INTERFACE.md` and `CARD_STACK_MODEL.md` |

## Evaluation lens

Watchlist review should ask:

```text
What capability does this show?
What governance problem does it reveal?
What can Pantheon learn without absorbing runtime responsibility?
What evidence would be needed before reuse?
What approval level would be required?
What memory risk does it create?
What external effect risk does it create?
Which existing Pantheon document should own the distilled pattern?
```

## Periodic review

Watched references should not accumulate indefinitely.

A stale watch item should be:

```text
reconfirmed
promoted to pattern candidate
moved to method review
moved to skill watchlist
recorded in rejected patterns
archived
```

Unreviewed accumulation creates architectural noise.

## Forbidden drift

The Watchlist must never become:

- dependency registry;
- vendor endorsement list;
- implementation backlog;
- runtime roadmap;
- plugin marketplace;
- MCP server catalog;
- provider router plan;
- skill installer queue;
- automatic adoption workflow;
- hidden approval mechanism;
- memory promotion queue;
- proof that a reference is safe.

If a watched item is treated as authorization, the boundary has failed.

## Relationship to approvals

Watching a reference is C0 support work.

Distilling a governance pattern may require stronger review when it changes doctrine, evidence expectations, approval posture, memory rules, integration boundaries or protected files.

Implementation remains outside this document.

## Final rule

```text
Watch broadly.
Distill narrowly.
Reject explicitly.
Never import runtime responsibility into Pantheon.
```
