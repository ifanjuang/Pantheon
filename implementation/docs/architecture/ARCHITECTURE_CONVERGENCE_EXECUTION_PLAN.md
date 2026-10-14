# Pantheon architecture convergence execution plan

Status: active working implementation plan — non-authoritative, non-runtime, removable after completion.

Date: 2026-08-02

Canonical governance remains in `Pantheon-Next`. This document owns only the implementation sequence for `pantheon-mvp` and the coordinated cross-repository cleanup.

Primary references:

```text
Pantheon-Next/docs/governance/ROADMAP.md
Pantheon-Next/docs/governance/authority/PANTHEON_SYSTEM_OWNERSHIP_REGISTRY.json
docs/architecture/PANTHEON_ARCHITECTURE_AUDIT.md
```

## 1. Purpose

Converge the existing implementation before adding more layers.

The program must:

- remove active generation-named modules, routes, schemas, tests and projections;
- eliminate competing paths and obsolete compatibility surfaces;
- identify and remove proven dead code;
- place doctrine, implementation, runtime behavior and projection correctly;
- make new governed rules easy to integrate without touching unrelated domains;
- improve PostgreSQL, API and Cockpit performance from measured baselines;
- preserve Evidence, approval, scope, task authorization and human-decision boundaries.

```text
one governed concept
-> one semantic owner
-> one canonical implementation path
-> replaceable adapters
-> simple projections
```

## 2. Current baseline and open-PR gate

The calibrated cross-repository audit is merged and executable. Its last reliable run found no demonstrated P0 authority conflict, but identified active generation names, internal version-prefixed routes, misplaced governance material and Python modules without a proven consumer.

The audit must be regenerated because the contradictory-review doctrine, compiler, persistence and API slices were merged afterwards.

`pantheon-mvp#163` is draft and currently declares new contradictory-review routes under `/v1`. It must not merge in that form. The routes must be renamed to stable responsibility-based paths, or the PR must remain draft until the Agency/Work route tranche establishes them. No permanent compatibility alias may be added merely to permit merging.

## 3. Permanent boundaries

```text
Pantheon-Next
-> semantic governance, schemas, states, gates, Evidence, scope and approvals

pantheon-mvp
-> PostgreSQL, APIs, application services, projections and bounded adapters

Hermes / external runtime
-> task execution, tools, provider routing and runtime-local state

Cockpit / OpenWebUI
-> interaction, display and human-decision surfaces

Human
-> consequential decision
```

Every tranche preserves:

```text
semantic owner != implementation owner
implementation owner != runtime owner
projection owner != authorization authority
installed != approved
healthy != safe
runtime_success != Evidence
retrieved != truth
binding_selected != dependency_adopted
activated != task_authorized
UI status != authorization
```

## 4. Modularity target

### 4.1 Code modularity

Each module has one reason to change and belongs to one layer:

```text
domain       -> concepts, invariants and state transitions
application  -> commands, queries and deterministic orchestration
api          -> HTTP translation and authentication dependencies
persistence  -> PostgreSQL transactions, repositories and migrations
adapters     -> Hermes, Paperless, Docling, OpenWebUI and other bindings
projections  -> Cockpit and read-model composition
registries   -> validated declarative definitions and startup indexes
bootstrap    -> explicit static wiring
```

Dependency direction:

```text
api -> application -> domain
persistence -> domain
adapters -> application/domain contracts
projections -> application query results
bootstrap -> concrete implementations
```

Forbidden directions:

```text
domain -> FastAPI/PostgreSQL/Cockpit/Hermes client
adapter -> approval authority
projection -> semantic state mutation
```

The structure is introduced domain by domain. Empty architecture folders are not created in advance.

### 4.2 Rule modularity

A new governed rule follows one bounded path:

```text
1. governed definition in Pantheon-Next
2. stable rule identifier plus technical revision
3. vendored/reference contract in pantheon-mvp when required
4. pure deterministic evaluator
5. explicit static registration in one composition root
6. typed RuleResult or Observation
7. focused tests
8. optional Cockpit projection
```

The evaluator accepts explicit typed input, returns a candidate result, performs no network or database access, triggers no external action, promotes neither Evidence nor approval, and exposes unsupported or inconclusive states.

```python
@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    revision: int
    input_type: str
    result_type: str

class RuleEvaluator(Protocol):
    definition: RuleDefinition

    def evaluate(self, subject: object, context: object) -> object:
        ...
```

Evaluators are wired through an explicit startup registry. This is static application composition, not dynamic plugin discovery.

```text
registry != plugin manager
registered != approved
rule available != task authorized
rule evaluated != action permitted
```

### 4.3 Extension classification

| Addition | Semantic owner | Implementation location | Extension point |
|---|---|---|---|
| Governed rule or status | Pantheon-Next | pure evaluator when required | rule registry |
| Application use case | Pantheon-Next contract | `application/` | command/query handler |
| Persistence | governed data semantics | `persistence/` | repository protocol |
| External integration | governed boundary | `adapters/` | adapter protocol |
| Cockpit display | presentation constraints | `projections/` | projection builder |
| Runtime capability | Hermes/external runtime | outside Pantheon | Task Contract and return adapter |

