# Architecture Project Navigation UX

Status: candidate support doctrine — documented non-implemented.
Boundary profile: candidate_support_note.

This document specializes the Pantheon Cockpit project-navigation experience for architecture practice.

It complements:

- `docs/governance/PANTHEON_COCKPIT_UX_SPEC.md`;
- `docs/governance/CARD_STACK_MODEL.md`;
- `docs/governance/KNOWLEDGE_NAVIGATION_UX.md`;
- `docs/domain-packs/architecture/PROJECT_ANATOMY_MODEL.md`;
- `docs/domain-packs/architecture/PROJECT_ANATOMY_KNOWLEDGE_STRUCTURE.md`;
- `docs/domain-packs/architecture/DOCUMENT_AND_KNOWLEDGE_ORGANIZATION.md`;
- `docs/governance/DOCUMENT_LIFECYCLE_GOVERNANCE.md`;
- `docs/governance/DOCUMENT_PRODUCTION_LIFECYCLE.md`.

It defines a candidate UX contract only.

It does not implement a Cockpit component, flip-card renderer, project database, contact manager, CRM, ERP, address book, PLU service, cadastral connector, geocoder, document store, approval engine, archive service, Hermes Skill or external action.

```text
The Project Card exposes.
The project records and source-backed claims describe.
Pantheon governs status, scope and consequential use.
Hermes may propose or refresh candidates.
The human verifies and decides.
```

## 1. Purpose

Each architecture project should appear in the Cockpit as a project-specific navigation container with a recognizable identity.

The project entry should not be a generic folder icon or an unstructured list row.

It should combine:

```text
project identity
+ navigation entry
+ essential summary
+ detailed project profile
+ direct access to participants
+ direct access to companies
+ direct access to project phases and documents
```

The target experience is:

```text
Projects
├── Project Card / project folder A
├── Project Card / project folder B
└── Project Card / project folder C
```

Opening a Project Card enters a project-scoped space.

```text
Project Space
├── Project identity
├── Project phases
├── Intervenants & contacts
├── Entreprises
├── Documents
├── linked Knowledge
├── decisions and review items
└── traces and governed records
```

## 2. Core distinctions

```text
Project Card != project source of truth
Project folder != physical NAS folder
Project color != status
front summary != complete project record
back details != verified merely because displayed
contact listed != current contact verified
company selected != company contracted
PLU zone displayed != regulatory conclusion
regulation listed != applicability approved
surface value != one universal surface definition
```

The card is a Cockpit projection of governed project data and source-backed claims.

## 3. Project folder and Project Card

### 3.1 One object, two UX roles

The top-level project object has two related UX roles:

```text
Project folder
= navigation container that opens the project space

Project Card
= visual summary and detailed identity projection of that same project
```

The folder and card must not create two project identities.

```text
one project identity
-> one top-level project navigation card
-> several bounded project views
```

### 3.2 Logical navigation, not storage coupling

The Project Card may open the project's document phases and related records, but this does not require the Cockpit navigation tree to mirror the physical filesystem exactly.

```text
open Project Card != mount physical folder
move card in UI != move project files
archive Project Card != delete project sources
rename display title != rename every source file
```

The existing architecture document phases remain a bounded documentary structure:

```text
00_Gestion
10_Conception
20_Autorisations
30_DCE
40_Marche
50_Chantier
60_Reception
90_Sinistres
```

The project root may expose these phases as project navigation folders while project identity, contacts and companies remain dedicated cards.

## 4. Visual grammar

### 4.1 Project Card

The Project Card uses a **solid-color background**.

```text
Project Card / project folder
= full solid-color surface
= no gradient fill
```

The solid color identifies the project across the Cockpit.

It may be user-selected from an accessible palette or assigned by a deterministic project-color rule.

The project color must not encode:

- approval;
- risk;
- certainty;
- phase;
- delay;
- archive status;
- Evidence status;
- runtime state.

Those states remain explicit through badges, labels and icons.

### 4.2 Relationship with Knowledge visual grammar

The visual system distinguishes:

