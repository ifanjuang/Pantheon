# Cockpit structured-interface foundation

Status: historical reference — not a current architecture map.

This file succeeds the former `COCKPIT_V2_STRUCTURED_INTERFACE.md` implementation note.

The former note described an intermediate branch state. Its route paths, module names and implementation statuses no longer match the current `main` branch, so they are not reproduced as active documentation.

## Durable decisions

```text
PostgreSQL Agency Data = native agency system of record
Cockpit                = projection and interaction surface
Hermes                  = external execution runtime
Pantheon                = governance of consequential effects and statuses
Notion                  = optional collaborative projection
Human                   = consequential decision authority
```

Durable distinctions:

```text
Card != source of truth
PostgreSQL ownership != Pantheon governance authority
Work Issue assigned_to=hermes != Hermes run
runtime callback != command to start
runtime success != Evidence
```

## Current sources

Read the focused owners instead:

- `mvp_vertical/cockpit/` — current implementation;
- `docs/cockpit/COCKPIT_LIVING_CARDS.md` — presentation boundary;
- `docs/architecture/cockpit-navigation-lifecycle.md` — navigation ownership;
- `docs/architecture/ARCHITECTURE_CONVERGENCE_EXECUTION_PLAN.md` — convergence plan;
- `docs/COCKPIT_NOTION_AGENCY_BINDING.md` — optional Notion seam;
- `docs/HERMES_RUNS_API_OBSERVATION.md` — external Hermes observation;
- Pantheon-Next — semantic and authority owners.

The original detailed snapshot remains available in Git history.

```text
historical note != current contract
old route list != compatibility requirement
past module name != permanent architecture identity
```
