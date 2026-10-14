# Notion Agency Data Binding for Pantheon Cockpit V2

Status: candidate support doctrine — PostgreSQL-master / optional Notion collaborative binding documented; executable policy seams exist externally in `pantheon-mvp` PR #65; live synchronization not implemented.

Boundary profile: candidate_support_note.

Decision date: 2026-07-24.

## 1. Purpose

This document specializes `AGENCY_DATA_SYSTEM_OF_RECORD.md` for the agency Notion workspace.

The current decision is:

```text
PostgreSQL Agency Data
= native system of record

Notion
= optional collaborative projection
```

Notion may display selected Agency Data fields and may be allowed to edit some explicitly declared fields.

```text
Notion editable != Notion authoritative
Notion connected != Notion required
sync completed != Evidence
```

## 2. Core architecture

```text
                     POSTGRESQL
                 Agency Data master
                      ▲      ↓
        allowed edit  │      │ projection
                      │      │
                    NOTION
               optional collaboration

Cockpit/Hermes read native Agency Data from PostgreSQL-backed services.
Hermes writes native Agency Data through bounded Agency Data capabilities.
```

Notion is not in the critical path for normal Agency Data operation.

## 3. Agency pilot mapping

The observed agency workspace remains highly useful as a collaborative surface.

### `_Affaires`

Observed relevant properties include:

```text
Code
Statut
Phase
Lieu
Description
Budget
Contrat
DROC
Date Arrêté
Date dépot
Réception
Levée des réserves
No Permis
Numéro de Parcelle
Zone PLU
Srf Terrain
Srf Construite
Srf Démol
Srf plancher Existante
surface Taxable
Emprise Existante
Emprise Créée
Emprise supprimé
GEORISQUE
Lien GNAU
dossier MAF
type ERP
Intervenants
_Décisions
```

Candidate Agency Data concept:

```text
Project / Affaire
```

### `_Personnes`

Observed fields:

```text
Nom
E-mail
Numéro
adresse
Société
```

Candidate Agency Data concept:

```text
Person
```

### `_Sociétés`

Observed fields:

```text
Name
E-mail
Téléphone
Adresse
siret
RIB
Personnes
```

Candidate Agency Data concept:

```text
Organization
```

Sensitive or unnecessary fields are not exposed merely because they exist. `RIB`, for example, is outside ordinary Context Resolver search.

### `_Intervenants`

Observed fields include:

```text
Affaire
Responsable
Rôle
Type
Société
Code
HT
TTC
Fichiers et médias
```

Candidate Agency Data interpretation:

```text
ProjectParticipation
or CompanyEngagement projection depending on the record
```

### `_Décisions`

Observed fields include:

```text
Arbitrage
Argumentaire
Conseil Pantheon
Contenu
Date de décision
Décideur / validateur
Description du choix
Effet
Impact métier
Lien source canonique
Mots-clés
Moyen de décision
```

These can be useful agency/project decision records, but:

```text
AgencyDecisionRecord
!=
PantheonGovernanceDecision
```

A relation may connect them where legitimate.

## 4. PostgreSQL identity versus Notion identity

The PostgreSQL Agency Data record keeps the stable internal identity.

Example:

```text
Project.entity_id = project-01J...
Project.revision = 42

NotionProjection.external_id = notion-page-...
NotionProjection.base_revision = 42
```

A Notion page ID is a projection identifier, not the master record identity.

## 5. Notion modes

Candidate binding modes:

```text
disabled
mirror_read_only
selective_bidirectional
```

### `disabled`

No Notion collaboration is active.

Cockpit/Hermes continue using PostgreSQL Agency Data normally.

### `mirror_read_only`

Selected PostgreSQL fields are projected to Notion.

Notion changes to protected/read-only fields do not mutate Agency Data.

### `selective_bidirectional`

Only fields with an explicit `FieldSyncPolicy` may produce inbound mutation candidates from Notion.

There is no generic whole-workspace two-way synchronization rule.

## 6. FieldSyncPolicy

Each projected field must have an explicit policy.

Candidate shape:

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

Supported direction vocabulary:

```text
postgres_to_notion
bidirectional
```

A Notion-editable field must use `bidirectional`.

Candidate agency examples:

| Agency field | Notion visible | Notion editable | Direction | Conflict posture |
|---|---:|---:|---|---|
| `Project.code` | yes | maybe | bidirectional if enabled | human_review |
| `Project.status` | yes | yes candidate | bidirectional | human_review |
| `Project.phase` | yes | yes candidate | bidirectional | human_review |
| `Project.location` | yes | yes candidate | bidirectional | human_review |
| `Project.description` | yes | yes candidate | bidirectional | human_review or bounded merge candidate |
| administrative dates | yes | selected fields only | bidirectional when enabled | human_review |
| surface values | yes | selected fields only | bidirectional when enabled | human_review |
| `Person` contact data | yes | selected fields | bidirectional | human_review where needed |
| `Organization` contact data | yes | selected fields | bidirectional | human_review where needed |
| `Evidence.status` | optional | no | postgres_to_notion | postgres_authoritative |
| formal governance Decision state | optional | no | postgres_to_notion | postgres_authoritative |
| capability activation | optional | no | postgres_to_notion | postgres_authoritative |

