# Cockpit Runtime Configuration Assistance

Status: candidate support doctrine — minimal raw runtime-configuration boundary — documented non-implemented.
Boundary profile: candidate_support_note.

This document defines the narrow treatment of raw Hermes Agent and OpenWebUI configuration.

It does not define capability lifecycle management. Skills, functions, workflows, runtime agents, plugins and MCP bindings are governed separately by `COCKPIT_CAPABILITY_MANAGEMENT.md` and `GOVERNED_RESOURCE_DASHBOARD_MODEL.md`.

```text
Raw configuration assistance
!= capability management
```

The cockpit should manage capabilities. It should avoid becoming a generic editor for unstable runtime configuration files.

## 1. Decision

The selected raw-configuration posture is:

```text
install and maintain through native/operator tooling
-> observe exact runtime version and effective connection state
-> use version-matched native configuration surfaces
-> obtain policy, classification and validation from the Pantheon MCP
-> verify the effective result
```

Initial behavior:

```text
read-only observation           -> candidate future adapter
operator guidance               -> documentation / cockpit card
capability lifecycle operations -> allowed through reviewed native adapters;
                                  see COCKPIT_CAPABILITY_MANAGEMENT.md
arbitrary config-file editing   -> forbidden
```

The cockpit must remain simpler than the runtimes it exposes.

## 2. Responsibility boundary

```text
exposed_by:
  Pantheon MVP Cockpit, OpenWebUI-facing cards or another reviewed display surface.

executed_by:
  Hermes Agent, OpenWebUI, their native administration surfaces, reviewed runtime
  adapters and human/operator tooling.

governed_by:
  Pantheon doctrine and the Pantheon MCP for policy, classification, validation,
  capability status, scope, evidence expectations, activation gates and refusals.

approved_by:
  Human for installation, raw configuration change, capability lifecycle mutation,
  activation, update, restart and rollback.

forbidden:
  Generic YAML/JSON patcher, direct database editing, guessed field migration,
  Docker socket access, shell access, secret capture, silent restart, automatic
  update, provider routing or duplicated policy logic in the cockpit.
```

## 3. What remains in the Pantheon MCP

The Pantheon MCP remains the preferred bounded interface for:

```text
doctrine consultation
architecture explanation
request classification
capability-status qualification
external-action policy checks
candidate validation
provided-evidence verification
Context Pack planning and validation
status distinctions and refusal reasons
capability action preflight and receipt qualification when later implemented
```

The cockpit renders MCP results. It does not reimplement their rules locally.

```text
cockpit display != policy source
runtime observation != governance decision
MCP result != human approval
runtime success != evidence
```

## 4. Minimum raw-configuration observation

The cockpit should observe only facts needed to understand the active runtime path and adapter compatibility:

```text
runtime identity
runtime version
reachable / unreachable
bounded health signal
OpenWebUI -> Hermes effective connection target
Hermes API authentication present / absent, without exposing the key
Pantheon MCP binding present / absent
Pantheon MCP reachable / unreachable
configuration compatibility state after an update
adapter compatibility state
last observation time
observation source
```

Capability inventory is not excluded. It belongs to the capability-management surface rather than this raw-configuration document.

## 5. Narrow operator guidance

When a connection or compatibility problem is observed, the cockpit may prepare guidance for cases such as:

```text
correct the OpenWebUI -> Hermes base URL
add the required /v1 suffix when applicable
identify that the Hermes API key is missing or mismatched, without reading it
identify that the Pantheon MCP binding is absent, disabled or unreachable
identify that a native configuration migration is required after an update
open or name the relevant native administration surface
show a version-matched operator command candidate
show expected post-change checks
show the rollback reference
```

The cockpit must not produce a generic full-file patch.

Preferred form:

```text
short diagnosis
exact observed version
native setting or management surface
one bounded correction
expected result
verification checklist
rollback note
```

## 6. Configuration-version drift

Hermes and OpenWebUI configuration formats may change between versions. Field names, nesting, persistence behavior, defaults, environment variables, CLI commands and administration interfaces must not be assumed stable.

Therefore:

```text
runtime version must be observed before guidance
adapter declares supported version range
unknown or unsupported version -> mutation disabled
field path copied from another version -> not admissible evidence
runtime update -> configuration migration status checked separately
configuration digest change -> compatibility review required
```

The cockpit must never use a hard-coded file path or field path as a universal contract.

