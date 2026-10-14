# Hermes Runtime Governance

Status: candidate support doctrine — Hermes runtime capability slot and runtime-card placement. Repository state: documented non-implemented.
Boundary profile: candidate_support_note.

## Purpose

This document distills Hermes Agent setup and runtime material into a Pantheon governance shape.

It is not a Hermes installation guide.
It is not an operations runbook.
It is not a provider-routing plan.
It is not a dashboard-control specification.
It does not install, configure, update, run, expose or approve Hermes Agent.

The document answers one question:

```text
How should Pantheon classify and expose the state of Hermes Agent when Hermes is considered as the external execution runtime?
```

## Source posture

This document was created from a user-supplied external beginner setup guide for Hermes Agent dated 2026-07-08 and checked against official Hermes sources.

Source classes:

| Source | Authority for Pantheon | Use here |
|---|---|---|
| Official Hermes installation documentation | external reference | Confirms setup surfaces, installer posture, Tool Gateway, `hermes setup --portal`, `hermes doctor`, update/config commands and profile-local memory status. |
| Official Hermes release source | external reference | The current reviewed release identity and release-specific qualification facts are owned by `HERMES_RUNTIME_SURFACE_REVIEW.md`. |
| Community beginner setup guide | external reference / field report | Identifies user pitfalls, first-run mental model, and runtime-status signals worth exposing. |

No external source governs Pantheon. External references may inform adapter placement, evidence expectations, card fields, gates and risk warnings only.

## Local boundary

```text
exposed_by:
  OpenWebUI or another cockpit surface may expose Hermes runtime cards, warnings,
  evidence references, approval state and status probes.

executed_by:
  Hermes Agent executes externally when separately installed and configured outside
  Pantheon.

governed_by:
  Pantheon governs capability status, approval, evidence expectation, scope,
  memory impact, external-action legitimacy, activation posture, update authorization
  and rollback visibility.

approved_by:
  A human approves installation, activation, provider binding, tool surfaces,
  gateway exposure, consequential external action, update and rollback.

forbidden:
  Pantheon must not become a Hermes installer, runtime, scheduler, queue,
  provider router, MCP host, plugin manager, memory backend, approval engine,
  auto-update path, secret store or gateway exposure mechanism.
```

Non-equivalence rules apply: see `docs/governance/NON_EQUIVALENCE_RULES.md`.

Locally material distinctions:

```text
installed != approved
healthy != safe
update_available != update_authorized
binding_selected != dependency_adopted
runtime_success != evidence
gateway_running != gateway_exposed_safely
profile_created != scope_governed
hermes memory off != built-in memory injection off
memory tool absent != memory injection disabled
```

## Capability Slot

Hermes Agent is represented as a runtime-level Capability Slot, not as a Pantheon dependency.

```text
capability_id: hermes_agent_runtime
function: external agentic execution runtime for bounded tasks
candidate_binding: NousResearch/hermes-agent
binding_status: candidate / to_verify
owner_layer: execution_runtime
executed_by: Hermes Agent
governed_by: Pantheon Next
exposed_by: OpenWebUI / cockpit status card
installation_status: unknown | absent | proposed | pending_approval | installed | failed | blocked | suspended
health_status: unknown | ready | degraded | unavailable | error | stale
update_status: unknown | up_to_date | update_available | security_update_available | breaking_update_available | deprecated
activation_status: unavailable | detected | sandbox_enabled | project_enabled | production_enabled | suspended | rejected
allowed_outputs:
  - Result Candidate
  - Evidence Pack Candidate
  - Runtime Trace Reference
  - Capability Gap
  - Risk Escalation
  - Output Artifact Reference
forbidden_outputs:
  - approval
  - proof
  - canonical memory
  - external-action authorization
  - dependency adoption
  - safe-runtime conclusion
```

## Runtime card grammar

A Hermes Runtime Card may be exposed in the cockpit as a governed status object.

Minimum fields:

```text
card_id: hermes_runtime
card_type: external_runtime_card
runtime_name: Hermes Agent
runtime_version_observed:
runtime_version_source:
release_status: unknown | current | patch_available | stale | deprecated | to_verify
install_status:
health_status:
update_status:
activation_status:
provider_binding:
model_binding:
tool_surfaces:
  web:
  file:
  terminal:
  browser:
  gateway:
  memory:
profiles:
  default_profile_status:
  scoped_profiles:
  governed_profile_route:
  governed_runtime_mode_status:
memory_posture:
  external_provider: unknown | off | selected
  built_in_memory_injection: unknown | off | on
  built_in_user_profile_injection: unknown | off | on
  memory_tool: unknown | off | on
  session_memory_key: unknown | absent | present
  observation_source:
  observed_at:
gateway_channels:
  telegram:
  discord:
  whatsapp:
  other:
secrets_posture:
  stored_in_pantheon: false
  external_secret_owner:
  visible_to_pantheon: false | redacted_reference_only
last_status_probe:
status_probe_source:
evidence_refs:
approval_refs:
rollback_refs:
open_gates:
risk_notes:
```

The card exposes status. It does not create status.
The card may request review. It does not grant review.
The card may show a health probe. It does not establish safety.

A complete governed memory posture is:

```text
external_provider: off
built_in_memory_injection: off
built_in_user_profile_injection: off
memory_tool: off
session_memory_key: absent
```

Any unknown or `on/present/selected` value keeps the governed profile `not_qualified`.

## Setup guide distillation

The beginner setup guide is useful because it reveals governance surfaces that first-time users actually encounter.

