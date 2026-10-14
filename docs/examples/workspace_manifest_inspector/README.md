# Workspace Manifest Inspector — synthetic CCTP fixtures

Status: synthetic, non-client, non-production.

Parent candidate architecture:
`docs/architecture/WORKSPACE_MANIFEST_INSPECTOR_CANDIDATE.md`.

These fixtures answer two deliberately narrow questions before any Obsidian
plugin or production manifest schema is implemented:

1. can a workspace package sidecar map to the existing Professional Document
   family/version identities without becoming a second authority owner?
2. can a folder with Markdown offer a local "Generate" action and produce an
   unadmitted skeleton without fabricating governed identity?

Neither fixture adopts a production manifestability rule or production sidecar
schema.

## Scenario A — mapped existing governed document

The first object is one internally authored CCTP package:

```text
workspace/
└── CCTP/
    ├── document.yaml
    └── CCTP.md
```

The package is mapped to separate synthetic governed records:

```text
governed/
├── document_family.yaml
├── indexed_document_version.yaml
└── currentness_current_for_consultation.yaml
```

The governed records validate against the existing schemas on the repository
baseline recorded by the sidecar. The sidecar itself is deliberately **not**
validated by a new production manifest schema.

### What scenario A proves

```text
folder name
= local navigation title

document.yaml
= candidate carrier for workspace/package metadata and governed-ID references

document_family_id
= existing governed Professional Document family identity

document_version_id
= existing governed indexed version identity

currentness_current_for_consultation.yaml
= separate calculated currentness projection

CCTP.md digest
= exact basis used by the sidecar and indexed version
```

The sidecar therefore does not contain:

```text
current_for_consultation
current_contractual
current_for_execution
authority_status
effect_class
version_status
professional approval
Evidence
Decision
```

Those semantics remain with their existing governed owners/projections.

## Scenario B — qualifiable package without manifest

The second fixture starts with no `document.yaml` and no governed identity:

```text
workspace_qualifiable/
└── CCTP/
    └── CCTP.md
```

For this fixture only, a local inspector heuristic may expose:

```text
Markdown present
+ no document.yaml
→ local health = QUALIFIABLE
→ [ Generate ]
```

This is an **offer to qualify**, not a rule that every folder containing
Markdown must have a manifest.

The deterministic test-only generator produces an expected local skeleton
outside the workspace package:

```text
expected/
└── qualifiable_cctp_local_skeleton.yaml
```

The skeleton carries only observed local facts:

```text
package name
Markdown filename
exact Markdown digest
local health
identity mapping unresolved
semantic enrichment not requested
```

It deliberately carries no `document_family_id`, no `document_version_id`, no
currentness, no authority fields, no tags, no semantic full name and no
artifact-origin inference.

```text
local skeleton
!= governed Document
!= admitted identity
!= manifest schema adoption
```

A later qualification step would have to resolve whether the package maps to
an existing Document family/version or whether a new governed identity is
admitted by the applicable owner.

## Expected Card composition

For scenario A an inspector may compose:

```text
TITLE
CCTP
# derived from the actual folder name

SUBTITLE
Cahier des clauses techniques particulières — Fixture DCE
# derived from manifest display.full_name

LOCAL HEALTH
COHERENT
# only after local structural/digest checks

CURRENTNESS OVERLAY
current_for_consultation = C
# only from the separate currentness projection
```

For scenario B the local Card may remain intentionally sparse:

```text
TITLE
CCTP

LOCAL HEALTH
QUALIFIABLE

Markdown detected
No manifest
No governed identity resolved

[ Generate ]
```

`COHERENT` and `QUALIFIABLE` are plugin-health vocabulary only. They are not
professional lifecycle, authority or write-posture values.

## Non-goals

These fixtures do not:

- adopt `document.yaml` as a production schema;
- establish that every Markdown folder is manifestable;
- admit a real agency/client Document;
- create Document IDs from folder paths;
- infer currentness from index labels or filenames;
- define hierarchical tags;
- generate semantic title, summary, tags or artifact origin locally;
- implement Obsidian, Swiper, LiveSync or Hermes;
- authorize a Workspace write path;
- migrate any current owner.

## Test contract

`tests/test_workspace_manifest_inspector_fixture.py` verifies scenario A:

1. the synthetic family/version/currentness records validate against existing
   Pantheon schemas;
2. the manifest references exactly the same family/version UUIDs;
3. the Markdown SHA-256 matches both the manifest and indexed version;
4. currentness/authority fields are absent from the sidecar;
5. the Card title source remains the physical folder name while the fuller
   semantic name remains display metadata;
6. the sidecar pins the exact schema blob revisions used by its local
   validation basis.

It also verifies scenario B:

7. the selected package contains Markdown but no manifest;
8. the fixture heuristic may return `QUALIFIABLE` without making a manifest
   mandatory;
9. deterministic skeleton generation matches the expected fixture and exact
   Markdown digest;
10. the generated skeleton contains no governed IDs, UUIDs, currentness,
    authority fields or semantic enrichment fabricated locally.

Passing these tests proves fixture compatibility only. It does not authorize a
production manifest schema, plugin implementation or owner migration.