```text
Knowledge folder
= gradient-filled card-shaped container

Knowledge item
= neutral card with thick gradient outline

Project Card / project folder
= solid-color filled card-shaped container
```

This creates three recognizable families without using color alone as a governance status.

### 4.3 Contact and company cards

The project-scoped `Intervenants & contacts` and `Entreprises` cards should use:

```text
neutral interior surface
+ thick solid outline or accent using the project color
+ explicit icon and title
```

They should not use the full project fill, because they are records inside the project rather than the project container itself.

They should not use the Knowledge gradient outline, because they are project-scoped directories rather than reusable Knowledge items.

### 4.4 Accessibility

The project identity must remain recognizable without color.

Each card must also expose:

- project name;
- project code or short identifier;
- project type;
- locality;
- icon or monogram;
- text label for status;
- keyboard-visible focus;
- sufficient text contrast.

Color contrast should meet the product accessibility baseline.

The project color should have a derived accessible foreground token rather than relying on one fixed text color.

## 5. Recto / verso interaction

### 5.1 Principle

The Project Card exposes two information densities:

```text
Recto
= essential project identity and current orientation

Verso / Details
= parcel, surfaces, planning, regulatory and primary-contact details
```

The interaction may be visually designed as a card flip, but it must not depend on pointer hover.

### 5.2 Desktop interaction

A desktop implementation may use:

- a visible `Voir les détails` control;
- click or keyboard activation;
- an optional restrained flip animation;
- a clear `Retour au résumé` control.

The back state must remain keyboard navigable.

### 5.3 Mobile interaction

On mobile, a literal 3D flip may reduce readability.

The same information may instead open as:

- an expanded card;
- a details sheet;
- a full-screen project profile;
- a segmented `Résumé / Détails` control.

The semantic contract matters more than the animation.

### 5.4 Reduced motion

When reduced motion is requested, the UI should switch instantly between the two states without a flip animation.

## 6. Recto — essential project information

The front should remain scannable.

Recommended fields:

```text
project display name
project code or internal reference
project type
commune or locality
current project phase
project lifecycle status
mission-scope summary
primary client display name, when permissions allow
one principal surface indicator, explicitly typed
open warning or review badge, when material
```

Example:

```text
VERGER
Maison individuelle neuve
APD · Mission complète
Verger (00)
Client : Mme / M. …
Surface de plancher projetée : 315 m²
2 points à vérifier
```

The front must not become a dense technical dashboard.

Sensitive client identity may be abbreviated or hidden according to the viewer's permissions.

## 7. Verso — detailed project identity

The back or detail surface may group information into bounded sections.

### 7.1 Administrative identity

```text
project code
project title
project type
project status
mission scope
current phase
project address
commune
postal code
country
internal project owner
creation date
last project-profile review date
```

### 7.2 Client identity and primary contacts

The detail surface may show a compact subset:

```text
client / maîtrise d'ouvrage display name
primary contact name
primary email
primary phone
preferred communication channel
billing contact, when permitted
```

The complete participant directory remains in the dedicated `Intervenants & contacts` card.

```text
primary contact summary != complete contact directory
```

### 7.3 Parcel identity

Projects may involve one or several parcels.

A generic single `parcel_number` field is insufficient.

Candidate shape:

```yaml
parcel_reference:
  parcel_ref_id:
  commune_code:
  section:
  parcel_number:
  cadastral_area:
  source_ref:
  observed_at:
  review_status:
```

The detail surface may display:

```text
Commune 27202
Section AB
Parcelles 124, 125 and 126
Cadastral area: 4,820 m²
Last verified: 2026-07-12
```

The cadastral identifier and cadastral area must remain source-backed and dated.

### 7.4 Surfaces

The Cockpit must not expose one ambiguous field named only `surface`.

Surfaces should be typed.

Candidate types include:

```text
cadastral parcel area
site area
existing footprint
proposed footprint
existing floor area
proposed floor area
habitable area
useful area
renovated area
extension area
commercial area
landscape area
```

Candidate shape:

```yaml
project_surface_claim:
  surface_claim_id:
  surface_type:
  value:
  unit: m2
  state: existing | proposed | retained | as_built
  source_ref:
  calculation_ref:
  observed_or_calculated_at:
  review_status:
  allowed_use: []
```

