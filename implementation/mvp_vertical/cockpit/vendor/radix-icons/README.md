# Radix Icons — pinned Cockpit source

This directory records the Radix Icons source selected and activated for the Pantheon MVP Cockpit presentation layer.

Upstream: `radix-ui/icons`
Upstream commit: `112af91ad275a63c3a29b0da2588342af74ef9bf`
Upstream icon directory: `packages/radix-icons/icons/`
Upstream manifest: `packages/radix-icons/manifest.json`
License: MIT, Copyright (c) 2022 WorkOS. See `LICENSE`.

## What is present

Two layers are kept deliberately distinct:

1. `upstream/` is the complete Radix Icons repository pinned as a Git submodule to the exact reviewed upstream commit. It provides the complete source set, including all 331 15×15 icons declared by the upstream manifest.
2. `icons/` contains SVG files copied verbatim into the MVP tree for Cockpit use. The committed selection covers the icon keys used by the current Cockpit. `materialize-icons.sh` can copy the complete pinned SVG set from the checked-out submodule into this directory for a reviewed re-vendoring commit.

Clone with the pinned source available:

```bash
git clone --recurse-submodules https://github.com/ifanjuang/pantheon-mvp.git
```

For an existing checkout:

```bash
git submodule update --init --recursive
```

To materialize every pinned SVG into the main MVP tree:

```bash
mvp_vertical/cockpit/vendor/radix-icons/materialize-icons.sh
```

The script refuses to copy if the checked-out submodule commit differs from `UPSTREAM_COMMIT`.

## Cockpit activation

The Cockpit presentation binding is active and native to the primary renderer:

- `styles/cards.css` maps semantic Cockpit icon keys to the vendored Radix SVGs;
- `app.js` creates `.radix-icon` elements directly for cards and responsibility indicators;
- the detail close control uses the Radix `cross-2` asset directly;
- there is no secondary icon shim and no legacy inline 24×24 icon-path fallback;
- existing text labels, status labels and governed records remain authoritative.

## Boundary

These files are presentation assets only.

```text
icon displayed != governed status
healthy icon != safe
check icon != approval
runtime success != evidence
binding activated in Cockpit != Hermes runtime activation
upstream update_available != update_authorized
```

Pantheon governs the semantic meaning exposed by the Cockpit. The Cockpit renders these assets. Hermes does not execute them. Human decisions remain explicit records rather than icon states.

## Snapshot policy

The upstream pin is immutable until a reviewed change updates `UPSTREAM_COMMIT`, the submodule pointer and any materialized assets together. There is no automatic updater.

`SELECTION.md` owns the current Cockpit-key → Radix-asset presentation mapping. An icon mapping does not own object identity, lifecycle, approval or Evidence status.

The Radix source pin is not an npm installation and does not activate any Hermes or Pantheon runtime capability.
