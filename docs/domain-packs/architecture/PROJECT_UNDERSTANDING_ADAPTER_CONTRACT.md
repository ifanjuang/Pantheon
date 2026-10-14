# Architecture Project Understanding — Adapter Contract

Status: candidate support doctrine — adapter chokepoint for Architecture Project Understanding.

This document defines the binding an external source adapter must respect to feed Architecture Project Understanding (APU) without becoming an APU authority.

The adapter may read PDF/drawings, IFC, images, photographs, Revit or another admitted source. It is runtime and lives outside Pantheon. Pantheon governs contracts, scopes, candidate admission, Evidence expectations and downstream review.

It is documentation only. It implements no reader, OCR, vision model, extractor, Revit add-in, IFC engine or connector. It specializes the generic `BRIDGE_CONTRACT.md` and `ADAPTERS_AND_BINDINGS.md` for the APU family.

```text
Optional runtime clients may expose interaction.
Hermes Agent executes/orchestrates.
Pantheon Next governs.
The human decides consequential effects.
```

## 1. Chokepoint

Every observational APU adapter crosses one bounded seam:

```text
Task Contract + bounded project/source context in
-> external adapter/runtime
-> Observation Bundle Candidate
 + Evidence Pack Candidate out
```

`Observation Bundle Candidate` is the APU specialization of the generic bridge `result_candidate` slot. It is not a new execution-result authority and it must not be confused with the provisioning-oriented `catalog/schemas/execution-result-candidate.schema.json` contract.

```text
Observation Bundle Candidate != Project Anatomy mutation
Observation Bundle Candidate != Evidence Pack
Observation Bundle Candidate != Proof
adapter success != candidate admission
```

The executable validation contract is
`schemas/architecture-project-understanding/observation_bundle.schema.yaml`.
It is a candidate exchange schema only: it creates no ingestion API,
persistence owner, APU application or authority transfer.

## 2. Input boundary

The Task Contract and bounded context should provide or reference only what the adapter needs for the requested observation.

Typical inputs include:

```text
project_ref
task_contract_ref
context_pack_ref when applicable
source artifact refs
source version / digest / professional index when known
revision_set_ref when a reviewed documentary baseline exists
requested capability_id
binding_id / operation_id
requested scope
freshness expectations
allowed output categories
expected evidence
known stable_object refs only when identity candidates may be evaluated
```

A missing professional index, source version or stable identity is valid when explicitly represented as unavailable. The adapter must not manufacture missing provenance to make an input look complete.

```text
missing source metadata != guessed source metadata
known Revit/IFC/native id != stable_object_id
same label != confirmed identity
```

## 3. Observation Bundle Candidate

The domain result should preserve enough structure for Pantheon/MVP to validate, normalize and review candidates without coupling the adapter to PostgreSQL persistence.

Executable envelope:

```text
observation_bundle_id
project_ref
task_contract_ref
basis
  source_artifact_refs
  source_version_refs / digests when known
  revision_set_ref when applicable
method
  capability_id
  binding_id
  operation_id when applicable
  adapter_ref
  adapter/runtime version
  run/request correlation id
observed_at
freshness_token when a source observation succeeded
scope
coverage
limitations
source_representations[]
attribute_claim_candidates[]
relation_claim_candidates[]
gaps[]
withheld[]
warnings[]
operational_outcome
authority
```

This is an exchange validation shape, not a database or persistence schema.
`scope` records the declared observation boundary; `coverage.observed_scope`
records what was actually traversed. Completeness is closed to
`complete_for_declared_scope`, `partial_for_declared_scope` or `unknown`.
Partial and unknown coverage force `absence_inference_allowed = false`.

The deterministic, source-independent H5.2 qualification corpus is
`schemas/examples/architecture-project-understanding/qualification_corpus.yaml`.
It combines representative chronology, contradiction, partial-coverage,
granularity and non-authority scenarios without claiming live adapter or
real-project validation. The corpus reuses this executable envelope and adds no
runtime or persistence contract.

### Source representations

An observational adapter may emit candidate `source_representation` records conforming to the active Project Anatomy contract.

A source representation describes one localizable observation in one exact source/version context. It may carry native identity, locator, frame/calibration, observed time, freshness, coverage and limitations where the active schema permits them.

