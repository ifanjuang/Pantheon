# Module Activation

Status: active support doctrine — capability activation and effective-policy specialization — documented non-implemented.
Boundary profile: active_support_doctrine.

This document owns the governance semantics between **capability detection**, **governance activation** and **task authorization**.

It does not own the universal capability law, runtime execution, Cockpit product behavior, external binding selection, Evidence, approval or memory rules. Those remain with their existing owners.

## Purpose

Pantheon must be able to say that a capability exists without silently enabling it, and that a capability is enabled for a scope without silently authorizing every task that could use it.

The activation seam is:

```text
capability detected
-> governance activation for an explicit scope
-> task authorization under Task Contract + applicable policy
-> runtime/PEP may execute admitted work
```

The three stages must remain distinct.

## Parent governance

`UNIFORM_CAPABILITY_GOVERNANCE.md` owns the common law and passport rule for capabilities.

`MODULE_ACTIVATION.md` specializes that law for activation state only:

```text
Uniform Capability Governance
  -> what every capability must satisfy

Module Activation
  -> whether that capability is enabled for this scope now

Task Contract + Pantheon policy
  -> whether this task may use it

Hermes / external runtime as PEP
  -> whether admitted work/effects are actually executed
```

Product-specific optional bindings remain with `HERMES_CAPABILITY_BINDINGS.md` and related binding records. Cockpit lifecycle projection/action boundaries remain with `COCKPIT_CAPABILITY_MANAGEMENT.md` and the applicable Cockpit owners.

## Core non-equivalence

```text
detected != activated
installed != activated
activated != task-authorized
task-authorized != approved
activation != execution authorization
runtime enabled != governance activated
Cockpit projection != activation persistence
```

A capability may exist in Hermes, a runtime client or another environment without being governed for Pantheon use.

## Three-stage model

### 1. Capability detection

Detection is factual observation that a capability or surface exists somewhere.

A detection observation may include:

```text
capability_id
capability_class
detected
detected_by
detected_where
version
health
last_checked
notes
```

Detection does not enable, approve or authorize use.

### 2. Governance activation

Activation records that Pantheon has a governed posture for using the capability within an explicit scope.

Typical activation postures include:

```text
disabled
watch
candidate
sandbox_enabled
project_enabled
dossier_enabled
domain_enabled
organization_enabled
suspended
deprecated
rejected
```

Activation must identify its scope and must remain compatible with the capability passport and universal governance rules.

An activation may narrow a capability. It must not widen the passport, lower an approval ceiling or bypass a mandatory gate.

### 3. Task authorization

Task authorization is specific to a Task Contract and the applicable Pantheon policy disposition.

A capability may be detected and activated while still unauthorized for the current task.

Task authorization must preserve at least:

```text
task_contract identity
scope fit
capability/passport fit
allowed and forbidden effects
approval ceiling
required return/evidence posture
applicable policy disposition
```

Task authorization does not self-authorize a consequential effect. The external runtime/PEP still enforces the applicable policy decision.

## Activation status vocabulary

| Status | Meaning |
|---|---|
| `unavailable` | capability is not currently observed as available |
| `detected` | capability exists somewhere; no activation implied |
| `disabled` | explicitly unavailable for governed use |
| `watch` | observed but not ready for activation |
| `candidate` | reviewed as possible future activation |
| `sandbox_enabled` | enabled only for bounded sandbox use |
| `project_enabled` | enabled for an identified project scope |
| `dossier_enabled` | enabled for an identified dossier/case scope |
| `domain_enabled` | enabled for a professional/domain scope |
| `organization_enabled` | broadly enabled; exceptional and high-governance |
| `task_authorized` | current Task Contract may use the capability, subject to policy/effects |
| `suspended` | temporarily blocked pending review |
| `deprecated` | retained only for transition/compatibility |
| `rejected` | forbidden under current doctrine |

`task_authorized` is a task-facing status, not a replacement for operation-specific PDP/PEP enforcement.

## Activation scope

Activation must be scoped.

Supported conceptual scope levels include:

```text
session
task
dossier
project
domain
user
organization
system
```

Default posture:

```text
no global activation by default
```

Broader scope requires stronger justification. A system-level activation must not disable universal capability rules.

## Mandatory versus optional activation conditions

Universal mandatory constraints remain owned by the capability passport, Task Contract, Evidence, approval, memory, external-tool and policy owners.

An activation record references those owners; it does not duplicate their rulebooks.

