# Workspace Manifest Inspector — document routing qualification

Status: synthetic, non-client, non-production.

Parent issue: Pantheon-Next#859.

This qualification extends the existing Pantheon-Next#688/#689 fixture family without
adopting a production `document.yaml` schema.

## M2 — information routing corpus

### Question under test

Can one lightweight document-local `information[]` carrier express useful,
addressable references across heterogeneous architecture sources while keeping
all existing authority owners intact?

The corpus uses one synthetic façade/window context across:

- architectural plan index C;
- architectural plan index D with the same information repositioned;
- structural plan with grid-only localization plus one general comment with no
  precise anchor;
- IFC source with a native element identifier;
- CCTP-like specification;
- DPGF-like price schedule;
- BET-like email, including one deliberately ambiguous statement.

### Candidate shape

The fixture intentionally uses only the small shape being qualified:

```text
information[]
├── info_id
├── text?          # source-local summary when useful
├── anchor?        # best available source-local locator
├── comment?       # free context; may be the only descriptive field
├── status?        # lightweight, not professional approval
└── refs[]?        # heterogeneous navigation/context refs
```

Only `info_id` is structurally assumed for every item by this fixture. An item
must carry useful local context through `text` or `comment`, but no precise
anchor, status or ref is required.

Reference schemes are open strings in this fixture. Only schemes required by
the corpus are exercised now:

```text
anatomy
document
ifc
web
```

This is not a registry adoption. Future `bcf`, `bsdd`, `ids`, `revit`,
`opencde` or other schemes require demonstrated use rather than pre-allocation.

### Project Anatomy boundary

Project Anatomy already owns project semantics and its existing external seam
is the canonical Observation Bundle. This M2 fixture does not implement a
second plan-to-Anatomy pipeline.

```text
manifest information/ref
!= relation_claim
!= attribute_claim
!= requirement
!= Evidence
!= Decision
```

An `anatomy` ref in this fixture is deliberately a proposed synthetic target,
not a fabricated governed Anatomy UUID. Semantic promotion, when justified,
must use the existing Observation Bundle/review/application owners.

The IFC GlobalId remains a source-native identifier and is explicitly distinct
from the candidate stable-object reference.

### Repositioning

`I-W17-DETAIL` appears in plan indices C and D with the same information
identity and a different page/bounding box. The fixture preserves both version
contexts rather than overwriting the older source occurrence.

```text
same information identity
!= same source coordinates

new locator
!= new governed object identity
```

### Weak localization and ambiguity

The structural case `I-STRUCT-GENERAL-002` intentionally carries only a comment
and no anchor or refs. It demonstrates that missing grid/cloud/page precision
does not make an information item unusable.

The email case `I-MAIL-AMBIGUOUS-002` has no resolved refs. Its source text is
retained with a `to_check` state and a comment explaining that several targets
match.

```text
weak localization
!= fabricated precision

ambiguous reference
-> unresolved / no fabricated target
```

### Deep navigation and preview boundary

Locators retain enough context for a later adapter to reconstruct a preview or
deep navigation target when such a locator exists. The preview itself is not
persisted in this fixture.

```text
source/version + locator
-> reconstructible preview/navigation

preview
!= source
!= Evidence
```

## M3 — routing shape decision

Exact decision fixture: `m3_routing_decision.yaml`.

Repository observation at the recorded baseline:

```text
production document.yaml schema = absent
M2 common carrier               = expressive as a fixture
Project Anatomy semantic seam   = canonical Observation Bundle
document structure derivative   = existing document_knowledge_slice contract
```

M3 therefore selects outcome A from Pantheon-Next#859:

```text
routing persistence = none
routing resolution  = calculated or explicitly unresolved at use time
```

Do not add these document-local persisted routing fields now:

```text
profile_refs
analysis_routes
capabilities
```

Document kind, physical format and partial source scope may inform routing, but
they do not transfer authority. Existing Project Anatomy profile references and
Capability bindings are reused when they are actually available; absence of an
executable/current resolution remains unresolved rather than being copied into
the sidecar as guessed configuration.

M2 also does not by itself authorize production persistence of `information[]`
or `scope`. They remain useful candidate workspace metadata because anchors,
comments and confirmed navigation references may not be reconstructible, but a
production sidecar owner/write lifecycle has not yet been adopted.

```text
M2 expressiveness
!= production persistence decision

local information/ref
!= Project Anatomy claim

source scope
!= project completeness
```

This avoids three duplicate persistence paths:

```text
document.yaml ↛ copied document structure/chunks
             ↛ copied Project Anatomy claims
             ↛ copied Capability/profile selection state
```

The next qualification is M4: prove that document analysis producing Project
Anatomy semantics uses the canonical Observation Bundle and existing
review/application path rather than a manifest-owned or `document_knowledge`
semantic bypass.

## Non-goals

This qualification does not:

- adopt a production sidecar schema;
- create `PlanManifest`, `CctpManifest` or other per-type schemas;
- create a new Project Anatomy primitive or graph;
- persist extracted document knowledge wholesale into the manifest;
- infer professional approval from `status` or comments;
- promote web references to Evidence;
- turn IFC native identifiers into Pantheon stable-object identity;
- implement BCF, IDS, bSDD or openCDE inside Pantheon;
- authorize automatic Workspace writes.

`tests/test_workspace_manifest_information_routing.py` protects the M2 fixture
invariants. `tests/test_workspace_manifest_m3_routing_decision.py` protects the
M3 non-persistence and downstream-contract reuse decision.