These are candidate policies; live agency field adoption remains to be reviewed explicitly.

## 7. PostgreSQL to Notion flow

Conceptual outbound flow:

```text
PostgreSQL record revision N
        ↓
external Notion integration
        ↓
write selected projection fields
        ↓
record projection revision/base marker N
        ↓
re-read/receipt observation
```

The integration must avoid writing unrelated fields simply because the Notion page contains them.

## 8. Notion to PostgreSQL flow

Conceptual inbound flow:

```text
human edits Notion
        ↓
identify projected Agency Data record
        ↓
FieldSyncPolicy lookup
        ↓
notion_editable?
        ↓ yes
validate scope/value
        ↓
compare Notion base revision with PostgreSQL revision
        ↓
mutation candidate
        ↓
applicable Pantheon gate
        ↓
execute through authorized Agency Data capability
        ↓
PostgreSQL revision N+1
        ↓
refresh Notion projection
```

The Notion integration does not bypass the Agency Data owner.

## 9. Revision and conflict rule

Recommended sync metadata:

```text
entity_id
postgres_revision
notion_external_id
notion_base_revision
notion_last_edited_time
last_synced_at
sync_status
mutation_origin
```

Example no-conflict case:

```text
Notion base revision = 42
PostgreSQL current revision = 42
field policy = editable

→ mutation candidate may be prepared
```

Example conflict case:

```text
Notion base revision = 42
PostgreSQL current revision = 43

→ conflict
```

The system must not silently overwrite revision 43 with an edit created from revision 42.

Generic last-write-wins is excluded for business-significant fields.

## 10. Conflict policies

Candidate policies:

```text
human_review
merge_append
postgres_authoritative
```

### `human_review`

Used for fields such as:

```text
phase
status
address
budget-related professional facts
permit dates
surface values
participant relations
```

### `merge_append`

May be considered only for compatible append-only notes/list semantics.

It must not be used to merge mutually exclusive business states.

### `postgres_authoritative`

Used for read-mostly or protected projections where Notion is never an editing authority.

## 11. Notion outage

If Notion is unavailable:

```text
PostgreSQL Agency Data remains available
Cockpit remains available
Hermes may continue authorized Agency Data operations
Notion collaboration is degraded/unavailable
Notion synchronization is degraded/unavailable
```

PostgreSQL does not wait for Notion to recover before accepting normal Agency Data mutations.

When Notion returns:

```text
reconnect
↓
read current projection state
↓
compare revision markers
↓
resume safe projection or raise conflict
```

```text
Notion unavailable != Agency Data unavailable
Notion recovery != blind overwrite
```

## 12. Sync observations

Useful status vocabulary:

```text
synced
postgres_ahead
notion_ahead
conflict
notion_unavailable
sync_error
unknown
```

Pantheon may display and qualify these observations.

```text
sync observation != business decision
sync observation != Evidence
```

## 13. Deletion and archival

A Notion page disappearing does not automatically delete the master PostgreSQL record.

The integration must distinguish:

```text
page archived
page deleted
page moved out of declared scope
permission lost
Notion unavailable
```

Any destructive Agency Data effect follows the owner-level deletion rule and applicable gate.

## 14. Context Resolver

Normal Context Resolver results for native Agency Data should come from the PostgreSQL-backed Agency Data provider.

```text
_LIE
@lebre
*ABF
```

Notion does not need to be queried in real time for ordinary resolver use.

The Notion projection may still contribute synchronization/source metadata to a card, such as:

```text
Notion external link
last synced at
sync state
Notion last edited time
editable projection fields
```

## 15. Project Card composition

Example:

```text
Project Card Verger
├── identity/status/phase/location        PostgreSQL Agency Data
├── participants                         PostgreSQL Agency Data
├── administrative facts                PostgreSQL Agency Data
├── Notion collaboration status          projection metadata
├── tags                                 Tag Registry
├── source documents                     Paperless/NAS/Drive/etc.
├── Knowledge applicable relations       Knowledge owner + governed relation
├── Evidence                             Pantheon governance
├── human attention/Decision projections Pantheon + owner statuses
└── Hermes answers/runs                  Hermes/runtime observations
```

The user sees one coherent card while authorities remain separated.

## 16. Tags and Notion

The Cockpit Tag Registry remains richer than a generic Notion multi-select.

Canonical Tag candidate shape:

```text
tag_id
name
description
icon_key
color
aliases
category
status
provenance
```

