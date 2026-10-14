# Pantheon consultation contract

Status: implemented read-only / partial / protected path — transport-neutral response contract for the bounded `mcp-server/` consultation and policy slice.

This contract lets MCP clients and authenticated internal HTTP clients consume one transport-neutral policy service without duplicating Pantheon policy logic.

It does not implement an execution runtime, remote MCP transport, user identity authority, evidence store, private knowledge retrieval engine, Mem0 or Memvid connector, approval engine or write path.

## Boundary

```text
repository sources or caller-provided candidates/evidence
  -> PantheonPolicyService
  -> local MCP stdio projection
  -> authenticated internal HTTP projection
```

The service may:

- list honest surface availability;
- explain allowlisted architecture placement and rationale;
- cite governed repository sources with authority and status;
- qualify caller-provided operational-status candidates;
- classify requests and required gates;
- evaluate whether candidate work may continue;
- prepare Task Contract and Evidence Pack candidates;
- validate caller-provided governed structures;
- classify caller-provided verification evidence;
- plan and validate a scoped Context Pack candidate.

It must not:

- probe Hermes or another runtime unless a separately defined read-only verifier explicitly receives caller-provided probe results;
- claim to discover installed modules;
- retrieve project documents, private knowledge or memory;
- authorize activation, installation, update, execution or external transmission;
- approve evidence or write the Registre Probatoire;
- infer a missing status from another status;
- persist a human decision;
- execute, schedule, queue, route providers, send or mutate external state.

## Common response envelope

Every service projection carries:

```text
contract
operation
source_mode
authority_effect       none
authorization_effect   none
write_effect           false
execution_effect       false
evaluated_at
repository.version
repository.commit
input_sha256            when an input was supplied
```

Consultation functions that already use `pantheon.consultation.v1` retain that contract identifier while also receiving the shared operation and effect fields. Other service responses use `pantheon.policy.v1`.

Source-backed responses also carry source references containing, where available:

```text
uri
title
source_file
exists
authority
status
declared_status
content_sha256
```

The response is a projection. The cited source retains its declared authority and status.

## Implemented read-only consultation functions

### Consultation catalog

`consultation_catalog()` distinguishes:

```text
implemented_read_only
implemented_read_only_partial
implemented_external_read_only_partial
documented_non_implemented
```

The local MCP and internal HTTP adapters expose the same catalog through:

```text
MCP:  get_consultation_catalog
HTTP: GET /consultation
```

Live runtime inventory remains an external Hermes dashboard-plugin responsibility. Evidence-instance queries, private knowledge retrieval, Mem0/Memvid retrieval, scoped identity/permission enforcement and remote MCP transport remain non-implemented in the policy service.

### Architecture explanation

`explain_architecture(topic)` supports an allowlist of architecture concepts:

```text
pantheon
hermes
openwebui
pantheon-control
mcp
api
capabilities
knowledge
memory
evidence
```

Unknown input returns `unknown_topic`; it never becomes a repository path.

```text
MCP:  explain_architecture
HTTP: GET /architecture/{topic}
```

### Capability-status qualification

`qualify_capability_status(candidate)` retains the client-facing capability identity but its source mode is always `provided_status_candidate`. It performs no runtime lookup.

```text
MCP:  get_capability_status
HTTP: POST /observations/capabilities:qualify
```

The provided candidate mirrors independent reported runtime and governance-oriented axes:

```yaml
capability_id: document-retrieval
producer: hermes_dashboard
listed: true
detected: true
installed: true
configured: true
enabled: true
reachable: true
health: healthy
governance_status: approved_for_project
task_use_status: eligible_under_reviewed_contract
update_status: up_to_date
rollback_status: tested
observed_at: "2026-07-15T21:00:00+02:00"
scope:
  scope_type: project
  scope_id: example-project
evidence_refs:
  - evidence-pack.example
```

The `governance_status` and `task_use_status` values on this legacy operational-status surface are caller-reported qualification inputs. They are not the canonical tranche-I eligibility or task-authorization owners.

```text
reported governance_status
!= Capability Passport exact-release eligibility

reported task_use_status
!= Task Contract / Execution Admission
```

Canonical Capability eligibility is qualified from the Capability Passport and its exact immutable implementation provenance. Scoped activation belongs to the exact-binding `CapabilityActivation` record. Task/run legitimacy remains downstream in Task Contract / Execution Admission. A caller-provided positive status never substitutes for any of those owners.

