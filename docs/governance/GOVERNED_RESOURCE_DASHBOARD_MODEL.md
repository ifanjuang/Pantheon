# Governed Resource Dashboard Model

Status: candidate support doctrine — documented non-implemented.

Boundary profile: candidate_support_note.

Placement: runtime-adapter support / dashboard governance candidate.

This document defines a simplified dashboard model for governing installable modules, runtime surfaces, AI nodes, model bindings, exposures, policies and external runtime capabilities without collapsing Pantheon Next into a runtime, installer, provider router, plugin marketplace, scheduler, queue or approval engine.

It is not a UI implementation.

It is not a schema.

It is not a Docker, Portainer, OpenWebUI, Hermes, Ollama, PostgreSQL, reverse-proxy or secret-store installation plan.

It is not an authorization to modify protected paths.

Capability lifecycle specialization is owned by `COCKPIT_CAPABILITY_MANAGEMENT.md`.

## Purpose

Pantheon runtime governance needs to be understandable for non-expert users without losing the internal distinctions that keep governance separate from execution.

The proposed simplification is:

```text
User-facing surface:
  Resource Card

Internal model:
  strictly typed governed resource
```

A user may see one simple card pattern.

Pantheon must still keep the real type, dependency, adapter, gate, evidence expectation, rollback posture and forbidden inference for each resource.

## Problem

A dashboard that only says `modules` is too coarse.

It hides material differences between:

```text
PostgreSQL container
OpenWebUI instance
Hermes runtime
Hermes provider binding
Hermes toolset policy
Hermes skill
Hermes function / tool
Hermes workflow
Hermes runtime agent / profile
Hermes or OpenWebUI plugin
MCP server / binding
Ollama workstation node
local model
OpenWebUI -> Hermes connection
public HTTPS exposure
secret reference
memory policy
```

These do not share the same lifecycle, risk, adapter, evidence or approval gate.

A dashboard that exposes every distinction directly is too complex for a beginner.

The model therefore separates interface simplification from governance ontology.

## Core rule

```text
Resource Card is a UX simplification.
Governed Resource is the internal typed object.
```

Pantheon may display different resource kinds through a common card surface.

Pantheon must not flatten them internally.

## User-facing Resource Card

A Resource Card may show:

```text
name
description
status summary
risk summary
dependencies
actions
last observation
next required decision
rollback / backup note
```

Common user-facing actions may include:

```text
install
adopt
configure
activate
deactivate
suspend
resume
update
downgrade
repair
remove
replace
keep external
view risks
view diff
view rollback
```

The fact that actions appear under one common surface does not mean they are executed the same way or carry the same gate.

## Internal resource types

Every Resource Card must map to one explicit internal type.

```text
infrastructure_module
runtime
runtime_surface
skill
function
workflow
runtime_agent
plugin
mcp_binding
connector_binding
ai_runtime_node
model
binding
policy
secret_reference
exposure
data_store
prompt_surface
observability_surface
backup_surface
```

### Type guidance

```text
infrastructure_module:
  installable or adoptable external component such as OpenWebUI, PostgreSQL,
  pgvector, Portainer, Langfuse or SearXNG.

runtime:
  external execution runtime such as Hermes Agent.

runtime_surface:
  configurable native surface of a runtime, such as Hermes providers, models,
  toolsets, memory settings, Cron, gateway or API server.

skill:
  reusable instruction and resource package consumed by an external runtime.
  Lifecycle specialization: COCKPIT_CAPABILITY_MANAGEMENT.md.

function:
  callable tool or function exposed by Hermes, a plugin, an MCP server, a
  connector or another admitted runtime.

workflow:
  external runtime workflow or binding of a Pantheon Workflow Manifest to an
  admitted executor. Pantheon does not become its workflow engine.

runtime_agent:
  external runtime agent or profile executed by Hermes or another admitted
  runtime. Pantheon Roles and gods are not runtime agents.

plugin:
  installable extension package owned by Hermes, OpenWebUI or another admitted
  host. installed != approved; enabled != scope-activated.

mcp_binding:
  external MCP server declaration and its runtime binding. Pantheon does not
  become the MCP host.

connector_binding:
  governed relationship to a third-party connector or connector gateway.

ai_runtime_node:
  workstation or server exposing local inference capacity, such as Ollama, vLLM,
  LM Studio or LocalAI.

model:
  model artifact or served model observed on a runtime node or provider.

binding:
  governed relationship between resources, such as OpenWebUI -> Hermes,
  Hermes -> model endpoint, model -> node, provider -> scope, or tool -> project.

policy:
  rule surface for approvals, memory, evidence, external actions, network,
  fallback, data sensitivity or retention.

secret_reference:
  reference to a secret or credential location. The dashboard may govern
  status and handling but must not become a secret store by implication.

exposure:
  network or publication surface such as localhost, LAN, public HTTPS,
  reverse proxy, CORS or WebSocket handling.

data_store:
  persistent state, database, volume, vector store or managed data directory.

prompt_surface:
  governed prompt-related surface such as SOUL.md, context files, system prompt
  overlays, role prompts or tool policy excerpts.

observability_surface:
  health, logs, runtime traces or telemetry status.

backup_surface:
  backup, restore, snapshot or rollback posture.
```

