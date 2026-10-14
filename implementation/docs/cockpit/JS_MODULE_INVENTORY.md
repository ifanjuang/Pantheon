# Cockpit JavaScript inventory

## Scope

This inventory describes the browser-side Cockpit code loaded from `mvp_vertical/cockpit`. It does not change Pantheon governance, authorization, Evidence, ChangeCandidate semantics, or server authority.

## Current active chain

`index.html` loads `cockpit_bootstrap.js`.

Live mode then loads `live_bootstrap.js`, which first loads the module boundaries for registries, projection definitions, Swiper, the lazy D3 loader and ordered classic scripts:

- `rendering/tag_icons.js`;
- `projection/navigation_registry_loader.js`;
- `projection/card_projection_definition_loader.js`;
- `navigation/swiper_loader.js`;
- `live_collection_adapter.js` when Swiper is available;
- `visualization/d3_loader.js`, which exposes lazy D3 acquisition but does not load D3 until Runtime Topology needs it;
- `boot/classic_script_loader.js`.

The ordered classic chain is:

1. `shell_controls.js`;
2. `structured_interface.js`;
3. `context_resolver.js`;
4. `agency_data_binding.js`;
5. `spatial_navigation.js`;
6. `projection/navigation_registry_adapter.js`;
7. `projection/decision_request_projection.js`;
8. `projection/project_anatomy_projection.js`;
9. `projection/child_collection_assembler.js`;
10. `data/cockpit_data_loader.js`;
11. `projection/cockpit_projection.js`;
12. `interactions/interaction_policy.js`;
13. `project_claim_view_adapter.js`;
14. `information_view_adapter.js`;
15. `context/context_selection.js`;
16. `handoff/handoff_lifecycle.js`;
17. `handoff/handoff_send.js`;
18. `handoff/runtime_topology.js`;
19. `handoff/role_dialogue.js`;
20. `actions/card_actions.js`;
21. `actions/decision_request_actions.js`;
22. `actions/change_candidate_actions.js`;
23. `actions/change_candidate_review.js`;
24. `schema_editor.js`;
25. `contacts_editor.js`;
26. `information_create.js`;
27. `interactions/card_interactions.js`;
28. `map/map_graph_model.js`;
29. `map/map_layouts.js`;
30. `map/map_tokens.js`;
31. `map/map_corroboration.js`;
32. `map/map_bundle.js`;
33. `map/map_view.js`;
34. `map/map_mount.js`;
35. `map_binding.js`.

The read-only knowledge-map lens (`map/`) binds to the projection snapshot
(`window.PantheonCockpitGraph`) exposed by `projection/cockpit_projection.js`.
`map_binding.js` owns one presentation-only graph host and inserts it into the
verso of rendered `pantheon` cards when absent. This keeps the canonical Swiper
renderer and the supported non-Swiper fallback on the same graph lifecycle.
There is no independent graph menu or graph navigation state. The lens never
fetches or mutates governed state (`map view != data model`, `projection != authority`).

`live_collection_adapter.js` imports `rendering/card_renderer.js` directly. The live collection receives canonical card structure before mount.

Runtime Topology is a separate read-only presentation path. `role_dialogue.js`
keeps the single authenticated Role Trace SSE connection and routes only
`runtime.subagent` projections to `handoff/runtime_topology.js`.
`runtime_topology.js` does not fetch independently. It renders explicit Hermes
runtime identifiers only and may ask `visualization/d3_loader.js` to obtain the
pinned D3 runtime lazily. The D3 layout is presentation only and never becomes
runtime state, a scheduler, a causal model or governance authority.

Demo mode uses the same chain. `live_bootstrap.js` reads `?mode=demo`, loads
`demo_bootstrap.js` to substitute the fixture layer, and then continues through the
identical renderer, provider and classic-script sequence. There is no second demo
application and no second provider.

## Responsibility classification

### Entrypoints and boot

