# Pantheon candidate catalog

Status: candidate declarative data — non-executable.

This directory is a bounded proving ground for independent capability, resource, binding, activation and observation records used by the common governance baseline.

```text
Capability
Resource
Capability Binding
Capability Activation
Capability Compatibility Observation
Module status
```

A `CapabilityBinding` is a relation only:

```text
Capability Slot
-> Capability Passport reference
-> exact immutable implementation anchor
```

It does not copy the Capability Passport or implementation provenance body, and it does not install, adopt, activate or authorize anything. `unbound` is an explicit valid state when a slot remains profile- or project-specific.

A `CapabilityActivation` records only governance activation for one exact binding and scope. It has no runtime activation effect and no task-authorization effect.

A `CapabilityCompatibilityObservation` references an externally produced observation for one exact binding/release. It keeps compatibility, safety, health/freshness, activation, authorization and Evidence as separate axes; Pantheon performs no probe by creating the record.

## Synthetic fixtures vs field observations

`catalog/examples/` may contain synthetic conformance fixtures that exercise the schemas and cross-record invariants. Their identities, digests, timestamps and compatibility states are test data only even when the fixture itself validates against `CapabilityCompatibilityObservation`.

`catalog/observations/` is reserved for binding-scoped field observations backed by an actually observed implementation anchor. Synthetic placeholder anchors such as repeated-character SHA-256 values must not be stored there.

A substantial runtime/source qualification performed before a legitimate `CapabilityBinding` exists remains with its existing source owner (for example the relevant qualification note, audit or runtime/source-adapter record). It does not become a `CapabilityCompatibilityObservation` merely because compatible vocabulary exists.

When a legitimate binding is later selected, linking is explicit:

```text
pre-binding field qualification
-> explicit binding selection
-> binding-scoped compatibility observation
   with exact observed implementation anchor
   and source_qualification_ref when useful
```

No step is inferred automatically. In particular, the Hindsight 0.9.1 / Hermes / Obsidian qualification from Pantheon-Next#655 remains a pre-binding field qualification while `external_runtime_memory` is `unbound`; it must not cause creation of a Hindsight binding or passport merely to fit this catalog.

```text
synthetic fixture != field observation
field observation != binding selection
binding selected != dependency adopted
compatibility observed != safety qualified
runtime success != Evidence
```

The common required component set is defined only by:

```text
docs/governance/COMMON_INSTALLATION_BASELINE.md
```

Historical installation-composition manifests and their schema have been removed. They remain available only through Git history and are listed in `docs/governance/authority/OBSOLETE_AND_ABSENT_INDEX.md`. The bounded binding/activation/observation relations do not restore those Presets or installation-composition manifests.

The remaining catalog files do not create a live runtime registry, installer, provisioner, connector, OAuth flow, secret store, runtime, scheduler, queue, approval engine, memory engine, runtime activator or health probe.

Required distinctions:

```text
manifest_present != resource_installed
candidate_resource != selected_binding
binding_selected != dependency_adopted
binding_selected != installed
binding_selected != activated
activated_for_scope != task_authorized
healthy != compatible
compatible != safe
compatible != activated
compatibility_observation != Evidence
unbound != missing_governance
connected != authorized_for_scope
```
