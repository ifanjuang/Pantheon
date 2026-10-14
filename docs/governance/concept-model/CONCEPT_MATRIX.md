# Pantheon Concept Matrix

Status: validation-only support map — documented non-implemented.
Boundary profile: validation_only_trace.

This matrix identifies existing owners and placements. It is not a concept registry and does not replace any cited owner.

## Reading rule

```text
Owner
= document or owner family that defines the governed meaning.

Projection
= document or surface that may display or compose the concept.

Execution
= runtime seat, if an associated operation exists.

Human gate
= consequential decision that remains human.
```

## Initial concept map

| Concept | Current owner or owner family | Projection / exposure | Execution seat | Human gate | Current repository posture |
|---|---|---|---|---|---|
| Case | `CORE_CONCEPTS_MAP.md`, `TASK_CONTRACTS.md`, applicable Case/Situation owner documents | `CONTEXT_STACK.md`, `CARD_STACK_MODEL.md`, `PANTHEON_COCKPIT_UX_SPEC.md` | Hermes may execute a bounded Task Contract; Case meaning remains Pantheon-governed | scope, mission intent, consequential use and external effects | owner documented; cockpit projection candidate; no Case engine in Pantheon |
| Source | `RAW_DERIVED_GOVERNED_RECORDS.md`, `SOURCE_INGESTION_RETRIEVAL_MODEL.md` | Source Card, Evidence views and retrieval traces | external/Hermes-side ingestion and retrieval binding | source admission, access scope and reliance | doctrine documented; external implementation may be observed; Pantheon does not ingest |
| Evidence | `EVIDENCE_PACK.md`, `EVIDENCE_TOPOLOGY.md` and applicable Register doctrines | Evidence Card, Evidence views, Decision Surface | evidence producers may run externally; acceptance is not runtime-owned | evidence acceptance and consequential reliance | doctrine present; bounded projections exist; runtime success remains non-evidence |
| Gate | `APPROVALS.md` and applicable gate-specific doctrines | Gate Card, Decision Surface and bounded review collections | no autonomous execution seat; enforcement may be implemented by bounded policy checks | opening, satisfying, refusing or escalating a consequential gate | doctrine present; bounded projections exist; no automatic approval engine |
| Decision | decision owner contracts and schemas, `APPROVALS.md`, `DECISION_SURFACE_SPEC.md` for display/capture | Decision Card and Decision Surface | no runtime may decide on behalf of the accountable human | explicit scoped human determination | contracts and display candidate exist; `recorded != current`; resolver not yet implemented |
| Register | `MEMORY.md`, `EVIDENCE_MEMORY_CANONICALIZATION.md` and Register owner contracts | Register links, Evidence/Trace projections and future governed record projections | external storage may persist only through an authorized seam; Pantheon governs admission | durable retention, supersession and admission | doctrine and some declarative contracts exist; no automatic memory-promotion engine |
| Runtime | `WHAT_RUNS.md`, `PANTHEON_CONTROL_PLANE_BOUNDARY.md`, runtime-adapter owner documents | Runtime/Resource Cards and control-plane views | Hermes Agent or another separately approved external runtime | adoption, installation, activation, update, data use and rollback | external runtimes may be observed; installed/healthy/adopted/activated remain separate axes |
| Card | `CARD_STACK_MODEL.md`; machine-readable mapping specialized by `CARD_PROJECTION_DEFINITION_MODEL.md` | co-located Cockpit renderer plus static Card Stack prototypes | none by the Card itself | none by the Card itself; interactions may route to governed review/action seams | generic projection grammar documented; executable candidate Card renderer and projection definitions present; production adoption is not implied |
| Scene | `CARD_STACK_MODEL.md` | bounded filtered/ordered Card collection where useful; not a root-space list | none | scene composition must not hide required review information | generic composition term retained; no separate persisted Scene engine or competing Cockpit information architecture |

## Placement invariants

```text
Case != Task runtime
Source != Evidence
Evidence Candidate != accepted Evidence
Gate != Decision
Decision recorded != Decision current
Register != runtime memory
Runtime healthy != safe
Card != governed object
Scene != exhaustive graph
projection != ownership
```

## Candidate gaps not admitted by this map

The following terms remain design candidates or gaps rather than owned concepts:

| Candidate term | Current treatment | Admission condition |
|---|---|---|
| Lens | possible deterministic filtering/projection vocabulary | define non-duplication against Scene, Context Stack and existing views; human review required |
| Perspective | possible cognitive composition of several views | define actor/role boundary without creating automatic routing or authority inference |
| Cluster | purely visual grouping candidate | remain non-semantic and non-governance unless a separate owner is justified |
| Current View | future derived projection | depends on deterministic current Decision/Gate/status resolution; must not store invented state |

## Boundary

This matrix can reveal jurisdictional gaps. It cannot fill them by implication.
