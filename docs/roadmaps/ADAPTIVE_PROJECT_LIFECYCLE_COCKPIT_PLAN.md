# Adaptive Project Lifecycle and Cockpit Convergence Plan

Status: validation-only roadmap — documented, not implemented.
Boundary profile: candidate_support_note.
Date: 2026-08-05

```text
OpenWebUI exposes conversation and intake.
Hermes executes bounded admitted work.
Pantheon Next governs semantics, authority and consequential transitions.
pantheon-mvp owns executable persistence, APIs, projections and adapters.
The human decides consequential effects.
```

## 1. Objective

Define a simple professional experience that can begin from any practical agency
input — email, mission letter, plan, PLU extract, spreadsheet, photograph, question
or uploaded file — and remain coherent through design, authorization, consultation,
works, reception, GPA, claim and dispute.

The roadmap converges existing contracts and doctrines. It does not create a new
runtime, graph, inbox engine, scheduler, queue, provider router, memory engine,
approval engine or automatic project mutation.

## 2. Product navigation

The accepted first-level navigation is:

```text
Pantheon
Décisions
Affaires
Connaissances
Compétences
Outils
```

Responsibilities:

```text
Pantheon
= contextual conversation and intake.

Décisions
= cross-agency human inbox for questions, confirmations, arbitrations and
  consequential authorizations.

Affaires
= projects and their complete lifecycle.

Connaissances
= reusable cross-project knowledge: DTU, standards, regulation, MAF guidance,
  jurisprudence, agency doctrine, methods and technical references.

Compétences
= governed business capabilities visible to the user.

Outils
= replaceable connectors, adapters, services, plugins, MCP entries and runtimes.
```

```text
knowledge retrieved != applicable project rule
capability created != capability admitted
capability available != task authorized
tool installed != tool adopted
```

## 3. Visual families and semantic objects

The Cockpit and backend deliberately use different vocabularies.

```text
UX card family != backend semantic entity
navigation section != card family
projection != persistence
```

### 3.1 Current visual families

The existing architecture-facing visual grammar remains:

```text
Project
Information
Contacts
Work
Decision
Tool
```

The `Work` family uses **Tâches** as its principal UX label.
`WorkIssue` is the principal canonical object projected in that family.
The family may remain extensible without creating competing Task, Todo, Action,
Ticket, Issue or WorkItem concepts.

### 3.2 Semantic objects

The backend may distinguish, among others:

```text
Project
Document
Information
ProjectClaim
WorkIssue
Decision
Person
Organization
Participation
Knowledge
Capability
Evidence
ResultCandidate
APU objects and relations
```

A `Document` is therefore a first-class semantic object without necessarily
becoming a seventh primary visual family.

## 4. Project experience

The primary project navigation remains deliberately small:

```text
Vue d’ensemble
Contenus
À traiter
Décisions
```

```text
Vue d’ensemble
-> Project card and current project summary.

Contenus
-> Information-family projections representing useful project content.

À traiter
-> Tâches, questions, contradictions and review items requiring attention.

Décisions
-> project-scoped Decision objects and their history.
```

Secondary views appear only when useful:

```text
Contacts
Anatomie du projet
Sources et provenance
Outils
```

The global `Décisions` space and the project `Décisions` section are two projections
of the same governed Decision identities, not duplicate records.

## 5. Project card

The front remains a concise operational summary.

The back remains the project identity sheet and may expose:

```text
address
parcels
mission
phase and contexts
main client / MOA
principal contacts
surfaces
budget or works amount
PLU / zoning
authorizations
key dates
principal ProjectClaims and provenance posture
```

`Anatomie du projet` may be summarized there when useful, but it does not replace
the identity sheet.

## 6. Information as the default project-content family

`Information` is the default visual family for useful project content when no more
specific presentation is required.

It may present:

```text
email
letter
meeting or site report
note
plan
sketch
photograph
table
CCTP
DPGF
devis
diagnostic
attestation
analysis
synthesis
IFC or other model representation
native Pantheon content
```

An Information-family card may have no file, one file or several files.

This does not make Information the exclusive presentation of a Document. A Document
may also appear through a viewer, revision list, chronology, source browser or other
specialized projection.

### 6.1 Document boundary

```text
Information-family card
= default user-facing project-content projection.

Document
= backend authority for a file or source-bearing documentary record.
```

Document owns, when applicable:

```text
original bytes or external source reference
hash
format
pages or native units
attachments
structure and extraction
version and index
provenance
archive state
```

A Document is not duplicated as a second Information semantic object merely for
display.

### 6.2 Information semantic boundary

A semantic Information is an observation, requirement, analysis, note or synthesis
that retains professional value independently of one source file.

```text
Information
!= ProjectClaim
!= ResultCandidate
!= Decision
!= WorkIssue
```

A structured professional value such as a surface, budget, PLU zone or reception
date normally uses `ProjectClaim` when provenance, date, contradiction or
obsolescence matters.

An unadopted Hermes interpretation remains a `ResultCandidate`. It becomes an
Information only when deliberately retained as an authored or consolidated analysis.

## 7. Information card grammar

### Upper left

```text
business kind
professional index when applicable
business date
```

### Upper right

Icons describe actual media and data modes:

```text
email
PDF
text
table
image
photo
audio
video
DOCX
XLSX
IFC
link
```

Several may coexist.

### Body

```text
title
summary
author or origin
lifecycle status
limits or restrictions when relevant
```

### Lower right

Subject tags are aligned toward the lower right and may wrap onto additional lines.
Tags support filtering, discovery and Hermes context selection. They do not replace
relations, status, version, applicability or professional conclusions.

```text
tagged DTU != applicable DTU confirmed
tagged conforme != compliance validated
```

## 8. Dates, variants, revisions, indices and status

```text
Variant
= concurrent option.

Revision
= successive evolution of the same option.

Professional index
= issued professional version.

Lifecycle status
= position in the content lifecycle.
```

```text
variant != revision
revision != professional index
professional index != lifecycle status
```

Relevant dates may include `source_date`, `received_at`, `issued_at` and `updated_at`.
The card displays the most relevant business date. Internal technical edits do not
consume a new professional index.

## 9. Relations between Informations

Informations form a lightweight graph, not a mandatory parent-child tree.
One response may relate to several prior messages and several messages may respond
to one request.

The first implementation is deliberately limited to four demonstrated meanings:

```text
répond à
s’appuie sur
remplace
contredit
```

Additional candidates may be tested later:

```text
complète
dérive de
contient
compare avec
```

They are not canonical until real-project use and authority inventory demonstrate
that they represent distinct responsibilities.

The exact storage field, relation authority, vocabulary identifiers and review
status must be decided after inventory of the existing generic graph, domain
relations and APU mapping contracts. That inventory is
`INFORMATION_RELATION_AUTHORITY_INVENTORY.md`, and it is complete.

### Storage field (human decision, 2026-08-06)

One generic edge carrier keyed on `EntityRef`, not a table dedicated to
Informations:

```text
relation_id       stable identity
from_entity_type  closed set, extended one reviewed tranche at a time
from_entity_id
to_entity_type
to_entity_id
relation_type     closed: the four canonical meanings only
```

Generic in **shape**, closed in **meaning**. The four relations above remain the
only permitted `relation_type` values; a Tâche that *concerns* an object (§11) is
a scope link, not one of them, and opening the carrier to it is a separate
reviewed decision.

Two properties decided this. §21 forbids a second relation graph, and §11 already
requires polymorphic links, so a carrier restricted to Informations guarantees
that Tâches, Anatomy and Compétences each build their own. And the convention
already exists in the implementation: `agency_project_claims` stores a
polymorphic reference as `backing_entity_type` + `backing_entity_id` with a
both-or-neither CHECK, over the `EntityRef` primitive.

