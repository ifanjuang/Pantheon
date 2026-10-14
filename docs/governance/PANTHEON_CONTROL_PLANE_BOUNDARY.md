# Pantheon Control Plane Boundary

Status: candidate support doctrine — control-plane boundary. Repository state: documented non-implemented.
Boundary profile: candidate_support_note.

This document clarifies how Pantheon Next may govern operational state for external runtimes without becoming the runtime, installer, scheduler, queue, provider router, MCP host, plugin manager, memory engine or approval engine.

It does not implement runtime code.

It does not install tools.

It does not add schemas.

It does not create operations, platform, Docker, `.env`, service, queue, scheduler, connector runtime, OpenWebUI plugin, Hermes skill or automatic approval mechanism.

## Purpose

Pantheon Control needs to display and qualify the operational state of external runtimes such as Hermes, OpenWebUI-facing adapters, observability layers, Revit local plugins, connector gateways and local capability managers.

The existing doctrine correctly rejects Pantheon as an execution runtime. The missing distinction is:

```text
Knowing status is not executing.
Authorizing a handoff is not executing.
Displaying health is not approval.
Runtime success is not evidence.
```

This document creates a bounded control-plane exception:

```text
Pantheon may govern, display and qualify operational state.
Pantheon must not execute, host, schedule, route or self-maintain operational runtime.
```

## Control plane versus runtime plane

| Layer | May do | Must not do |
|---|---|---|
| Pantheon kernel | define status vocabulary, gates, evidence expectations, approval posture, scope rules and forbidden effects | execute runtime work, install tools, hold secrets, run jobs |
| Pantheon Control | display governed operational state, proposals, gates, gaps, trace references and human decision surfaces | bypass Hermes, call tools directly, auto-approve, auto-promote memory |
| OpenWebUI | expose cards, warnings, decision buttons, logs and status summaries | become authority, bypass Task Contracts, mutate memory silently |
| Hermes / external runtime | install, probe, execute, update, rollback and return reports when authorized | promote canonical memory, approve itself, redefine Pantheon doctrine |

## Allowed governed operational state

Pantheon may store or display these as governance state about an external runtime:

```text
capability_id
binding_id
runtime_owner
install_status
health_status
update_status
activation_status
rollback_status
capability_gap
runtime_trace_ref
last_checked_at
last_reported_version
governance_gate
approval_required
scope_status
risk_status
```

This state is not proof, approval or canonical memory.

## Forbidden executable state

Pantheon Control must not contain or own:

```text
install_command
shell_script
docker_compose_runtime
active_cron
active_queue
worker_process
provider_router_config
raw_secret
raw_access_token
webhook_secret
MCP_server_runtime
browser_runtime
Revit_transaction_executor
auto_update_policy_with_execution
auto_approval_rule
auto_memory_promotion_rule
```

Executable configurations, commands and secrets belong outside Pantheon, in the execution runtime or operator-controlled infrastructure.

## Status vocabulary

### Install status

```text
unknown
absent
proposed
pending_approval
approved_for_sandbox
installing
installed
failed
blocked
suspended
```

### Health status

```text
unknown
ready
degraded
unavailable
error
stale
```

### Update status

```text
unknown
up_to_date
update_available
security_update_available
breaking_update_available
deprecated
abandoned
```

### Activation status

```text
unavailable
detected
sandbox_enabled
project_enabled
production_enabled
suspended
rejected
```

### Rollback status

```text
unknown
not_required
available
not_available
tested
failed
required_before_activation
```

### Governance status

```text
external_reference
candidate
to_verify
approved_for_sandbox
approved_for_project
approved_for_production
blocked
refused
superseded
```

## Non-equivalence rules

The following distinctions are mandatory:

```text
installed != approved
healthy != safe
update_available != update_authorized
runtime_success != evidence
binding_selected != dependency_adopted
trace_record != proof
status_display != approval
capability_visible != capability_enabled
sandbox_enabled != production_approved
```

If a UI card, report, adapter or issue comment collapses one of these distinctions, it creates governance drift.

## Governed execution handoff

Pantheon may issue or record a governed handoff request to Hermes or another execution runtime.

A handoff may contain:

```text
intent
capability_id
binding_id
runtime_target
scope
constraints
approval_state
allowed_outputs
forbidden_outputs
expected_status_report
risk_notes
rollback_expectation
```

A handoff must not contain:

```text
raw secret
install script
unreviewed shell command
auto-run instruction
hidden schedule
unbounded provider access
unscoped external write
memory promotion instruction
approval substitution
```

## Runtime status report

Hermes or another runtime may return a status report.

Pantheon may record and qualify it as:

```text
Runtime Status Candidate
Capability Gap
Trace Summary Candidate
Evidence Pack Candidate support material
User Decision Gate Candidate
```

Pantheon must not treat it as:

```text
Evidence Pack by itself
approval
professional validation
canonical memory
scope authorization
truth
```

## OpenWebUI projection

OpenWebUI may expose:

```text
capability cards
install proposal cards
health cards
update available cards
rollback cards
capability gap cards
trace summary links
approval buttons
risk warnings
human decision surfaces
```

OpenWebUI must not:

```text
directly execute tools bypassing Hermes
turn a card click into automatic installation
hide approval thresholds
hide scope limits
promote a runtime trace into proof
promote repeated observations into memory
```

## Review triggers

A control-plane item requires review when it introduces or changes:

```text
credentials
webhooks
MCP exposure
browser automation
network exposure
external writes
file deletion
save / sync / publish / send effects
model mutation
production activation
auto-update behavior
memory promotion behavior
approval threshold
scope boundary
```

## Relationship to Pantheon Control dashboard boundary

`PANTHEON_CONTROL_BOUNDARY.md` remains the slim boundary for the concrete verification surface named `dashboard/` in monorepo discussions.

This document is broader. It defines the generic governance control-plane rule for external runtime state.

```text
PANTHEON_CONTROL_BOUNDARY.md
= dashboard / verification surface boundary.

PANTHEON_CONTROL_PLANE_BOUNDARY.md
= generic operational control-plane doctrine.
```

The dashboard boundary may verify liveness, logs and install visibility, but it inherits the non-equivalence rules here.

The control-plane doctrine may define status vocabulary and handoff posture, but it does not authorize a concrete dashboard module to gain Docker socket access, repository write access, credentials, runtime authority, approval authority or memory authority.

If the two files conflict, route the conflict through `AUTHORITY_INDEX.md`; neither file may silently override the master authority vocabulary or sensitive-path guardrail.

## Relationship to Revit

Revit is a special local runtime surface because it contains live professional model state. Pantheon may define the capability grammar, profiles and status vocabulary for a Revit local adapter, but model transactions remain inside the Revit plugin / Hermes runtime side.

For local Revit sandbox exploration, see:

```text
docs/governance/PANTHEON_REVIT_LOCAL_SANDBOX_EXCEPTION.md
```

For the first sandbox action contract, see:

```text
docs/governance/PANTHEON_REVIT_FIRST_SANDBOX_ACTION_CONTRACT.md
```

## Relationship to Hermes bindings

Product and repository names should live in the bindings registry, not in generic doctrine.

See:

```text
docs/governance/HERMES_CAPABILITY_BINDINGS.md
```

## Status

```text
implemented: no
runtime_added: no
schemas_added: no
protected_paths_touched: no
repo_state: documented non-implemented
```

## Final rule

```text
Pantheon does not become the engine.
Pantheon becomes the governed dashboard of the engine.
Hermes executes.
The human decides.
Validated state remains.
```
