# Cockpit — optional Notion Agency binding

Status: implementation contract present / external synchronization runtime absent / adoption not authorized.

## Ownership

```text
PostgreSQL = Agency Data system of record
Notion     = optional collaborative projection
Cockpit    = display and interaction surface
Hermes     = external execution runtime
Pantheon   = governance of consequential effects
Human      = consequential decision authority
```

Notion is not in the critical path for Cockpit or Hermes.

## Implemented seam

`mvp_vertical/cockpit/notion_agency_binding.js` implements a removable, browser-local contract for:

- explicit collaboration modes: `disabled`, `mirror_read_only`, `selective_bidirectional`;
- field-policy registration;
- Project projection from the server-owned `notion` schema view;
- revision-conflict classification;
- synchronization-state projection;
- mutation-candidate preparation without execution.

The module does not contain Notion credentials, perform provider I/O, write PostgreSQL or activate synchronization.

## Field policy

Each declared field policy carries:

```text
entity_type
field
notion_visible
notion_editable
sync_direction
conflict_policy
validation_rule
sensitivity
```

A field marked `notion_editable=true` must use `bidirectional` synchronization. Projection or claim fields remain read-only by construction unless a separately reviewed design changes their owner contract.

```text
schema view != write authorization
notion_editable != mutation authorized
mutation candidate != applied mutation
```

## Revision discipline

An inbound candidate requires an explicit Notion base revision and the current PostgreSQL revision.

```text
base revision == current PostgreSQL revision
→ candidate may be prepared

base revision != current PostgreSQL revision
→ conflict
```

No generic last-write-wins policy is provided.

Supported conflict postures:

```text
human_review
merge_append
postgres_authoritative
```

## Runtime placement

A future live adapter belongs outside the Cockpit browser and outside Pantheon's governance kernel. It would own provider authentication, polling/webhooks, transport, retries and synchronization execution.

Pantheon may govern and project:

```text
binding candidate
field policy
installation observation
health observation
update observation
activation state
scope
conflict
consequential gate
```

It does not become the Notion runtime.

## Protected distinctions

```text
Notion available != binding adopted
binding adopted != synchronization activated
synchronization healthy != safe
Notion edit != PostgreSQL mutation
PostgreSQL write success != Evidence
Notion status != authorization
```

Governance-sensitive values such as Evidence status, Pantheon Decision status, capability approval/activation and task authorization remain outside generic Notion editing unless a separate reviewed contract explicitly permits a bounded projection.
