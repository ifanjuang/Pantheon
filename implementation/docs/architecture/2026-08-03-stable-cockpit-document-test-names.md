# Stable Cockpit document and test names

Date: 2026-08-03

Status: applied naming convergence — no runtime or authority change.

## Purpose

This tranche completes the `pantheon-mvp` portion of convergence step C. Active documents and tests no longer carry permanent V2, V3 or V019 architecture identities.

## Documents

```text
docs/COCKPIT_V2_NOTION_AGENCY_BINDING.md
→ docs/COCKPIT_NOTION_AGENCY_BINDING.md

docs/COCKPIT_V2_STRUCTURED_INTERFACE.md
→ docs/COCKPIT_STRUCTURED_INTERFACE_FOUNDATION.md

docs/HERMES_V019_RUNS_API_OBSERVATION.md
→ docs/HERMES_RUNS_API_OBSERVATION.md

docs/cockpit/COCKPIT_V3_LIVING_CARDS.md
→ docs/cockpit/COCKPIT_LIVING_CARDS.md
```

The documents were not blindly copied:

- the Notion document now reflects the current removable browser-local policy seam;
- the cumulative structured-interface note is explicitly historical rather than a competing current architecture map;
- Hermes `v0.19` is retained as observed external-release metadata inside the document, not in the Pantheon-owned filename;
- Living Cards now documents the current single page, bootstrap, renderer and material registry.

## Tests

The active test filenames are responsibility-based:

```text
test_cockpit_demo.py
test_cockpit_change_candidates.py
test_cockpit_design_refinement.py
test_cockpit_handoff.py
test_cockpit_native_shell.py
test_cockpit_spatial_navigation.py
test_cockpit_tool_cards.py
```

Assertions that mention `v2-` or `v3-` DOM/CSS seams remain where they verify current compatibility or the absence of retired assets. Those seams are implementation residue to be removed only with a bounded functional migration, not hidden by renaming tests.

## Debt reduction

```text
generation-named artifacts: 18 -> 7
```

The seven remaining baseline entries all belong to `Pantheon-Next` and require a separate classification of active governance documents, historical assets and prompt revisions.

Internal versioned route debt remains unchanged in this tranche:

```text
route files:        9
route declarations: 44
```

## Preserved boundaries

```text
filename identity != schema revision
external release metadata != Pantheon architecture generation
historical note != current contract
DOM compatibility seam != authorization
presentation document != backend authority
```

No route, schema, persistence model, runtime, scheduler, queue, provider binding, Evidence rule or approval behavior changes.
