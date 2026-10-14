# Project Anatomy Knowledge Structure

Status: candidate support note — discussion-recovery annex, documentation only.
Boundary profile: candidate_support_note.
Date: 2026-08-06.

This annex records only the Project Anatomy requirements that were not explicit
enough in the existing owner documents. It is not an ontology, persistence owner,
graph authority or second implementation roadmap.

The active owners remain:

```text
PROJECT_ANATOMY_MODEL.md
-> stable project identity, source representations, claims, requirements and boundaries.

schemas/architecture-project-understanding/
-> exact validation shapes for the active Project Anatomy contracts.

PROGRAM_AND_CONFORMANCE.md
-> requirements, intent, classifications and reviewed deviations.

PROJECT_UNDERSTANDING_ADAPTER_CONTRACT.md
-> candidate-only input from PDF, image, IFC, Revit and other readers.

PROJECT_ANATOMY_BASELINE_DECISION.md
-> V0.2-only first-installation and emission decision.

REVIT_LOCAL_ADAPTER.md
-> local Revit binding, Context Snapshot, preflight and transaction boundary.
```

Where this annex conflicts with an owner, schema or reviewed registry, the owner,
schema or registry prevails.

## 1. Recovered intent

Project Anatomy must expose a governed, queryable understanding of an
architectural project assembled progressively from heterogeneous sources:

```text
plans, sections, elevations and details
CCTP and DPGF
IFC and Revit observations
plan images, scans and sketches
site photographs
reports, meeting minutes and professional notes
manual professional input
```

The target is not automatic complete 3D reconstruction. It is a coherent and
correctable project hypothesis that can answer:

```text
what object is concerned
where it is situated
which source representation supports each assertion
which phase, index and variant the assertion concerns
what is required, proposed, observed or as-built
what is uncertain, contradictory or missing
what requires human review, work or decision
```

```text
coherent hypothesis != complete geometric reconstruction
multi-source agreement != truth
3D-compatible understanding != BIM authority
```

## 2. Stable identity and source representations

A project object keeps one internal stable identity while several source-bound
representations may describe it:

```text
plan occurrence
section or elevation occurrence
detail occurrence
photo observation
IFC representation
Revit representation
manual annotation
```

Each representation preserves its source, version or professional index, locator,
coordinate frame, calibration posture, observation time and limitations.

```text
representation != stable object
source-native id != stable_object_id
same label across sources != reviewed identity match
```

This distinction is the basis for continuity across document indices, Revit model
versions and site observations.

## 3. Progressive multi-view understanding

Project Anatomy may establish useful topology before exact geometry is available.
It may know that an opening belongs to a wall, that two spaces are adjacent or
that a shaft spans several levels before it can reconstruct a complete solid.

The retained coordinate frames remain those defined by APU:

```text
PIXEL
PAGE
MODEL_LOCAL
PROJECT
GEO_NGF
```

Registration between sources is a reviewed calibration problem. Divergent
witnesses cap the permissible certainty of derived geometry and quantities.

```text
topology known != geometry complete
geometry aligned != identity confirmed
identity confirmed != every property validated
```

The same server-owned identities may later support tree, plan, section, photo,
IFC, Revit or 3D lenses. A viewer never becomes a parallel truth store.

## 4. Professional first wave

The first useful wave is architecture-led and reuses the same APU identities and
provenance across five viewpoints:

```text
architecture and spatial design
project economy and quantities
construction-site review and DET support
thermal-data preparation and RE2020 consistency
life-cycle assessment and carbon analysis
```

Detailed structural and MEP/CVC engineering are not first-wave design
responsibilities. Their objects may be observed where required for architectural
coordination and interfaces without Pantheon replacing the relevant BET.

### Architecture and spatial design

Project Anatomy supports program, spaces, levels, zones, circulation, openings,
interfaces, phase states and source-backed variant or index comparison.

### Economy and quantities

Quantities remain sourced claims attached to objects or groups. Accepted amounts,
budgets, contractual values and adopted DPGF quantities remain governed
ProjectClaim or other business-record responsibilities.

```text
APU quantity != accepted DPGF quantity
quantity x unit price != approved budget
```

### Site and DET

