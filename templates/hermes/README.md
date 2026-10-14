# Hermes Templates

Status: external Hermes integration templates — inactive by presence; selected artifacts externally installable.

This directory contains candidate templates for future Hermes execution handoffs, returns and skill candidates.

They are not installed Hermes profiles, skills, tools or toolsets merely by
repository presence. The activity-projection template has an explicit Ubuntu
configurator, and the pre-built browser bundle under
`dashboard-plugins/pantheon-modules/` is an installable Hermes dashboard-only
plugin template. Either executes only after an external operator applies its
separate installation or enablement step.

Nothing in this directory executes inside Pantheon Next by its presence here.

## Four entry surfaces

Read the template through four stable entry surfaces:

```text
AGENTS.md   external runtime-agent behavior and Pantheon Role boundary
CLAUDE.md   Claude-specific repository and review adapter
SKILLS.md   set-level skill classification and evolution contract
DESIGN.md   architecture, ownership and monorepo evolution index
```

Individual skill candidates remain under `skills/<skill-name>/SKILL.md`.

`profiles/pantheon-governed/SOUL.append.md` is a bounded managed supplement for
the external governed profile. It is installed only by the explicit Ubuntu
configurator and does not replace the runtime-owned base `SOUL.md`.

These four files are adapters and indexes. They do not replace their canonical governance owners, install anything or grant authority.

## Placement

Hermes may execute under Task Contract and return candidates.

Hermes must not approve, canonize memory, mutate doctrine, merge directly or bypass approvals.

Pantheon implementation code that consumes these contracts is co-located under `implementation/`. Repository co-location does not make Hermes an in-repository runtime and does not transfer governance authority to implementation code.

## Common installation baseline

The current installation orientation is one common baseline. Read:

```text
docs/governance/COMMON_INSTALLATION_BASELINE.md
docs/install/COMMON_BASELINE_RUNBOOK.md
```

Hermes and OpenWebUI may be installed manually before Pantheon integration. The operator then installs the versioned Pantheon MCP, mounts a pinned checkout read-only, connects OpenWebUI to the authenticated internal Hermes API and runs the acceptance checks.

The common baseline may require PostgreSQL, pgvector, an embedding service, Docling and SearXNG to be present while leaving their exact execution bindings default-off until reviewed.

```text
required presence != binding selected
binding selected != dependency adopted
dependency adopted != task-authorized
```

## First template classes

```text
connection/         candidate fragments for external Hermes configuration
dashboard-plugins/  installable external Hermes dashboard extensions
distribution/       composition lock schema and example; no installer or activation
handoffs/           future Task Contract and Context Pack input envelopes
returns/            future candidate return envelopes
skills/             future skill candidate declarations
```

The distribution lock records exact source revisions, independently reviewable components and required acceptance checks. A candidate operational lock belongs with the implementation or deployment material it describes. A valid lock does not install, activate or authorize anything.

## Runtime evolution

The templates must be reviewed against current `Pantheon-Next/main`, the current co-located consumers under `implementation/`, relevant open pull requests and the exact observed external Hermes release. The former `pantheon-mvp/main` remains historical provenance at cutoff `d960862dd0e23b7003a0f3e4ee0ea630ffc12af9`; it is not a second current consumer branch.

A Runtime Profile is only a descriptive, replaceable candidate for external runtime configuration. It may state intended versions, bindings and compatibility assumptions, but it is not a Pantheon identity, source of authority, approval, activation or task authorization. Runtime Observation may report factual runtime state with provenance and uncertainty; neither object creates Pantheon authority.

```text
profile selected != binding adopted
release observed != dependency adopted
reported != observed
healthy != compatible
compatible != safe
compatible != activated
activated != task authorized
runtime success != Evidence
```

Pantheon internal routes use stable responsibility identities. Removed internal `/v1` paths and generation-labelled active artifacts must not be reintroduced by old templates. Versioned upstream protocols may remain versioned where the external contract requires it.

## Pantheon Modules dashboard plugin