Local optional switches may narrow runtime affordances when useful, for example:

```text
checkpoint/resume permitted
streaming status permitted
human interruption permitted
bounded retry permitted
read-only tools permitted
write tools permitted only behind applicable gates
sandbox execution permitted
project execution permitted
```

An optional switch may only narrow or configure an already-admissible capability. It must not override a mandatory rule or convert a denied effect into an allowed one.

## Effective Policy

An **Effective Policy** is the composed governance view for one capability in one current context.

It answers:

```text
Given what is detected, activated, scoped and requested,
what is the current governed posture for this capability?
```

A reviewable Effective Policy should identify or reference at least:

```text
capability/module identity
capability class
detection observation
activation status
activation scope
passport reference
Task Contract reference when task-specific
task-authorization status
applicable approval ceiling
allowed/forbidden effects or tool classes
required return/evidence posture
local optional switches
blocking reason when not usable
review/suspension state
```

Effective Policy is a governance artifact. It is not a policy engine and does not replace an operation-specific PDP disposition.

```text
Effective Policy describes current capability posture.
PDP decides the bounded policy question.
PEP enforces the consequential effect.
```

## Activation record seam

A governance activation record should remain small and scoped. Conceptually it needs:

```text
capability_or_module_id
activation_status
scope_type
scope_id
passport_ref
reviewed_by / decision_ref when required
approval_ceiling_ref
local_optional_switches
review_after
suspension_or_rejection_reason
```

This is documentary vocabulary, not a new executable schema. Existing machine-checkable capability activation/binding contracts remain the machine owners where implemented.

## Runtime and administration boundary

Runtime availability, installation and native enablement are operational facts.

They are not governance activation.

An operator-facing client may perform an explicitly human-confirmed one-shot administration request against an authenticated native runtime interface when the target and effect are visible. The observed runtime state must then be re-read truthfully.

That operation must remain distinct from Pantheon activation and task use:

```text
human-confirmed runtime administration request
-> native runtime operation
-> observed runtime state

observed runtime state
!= governance activation
!= task authorization
```

No hidden retry, follow-on task or automatic activation is implied.

Detailed runtime/client/Cockpit placement remains owned by `HERMES_INTEGRATION.md` and the applicable Cockpit/runtime configuration owners.

## Cockpit projection boundary

Pantheon Cockpit may project:

```text
detection status
activation status and scope
Effective Policy summary
blocking reason
approval/evidence gaps from their owners
review, suspend or enablement-request actions
```

A projected control may request a governance transition. Projection itself does not perform the runtime effect, persist authority by itself or authorize a consequential task.

## Suspension and review

Activation should be suspended or reviewed when evidence shows that the activation assumptions are no longer reliable, including material changes such as:

```text
scope breach
unapproved external effect
material capability/version change
runtime behavior incompatible with the passport
unexplained or misleading operational state
required policy/evidence/approval boundary violated
security or professional-risk regression
```

Suspension is a governance status. Runtime disablement may be a separate operational response.

## Handoffs to existing owners

This document stops at activation semantics.

- `UNIFORM_CAPABILITY_GOVERNANCE.md` owns the universal law/passport envelope;
- `CAPABILITY_PLACEMENT.md` owns generic capability/effect placement;
- `TASK_CONTRACTS.md` owns task scope;
- `APPROVALS.md` owns approval legitimacy and ceilings;
- `EVIDENCE_PACK.md` owns Evidence packaging/admission semantics;
- `MEMORY.md` owns Register/memory boundaries;
- `EXTERNAL_TOOLS_POLICY.md` owns external capability review/effect risk;
- `HERMES_CAPABILITY_BINDINGS.md` owns product-specific optional binding posture;
- `HERMES_INTEGRATION.md` owns runtime/client/PDP/PEP/Cockpit placement;
- Cockpit capability owners own governed projection and supported management actions.

```text
reference reviewed != activated
binding selected != activated
activated != task-authorized
task-authorized != approved
runtime success != authorization
memory != Evidence
```

## Boundary

`active_support_doctrine` boundary profile applies.

This document creates no registry, installer, plugin manager, provider router, workflow engine, scheduler, queue, runtime, approval engine or memory engine.

## Final rule

```text
Detection says the capability exists.
Activation says Pantheon permits a bounded scope under declared conditions.
Task authorization says this Task Contract may use it.
Policy and the external PEP govern consequential effects.
None of those states collapse into the next one automatically.
```