- `cockpit_bootstrap.js`: canonical browser entrypoint and visible boot failure. It selects no mode.
- `live_bootstrap.js`: mode detection and state, ordered application startup and visible failure projection. It records whether Swiper navigation is available; when it is not, it exposes the existing previous/next controls so the supported fallback remains navigable. It exposes the lazy D3 loader without eagerly loading D3.
- `boot/classic_script_loader.js`: ordered loading of explicitly listed classic scripts; it owns no domain state.
- `navigation/swiper_loader.js`: optional Swiper acquisition, version pinning and readiness metadata.
- `visualization/d3_loader.js`: optional D3 acquisition, fixed version, SRI and readiness metadata. Loading D3 does not create graph state or authority.
- `demo_bootstrap.js`: live renderer demo data bootstrap.

### Collection and navigation

- `live_collection_adapter.js`: collection integration boundary and canonical renderer consumer.
- `collection/collection_controller.js`: collection lifecycle and the single caller of responsive collection motion.
- `collection/motion_adapter.js`: sole Swiper instance/API boundary. Compact mobile collections expose the same Swiper navigation with a fraction position indicator; this does not create a second navigation model.
- `collection/navigation_state.js`: navigation state.
- `providers/live_provider.js`: live collection snapshots.
- `spatial_navigation.js`: spatial sibling, descend, ascend and root navigation state.
- `projection/navigation_registry_loader.js`: strict loader for the versioned root-navigation registry.
- `projection/navigation_registry_adapter.js`: read-only projection of registered root identity, order and abstract sources. It does not mutate `PantheonSpatialNavigation`; `cockpit_projection.js` passes the projected root parameters explicitly when creating navigation state.
- `projection/child_collection_assembler.js`: resolves abstract registry sources and assembles root and selected-project child collections. It attaches the server-calculated Project Anatomy projection under the selected Project when that projection belongs to the same Project. It owns no transport, authorization or Evidence semantics.

Registry source names are projection inputs only: they are neither endpoint declarations nor authority grants.

Swiper must remain isolated behind `collection/motion_adapter.js` for instance construction and navigation APIs. Compact cross-axis vertical gestures are translated by the collection adapter into the existing spatial ascend/descend controls; they do not create a second navigation state. Mobile fraction pagination is presentation-only. When Swiper is unavailable, the existing button controls remain the compatibility path rather than a second navigation model.

### Rendering and projection

- `rendering/card_renderer.js`: canonical structural card renderer. It owns card structure only; graph host creation and lifecycle remain in `map_binding.js` so the non-Swiper fallback receives the same map lens.
- `rendering/tag_icons.js`: presentation-only type and subject icon resolver.
- `projection/card_projection_definition_loader.js`: loads declared root projection definitions without creating authority.
- `projection/cockpit_projection.js`: card-model normalization, direct optional I7 Capability-governance presentation, Cockpit state, navigation orchestration and bounded non-Swiper fallback. Root card identities are derived from the Navigation Registry and metadata remain owned by `card_projection_definitions.json`. It delegates all parent-child assembly to `child_collection_assembler.js`.
- `projection/decision_request_projection.js`: projects one Decision Request identity as an attention card. It does not create a Decision, classify a Project, transition Work or authorize execution.
- `projection/project_anatomy_projection.js`: presentation-only adapter for the server-calculated Project Anatomy read model. It projects one secondary `Anatomie du projet` card, stable-object cards and explicitly unmapped source-representation cards. It does not infer hierarchy, absence, authorization, Evidence or canonical state and exposes no actions.
- `handoff/runtime_topology.js`: read-only rendering of explicit `runtime.subagent` nodes and explicit `parent_id` links. Its synthetic run root is display containment only; missing parents are not inferred and D3 is only a replaceable layout layer.
- `structured_interface.js`: structured interface projection.
- `project_claim_view_adapter.js`: ProjectClaim projection adapter.
- `information_view_adapter.js`: Information projection adapter.

The exact Capability fields remain projection-only. Their presence in a Tool Card does not make the catalogue or browser authoritative, and absent canonical values remain `not_observed`.

### Interaction and consequential actions

