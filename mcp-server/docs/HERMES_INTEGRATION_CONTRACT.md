# Hermes Integration Contract — MCP Policy Server

Status: implementation candidate — integration contract for the bounded `mcp-server/` module. Candidate until reviewed.

This contract describes how Hermes may consult Pantheon to frame work without Pantheon executing the work.

```text
exposed_by:  Hermes Web/dashboard, or another compatible client
executed_by: Hermes Agent, outside Pantheon
governed_by: Pantheon Next, via the bounded MCP Policy Server
approved_by: the human, at the applicable gate
forbidden:   execute business work; send externally; write files or state;
             approve a result; promote memory or write the Registre Probatoire;
             install, schedule, queue or route providers
```

## Boundary

The MCP Policy Server is read-only / validation / candidate-preparation only.

It may:

- list implemented consultation surfaces;
- explain allowlisted governance placement from governed sources;
- qualify caller-provided capability-status candidates;
- classify requests on the K/V/C axes;
- project the smallest currently relevant governance handling;
- validate capability passports and governed references;
- prepare Task Contract and Evidence Pack candidates;
- run read-only doctor checks;
- return policy decisions as data.

It must not:

- execute business work;
- send externally;
- write files or state;
- approve a result;
- promote memory or write the Registre Probatoire;
- install, schedule, queue or route providers;
- become a natural-language planner, hidden router, Role runtime or workflow engine.

## Optional consultation preflight

Before task classification Hermes may use existing consultation surfaces:

```text
get_consultation_catalog
explain_architecture(topic)
get_capability_status(status_yaml)
```

The MCP qualifies supplied candidates; it does not discover live runtime state by itself.

```text
connected != consulted
consulted != obeyed
reported status != runtime probe
qualified candidate != authorized capability
```

## Request intake

Pantheon does not need to become the language-understanding runtime.

The declarative Hermes candidate `templates/hermes/skills/pantheon-request-intake/SKILL.md`
now owns the bounded runtime guidance for translating raw language into the
smallest request candidate. It is not a second policy owner and it does not
derive K/V/C.

Hermes may describe the request with existing governed conditions owned by `ROLE_ACTIVATION.md`:

```yaml
conditions:
  - source_required
  - legal_or_professional_risk
```

Conditions are candidate observations.

```text
semantic intake != policy classification
condition supplied != truth
condition supplied != consequence classification
condition supplied != Role authority
condition supplied != authorization
```

The intake materiality rule is deliberately narrow: emit a condition only when
omitting it could materially change meaning, reliability/source need,
responsibility, authorization/external effect, continuity/retention, or the next
legitimate transition. This is runtime guidance, not a new consequence scale.

Legacy task-specific fields may remain compatibility aliases while callers migrate, but they are not the core ontology.

Raw intent matching remains a conservative compatibility fallback. Generic wording such as `confirm` / `confirmer` must not by itself create a high-consequence professional position.

## Progressive handling: minimal model

The handler should expose only what is needed for the next legitimate transition.

Conceptually it works from five small concerns:

```text
current state
next target state
conditions
coordination relations
gate
```

These are projection concerns, not a new persisted State schema.

Existing owners remain authoritative:

```text
REQUEST_LIFECYCLE          -> cap and proportional lifecycle
ROLE_ACTIVATION            -> governance viewpoints and trigger vocabulary
Task Contract              -> scope, constraints and admitted topology metadata
Workflow Manifest          -> governed phases, inputs, outputs and completion
K/V/C + approval owners    -> consequence, verification and authority
Hermes                     -> external execution
human                      -> consequential decision
```

## Generic coordination relations

Pantheon should describe necessary relationships, not prescribe a domain-specific recipe.

The bounded request candidate may optionally include non-persistent coordination relations:

```yaml
coordination:
  requires:
    - [state_a, state_b]
  independent:
    - [state_c, state_d]
  synthesize: true
  branch_on:
    - observed_result
  repeat_until:
    - acceptance_criteria_met
```

Meanings:

```text
requires      -> one named state must precede another
independent   -> named work items have no declared ordering dependency
synthesize    -> independent results need one shared synthesis
branch_on     -> a returned condition determines the next path
repeat_until  -> another attempt may be needed until a named criterion is met
```

These relations are caller-provided candidates. They are not a workflow, scheduler or execution graph.

```text
relation supplied != relation proven
coordination relation != dispatch
repeat condition != autonomous loop authorization
```

## Deriving existing topology

Topology is a projection of coordination relationships. It must not be selected from domain names or Role combinations.

V1 derivation:

```text
no material relation
  -> no topology emitted; direct handling remains the default

requires
  -> sequential_handoff

branch_on
  -> router

independent + synthesize
  -> fanout_extract_then_single_synthesis

independent without synthesis
  -> parallel_independent_workers

repeat_until only
  -> no new topology invented; retain it as a bounded control condition
```

`repeat_until` intentionally does not manufacture a new Task Contract topology because the current canonical topology vocabulary does not define one.

If several relation families coexist, the projection may expose the dominant existing topology while preserving all supplied relations. Hermes may optimize execution only inside those declared dependencies and the admitted Task Contract.

```text
topology selected != workers dispatched
parallel work != Role consultation
completion != approval
runtime success != authorization
```

## Roles remain independent of topology

Role viewpoints answer **who carries a governance judgement**.

Coordination relations answer **what must precede, may run independently, branch or repeat**.

