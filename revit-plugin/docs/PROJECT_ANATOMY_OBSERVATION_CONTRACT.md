# Revit 2027 ↔ Project Anatomy V0.2 observation contract

Status: executable candidate exchange contract; Revit adapter implementation and live Revit support remain external/to verify.

Authority relationship:

- `docs/domain-packs/architecture/PROJECT_ANATOMY_MODEL.md` remains the conceptual authority for Project Anatomy V0.2;
- `docs/governance/REVIT_LOCAL_ADAPTER.md` remains the canonical Revit execution boundary;
- the V0.2 schemas remain the structural authority for `source_representation`, `attribute_claim` and `relation_claim`;
- `schemas/architecture-project-understanding/observation_bundle.schema.yaml` is the executable candidate exchange authority;
- this note specializes the Revit 2027 adapter seam and creates no second APU, Evidence, approval or runtime authority;
- the production add-in and Host Agent remain external implementation artifacts.

## 1. Purpose

The Revit adapter translates live Revit source reality into bounded observations that Pantheon can inspect, persist, review and later align with Project Anatomy.

```text
Revit live state
→ Revit Context Snapshot
→ source-bound observations
→ Observation Bundle candidate
→ Hermes interpretation / matching candidate
→ Pantheon review and governance
→ Project Anatomy owner application
```

The add-in does not decide project identity and does not directly create canonical project objects.

```text
Revit ElementId != stable_object_id
Revit UniqueId != stable_object_id
source representation stored != project truth
attribute observed != attribute accepted for every downstream purpose
relation observed != stable project-world relation
matching candidate != identity alignment admitted
runtime success != Evidence
transaction success != governance approval
```

## 2. Target implementation baseline

The first production binding targets:

```text
product: Autodesk Revit
release: 2027
target framework: .NET 10 / Windows, subject to final Revit 2027 API verification
execution: local only
Internet dependency: none
Autodesk Assistant dependency: none
Autodesk Public MCP dependency: none
APS dependency: none
```

This is a target, not a support claim. A capability becomes `supported` only after its live Revit 2027 conformance tests pass.

## 3. V0.2 project-world primitives

The adapter is designed around the frozen core:

```text
stable_object
source_representation
attribute_claim
relation_claim
```

Its normal contribution is:

```text
source_representation
attribute_claim candidate about a source_representation
relation_claim candidate between source_representations
```

An identity proposal is not emitted as a stable-object mutation. It is a candidate relation:

```text
relation_type = identity.represents
subject_ref = source_representation
object_ref = stable_object
```

Only the governed Project Anatomy owner may apply that alignment.

## 4. Revit source representation

A Revit occurrence maps naturally to `source_representation`. The following example uses only vocabulary accepted by the current V0.2 shared schema:

```yaml
representation_id: rep.revit.project-a.3f54
project_ref: project-a
source_artifact_ref: source.revit.model-a
source_version_ref: snapshot.revit.model-a.00042
source_kind: revit
identifiers:
  - scheme: revit.unique_id
    value: "3f54..."
  - scheme: revit.element_id
    value: "145772"
locators:
  - type: element_id
    value: "145772"
    note: "Document source.revit.model-a"
observed_at: "2026-08-07T21:00:00Z"
binding_ref: binding.revit-local.workstation-01
adapter_version: "0.1.0"
freshness_token: "sha256:..."
content_digest: "sha256:..."
coordinate_frame: MODEL_LOCAL
context:
  document_ref: revit-document:model-a
  view_ref: revit-view:level-00
  phase_ref: revit-phase:new-construction
  design_option_ref: revit-option:main
  workset_ref: revit-workset:architecture
  level_ref: revit-level:00
  native_context:
    category: OST_Doors
    family: Porte intérieure
    type: P93
proof_status: candidate
limitations: []
evidence_refs: []
```

The Revit binding/profile owns the exact identifier conventions. Project Anatomy does not need Revit-specific fields in its canonical core.

