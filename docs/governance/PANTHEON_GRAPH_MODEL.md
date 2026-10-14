# Pantheon Graph Model

Status: candidate support doctrine — documented non-implemented.

Date: 2026-07-11

This document defines a candidate graph grammar for relating Pantheon governance objects. It does not create a graph database, graph runtime, workflow engine, scheduler, queue, router, approval engine, memory engine, installer, updater, OpenWebUI component, Hermes skill, MCP host or external action.

```text
exposed_by  -> exposure surface, including future cockpit projections
executed_by -> Hermes Agent or another external runtime under contract
governed_by -> Pantheon status, evidence, scope, approval and relation rules
approved_by -> human authority where a consequential relation or action is adopted
forbidden   -> inferred execution, automatic adoption, automatic approval or automatic memory promotion
```

## 1. Purpose

Pantheon already declares capabilities, resources, evidence, decisions, context, actions and governance boundaries. The missing question is not only which objects exist, but why one object may legitimately depend on, support, constrain or authorize another.

This model treats those links as governed records.

```text
The node identifies.
The relation qualifies.
The evidence supports.
The decision authorizes or refuses.
The external runtime executes.
```

The model is a governance graph, not an execution graph.

## 2. Placement in the existing model

This document does not replace:

- `COMPETENCE_MODEL.md`, which distinguishes professional competence from runtime skills and tools;
- `CAPABILITY_REGISTRY.md`, which declares abstract capabilities and their dependencies;
- `CONTEXT_STACK.md`, which frames dynamic context projections;
- `CARD_STACK_MODEL.md`, which defines cockpit-facing card projections;
- `EVIDENCE_PACK.md`, `APPROVALS.md` and related canonical doctrine;
- runtime adapters, schemas or implementation artifacts.

It supplies a common relation grammar between those areas.

## 3. Candidate node classes

The graph may reference the following governance objects where they already exist in doctrine or candidate models:

| Node class | Question answered | Boundary |
|---|---|---|
| Intent | Why is the work being considered? | An intent does not authorize execution. |
| Context | Under which situated conditions is it considered? | Context is not truth, proof or approval. |
| Competence | Which professional ability or method is relevant? | A competence is not an executable skill. |
| Capability | What abstract function is required? | A capability declaration is not authorization. |
| Binding | Which candidate implementation arrangement may cover the capability? | Selection is not adoption or activation. |
| Resource | Which concrete component, repository, skill, model, connector, runtime, template or policy is referenced? | Presence or installation is not approval. |
| Policy | Which governance rule constrains the relation or decision? | A policy does not execute or self-enforce. |
| Evidence | What reviewable support bears on a claim, relation or decision? | Runtime success is not sufficient evidence. |
| Decision | Which human-governed arbitration accepts, limits, suspends or refuses something? | A decision record does not execute an action. |
| Action | Which concrete operation is proposed or reported? | Execution remains external. |
| Trace reference | Where may reviewable activity be inspected? | A trace is not proof, canon or hidden reasoning. |

These classes are not a requirement to create one storage table, API type or cockpit card per class.

## 4. Relations are governed records

A relation is not an informal pointer. It is a scoped assertion that one node bears a defined relation to another.

Candidate minimal shape:

```yaml
relation_id: rel.example.001
relation_type: covers
source_ref: binding.ui.capture.v1
target_ref: capability.ui.full_page_capture
scope_ref: project.example
status: candidate
valid_from: 2026-07-11
valid_until: null
policy_refs:
  - policy.minimum_permissions
evidence_refs:
  - evidence.review.001
decision_ref: null
provenance:
  source: human_review
  recorded_at: 2026-07-11T00:00:00+02:00
```

A relation record may remain candidate. It becomes adopted, active, suspended, superseded or refused only through the applicable governance path.

## 5. Controlled relation types

### 5.1 Intent and context

```text
Intent      --situated_by--> Context
Intent      --requires-----> Capability
Intent      --bounded_by---> Policy
Context     --scoped_to----> Case / dossier / project
Context     --supported_by-> Source or trace reference
```

Rules:

- `situated_by` does not make context authoritative;
- `requires` expresses a governance need, not a runtime call;
- context changes must not silently broaden scope;
- an intent remains human-originated or explicitly adopted, never inferred as authorization from runtime activity.

### 5.2 Competence and capability

```text
Competence --supported_by--> Guide / resource / template
Competence --requires------> Capability
Capability --depends_on----> Capability
Capability --constrained_by> Policy
```

Rules:

- a competence may require several capabilities;
- a capability may support several competences;
- `depends_on` is structural dependency, not execution order;
- cyclic dependencies are not automatically invalid, but must be surfaced for review;
- a capability remains implementation-independent.

### 5.3 Capability and binding

```text
Binding --covers----------> Capability
Binding --alternative_to--> Binding
Binding --supersedes------> Binding
Binding --constrained_by--> Policy
Binding --supported_by----> Evidence
Binding --subject_to------> Decision
```