## Lifecycle states

The common lifecycle vocabulary is:

```text
listed
observed
detected
selected
review_pending
adoption_pending
adopted
install_pending
install_authorized
installed
configured
configuration_observed
health_observed
activation_pending
activated
degraded
update_available
update_authorized
update_applied
rollback_available
rollback_authorized
deactivation_pending
deactivated
suspended
removal_pending
removed
retired
blocked
```

Not every type uses every state.

A state must be interpreted through the resource type.

For example, a `runtime_surface` is usually configured or activated, not installed as a standalone module.

A `binding` is created, verified and activated; it is not installed like a container.

A `secret_reference` may be present or missing; it must not be treated as Pantheon-owned secret material.

A `skill`, `plugin` or `mcp_binding` may be installed and enabled by its native host while remaining unapproved or inactive for every governed scope.

## Chronological phases

The dashboard must avoid circular dependencies.

```text
Phase 0 — Seed
  Minimal Pantheon bootstrap.
  No dependency on OpenWebUI, Hermes, PostgreSQL, Portainer, Ollama or Langfuse.

Phase 1 — Bootstrap Dashboard
  Minimal local dashboard or setup surface.
  Uses bootstrap state only.
  Displays enough to install, adopt or keep external the baseline resources.

Phase 2 — Discovery
  Detects container runtime, existing modules, existing runtimes, ports,
  volumes, managed config locations, AI runtime nodes, native capabilities and
  candidate bindings.

Phase 3 — Adoption / installation
  Human chooses per resource: adopt existing, install missing, ignore,
  keep external, replace or repair.

Phase 4 — Durable state
  Persistent state store is installed or adopted where required.
  Bootstrap state may be migrated.

Phase 5 — Full Dashboard
  Full resource dashboard becomes available after baseline state and control
  surfaces are installed or adopted.

Phase 6 — Runtime configuration
  Raw runtime surfaces are configured through version-matched adapters that use
  native mechanisms. Arbitrary file or database editing remains refused.

Phase 7 — Capability management
  Skills, functions, workflows, runtime agents, plugins and MCP bindings are
  inventoried and managed through the lifecycle defined in
  COCKPIT_CAPABILITY_MANAGEMENT.md.

Phase 8 — Bindings
  Connections are created or updated only after both sides exist or are adopted.

Phase 9 — Activation
  Consequential uses are activated after configuration, health observation,
  scope review and human approval where required.

Phase 10 — Maintenance
  Updates, downgrades, backups, restore checks, suspension, deactivation,
  removal and retirement are handled as governed lifecycle actions.
```

## Dependency rule

```text
A resource may be displayed before installation.
A resource may be discovered before adoption.
A resource may be configured only after installation or adoption.
A capability may be enabled by its native host before Pantheon scope activation.
A resource may be activated only after configuration and observation.
A consequential use requires a separate approval gate.
```

This prevents cycles such as requiring the full dashboard to install the state store it depends on.

It also prevents interpreting a native enabled flag as global Pantheon authorization.

## Adapter model

A Resource Card never executes by itself.

Each actionable resource resolves to an adapter or external runtime.

Candidate adapter families:

```text
container_adapter:
  Docker, Podman, Portainer or equivalent external provisioner.

hermes_config_adapter:
  Hermes-native raw configuration surfaces with version-specific compatibility.

hermes_capability_adapter:
  Hermes-native plugins, skills, functions/tools, profiles/runtime agents,
  workflows and MCP bindings. It performs one admitted native lifecycle action
  after Pantheon preflight and human confirmation.

openwebui_config_adapter:
  OpenWebUI installation/adoption, initial environment, persisted configuration,
  provider/agent connections, admin settings and health checks.

openwebui_capability_adapter:
  OpenWebUI-native plugins, functions and other admitted extension surfaces.

ai_runtime_node_adapter:
  local or remote inference-node discovery, pairing, adoption, model inventory,
  context qualification, model install request and health status.

exposure_adapter:
  reverse proxy, HTTPS, CORS, WebSocket, public/LAN/localhost exposure and
  exposure rollback.

secret_reference_adapter:
  external secret-store reference, credential presence checks, redaction and
  secret-handling gates.

backup_adapter:
  backup, restore, snapshot, rollback and destructive-action preflight.
```