- `interactions/card_interactions.js`: canonical card activation and flip behavior. Presentation materials are loaded from the stable `registries/materials.json` path.
- `interactions/interaction_policy.js`: interaction policy and navigation locking while a verso is open.
- `actions/card_actions.js`: Information and Work review actions; server authority remains mandatory.
- `actions/decision_request_actions.js`: records an explicit human response to a pending Decision Request and creates a separate Decision record through the server. It does not resume Hermes, execute an action or transition a WorkIssue.
- `actions/change_candidate_actions.js`: human apply/reject actions for ChangeCandidates.
- `actions/change_candidate_review.js`: human-only structured revision request, review annotations and append-only history projection. It creates no Hermes run and does not mutate the Project.
- `handoff/handoff_lifecycle.js`: handoff preview, submission, bounded admission and revocation lifecycle.
- `handoff/handoff_send.js`: convenience adapter that prepares then submits a handoff; it does not admit or dispatch execution.
- `handoff/role_dialogue.js`: read-only progressive Role trace projection for one already-admitted Hermes run and the sole browser consumer of the Role Trace SSE. It multiplexes display events to Role Trace or Runtime Topology and exposes no run-control or approval action.

### Context, bindings and data

- `context_resolver.js`: context resolution.
- `agency_data_binding.js`: agency data binding.
- `data/cockpit_data_loader.js`: bounded browser transport for registries, tool catalogue and read-only Agency Data projections. Its global Decisions read uses the unclassified-only `/decision-inbox`; Project requests use the matching Project route. Project Anatomy is read from the bounded Project route and only `404` (no owner) or `409` (owner unavailable) are treated as an unavailable optional projection; other read failures remain visible.
- `context/context_selection.js`: read-only context search and explicit user selection.
- `map_binding.js`: presentation-only owner of the Pantheon verso graph host and lifecycle glue that mounts/destroys the read-only lens for both canonical and fallback card rendering.

### Editors

- `schema_editor.js`: schema-driven editor.
- `contacts_editor.js`: Contacts editor.
- `information_create.js`: Information creation workflow.
- `actions/change_candidate_review.js`: mobile review dialog over the existing ChangeCandidate review card; it remains an adapter rather than a second editor model.

### Shell

- `shell_controls.js`: shell menu and Hermes dock interactions. The shell no longer owns a graph toggle or graph overlay.

## Confirmed architectural debt

1. `projection/cockpit_projection.js` still combines model normalization, navigation orchestration and a bounded fallback renderer; child assembly and network transport now have separate owners.
2. Compatibility `v2-*` classes and identifiers remain because active HTML, CSS, interaction adapters and published regression surfaces still consume them.
3. `live_bootstrap.js` still combines mode state, ordered script loading and failure projection.
4. Classic scripts communicate through globals, so imports alone are insufficient to prove a file dead.
5. Swiper instance construction and navigation APIs remain isolated behind `collection/motion_adapter.js`.
6. D3 is an optional runtime-topology layout dependency only; topology data ownership remains outside D3.

## Dead-code proof

Before deleting a JavaScript file or compatibility token, establish all of the following reference classes:

- HTML script inclusion;
- static import;
- dynamic import;
- ordered classic-script inclusion;
- global produced and global consumed;
- CSS selector consumption;
- test or published regression surface dependency.

Removal is allowed only when every dependency category is empty.

## Next stages

### Compatibility retirement

Identify `v2-*` classes and identifiers whose dependency graph is empty, remove them in bounded changes and retain those still consumed by active HTML, CSS, interaction adapters or published routes.

### Decision and ChangeCandidate continuation

Decision Requests now have a separate global unclassified projection and Project-classified projection. ChangeCandidate review remains a distinct responsibility. Future variants, coherence-report candidates and conflict-safe offline replay must reuse server-owned proposal, revision, provenance and explicit human-decision contracts rather than create a parallel Decision authority.

### Project Anatomy continuation

The Cockpit surface consumes only the server-calculated Project Anatomy read projection. Observation Bundle coverage is not yet persisted by the executable owner, so the UI must keep absence inference disabled and keep the structure flat until an admitted hierarchy-relation registry exists. Future IFC/Revit/viewer lenses must reuse the same stable identities and source provenance rather than create parallel stores.

### Graphical evolution

Only after the functional compatibility cleanup is stable, apply the ConnorGriffin-inspired method to a new graphical evolution. The graphical layer must consume the existing schema-driven projection contracts and must not introduce backend authority or runtime behavior.

## Invariants

```text
visual projection != semantic model
UI status != authorization
runtime_success != Evidence
retrieved != truth
binding_selected != dependency_adopted
Pantheon != runtime
```