The `covers` relation is central. It records the claim that a particular binding can cover an abstract capability under a defined scope.

Required distinctions:

```text
covers_candidate != covers_approved
binding_selected != dependency_adopted
binding_tested   != binding_safe
binding_active   != capability_universally_available
```

A binding may cover a capability only for a specified task family, dossier, domain, environment or approval ceiling.

### 5.4 Binding and resource

```text
Binding --requires-------> Resource
Binding --optionally_uses> Resource
Binding --executed_by----> Runtime resource
Binding --exposed_by-----> Exposure resource
Binding --observed_by----> Observability resource
Binding --stores_in------> External data or memory resource
```

Each resource relation should state, where relevant:

```yaml
role: required | optional | fallback | observer
permission_scope:
  filesystem: read_scoped
  network: declared_domains_only
  external_write: forbidden
adoption_status: proposed
installation_status: not_installed
activation_status: inactive
```

Resource status remains independent from binding status.

```text
installed resource != approved binding
healthy resource   != safe relation
updated resource   != authorized adoption
```

### 5.5 Evidence, policy and decision

```text
Evidence --supports------> Relation or assertion
Evidence --contradicts---> Relation or assertion
Policy   --constrains----> Relation, binding, resource or action
Decision --applies_to----> Relation, binding, resource, capability or action candidate
Decision --cites---------> Evidence
Decision --applies-------> Policy
Human    --authors-------> Decision
```

Rules:

- evidence may support or contradict without deciding;
- a decision must not invent policy silently;
- the decision record must identify author, date, scope, rationale and cited support;
- a successful runtime event may become a trace reference or test observation, but not automatically sufficient evidence;
- no role, including Zeus, creates truth by status assignment.

### 5.6 Action and execution

```text
Action candidate --implements_intent_for--> Intent
Action candidate --uses_binding----------> Binding
Action candidate --requires_decision------> Decision gate
Runtime report   --reports_on-------------> Action candidate
Evidence         --supports---------------> Runtime report or output claim
```

Rules:

- Pantheon may frame, gate, record and expose an action candidate;
- Hermes or another external runtime performs the operation;
- a decision does not automatically dispatch the action;
- an action report does not automatically validate the result;
- consequential external effects require the applicable human approval.

## 6. Relation status lifecycle

Relations have their own lifecycle, independent from node lifecycles.

```text
observed
→ candidate
→ qualified
→ approved
→ active
→ suspended
→ superseded
→ retired

or

candidate
→ refused
```

Interpretation:

| Relation status | Meaning |
|---|---|
| observed | A possible relation was found; it has not been framed as a governance candidate. |
| candidate | The relation is explicitly proposed and visible for review. |
| qualified | Scope, source, permissions, limitations and evidence expectations have been reviewed. |
| approved | A human decision accepts the relation within a stated scope and ceiling. |
| active | The approved relation is currently selected for governed use. |
| suspended | Use is temporarily blocked without deleting history. |
| superseded | A replacement relation is preferred; the prior record remains traceable. |
| retired | The relation is no longer available for new use. |
| refused | The relation was reviewed and rejected or declared inadmissible. |

Approval and activation remain distinct.

## 7. Cardinality and scope rules

Candidate cardinalities:

```text
one Intent      -> zero or many Capabilities
one Capability  -> zero or many Bindings
one Binding     -> one or many Resources
one Resource    -> zero or many Bindings
one Relation    -> zero or many Evidence references
one Decision    -> one or many governed targets
one governed target -> zero or many historical Decisions
```

Every consequential relation should carry a scope reference or an explicit global-scope justification.

Default:

```text
project-scoped before organization-scoped
organization-scoped before global
minimum permissions before broad permissions
pinned source before floating source
reversible adoption before irreversible adoption
```

## 8. Invariants

### G-1 — Node identity does not confer authority

A node may exist without being approved, adopted, installed, healthy or active.

### G-2 — Relations do not execute

No graph relation is a runtime edge, command dispatch, queue transition or workflow step unless an external implementation separately interprets it under contract.

### G-3 — Consequential relations require explicit status

A relation that may affect truth, memory, approval, scope, external action, installation, activation, update or rollback cannot remain an untyped implicit link.

### G-4 — Scope cannot broaden transitively by default

If A is permitted in scope X and A depends on B, B does not automatically inherit broader permissions or scopes.

### G-5 — Evidence attaches to the claim being reviewed

Evidence supporting a resource's health does not automatically support the safety of the binding, the truth of an output or the legitimacy of an external action.

### G-6 — Decisions are attributable and bounded

Every approval, refusal, suspension or supersession must identify its human author or authorized human authority, scope, date and rationale.

### G-7 — Historical relations remain traceable

Superseded, suspended, retired and refused relations are not silently deleted when they bear on prior decisions or evidence.

### G-8 — Tool releases are relation review events by default

A new runtime, model, skill or connector version normally triggers review of the relevant binding-resource relation. It changes kernel doctrine only when the existing relation grammar cannot classify the new consequence.

