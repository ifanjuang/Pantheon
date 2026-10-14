# Tool Capability Card Contract

Status: candidate support doctrine — documented non-implemented.
Boundary profile: candidate_support_note.

This document defines the governance information that a cockpit Tool Card must preserve. It does not define the executable UI, catalogue store, Hermes inventory reader, installer or runtime adapter.

The concrete card implementation belongs to the bounded Pantheon implementation under `implementation/`. Product-specific candidate bindings remain in `HERMES_CAPABILITY_BINDINGS.md`.

## Purpose

A Tool Card is a governance projection over one concrete tool, skill, plugin, function, MCP binding, workflow runtime or adjacent capability product.

Minimum visible contract:

```text
identity and title
short + operational description
resource type / native owner
Capability Slot relationship
source and provenance
installation observation
native runtime observation
health observation
update observation
Pantheon governance status
scope activation status
permissions / consequence-bearing effects
evidence expectation
rollback posture
last observation
next required human decision
```

## Provenance classes

```text
hermes_native_inventory
hermes_dynamic_skill
runtime_installed
pantheon_catalog
external_reference
operator_declared
discovered_binding
```

`hermes_dynamic_skill` means a skill discovered through Hermes-owned native inventory or reviewed adapters. Pantheon may qualify the normalized observation; it does not become the skill loader.

`pantheon_catalog` means a documented candidate/reference. Catalogue presence is not runtime presence.

## Required non-equivalences

```text
catalogued       != discovered
discovered       != installed
installed        != approved
native_enabled   != scope_activated
healthy          != safe
update_available != update_authorized
runtime_success  != evidence
binding_selected != dependency_adopted
watchlist_item   != install_instruction
```

These axes remain independent.

## Capability Slot placement

Every concrete relationship should be expressible as:

```text
abstract capability
-> candidate binding
-> installation status
-> health status
-> update status
-> activation status
-> Pantheon gates
-> human approval
```

A card also preserves:

```text
exposed_by
executed_by
governed_by
approved_by
forbidden
```

A product may satisfy several Capability Slots without becoming an adopted dependency for all of them.

## Consequence-bearing dimensions

When applicable, the card exposes known/unknown status for:

```text
file read / write
command execution
network/browser access
external API read / write
external communication
repository mutation
runtime configuration mutation
package installation
credential handling
private project-data access
memory-candidate production
external artifact production
```

Unknown permissions stay unknown; they are never inferred safe.

## Evidence and technical receipts

```text
technical receipt != Evidence Pack
trace             != proof
successful probe  != safety
successful run    != approved result
```

The evidence expectation for consequential use remains separate.

## Reconciliation contract

A cockpit may reconcile Pantheon catalogue records with normalized Hermes/runtime observations while preserving disagreement.

Valid outcomes include:

```text
catalog_only
runtime_only
matched
version_drift
metadata_drift
possible_duplicate
source_unknown
adapter_incompatible
to_verify
```

Preferred matching uses stable native identifiers, admitted capability/skill identifiers, pinned source references or explicit operator mappings. Ambiguous records remain separate.

## Ownership boundary

```text
Pantheon governance
  governance contract, Capability Slot placement, status distinctions,
  evidence/approval/scope rules and candidate binding doctrine.

Pantheon implementation (`implementation/`)
  concrete catalogue records, executable card projection and
  normalized runtime/Hermes inventory reconciliation.

Hermes
  native skill/tool/plugin/MCP/workflow discovery and execution mechanics.

OpenWebUI / Cockpit
  exposure and decision surfaces.

Human
  consequential adoption, installation, activation, update and use decisions.
```

The historical `pantheon-mvp` repository is provenance for the imported implementation at cutoff `d960862dd0e23b7003a0f3e4ee0ea630ffc12af9`; it is not the current owner path.

## Retrieval/framework candidates

Specific frameworks such as Haystack, LlamaIndex, LangChain or LangGraph are not duplicated here. Their placement belongs in `HERMES_CAPABILITY_BINDINGS.md` and specialized binding doctrine.

```text
Capability Slot documented != preferred binding selected
candidate binding != dependency adopted
```

## Boundary

This contract creates no runtime behavior, executable card, installer, updater, plugin manager, skill manager, scheduler, queue, provider router, MCP host or automatic approval path.
