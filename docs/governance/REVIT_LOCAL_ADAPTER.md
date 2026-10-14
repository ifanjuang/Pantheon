# Revit Local Adapter Boundary

Status: candidate support doctrine — canonical local-adapter boundary — documented non-implemented.
Boundary profile: candidate_support_note.

This document is the single authority for the placement of a future local Revit adapter in the Pantheon ecosystem. It specializes the generic Bridge, Task Contract, Context Pack, capability, workflow and runtime-return contracts without creating a second governance model.

It does not claim that an add-in, Host Agent, binding, workflow or model-writing capability is installed, healthy, activated, admitted or authorized.

```text
Pantheon Next governs contracts, scope, status, Evidence posture and human gates.
pantheon-mvp may implement persistence, APIs, projections and adapter seams.
Hermes may orchestrate one admitted task as an external runtime.
A local Host Agent may adapt transport and correlate bounded calls.
The Revit add-in alone executes Revit API calls inside Revit context.
Cockpit or OpenWebUI exposes context, preflight, proposals and results.
The human decides consequential mutations.
```

```text
installed != approved
healthy != safe
locally_enabled != task_authorized
available != admitted
preflight_passed != effect_authorized
transaction_success != accepted_result
runtime_success != Evidence
UI status != authorization
```

## Purpose

The adapter connects a live Revit document to governed Pantheon work without moving Revit execution into Pantheon. It may observe exact model context, prepare bounded candidates and, after a separate explicit authorization, execute a named local transaction through an external add-in.

Pantheon is not intended to reproduce a generic natural-language wrapper around the Revit API. The target is a project assistant for the architect, able to connect Revit observations and actions to program, plans, sections, CCTP, DPGF, IFC, photographs, site observations, decisions, Project Anatomy and specialist calculation results.

## Full-local invariant

The core path must remain usable without Internet access and without an Autodesk execution service.

```text
no Autodesk Assistant dependency
no Autodesk Public MCP dependency
no APS dependency
no Autodesk-hosted execution requirement
no cloud LLM requirement
no hidden remote fallback
no automatic upload of model or project data
```

A deployment may run on one workstation or on a private local network. The binding must report its actual connection posture:

```text
offline_local
private_lan
externally_connected
```

A connection-mode change is a visible technical observation. It does not silently broaden scope, permissions or data exposure.

Autodesk Assistant, Autodesk Public MCP and APS may remain reference material or optional future bindings. The Pantheon architecture and capability identity must not depend on them.

## Project Anatomy consumption boundary

The architecture-domain Project Anatomy doctrine owns the professional first-wave scope:

```text
architecture and spatial design
project economy and quantities
construction-site review and DET support
thermal-data preparation and RE2020 consistency
life-cycle assessment and carbon analysis
```

This Revit boundary does not redefine that métier scope. It defines only which bounded Revit observations and operations may support those viewpoints through one replaceable binding.

These are five viewpoints over the same project objects, not five parallel object models.

Example:

```text
one window
-> geometry and type in Revit
-> program requirement
-> CCTP article
-> DPGF quantity and price assumption
-> thermal characteristics
-> environmental-data association
-> site observation or reserve
-> decision and history
```

The first wave does not include detailed professional design or dimensioning of structural systems, HVAC networks, plumbing networks, electrical systems or fabrication systems. Those elements may be observed when they are necessary context for architecture, economy, site review, RE2020 or carbon analysis.

```text
technical element observed != technical system designed
thermal input prepared != regulatory calculation certified
environmental match proposed != environmental data validated
quantity extracted != price approved
site observation captured != non-conformity decided
```

## Responsibility split

### Pantheon Next

Pantheon Next owns:

```text
Capability Slots and binding boundaries
Task Contract and requested-effect vocabulary
Context Pack and scope requirements
approval ceilings and human-gate requirements
ChangeCandidate, Result Candidate and Evidence posture
status semantics and non-equivalences
adapter adoption, suspension and revocation doctrine
workflow and capability contracts
```