### G-9 — Cards are projections

A cockpit card is a view over nodes, relations, evidence and decisions. It is not the authoritative graph record and does not gain execution authority through interaction design.

### G-10 — Human approval is not inferred

No runtime success, test pass, healthy status, popularity, installation, recommendation, prior selection or watchlist entry implies current human approval.

## 9. Roles and relation viewpoints

Pantheon roles remain governance viewpoints, not autonomous graph actors.

A role may:

- inspect a relation from its doctrine-defined viewpoint;
- request missing evidence;
- expose a tension or scope conflict;
- propose a candidate status change;
- route a consequential relation to a human gate.

A role must not:

- own a node as private authority;
- mutate graph status autonomously;
- execute a binding;
- convert runtime telemetry into proof by itself;
- approve its own proposal;
- promote memory automatically.

Role names should not be embedded as mandatory storage ownership. The durable record is the relation, evidence and human decision, not a mythological persona.

## 10. Cockpit and constellation projections

OpenWebUI or another exposure surface may project the graph as:

- a Capability Card showing candidate and approved bindings;
- a Binding detail showing resources, permissions, evidence and decisions;
- a Resource Card showing all bindings that depend on it;
- an Evidence view showing which claims and decisions it supports;
- a Decision surface showing the precise relation under review;
- a constellation showing a bounded subgraph for one project, intent, capability or runtime.

The projection should favor human decisions over ontology exposure.

```text
Internal model: rich typed graph.
Visible surface: bounded question, relevant evidence, explicit decision.
```

No swipe, tap, long press, constellation or other UI gesture may itself bypass the applicable approval semantics.

## 11. Capability Slot projection

For an external repository, skill, connector, workflow or runtime, the graph should support this bounded path:

```text
abstract capability
→ candidate binding
→ required and optional resources
→ installation status
→ health observations
→ update observations
→ activation status
→ evidence
→ Pantheon gates
→ human decision
```

Example candidate relation set:

```yaml
nodes:
  capability: ui.full_page_capture
  binding: mengto.stitched_full_page_capture
  resource_repository: github.MengTo.Skills
  resource_runtime: hermes

relations:
  - type: covers
    source: mengto.stitched_full_page_capture
    target: ui.full_page_capture
    status: candidate

  - type: requires
    source: mengto.stitched_full_page_capture
    target: github.MengTo.Skills
    status: candidate

  - type: executed_by
    source: mengto.stitched_full_page_capture
    target: hermes
    status: candidate
```

This example is documentation only. It does not approve, install, activate or execute the repository or skill.

## 12. Coverage and confidence

Coverage and confidence may be useful derived views, but neither is a kernel truth by itself.

### Coverage

Coverage answers whether a capability has at least one relation to a binding that is approved and available within the relevant scope.

It must not be calculated from installation alone.

### Confidence

Confidence may summarize test recency, evidence quality, source pinning, runtime observations, error history and human review.

It must remain:

- explainable;
- decomposable into cited inputs;
- scope-specific;
- non-authoritative;
- unable to approve or activate automatically.

A percentage without its basis is display decoration, not governance evidence.

## 13. Storage and implementation neutrality

This candidate model does not select Neo4j, PostgreSQL property graphs, RDF, a document database, relational tables, JSON files or another storage implementation.

An implementation may use nodes and edges, normalized tables, documents or materialized projections, provided the governance invariants remain testable.

```text
property graph selected != graph runtime adopted
schema created          != governance relation approved
data stored             != evidence admitted
query succeeds          != decision justified
```

Any schema, test, database migration, read-only MCP verification surface or cockpit implementation requires its own reviewed work package, especially under protected paths.

## 14. Adoption sequence

Recommended sequence:

1. review this candidate grammar against canonical approval, evidence, scope and memory doctrine;
2. reconcile naming with `CAPABILITY_REGISTRY.md`, `COMPETENCE_MODEL.md` and `TERMINOLOGY_BOUNDARIES.md`;
3. test three representative relation sets: documentary skill, tool-assisted binding and executable external runtime binding;
4. define a minimal read-only relation record only after the doctrine review;
5. add schema or verification artifacts only through an explicitly approved protected-path package;
6. project bounded relation views into `CARD_STACK_MODEL.md` and cockpit specifications;
7. retain human approval for consequential relation adoption and activation.

## 15. Current status

```text
implemented:                 this Markdown candidate exists once merged
documented non-implemented: graph registry, storage, API, cockpit projection, validators
partial / to verify:         alignment with existing capability and register-link candidates
to verify:                   canonical relation vocabulary and promotion path
not applicable:              runtime health for this documentation file
forbidden:                   treating this document as a graph engine or approval mechanism
```

## Final rule

```text
Pantheon may govern the legitimacy and status of relations.
Hermes may execute an approved binding externally under contract.
OpenWebUI may expose bounded projections.
Evidence supports review.
A human decides.
The graph does not become the engine.
```