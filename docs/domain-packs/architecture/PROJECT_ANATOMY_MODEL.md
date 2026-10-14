# Project Anatomy — Conceptual Model

Status: candidate support doctrine — frozen conceptual target.
Boundary profile: candidate_support_note.
Current contract generation: V0.2.
Frozen: 2026-08-07.

This document is the stable active identity for the Project Anatomy conceptual model. Git history records earlier reviews and generations; the filename must not change when the model evolves.

The active reviewed schemas remain authoritative for exact validation shapes. This document governs the conceptual boundaries that executable owners, adapters and projections must preserve.

## 1. Purpose

Project Anatomy is the governed, progressive semantic reconstruction of an architectural project from heterogeneous, incomplete and sometimes contradictory sources.

It is not a BIM mirror, a graph runtime, an Evidence store, a workflow engine, a memory engine or a Revit authority.

```text
Pantheon Next governs.
Hermes Agent executes external admitted work.
Hermes Web/dashboard and compatible clients expose runtime interaction.
Pantheon Cockpit projects governed Cards, navigation, decisions and status.
Revit executes local adapter operations.
The human decides consequential effects.
```

## 2. Frozen project-world core

Project Anatomy keeps exactly four project-world primitives:

```text
stable_object
source_representation
attribute_claim
relation_claim
```

Prescriptive intent remains separate through:

```text
requirement
```

Supporting provenance such as `derivation` is not a fifth project-world primitive.

```text
stable_object != source occurrence
source_representation != project truth
attribute_claim != ProjectClaim
relation_claim != generic Pantheon graph edge
requirement != observed fact
projection != authority
```

Adding a fifth project-world primitive requires a separate architecture decision showing that the need cannot be expressed with the four primitives plus requirements, profiles, provenance and governance records.

## 3. Stable identity

`stable_object` owns durable project identity and nomenclature.

It must not become a copy of Revit, IFC, a DPGF row, a thermal object, a carbon object or a property bag. Source-native identifiers, detailed classifications, geometry, quantities, prices, Evidence and approval state remain outside identity.

The active schema may retain a very broad `object_family` for structural validation and indexing. That vocabulary must remain source-independent and must not grow into a BIM or métier taxonomy.

```text
Revit Category != object_family
IFC Class != object_family
DPGF lot != object_family
classification != identity
```

Detailed semantics belong to claims and governed profiles.

Objects normally remain addressable through lifecycle transitions rather than destructive deletion. Replacement, split, merge, retirement and supersession preserve history.

## 4. Source representations

A `source_representation` records one localizable observation in one exact source/version context.

Applicable sources include:

```text
Revit
IFC
PDF plans / sections / elevations / details
OpenTakeoff output
photographs
CCTP / DPGF fragments
reports / meeting minutes / emails
structured databases
manual professional descriptions
scans / point clouds
```

A representation may exist before Pantheon knows which stable object it represents.

Where applicable it preserves:

```text
source / artifact reference
source version or digest
revision-set reference
native identity
locator
coordinate frame / calibration
observed_at
binding / adapter version
freshness token
coverage
limitations
```

```text
source-native id != stable_object_id
representation observed != stable identity resolved
same label across sources != identity confirmed
```

## 5. Attribute claims

`attribute_claim` is the canonical value-bearing assertion carrier.

A claim may target a stable object or a source representation before identity resolution. Machine-actionable project values must not be duplicated into parallel property, override, phase or classification channels.

Typical namespaced predicates include:

```text
architecture.width
classification.ifc
classification.revit_category
classification.agency
lifecycle.project_state
economy.quantity
thermal.Uw
carbon.product_mapping
construction.installation_status
```

A human correction creates a new superseding claim; it does not mutate the original source assertion.

```text
human correction != source mutation
later claim != erased history
```

## 6. Relation claims

`relation_claim` is the canonical relationship assertion carrier.

It covers project-world relations and source-to-project identity alignment.

Examples:

```text
identity.represents
spatial.contains
spatial.located_in
spatial.adjacent_to
architecture.opens_to
architecture.hosted_by
assembly.part_of
model.instance_of
project.belongs_to_group
identity.replaced_by
identity.split_into
identity.merged_into
identity.supersedes
```

Relation ids are governed and namespaced. Hermes or adapters may propose relations but cannot invent an admitted ontology silently.

A source-to-project match is represented as:

```text
source_representation
-- identity.represents -->
stable_object
```