Forbidden pattern:

```text
open config.yaml
-> replace arbitrary text
-> restart container
```

Preferred pattern:

```text
observe exact runtime version
-> select version-compatible native adapter or upstream guidance
-> perform one native action after the required gate
-> observe effective result again
```

When the runtime offers official validation or migration commands, the cockpit may display them or a reviewed adapter may invoke them only under the separately defined action and approval rules.

## 7. Hermes raw-configuration scope

Observable:

```text
Hermes version
API reachability
bounded health response
API authentication present / absent
OpenWebUI-facing API base URL or service identity
Pantheon MCP binding identity
configuration validation or migration-needed status
adapter compatibility
```

Raw proposal or guidance:

```text
correct the Hermes API connection used by OpenWebUI
restore a reviewed Pantheon MCP declaration
route to the native Hermes configuration surface
show version-matched validation or migration commands
reduce accidental broad API exposure when a reviewed correction is known
```

Capability management such as plugin, skill, tool, MCP, workflow or runtime-agent lifecycle is explicitly in scope for the cockpit, but it uses native capability adapters and the governance flow defined in `COCKPIT_CAPABILITY_MANAGEMENT.md` rather than arbitrary `config.yaml` editing.

## 8. OpenWebUI raw-configuration scope

Observable:

```text
OpenWebUI version
application reachability
active Hermes connection name or identifier
Hermes base URL
model discovery through Hermes
connection authentication present / absent, without exposing the key
effective connection observed versus container-environment declaration
```

Proposal or guidance:

```text
correct the Hermes base URL
replace localhost with the private-network service name
add the required /v1 suffix
route the human to native secret entry
identify an obsolete duplicate Hermes connection
route to Admin Settings when persisted configuration overrides environment values
```

OpenWebUI may persist configuration in its database. The cockpit must distinguish:

```text
container environment observed
persisted OpenWebUI setting observed
effective connection observed
```

It must not edit the OpenWebUI database directly.

## 9. Secrets

The cockpit does not store raw runtime secrets.

Allowed:

```text
secret present: true | false | unknown
secret owner
secret reference identifier when externally provided
last rotation time when externally provided
```

Forbidden:

```text
raw API key
raw database password
private SSH key
browser cookie or authenticated profile
unredacted .env file
secret copied into Knowledge, logs or Evidence Packs
```

A secret change routes to the native secret-entry surface or an external secret manager.

## 10. Updates and compatibility

```text
update_available != update_authorized
runtime_updated != configuration_compatible
configuration_migrated != runtime_safe
healthy != safe
rollback_available != rollback_decided
```

After a Hermes or OpenWebUI update:

```text
observe new version
check upstream release and migration guidance
select a compatible adapter contract
check effective OpenWebUI -> Hermes connection
check Pantheon MCP binding
refresh capability inventory
run or request native validation/migration checks when applicable
disable unsupported mutations
record compatibility result
```

Compatibility result vocabulary:

```text
observed_compatible
observed_degraded
migration_required
adapter_compatibility_to_verify
failed
to_verify
```

## 11. Direct-write distinction

A generic raw-configuration write adapter is not selected.

```text
generic file or database patch -> forbidden
capability lifecycle action    -> permitted only through a reviewed native adapter
one versioned native setting   -> may be considered when required by a concrete adapter
```

This distinction allows the cockpit to manage skills, functions, workflows, agents, plugins and MCP bindings without coupling the product to unstable configuration-file structures.

## 12. Runtime connection card

A runtime-connection card may show:

```text
runtime
version
reachability
connection status
Pantheon MCP status
adapter compatibility
configuration compatibility
last observed
open issue
native action required
verification action
rollback reference
```

Actions:

```text
Inspect
Open native settings
Copy reviewed command candidate
Verify connection again
Consult Pantheon MCP
Show rollback note
Open capability management
```

Capability cards have their own lifecycle actions under `COCKPIT_CAPABILITY_MANAGEMENT.md`.

## 13. Current status

```text
installation documentation               -> implemented as documentation
raw configuration boundary                -> implemented as documentation
capability management doctrine            -> implemented as documentation in sibling document
MCP-backed policy projection              -> documented non-implemented in cockpit
live Hermes/OpenWebUI observation adapter  -> documented non-implemented
generic config editor                      -> voluntarily absent
capability lifecycle adapters              -> partial external referent / broader mapping to verify
```