The card should display the label with the value.

```text
Surface de plancher projetée : 315 m²
Emprise au sol projetée : 186 m²
Surface parcellaire cadastrale : 4 820 m²
```

### 7.5 PLU / PLUi zones

A project may cross several parcels or zoning sectors.

Candidate display:

```text
Document d'urbanisme : PLUi Métropole Rouen Normandie
Zone principale : UC0
Other sector: landscaped protection strip
Document version / approval date
Last applicability review
Source link
Review status
```

Candidate shape:

```yaml
planning_zone_claim:
  planning_claim_id:
  planning_document_title:
  authority:
  document_version_or_date:
  zone_code:
  subzone_or_sector:
  affected_parcel_refs: []
  source_ref:
  locator_ref:
  observed_at:
  review_status:
  regulatory_use_status:
```

The interface must preserve:

```text
zone identified from source != rule interpreted
rule retrieved != rule applicable to every project act
planning document available != current opposable version verified
```

### 7.6 Applicable regulations

The project profile may list regulatory frameworks or review contexts such as:

- PLU or PLUi;
- code de l'urbanisme;
- RE2020;
- accessibility;
- fire safety;
- heritage or ABF context;
- sanitation rules;
- flood or risk-prevention plan;
- seismic zone;
- acoustic requirements;
- local subdivision or easement rules.

The card must not present a generated list as a definitive legal conclusion.

Candidate shape:

```yaml
applicable_regulation_candidate:
  regulation_candidate_id:
  title:
  authority:
  applicability_scope:
  source_ref:
  locator_ref:
  identified_at:
  freshness_status:
  review_status:
  applicability_status: candidate | reviewed | not_applicable | superseded
```

The UI should distinguish:

```text
Identified
To verify
Reviewed for this project
Not applicable
Superseded
```

### 7.7 Project constraints and key facts

The detail surface may also show compact key facts:

- heritage or ABF perimeter;
- site slope;
- sanitation mode;
- flood or soil risk;
- occupancy or ERP category;
- building count;
- renovation / extension / new-build status;
- principal deadlines;
- planning-authorization reference.

These remain source-backed project claims, not decorative profile text.

## 8. Project data provenance

Every material field should expose its status and provenance on demand.

The Cockpit does not need to show a citation beside every value on the front, but a details or provenance action should answer:

```text
Where did this value come from?
When was it read or entered?
Was it calculated, observed, proposed or human-entered?
Has it been reviewed?
For which use may it be relied on?
```

Candidate field projection:

```yaml
project_profile_field:
  field_key:
  display_value:
  modality: declared | observed | calculated | proposed | as_built
  source_ref:
  locator_ref:
  last_observed_at:
  review_status:
  freshness_status:
  allowed_use: []
```

The project profile should reuse source-backed claims and APU contracts where appropriate rather than create a parallel truth store.

## 9. Intervenants & contacts card

### 9.1 Purpose

Every project should expose one dedicated `Intervenants & contacts` card.

It is a project-scoped directory of people and organizations involved in the project, excluding construction companies when they are better represented in the separate `Entreprises` card.

Typical categories:

```text
Clients / maîtrise d'ouvrage
Internal agency team
Architects and designers
Bureaux d'études
Economist
Geotechnical engineer
Surveyor
Thermal engineer
Acoustic engineer
Control bureau
SPS coordinator
AMO
Notary
Insurer or expert
Planning authority contacts
Other consultants
```

### 9.2 Card front

Recommended summary:

```text
Intervenants & contacts
12 active contacts
3 bureaux d'études
Primary client: …
2 contacts to verify
```

### 9.3 Card detail

The expanded card should support grouped entries.

Candidate shape:

```yaml
project_participant:
  participant_id:
  project_id:
  person_ref:
  organization_ref:
  display_name:
  organization_name:
  participant_category:
  role_title:
  mission_scope:
  email:
  phone:
  address:
  preferred_channel:
  active_from:
  active_to:
  participation_status:
  source_ref:
  last_verified_at:
  visibility_scope:
```

