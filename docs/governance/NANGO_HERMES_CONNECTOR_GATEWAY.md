# Nango Hermes Connector Gateway

Status: support doctrine — Hermes connector gateway candidate specification, not implemented.
Boundary profile: candidate_support_note.

This document defines how Nango may be considered as a bounded Hermes-side connector gateway for third-party APIs.

It does not install Nango.

It does not configure OAuth providers.

It does not create Nango connections.

It does not add credentials.

It does not install Hermes skills.

It does not create a Pantheon runtime, tool runtime, provider router, scheduler, queue, message bus, MCP layer, plugin manager, connector marketplace, automatic approval mechanism, automatic memory promotion mechanism or OpenWebUI extension.

## Purpose

Nango may be useful when Hermes needs governed access to external APIs without Pantheon becoming a connector runtime or credential store.

Example API domains:

```text
GitHub
Google Drive
Google Calendar
Notion
Slack
Linear
CRM
project-management APIs
internal business systems
```

The capability exists to produce bounded external API actions and reviewable output candidates.

It must not become authority, memory or governance.

## Classification

```text
capability_type: External Connector Gateway
execution_layer: Hermes Agent
connector_layer: Nango
exposure_layer: OpenWebUI
validation_layer: Pantheon Next
status: optional_connector_gateway_candidate
installation_state: not_installed_by_pantheon
credential_state: external_to_pantheon
memory_state: non_canonical
```

## Scope

Allowed scope:

```text
read-only external API retrieval under Task Contract
scoped external API action under explicit approval
external action trace collection
connector capability gap reporting
Evidence Pack Candidate preparation
OpenWebUI consent and result exposure
```

Excluded scope:

```text
Pantheon-owned credential storage
Pantheon-owned connector runtime
Pantheon MCP server
Pantheon scheduler or webhook bus
Pantheon provider router
OpenWebUI direct execution bypassing Hermes
automatic connector activation
automatic external write
automatic memory promotion from API results
automatic approval from successful API response
connector marketplace semantics
```

## Required Task Contract

Any Nango-mediated action requires a Task Contract when the task uses private APIs, account credentials, external writes, schedules, webhooks, MCP/tool exposure, protected files, professional dossier material or memory-sensitive data.

Recommended Task Contract type:

```text
EXTERNAL_CONNECTOR_ACTION
```

Minimal Task Contract fields:

```text
Identity
Intent
Provider
Connection Handle
Scope
Roles
Constraints
Approvals
Expected Evidence
Allowed Outputs
Forbidden Outputs
Memory Rules
Risk Notes
Rollback or Correction Path
```

### Example Task Contract outline

```text
Identity:
  id: TC-NANGO-CONNECTOR-[date]-[provider]-[short-action]
  owner_role: ATHENA
  creation_source: OpenWebUI user request

Intent:
  Perform a bounded external API action through Hermes using Nango as the external connector gateway.

Provider:
  name: [github | google_drive | notion | slack | linear | other]
  environment: [sandbox | project | production]
  connection_handle: [opaque reference only]

Scope:
  included:
    - named account, repository, folder, workspace, channel, project or object set
    - allowed action category
    - allowed time range or resource subset when relevant
  excluded:
    - unrelated accounts
    - unrelated workspaces
    - unrelated projects or dossiers
    - secrets and raw credentials
    - broad cross-project retrieval
    - hidden schedule or webhook execution
    - Registre Probatoire entry mutation

Roles:
  ATHENA: task structure and scope definition
  ARGOS: source, provider, connection and provenance check
  THEMIS: risk, approval and credential boundary review
  HEPHAISTOS: Hermes-side connector call candidate
  APOLLO: result clarity and delivery-readiness review
  IRIS: consent, clarification and user-facing transmission wording
  ZEUS: status arbitration if external effect, memory or protected work is involved

Constraints:
  - no credential values in Pantheon documents
  - no token, secret or API key in Context Pack or Evidence Pack
  - no direct OpenWebUI-to-Nango execution
  - no schedule or webhook unless separately authorized
  - no MCP/tool exposure unless separately authorized
  - no provider-wide access when object-level access is sufficient
  - no memory promotion
  - no doctrine mutation
  - no external write without explicit approval

Approvals:
  - C1 for low-risk read-only capability inspection
  - C2 for read-only retrieval that affects a draft candidate
  - C3 for project mutation candidates or governance-sensitive outputs
  - C4 for external write, communication effect, repository mutation or third-party account change
  - C5 for credentials, self-hosting, provider configuration, webhook/schedule, MCP exposure, irreversible deletion or protected doctrine areas

Expected Evidence:
  - provider name and connection handle label, without secrets
  - action category and resource scope
  - read/write effect classification
  - input summary with sensitive values omitted
  - output summary or artifact reference
  - external action trace or connector log summary
  - risks, limitations and rollback or correction note
  - approval state and user decision status

Allowed Outputs:
  - External API Result Candidate
  - Connector Trace Summary
  - Evidence Pack Candidate
  - Capability Gap
  - Risk Escalation
  - User Decision Gate Candidate

Forbidden Outputs:
  - credential values
  - raw access tokens
  - raw refresh tokens
  - API secrets
  - Registre Probatoire entry
  - automatic approval
  - unreviewed external write
  - hidden scheduled action
  - hidden webhook action
  - MCP route as Pantheon runtime
  - connector catalog as marketplace

Memory Rules:
  - no memory by default
  - API result is Raw Source or Retrieved Knowledge at most
  - Register Candidate only if explicitly requested and evidence-linked
  - connector log is not memory
  - repeated external data does not create memory

Risk Notes:
  - provider scopes may be broader than task need
  - connector output may be partial or stale
  - external API response may be ambiguous
  - write actions may affect third parties
  - credential errors may become security incidents
  - logs may contain sensitive data and need minimization
```