| Setup-guide element | Pantheon reading | Governance effect |
|---|---|---|
| Desktop installer / CLI installer | installation proposal | Human approval before install; evidence of install path required before status changes. |
| `hermes setup --portal` | provider and Tool Gateway binding candidate | Provider binding and bundled tools require explicit classification; convenience does not equal authorization. |
| Model selection | model capability binding | Route through model passport / capability suitability, not provider-router logic. |
| Local model path | local processing posture | Data exposure may decrease, but local host-control risk increases; still needs governance. |
| Free cloud model tiers | external provider candidate | Cost and availability do not decide admissibility. |
| Tool enablement | capability surface activation | `tool_available` and `tool_enabled` remain below approval for consequential use. |
| Memory provider selection | external memory binding | `hermes memory off` disables the external provider only; built-in injection, user profile and memory-tool states remain separate observations. |
| Gateway setup | external communication surface | Gateway activation and channel exposure require explicit human approval. |
| Profiles | scope/memory compartment | Profile creation does not govern professional scope or memory admission. |
| `hermes doctor` | health probe | Health probe is evidence of technical status only, not safety or proof. |
| Update commands | update signal | Update available does not authorize update. |
| Common pitfalls | risk warnings | Useful for card warnings and preflight checks, not doctrine by themselves. |

## Gates

### Installation gate

Hermes installation may be proposed as a runtime binding event.

Required before status moves beyond `proposed`:

```text
human_approval: required
source_review: required
install_path_declared: required
secrets_policy_declared: required
rollback_expectation: required
```

Pantheon may record the decision. Hermes or the operating environment performs the installation outside Pantheon.

### Provider-binding gate

Any cloud or local model provider binding must identify:

```text
provider_name
model_name_or_family
processing_posture: local | cloud | hybrid | unknown
data_exposure
cost_or_quota_signal
capability_suitability
forbidden_task_families
approval_ceiling
```

A provider selected by a setup wizard remains a candidate binding until reviewed.

### Tool-surface gate

Tool surfaces such as web, file, terminal, browser, memory and gateway are classified independently.

```text
tool_detected != tool_authorized
tool_enabled != approved_for_consequential_use
tool_success != evidence
memory tool absent != memory injection disabled
```

Terminal, file, browser, gateway and external connector surfaces require elevated review because they can produce host-control effects, data exposure, external action or memory drift.

### Governed-memory gate

Before a profile is qualified for a Pantheon Task Contract, record all five memory-posture axes:

```text
external provider
built-in MEMORY.md injection
built-in USER.md profile injection
memory tool
X-Hermes-Session-Key use
```

A provider-off observation alone is incomplete. The observer must fail closed when any axis is unknown.

The observation may be produced by a bounded external/operator probe. Pantheon displays and classifies the observation; it does not read arbitrary profile files, run configuration commands or mutate Hermes.

### Gateway exposure gate

A running gateway is not safe exposure.

Before any messaging channel is treated as admissible for governed work, record:

```text
channel
inbound_scope
outbound_scope
identity_binding
approval_signal_rule
external_send_rule
idempotency_requirement
log_or_trace_expectation
revocation_path
```

### Update gate

An available Hermes update may be shown as a card signal.

It must not trigger installation.

```text
update_available -> review_required
security_update_available -> urgent_review_signal
breaking_update_available -> compatibility_review_required
update_authorized -> human_decision_required
```

### Rollback gate

Rollback visibility is required for consequential runtime activation.

Minimum:

```text
previous_version_known
config_backup_or_recreation_path_known
profile_export_or_recreation_path_known
secrets_not_stored_in_pantheon
rollback_owner_known
```

Rollback availability does not mean rollback is decided.

## OpenWebUI exposure pattern

Allowed cockpit affordances:

```text
show runtime status
show last health probe
show release/update signal
show active approval gates
show risk notes
show evidence references
show provider/model/tool scope
show complete memory posture
show rollback readiness
request human approval
open external docs as references
```

Forbidden cockpit affordances unless a separate approved external adapter exists:

```text
install Hermes
run Hermes setup
enter or store API keys in Pantheon
enable tools
enable gateway channels
update Hermes
rollback Hermes
send external messages
authorize provider routing
promote Hermes memory to Pantheon memory
```

## Relation to existing documents

This document complements:

- `HERMES_INTEGRATION.md` — execution boundary and task-contract bridge.
- `HERMES_RUNTIME_SURFACE_REVIEW.md` — stable identity for the latest reviewed external release surface and adapter decision.
- `HERMES_CAPABILITY_BINDINGS.md` — capability-slot registry for Hermes-side bindings.
- `EXTERNAL_TOOLS_POLICY.md` — external tool and runtime threat review.
- `MODEL_CAPABILITY_PASSPORT.md` — model capability and admissibility classification.
- `CARD_STACK_MODEL.md` — cockpit card grammar.
- `WHAT_RUNS.md` — repository runtime-status honesty map.

If this document conflicts with `STATUS.md`, `WHAT_RUNS.md`, `AUTHORITY_INDEX.md` or `MODULES.md`, the active repository authority path wins.

## Review status

Current decision:

```text
review_result: candidate / to_verify
release_review_owner: HERMES_RUNTIME_SURFACE_REVIEW.md
runtime_impact: none
protected_paths_touched: no
schema_test_ci_impact: documentation and existing ecosystem tests only
external_action: none
memory_behavior: observation contract clarified; no memory operation
approval_behavior: none
```

The useful residue of the setup guide is the runtime-status card and gate vocabulary above. The install recipe itself remains outside Pantheon.