### Native identifiers

Retain when available:

- `ElementId` as an execution locator bound to the observed document state;
- `UniqueId` as a more durable Revit-native identifier;
- document and linked-document identity;
- category/family/type as source classification context;
- phase, option, workset, level and view context.

No native identifier establishes Pantheon stable identity by itself.

## 5. Revit Context Snapshot

Before an operation emits observations, the add-in must be able to report:

```text
binding identity
plugin version
Revit version/build
document identity
read-only/modifiable state
worksharing state
active view
selection
phase context
design option context
units
coordinate context
observed_at
freshness token
```

The snapshot is execution/source context, not a Project Anatomy object. Operations requiring live freshness refuse a stale snapshot.

## 6. Observation Bundle

Project Anatomy V0.2 identifies an Observation Bundle as the intended adapter seam. For Revit it should be bounded, immutable and source-oriented:

```yaml
observation_bundle_id: observation-bundle.revit.00042
project_ref: project-a
task_contract_ref: task-contract.observe-scope.42
basis:
  source_artifact_refs: [source.revit.model-a]
  source_version_refs: [snapshot.revit.model-a.00042]
  exact_digests:
    - source_artifact_ref: source.revit.model-a
      source_version_ref: snapshot.revit.model-a.00042
      digest: sha256:...
method:
  capability_id: building_model.observe.scope
  binding_id: binding.revit-local.workstation-01
  operation_id: revit.architecture.observe_scope.v1
  adapter_ref: pantheon.revit
  adapter_version: "0.1.0"
  request_ref: request-42
observed_at: "2026-08-07T21:00:00Z"
freshness_token: "sha256:..."
scope:
  document_refs: [revit-document:model-a]
  level_refs: [revit-level:00]
  categories: [OST_Rooms, OST_Doors]
  include_linked_sources: false
coverage:
  completeness: partial_for_declared_scope
  observed_scope:
    document_refs: [revit-document:model-a]
    source_snapshot_refs: [snapshot.revit.model-a.00042]
    categories: [OST_Rooms, OST_Doors]
    include_linked_sources: false
  excluded_reasons: [linked_models_not_observed]
  absence_inference_allowed: false
source_representations: []
attribute_claim_candidates: []
relation_claim_candidates: []
gaps: []
withheld: []
warnings: []
limitations: []
operational_outcome: success
authority:
  is_fact: false
  is_evidence: false
  is_decision: false
  is_memory: false
  is_apu_write: false
  authorizes_external_effect: false
```

The executable shape is deliberately an exchange/candidate schema. It is not a
database table, adapter-ingestion API or permission to apply its primitives.

## 7. Attribute observations

A Revit value becomes a candidate `attribute_claim` about its source representation unless a later governed process has aligned it to project identity.

Example conforming to the current shared vocabulary:

```yaml
attribute_claim_id: claim.revit.width.145772
subject_ref:
  entity_type: source_representation
  entity_id: rep.revit.project-a.3f54
attribute_key: geometry.width
value:
  value_type: number
  value: 930
  unit: mm
assertion_mode: observed
source_authority: project_working_document
proof_status: candidate
certainty: E4
source_representation_refs:
  - rep.revit.project-a.3f54
```

`source_authority` is determined from the governed status of the source artifact. The adapter must not invent a stronger authority level merely because Revit supplied the value.

The Revit profile maps native parameters to governed `attribute_key` values. Unknown or ambiguous mappings remain source-native context or are withheld.

## 8. Relation observations

Relations directly observable in Revit may become candidate `relation_claim` records between source representations, for example:

- hosted-by;
- containment;
- room/door adjacency when deterministically resolvable;
- source-native grouping;
- source-native type/instance relations where a governed relation type exists.

If a relation requires interpretation beyond deterministic Revit state, it must carry the corresponding proposed/derived posture and derivation provenance.

## 9. Identity alignment

