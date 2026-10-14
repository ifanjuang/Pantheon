# Role Dialogue Trace

Status: candidate support specification — legacy compatibility path retained for
existing Cockpit consumers after the Role/runtime convergence of Pantheon-Next#1085/#1086.

This document no longer defines the active Hermes presentation model.

The canonical boundary is:

```text
Pantheon Role
= governance jurisdiction

Hermes runtime
= execution

Ulysse / Nestor / Dédale / Cassandre
= optional work postures

runtime milestone
= observable presentation only
```

## Why this surface is legacy

The first implementation projected model-authored headers such as
`Athena · Analyse`, `Argos · Sources` or `Zeus · Statut` into transient
`role.stage` events and displayed them as Cockpit dialogue/graph lanes.

That was intentionally non-authoritative, but the architecture has since
converged further: Pantheon Roles are not runtime identities and normal Hermes
work no longer needs one visible Role label per cognitive function.

Therefore new Hermes presentation must not manufacture Pantheon Role state from
model prose.

```text
model says "Athena" != ATHENA Role activated
role-labelled prose != governed Role observation
visible lane != authority
projection != persistence
runtime completion != Evidence
runtime success != authorization
```

## Current compatibility behavior

The following implementation remains temporarily available because it has real
Cockpit consumers and provides useful bounded observability:

```text
implementation/mvp_vertical/hermes_role_stage_projection.py
implementation/mvp_vertical/hermes_role_trace_relay.py
implementation/mvp_vertical/cockpit/handoff/role_dialogue.js
implementation/workspace_cockpit/static/app.js
```

The relay is in-memory, bounded and read-only. It does not create or control a
Hermes run, persist a Role Signal, approve a result, promote Evidence, authorize
an effect, schedule work or expose private reasoning.

The legacy projector may still recognize old role-labelled public messages for
backward compatibility. That compatibility must not be treated as the preferred
producer contract.

No new producer should be added that requires those labels.

## Active presentation target

New governed runtime presentation uses generic Hermes milestones:

```text
⚙ Hermes · Plan
⚙ Hermes · Source vérifiée
⚙ Hermes · Production
⚙ Hermes · Statut
```

When the governed method actually selects a work posture and the label is useful,
a milestone may additionally expose:

```text
Posture: Ulysse
Posture: Nestor
Posture: Dédale
Posture: Cassandre
```

Those names remain work postures, not identities, profiles or authorities.

```text
posture selected != Pantheon Role activated
posture changed != profile changed
posture changed != subagent created
milestone emitted != runtime dispatch
```

Runtime topology remains a separate projection of explicit Hermes identifiers
such as `subagent_id` and `parent_id`. It must never infer Role relations from
postures, timestamps, textual handoffs or model prose.

## Governed Role references

A Pantheon Role may still be displayed when a governed Pantheon object explicitly
records that Role viewpoint, responsibility or decision context. In that case the
Role comes from Pantheon state, not from a language-model header.

This compatibility document does not define such a persisted Role event.

```text
governed Role reference -> may be projected
model-authored Role header -> legacy presentation only
runtime worker -> never a Pantheon Role
```

## Migration posture

Do not add a second trace service or rename the whole path merely for cosmetic
purity.

The safe convergence sequence is:

```text
active profile stops producing Role-labelled runtime prose
-> generic activity milestones become normal
-> observe remaining consumers of legacy role.stage
-> retire/rename the compatibility projector only when no useful consumer depends on it
```

Until that final retirement, keep the compatibility path bounded and explicitly
non-authoritative.

## Final invariants

```text
Pantheon governs; Hermes executes.
Pantheon Role != Hermes runtime identity.
work posture != Pantheon Role.
runtime topology != governance topology.
projection != persistence.
retrieved != true.
runtime result != Evidence.
successful execution != authorization.
```
