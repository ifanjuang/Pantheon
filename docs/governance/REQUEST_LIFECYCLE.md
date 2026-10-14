# Request Lifecycle

Status: active support doctrine — the governed lifecycle of a request, from situated comprehension to human engagement — implemented as documentation.
Boundary profile: active_support_doctrine.

This document defines the moments a request passes through, how its goal (the cap) is clarified and kept stable, how governance depth adapts to consequence, how a Case / Situation is clarified before workflow forging, how material changes are re-evaluated, and how memory/retention boundaries remain visible.

It connects the Governance College, Task Contracts, context/source owners, memory owners, rites and the autonomy doctrine into one lifecycle without creating another Role, router or workflow engine.

Runtime/client boundary: see `HERMES_INTEGRATION.md`. This document owns lifecycle choreography, proportional request activation and the documentary Case / Situation intake brief only; execution remains external and consequential memory, Evidence, approval and engagement gates remain separately governed.

## Core thesis

A request is not just executed. First its real demand is understood, a heading (the cap) is made explicit, the professional situation is clarified enough for the next method boundary, only the governance owners required by consequence are activated, external execution happens inside the admitted boundary, returned candidates are reviewed, and the human engages where consequence requires authority.

```text
Understand the cap.
Hold the cap as an explicit task property.
Clarify the situation.
Activate only what consequence requires.
Execute outside Pantheon.
Review the returned candidates.
Arbitrate status when necessary.
The human engages where required.
```

The cap is the goal. The path is the method. Pantheon governs the cap and its changes; it does not prescribe Hermes internal execution mechanics.

## The lifecycle

```text
request
  -> triage: clear enough to proceed?
       yes -> light handling inside the allowed autonomy envelope
       no  -> situated clarification using existing Role viewpoints
  -> clarify the minimum Case / Situation brief when the request must become an Approach or Workflow Candidate
  -> make the cap explicit in the Task Contract / governed request
  -> activate only the context/source/risk/memory/evidence owners required by consequence
  -> pre-execution admission / policy check when the effect requires it
  -> Hermes or another admitted external runtime executes inside the bounded contract
  -> Result Candidate + Evidence Pack Candidate + observations return
  -> applicable Role viewpoints review the result
  -> ZEUS arbitrates status/procedure when conflict, material ambiguity or competing paths remain
  -> the human decides at consequential cliffs
  -> any durable retention follows MEMORY.md / Register owners and applicable human approval
```

A material change of cap routes back to a governed Task Contract revision. It is never a silent runtime pivot.

## Situated clarification is a function, not a Role

Pantheon already has a canonical Role registry in `AGENTS.md`. Request clarification therefore composes existing viewpoints instead of introducing a new permanent Role.

Typical composition:

```text
IRIS       -> clarify wording, audience and requested effect
ATHENA     -> structure the goal, phases and method boundary
ARGOS      -> expose missing sources, provenance and freshness needs
MNEMOSYNE  -> expose relevant prior state, version or supersession questions
THEMIS     -> expose risk, responsibility and approval boundaries
ZEUS       -> arbitrate status/procedure when material ambiguity remains
```

Not every request needs this set. A clear low-consequence request may require none of these viewpoints explicitly.

```text
clarification function != new canonical Role
Role viewpoint != executable agent
Role activation != task authorization
```

## Proportional activation

The lifecycle is always the governing frame, but every request does not need every governance owner.

Use the smallest owner set that matches the request and its possible consequence:

```text
simple, clear, low-consequence request -> light handling inside the autonomy envelope
unclear cap or multi-intent request      -> IRIS / ATHENA clarification; ZEUS only if arbitration is needed
context dependency or missing context    -> CONTEXT_STACK.md
source dependency or freshness gap       -> SOURCE_NEED_AND_REGISTRY.md / ARGOS
prior-state or version continuity         -> MNEMOSYNE + applicable source owner
liability or external effect             -> THEMIS + policy / approval / human gate as applicable
memory or durable-retention effect        -> MEMORY.md + MNEMOSYNE framing + applicable Register/approval gates
candidate output                          -> Evidence and approval posture appropriate to intended use
```

Proportional activation must not become a hidden router or workflow engine. It is a method rule for deciding which existing owners are relevant.

### Information acquisition route

When required information is available, use the least indirect admitted route that preserves source identity, scope and provenance:

```text
known exact source                                      -> direct source/context access
unknown location inside an admitted documentary corpus -> search / retrieval
current structured or operational state                 -> typed query against its existing operational owner
past conversational or workstream context                -> runtime memory
missing external or project source                       -> Source Need Candidate -> permitted source route
```

This classifies acquisition, not authority. It creates no Pantheon router and does not change source, Evidence or approval rules. Hermes or another admitted external runtime may choose and compose capabilities inside the Task Contract; consequential use remains governed separately.

### Request decomposition

When the request needs more than light handling, separate the candidates before composing them:

```text
Request Candidate           -> what the user asked, as received
Cap Candidate               -> the situated aim proposed from the request
Expected Context Profile    -> context expected to safely proceed
Input Admission Candidate   -> what was supplied, retrieved, recalled or is absent
Source Need Candidate       -> what source is missing and why it matters
Output Intent Candidate     -> what kind of output is expected and under what status
Situated Approach Candidate -> what method motifs are composed for this situation
Result Candidate            -> output produced by a role, runtime or adapter
Evidence Pack Candidate     -> review material supporting or contradicting assertions
Gate / Decision             -> accepted, refused, to_verify, to_arbitrate or blocked
```

These are governance objects or documentary candidates. They do not execute.

Their detailed contracts remain with their existing owners.

### Input is not output

Pantheon keeps available input separate from intended output:

```text
Input describes what is available.
Output describes what is requested.
The governed approach constrains the transformation.
```

Input availability never authorizes final output by itself. The same corpus may support an internal orientation but remain insufficient for a source-backed claim, external transmission, durable memory or another consequential effect.

### Complexity drivers

Governance depth increases when a material driver increases, including:

```text
cap ambiguity
multi-intent request
project-specific fact
context or source dependency
evidence dependency
freshness dependency
contradiction
regulatory or contractual effect
professional responsibility
external visibility or action
memory or register effect
sensitive input
```

### Owned context, source and memory seams

This lifecycle activates, but does not redefine, the specialist owners:

- `CONTEXT_STACK.md` owns context composition, sufficiency states, Context Stack Change Candidates and the candidate HESTIA boundary;
- `SOURCE_NEED_AND_REGISTRY.md` owns Source Need Candidate structure, source families, source routes, registry semantics and freshness policy;
- `AGENTS.md` owns canonical Role identity;
- `MEMORY.md` owns the boundary between runtime memory and governed durable retention;
- Evidence, approval and Register promotion remain with their respective owners.

```text
missing context -> consult context sufficiency -> narrow, request context or escalate
missing source  -> Source Need Candidate -> permitted retrieval handoff -> source/Evidence review
prior state     -> MNEMOSYNE frames where/how to look -> runtime performs admitted retrieval -> source review as needed
retention       -> Register Candidate / applicable memory path -> review / approval -> durable effect only if admitted
```

Retrieved or recalled material remains candidate until the applicable source, Evidence and approval owners qualify the consequential use.

### Output consequence and safe defaults

Output intent determines how much governance is needed. Typical output families include orientation, internal draft, extraction candidate, source-backed claim, document/comparison candidate, pre-transmission candidate, external-action preparation, memory candidate and register candidate.

When cap, context, source status or output consequence is unclear, prefer:

```text
allow orientation only
allow draft only
mark missing source or context
surface assumptions
request source or context
block external action
block memory promotion
send to ZEUS or a human gate when required
```

## Case / Situation intake brief

When a request must cross from situated comprehension into Approach selection or Workflow Candidate forging, create a short documentary intake brief first.

`Case / Affaire` is the governed professional unit. `Situation` is the concrete question or tension. `Corpus` is a document set. A filesystem folder or colloquial dossier is not the governed Case identity.

The legacy identifier `dossier_situation_brief` and field name `dossier_situation_brief_ref` are retained as compatibility vocabulary for existing documentary examples and Workflow Candidate shapes. New explanatory text should read them as **Case / Situation brief**.

### Intake is a function, not a Role

The brief composes existing viewpoints; it creates no new canonical Role:

| Viewpoint | Intake contribution |
|---|---|
| IRIS | clarify wording, intended audience and requested effect |
| ATHENA | structure the Situation and identify an Approach / Workflow Candidate family |
| ARGOS | identify required sources, versions, provenance and Evidence gaps |
| MNEMOSYNE | identify relevant prior state, supersession/version questions and possible retention impact |
| THEMIS | identify risk, liability, approval and external-effect boundaries |
| APOLLO | check completeness and delivery readiness of the brief |
| ZEUS | arbitrate status and next procedure when ambiguity or conflict remains |
| HEPHAISTOS | forge a later artifact or Workflow Candidate; not intake authority |

### Minimum documentary shape

```text
dossier_situation_brief:   # compatibility identifier; means Case / Situation brief
  request:
    raw_user_request:
    clarified_request:
    requested_output:
    requested_effect:
  project_identity:
    official_name:
    aliases:
    address:
    commune:
    parcel_refs:
    project_type:
  phase:
    user_says:
    contract_phase:
    operational_phase:
    contradiction:
  geography_and_rules:
    jurisdiction:
    PLU_zone:
    ABF_or_heritage:
    ERP_context:
    known_constraints:
  sources:
    received_now:
    required:
    available:
    missing:
    superseded_or_uncertain:
  versions:
    latest_plan_known:
    latest_notice_known:
    incoming_document_index:
    version_conflicts:
  contract_scope:
    mission_reference:
    in_scope:
    out_of_scope:
    unclear:
  relation_context:
    client_tension:
    authority_or_ABF_tension:
    contractor_tension:
    insurer_or_claim_context:
  risk_triggers:
    safety:
    cost:
    schedule:
    external_commitment:
    professional_liability:
  memory_and_register:
    runtime_memory_relevant:
    registre_entries_required:
    contradictions:
  blocking_questions:
  non_blocking_questions:
  recommended_next_status:
```

