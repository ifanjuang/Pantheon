# Bridge Contract

Status: active support doctrine — future non-authoritative bridge adapter seam — documented non-implemented.
Boundary profile: active_support_doctrine.

This document specializes the adapter boundary for a future bridge that may translate between Pantheon policy contracts and an admitted external runtime without becoming authoritative itself.

Generic runtime/client/PDP/PEP/Cockpit placement remains owned by `HERMES_INTEGRATION.md`. Generic blueprint-versus-adapter placement remains owned by `ADAPTERS_AND_BINDINGS.md`. Task, Evidence, approval, memory and capability rules remain with their respective owners.

## Core rule

```text
The bridge may adapt and convey.
The bridge may refuse malformed adapter input.
The bridge must not decide, widen or enforce authority.
```

A bridge is an adapter seam, not a second control plane.

It may translate an admitted request into the shape required by an external runtime and normalize returned material into Pantheon-readable candidates. It must preserve the applicable Pantheon policy result without broadening it.

## Parent boundaries

The bridge composes existing owners rather than restating them:

```text
HERMES_INTEGRATION.md       -> runtime/client/PDP/PEP/Cockpit placement
ADAPTERS_AND_BINDINGS.md   -> dependency direction and external adapter placement
TASK_CONTRACTS.md          -> task scope and delegation boundary
UNIFORM_CAPABILITY_GOVERNANCE.md -> capability/effect eligibility
EVIDENCE_PACK.md           -> Evidence Pack Candidate semantics
APPROVALS.md / USER_DECISION_GATE.md -> consequential approval/human decision
MEMORY.md                  -> durable-retention boundary
```

If one of those owners changes, the bridge adapts to that owner. It does not maintain a competing copy of the rule.

## Allowed bridge responsibilities

A future bridge may:

```text
receive a bounded adapter request
check that required structural fields and references are present
refuse malformed or structurally incomplete adapter input
prepare a deterministic request for the Pantheon policy service
convey the returned PDP disposition without widening it
translate eligible request material into an admitted external-runtime envelope
attach non-authoritative trace metadata
normalize runtime-return material into existing candidate object families
report adapter availability or structural failure
surface Capability Gap or human-decision need already implied by governed state
```

These are translation, structural validation and normalization operations.

They are not execution or authorization.

## Forbidden bridge responsibilities

A bridge must not:

```text
act as a second PDP
reinterpret deny as allow
widen scope, approval ceiling or effect class
claim PEP authority over a consequential effect
execute the governed work itself
own provider-routing policy
own scheduler, queue or workflow state
own memory or Evidence admission
approve output
promote Registre Probatoire material
send, publish, merge or deploy by its own authority
silently resolve a human or governance disagreement
```

```text
bridge structural preflight != policy decision
bridge handoff != runtime authorization beyond the returned policy result
bridge return != Evidence admission
bridge success != professional acceptance
```

## Input seam

The bridge consumes existing governed references rather than inventing a second task contract.

Minimum adapter-facing information should identify or reference:

```text
request_id
task_contract_id
requested_executor_or_binding
scope_reference
requested_effect_class
policy_context_or_gate_signals
trace_policy
```

Any detailed scope, approval, memory, Evidence or effect rule remains in the owning governance object.

The bridge may reject structurally incomplete input before policy consultation. Such rejection is an adapter result, not a Pantheon policy denial.

## PDP disposition seam

Only the Pantheon policy service may issue the bounded PDP disposition for a consequential effect.

The bridge may:

```text
submit the normalized policy request
receive the disposition
verify it is structurally readable
convey it unchanged to the admitted runtime boundary
```

It must never convert unavailable, malformed, expired or negative policy material into permission.

The external runtime/PEP remains responsible for fail-closed enforcement of the consequential effect as defined by `HERMES_INTEGRATION.md` and the canonical policy-service contract.

## Executor or binding selection seam

A bridge may target only an executor/binding already admissible under existing capability and binding governance.

The bridge must not create eligibility merely because an adapter is installed, reachable or named.

Concrete products, provider choices and version compatibility belong to the applicable bindings/placement owners, not to this generic bridge contract.

## Return seam

A bridge may normalize returned material into references or candidates already owned elsewhere, for example:

```text
Result Candidate
Evidence Pack Candidate
patch or artifact candidate
memory candidate
Capability Gap
risk escalation
human-decision-needed signal
trace reference
outcome observation candidate
```

The bridge does not determine the governed status of those objects beyond truthful adapter/runtime observation.

## Adapter status vocabulary

Bridge-specific operational statuses may include:

```text
policy_check_required
policy_unavailable
policy_invalid
request_not_forwarded_structural_invalid
pdp_disposition_received
eligible_for_executor_handoff
returned_candidate
returned_with_risk
returned_capability_gap
human_decision_required
adapter_failed
```

These statuses describe adapter progress or failure only.

They must not replace canonical PDP disposition vocabulary, approval status, Evidence status, runtime execution status or human-decision status.

## Failure posture

A future bridge must fail conservatively when it cannot preserve the boundary.

```text
missing required reference       -> do not forward
unreadable policy result          -> do not reinterpret
policy unavailable               -> report unavailable; no implied allow
binding not admissible            -> do not select it
runtime return structurally invalid -> return adapter failure/candidate gap
```

Failure to adapt is not authority to improvise.

## Dependency direction

```text
Pantheon governance contracts
        ↓
bridge adapter
        ↓
external runtime / binding
```

The dependency must not reverse. Pantheon doctrine must remain understandable without a bridge implementation.

A bridge can be replaced without changing governance semantics as long as the replacement conforms to the same owners and policy boundary.

## Boundary

`active_support_doctrine` boundary profile applies.

This document creates no API, endpoint, queue, scheduler, message bus, provider router, runtime, workflow engine, PDP, PEP, approval engine, memory engine or product-specific adapter implementation.

```text
Pantheon owners define the governed contracts and policy result.
The bridge adapts and conveys without widening authority.
The external runtime/PEP enforces and executes when allowed.
Returned material remains candidate until its owning governance path resolves status.
```