No fifth `representation_match` authority is required.

## 7. Requirements stay separate from facts

A required condition is not an observed project fact.

`requirement` represents prescriptive intent from admitted sources such as:

```text
programme
client decision
CCTP
contract
IDS
regulation
approved technical brief
agency standard when explicitly applicable
```

A requirement may constrain the same predicate that an attribute claim observes, but the two responsibilities remain separate.

```text
required != observed
IDS validation success != professional approval
```

## 8. Profiles and registries

Extensibility comes from versioned profiles and governed predicate/relation registries, not arbitrary extension bags or new core primitives.

Candidate profiles include:

```text
architecture@1
revit@2027
ifc@4.3
ids@1
economy@1
construction@1
re2020@1
carbon@1
```

A profile may define:

```text
predicate vocabulary
relation vocabulary
classification schemes
value schemas
units and dimensions
endpoint rules
derived structural facets
validation rules
```

Structural facets may be derived and indexed for query/performance. They are rebuildable projection state, not Project Anatomy authority.

```text
profile installed != profile admitted
predicate visible != predicate approved
classification proposed != classification retained
```

The executable Profile/Predicate/Relation Registry remains documented non-implemented until its reviewed slice lands.

## 9. Revision Sets — documentary baselines

A coordinated group of project files carrying the same professional issue context may form a `Revision Set` support concept outside the four APU primitives.

A Revision Set represents a declared documentary state of the project at an instant. It does not assert that every source agrees and it does not become project truth.

Typical metadata:

```text
revision_set_id
project_ref
professional_index
issued_at
received_at when relevant
artifact refs
coverage
supersedes_revision_set_ref
content digest / manifest
```

Professional indices are opaque business identifiers. Ordering is established by explicit lineage, dates and reviewed supersession, never by lexical comparison.

```text
same revision index != source agreement
Revision Set != necessarily complete dossier
latest Revision Set != universally applicable truth
```

A partial set is valid. Later receipt of a missing artifact may enrich the same declared set when the professional issue context has not changed.

## 10. Incompleteness and coverage

Incomplete data is normal.

Absence of an attribute claim usually means that Project Anatomy has no retained claim for that predicate. Pantheon must not manufacture synthetic `unknown` claims merely to make records appear complete.

Operational states such as:

```text
not_observed
withheld
ambiguous
missing_input
conflicting_sources
```

belong primarily in Observation Bundles, Execution Results, WorkIssues or Decision Requests unless a source explicitly asserts such a fact.

Coverage becomes mandatory whenever an adapter or analysis intends to interpret absence.

```text
not found != absent
missing from snapshot != deleted project object
absence of claim != negative claim
```

A source may legitimately cover only one floor, category, phase, discipline, drawing area or task scope.

## 11. Temporal and append-oriented knowledge

New observations do not silently rewrite prior claims.

For example:

```text
Revision B -> width = 900 mm
Revision C -> width = 1000 mm
```

Both observations remain traceable. A later claim may supersede an earlier claim for a declared projection/use without erasing history.

The architecture must keep distinct when materially relevant:

```text
source version / revision context
observed_at
effective interval
```

```text
latest observation != universally current value
superseded != deleted
historical claim != current projection
```

## 12. Purpose-specific lenses

Project Anatomy stores identities, representations, claims and relations. Consumers calculate purpose-specific projections.

Candidate lenses include:

```text
design-current
architecture
economy
construction / as-built
RE2020
carbon
contractual review
Cockpit
Hermes Context Slice
```

There is no universal stored `current_value`.

```text
accepted for economy != accepted for contractual action
accepted for RE2020 input != regulatory approval
Cockpit display != persisted authority
```

A lens is a projection policy, not another graph or truth store.

### Human-readable project spatial working projection

A project may keep one human-readable Markdown working note in its authorized Obsidian/Markdown workspace to expose the current spatial understanding to humans and Hermes. A filename such as `connaissance_spatiale.md` is an illustrative workspace convention only; its name or path is not a Pantheon contract or governed identity.

The generated projection is project-scoped derived working material. It is not reusable agency Knowledge by default, not an original professional source, not a fifth Project Anatomy primitive, not a canonical spatial truth store and not Evidence. When a human intentionally authors or corrects content in this note, that authored content is also workspace-source input under the existing workspace source rule; the edit does not become an admitted Project Anatomy fact merely because it is written in Markdown.

