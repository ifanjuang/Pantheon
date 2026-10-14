# Tool Card implementation

Status: executable candidate — catalogue, GET-only Hermes observation adapter, spatial catalogue projection and direct I7 exact-governance projection implemented; live Hermes observation and canonical I2–I6 records are not yet connected to the Cockpit deployment path.

Pantheon Next owns Capability governance and the canonical I2–I6 contracts. This repository owns concrete catalogue records, normalized runtime/Hermes observations and the executable Cockpit projection. Hermes owns native discovery and execution. The Cockpit never becomes the owner of binding, activation, compatibility, safety or authorization state.

The absence of a live canonical feed is an integration/deployment posture, not a second semantic owner. I7 is complete when the existing Tool Card can project the canonical dimensions when supplied, keeps missing values explicitly `not_observed`, and never reconstructs authority from browser/runtime state. Connecting a future server-side feed must reuse those owners rather than create another binding/activation/compatibility model.

## Implemented here

- `mvp_vertical/cockpit/tool_catalog.json`: concrete supplementary catalogue, not authority.
- `mvp_vertical/hermes_tool_inventory.py`: GET-only normalization of reviewed Hermes discovery surfaces.
- `mvp_vertical/cockpit/data/cockpit_data_loader.js`: `loadToolCatalog()` reads the catalogue as an optional collection, so an unreachable catalogue degrades visibly instead of inventing state.
- `mvp_vertical/cockpit/projection/cockpit_projection.js`: the single Tool Card construction path. `normalizeTool()` projects the ordinary catalogue/runtime axes and the optional exact I7 fields directly on the same card model; there is no post-build decorator or browser-side governance join.
- `mvp_vertical/cockpit/projection/child_collection_assembler.js`: resolves the Tool Card collection for spatial navigation.
- independent axes remain visible for catalogue, installation, native state, health, governance, update, activation, compatibility, safety and freshness.
- consequence-bearing permissions remain known/unknown/potential; unknown is never inferred safe.
- Haystack remains a candidate only; LlamaIndex/LangChain/LangGraph remain watch/comparison entries. No dependency is selected, installed, approved or activated by this catalogue.

## I7 exact-governance projection

The direct Tool Card projection accepts these optional fields on a Tool catalogue/projection record:

```text
binding_id
implementation_anchor.kind
implementation_anchor.value
activation_state
activation_scope.scope_type
activation_scope.scope_id
activation_scope.scope_label
compatibility_status
safety_status
freshness_status
source_observation_ref
compatibility_observed_at
```

They mirror, without owning, the Pantheon-Next I2–I6 dimensions:

```text
Capability Slot
  -> exact Capability Binding
  -> immutable implementation/release anchor
  -> scoped governance activation
  -> exact-release compatibility observation
```

The current catalogue intentionally does not invent canonical binding IDs, release digests, activation decisions or compatibility observations for its existing framework entries. Until an authoritative server-side projection supplies those values, the I7 fields display `not_observed`.

This boundary is intentional:

```text
projection contract complete != live canonical feed deployed
canonical record absent from response != canonical state absent
runtime observation != governance record
browser join != authority
```

A later server-side join is admissible only when an operational Cockpit path requires it. It must read/project the canonical owners and must not make `tool_catalog.json`, Hermes inventory or the browser a persistence or authorization source.

## Spatial projection

The active Cockpit keeps one schema-driven CardShell path. No alternate Tool renderer and no post-build Tool governance decorator are introduced. `normalizeTool()` creates one Tool Card model from the supplied projection record, and `child_collection_assembler.js` exposes that same model through the `tools` source.

```text
Outils
  ↓
tool_catalog.json / future server projection
  ↓
normalizeTool()
  ↓
Tool Card siblings
  ├─ identity / description
  ├─ Capability Slots
  ├─ exact binding identity
  ├─ immutable release anchor
  ├─ installation observation
  ├─ native state
  ├─ health observation
  ├─ governance state
  ├─ scoped activation
  ├─ compatibility observation
  ├─ safety qualification
  ├─ freshness
  ├─ update state
  ├─ permissions
  ├─ Evidence expectation
  ├─ rollback posture
  └─ next human decision
```

If the catalogue cannot be loaded, the Cockpit displays an explicit catalogue-unavailable card. It does not infer that any runtime/tool is absent or uninstalled.

## Runtime observation

Reviewed Hermes surfaces:

```text
GET /v1/skills
GET /v1/toolsets
GET /v1/capabilities
```

Normalized observations preserve runtime provenance and state but do not become I2–I6 governance records by themselves. The adapter performs no POST, install, enable, update, approval, run launch or activation.

The live observer is deliberately not called from the browser. Its future Cockpit connection must remain server-side so credentials are never exposed to the UI. A future server projection may join canonical I2–I6 records to Tool Cards; the browser must not reconstruct that authority from runtime observations.

## Non-equivalences

```text
catalogued       != discovered
discovered       != installed
installed        != approved
binding_selected != dependency_adopted
native_enabled   != scope_activated
scope_activated  != task_authorized
healthy          != compatible
compatible       != safe
compatible       != activated
update_available != update_authorized
runtime_success  != Evidence
projected        != persisted
projection ready != canonical feed deployed
UI status        != authorization
watchlist_item   != install_instruction
```