Before adding a concept, test whether Context, Trace, Knowledge, Evidence, Claim, ChangeCandidate, Competence, Governed Resource or Observation already covers it.

## 5. PR discipline

Every PR must have one architectural responsibility, identify the semantic owner, enumerate consumers, include audit before/after evidence, keep rollback possible through one revert, add no permanent alias, and avoid combining a broad move with a behavior rewrite.

A PR must not increase the number of active implementation paths or hide changes to Evidence, approval, scope or task authorization.

## 6. Ordered stages

### Stage A — Refresh the baseline

Actions:

1. run the cross-repository audit on both current `main` branches;
2. archive Markdown and JSON results;
3. generate the Python import graph;
4. enumerate mounted FastAPI routes from composed applications;
5. enumerate JavaScript inclusion, imports, dynamic loads, globals and CSS dependencies;
6. record test duration, startup duration, Cockpit snapshot latency and SQL query count.

Exit criteria:

- every P0–P2 finding has a stable identifier;
- open PRs adding debt are listed;
- measurements are reproducible.

Rollback: generated reports only; no runtime change.

### Stage B — Freeze new debt

Actions:

- establish a checked baseline for generation names and internal route prefixes;
- fail CI when a PR increases it;
- distinguish internal paths from external protocol versions;
- allow exceptions only for ordered migrations, data/schema revisions and external protocols isolated in adapters;
- require a removal condition for every retained `legacy`, `compat`, `deprecated`, `obsolete` or `old` path.

Exit criteria:

- the baseline can only decrease;
- Pantheon-Next#163 uses stable paths or remains draft.

### Stage C — Remove passive generation names

First target:

```text
mvp_vertical/cockpit/v3/materials.json
-> mvp_vertical/cockpit/registries/materials.json
```

Replace:

```json
{"schema_version": "cockpit.materials.v1"}
```

with:

```json
{"schema_id": "cockpit.materials", "revision": 1}
```

Also review active test names, documents, CSS classes and JavaScript globals named after generations. For Cockpit assets, prove HTML inclusion, static/dynamic imports, ordered loads, global producers/consumers, CSS selectors, tests and published regression dependencies before removal.

Exit criteria: no active file path is generation-named; visual and behavioral contracts remain unchanged.

### Stage D — Correct repository placement

Known target:

```text
pantheon-mvp/docs/governance/PROFESSIONAL_DUTY_OF_CARE.md
```

Compare it with existing responsibility doctrine in `Pantheon-Next`, merge into an existing owner when possible, index the resulting authority, then remove the MVP copy or replace it with a short implementation reference.

Exit criteria: one semantic source remains and the audit no longer reports competing placement.

### Stage E — Remove internal route generation prefixes

Each domain tranche updates atomically:

```text
server route
-> Python clients
-> JavaScript clients
-> scripts
-> tests
-> examples
-> documentation
```

The old route is removed in the same PR; no permanent alias.

Order:

1. **Read-only MCP HTTP projection** — bounded pilot.
2. **Agency, Work and contradictory review** — candidate paths:
   ```text
   /agency/projects
   /agency/claims
   /agency/change-candidates
   /work/decisions
   /projects/{project_id}/contradictory-reviews
   /contradictory-reviews/{review_id}
   ```
3. **Cockpit** — migrate routers, shell, data loader, actions, editors, registry consumers and tests together.
4. **Documents and governed resources** — candidate paths:
   ```text
   /documents/observations
   /documents/network-observations
   /resources/paperless
   /resources/openwebui
   ```
5. **Hermes** — migrate last:
   ```text
   /hermes/handoffs
   /hermes/executions
   /hermes/project-change-candidates
   ```

Exit criteria: no active internal route begins with a generation prefix and no duplicate route family remains.

### Stage F — Prove use before deleting modules

For every suspect module, inspect absolute and relative imports, `include_router`, console scripts, `python -m`, Docker commands, shell calls, dynamic/path-based invocation, tests, Hermes invocation, migration loading and framework reflection.

Each module receives one decision:

```text
retain
simplify
merge
move
remove
```

Removal requires no consumer, deployment reference, compatibility obligation or vendored-reference role, plus green full tests.

Exit criteria: no module remains merely “possibly unused”.

### Stage G — Consolidate shared primitives

Candidates:

```text
EntityRef
SourceRef
ActorRef
Provenance
Revision
Observation
Pagination
ApplicationError
IdempotencyKey
ExpectedRevision
```

A primitive is introduced only after at least two genuinely compatible uses are demonstrated. Domain-specific data and semantic status enums remain in their domains. Universal repositories and generic base classes are rejected unless they remove real repeated behavior.

Exit criteria: one internal representation per accepted primitive, no circular imports and no loss of domain meaning.

### Stage H — Establish modular domain boundaries

Target shape, introduced progressively:

```text
pantheon_mvp/
  domain/
  application/
  api/
  persistence/
  adapters/
  projections/
  registries/
  bootstrap/
```