Therefore the same viewpoints may legitimately appear under different coordination shapes.

```text
Role viewpoint != ordering rule
Role combination != topology
```

The handler maps only an implemented subset of `ROLE_ACTIVATION.md` triggers to Role viewpoints. Regression tests bind every implemented mapping back to that doctrine so the MCP cannot silently create a second trigger authority.

## Completion requirements

The handler accepts explicit completion requirements when the task can state them safely:

```yaml
completion_requirements:
  - requested_fact_resolved
  - tests_pass
  - acceptance_criteria_met
```

When none are provided, bounded generic fallbacks may be projected from existing governance conditions:

```text
scope_and_method_bounded
supporting_basis_qualified
current_state_qualified
consequence_boundary_reviewed
delivery_boundary_qualified
```

Explicit requirements take precedence over these fallbacks.

They remain observable transition criteria, not hidden reasoning and not a new milestone ontology.

## Current and target state

A caller may optionally provide lightweight projection labels:

```yaml
current_state: draft
target_state: reviewable_candidate
```

They help explain the transition but create no canonical state machine and no persistence by themselves.

```text
projection != persistence
state label != governed status authority
```

## Handling dispositions

Three projected dispositions remain sufficient:

```text
PROCEED  -> no additional governance consultation is currently material
CONSULT  -> one or more current requirements/relations/viewpoints need attention
GATE     -> the requested consequential effect cannot occur before the applicable decision gate
```

These are derived outcomes, not a second consequence scale.

A high-consequence candidate may remain `CONSULT` while being prepared or reviewed. The gate constrains the effect, not every prior analytical step.

## Conflict and rites

Conflict remains an observed condition, not a topology.

When a material source/Evidence conflict is reported, Pantheon may propose the existing `concordance_des_sources` rite.

```text
conflict detected != contradiction resolved
rite proposed != rite executed
rite completed != truth approved
```

## Reconsultation

Hermes does not reconsult Pantheon after every internal step.

Reconsult when a material governed condition becomes newly true, for example:

```text
source_required
evidence_gap
source_freshness_risk
provenance_unclear
project_history_reuse
duplicate_or_supersession_risk
legal_or_professional_risk
liability_risk
external_effect
external_transmission
memory_promotion
approval_required
policy_conflict
```

Or when the cap, scope, destination, authority boundary or declared coordination relationship changes materially.

```text
current governed frame
  -> smallest legitimate next transition
  -> Hermes works externally
  -> material change?
       no  -> continue
       yes -> reconsult Pantheon
```

A material cap/scope change still follows the Task Contract revision rules owned by `REQUEST_LIFECYCLE.md` and `TASK_CONTRACT_REVISIONS.md`.

## K0 fast exit

The canonical Glossary defines K0 as including orientation, formatting, local display and harmless drafts.

A declared harmless transformation such as `rewrite`, `wording`, `polish`, `formatting` or `summary` may therefore remain K0 when no stronger consequence signal is present.

```text
K0 harmless transformation
  -> no Task Contract solely because text exists
  -> no scope gate solely because text exists
  -> PROCEED unless another material condition appears
```

This makes an always-consulted Pantheon compatible with a light everyday experience.

## Target sequence

```text
1. User sends a request through an admitted Hermes client.
2. Hermes uses the bounded semantic intake guidance to identify only material candidate conditions and, when useful, coordination/completion relations.
3. Hermes calls mcp.classify_request.
4. Pantheon returns K/V/C plus the smallest handling projection.
5. PROCEED -> Hermes continues inside the admitted boundary.
6. CONSULT -> Hermes satisfies the listed requirements while respecting dependencies.
7. Material condition/relation changes -> Hermes reconsults Pantheon.
8. Task Contract / Evidence Pack candidates are prepared only when existing rules require them.
9. Hermes executes outside Pantheon.
10. GATE -> the consequential effect waits for the applicable human decision.
```

## Expected Hermes output envelope

```text
RESULT_CANDIDATE
EVIDENCE_PACK_CANDIDATE
STATUS
SCOPE_USED
APPROVAL_NEEDED
REGISTER_CANDIDATE
LIMITS_AND_UNCERTAINTIES
```

Allowed status language:

```text
candidate
requires approval
scope unclear
blocked pending evidence
human decision required
```

Forbidden status language:

```text
approved
validated truth
authorized action
safe to execute
```

## Regression coverage

`mcp-server/tests/test_progressive_request_handling.py` verifies policy projection.
`tests/test_pantheon_request_intake_skill_contract.py` binds the Hermes semantic
adapter to existing `ROLE_ACTIVATION.md` trigger ownership.
`tests/fixtures/hermes_request_intake_cases.yaml` plus
`tests/test_hermes_request_intake_policy_corpus.py` exercise a broad request
corpus across harmless transformations, factual questions, current comparison,
software diagnosis, contradiction, creative work, professional review, memory,
external transmission, branching and repeat-until behavior.

These tests validate declared semantic candidates and policy projection only.
They do not prove that a live Hermes model will infer every candidate correctly.
Live precision/recall remains a separate runtime qualification step.

## Final rule

```text
Hermes describes material conditions; it does not decide their consequence.
Pantheon governs the constraints of the path, not the path itself.
Hermes may optimize execution inside those constraints.
Roles carry bounded judgement responsibilities.
Topology is derived only when coordination relationships justify it.
Material changes trigger reconsultation.
The gate constrains consequential effects.
The human decides.
```