Candidate participation statuses:

```text
proposed
contacted
active
waiting
mission_completed
replaced
inactive
archived
```

### 9.4 Clients

Client records should support:

- several co-clients;
- a primary client contact;
- billing contact distinct from project contact;
- legal entity and individual contacts;
- communication preferences;
- privacy restrictions.

```text
client name visible != every user may access private contact details
```

### 9.5 Bureaux d'études

A participant entry for a bureau d'études should make the mission explicit.

Examples:

```text
BET structure — AVP / PRO
BET fluides — reservations and systems
BET thermique — RE2020
Geotechnical office — G2 AVP + G2 PRO
Surveyor — topographic and boundary survey
```

The organization and individual contact are separate references.

A person may change while the organization remains engaged.

## 10. Entreprises card

### 10.1 Purpose

Every project should expose one dedicated `Entreprises` card for contractors, artisans and suppliers involved or considered for the works.

It must distinguish:

```text
company identified
company consulted
quotation received
company selected
company contracted
company active on site
works completed
company archived
```

`Selected` must not be treated as `contracted` unless the contractual record supports it.

### 10.2 Card front

Recommended summary:

```text
Entreprises
14 lots
9 companies selected
6 contracts recorded
3 quotations pending
1 insurance verification warning
```

### 10.3 Detail by lot

Entries should be grouped or filterable by work lot.

Examples:

```text
Lot 01 — Earthworks
Lot 02 — Structural work
Lot 03 — Timber frame
Lot 04 — Roofing / zinc
Lot 05 — External joinery
Lot 06 — Partitions / insulation
Lot 07 — Electricity
Lot 08 — Plumbing / HVAC
Lot 09 — Floor and wall finishes
Lot 10 — Painting
Lot 11 — Landscaping
```

The lot nomenclature should remain configurable by project.

### 10.4 Candidate shape

```yaml
project_company_engagement:
  engagement_id:
  project_id:
  company_ref:            # reference to the stable company identity record (§11)
  contact_person_ref:     # reference to the stable person identity record (§11)
  # Identity fields (company name, contact name, email, phone) are NOT duplicated
  # here: they are read from the referenced records so this engagement cannot
  # diverge when a company renames or a contact changes. If a historical label
  # must be shown as it stood at engagement time, use an explicit dated snapshot:
  identity_snapshot:      # optional, immutable, for historical display only
    captured_at:
    company_name:
    contact_name:
    email:
    phone:
  lot_code:
  lot_title:
  engagement_status:
  consultation_ref:
  quotation_refs: []
  selected_at:
  contract_ref:
  contract_status:
  insurance_status:
  works_status:
  source_refs: []
  last_verified_at:
  visibility_scope:
```

Candidate engagement statuses:

```text
candidate
consultation_planned
consulted
quotation_received
quotation_rejected
selected_pending_contract
contracted
active_on_site
suspended
works_completed
reservations_open
closed
archived
```

### 10.5 Sensitive commercial data

Contract amounts, bank details, insurance certificates and evaluation notes should not be exposed in every card view.

The card summary may show counts and warnings.

Restricted details require project permissions.

## 11. Contact and organization identity

A person, organization or company should have stable identity independent of display name.

```text
person identity != email address
organization identity != current legal name string
company engagement != company master record
```

The project cards should reference contact and organization records rather than duplicate every value permanently.

Project-specific fields such as mission, lot, role, active period and status belong on the project relationship.

```text
Person
+ Project Participant relationship
= project role and contact posture

Company
+ Project Company Engagement
= lot, consultation, contract and works posture
```

## 12. Card navigation inside a project

Recommended project landing composition:

```text
[Project identity card — solid color]

[Intervenants & contacts] [Entreprises]

[00_Gestion] [10_Conception] [20_Autorisations]
[30_DCE] [40_Marche] [50_Chantier]
[60_Reception] [90_Sinistres]

[Recent documents]
[Open reviews]
[Linked Knowledge]
```

The identity card remains visually dominant because it owns the project context.

The Contacts and Entreprises cards remain next to it or immediately below it because they are high-frequency project directories.

