# AgentTransfer Hermes Artifact Transfer Candidate

Status: candidate support doctrine — Hermes-side artifact-transfer binding note. Repository state: documented non-implemented.
Boundary profile: candidate_support_note.

This document classifies `shehryarsaroya/agenttransfer` as a possible Hermes-side binding for governed artifact transfer between agents, humans and external runtimes.

It does not install AgentTransfer.

It does not add a dependency.

It does not create a Pantheon runtime, installer, scheduler, queue, MCP host, plugin manager, provider router, file-transfer service, storage backend, email relay, approval engine, memory engine, evidence engine, OpenWebUI plugin, Docker file, `.env`, schema, test, operation file or platform service.

## Capability slot

```text
capability_id: agent_artifact_transfer
function: governed transfer of files, artifacts and handoff packages between agents, humans and external runtimes
preferred_binding: shehryarsaroya/agenttransfer
fallback_bindings: none selected
watchlist_bindings: generic object storage + signed URL + notification channel, S3-compatible presigned URL stack, private file gateway
owner_layer: execution runtime / connector gateway / artifact transport
executed_by: Hermes
exposed_by: OpenWebUI / administration cockpit
governed_by: Pantheon
binding_status: candidate
authority_class: candidate support doctrine
repo_state: documented non-implemented
install_status: unknown
health_status: unknown
update_status: unknown
activation_status: unavailable
```

## Why it belongs behind Hermes

AgentTransfer is a transport surface.

It may help Hermes move large artifacts that should not pass through model context: generated files, datasets, model outputs, screen recordings, archive bundles, conversion outputs, render packages, IFC exports, logs, evidence folders and handoff packages.

Pantheon may govern whether such a transfer is allowed, visible, scoped, retained, encrypted, expired or blocked.

Pantheon must not become the file-transfer service.

```text
transport selected != dependency adopted
receipt produced   != evidence validated
hash verified      != content true
message delivered  != human approved
MCP bridge active   != Pantheon MCP host
healthy runtime     != safe transfer
```

## What Pantheon governs

Pantheon governs consequential decisions around the transfer:

- whether the binding may be proposed;
- whether installation may be attempted by Hermes or an operator;
- whether the binding is allowed only in sandbox, project scope or production scope;
- whether open signup is allowed or forbidden;
- which agents, humans, domains and spaces may receive artifacts;
- whether an external human recipient requires explicit approval;
- whether a sensitive artifact requires encryption, redaction, quarantine or refusal;
- whether transfer receipts may be attached to a trace;
- whether transfer status may be shown in OpenWebUI;
- whether an update may be applied;
- whether rollback or suspension is required.

Pantheon records governance state, not bytes.

## What Hermes executes

Hermes may execute the binding if separately installed and approved outside Pantheon:

- signup or identity creation after approval;
- upload and download;
- inbox polling;
- artifact send;
- upload request creation;
- receipt retrieval;
- receipt verification;
- hash verification;
- health probing;
- version probing;
- local MCP bridge calls;
- quarantine routing;
- rollback or suspension commands delegated to the operator.

Hermes execution remains bounded by the task contract and by explicit gates.

## What OpenWebUI exposes

OpenWebUI may show an administration or project card:

```text
AgentTransfer
status: candidate / installed / degraded / suspended
scope: sandbox / project / production
open_signup: allowed / blocked / unknown
external_send: disabled / gated / enabled
encryption_required: yes / no / conditional
latest_receipt: available / missing / unverifiable
storage: unknown / within quota / near limit / exceeded
health: unknown / ready / degraded / unavailable
update: unknown / up_to_date / update_available / review_required
```

The card may expose controls only as requests for governed action. It must not silently execute install, update, send, delete, revoke, expose or promote memory.

## Human approval floor

Human approval is required before:

- installing the binding;
- activating it beyond local sandbox;
- exposing a public domain, DNS record, SMTP listener or outbound relay;
- enabling open signup;
- creating or approving a verified human-owned agent;
- sending any artifact to an external human recipient;
- sending any artifact to an external domain or external instance;
- increasing quotas;
- changing retention or TTL policy;
- disabling encryption requirements;
- applying an update;
- treating a receipt as part of a professional evidence trail.