A Notion multi-select may display or map to an existing Tag.

It must not silently create canonical vocabulary.

Example:

```text
Notion text "Secteur ABF"
   ↓ alias/similarity lookup
existing Tag ABF
   ↓
TagAssignment Candidate
```

If no adequate tag exists, the result is a new Tag Candidate, not immediate canonical creation.

## 17. Decision separation

Cockpit `Décisions` may display:

```text
agency decisions synchronized from Notion
Documents requiring review
Work Issues
Decision Requests
formal Pantheon Decisions
sync conflicts requiring human review
```

The underlying type/status must remain visible.

```text
appears in Décisions != formal governance Decision
agency arbitration Accepted != Pantheon effect authorization
sync conflict resolution != automatic professional approval
```

## 18. Sensitivity and minimization

Notion access must be minimized at:

```text
workspace scope
database/data-source scope
field/object scope
```

Examples:

```text
Project collaboration does not require RIB attachments
People autocomplete does not require unrelated project finance
Verger synchronization does not imply all Affaires are in scope
```

Connector responses and traces must avoid raw credentials and unnecessary sensitive values.

## 19. Outils projection

`Outils → Connecteurs → Notion` may expose a status card.

Front candidate:

```text
NOTION
workspace label
mode
sync state
number of declared field policies
```

Back candidate:

```text
workspace label
binding status
configured data sources
read/write posture
last sync observation
health observation
permissions summary
field-policy summary
conflicts
next decision
```

Required distinctions:

```text
configured != connected
connected != adopted
reachable != healthy
healthy != safe
write-capable != write-authorized
Notion editable != system-of-record authority
```

## 20. Responsibility allocation

### Pantheon governs

```text
binding adoption
legitimate workspace/data-source scope
field-policy legitimacy
consequential gates
conflict escalation
status qualification
activation/suspension posture
relations to Evidence/Decision/Context
```

### Hermes executes

```text
bounded Agency Data operations through the PostgreSQL owner capability
bounded Notion operations through an adopted external integration
normalization/enrichment when delegated
re-read and error reporting
```

### OpenWebUI / Cockpit displays

```text
PostgreSQL-owned Project/Person/Organization records
Notion projection/sync metadata
Context Resolver results
sync conflicts
visible mutation candidates and gates
```

### Human approves/decides where required

```text
adoption of editable Notion field policies
consequential business mutations
conflict arbitration under human_review
material scope changes
formal Pantheon Decisions
```

### Forbidden

```text
browser-held Notion secrets
implicit cross-workspace retrieval
generic whole-workspace two-way editing
last-write-wins authority collapse
Notion agency choice treated as Pantheon approval
Notion multi-select treated as canonical Tag without review
API success treated as Evidence
automatic governance approval from sync success
```

## 21. Implementation stages

### Stage N0 — documented Postgres-master model

```text
status: documented in AGENCY_DATA_SYSTEM_OF_RECORD.md and this specialization
```

### Stage N1 — external MVP contracts

```text
agency_data_binding.js
  PostgreSQL owner projection seam
  mutation-intent shape

notion_agency_binding.js
  field-policy registry
  revision conflict classification
  sync-state projection
```

Status:

```text
implemented candidate in pantheon-mvp PR #65
live transports not established by these browser contracts
```

### Stage N2 — live PostgreSQL Agency Data transport

Target:

```text
bounded read API
stable entity IDs
revision-aware mutations
Hermes Agency Data adapter
```

Not established by this document.

### Stage N3 — live Notion projection adapter

Target:

```text
project selected PostgreSQL fields to Notion
preserve revision marker
observe Notion edits
apply FieldSyncPolicy
raise conflicts instead of overwriting
```

Not implemented.

### Stage N4 — Project Card real-data pilot

Target:

```text
Affaires
People
Organizations
Intervenants
Notion sync metadata
```

Not yet connected live.

### Stage N5 — bounded `_Décisions` collaboration

Map `_Décisions` as AgencyDecisionRecord collaboration without collapsing Pantheon governance Decision semantics.

Not implemented.

## 22. Status summary

```text
PostgreSQL default Agency Data system of record       documented
Agency Notion schema observation                        observed
Notion optional collaboration posture                 documented
selective per-field two-way policy                    documented
no-last-write-wins conflict rule                      documented
Notion outage continuity rule                         documented
MVP PostgreSQL Agency Data projection seam            implemented candidate
MVP Agency Data mutation-intent contract              implemented candidate
MVP Notion field-policy/conflict contract             implemented candidate
browser Notion credential handling                    forbidden / absent
live PostgreSQL Agency Data transport                  to verify / separate implementation
Hermes server-side Agency Data mutation adapter       to verify / separate implementation
live Notion synchronization                           not implemented
Notion `_Décisions` synchronization                    not implemented
production adoption                                   not authorized
```