## 13. Search and filtering

### 13.1 Project search

The Projects scene should support search by:

- project name;
- project code;
- commune;
- client display name, subject to permission;
- project type;
- phase;
- status;
- parcel reference;
- PLU zone candidate;
- participant organization;
- company or lot.

### 13.2 Contact filters

The Contacts card should support:

- category;
- organization;
- mission;
- active / inactive;
- missing information;
- verification freshness.

### 13.3 Company filters

The Entreprises card should support:

- lot;
- consultation state;
- selection state;
- contract state;
- works state;
- insurance warning;
- reservations status.

## 14. Editing posture

The Cockpit may allow authorized humans to:

- update project presentation fields;
- select project color;
- correct a client or participant relationship;
- add or remove a contact from the project;
- classify a company by lot;
- correct a parcel reference;
- request review of a surface or PLU claim.

Hermes may propose:

- contacts extracted from a document;
- a company and lot detected from a quotation;
- parcel references detected from a planning document;
- surface candidates extracted or calculated from sources;
- PLU zone and regulation candidates;
- stale-contact warnings.

Hermes must not silently confirm these proposals.

```text
contact extracted != participant confirmed
company named in PDF != company engaged
surface calculated != surface approved for filing
PLU article retrieved != applicability decided
```

## 15. Permissions and privacy

Project cards may contain personal and commercially sensitive information.

Permissions should separately control access to:

- project summary;
- client names;
- client contact details;
- consultant contact details;
- company contact details;
- contract information;
- quotation amounts;
- insurance documents;
- internal evaluation notes;
- regulatory source documents.

A user may be allowed to see the Project Card without being allowed to see all contact or financial details.

The Cockpit must not expose full contact details in global search results unless permitted.

## 16. Status and freshness

Project data changes over time.

The interface should show freshness when it matters.

Examples:

```text
Parcel references — reviewed 12 July 2026
PLUi zone — review required after document update
BET structure contact — active
Electrician contact — replaced
Company insurance — verification expired
Surface de plancher — APD calculation, superseded by PRO
```

Freshness and status should use text and icons, not only color.

## 17. Archive behavior

Archiving a project changes its project lifecycle posture.

It does not delete:

- project sources;
- contact history;
- company engagements;
- parcel claims;
- surface claims;
- PLU or regulation references;
- decisions;
- traces.

Archived projects may be removed from the default active grid while remaining searchable in an archive view.

```text
project archived != sources deleted
contact inactive != contact record deleted
company closed != contractual history deleted
```

## 18. Responsive behavior

### Desktop

- project cards may use recto / verso interaction;
- project grid supports multiple cards per row;
- project detail may use a two-column layout;
- Contacts and Entreprises may open as side panels or full views.

### Tablet

- cards use a reduced grid;
- detail sections stack progressively;
- the recto / verso control remains explicit.

### Mobile

- project cards occupy most of the viewport width;
- `Résumé / Détails` replaces hover or pointer-only flip;
- phone and email actions may be exposed when permitted;
- long company and contact directories use search and collapsible groups;
- sensitive fields remain hidden until explicitly opened.

## 19. Empty and incomplete states

A project may exist before every identity field is known.

The card should display useful incomplete states:

```text
Parcelle à renseigner
Surface de plancher à vérifier
Zone PLU non confirmée
Aucun BET enregistré
Aucune entreprise consultée
Contact client incomplet
```

Missing data must not be replaced by a plausible generated value.

## 20. Candidate API projections

Exact routes remain an external MVP implementation decision.

Candidate read projections:

```http
GET /v1/projects
GET /v1/projects/{project_id}/profile-card
GET /v1/projects/{project_id}/profile-details
GET /v1/projects/{project_id}/participants
GET /v1/projects/{project_id}/companies
GET /v1/projects/{project_id}/phases
```

Candidate bounded mutations:

```http
PATCH /v1/projects/{project_id}/presentation
POST  /v1/projects/{project_id}/participants
PATCH /v1/projects/{project_id}/participants/{participant_id}
POST  /v1/projects/{project_id}/company-engagements
PATCH /v1/projects/{project_id}/company-engagements/{engagement_id}
POST  /v1/projects/{project_id}/claims/{claim_id}/review-request
```