The accepted cost is the loss of foreign-key integrity that a single-target table
would have. It is bounded by keeping `entity_type` closed — so every extension is
visible in review — and by a project-scope trigger, as
`agency_information_document_links` already does.

Relation authority, vocabulary identifiers and review status remain open.

```text
relation shown on a card != new relation authority
explicit relation != inferred candidate relation
generic carrier != open vocabulary
```

Explicit relations are priority context for Hermes. Their absence never means that
Hermes may skip autonomous compatibility checks.

## 10. Variants inspired by GitHub branches

The UX may present `Variantes` for genuinely competing options. A selected variant
becomes the current reference through a Decision or other governed adoption.
Rejected alternatives remain historized.

The roadmap does not create a universal `InformationBranch` schema. Existing
version, derivation and relation contracts must be inventoried first. A new branch
object is justified only if real-project tests show that relations and revisions are
insufficient.

## 11. Tâches

The `Work` visual family is presented to users primarily as **Tâches**.
`WorkIssue` is the principal canonical object projected in that family.

A Tâche is an autonomous action, not a status of an Information and not a copied
child record.

Canonical WorkIssue statuses remain:

```text
open
in_progress
waiting
review
done
cancelled
```

Possible UX labels are projections only:

```text
À faire
En cours
En attente
À relire
Terminé
Annulé
```

A Tâche may concern a Project, Information, Decision, Contact, Anatomy object,
several of these at once, or the agency without a Project. Each surface projects the
same WorkIssue identity.

## 12. Décisions

A Decision is a structured human intervention that conditions continuation. It may
result from low confidence, contradiction, ambiguity, missing information, variant
selection, important external response, authorization, budget arbitration,
reception or responsibility.

Hermes may propose a Decision or clarification. Hermes does not decide.

```text
wait for a quote
-> Tâche with waiting status

judge whether the quote is acceptable
-> Decision
```

## 13. Contacts

`Contacts` is an aggregated visual projection grouped by project role.
Backend authority remains separated:

```text
Person
Organization
Participation
```

## 14. Anatomie du projet

`Anatomie du projet` is the user-facing structural, spatial, functional and
technical understanding of an affair.

It may include sites, parcels, buildings, levels, zones, spaces, elements, systems,
fire zones, functional sectors, compartments, flows, paths, relations between works
and existing / demolition / projected / as-built states.

```text
APU
= internal authority for project objects and relations.

Anatomie du projet
= calculated user-facing projection of APU coverage, provenance and uncertainty.
```

It may reuse the Information visual grammar, but it is not an ordinary editable
Information and not a second graph store.

## 15. Relations to Anatomy objects

Informations, Tâches and Decisions must be able to concern project objects such as
spaces, zones, elements or systems.

The roadmap records the capability but does not prescribe a new universal
`related_project_objects[]` field. Implementation must first inventory the existing
generic graph, architecture-domain typed relations, APU mapping contracts and card
projection definitions.

## 16. Connaissances, Compétences and Outils

```text
Connaissances
= general reusable knowledge outside one affair.

Compétences
= governed business-facing capabilities.

Outils
= replaceable technical means.
```

A Capability may internally reference workflows, knowledge, rules, templates,
responsibilities, rites, places, tools and Hermes implementations.

```text
Créer une compétence
-> crée ou propose une Capability candidate gouvernée dans Pantheon.

Implémenter cette compétence
-> peut demander à Hermes de préparer un Skill ou Workflow candidat.

Capability candidate created
!= Hermes Skill implemented
!= Capability admitted
!= Task authorized
```

Pantheon exposes its governed capabilities. It does not duplicate the complete
internal Hermes skill catalogue or become a skill runtime.

## 17. Hermes context and compatibility checks

When Hermes works on an Information, priority context may include explicit
relations, variants, newer indices, contradictions, linked Tâches, applicable
Decisions, Anatomy objects, selected general Knowledge, sources and limits.

