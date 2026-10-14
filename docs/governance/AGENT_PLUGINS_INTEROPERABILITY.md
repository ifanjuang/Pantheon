# Agent Plugins interoperability

Status: candidate external-interoperability review — documented, not installed, activated, adopted or task-authorized.
Boundary profile: external_reference_review.
Reviewed specification: Agent Plugins 1.0.0 — Published.
External currentness revalidated: 2026-08-28.

## Purpose

This document classifies the Agent Plugins specification against Pantheon Next's existing governance and Hermes boundaries.

It does not create a Pantheon plugin format, plugin manager, installer, runtime, registry, package resolver, MCP runtime, skill runtime or approval mechanism.

```text
Optional Hermes WebUI or other compatible clients may expose runtime interaction.
Hermes Agent executes external admitted work.
Pantheon Cockpit projects governed Cards, decisions, navigation and status.
Pantheon Next governs.
The human decides consequential effects.
```

`nesquena/hermes-webui` is an optional/proposed external Hermes interaction surface, not a required Pantheon component or authority owner.

The objective is convergence: reuse a portable external package format where it fits, while keeping Pantheon concepts authoritative and tool-agnostic.

## Reviewed upstream contract

Current upstream state revalidated on 2026-08-28:

```text
specification: https://agent-plugins.org/specification
spec_version: 1.0.0
status: Published
portable_manifest: plugin.json
portable_component_types:
  - Agent Skills under skills/*/SKILL.md
  - MCP servers declared in mcp.json
```

The normative specification defines a `Client` as the tool that discovers, installs, loads and executes plugin components. Agent Skills remain governed by the Agent Skills specification; Agent Plugins defines their fixed discovery location. MCP wire behavior remains governed by MCP; Agent Plugins defines the portable `mcp.json` configuration that a client maps into its native configuration.

This places the Agent Plugins client responsibility in the execution/runtime layer, not in Pantheon governance.

The 1.0.0 format uses canonical versioned schemas. The portable root manifest is closed and client-specific metadata belongs under namespaced `extensions`. Published format status does not itself establish support in any selected runtime.

```text
specification published != client support
client support != plugin adopted
manifest valid != package trusted
```

## Canonical placement

```text
Agent Plugin package
        |
        v
external portable packaging
        |
        v
Hermes-side native support or external translator, only when required
        |
        v
existing Pantheon capability and binding governance
        |
        +--> optional Hermes WebUI / compatible-client runtime interaction
        |
        +--> Pantheon Cockpit governed projection
        |
        v
human decision for consequential effects
```

Pantheon must not become an Agent Plugins conformant runtime merely to govern packages that another runtime can consume.

The existing responsibility split remains sufficient:

```text
Agent Plugins      -> describes and packages portable runtime components
Hermes Agent       -> executes admitted runtime components through supported surfaces
optional clients   -> may expose runtime interaction; Hermes WebUI is one proposed option
Pantheon           -> governs eligibility, scope, binding legitimacy, approval and Evidence status
Pantheon Cockpit   -> projects governed state and decisions
human              -> decides consequential effects
```

No client selection transfers authority to that client.

## Mapping to existing Pantheon concepts

Agent Plugins introduces no missing Pantheon authority object.

| Agent Plugins surface | Pantheon interpretation | Required posture |
|---|---|---|
| plugin package | external capability package candidate | preserve source, version and observed package identity; no automatic adoption |
| `plugin.json` | external package metadata | metadata only; never a Capability Passport or authorization record |
| `skills/*/SKILL.md` | runtime skill candidates | Hermes-side skill surface; consequential use remains bounded by Task Contract and scope |
| `mcp.json` | portable MCP binding declaration | candidate runtime bindings; tool availability does not authorize use |
| MCP server entry | candidate concrete binding | qualify exact effects, target, permissions and failure posture before consequential use |
| client extension namespace | client-specific runtime metadata | keep outside Pantheon kernel unless a tool-agnostic governance distinction is demonstrated |
| `PLUGIN_ROOT` | runtime package location | runtime state only; not Pantheon memory or provenance by itself |
| `PLUGIN_DATA` | client-managed persistent runtime data | runtime state only; never canonical memory, Evidence or approval state |

