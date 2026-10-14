# Hermes Installation Assistance

Status: candidate support doctrine — Hermes installation assistance and read-only check pattern. Repository state: documented non-implemented.
Boundary profile: candidate_support_note.

## Purpose

This document defines how Pantheon Next may help a human prepare, check and review a Hermes Agent installation without becoming the installer.

It covers:

```text
pre-install readiness
installation plan assistance
human-run command candidates
post-install status capture
health-signal interpretation
activation gates
rollback readiness
```

It does not install Hermes.
It does not run commands.
It does not store secrets.
It does not configure providers.
It does not enable tools or gateways.
It does not update or roll back Hermes.
It does not declare the runtime safe.

## Boundary

```text
exposed_by:
  OpenWebUI or another cockpit surface may expose installation-assistance cards,
  readiness questions, checklists, command candidates, risk notes and status reports.

executed_by:
  The human, operating system, terminal, package manager, Hermes installer or
  external runtime performs installation and checks outside Pantheon.

governed_by:
  Pantheon governs the assistance boundary, admissible checks, required evidence,
  approval gates, status vocabulary, scope, secret handling and rollback posture.

approved_by:
  The human approves installation, local command execution, provider configuration,
  tool activation, gateway exposure, update and rollback.

forbidden:
  Pantheon must not become an installer, shell runner, secret store, auto-configurator,
  provider router, Tool Gateway controller, update runner, rollback runner, runtime
  health oracle or approval shortcut.
```

Non-equivalence rules apply: see `docs/governance/NON_EQUIVALENCE_RULES.md`.

Local distinctions:

```text
install_plan != install_authorization
command_candidate != command_executed
command_executed != approved_installation
health_probe != safe_runtime
setup_complete != activation_authorized
api_key_present != secret_governed
model_reachable != model_approved
rollback_path_known != rollback_decided
```

## Assistance modes

### 1. Pre-install readiness

Pantheon may help collect the minimum environment facts before any install proposal:

```text
host_name_or_alias:
os_family: macos | linux | windows | wsl | unknown
installation_target: local_machine | server | container | vm | unknown
privilege_level_needed: none | user | admin | sudo | unknown
python_available: yes | no | unknown
node_available: yes | no | unknown
git_available: yes | no | unknown
docker_available: yes | no | not_applicable | unknown
network_policy_known: yes | no | unknown
secret_storage_policy_known: yes | no | unknown
rollback_expectation_known: yes | no | unknown
```

These fields are declarations or observations. They do not authorize installation.

### 2. Installation plan assistance

Pantheon may produce an installation plan candidate.

Allowed content:

```text
chosen_installation_path
source_reference
prerequisites_to_check
human-run command candidates
expected_outputs
known_risks
stop_conditions
rollback_preparation
approval_required_before_next_step
```

Forbidden content:

```text
auto-run command
secret capture
silent dependency installation
provider auto-selection
tool auto-enablement
gateway auto-exposure
health-to-safety conclusion
```

### 3. Human-run command candidates

Pantheon may display command candidates only as copyable review material.

Required label:

```text
Command Candidate — not executed by Pantheon.
Review before running in your terminal.
```

Each command candidate should carry:

```text
purpose
source
expected_effect
expected_output
risk_level
requires_admin: yes | no | unknown
writes_files: yes | no | unknown
network_access: yes | no | unknown
secrets_required: yes | no | unknown
rollback_note
approval_before_run: required
```

Command candidates that touch secrets, shell profiles, global package managers, Docker, services, launch agents, systemd, firewall, browser automation, messaging channels or production directories require elevated approval.

### 4. Post-install status capture

Pantheon may ask the human to paste outputs from external checks.

Allowed inputs:

```text
version output
health check output
configuration summary with secrets redacted
provider list with secrets redacted
tool list
gateway status
profile list
log excerpt without secrets
error message
```

Pantheon may classify the result as:

```text
not_checked
observed_ready
observed_degraded
observed_failed
blocked_by_missing_dependency
blocked_by_missing_secret_policy
blocked_by_provider_binding
blocked_by_gateway_risk
blocked_by_rollback_gap
to_verify
```

A pasted output remains a source candidate until reviewed.

## Installation Assistance Card

Minimum card shape:

```text
card_id: hermes_installation_assistance
card_type: installation_assistance_card
runtime: Hermes Agent
assistance_status: not_started | collecting_context | plan_candidate | waiting_human_run | output_review | blocked | ready_for_activation_review
host_context:
  os_family:
  install_target:
  privilege_level:
installation_path_candidate:
source_refs:
command_candidates:
redaction_required: true
secret_policy:
  pantheon_stores_secrets: false
  secret_owner:
  redaction_rule:
status_checks:
  version_check:
  health_check:
  provider_check:
  tool_surface_check:
  gateway_check:
  profile_check:
rollback_readiness:
open_gates:
risk_notes:
evidence_refs:
human_decision_refs:
```

The card is a decision and review surface. It is not an installer.

## Check taxonomy

### Preflight checks

Preflight checks answer whether the installation plan is coherent enough to propose.

```text
source_check
host_context_check
permission_check
dependency_check
network_check
secret_policy_check
provider_binding_check
rollback_check
scope_check
```

Output:

```text
preflight_result: pass | pass_with_warnings | fail | to_verify
```

Preflight pass does not authorize installation.

### Post-install checks

Post-install checks answer whether an externally installed Hermes instance appears technically reachable and classifiable.

```text
version_observed
binary_or_entrypoint_observed
health_probe_observed
config_location_observed
provider_binding_observed
tool_surface_observed
gateway_surface_observed
profile_surface_observed
log_path_observed
rollback_path_observed
```

Output:

```text
post_install_result: observed_ready | degraded | failed | incomplete | to_verify
```

Post-install ready does not mean safe, approved or activated.

### Activation checks

Activation checks answer whether the runtime may be enabled for a bounded use case.

```text
task_scope_declared
provider_approved
tool_surfaces_approved
gateway_exposure_approved
secret_policy_approved
evidence_return_path_known
rollback_owner_known
human_approval_recorded
```

Output:

```text
activation_recommendation: activate_sandbox | activate_project | keep_disabled | block | to_arbitrate
```

Only the human decision can activate consequential use.

## Stop conditions

Pantheon assistance must stop and request review when:

```text
secret requested without redaction policy
command requires elevated privileges unexpectedly
installer source is ambiguous
install path writes outside expected scope
provider binding is unclear
gateway channel may expose external messages
browser or terminal tool is enabled by default
rollback path is unknown
health probe fails
output contains private data or secrets
human asks Pantheon to run commands directly
```

## Evidence expected

A complete installation-assistance dossier may include:

```text
source reference
selected installation path
human approval for installation attempt
command candidates shown
human-declared commands run
redacted outputs pasted
status classification
open risks
rollback readiness
activation decision or activation gap
```

It should not include raw API keys, tokens, private SSH keys, unredacted `.env` files or unrelated host logs.

## Relation to Hermes Runtime Governance

`HERMES_RUNTIME_GOVERNANCE.md` defines the runtime Capability Slot and runtime card.

This document defines the assistance layer around installation and checks.

```text
Runtime Governance -> what Hermes is allowed to mean in Pantheon.
Installation Assistance -> how Pantheon may help the human inspect and prepare it.
Hermes / OS / human -> what actually installs and runs.
```

## Review status

Current decision:

```text
review_result: candidate / to_verify
runtime_impact: none
protected_paths_touched: no
schema_test_ci_impact: none
external_action: none
memory_behavior: none
approval_behavior: none
```
