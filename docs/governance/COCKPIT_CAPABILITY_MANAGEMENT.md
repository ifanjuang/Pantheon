# Cockpit Capability Management

Status: candidate support doctrine — executable lifecycle seam and Tool Card projection co-located; unified live capability feed and public Compétences space remain incomplete.
Boundary profile: candidate_support_note.

This document owns one narrow responsibility: how the Cockpit exposes and requests bounded lifecycle actions for external capabilities without becoming their semantic owner or execution runtime.

Canonical capability identity, eligibility, binding, activation, compatibility and task/run legitimacy remain owned by their existing contracts. This document does not define a second capability registry or lifecycle truth.

```text
Cockpit projects and captures bounded intent.
Pantheon qualifies policy and governance state.
Hermes or another admitted native runtime performs the operation.
The human decides consequential effects.
```

## 1. Owner boundaries

The Cockpit may project skills, functions/tools, workflows, runtime agents/profiles, plugins, MCP bindings and connectors through a common capability-facing surface.

It must preserve the concrete native type and existing owner records.

```text
Capability Passport
  = governed capability classification + exact-release eligibility

CapabilityBinding
  = exact replaceable implementation relation

CapabilityActivation
  = scoped governance activation of one exact binding

CapabilityCompatibilityObservation
  = compatibility observation for the exact release

Task Contract / Execution Admission
  = task/run legitimacy

Tool Card
  = Cockpit projection only

native runtime
  = installation, enablement and execution mechanics
```

Forbidden collapse:

```text
catalogued != discovered
installed != approved
enabled != activated for a scope
activated != task-authorized
healthy != compatible
compatible != safe
update_available != update_authorized
technical receipt != Evidence
runtime success != Evidence
projection != persistence
```

## 2. Cockpit responsibility

The Cockpit may expose:

- inventory or catalogue observations supplied by existing owners;
- provenance and exact-release information when supplied;
- installation/native-state observations;
- governance, activation, compatibility, safety and freshness dimensions without reconstructing them in the browser;
- dependencies, permissions/effects, Evidence expectations and rollback posture;
- the next required human decision;
- bounded action candidates such as install, enable, disable, update, suspend or retire when a reviewed native adapter supports them.

The Cockpit must not:

- create a parallel capability catalogue merely for UI navigation;
- infer governance state from runtime state;
- treat the supplementary Tool catalogue as authority;
- expose provider secrets to the browser;
- install or execute capabilities itself;
- chain consequential mutations implicitly;
- turn a successful native receipt into approval, Evidence or task authorization.

Raw runtime configuration assistance remains separate and is governed by `COCKPIT_RUNTIME_CONFIGURATION_ASSISTANCE.md`.

## 3. Consequential action flow

One consequential capability mutation follows the existing governance path:

```text
1. Read the current supplied/native observation.
2. Build one bounded action candidate.
3. Route the action through the existing policy/preflight chokepoint.
4. Require the applicable human decision.
5. Invoke exactly one reviewed external/native operation.
6. Return a technical receipt and fresh observation.
7. Project the result without inferring Evidence, approval, activation or task authorization.
```

No chained transition is implied:

```text
install -> does not automatically enable
enable  -> does not automatically activate globally
activate -> does not authorize a task
update  -> requires its own authorization
retire/remove -> remains separately consequential/destructive
```

## 4. Version and adapter posture

Native lifecycle mutations are valid only through an explicitly reviewed adapter surface for the observed runtime/version.

An adapter should identify:

```text
runtime product
supported version/range
native API, CLI or plugin surface
supported capability types
supported actions
readback method
rollback method when applicable
```

Unknown or incompatible version posture is fail-closed for mutation. Read-only observation may remain available only where its contract is still known to be safe.

```text
unknown adapter compatibility
-> mutation disabled
-> explicit to_verify observation
-> no guessed YAML/JSON/file patch
```

## 5. Current executable seams

The co-located implementation already contains bounded pieces of this model.

### 5.1 Capability lifecycle seam

`implementation/mvp_vertical/capability_manager.py` implements a bounded candidate lifecycle seam for one supplied `CapabilityRecord` at a time.

It currently supports planning and guarded transitions for:

```text
propose_install
install
enable
disable
update
suspend
retire
```

Consequential transitions require the existing policy chokepoint and a human decision before the injected external executor is called. The manager does not persist a canonical capability catalogue and does not execute the capability itself.

`HermesCapabilityExecutor` is only a generic transport seam for a separately reviewed native operation endpoint. It deliberately has no guessed default Hermes capability-management endpoint.

### 5.2 Tool Card projection

The current Cockpit Tool Card path is documented by `implementation/docs/TOOL_CARD_IMPLEMENTATION.md` and tested under `implementation/tests/test_cockpit_tool_cards.py`.

The single projection path can display supplied exact-governance dimensions such as:

```text
binding identity
immutable implementation anchor
activation state/scope
compatibility status
safety status
freshness/source observation
```

Missing canonical values remain `not_observed`; the browser does not derive them from catalogue/runtime observations.

### 5.3 Canonical validation owner

Capability Passport validation is implemented read-only in `mcp-server/pantheon_mcp/passports.py` against `schemas/capability_passport.schema.yaml`.

It qualifies candidate shape and exact-release eligibility only. It has no activation, write or task-authorization effect.

## 6. Remaining implementation gaps

The following remain real gaps and must not be described as implemented:

- no unified live server-side feed currently joins canonical Passport/Binding/Activation/Compatibility records into every Cockpit capability projection;
- no public `Compétences` Cockpit root is currently implemented;
- the current Navigation Registry exposes `Workspace` as a root instead;
- no generic durable Cockpit capability inventory is introduced here;
- broader native adapters for all capability kinds are not established;
- workflow/runtime-agent authoring remains dependent on reviewed native contracts;
- target installation or production activation is not implied by repository code or CI.

A future live feed must reuse the existing canonical owners. The absence of that feed is an integration gap, not justification for a new registry.

## 7. Compétence boundary

`Compétence` is not a synonym for Workspace, runtime Skill or Tool.

```text
Compétence
  = governed reusable business ability

Capability
  = governable effect/capability abstraction according to capability doctrine

Skill
  = external runtime realization of a governed ability

Tool
  = technical means

Workspace
  = read-only filesystem projection where configured
```

The Cockpit must not satisfy the product `Compétences` space by relabelling `Workspace`, the Tool catalogue or a Hermes inventory.

If a Compétence projection is implemented later, it must compose existing governed owners and preserve the distinction between a business-facing ability and its replaceable technical implementations.

## 8. Validation posture

Current executable coverage includes:

- `implementation/tests/test_capability_manager.py` for legal transitions, human-decision gates, policy refusal and external-executor isolation;
- `implementation/tests/test_capability_executor.py` for the explicit external transport seam;
- `implementation/tests/test_cockpit_tool_cards.py` for direct Tool Card projection and non-inference of authority;
- repository CI for the co-located implementation.

These tests establish behavior of the candidate implementation only.

```text
tests green != adopted
repository implementation != target installation
technical receipt != Evidence
runtime success != authorization
```

## 9. Final rule

Keep the Cockpit simple by projecting existing authority, not by recreating it.

```text
one semantic owner per governed fact
one bounded external operation per consequential decision
one projection may combine many owners
no projection becomes persistence or authorization
```