Pantheon Next does not call the Revit API, open a transaction, save, synchronize or mutate an RVT file.

### pantheon-mvp

A reviewed implementation may own:

```text
binding observations and capability projections
project-scoped Task Contract and Context Pack references
governed-execution handoff persistence
preflight, authorization and technical-result persistence
Cockpit APIs and projections
Execution Result and Result Candidate persistence
Project Anatomy read projections
human decisions and bounded one-time action authorizations
```

The server remains authoritative for persisted project state, task admission, authorization records and review state.

### Hermes

Hermes may:

```text
consume one admitted Task Contract and Context Pack
select an admitted workflow and available binding
use structured Revit métier knowledge
prepare an analysis, method or ChangeCandidate
request bounded typed adapter operations
return a Result Candidate and technical trace
```

Hermes must not infer broader scope, manufacture approval, invent an absent capability, execute arbitrary code in Revit, bypass the add-in, silently select an external provider or promote a result to Evidence.

Revit usage knowledge belongs in skills, workflows and tool metadata, including preconditions, compatible element classes, units, version limits, transaction requirements, failure modes and refusal conditions. It must not exist only in a prompt.

### Local Revit Host Agent

A local Host Agent may sit between Hermes and the add-in. It is a transport adapter, not a runtime or authority.

Allowed responsibilities:

```text
local authentication
connection and reconnection
Revit-instance discovery
protocol-version negotiation
manifest transport
request correlation
payload validation
redaction of local paths and secrets
transport timeout and refusal
```

Forbidden responsibilities:

```text
workflow state
business status
approval
Project Anatomy or model truth
memory
provider routing
scheduling or queues
autonomous retries
```

Transport may be MCP, stdio, loopback HTTP, gRPC or another bounded local interface. Transport is replaceable and is not part of capability identity.

### Revit add-in

The add-in owns:

```text
Revit and .NET compatibility
active-document and active-view observation
selection and ElementId resolution
freshness checks
ExternalEvent or equivalent Revit-thread execution
Transaction and TransactionGroup discipline
failure handling and rollback observation
changed-element journaling
visible local stop and disable controls
```

The add-in is the only component allowed to execute Revit API mutations.

Production code belongs in a dedicated implementation repository. The `revit-plugin/` directory here is a non-executable reference skeleton.

### Cockpit or OpenWebUI

The exposure surface may display:

```text
binding observations
local exposure profile
supported, enabled, available and admitted capabilities
Task Contract and exact scope
Context Pack and snapshot freshness
preflight warnings and blockers
method and ChangeCandidate previews
affected elements
human decision controls
technical result and rollback posture
Evidence candidates and provenance references
```

Cockpit does not communicate directly with Revit. A projection does not own truth or authorization.

### Human

A human decision remains required for binding adoption, project activation and every consequential mutation. Result acceptance, ChangeCandidate application, Evidence admission, save, synchronization, publication and transmission remain separate decisions.

## Component topology

```text
Cockpit / OpenWebUI
        |
        | governed API
        v
pantheon-mvp
        |
        | governed_execution_handoff
        v
Hermes
        |
        | bounded capability operation
        v
Local Revit Host Agent
        |
        | authenticated local IPC
        v
Revit add-in
        |
        | Revit API / ExternalEvent / Transaction
        v
live Revit document
```

The preferred add-in-to-Host-Agent channel is a Windows Named Pipe or equivalent authenticated same-machine IPC. No network listener is required inside Revit.

For a private LAN, the workstation should prefer an authenticated outbound connection to the admitted Hermes endpoint rather than an unauthenticated inbound port.

## Existing contract reuse