Adapters may apply changes only when the action is authorized under the relevant gate.

Pantheon governs the decision and state.

The adapter or external runtime performs the operation.

## Gates

Every action must resolve to a gate class.

```text
safe_read:
  read-only status or documentation display.

normal_change:
  reversible configuration, installation or capability-state change with
  limited blast radius.

sensitive_change:
  provider, model, tool, plugin, skill, workflow, runtime-agent, memory,
  network, connector, runtime surface or scope change.

destructive_change:
  deletion, volume removal, irreversible reset, downgrade with data migration
  risk, secret removal or state-store replacement.

external_exposure:
  public/LAN exposure, reverse proxy, webhook, gateway or outbound connector.

secret_handling:
  API keys, OAuth, tokens, shared env, service accounts or credentials.

memory_or_evidence:
  memory capture, memory promotion, evidence claim, trace admission or register update.

runtime_execution:
  operation that invokes an external runtime, provisioner, node agent, CLI,
  container, SSH, MCP server, gateway or model endpoint.
```

Gate result vocabulary:

```text
allow
allow_with_gate
needs_approval
needs_evidence
needs_revision
block
to_verify
```

## Non-equivalence rules

```text
listed != authorized
observed != adopted
detected != approved
installed != approved
installed != activated
native enabled != Pantheon scope-activated
adopted != safe
configured != effective
configuration_observed != usage_authorized
healthy != safe
connected != approved_for_scope
runtime agent != Pantheon Role
workflow selected != workflow authorized
function visible != function authorized
plugin enabled != plugin approved for every scope
node_detected != node_adopted
model_downloaded != model_approved
provider_configured != provider_authorized
binding_created != binding_activated
secret_present != secret_governed
managed_scope_applied != hard_security_boundary
public_url_reachable != public_exposure_approved
update_available != update_authorized
update_applied != validated
downgrade_possible != downgrade_safe
backup_exists != backup_verified
rollback_known != rollback_decided
removed != data_forgotten
technical receipt != evidence
```

## OpenWebUI placement

An installed or adopted OpenWebUI instance is an `infrastructure_module` resource.

Its connection to Hermes, Ollama, OpenAI-compatible endpoints or other providers is a `binding`, not the same resource as the OpenWebUI instance.

Its localhost, LAN or public HTTPS availability is a separate `exposure` resource.

OpenWebUI-native plugins or functions may be managed as `plugin` or `function` cards with OpenWebUI identified as native host.

OpenWebUI remains primarily the conversational exposure surface when Hermes owns execution capabilities.

## Hermes placement

Hermes Agent is an external execution runtime.

Hermes itself is a `runtime` resource.

Hermes native raw configuration areas remain `runtime_surface` resources.

Hermes skills, functions/tools, workflows, runtime agents/profiles, plugins and MCP bindings are explicit capability resource types managed under `COCKPIT_CAPABILITY_MANAGEMENT.md`.

Pantheon may govern intended state, approval gates, scope and observed status.

Hermes native mechanisms or a Hermes adapter apply the lifecycle operation.

Hermes execution results return as candidates until governed review is complete.

## Dashboard action and timing contract

Pantheon Control may expose actions that govern an operation performed by Hermes or another admitted external runtime. A visible action is not itself an execution engine.

Every actionable card must keep at least these dimensions separate:

```text
installation_status
configuration_status
native_enabled_status
governance_authorization_status
scope_activation_status
health_status
update_status
rollback_status
```

Therefore:

```text
installed != configured
configured != natively enabled
natively enabled != authorized by Pantheon policy
authorized != active for every project or user
active for one scope != healthy
healthy != professionally validated
```

The preferred reversible user action is `suspend` or `disable`, not `uninstall`. Removal is reserved for a separately reviewed destructive path.

### Default-off invariant

All write-capable, compute-capable, scheduled, ingestion, vectorization, runtime-memory, maintenance, reconstruction, notification and external-action features are disabled by default for governed use.

Native installation or enablement may be observed without implying Pantheon activation.

Only passive surfaces may be available before explicit activation:

```text
read doctrine and help
display declared inventory
display already supplied status reports
prepare a configuration, capability or activation proposal
preview scope, dependencies, risks and required gates
```

