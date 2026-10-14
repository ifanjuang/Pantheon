# Agency Data System of Record

Status: candidate support doctrine — documented non-implemented data ownership and synchronization contract; executable contract seams exist externally in `pantheon-mvp` PR #65.

Boundary profile: candidate_support_note.

Decision date: 2026-07-24.

## 1. Purpose

This document owns the Cockpit V2 rule for structured agency records such as Projects, People, Organizations and project participation relations.

The default architecture is:

```text
PostgreSQL Agency Data
= native system of record

Notion and other business applications
= optional collaborative projections or specialized owner systems only when explicitly declared
```

The core rule is:

```text
record identity and revision live in the declared system of record
projection does not acquire authority merely because it is editable or synchronized
```

For the current Cockpit V2 direction, native Agency Data uses PostgreSQL as the default system of record.

## 2. Scope

Candidate native Agency Data includes:

```text
Project / Affaire
Person
Organization
ProjectParticipation
CompanyEngagement
ProjectFact
Tag
TagAssignment
selected agency-level decision/reference records
other future professional records explicitly admitted to the Agency Data Core
```

This document does not redefine:

```text
Evidence
formal Pantheon governance Decisions
Registre Probatoire
Document source authority
Knowledge authority
Capability activation authority
runtime health/safety qualification
```

Those retain their existing owner doctrines.

## 3. Default architecture

```text
                         COCKPIT
                            │
                     structured API
                            │
                   POSTGRESQL AGENCY DATA
                    system of record
                       ▲          ▲
                       │          │
            Hermes mutations    optional sync
                       │          │
                       │       NOTION
                       │     collaborative UI
                       │
                    HERMES
                       ▲
                       │
                    PANTHEON
                 governs effects
```

Notion is not required for Cockpit or Hermes to work with native Agency Data.

## 4. Core non-equivalences

```text
PostgreSQL system of record != Pantheon governance authority
Notion projection != system of record
Notion editable != Notion authoritative
sync completed != Evidence
sync health != safety
mutation candidate != authorized mutation
API success != professional validation
record revision != approval state
```

## 5. PostgreSQL ownership

A native Agency Data record should carry at least:

```text
entity_id
entity_type
revision
created_at
updated_at
updated_by or mutation origin
business fields
```

Where a record is projected to another system, synchronization metadata may add:

```text
projection_system
projection_external_id
projection_revision_marker
projection_last_edited_at
last_synced_at
sync_status
```

The projection metadata does not change ownership.

## 6. Hermes write rule

Hermes may produce bounded Agency Data mutation candidates targeting PostgreSQL-owned records.

Recommended command shape:

```text
operation: agency_record_mutation_candidate
owner_system: postgres
entity_type
entity_id
field or bounded patch
value
expected_revision
requested_by
classified_effect
execution_authorized: false
```

The expected revision is mandatory for ordinary mutable records unless a more specific owner contract provides an equivalent concurrency check.

Conceptual flow:

```text
user/Hermes intent
      ↓
resolve record + field
      ↓
read current PostgreSQL revision
      ↓
prepare bounded mutation candidate
      ↓
apply Pantheon gate when consequential
      ↓
execute through authorized Agency Data capability
      ↓
transaction + revision increment
      ↓
receipt + re-read
```

Hermes should use an Agency Data capability/adapter rather than arbitrary generated SQL.

## 7. Cockpit read rule

Cockpit and normal Hermes context retrieval should prefer the normalized Agency Data API backed by PostgreSQL for native Agency Data.

This supports:

```text
Context Resolver `_`
Context Resolver `@`
permitted `*` search
Project Cards
Person/Organization cards
Project participant relations
Hermes Card Context
```

The browser does not need database credentials.

## 8. Optional collaborative projections

An external collaboration surface such as Notion may expose selected Agency Data fields.

A projection policy must declare each field's posture rather than enabling generic whole-record synchronization.

Candidate field policy:

```text
FieldSyncPolicy
entity_type
field
projection_system
visible
editable
sync_direction
conflict_policy
validation_rule
sensitivity
```

Candidate directions:

```text
postgres_to_projection
bidirectional
```

`bidirectional` means the external UI may propose a mutation back to the PostgreSQL-owned record. It does not make the external projection co-authoritative.

## 9. Incoming external edit

An edit made in an allowed external projection follows this conceptual path:

```text
external human edit
      ↓
field policy lookup
      ↓
field editable?
      ↓ yes
validate value/scope
      ↓
compare projection base revision with PostgreSQL current revision
      ↓
mutation candidate
      ↓
applicable governance gate
      ↓
Agency Data mutation
      ↓
new PostgreSQL revision
      ↓
projection refresh
```

