# Cockpit knowledge map (read-only lens)

Status: implemented candidate — a bounded, read-only visual lens over the
existing Cockpit projection. Live mounting is wired into the Pantheon card
verso; there is no separate global map menu or overlay.

## Invariants (tested)

```text
map view != data model
projection != authority
read-only : no fetch, no mutation, no run launch, no memory promotion
```

The map reshapes and draws the **already-normalised** card graph. It decides
nothing and admits nothing. `tests/test_cockpit_map.py` enforces the read-only
boundary (no `fetch`/storage/socket) and the declared invariants.

## What it binds to

The in-memory projection produced by `../projection/cockpit_projection.js`:

- `state.cards` — `Map<entity_id, cardModel>`;
- `state.children` — `Map<parentId, entity_id[]>`.

The projection exposes a **read-only snapshot** as
`window.PantheonCockpitGraph = Object.freeze({ cards, children })` and fires
`pantheon:graph-updated` after each rebuild. The lens reads that snapshot; it
never writes back. It reads only projected fields (`entity_id`, `entity_type`,
`presentation_family`, `title`, `status`, `date`, `subject_tags`, `series_id`,
`base_acted_id`, `source_run_id`, and a `magnitude` hint when present). It never
calls the HTTP API, so the stable-route convergence (no `/v1`) does not affect
it — the map sits above the transport seam.

## Modules

- `map_graph_model.js` — pure `build(cards, children) -> { nodes, links }`
  (containment + version lineage). `node.origin` records the factual source
  (`agency` / `knowledge` / `hermes`) — **not** an authority claim.
- `map_layouts.js` — swappable layout registry, each a pure
  `(nodes, opts) -> {id:{x,y}}` (`cluster`, `radial`, `grid`, `chain`).
  Deterministic, no force. Add a graph type = add one entry.
- `map_tokens.js` — read-only token resolver: subject colour + icon, status
  colour, origin border, magnitude→radius. Registries are dependency-injected
  (pass the real `tag_registry` / `status_registry`), with a bundled fallback.
  Colour is never the sole identifier — an icon disambiguates same-colour
  subjects (the registry collapses ~33 subjects onto ~9 colour tokens).
- `map_corroboration.js` — pure support-edge builder (corroboration /
  contradiction) + candidate certainty aggregation. **Gated**: returns `[]`
  until cards carry support refs (only the negative `contradictory_review`
  signal exists upstream today).
- `map_bundle.js` — hierarchical edge bundling for the support overlay
  (deterministic, no force). Renders empty when there are no edges.
- `map_view.js` — read-only SVG renderer wiring the layers: subject colour +
  icon, origin border, status badge, magnitude sizing, organic metaballs,
  containment + lineage links, support overlay (HEB), subject focus, and a time
  scrubber. `create(svg, {cards, children}, opts)` →
  `{ setLayout, setGroupBy, setLens, setMeta, setSupport, setFocus, setTime,
  render, destroy }`.
- `map_mount.js` — live mount hook: `mountLive(svg, opts)` renders from
  `window.PantheonCockpitGraph` and refreshes on `pantheon:graph-updated`.

## Default layout per scope (caller's choice)

```text
project (overview)  -> radial (family satellites)
documents           -> chain  (revision lineage)
information         -> chain  (version lineage)
knowledge           -> grid   (dense scan)
subject view        -> cluster (organic grouping)
```

## Live card mount (wired)

`../map_binding.js` (loaded by `../live_bootstrap.js`) owns the single
presentation-only graph host. It detects every rendered `pantheon` card, inserts
the host into its verso when absent, builds tokens from the loaded tag registry
(`PantheonTagIcons`) and mounts the existing lens through
`map_mount.mountLive`. This keeps the canonical Swiper renderer and the supported
non-Swiper fallback on the same graph lifecycle instead of duplicating a second
map surface.

When a Pantheon card leaves the stage DOM, the binding destroys that mount and
removes its graph-update subscription before a later clean remount. The map
controls (`cluster`, `radial`, `grid`, `chain`, corroboration) live in the verso
host. The global `#v2-map-toggle` / `#v2-map-panel` surface is retired: the graph
is a card detail lens, not a parallel Cockpit navigation surface.

## Data-gated layers

- **Support overlay / HEB** — the **conduit is wired**: `cockpit_projection.js`
  now passes `corroboration_refs` / `contradiction_refs` (or `support_refs`)
  through to Information / Document / Knowledge cards, and `map_corroboration`
  reads them. It still renders empty until the **producer** emits those refs
  (a governed step: contradictory_review / a corroboration projection → per-card
  refs). `corroboration != promotion` — a certainty ring stays candidate.
- **Magnitude sizing** — uses `magnitude` / `page_count` / `chunk_count` when
  present; falls back to a base radius otherwise.

## Try it

Open `demo.html` — it builds a small in-memory `{cards, children}` and mounts the
view. No network, no build step.