`dashboard-plugins/pantheon-modules/` reads the native Hermes memory, MCP, plugin and Cron inventories and presents their states without collapsing operational enablement into governance activation or task authorization.

It includes explicitly confirmed Hermes-native controls for ready memory providers, reviewed MCP catalog entries and installed plugins. It has no Pantheon backend and retains no credentials. See its local `README.md` for the review-first install sequence and the Mem0, n8n, LangGraph and Memvid placements.

For status consultation, this plugin is the live observation producer. The Pantheon policy MCP may qualify the resulting nine-axis envelope, but it does not call Hermes, duplicate the inventory or infer governance approval from the plugin's descriptive placement labels.

Its `night-operations.template.yaml` and `Night ops` view propose a staggered, finite-trial maintenance window and observe matching native Cron jobs. They do not create or execute schedules. Runtime timezone, profile, workdir, scopes, adapter and expiry remain required operator decisions.

## Native multi-model deliberation candidate

`connection/pantheon_deliberation_moa.template.yaml` is a disabled native Hermes Mixture of Agents configuration fragment reviewed against Hermes Agent `0.18.2`. It contains placeholders only: no provider, model or credential is selected by Pantheon.

The configuration is intended for occasional, one-shot contradictory review. Its governed envelopes are:

```text
handoffs/multi_model_deliberation_handoff.template.yaml
handoffs/multi_model_deliberation_prompt.template.md
returns/deliberation_candidate.template.yaml
```

The default method is one independent-advice pass and, only when needed, one challenge pass. The aggregator organizes dissent but does not become ZEUS or a truth authority. Installation, provider credentials, model admissibility, activation and every real-data run remain separate operator and human decisions. Use the named configuration in a fresh Hermes session; native `/moa` invokes the separately configured default and does not select this candidate by name.

## Pantheon policy/wiki MCP connection

`connection/pantheon_policy_mcp.template.yaml` is a native Hermes Agent `~/.hermes/config.yaml` fragment aligned with the common installation baseline.

The governed runtime surface deliberately exposes one compact routing entry
point plus the read-only consultation and candidate helpers it may need:

```text
route_governed_request
read_doctrine
explain_governance_structure
get_consultation_catalog
explain_architecture
get_capability_status
evaluate_preflight
prepare_task_contract_skeleton
prepare_evidence_pack_skeleton
plan_context_pack
validate_context_pack
```

The fragment is not installed, activated or approved by its presence here. An external operator must install the `mcp-server/` distribution into a versioned side-by-side environment, mount a pinned Pantheon checkout read-only, adapt the absolute executable path, merge the fragment into the real Hermes config and verify discovery.

Sampling and MCP resource/prompt wrappers are disabled. Parallel calls are disabled by conservative common-baseline default to simplify trace review. The status qualifier only evaluates data provided by its caller and performs no runtime probe.

The template explicitly restricts `platform_toolsets.api_server` to `pantheon-policy`. Omitting that override restores Hermes' broad native API-server toolset. Hermes `0.18.2` may still log a static unknown-toolset warning because configuration validation occurs before dynamic MCP registration. This warning does not invalidate the restriction and must not be "fixed" by removing it.

Runtime acceptance must prove:

```text
native Hermes API toolsets absent
pantheon-policy dynamically callable
only the reviewed six Pantheon MCP tools exposed
```

The static `/v1/toolsets` catalog may not enumerate the dynamic MCP surface, so a successful real MCP consultation is required in addition to static inspection.

## Loop candidate templates

Loop candidate templates apply `docs/governance/LOOP_GOVERNANCE_MODEL.md` to Hermes-side handoffs and returns.

```text
handoffs/loop_contract_candidate.json
returns/loop_result_candidate.json
```

They are governance-readable examples, not executable schemas.

Runnable loop mechanics, retry state, queues, checkpoints and tool calls remain in Hermes or another execution runtime.

Pantheon governs admissibility, scope, evidence, blockers, gates and status.

## Rule

Hermes done does not mean Pantheon validated.
