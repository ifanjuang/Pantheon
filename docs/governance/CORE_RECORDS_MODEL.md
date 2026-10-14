# Core Records Model

Status: active support doctrine — cross-domain record model and scope-keyed separation.

This document defines the tool-agnostic, profession-agnostic record model shared by every domain: the common objects (contact, organization, scope, document, message, event, decision) and the rule that keeps dossiers separated.

It is documentation only. It does not implement a database, schema, table, migration, connector, email intake, contact sync, OCR, vector index, runtime or executable artifact. The actual database and connectors are adapters that live outside Pantheon and conform to this model (`ADAPTERS_AND_BINDINGS.md`).

```text
The exposure surface exposes.
The execution runtime executes.
Pantheon governs.
```

## Purpose

Every professional — architect, lawyer, accountant, engineer, doctor — shares the same backbone: contacts, separated dossiers, documents, emails, dated events and decisions. Only the profession-specific objects differ.

This document answers one question:

```text
What record model is common to all professions, and how does it stay separated by dossier?
```

It is the foundation the intake workflow, the proposed file tree, the domain packs and any proof register build upon.

## Two layers

```text
Common core (this document)        Domain pack (per profession)
---------------------------        ----------------------------
contact, organization              CCTP, lot, reserve (architecture)
party role                         pleading file (law)
scope / dossier                    accounting entry (accountancy)
document, version                  site report
message (email)                    ...
event, decision
membership
```

The common core is stable and identical across professions. Profession-specific record types are defined in the domain pack and extend the core; they never replace it.

```text
Contacts, dossiers, documents and messages live in the core, once.
A profession only adds its own record types on top.
```

Putting contacts or emails inside one profession's pack is forbidden: it would have to be rewritten for the next profession.

## Scope is the backbone

Separation between dossiers is not one feature among others. It is the load-bearing rule.

Every core record carries a `scope_id`. Scope is what guarantees:

- dossier watertightness — a message in dossier A never surfaces in dossier B;
- confidentiality — a record attached to one dossier is not globally reusable;
- controlled reuse — a general reference is distinct from a dossier-specific record.

The scope vocabulary and isolation rule are owned by `SCOPE_ISOLATION.md` (session, task, dossier, project, domain, user, organization, repository, governance, system). This document references that vocabulary; it does not restate it.

```text
No global record by default.
A record may be used only within its declared scope unless a governed review broadens it.
```

In an implementation adapter, scope separation should be enforced structurally (for example row-level security keyed on `scope_id`), so cross-dossier leakage is impossible by construction, not merely forbidden by discipline.

## Core objects

Shapes only. The implementation schema, if created, lives under `schemas/` and requires explicit approval.

### Identity vs role-in-a-dossier

A contact is global: a person exists once. The contact's role is per dossier. The same person may be a client on one project and a neighbour on another. The contact is never duplicated; the link (membership) carries the dossier-specific role.

```text
core_contact          # a person, regardless of dossier
core_organization     # a firm, office, company, public body
core_party_role       # the role a contact holds IN a given scope (client, contractor, BET, expert, ...)
core_scope            # a dossier / project / perimeter — the separation key
core_membership       # which contact belongs to which scope, with which role
core_document         # a piece/file, versioned, attached to a scope
core_message          # an email/exchange, attached to a scope
core_event            # a dated action, milestone or decision, attached to a scope
```

### Common envelope fields

Every core record carries the governance envelope (consistent with `MEMORY.md`, `EVIDENCE_PACK.md` and the manifest in `MODULAR_DOMAIN_REORIENTATION.md`):

```text
id
scope_id            # the separation key (required)
status              # candidate | verified | active | superseded | rejected | archived
source_ref          # where it came from
confidence          # when derived/extracted
created_at / created_by
valid_from / valid_until
superseded_by
```

### `core_contact` / `core_organization`

```text
contact_id / organization_id
display_name
kind                # person | organization
emails / phones / addresses   # contact points
external_links      # opaque references to a synced contact source, no secrets
status
# NOTE: a contact is global identity; its dossier role lives in core_party_role/core_membership
```

### `core_membership` + `core_party_role`

```text
membership_id
scope_id            # the dossier
contact_id          # who
role                # party role within this scope (domain pack may extend the role vocabulary)
status
```

### `core_document`

```text
document_id
scope_id
document_type       # generic here; the domain pack defines profession-specific types
canonical_title
current_version_id
hash
storage_ref         # metadata/locator only; the file lives in storage, not in Pantheon
status
```

### `core_message`

```text
message_id
scope_id            # the dossier this email/exchange belongs to
direction           # inbound | outbound
from_contact_id / to_contact_ids
subject
attachments         # references to core_document candidates
received_at
status              # candidate until attribution is validated
```

### `core_event`

```text
event_id
scope_id
event_type          # created | received | classified | decided | approved | sent | ...
object_type / object_id
occurred_at
actor
reason
# append-only in an implementation; an event is a record of what happened, not a mutable row
```

## How an item enters and is filed

The same flow for every profession; only the detected `document_type` differs.

```text
An email (or document) arrives
 -> candidate (nothing is filed yet)
 -> detect: which scope? which contact? which type?
 -> propose attachment (scope + contact + type)
 -> human validates (or the Review Queue surfaces it)
 -> filed: linked to a scope and a contact, status validated
```

Nothing is filed silently. Attribution is a candidate until validated. Cross-scope attribution is never inferred without review.

## Placement

| Concern | Layer |
|---|---|
| Core record shapes, scope rule, candidate-before-filed | Pantheon (this document + `SCOPE_ISOLATION.md`) |
| Profession-specific record types | domain pack |
| The real database, row-level scope enforcement, email/contact connectors | adapter outside Pantheon (`ADAPTERS_AND_BINDINGS.md`) |
| Showing records, capturing attribution decisions | exposure surface |
| Detection, extraction, attribution proposals | execution runtime |

Pantheon owns the shapes and the separation rule. It does not hold the database or the connectors.

## Relation to existing doctrine

- `SCOPE_ISOLATION.md` — owns the scope vocabulary and isolation rule; this model applies it to records.
- `MEMORY.md` / `KNOWLEDGE_TAXONOMY.md` — a filed record is not memory or evidence by itself; promotion stays governed.
- `MODULAR_DOMAIN_REORIENTATION.md` — the core is the stable base; domain packs extend it.
- `DATA_PLATFORM_*` (candidate) — implementation-side register families realize this model outside Pantheon.
- `REVIEW_QUEUE.md` (candidate) — surfaces attribution and merge decisions for human resolution.

## Boundary phrase

```text
The core records what every profession shares.
The scope keeps each dossier separate.
The domain pack adds the profession.
Nothing is filed, merged or reused without a governed decision.
```