It may exist before Pantheon has resolved a durable project identity.

```text
source_representation observed != stable identity resolved
source-native id != stable_object_id
```

### Attribute claims

The adapter may emit candidate `attribute_claim` records about:

```text
source_representation
or
an already-known stable_object when the bounded context explicitly supplies it
```

For unresolved identity, observations should stay attached to the source representation rather than forcing a new project object.

Claims use the active V0.2 assertion vocabulary (`observed`, `proposed`, `derived`, `human_asserted`, `as_built`) according to their real method. An adapter normally emits `observed`, `proposed` or deterministic `derived` assertions; it must not relabel prescriptive intent as observation.

Detailed classifications are claims/predicates. They do not expand `object_family` and do not become identity merely because a source reports `IfcDoor`, `OST_Doors`, a drawing label or a DPGF class.

### Relation claims

The adapter may emit candidate `relation_claim` records between source/project entities available in the bounded context.

Identity alignment is expressed only as a candidate relation:

```text
source_representation
-- identity.represents -->
stable_object
```

The stable object must already be an available project identity supplied by the governed context. The adapter must not create a new `stable_object` merely to complete a match.

```text
candidate match != identity accepted
source agreement != reviewed identity
```

## 4. What adapters do not emit

Observational adapters emit only the active Project Anatomy primitives and
supporting provenance contracts. They must not introduce a parallel identity,
property, relation, phase, group, override or match carrier.

They also must not silently create:

```text
stable_object
ProjectClaim
Evidence
Proof
Decision
WorkIssue closure
approval/use grant
memory promotion
```

A new durable project identity is a separate governed owner action. A human correction is represented through new/superseding governed claims or another explicit governance mechanism; it is not an adapter-owned `human_override` write.

## 5. Requirements and prescriptive extraction

`requirement` remains separate from observed facts.

This observational adapter contract must not smuggle programme, CCTP, IDS or regulatory intent into `attribute_claim` as though it had been observed in the project state.

When a Task Contract explicitly requests prescriptive extraction, the returned requirement material remains candidate support for the separate requirement/governance path and must preserve its source provenance. It does not become an observed project fact and it does not create a compliance verdict.

```text
required != observed
requirement extracted != requirement admitted
IDS check result != professional approval
```

## 6. Coverage, absence and delta

Coverage is mandatory whenever an adapter or downstream consumer intends to interpret absence.

Coverage should be as specific as the source/method requires, for example:

```text
levels / zones
categories / classes
phases
sheets / pages / drawing regions
views
property groups
measurement modes
source snapshot/version
```

Hard rule:

```text
not found != absent
missing from snapshot != project object deleted
```

An absence conclusion is admissible only when the declared coverage and method semantics support it.

High-density adapters such as Revit and IFC should support delta-first output when practical:

```text
added source representations
changed source representations
missing source representations
unchanged source representations
```

A `missing` source occurrence remains an observation outcome, not automatic stable-object retirement.

## 7. Gaps, withheld and operational outcomes

Operational inability or uncertainty must not be manufactured as project facts.

The Observation Bundle may carry typed operational items such as:

```text
gap
withheld
warning
ambiguous
missing_input
conflicting_sources
```

These remain result-state information unless a source explicitly asserts the same fact.

The adapter should distinguish, when relevant:

```text
success
withheld
blocked
refused
failed
cancelled
rolled_back
```

```text
withheld != failed
blocked != rejected project claim
runtime success != Evidence
```

## 8. Provenance and certainty

Every machine-actionable candidate must remain traceable to its observation method and source context.

Important fields should carry or resolve to the active Project Anatomy provenance structures, including source representation locators/refs and derivation refs when applicable.

When the active schema uses the E0–E4 certainty axis, an adapter may emit the governed band supported by its method. A hidden numeric model score is not promoted into a new Pantheon authority.

`proof_status` in current V0.2 contracts is a support qualification. It is not a Proof object, approval or task authorization.

```text
high certainty != approved
accepted_as_support != accepted for every use
```

## 9. Evidence Pack Candidate remains separate

The companion Evidence Pack Candidate makes the execution/result reviewable at governance level. It may summarize:

```text
linked Task Contract
sources used
assumptions
actions at governance-relevant level
risks
outputs
limitations
review needs
```

It may reference Observation Bundle/source material, but it must not duplicate the adapter's raw runtime state or become necessary to resume execution.

```text
Observation Bundle = candidate project/source observations
Evidence Pack Candidate = candidate governed justification for review
runtime trace = external observability material
```

These responsibilities must remain distinct.

## 10. Source-specific specializations

Source adapters may define stricter local bindings without changing this chokepoint.

Current reviewed examples:

```text
Revit
  REVIT_LOCAL_ADAPTER.md
  + revit-plugin/docs/PROJECT_ANATOMY_OBSERVATION_CONTRACT.md
  -> local Revit context, capability exposure, preflight, source-first observations,
     coverage/delta semantics and controlled model execution boundary.

Drawing / PDF takeoff
  docs/domain-packs/architecture/DRAWING_TAKEOFF_LOCAL_ADAPTER.md
  -> local drawing/takeoff source boundary, measurement provenance, scale/unit
     discipline, withheld/refusal semantics and offline packaging/adoption gates.
```

Future IFC, image or other adapters should specialize the same input/output seam rather than create parallel Project Anatomy output models.

```text
PDF measurement != Revit observation
IFC class != Pantheon identity
source agreement != reviewed identity match
quantity computed != quantity contractually accepted
```

Hermes may compare candidates from several admitted bindings. Cross-source synthesis still remains candidate material until the appropriate Pantheon/MVP review/application path accepts it.

## 11. Hard constraints

1. Adapter/runtime lives outside Pantheon and depends on Pantheon contracts, never the reverse.
2. Adapter output is candidate material. It never canonizes project truth.
3. Adapter does not create durable `stable_object` identity automatically.
4. Source-native identifiers remain correlation/matching material only.
5. Claims use the sole active Project Anatomy carriers; parallel carriers are invalid output.
6. Coverage precedes absence interpretation.
7. Missing/withheld/gap states are not synthesized as project facts.
8. Prescriptive intent stays separate from observed facts.
9. Evidence/Proof/approval/use authority is not transferred to the adapter.
10. Adapter output contract is not the pantheon-mvp database schema.
11. Adapter does not mutate its source unless a separately authorized writable capability explicitly allows that external effect.
12. A valid Observation Bundle does not authorize APU application; Pantheon/MVP validates and reviews what may be retained.

## 12. Reference shapes

- Project Anatomy conceptual model: `docs/domain-packs/architecture/PROJECT_ANATOMY_MODEL.md`.
- Active Project Anatomy schemas: `schemas/architecture-project-understanding/`.
- Observation Bundle Candidate schema: `schemas/architecture-project-understanding/observation_bundle.schema.yaml`.
- Generic bridge return boundary: `docs/governance/BRIDGE_CONTRACT.md`.
- Adapter dependency/version discipline: `docs/governance/ADAPTERS_AND_BINDINGS.md`.
- Evidence boundary: `docs/governance/EVIDENCE_PACK.md`.
- Task input authority: `docs/governance/TASK_CONTRACTS.md`.
- Revit specialization: `docs/governance/REVIT_LOCAL_ADAPTER.md` and `revit-plugin/docs/PROJECT_ANATOMY_OBSERVATION_CONTRACT.md`.
- Drawing takeoff specialization: `docs/domain-packs/architecture/DRAWING_TAKEOFF_LOCAL_ADAPTER.md`.
- Referential-integrity expectations for current APU schemas: `.github/scripts/check_apu_referential_integrity.py`.

## 13. Explicitly not implemented by this contract

This document does not implement:

```text
adapter ingestion API
Hermes workflow
Revit add-in or Host Agent
IFC/PDF/image adapter
stable-object creation flow
candidate admission workflow
Evidence admission
Proof
Cockpit projection
```

Those capabilities require separate reviewed slices.

## Final rule

```text
The adapter observes sources and returns candidates.
Hermes may orchestrate, compare and propose.
Pantheon/MVP validates and governs what may be retained.
Project Anatomy does not become a mirror of the adapter runtime.
The human retains consequential decisions.
```