A UI route does not authorize the underlying mutation by itself.

## 21. Responsibility split

### Pantheon governs

Pantheon governs:

- project identity and scope references;
- field status and provenance expectations;
- review posture;
- visibility and privacy policies;
- claim freshness;
- regulatory-use gates;
- archive and supersession status;
- relationship meaning.

### Hermes executes or proposes

Hermes may:

- extract candidate identities and contacts;
- reconcile organization names;
- propose parcel, surface, PLU and regulation claims;
- identify missing fields;
- prepare update proposals;
- return provenance and confidence observations.

Hermes does not approve:

- project identity;
- client identity;
- contractual engagement;
- PLU applicability;
- regulatory conclusion;
- surface used for a consequential filing.

### Cockpit exposes

The Cockpit:

- displays project cards;
- captures navigation;
- exposes recto / details;
- shows contacts and companies;
- shows status and freshness;
- captures human corrections and review requests;
- respects permissions.

### Human decides

The human:

- verifies project identity;
- confirms clients and project participants;
- confirms company selection and contract posture;
- validates consequential parcel, surface and regulatory use;
- decides corrections and archive posture.

## 22. Capability Slot classification

```yaml
capability_slot: architecture_project_navigation_and_directory
abstract_function: >-
  expose one project as a recognizable navigation container with a concise identity,
  detailed source-backed project profile, participant directory and contractor
  directory without collapsing presentation, truth, regulation, contract or archive.
candidate_binding:
  exposure_surface: Pantheon Cockpit MVP
  execution_support: Hermes and external adapters when requested
implementation_status: documented non-implemented
installation_status: not applicable to this specification
health_status: not applicable to this specification
activation_status: not authorized by this document
pantheon_gates:
  - project scope and permissions
  - source-backed field status
  - participant and company relationship review
  - regulatory-use review
  - archive and privacy posture
```

## 23. Implementation sequence

### Phase 1 — Static project card projection

- solid project color;
- front summary;
- explicit details view;
- project phase navigation;
- read-only project identity.

### Phase 2 — Contacts and companies

- project participants directory;
- clients and consultants;
- company engagements by lot;
- search and filters;
- permission-aware contact details.

### Phase 3 — Source-backed detail fields

- parcels;
- typed surfaces;
- PLU / PLUi zones;
- applicable-regulation candidates;
- provenance and freshness view.

### Phase 4 — Governed editing

- bounded human updates;
- Hermes extraction proposals;
- correction and review requests;
- change trace;
- no silent confirmation.

## 24. Acceptance criteria

The UX specification is coherent when:

1. every active project has one recognizable Project Card;
2. the Project Card also opens the project navigation space;
3. the project uses a solid-color fill rather than a gradient;
4. the color is project identity, not governance status;
5. the recto remains concise;
6. the verso or details view exposes parcel, typed surfaces, PLU zones, regulations and primary contacts;
7. the details interaction works without hover;
8. every material project field can expose provenance and review status;
9. multi-parcel and multi-zone projects are supported;
10. surfaces are typed rather than stored as one ambiguous value;
11. every project exposes an `Intervenants & contacts` card;
12. client and BET relationships are explicit and project-scoped;
13. every project exposes an `Entreprises` card;
14. companies are grouped by configurable work lots;
15. selected, contracted and active-on-site remain distinct;
16. contact and commercial data respect permissions;
17. Hermes proposals remain candidates;
18. project archive does not delete sources or relationship history;
19. the project card remains distinct from Knowledge folder and Knowledge item visual grammar;
20. no runtime, CRM, ERP, PLU service or archive system is introduced into Pantheon Next.

## 25. Final rule

```text
The Project Card is both the door into the project and the compact expression of
its identity.

Its solid color identifies the project.
Its recto orients.
Its details qualify.
Its sources constrain.
Its Contacts card maps the people and consultants.
Its Entreprises card maps the contractors and lots.
Pantheon governs the status and permitted reliance of what is shown.
```
