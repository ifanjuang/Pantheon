# Non-Equivalence Rules

Status: active support doctrine — non-equivalence vocabulary and deduplication rule.
Boundary profile: active_support_doctrine.

This document centralizes Pantheon Next's recurring “X does not mean Y” rules.

It does not create a runtime, schema, test, CI workflow, operation, platform component, Docker configuration, environment setting, approval engine, memory engine, scheduler, queue, provider router, plugin manager, installer, updater or external action.

## Purpose

Pantheon Next relies on non-equivalence rules to prevent status collapse.

These rules stop a useful signal, artifact, test, trace, template, runtime result or candidate from being mistaken for authority.

Use this document as the canonical reference instead of repeating long local lists everywhere.

## Core rule

A thing may be useful without being authoritative.

A thing may be structurally valid without being true.

A thing may be available without being approved.

A thing may have executed successfully without being evidence.

## Runtime and operation

```text
runtime_success != evidence
runtime_success != approval
runtime_success != safety
healthy != safe
installed != approved
installed != activated
activated != authorized_for_consequential_use
update_available != update_authorized
rollback_available != rollback_decided
projection != persistence
binding_selected != dependency_adopted
watchlist_item != install_instruction
```

## Evidence and truth

```text
retrieved != truth
indexed != evidence
source_ref != evidence
retrieval_trace != proof
reference_valid != truth
schema_valid != evidence
schema_valid != approved
source capture != Evidence
fixture_pass != runtime_success
validator_success != runtime_success
claim_extracted != claim_confirmed
latest != applicable
retrieved_predecessor != valid_predecessor
```

## Approval and external action

```text
candidate != approval
reviewable != approved
runtime_approval != Pantheon_Decision
runtime_always_allowance != governed_approval_ceiling
pre_tool_call != Pantheon_PEP
runtime_guard_passed != effect_authorized
runtime_guard_available != effect_boundary_owned
lab_sentinel_pass != deployed_route_guard_qualified
runtime_guard_unqualified != Pantheon_PEP_unavailable
internal_draft_approval != external_send_authorization
approve_for_internal_draft != authorize_external_send
human_review_needed != human_approval_granted
external_action_possible != external_action_authorized
send_draft != send_authorization
effect_executed != outcome_qualified
```

## Memory and register

```text
register_candidate != admitted_memory
register_candidate_creation != memory_admission
memory_candidate != memory
memory != Evidence
folder/path != governed identity
trace != doctrine
ai_log != canon
recalled != validated
stored != approved
```

## Templates and documents

```text
template != implementation
prompt_template != deployed_system_prompt
method_card != method_engine
workflow_candidate != workflow_runtime
documented_workflow != implemented_workflow
example != authority
static_prototype != live_cockpit
public_page != product_availability
```

## Schemas, tests and validation

```text
schema_contract != runtime
schema_valid != policy_decision
test_pass != authority_promotion
green CI != adoption
green_check != protected_path_authorization
read_only_check != approval_engine
validation_report != human_decision
```

## Capability and dependency

```text
capability_slot != installed_capability
capability_candidate != approved_dependency
external_reference != adopted_dependency
provider selected != authority transfer
reference_review != dependency_approval
model_passport != model_router
MCP_passport != tool_authorization
```

## Dependency, order and sequencing

```text
depends_on != execution_order
dependency_edge != execution_instruction
dependency_satisfied != approval_granted
task_completed != downstream_authorized
scheduled != authorized
runtime_order != governed_project_chronology
parallelizable != safe_to_parallelize
blocked_by != caused_by
cycle_detected != invalid_dependency
rite_completed != next_rite_authorized
```

A dependency relation describes what a governed object needs. It does not compute
readiness. Whether a predecessor's exit criteria are met remains an APOLLO
judgment, and whether the next step is permitted remains a THEMIS and approval
question. Traversing an edge answers neither.

A blocking relation is therefore asserted by a Role, a method or a human. It is not
derived from state by a traversal. Deriving it would let the graph decide the next
allowed action, which is the scheduler these rules exist to prevent.

Governance-graph relation vocabulary remains owned by `PANTHEON_GRAPH_MODEL.md`.
Project-world relations of the architecture domain are owned by
`docs/domain-packs/architecture/PROJECT_ANATOMY_MODEL.md` (sections 6 and 8) and
its versioned relation profile
`registries/architecture_relation_profile.registry.json`;
`ARCHITECTURAL_PROJECT_GRAPH.md` uses plain orientation labels for those
relations and owns none of them. This section records the status collapses to
avoid when those relations are read, not the relations themselves.

## Use in documents

Prefer a short local reference:

```text
Non-equivalence rules apply: see docs/governance/NON_EQUIVALENCE_RULES.md.
```

If a document has a local risk, repeat only the relevant two or three distinctions.

Do not copy the whole list unless the document itself is a boundary map.

## Use in PRs

PR descriptions should name the local distinctions when a change could collapse statuses.

Example:

```text
Preserved distinctions:
- template != implementation
- candidate != approval
- runtime_success != evidence
```

## Forbidden use

Do not use a non-equivalence rule as a substitute for review.

If a change touches runtime, protected paths, external action, memory, approval or installation/update status, the PR must still name that specific effect.