For each domain:

1. inventory API, persistence, service and projection files;
2. define the domain contract without changing behavior;
3. move deterministic behavior;
4. place persistence behind a protocol;
5. reduce routers to translation;
6. wire concrete implementations in one composition root;
7. remove former paths after consumer migration.

Composition roots such as `bootstrap/cockpit.py`, `bootstrap/documents.py` and `bootstrap/hermes.py` may wire components but contain no domain decisions.

Exit criteria: dependency direction is testable and a rule can be added without editing unrelated modules.

### Stage I — Consolidate Hermes boundaries

Canonical use cases:

```text
admission
launch preparation
context access
return capture
human reconciliation
```

Target split:

```text
domain/hermes      -> identities, states and invariants
application/hermes -> admission, preparation, context and return
adapters/hermes    -> transport and runtime observations
api/hermes         -> HTTP translation only
```

Pantheon must not own scheduling, queues, provider routing, autonomous retries, tool selection, runtime memory or approval from execution success.

Exit criteria: one canonical chain from admission to result candidate, no duplicated validation, replaceable transport and candidate-only returns.

### Stage J — Normalize observations and governed resources

Use one envelope while preserving independent dimensions:

```python
@dataclass(frozen=True)
class Observation:
    subject: EntityRef
    dimension: str
    status: str
    observed_at: datetime
    source: SourceRef
    details: Mapping[str, object]
```

Dimensions may include installation, reachability, health, native state, update, activation, governance, task authorization and compatibility.

Adapters produce observations; application queries compose them; Cockpit projects them.

Exit criteria: Paperless, Docling, Hermes and OpenWebUI share one envelope without implying one status from another.

### Stage K — Optimize measured performance

Measure before and after:

- startup and registry loading;
- Cockpit snapshot latency and payload size;
- SQL query count per major endpoint;
- controlled p50/p95 durations;
- full test duration;
- pagination behavior.

Candidate optimizations:

- compile registries once at startup and publish immutable indexes atomically;
- share one HTTP client/pool per adapter;
- keep network calls outside database transactions;
- use short reserve/record transactions around external effects;
- batch reads and remove N+1 queries;
- create bounded Cockpit read projections;
- paginate documents, chunks, runs, observations and ChangeCandidates;
- remove repeated full-payload validation between trusted layers while retaining entry/effect invariant checks.

Exit criteria: every optimization has a measured gain or documented correctness benefit; no cache becomes a truth or authorization source.

### Stage L — Close the program

Actions:

1. rerun the complete audit;
2. review every remaining finding;
3. require zero unreviewed P0, P1 and P2 findings;
4. reduce the temporary baseline to zero;
5. remove expired exceptions;
6. record final architecture and performance metrics;
7. close or remove temporary plans according to repository cleanup rules.

Final criteria:

```text
no active generation-named architecture
no internal generation-prefixed routes
one semantic owner per governed concept
one canonical implementation path per responsibility
no unclassified suspected dead code
replaceable adapters
static reviewable composition
new rule integration = definition + evaluator + registration + tests + optional projection
```

## 7. Planned PR sequence

```text
A  refresh architecture and performance baseline
B  freeze new versioned identities and route debt
C  remove passive generation-named Cockpit paths and identities
D  move misplaced governance material
E  migrate read-only MCP HTTP routes
F  migrate Agency, Work and contradictory-review routes
G  migrate Cockpit routes and clients
H  migrate Documents and governed-resource routes
I  migrate Hermes routes
J  classify and remove proven dead modules
K  consolidate accepted shared primitives
L  establish domain modules and composition roots
M  consolidate Hermes application seams
N  normalize observations and governed-resource projections
O  optimize PostgreSQL, API and Cockpit performance
P  close the audit baseline and temporary plan
```

The letters express order only. They are not architecture generations or permanent identifiers.

## 8. Rule-addition checklist after convergence

1. Which existing Pantheon concept owns the rule?
2. Is a new concept genuinely required?
3. What is the stable identifier and technical revision?
4. What exact typed input is accepted?
5. What typed candidate result is returned?
6. Can the evaluator run deterministically without I/O?
7. Where is it statically registered?
8. Which application use case invokes it?
9. Which human or gate remains authoritative?
10. Does Cockpit only project the result?
11. Which tests cover unsupported, inconclusive and rejected states?
12. Which adapter is optional and replaceable?
13. Does the addition create any scheduler, queue, provider router, plugin manager, memory engine or automatic approval behavior?

An unanswered item blocks implementation or returns the proposal to architecture review.

## 9. Definition of done for each PR

```text
scope documented
canonical owner identified
consumers enumerated
focused tests green
full CI green
audit finding reduced or intentionally classified
no new generation identity
no hidden compatibility path
no authority-boundary regression
rollback documented
```

## 10. Non-goals

This plan does not authorize microservices, event-bus adoption, framework-driven CQRS, dynamic plugins, runtime installation, provider selection, automatic retries, scheduling, memory promotion, Evidence admission, automatic approval or broad ontology expansion.

The intended result is a disciplined modular monolith, not a new platform layer.