Discovery probes are not assumed passive merely because they are read-only: if they contact a runtime, scan a network, open protected files or consume meaningful compute, they require a separately admitted read action.

The first activation defaults to one bounded sandbox or project scope.

### Action catalogue

| Family | Dashboard action | External executor / owner | Default gate |
|---|---|---|---|
| Observation | Refresh inventory, configuration, liveness, health and version status. | Hermes adapter or operator probe | `safe_read` |
| Capability | Inspect skill, function, workflow, runtime agent, plugin or MCP binding source, manifest, permissions and current state. | Hermes/OpenWebUI adapter | `safe_read` |
| Capability | Create or amend a skill, workflow or runtime-agent candidate. | Cockpit candidate authoring; no native mutation | consequence-dependent review |
| Capability | Propose install or adoption of a reviewed capability. | Hermes/OpenWebUI native adapter or operator | `normal_change` or higher |
| Capability | Enable, disable, suspend, resume or probe one reviewed native capability. | Native runtime adapter after Pantheon preflight | explicit confirmation; scope-dependent |
| Capability | Activate one capability for sandbox, project or production scope. | External runtime after authorization | `sensitive_change` |
| Capability | Prepare update, rollback, replacement, retirement or destructive removal. | Native runtime adapter / operator | risk-dependent; removal is `destructive_change` |
| Lifecycle | Propose installation or adoption of a missing infrastructure resource. | Provisioner or human operator | `normal_change` or higher |
| Lifecycle | Configure an installed raw runtime surface through its version-matched native mechanism. | Native adapter or external provisioner | `normal_change` |
| Timing | Observe matching native Hermes jobs and prepare one bounded schedule proposal. | Hermes native Cron / operator | dashboard `safe_read`; configuration separately gated |
| Ingestion | Admit queued sources for one scope and process changed material. | Hermes ingestion worker / admitted adapter | scope and source gate |
| Retrieval | Vectorize changed chunks and synchronize an eligible retrieval projection. | External vector adapter | `memory_or_evidence` |
| Human decision | Accept, reject, amend, supersede or request evidence for a candidate. | Human decision through governed review | consequence-dependent User Decision Gate |

No action may silently chain installation, enablement, activation and execution.

## Mandatory protections

Whenever an ingestion, vectorization, maintenance, integrity or broad capability action is admitted, preserve:

```text
scope isolation
fixed and reviewable source or capability manifest
source / package identity and version trace
snapshot or rollback reference before mutable work
append-only execution and discrepancy trace
bounded duration, compute, retry and finite-run budget where applicable
explicit failure and continuation state
fail closed on missing scope, rollback or required dependency
human gate for semantic, destructive or cross-scope effects
```

An optional action may be suspended. Mandatory protections may not be disabled to make it run.

## Action status vocabulary

```text
unavailable
available
blocked_dependency
proposed
pending_confirmation
authorized
dispatched
running
succeeded_technical
failed
suspended
review_pending
to_verify
```

`succeeded_technical` means the external operation returned its expected technical receipt. It does not mean the content was accepted as evidence, canonical memory or professional truth.

## Forbidden interpretations

This model must not be read as creating:

```text
live dashboard implementation
Pantheon-owned module registry
Pantheon-owned plugin manager
installer
Portainer stack
Docker file
shell runner
provider router
MCP host
workflow engine
agent host
scheduler
queue
automatic approval engine
automatic memory engine
secret store
model marketplace
runtime orchestrator
automatic fallback router
external-send channel
```

A cockpit may manage capability lifecycle through external adapters without becoming the native manager or runtime itself.

## Implementation status

```text
implemented:
  none in this document.

documented non-implemented:
  Governed Resource Dashboard model, Resource Card simplification, explicit
  capability types, lifecycle states, dependency rule, adapter classes,
  gate classes and action catalogue.

partial:
  Existing repository documentation and the external Pantheon Modules Hermes
  dashboard plugin already contain bounded native inventory and confirmed
  administration actions.

to verify:
  Exact adapter contracts, UI behavior, state storage, health checks, capability
  authoring contracts, runtime compatibility and OpenWebUI/Hermes native mechanics.

obsolete:
  Any interpretation that treats a card, listed capability, installation or
  native enabled state as automatic approval, activation, safety or adoption.

non applicable:
  Direct runtime execution by Pantheon.
```

## Promotion path

This candidate may be promoted only through an allowed referent such as:

```text
read-only status report for resource and capability cards
schema for governed resources or Capability Action Candidates
test coverage for lifecycle and non-equivalence rules
static prototype explicitly marked documented non-implemented
explicit dated human decision in a PR or issue
```

Until then, it remains candidate support doctrine.