| Need | Existing owner |
|---|---|
| declare the abstract function | Capability Slot and binding records |
| classify one operation | Capability Passport or its generalized successor |
| declare the adapter module | Module Manifest |
| declare a repeatable method | Workflow Manifest |
| bound one request | Task Contract |
| carry admitted project context | Context Pack and source references |
| transport an admitted execution request | governed_execution_handoff |
| report runtime separation | runtime_return |
| represent project understanding | APU adapter contract and Result Candidate |
| propose a consequential change | ChangeCandidate |
| capture unresolved attention | DecisionRequest |
| record a human determination | decision record |
| report a missing prerequisite | Capability Gap or typed blocker |
| expose work | WorkIssue and Cockpit projections |

Adapter-specific names such as `Revit Context Snapshot`, `Preflight Report` and `Action Report` are typed technical envelopes inside this existing grammar. They are not new project authorities.

## Capability identity and binding operations

Capability identity should describe an abstract building-model function, not the implementation product.

Examples:

```text
building_model.observe.document
building_model.observe.selection
building_model.observe.spaces
building_model.observe.elements
building_model.observe.quantities
building_model.navigate.highlight
building_model.review.create_view
building_model.write.set_parameter
building_model.write.change_type
```

The Revit binding maps these to versioned technical operations:

```text
revit.document.snapshot.v1
revit.rooms.snapshot.v1
revit.elements.query.v1
revit.quantities.extract.v1
revit.navigation.highlight.v1
revit.element.set_parameter.v1
revit.element.change_type.v1
```

```text
Capability Slot != Revit command
capability identity != transport name
ElementId != stable_object_id
```

A manifest must be generated from a closed registry, versioned and accompanied by a digest. Reflection-based exposure of arbitrary Revit API methods, arbitrary C# execution and arbitrary Python execution are refused.

## Local exposure menu

The Revit panel may let the user enable or disable capability families and detailed operations.

Recommended simple profiles:

```text
Observation
Analysis and navigation
Review
Controlled modifications
```

Sensitive write families should be disabled by default and may be session- or project-scoped.

The menu defines the maximum local exposure accepted by the user. It does not grant Pantheon task authorization.

For each capability, the system distinguishes:

```text
supported       implemented by this binding version
locally_enabled accepted for local exposure
available       usable in the current Revit context
admitted        accepted by Pantheon for the binding and scope
authorized      allowed for the exact consequential action
executed        technically attempted or performed
accepted        result reviewed under its owning authority
```

The effective capability is the intersection of support, local exposure, current availability, binding admission, Task Contract scope and any required action authorization.

## Effect classes

| Adapter-local class | Meaning | Default posture |
|---|---|---|
| `read_only` | observe document, view, selection, elements, warnings or parameters | admitted scope required |
| `candidate_only` | highlight, preview, analyze or prepare a candidate | no Revit mutation |
| `write_light` | create a bounded review artifact or approved review parameter | fresh preflight, human authorization and named transaction |
| `write_model` | create or modify architectural model elements | blocked until dedicated proof of scope, rollback and review |
| `external_effect` | save, sync, publish, transmit, install, execute arbitrary code or alter shared state | refused unless a later exact contract explicitly opens it |

## First-wave capability families

The initial registry should remain small and workflow-driven. These capability families are Revit-binding slices of the architecture-domain scope above; they do not redefine Project Anatomy or professional authority.

Observation and context:

```text
document, view, selection, levels, phases, design options
architectural categories, elements, parameters, types and materials
rooms, boundaries, adjacency and door connections
walls, floors, roofs, ceilings, doors and windows
views, sheets, schedules and warnings
```

Architecture and Project Anatomy inputs:

```text
spatial hierarchy and relations
bounded geometry summaries
cross-source locators and source references
stable-object mapping candidates
phase and variant observations
```

Economy:

```text
counts, lengths, areas and volumes
material and layer quantities
differences between bounded snapshots
classification and lot parameters when present
```

Site review:

```text
selected-object and zone references
view captures and locators
highlight, isolate and zoom
comparison support for planned, modeled and observed states
```