Identity remains outside add-in authority. Hermes/Pantheon may propose:

```yaml
relation_claim_id: relation.identity.represents.145772
subject_ref:
  entity_type: source_representation
  entity_id: rep.revit.project-a.3f54
relation_type: identity.represents
object_ref:
  entity_type: stable_object
  entity_id: object.door.0042
assertion_mode: proposed
source_authority: model_interpretation_candidate
proof_status: candidate
certainty: E2
source_representation_refs:
  - rep.revit.project-a.3f54
```

The source representation remains valid even when identity is unresolved.

## 10. Delta-first observation

Revit is a high-density source. Continuous exchange should prefer:

```text
bounded baseline
+ explicit scope
+ source freshness
+ delta since baseline
```

A delta can report that a representation was added, changed or no longer observed in a defined source scope. It can also report changed attribute/relation observations.

```text
representation no longer found != stable_object deleted
```

Project-object retirement/deletion remains governed outside the adapter.

## 11. Coverage and absence

An empty result is not automatically a negative project fact. Extractions capable of supporting absence reasoning should report coverage:

```yaml
coverage:
  completeness: partial_for_declared_scope
  observed_scope:
    document_refs: [revit-document:model-a]
    categories: [OST_Rooms, OST_Doors]
    phase_refs: [revit-phase:new-construction]
    include_linked_sources: false
  excluded_reasons: [linked_models_not_observed]
  absence_inference_allowed: false
```

Without sufficient coverage, Hermes/Pantheon must not infer absence from non-return.

## 12. Operational outcomes

Do not collapse every non-success into an exception.

```text
success
withheld
blocked
refused
failed
cancelled
rolled_back
```

- `withheld`: the adapter cannot assert the observation/action safely; unrelated task work may continue;
- `blocked`: a dependency or user action is required;
- `refused`: scope, freshness, safety, contract or authorization conditions are unsatisfied;
- `failed`: unexpected technical execution failure;
- `rolled_back`: a started transaction had its effects reverted.

Examples:

```text
family required but absent -> blocked
ambiguous room adjacency -> withheld
wrong active document -> refused_document_mismatch
stale document -> refused_stale_document
stale active view -> refused_stale_view
stale selection -> refused_stale_selection
worksharing ownership conflict -> blocked_worksharing
unexpected API exception -> failed
```

## 13. Closed Revit Operation Registry

Every executable add-in operation must exist in one closed registry. The registry should generate or verify:

```text
Capability Manifest
Host Agent tool bindings
advanced local-exposure UI
documentation
conformance fixtures
```

Minimum conceptual entry:

```yaml
operation_id: revit.architecture.observe_rooms.v1
capability_id: building_model.observe.spaces
effect_class: read_only
warning_level: W0
revit_versions: [2027]
requires:
  active_document: true
  live_context: true
  transaction: false
outputs:
  observation_bundle: true
  source_representations: true
  attribute_claim_candidates: true
  relation_claim_candidates: true
local_exposure:
  configurable: true
preflight:
  required: false
tests:
  contract: required
  live_revit: required
```

The registry is not created by reflecting over the Revit API. An operation absent from it is not executable through Hermes.

## 14. One deterministic operation layer

Manual UI and Hermes must execute the same implementation:

```text
Ribbon / local UI ─┐
                   ├─> Revit Operation -> Revit API
Host Agent/Hermes ─┘
```

Parity is a testable requirement, not merely a code-style preference.

## 15. Units boundary

Revit internal units do not leak into the Pantheon/Hermes contract. Exposed claims carry explicit units, typically:

```text
length: mm or m according to the governed attribute profile
area: m²
volume: m³
angle: degrees when agent-facing
```

Conversions remain inside the binding and are live-tested on Revit 2027.

## 16. First-wave observation scope

### Architecture

- document/view/selection;
- levels, phases, design options, worksets;
- rooms and boundaries;
- walls, floors, roofs, ceilings;
- doors, windows, openings;
- architectural families/types;
- materials and compound structures;
- views, sheets, schedules;
- warnings/model-quality observations.