## Forbidden collapses

This binding must not become:

```text
Pantheon runtime
Pantheon MCP host
Pantheon file store
Pantheon inbox
Pantheon email relay
installer
scheduler
queue
provider router
plugin manager
memory engine
approval engine
evidence engine
source of truth
unrestricted external-send channel
auto-update path
```

## Allowed outputs

AgentTransfer may produce candidates and traces only:

```text
Artifact Transfer Candidate
Artifact Handoff Candidate
Transfer Receipt Trace Candidate
Hash Verification Candidate
Runtime Status Candidate
Capability Gap
Quarantine Signal
External Action Review Signal
```

## Forbidden outputs

AgentTransfer must not produce:

```text
validated truth
professional proof
approval
canonical memory
scope decision
legal delivery status
professional sign-off
safe-status assertion
unapproved external action
```

## Receipt rule

AgentTransfer receipts are useful transport traces.

They are not professional evidence by themselves.

```text
agenttransfer_receipt = transport trace
agenttransfer_receipt != project evidence
agenttransfer_receipt != source validation
agenttransfer_receipt != human approval
agenttransfer_receipt != delivery acceptance
```

A receipt may become a referenced trace in an Evidence Pack Candidate only if Pantheon marks it as transport evidence and keeps the substantive claim separate.

Example:

```text
Allowed:
The file `soil_report_extract.pdf` was transferred to `review-agent` at time T, with hash H.

Not allowed:
The soil report is correct because AgentTransfer produced a receipt.
```

## Risk surfaces

Primary risks:

- sensitive project files leaving the local perimeter;
- link leakage;
- open signup abuse;
- agent identity confusion;
- human-recipient confusion;
- email federation drift;
- DKIM/SPF/TLS misconfiguration;
- attachment malware or poisoned artifact intake;
- unencrypted storage or unmanaged disk retention;
- quota abuse;
- receipts mistaken for proof;
- MCP bridge mistaken for Pantheon runtime;
- spaces mistaken for project scope approval;
- successful download mistaken for professional validation.

## Required gates

```text
install_authorized
activation_authorized
public_exposure_authorized
open_signup_authorized
recipient_authorized
external_send_authorized
human_recipient_authorized
sensitive_artifact_authorized
encryption_policy_checked
retention_policy_checked
receipt_use_authorized
quota_change_authorized
update_authorized
rollback_authorized
```

## Health probes

Permitted status probes, if the binding exists outside Pantheon:

```text
agenttransfer demo
agenttransfer serve local readiness
agenttransfer doctor
whoami / identity check
MCP bridge tool list
upload small artifact
send to sandbox agent
download and sha256 verify
receipt chain verify
storage/quota check
DNS / TLS / SMTP / relay check
open_signup policy check
version check
```

Health probes are runtime state signals only.

```text
health probe passed != safe for production
```

## Default posture for Pantheon Control

```text
binding_status: candidate
install_status: absent_or_unknown
activation_status: unavailable
approval_floor: human approval required before install or activation
external_action: gated
memory_effect: none
proof_effect: none
rollback_status: not_applicable until installed
```

## Capability Slot decision

AgentTransfer is a good candidate for artifact transport because it models a specific missing function: moving large artifacts between agents and humans without pushing bytes through model context.

It should enter the watchlist as:

```text
agent_artifact_transfer -> shehryarsaroya/agenttransfer
```

It should not enter the kernel as a dependency.

It should not be promoted to preferred candidate until a separate reference review verifies:

- installation path;
- local-only mode;
- self-host mode;
- open signup controls;
- receipt verification;
- encryption behavior;
- storage retention;
- artifact deletion/revocation behavior;
- MCP bridge behavior;
- update and rollback path;
- security posture.

## Status

```text
implemented: no
runtime_added: no
dependency_added: no
schemas_added: no
tests_added: no
protected_paths_touched: no
repo_state: documented non-implemented
```

## Final rule

```text
AgentTransfer may transport artifacts.
Hermes may execute the transfer.
OpenWebUI may show the transfer state.
Pantheon governs the gates.
The receipt is a trace, not truth.
The human decides.
```