RE2020 and carbon preparation:

```text
envelope geometry and orientation
spaces, heated-status observations and volumes
openings, glazing and shading observations
materials and compound structures
quantities and identifiers needed by separate local calculation adapters
```

A specialist regulatory or ACV engine remains a separate binding. Hermes reasoning does not replace a regulatory calculation.

## Governed workflows

Workflows belong to Hermes and are declared through existing Workflow Manifests. The add-in provides bounded deterministic operations only.

Examples include:

```text
compare program and rooms
compare PDF, CCTP, IFC and Revit
compare two model snapshots
prepare quantities and candidate cost impact
attach a site observation to a stable object
verify a reserve against a later model state
prepare and check RE2020 inputs
prepare ACV quantities and environmental-data candidates
```

A deterministic adapter operation may group several internal Revit calls when they form one bounded observation. It must not perform cross-source reasoning or decide which project or model mutation should occur.

## Read execution sequence

```text
1. The binding publishes a current manifest and document observation.
2. pantheon-mvp records or refreshes the binding observation.
3. A Task Contract and Context Pack define exact admitted scope.
4. Pantheon records the policy posture and governed handoff.
5. Hermes selects an admitted workflow and capability.
6. The Host Agent validates and transports one typed operation request.
7. The add-in executes the observation in Revit context.
8. The add-in returns a technical result with provenance and freshness.
9. Hermes produces a Result Candidate and any required Evidence Pack Candidate.
10. pantheon-mvp persists and projects the reviewable result.
```

## Consequential-write sequence

```text
1. A workflow produces a ChangeCandidate.
2. The add-in performs a fresh technical preflight.
3. Cockpit exposes exact targets, predicted effects, warnings and blockers.
4. A human decides the exact proposed effect.
5. pantheon-mvp issues a bounded, expiring, single-use authorization.
6. The add-in repeats freshness, digest and target checks.
7. The add-in executes one named local transaction or refuses.
8. The add-in returns changed-element observations, failures and rollback posture.
9. Hermes returns a Result Candidate and Trace.
10. Result acceptance, APU update, Evidence admission, save and sync remain separate.
```

A stale document, view, selection, target set, phase, design option, workset, host, family or type invalidates the request.

## Freshness, correlation and idempotency

Every significant adapter object should carry the existing trace spine plus, where applicable:

```text
project_ref
task_contract_ref
context_pack_ref
handoff_ref
runtime_run_ref
binding_id
document_ref
snapshot_id
request_id
action_id
idempotency_key
authorization_ref
result_ref
```

A write authorization must bind to the request digest, preflight digest, binding, document identity, freshness token, exact operation, exact bounded target set, maximum effect, expiry and single-use state.

The add-in refuses execution when the authorization or idempotency posture no longer matches.

## Preflight minimum

Before a write, the add-in returns at least:

```text
document identity and binding version
active view and view type
exact target references
selection or work-area source
phase and design-option context
worksharing, workset and ownership observations
linked-model involvement
pinned, grouped, constrained and hosted-element observations
family and type availability
requested effect and authorization reference
transaction-name candidate
predicted created, modified and deleted categories
rollback or manual-reversal posture
freshness token
forbidden-effect findings
```

A passed preflight is a technical observation, never authorization.

## Transaction discipline

Every committed mutation executes inside Revit context with a deterministic name:

```text
PantheonRevit:<task_id>:<action_id>:<short_effect>
```

The add-in journals binding and Revit versions, document reference, Task Contract, authorization, transaction name, timestamps, created/modified/deleted ElementIds where available, before/after digests where available, warnings, failures and rollback posture.

The add-in must not silently save or synchronize after a successful transaction.

One batch intention should normally map to one atomic transaction or explicit TransactionGroup, not one unrelated transaction per element.

## Typed refusal

Recommended refusal families:

```text
refused_binding_not_admitted
refused_capability_disabled
refused_capability_unavailable
refused_document_mismatch
refused_stale_document
refused_stale_view
refused_stale_selection
refused_target_missing
refused_scope_violation
refused_precondition_failed
refused_worksharing_conflict
refused_linked_model_write
refused_authorization_missing
refused_authorization_expired
refused_authorization_mismatch
refused_idempotency_conflict
refused_forbidden_effect
refused_revit_failure
```

These are technical observations, not a second business task-state machine. WorkIssue, run events, Result Candidate, DecisionRequest and Capability Gap carry project-facing state.

## Project Anatomy relationship

Revit is a source representation and execution surface. Project Anatomy is a server-calculated projection of project understanding.

Observation path:

```text
Revit Context Snapshot
-> Execution Result
-> object, mapping or attribute candidates
-> human review
-> authorized APU operation
-> project-scoped APU state
-> Project Anatomy projection
```

Model-write path:

```text
ChangeCandidate
-> Revit preflight
-> human authorization
-> Revit transaction
-> Action Report
-> result review
```

```text
APU mapping applied != Revit model modified
Revit model modified != APU mapping accepted
snapshot != Project Anatomy
```

Removing or replacing the Revit binding must not destroy Project Anatomy or cross-source project identity.

## Source and Evidence posture

A Revit observation preserves document identity, binding/Revit version, view/selection/element references, observation time, method, parameters, units, warnings and freshness.

```text
observed != validated
absence_of_warning != safe
transaction_success != professional_validation
action_report != Evidence
screenshot != proof
Result Candidate != accepted result
Evidence Pack Candidate != Evidence admitted
```

## Security and minimization

```text
hash or redact local filesystem paths
never transport credentials in a Context Pack
declare whether geometry leaves the workstation
limit snapshots to admitted scope
avoid full-model export when a bounded query is sufficient
do not expose arbitrary API reflection or code execution
do not open unauthenticated LAN listeners
```

## Adoption gates

Before adoption or activation, verify together:

```text
implementation repository and owner
exact Revit and .NET compatibility
reviewed package identity and installer rollback
no silent startup mutation
visible local stop and disable control
closed capability registry and manifest digest
Task Contract and Context Pack correlation
fresh preflight and named transactions
changed-element trace
out-of-scope and stale-operation refusal
human gate before consequential effects
sandbox and production separation
sensitive-path redaction
one read-only acceptance proof
one stale-context refusal proof
one rollback or manual-reversal proof before write adoption
```

## Supporting documents

The following remain subordinate implementation notes, not parallel authorities:

```text
revit-plugin/README.md
ARCHITECTURE.md under the revit-plugin documentation directory
EXECUTION_MODEL.md under the revit-plugin documentation directory
CONTEXT_PACK_CONTRACT.md under the revit-plugin documentation directory
ACTION_LOG_CONTRACT.md under the revit-plugin documentation directory
PANTHEON_REVIT_GATE.md
PANTHEON_REVIT_LOCAL_SANDBOX_EXCEPTION.md
PANTHEON_REVIT_FIRST_SANDBOX_ACTION_CONTRACT.md
PANTHEON_REVIT_GATE_2027_PROTOTYPE_PLAN.md
PANTHEON_REVIT_GATE_DEVELOPER_DOSSIER.md
```

Where a supporting document conflicts with this boundary or a later canonical schema or registry, the canonical owner prevails.

## Planning boundary

This document records target architecture, ownership, interfaces and refusal rules. It does not define implementation tranche order, dates, milestones, staffing, release scope or migration sequence. Those belong to a later planning pass after contract review.

## Final rule

```text
Pantheon governs.
pantheon-mvp persists authority and review state.
Hermes composes admitted métier workflows.
The Host Agent adapts transport only.
The Revit add-in executes locally.
Cockpit exposes the decision surface.
The human decides consequential effects.
Technical success remains technical evidence only.
```