### Economy

- deterministic quantities;
- occurrence/type counts;
- material quantities;
- bounded snapshot deltas;
- schedule data.

### Construction / DET

- exact element navigation;
- visual/source snapshots;
- revision/delta observation;
- element state needed to verify a reviewed issue.

### RE2020 / thermal preparation

- envelope geometry/orientation;
- spaces and volumes;
- openings;
- materials/compositions;
- source parameters required by an external deterministic calculation engine.

### ACV / carbon preparation

- material/component quantities;
- product/type identifiers when present;
- source classifications and provenance for later environmental mapping.

The add-in is not the cost owner, RE2020 calculation engine or carbon database.

## 17. Explicit exclusions

The first implementation must not expose:

```text
send_code_to_revit
execute_csharp
execute_python
eval
arbitrary reflection dispatch
arbitrary Revit API invocation
silent save
silent synchronize-with-central
automatic purge
generic unrestricted delete
provider/LLM calls inside the add-in
project memory inside the add-in
workflow scheduler inside the add-in
```

Generated code remains W5 and is not executable in V0.

## 18. Mutation remains a separate seam

Observation compatibility with Project Anatomy does not authorize model writes.

```text
ChangeCandidate
→ fresh Revit Context Snapshot
→ technical preflight
→ Pantheon/human authorization
→ exact bounded Operation Request
→ named Revit transaction
→ Action Report
→ result review
```

A Project Anatomy write and a Revit model write are distinct effects with distinct authorization paths.

## 19. Revit 2027 conformance

Before a capability is marked supported, test at least:

- input/schema contract;
- invalid input -> structured refusal/error;
- wrong document;
- stale context;
- unit conversion;
- phases;
- design options where relevant;
- worksharing where relevant;
- linked-model context where relevant;
- repeated invocation with no stale previous result;
- result bound to the exact request/operation;
- live Revit result verification;
- zero unexpected mutation for reads.

Writes additionally require preflight, exact targets, named transaction, warning/failure capture, rollback behavior, retry/idempotency posture, before/after reporting and proof of no out-of-scope effect.

## 20. Dependency posture

External repositories remain implementation references, not authorities:

```text
Nice3point/RevitTemplates
→ candidate scaffold and multi-version packaging patterns

Nice3point/RevitApi
→ candidate build-time API references; redistribution rights still to verify

DTDucas/RevitMCPSDK
→ candidate command-registry / JSON-RPC / ExternalEvent patterns;
  direct dependency not yet approved

mcp-servers-for-revit and derivatives
→ command catalog and live-test references only
```

No external MCP repository is adopted as Pantheon runtime here.

## 21. First admissible executable proof

The first production-repo proof remains intentionally small:

```text
1. load in Revit 2027
2. identify plugin/binding build
3. observe active document
4. observe active view
5. observe exact selection
6. expose a closed capability manifest
7. execute one bounded read through ExternalEvent
8. emit an immutable Observation Bundle with source representations
9. refuse stale/wrong-document requests
10. prove zero model mutation
11. run the same operation from UI and Host Agent with equivalent domain result
12. succeed with Internet unavailable
```

It does not require stable-object creation, canonization, model write, save, sync, provider calls or OpenWebUI integration.

## 22. Status

Documented:

- Revit 2027 target;
- Project Anatomy V0.2 mapping;
- source-representation-first posture;
- executable Observation Bundle candidate schema;
- delta, coverage and gap semantics;
- registry/parity/conformance expectations.

Implemented outside Pantheon only after its own reviewed merge:

- compiling Revit 2027 add-in;
- Host Agent;
- Operation Registry code.

Still non-implemented/to verify at this authority surface:

- live Revit 2027 tests;
- Project Anatomy ingestion of adapter bundles;
- model mutations.

Nothing in this note upgrades those items to implemented.
