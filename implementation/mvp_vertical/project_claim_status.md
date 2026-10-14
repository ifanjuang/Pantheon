# ProjectClaim implementation boundary

Status: implemented candidate / not adopted / not activated.

This branch aligns the executable Agency Data candidate with the merged Pantheon Next ProjectClaim doctrine.

Implemented candidate:

- `agency.project.v2` separates core identity, descriptive attributes, semantic claim projections and system fields;
- consequential legacy Project JSONB keys are removed during pre-production schema initialization;
- `agency_project_claims` is append-only semantic storage;
- ProjectClaim writes validate against the vendored Pantheon Next governance schema;
- accepted claim types are limited to the Project registry;
- `source_backed` / `verified` require semantic `backing_ref`;
- ProjectClaim is not a visible Cockpit card family.

Non-equivalences:

```text
stored claim != approved value
source_backed != verified != opposable
ProjectClaim != Evidence
ProjectClaim != ChangeCandidate
CI green != adoption
```

Remaining before merge:

- expose claim projection through the existing Project read path without creating Claim cards;
- keep Hermes writes behind admitted bounded execution rather than the global Agency API;
- pass full CI after removing tests that still encode the obsolete Project-attributes model.