If the field is not explicitly editable, the incoming edit must not mutate the Agency Data record.

## 10. Concurrency and conflict

Generic last-write-wins is not accepted for business-significant Agency Data fields.

Example:

```text
shared base revision = 42

Hermes/PostgreSQL change:
phase DCE -> EXE
revision 43

Notion change still based on 42:
phase DCE -> ACT

result:
conflict
```

The system must not silently choose ACT or EXE merely because one write arrived later.

Candidate conflict policies:

```text
human_review
merge_append for compatible append-only text/list cases
postgres_authoritative for read-mostly protected fields
```

A conflict policy is a declared rule, not an automatic Pantheon approval.

## 11. Sync state observations

Useful observable states include:

```text
synced
postgres_ahead
projection_ahead
conflict
projection_unavailable
sync_error
unknown
```

Pantheon may qualify/display these observations in the control plane.

```text
sync status != business record status
sync status != Evidence
```

## 12. External projection outage

If an optional collaborative application is unavailable:

```text
PostgreSQL Agency Data remains authoritative and available
Cockpit remains usable
Hermes may continue authorized Agency Data operations
external collaborative UI is degraded/unavailable
synchronization is degraded/unavailable
```

PostgreSQL-native work does not wait for the optional application to recover.

On recovery, revision comparison occurs before accepting an external edit.

```text
external outage != Agency Data outage
external recovery != blind overwrite
```

## 13. Deletion and archival

External disappearance of a projected record must not automatically hard-delete the PostgreSQL system-of-record record.

The integration must distinguish at least:

```text
archived externally
deleted externally
projection no longer in scope
external permission loss
external service unavailable
```

Deletion semantics require an explicit owner-level rule.

## 14. Identity

The internal Agency Data identity is stable and independent of external projection IDs.

Example:

```text
entity_id = project-01J...

Notion projection:
external_id = notion-page-...

future alternate projection:
external_id = another-system-...
```

The external IDs are relations/projection identifiers, not replacements for `entity_id`.

## 15. Data-model placement

A physical PostgreSQL deployment may contain multiple semantic schemas.

Candidate direction:

```text
agency.*
  native Agency Data records

governance.*
  Pantheon-governed records

search_derived.*
  search/index/derived material

runtime_observation.*
  external runtime observations

projection.*
  optional external projection/sync metadata where useful
```

Physical co-location does not collapse authority between these schemas.

## 16. Responsibility allocation

### Pantheon governs

```text
which capability/binding may be used
scope
field-policy legitimacy
consequential mutation gates
conflict escalation
activation/suspension posture
status qualification
relations to Evidence and Decisions
```

### Hermes executes

```text
bounded Agency Data reads
bounded Agency Data mutation operations after applicable authorization
normalization/enrichment when delegated
external collaboration operations through an adopted binding
error reporting and re-read
```

### Cockpit/OpenWebUI displays

```text
Agency Data records
source/system-of-record attribution
projection/sync state
conflicts
mutation candidates/gates
Context Resolver results
```

### Human decides

```text
consequential business mutations when required
conflict arbitration when policy requires human review
adoption of writable external collaboration mappings
material field-policy changes
formal Pantheon Decisions
```

### Forbidden collapse

```text
external edit treated as automatic governance approval
projection record treated as canonical Evidence
arbitrary browser SQL
silent ownership transfer
last-write-wins across conflicting business edits
unbounded external editing of governance-sensitive fields
```

## 17. Relationship to Notion

`NOTION_AGENCY_DATA_BINDING.md` specializes this contract for the agency Notion workspace.

The generic Agency Data rule is owned here:

```text
PostgreSQL = default native system of record
```

The Notion document owns only:

```text
Agency mapping
Notion field projections
Notion editability policies
Notion revision/sync observations
Notion-specific sensitivity and connector boundaries
```

## 18. Implementation status

```text
PostgreSQL system-of-record direction                 documented
Agency Data identity/revision rule                    documented
selective external field sync policy                  documented
conflict/no-last-write-wins rule                      documented
external outage posture                               documented
MVP Agency Data projection seam                       implemented candidate externally
MVP mutation-intent shape                             implemented candidate externally
MVP Notion field-policy/conflict seam                 implemented candidate externally
live PostgreSQL schema/migration for this model       not established by this document
live Agency Data API                                  to verify / separate implementation
Hermes server-side Agency Data write adapter          not established by this document
live Notion synchronization                           not implemented
production adoption                                   not authorized
```