The preferred convergence path is therefore:

```text
plugin.json / skills / mcp.json
        -> external observation
        -> candidate capability bindings
        -> existing Capability / binding / Task Contract machinery
        -> governed execution handoff
        -> Result Candidate / Evidence Pack Candidate
```

No `PantheonPlugin`, `PantheonPluginManifest` or parallel plugin lifecycle is justified by the published specification.

## Required non-equivalences

```text
plugin discovered != plugin adopted
plugin installed != capability approved
manifest valid != package trusted
skill present != skill authorized
MCP server declared != MCP server selected
MCP server reachable != MCP tool authorized
binding selected != dependency adopted
runtime scan passed != safe for professional data
runtime success != Evidence
PLUGIN_DATA persisted != Pantheon memory
client extension present != Pantheon authority
optional client selected != authority transfer
```

These are applications of existing Pantheon invariants, not new kernel rules.

## Manifest boundary

Agent Plugins 1.0.0 uses a closed root `plugin.json` schema. Client-specific metadata belongs under namespaced `extensions`; unknown root fields must not acquire semantics.

Pantheon governance fields therefore must not be added to the portable root manifest.

Forbidden convergence pattern:

```text
plugin.json
  approved: true
  pantheon_scope: ...
  evidence_level: ...
  authorization: ...
```

Preferred pattern:

```text
portable plugin metadata
        +
separate Pantheon-side observation / qualification / binding records
```

A Pantheon-specific Agent Plugins extension namespace is not required by the current need. It should be introduced only if a concrete client-side interoperability requirement cannot be represented through existing Pantheon records without duplicating authority into the package.

## Security boundary

Agent Plugins constrains package-relative paths to the plugin root, but package containment is not process isolation and portable metadata does not authorize external effects.

For Pantheon this means:

```text
package containment != process sandbox
valid stdio command != safe command
valid remote MCP URL != approved external destination
configured header != secret mechanism
transport supported != transport authorized
plugin installed != task authorized
```

Credential discovery, storage, runtime sandboxing, installation integrity, update policy and rollback remain client/deployment concerns governed by existing Pantheon eligibility and external-effect rules; they must not be absorbed into `plugin.json`.

## Failure isolation

Agent Plugins separates component failure boundaries: one invalid or unavailable component must not silently turn unrelated components into accepted or rejected capability state.

Pantheon should preserve that granularity rather than projecting a single coarse `plugin healthy` state.

Preferred observation shape is conceptual, not a new canonical schema:

```text
package_observed
manifest_valid
skills:
  valid / invalid / unavailable
mcp_servers:
  valid / invalid / unreachable / unauthorized
capability_gaps
```

A package-level health label must not collapse component validity, runtime reachability, security qualification, governance approval and task authorization.

## Hermes fit and currentness

The original review used Hermes Agent 0.20.0 as an observed baseline. That version remains historical qualification context, not a permanent current-runtime claim.

Current upstream Hermes exposes first-class Skills, MCP and plugin surfaces. That reduces the demonstrated need for a Pantheon-owned translation layer even further: portable components should map through runtime-native surfaces where practical, and any external translator remains replaceable dev/runtime tooling.

Current `nesquena/hermes-webui` is a separate optional web/mobile surface around Hermes Agent. Upstream documents near-CLI interaction parity and, by default, in-process Hermes agent execution. Pantheon therefore treats it as an optional external runtime/client surface that requires separate deployment qualification if selected; its existence does not make a WebUI mandatory or move authority out of Pantheon.

```text
native Skills available != Agent Plugins conformance
native MCP available != Agent Plugins conformance
native plugin API available != portable package adopted
Hermes WebUI available != Hermes WebUI selected
Hermes WebUI selected != Pantheon authority transferred
```

Exact operational compatibility must still be checked against the deployed Hermes release before claiming that a full Agent Plugins package can be consumed directly.

The current evidence supports this sequence:

```text
1. do not change Pantheon kernel;
2. do not create a Pantheon plugin manager;
3. prefer Hermes native Skill / MCP / plugin surfaces;
4. use an external translator only when a real portability gap is demonstrated;
5. qualify resulting bindings through existing Pantheon governance;
6. treat Hermes WebUI as optional if a web/mobile client is desired;
7. require a real-instance observation before claiming operational compatibility.
```

## Adapter decision

Current decision:

```text
agent_plugins_specification: 1.0.0-published
placement: external interoperability format candidate
pantheon_kernel_change_required: false
pantheon_schema_change_required: false
pantheon_plugin_registry_required: false
pantheon_installer_required: false
hermes_runtime_adapter_required: not demonstrated
hermes_webui_required: false
hermes_webui_posture: optional / proposed external runtime interaction surface
external_translation_or_client_support: optional / need-driven
real_instance_observation_required: true before operational compatibility claim
installation_effect: none
activation_effect: none
task_authorization_effect: none
```

An Agent Plugins-specific adapter becomes justified only if a real package cannot be represented by the selected Hermes runtime's existing Skill, MCP and plugin surfaces without losing a material capability or provenance distinction.

Until such a gap is demonstrated, adding an adapter or compiler to Pantheon would be speculative duplication.

## Minimum future acceptance test

If a concrete portable-package need appears, use one synthetic package containing one harmless Agent Skill and one read-only MCP server, then verify:

1. exact package source, version and digest are recorded;
2. manifest and component schemas validate at the pinned Agent Plugins version;
3. skill maps to the exact selected Hermes release without changing Pantheon doctrine or schemas;
4. MCP server maps without embedding governance authority or credentials in portable metadata;
5. Hermes exposes only the expected read-only tools;
6. Pantheon still requires existing Task Contract / capability admission for consequential use;
7. component failure remains isolated and visible as a Capability Gap;
8. runtime output remains candidate output / candidate evidence only;
9. uninstall or rollback removes runtime availability without mutating Pantheon canonical state.

Synthetic acceptance remains need-driven. No custom adapter should be written merely to manufacture a reason for this test.

## Compiler / translator posture

A compiler such as Kitbash can be useful when one source Skill must actually be projected into several agent-client formats or emitted as an Agent Plugins package.

That is a tooling responsibility, not a Pantheon governance responsibility.

Current repository review does not demonstrate a multi-client compilation requirement. Hermes remains the selected execution runtime and already exposes native Skill, MCP and plugin surfaces. Therefore no Kitbash binding, registry entry, schema, runtime dependency or adapter is selected by this document.

```text
multi-target capability available != multi-target need demonstrated
compiler useful != compiler adopted
compiled != authorized
portable package emitted != plugin adopted
```

If a future multi-agent requirement appears, an external compiler may be re-evaluated against the exact then-current formats and clients without reopening Pantheon kernel architecture.

## Decision

Accepted with constraints as an external interoperability format.

Accepted:

```text
published portable packaging concept
Agent Skills reuse
portable MCP configuration concept
failure isolation
client-owned runtime translation
optional replaceable Hermes interaction clients
```

Refused:

```text
Agent Plugins as Pantheon runtime
Agent Plugins as Pantheon governance authority
Pantheon-owned plugin installer or plugin manager
root plugin.json governance fields
automatic capability adoption from package presence
automatic authorization from installation or health
compiler adoption without a demonstrated multi-client need
Hermes WebUI as mandatory Pantheon component
```

To verify only when an operational need appears:

```text
Agent Plugins conformance/support in the exact deployed Hermes release
selected external translator behavior if native support is insufficient
one synthetic package acceptance run
supply-chain and rollback posture of the selected runtime/client
Hermes WebUI deployment/security/runtime behavior if that optional surface is selected
```

## Relationship to existing doctrine

This review specializes but does not override:

- `CAPABILITY_PLACEMENT.md`;
- `ADAPTERS_AND_BINDINGS.md`;
- `HERMES_INTEGRATION.md`;
- `HERMES_RUNTIME_SURFACE_REVIEW.md`;
- `EXTERNAL_TOOL_PLACEMENT_REGISTER.md`;
- `EXTERNAL_TOOLS_POLICY.md`.

If any statement here conflicts with those authorities, the existing canonical governance documents win.