Where useful, the projection should retain or resolve enough provenance to identify the baseline it reflects, for example:

```text
project_ref
revision_set_ref / professional index when applicable
exact source / document / model refs used
last evaluated time
observed coverage
known uncertainties / contradictions / withheld areas
```

Its readable content may summarize levels, spaces, spatial relations, openings, circulation, access, zones and other project structure when those statements are supported by the admitted context. The note may also preserve unresolved alternatives or missing context rather than forcing one interpretation.

The default maintenance posture is delta-first and search-before-create:

```text
applicable source / Revision Set change
-> identify the changed source set and affected spatial scope
-> include intentionally authored workspace-source edits in the maintenance input
-> refresh only the observations/context needed for that scope
-> compare against the existing spatial working note
-> prepare a traceable delta candidate, including the exact prior text/provenance for statements that would be superseded
-> preserve that prior state in the governed maintenance trace before invoking the writer
-> apply a bounded workspace patch through the authorized workspace writer
```

A professional index change triggers re-evaluation; it does not by itself authorize a semantic overwrite or establish applicability. Automated maintenance must not silently overwrite intentionally authored human content; a material conflict between refreshed derived observations and human-authored workspace-source content remains explicit for review.

```text
higher index != automatically truer
new index != automatically applicable
new source != spatial change confirmed
generated projection != original professional source
intentional human edit = workspace-source input, not automatic Project Anatomy fact
workspace note != Project Anatomy authority
workspace note != Evidence
generated delta != accepted project fact
human edit != permission for silent regeneration
```

If the newly applicable baseline contains no spatially material change, the readable note may remain materially unchanged while the re-evaluation provenance/currentness signal records that result honestly.

The Revit adapter never owns this workspace write. Revit observes or executes locally under its own admitted operation and returns Observation Bundles/results. Hermes may compare those observations with the current workspace note and prepare or apply an authorized workspace patch. Pantheon continues to govern scope, status, provenance and consequential admission.

## 13. Observation Bundles for Hermes and adapters

Hermes and adapters must not be coupled to PostgreSQL persistence shapes and must not mutate APU authority directly.

The target external seam is a bounded Observation Bundle / ResultCandidate envelope carrying, as applicable:

```text
project_ref
basis / revision_set_ref
source representations
candidate attribute claims
candidate relation claims
coverage
gaps
withheld items
warnings
method provenance
capability_id
binding_id
adapter/runtime version
```

Pantheon validates, normalizes, reviews and selectively applies candidates through governed owners.

```text
Hermes output != APU mutation
Observation Bundle valid != candidate accepted
candidate retained != Evidence admitted
runtime success != project truth
```

The executable candidate exchange contract is
`schemas/architecture-project-understanding/observation_bundle.schema.yaml`.
It reuses the three active observation/claim schemas and adds no fifth
project-world primitive, persistence owner or automatic application path.

## 14. Delta-first high-density adapters

High-density sources such as Revit and IFC should support snapshot/delta operation where practical instead of forcing full semantic re-ingestion on every observation.

Typical delta categories:

```text
added source representations
changed source representations
missing source representations
unchanged source representations
```

A missing source occurrence only becomes a retirement/deletion candidate when declared coverage and method semantics support that conclusion.

```text
missing from Revit delta != project object deleted
new IFC GlobalId != new Pantheon identity automatically
```

## 15. Change Requests are baseline-bound

A consequential modification request should identify the exact project baseline against which it was made, normally a Revision Set or equivalent reviewed source state.

```text
Change Request
-> base Revision Set
-> target / locator / stable-object candidates
-> requested change
-> dependencies / preconditions
```

If the project has advanced, Hermes compares/rebases the request before execution.

Possible operational outcomes include:

```text
clean
conflict
blocked
requires_review
```

A stale baseline does not necessarily block independent actions in the same task.

```text
request based on Revision C != permission to mutate Revision D blindly
technical rebase possible != modification authorized
```

## 16. Identity lifecycle

Stable identity survives normal project evolution.

Examples:

```text
ROOM-12 -- identity.split_into --> ROOM-12A, ROOM-12B
WINDOW-07 -- identity.replaced_by --> WINDOW-19
ZONE-A + ZONE-B -- identity.merged_into --> ZONE-C
```

The old identities and historical references remain addressable.

```text
retired != erased
replacement != mutation of history
```

## 17. Proof and governance remain outside Anatomy