Hermes must also search for relevant incompatibilities not yet explicitly related,
including version, phase, project-state, disciplinary, semantic and applicability
conflicts.

Hermes produces candidates, questions and bounded results. It does not directly
create project truth, Evidence, memory promotion or consequential effects.

## 18. Required invariants

```text
1. Project is the root of an affair.
2. Information is the default visual family for project content, not its exclusive projection.
3. Document remains backend authority when a file or source record exists.
4. Work family uses Tâches as its principal UX label.
5. WorkIssue is the principal canonical object projected in the Work family.
6. Decision is a structured human intervention conditioning continuation.
7. Contacts projects Person, Organization and Participation.
8. Anatomie du projet is a calculated APU-backed projection.
9. Connaissances, Compétences and Outils remain distinct responsibilities.
10. Variant != revision != professional index != lifecycle status.
11. Information != ProjectClaim != ResultCandidate.
12. Explicit relation != inferred candidate relation.
13. Projection != persistence.
14. Hermes proposes; Pantheon governs; the human decides consequential effects.
```

## 19. Implementation order

```text
0. authority and vocabulary convergence
1. minimal Project, aliases and source intake
2. Information-family cards with optional Document backing, dates, indices,
   formats, statuses, tags and Contacts
3. four minimal Information relations after authority inventory
4. Tâches, global/project Decisions and one attention surface
5. ProjectClaims and consequential values
6. variants validated before any branch object
7. Anatomy relations and projection
8. Compétences registry and bounded Hermes implementation links
9. optional adapters and real-project validation
```

The first usable increment works without APU, Hermes, IFC, Mnemosyne, Paperless or
Docling.

### Why relations precede Tâches (human decision, 2026-08-06)

Steps 3 and 4 were the other way round. §11 states that a Tâche may concern a
Project, Information, Decision, Contact or Anatomy object — **several of these at
once**. That is a polymorphic many-to-many link, and §21 forbids creating a
second relation graph.

Building Tâches before a relation carrier exists therefore left only two
outcomes: invent a link table dedicated to Tâches, which is the second graph
§21 forbids, or stall waiting for one. The order now matches the constraint the
plan already imposed on itself.

The relations step keeps its own precondition: the authority inventory in
`INFORMATION_RELATION_AUTHORITY_INVENTORY.md`, which is complete.

## 20. Completion criteria

The roadmap is successfully implemented when:

1. any practical first input can be admitted without loss;
2. Project identity and aliases remain correctable;
3. Information-family cards represent file-backed and native content consistently;
4. Document authority is preserved without semantic duplication;
5. dates, indices, variants, revisions and statuses remain distinct;
6. tags remain descriptive and relations remain structural;
7. Tâches are unique WorkIssues projected in all relevant contexts;
8. global and project Decisions share one identity;
9. Informations support multi-source and multi-response relations;
10. ProjectClaims retain consequential value provenance;
11. Anatomy appears only as an APU-backed projection;
12. Knowledge, Capability and Tool responsibilities remain separate;
13. optional adapters can be disabled without losing authoritative project data.

## 21. Non-goals

This roadmap does not:

- implement schemas, migrations, APIs or Cockpit code;
- create a universal Information backend table for every object;
- make Information the exclusive presentation of Documents;
- create a seventh visual family without owner-doctrine convergence;
- create a mandatory parent-child Information hierarchy;
- create a universal branch system before real validation;
- create a second relation graph;
- make APU, IFC, Hermes, Mnemosyne, Paperless or Docling mandatory;
- make tags authoritative;
- allow Hermes to admit Evidence, promote memory or apply consequential changes;
- qualify the agency/NAS runtime.

```text
plan documented != implementation completed
Information projected != semantic responsibilities collapsed
Anatomie du projet displayed != APU truth replaced
candidate relation != adopted relation
reviewed candidate != project mutation
```