This is documentary vocabulary, not an executable schema. Any future schema belongs under `schemas/` and requires its own protected-path review.

### Intake statuses

| Status | Meaning |
|---|---|
| `ready_for_workflow_candidate` | enough information exists to forge a Workflow Candidate |
| `pending_clarification` | user wording or project target is ambiguous |
| `pending_source` | a required source, version or proof element is missing |
| `pending_contract_scope` | the mission boundary is unclear |
| `risk_review_required` | risk or tension requires THEMIS review before work continues |
| `zeus_arbitration_required` | conflicting candidate paths or statuses require arbitration |
| `blocked` | continuing would create false truth, unauthorized effect, wrong memory or another illegitimate consequence |

The brief remains candidate material. It does not answer the substantive question as final, send or publish, validate a professional position, mutate the Registre Probatoire, promote runtime memory or authorize a durable workflow.

Worked example: `../examples/architecture_erp_effectif_impact_workflow/` shows the richer ERP/effectif impact case without duplicating it here.

## The cap and its re-evaluation

The cap lives in the Task Contract (`TASK_CONTRACTS.md`) as its intent.

The lifecycle holds the cap as an explicit governed property; no extra canonical Role is required to own that noun.

Existing Roles contribute according to the question:

```text
IRIS / ATHENA -> clarify and structure the proposed cap
ARGOS         -> challenge source-dependent assumptions
MNEMOSYNE     -> challenge stale or superseded prior context
THEMIS        -> challenge responsibility / consequence boundaries
ZEUS          -> arbitrate status/procedure when material disagreement remains
human         -> decide a consequential change of destination or commitment
```

When incoming information changes the picture:

```text
minor clarification inside existing intent/scope -> record it and continue within the existing contract
material change of goal, scope, responsibility or destination -> governed Task Contract revision
consequential destination change -> applicable human decision gate
```

A material change of cap is a Task Contract revision (`TASK_CONTRACT_REVISIONS.md`), not a silent pivot.

## ZEUS arbitrates status and procedure

ZEUS is used when the next legitimate procedure is itself unclear: unresolved conflict, competing variants, material framing disagreement or a status transition that cannot be decided from the existing owners alone.

Typical outcomes:

```text
sufficient -> proceed
needs_clarification -> return to the applicable clarification/source/context owner
needs_evidence -> request the missing support
needs_human_decision -> expose the decision gate
blocked -> stop the consequential path
```

The loop is bounded. Repeating arbitration does not manufacture certainty; unresolved ambiguity eventually belongs to the human or remains explicitly unresolved.

ZEUS does not decide truth by himself and does not replace the Role or owner that has the substantive responsibility.

## Memory and retention threshold

Memory continuity is governed without creating separate gate personas.

`MNEMOSYNE` owns the continuity viewpoint: where to search, which prior state/version may matter, what may be stale or superseded, and where retention might belong. Hermes or another admitted runtime performs the actual retrieval. `MEMORY.md`, scope owners, Register contracts and approval owners govern whether anything may durably remain.

```text
runtime recall -> candidate context, not truth
stale recall -> mark / reconfirm before consequential reuse
out-of-scope recall -> do not silently admit
superseded material -> keep historical provenance but do not treat as current state
retention proposal -> Register Candidate or applicable memory candidate
promotion -> only through the existing governed review/approval path
```

Archive behavior belongs to the applicable record/document/memory owner. Superseded material is not hard-deleted merely because a newer state exists.

```text
MNEMOSYNE viewpoint != retrieval execution
retrieved memory != Evidence
retention placement proposal != persistence authorization
archive != deletion
```

## The consequential chokepoint

When the lifecycle reaches a consequential effect, the applicable external runtime / PEP must obtain the required Pantheon policy decision before performing that effect. The bounded PDP/PEP relationship is owned by `HERMES_INTEGRATION.md` and `UNIFORM_CAPABILITY_GOVERNANCE.md`.

```text
non-consequential effect -> runtime may proceed inside the admitted Task Contract
governed consequential effect -> required policy / gate check -> external runtime performs only if admitted
```

The lifecycle helps make consequence visible. It does not replace the placement, policy, Evidence or approval owners and it does not execute the effect.

## Boundary

`active_support_doctrine` boundary profile applies.

This document does not create a new canonical Role, new memory gate identity, runtime router, workflow engine, approval engine, memory engine or persistence owner.

```text
The lifecycle clarifies and holds the cap as a governed task property.
Existing Pantheon Roles provide only the viewpoints that matter.
The Case / Situation brief stays documentary and candidate.
Hermes or another admitted runtime executes outside Pantheon.
MNEMOSYNE frames continuity; existing memory/Register owners govern durable retention.
ZEUS arbitrates status/procedure when necessary.
The human decides consequential effects.
```