Project Anatomy does not own Evidence admission, Proof, professional approval, ProjectClaim, Decision or WorkIssue authority.

Future Proof qualifies whether claims are sufficiently supported for a declared purpose, policy, scope and time. It does not assert a universal boolean truth.

Conceptually:

```text
Claim
-> Evidence
-> Proof / review policy
-> sufficient for declared use
```

Different uses may legitimately reach different conclusions:

```text
preliminary design
quantity takeoff
RE2020 input
contractual acceptance
regulatory submission
```

```text
supported for one use != supported for every use
Evidence present != Proof conclusion
Proof conclusion != task authorization
```

## 18. Raw source data is not automatically Anatomy

Adapters may observe substantially more data than Pantheon needs to retain as semantic project knowledge.

A Revit model may expose hundreds of thousands of elements and millions of parameter values. That does not imply one canonical `attribute_claim` for every raw parameter.

```text
raw observed != canonically retained
source cache != project authority
adapter index != Project Anatomy
```

## 19. Domain reuse

The same stable identities are reused across architecture, economy, chantier/DET, RE2020 and ACV/carbon.

One window may simultaneously carry:

```text
architecture.class = window
classification.ifc = IfcWindow
Revit source representation
quantity claim
thermal.Uw claim
carbon product-mapping claim
construction status claim
```

It remains one project object, not one object per métier.

```text
quantity computed != quantity contractually accepted
thermal input retained != regulatory compliance
product matched != environmental data validated
site observation != work acceptance
```

## 20. Revit, IFC, IDS and drawing consequences

Revit and IFC are high-density source representations. Their native ids support matching but never define Pantheon stable identity.

The Revit add-in owns real Revit observation, native identifiers, freshness and technical results. The current W0 adapter is observation-only; future mutation preflight, authorization and named transactions remain separate work and are not implied by W0. The add-in does not own stable project identity, Evidence admission, Decision, WorkIssue closure, contractual truth or regulatory conclusion.

IDS feeds requirement/conformance candidates and deterministic validation. It does not canonize project claims automatically.

OpenTakeoff/drawing geometry remains source representation + claims; source-local approval marks do not become Pantheon approval.

## 21. Clean-install baseline

Project Anatomy is installed directly from this V0.2 model. The discarded
sandbox-only design has no active schema, reader, writer, adapter, database
migration or API projection. Existing sandbox databases are recreated instead
of upgraded.

Git history remains the only record of the discarded design. Reintroducing a
second carrier requires a separate architecture decision backed by an observed
external consumer; it is not part of ordinary installation or validation.

## 22. Repo-state discipline

Current repository state:

```text
Pantheon-Next schemas / read-only validation = implemented
implementation/ Project Anatomy persistence/review/application path = implemented candidate, not adopted
Pantheon-plugins Revit W0 adapter = implemented and CI-validated, live Revit 2027 proof still required
```

The former `pantheon-mvp` repository is provenance only; its executable owner now lives under `implementation/` in this monorepo.

Documented non-implemented until their reviewed slices land:

```text
Revision Set executable contract
Profile/Predicate/Relation Registry
semantic lens policy
purpose-specific Proof model
Revit mutation/write seam
```

The Revit W0 implementation must remain `implemented, to verify`, not `supported`, until the existing `Pantheon-plugins/revit/docs/FIRST_PROOF.md` live sequence succeeds. Repository or CI success does not satisfy that live qualification.

Repo state must be updated when these slices actually merge; documentation does not make them implemented.

## 23. Change-control invariants

The following changes require explicit architecture review:

```text
adding a fifth project-world primitive
embedding Evidence, Proof or approval inside APU
making source-native ids authoritative project identity
introducing an ungoverned extension bag
letting Hermes mutate APU directly
making a lens/projected cache authoritative
silently deleting project identity because a source occurrence vanished
```

New profiles, predicates, relations, lenses and adapter bindings may evolve without reopening the four-primitive core when they preserve these boundaries.

## 24. Final invariants

```text
source != project truth
source representation != stable object
missing != deleted
same revision != source agreement
claim != ProjectClaim
claim != Evidence
requirement != observed fact
latest != universally applicable
projection != authority
accepted for one purpose != accepted for every purpose
Hermes output != APU mutation
Revit transaction success != governance approval
raw observed != canonically retained
```

This small core is intentional. Project Anatomy becomes more rigorous by limiting canonical carriers while retaining provenance, temporal history, explicit uncertainty and governed extension points.