## Hermes-side behavior

Hermes may use Nango only as an external connector gateway under an authorized Task Contract.

Hermes may:

```text
inspect authorized connector capability
perform scoped read-only retrieval
perform approved external write action
summarize connector result
prepare Evidence Pack Candidate
report capability gaps
report approval gaps
report scope gaps
report credential or provider errors without exposing secrets
```

Hermes must not:

```text
create broad provider access because it is convenient
silently expand connector scope
store credentials in Pantheon artifacts
send tokens through prompts
write externally without approval
create schedules or webhooks without separate authorization
expose Nango MCP tools as Pantheon tools
turn connector logs into a Registre Probatoire entry
hide provider errors or permission gaps
```

## Nango object interpretation

| Nango object or surface | Pantheon interpretation |
|---|---|
| Provider integration | External capability surface |
| Connection | Credential handle, not memory |
| OAuth consent | User authorization event requiring scope visibility |
| Action function | External executable capability |
| Sync or scheduled function | Runtime behavior, forbidden by default unless separately governed |
| Webhook trigger | Event bus surface, forbidden by default unless separately governed |
| MCP/tool schema | Agent tool surface, external only, not Pantheon MCP |
| Logs | Runtime trace material that may inform Evidence Pack Candidate |
| Dashboard state | Operational status, not governance truth |

## Evidence Pack Candidate format

A Nango-mediated Hermes action may return an Evidence Pack Candidate with this shape:

```text
Identity:
  evidence_pack_id:
  linked_task_contract:
  produced_by: Hermes Agent / Nango Connector Gateway Candidate
  status: candidate

Provider:
  provider_name:
  connection_handle_label:
  environment:
  credential_values_included: false

Scope:
  included_resources:
  excluded_resources:
  action_category:
  read_write_classification:

Actions:
  - connector capability inspected, if applicable
  - scoped read performed, if applicable
  - external write performed, if explicitly approved
  - result summarized
  - capability gap reported, if applicable

Artifacts:
  - result_reference:
  - connector_trace_summary_reference:
  - output_candidate_reference:

Findings:
  retrieved_or_modified_resource_summary:
  provider_response_summary:
  limitation_notes:
  contradiction_or_uncertainty_notes:

Risks:
  - scope overreach risk
  - credential handling risk
  - external write risk
  - provider freshness or partial-response risk
  - log sensitivity risk
  - rollback or correction risk

Reviews:
  ATHENA:
  ARGOS:
  THEMIS:
  HEPHAISTOS:
  APOLLO:
  IRIS:
  ZEUS:

Register Candidates:
  - none by default

Approval State:
  status: under_review
  required_level:
  user_decision_gate:
  external_action_status:
```

## OpenWebUI workflow

OpenWebUI may expose the workflow as a visible cockpit sequence:

```text
1. User requests an external API action.
2. OpenWebUI shows provider, intended action, data scope and risk class.
3. Pantheon frames or revises a Task Contract.
4. User approves the task boundary when required.
5. Hermes calls Nango inside its own external runtime context.
6. Nango handles provider credentials and external API access outside Pantheon.
7. Hermes returns result candidates and an Evidence Pack Candidate.
8. OpenWebUI displays result, limitations, approval state and User Decision Gate options.
9. Pantheon classifies the output as candidate, under review, rejected, deferred or approved for a narrow use.
10. Any memory proposal, external write, schedule, webhook or connector expansion requires separate approval.
```

OpenWebUI may display:

```text
provider name
requested action
scope summary
risk class
approval prompt
consent status
result candidate
Evidence Pack Candidate
connector limitation note
User Decision Gate options
```

OpenWebUI must not display:

```text
raw access tokens
raw refresh tokens
client secrets
API keys
hidden connector logs with sensitive payloads
Nango dashboard state as governance truth
successful API response as automatic approval
```

## Role activation guidance

Suggested role viewpoints:

| Trigger | Roles |
|---|---|
| simple capability inspection | ATHENA + THEMIS |
| read-only retrieval | ATHENA + ARGOS + HEPHAISTOS |
| draft from retrieved external data | ATHENA + ARGOS + APOLLO |
| external write | ATHENA + THEMIS + HEPHAISTOS + IRIS + ZEUS |
| credential, OAuth or provider scope change | ARGOS + THEMIS + ZEUS |
| schedule, webhook or MCP exposure | ATHENA + THEMIS + ZEUS |
| memory implication from external data | ARGOS + THEMIS + ZEUS |

These are governance viewpoints.

They are not a runtime role team.

## User Decision Gate template

Open a User Decision Gate when the connector action creates a decision beyond bounded retrieval or draft production.

```text
Discord detected

Object of conflict:
The requested Nango-mediated action may read private data, create an external effect, alter provider state, widen credential scope, create a schedule/webhook/tool surface, or influence memory.

Role positions:
- ATHENA: action can be structured if provider, scope and output are explicit.
- ARGOS: provider, connection handle, source provenance and result limits need traceability.
- THEMIS: credentials, scopes, external effects and approval level may block execution.
- HEPHAISTOS: connector action is feasible only inside Hermes, not Pantheon.
- APOLLO: result can be reviewed if limitations and source status stay visible.
- IRIS: external communication or sharing must remain blocked until approved.
- ZEUS: human decision required when write effect, credential scope, memory or protected work is implicated.

Options:
1. Continue as read-only retrieval with narrow scope.
2. Request more provider or scope evidence.
3. Authorize a specific external write.
4. Reject connector use for this task.
5. Open a separate credential, webhook, schedule or MCP review.
6. Open a separate Register Candidate review.

Recommended procedure:
Use Nango as an external connector only. Do not treat connector availability, successful API response or dashboard status as approval.

Decision effects:
- output: candidate unless separately approved
- evidence: may support an Evidence Pack Candidate
- approval: required for external effect or trust boundary change
- memory: none by default
- transmission: blocked unless separately authorized
```

## Activation and deactivation

Recommended status lifecycle:

```text
detected
candidate
sandbox_enabled
project_enabled
task_authorized
suspended
rejected
```

Activation means only:

```text
eligible for task-bound Hermes execution through an external connector gateway under a Task Contract
```

Activation does not mean:

```text
installed by Pantheon
approved globally
available for all projects
authorized for all providers
authorized to write externally
authorized to handle credentials inside Pantheon
authorized to create memory
```

## Security posture

The capability touches external accounts, credentials, private data, provider scopes, third-party systems and potentially irreversible actions.

Minimum security posture:

```text
least privilege by default
read before write
provider scope visible before approval
opaque connection handles only
no credential values in governance artifacts
no raw secrets in Context Pack or Evidence Pack
sandbox before project use
project-specific authorization before production use
separate approval for write actions
separate approval for schedules, webhooks and MCP/tool surfaces
record artifacts and risks in Evidence Pack Candidate
```

## Final rule

```text
Nango is a connector gateway.
Hermes may use it under contract.
Pantheon governs legitimacy.
OpenWebUI exposes the consent and review surface.
```