This operational-status qualifier is retained because it preserves runtime/dashboard observations and impossible-state checks without probing or writing a runtime. It must not be extended into a second admission or activation engine.

Missing fields remain capability gaps. Unsupported values and impossible combinations fail closed as `result: invalid`.

Even a complete candidate returns:

```text
authorization_effect: none
runtime_probe_performed: false
use_posture: requires_task_preflight_and_any_applicable_human_decision
```

### Capability Passport eligibility

`validate_passport(candidate)` validates the canonical Capability Passport and qualifies review eligibility against an exact immutable implementation release when status is `reviewed`.

Its responsibility is deliberately narrower and stronger than the operational-status surface:

```text
Capability Passport
= governed Capability classification + exact-release eligibility

CapabilityActivation
= scoped governance activation of one exact CapabilityBinding

Task Contract / Execution Admission
= task/run legitimacy
```

The Passport validator has zero activation and authorization effect. Historical Passport activation/task fields are compatibility-only; a positive Passport `task_authorized` value is invalid.

## Policy classification and preflight

### Request classification

```text
MCP:  classify_request
HTTP: POST /policy/requests:classify
```

Returns K/V/C classification, Task Contract requirement, Evidence requirement and required gates. Classification is not authorization.

### Candidate-work preflight

```text
MCP:  evaluate_preflight
HTTP: POST /policy/preflights:evaluate
```

The preflight consumes a request plus caller-provided gate references and returns a disposition such as:

```text
blocked_pending_scope
blocked_pending_task_contract
blocked_pending_evidence
blocked_pending_human_decision
eligible_for_candidate_work
eligible_with_gate_signals_unverified
```

V0 never authorizes an external or canonical effect:

```text
external_effect_allowed: false
canonical_effect_allowed: false
gate_signal_validation_performed: false
authorization_effect: none
```

Hermes remains the Policy Enforcement Point. For consequential effects, failure to obtain a policy response must fail closed in the Hermes adapter.

## Context Pack split

The policy service does not retrieve a generic current context.

```text
MCP:  plan_context_pack
HTTP: POST /context-packs:plan
```

returns boundaries and missing fields for a producer that will assemble a scoped candidate.

```text
MCP:  validate_context_pack
HTTP: POST /context-packs:validate
```

validates a caller-provided candidate against `schemas/context_pack.schema.yaml`.

```text
schema valid != authorized context
retrieved != evidence
```

## HTTP compatibility routes

`POST /domain/approval/classify` is a temporary alias of the stable classification route. It classifies the required approval ceiling and never approves.

`GET /runtime/context-pack` and `GET /domain/snapshot` return HTTP `501 contract_not_defined`. Their generic object semantics are intentionally not invented. Callers must use explicit Context Pack, repository-state or capability-observation operations.

## Route identity

Internal HTTP paths use stable responsibility names. The response contracts remain revisioned independently:

```text
route identity != contract revision
pantheon.policy.v1 != /v1 route requirement
```

## Non-equivalence rules

```text
listed != installed
detected != configured
configured != enabled
enabled != reachable
reachable != healthy
installed != approved
hermes_enabled != pantheon_governance_activation
healthy != safe
reported_governance_status != exact_release_eligibility
reported_task_use_status != Execution Admission
governance_eligible != task_authorized
update_available != update_authorized
runtime_success != evidence
binding_selected != dependency_adopted
retrieved != evidence
ready != safe
classification != authorization
provided gate reference != validated decision
```

## Transport parity rule

For one operation and canonical input:

```text
core service result
MCP result
HTTP result
```

must retain the same operation-specific meaning. Transport metadata may differ; consequence, verification, approval, gaps, refusals and non-equivalence warnings must not.

## Deployment status

The HTTP adapter code and hardened Compose candidate are implemented in the repository. This means:

```text
implementation present
```

It does not mean:

```text
installed
healthy
connected to Hermes
enforced by Hermes
activated
approved for real data
production authorized
```

## Final rule

```text
The core defines one policy meaning.
MCP helps agents consult and prepare.
HTTP exposes deterministic policy/preflight data.
Hermes enforces and executes outside Pantheon.
The human decides consequential effects.
Neither transport becomes authority, evidence or runtime.
```
