# Cockpit — Living Cards

Status: candidate presentation implementation in `pantheon-mvp`.

## Purpose

Living Cards give the operational Cockpit a recognisable physical-card language without changing Pantheon authority, data ownership or governance semantics.

The presentation remains downstream of the server-authoritative model:

```text
entity / governed state
→ projection
→ card renderer
→ optional presentation metadata
→ DOM
```

A gradient, icon, animation or card face is presentation metadata only. It is not a status, authorization, Evidence, Claim or source-of-truth marker.

## Current page and bootstrap

`mvp_vertical/cockpit/index.html` is the single Cockpit page, served at `/cockpit/`. The static demonstration uses the same page with `?mode=demo`.

`live_bootstrap.js` loads the current registries, navigation adapter, collection adapter, projection, actions and editors in an explicit order. There is no separate generation-specific page or bootstrap.

Several DOM identifiers still contain `v2-` for current compatibility. They are implementation residue, not architecture identities and not a contract for future modules.

## Card projection and rendering

Current owners include:

```text
structured_interface.js
projection/cockpit_projection.js
projection/card_projection_definition_loader.js
rendering/card_renderer.js
rendering/tag_icons.js
registries/card_projection_definitions.json
registries/tag_registry.json
```

The server and projection determine card identity, family, status, tags, limits and actions. The renderer formats these values but does not create semantic authority.

## Material registry

`mvp_vertical/cockpit/registries/materials.json` carries:

```text
schema_id = cockpit.materials
revision = 1
assignment.strategy = stable-entity-hash
```

Assignment is deterministic from stable projected identity where available. The same card may therefore receive the same material without storing a consequential value in the backend.

The registry does not encode card family, status, approval, health, safety or task authorization.

## Interaction contract

- horizontal movement: siblings in the current collection;
- vertical navigation: declared parent/child navigation stack;
- activation on a non-interactive card area: front/back flip;
- front: reading surface;
- back: details and declared actions;
- embedded controls retain their own interaction;
- Hermès remains opt-in through the handoff surface.

Navigation ownership is documented in `docs/architecture/cockpit-navigation-lifecycle.md`.

## Progressive degradation

Registry or optional Swiper loading failures must not invent semantic state. The Cockpit may fall back to simpler navigation or visible presentation defaults while preserving the underlying card projection and explicit failure posture.

```text
presentation unavailable != entity unavailable
animation failure != workflow failure
material fallback != status change
```

## Preserved distinctions

```text
projection != governed value
material != status
UI state != authorization
runtime success != Evidence
installed != approved
healthy != safe
activated != task_authorized
```