Site observations, photographs, reserves, substitutions and temporary states may
reference APU identities. A reserve remains a WorkIssue or other governed project
record; it does not become a hidden graph status.

```text
photo timestamp != work acceptance
site observation != as-built canonization
```

### RE2020 and thermal preparation

APU may supply sourced geometry, envelope, opening, orientation, material and zone
candidates to a separate admitted calculation binding. It does not issue a
regulatory conclusion.

```text
calculation input candidate != validated input
calculation success != compliance decision
```

### ACV and carbon preparation

Material, product, quantity, scenario and environmental-source candidates retain
version, applicability, assumptions and uncertainty. A specialist calculation
binding remains separate.

```text
product candidate matched != product specified
FDES referenced != FDES applicable
carbon result computed != ACV approved
```

## 5. Source-specific expectations

Plans, sections, elevations and details contribute complementary occurrences and
locators. A detail may concern an interface between several objects and must not be
forced onto one room or element.

CCTP and DPGF fragments may concern objects, groups, zones, systems or classes of
objects. They produce source-backed requirements or values, not direct object
mutation.

Site photographs preserve capture time, author, viewpoint or zone candidate,
visible-object candidates, occlusion and localization limitations.

IFC and Revit are high-density source representations. Their GUIDs, ElementIds,
parameters and geometry support reviewed matching but do not define Pantheon
identity or professional truth.

Exact Revit context, binding freshness, local exposure, preflight and transaction
requirements are owned by `REVIT_LOCAL_ADAPTER.md` and its subordinate plugin
contracts. They are not repeated here.

## 6. Candidate routing categories

The following are presentation and routing categories over existing owners, not
new canonical entities:

```text
Spatial
-> hierarchy, zone, location, geometry or topological relation candidate.

Element
-> object kind, identity match, property, material or assembly candidate.

Requirement
-> program, CCTP, regulatory-source or professional-intent candidate.

Observation
-> site, document, IFC, Revit or manual observation candidate.

Contradiction
-> competing sourced assertions retained for review.

Missing information
-> absence or doubt with the material required to resolve it.
```

A proposed calculation or inference uses the existing APU derivation and Execution
Result boundaries. This annex introduces no generic `Derivation` object and no
`Consequence` attribute.

## 7. Operational cross-links

One APU identity may be referenced without duplication by:

```text
Information
ProjectClaim
WorkIssue
DecisionRequest or Decision
Document fragment or source representation
```

A factual project assertion may become a separately governed ProjectClaim through
its owning contract. Work remains a WorkIssue. A consequential choice remains a
DecisionRequest followed by a separate Decision where applicable.

```text
APU object exists != ProjectClaim created
object displayed under a task != WorkIssue duplicated
Decision recorded != APU mutation applied
```

## 8. Minimum useful projection

A read-only server-calculated Project Anatomy projection should answer, with
provenance and uncertainty:

```text
What exists in this project and where?
Which objects belong together or span several levels or sources?
Which exact source and locator support an assertion?
What changed between indices, variants or observations?
What is required, proposed, observed or as-built?
Which quantities, materials or dimensions conflict?
Which fragments remain unmapped?
Which WorkIssues and Decisions concern the object without being duplicated?
Which assumptions feed thermal, cost or carbon work?
What is known, derived, missing or awaiting human arbitration?
```

The first useful surface does not require a full 3D viewer. Structure, relations,
phases, provenance, uncertainty, contradictions and unmapped material are enough
to prove the authority boundary.

## 9. Preserved later extensions

Technical assemblies, constructive interfaces and coordination issues remain later
extensions already anticipated by the APU owners. The first executable slice must
preserve source-fragment links, object groups, property sets, qualified relations
and operational cross-links so those extensions do not require a parallel model.

## 10. Final boundary

```text
Sources describe and support.
Adapters detect and propose.
Hermes may orchestrate and return candidates.
APU owns reviewed project objects and domain relations.
Project Anatomy projects that authority for the user.
ProjectClaims govern consequential project assertions.
WorkIssue and DecisionRequest retain their own responsibilities.
The human decides consequential effects.
```

No schema, migration, API, Cockpit implementation, adapter runtime, automatic
object creation, automatic Evidence admission, automatic contradiction resolution
or professional validation is introduced by this annex.
