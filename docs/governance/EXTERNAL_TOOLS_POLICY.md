# External Tools Policy

Status: active support doctrine — external capability review and risk policy.
Boundary profile: active_support_doctrine.

External tools are capabilities.

They are not authority.

They are not governance.

They are not memory.

They are not proof by themselves.

```text
Optional runtime client     -> interaction / exposure only
External runtime / tool PEP -> performs admitted effects
Pantheon Cockpit            -> governed projection
Pantheon Next               -> governance / policy decision
human                       -> consequential decision
```

```text
tool available != tool authorized
runtime success != Evidence
client selected != authority transfer
projection != persistence
```

## 1. Purpose

This document owns the tool-agnostic governance policy for external capabilities, mixed AI workspaces and privileged execution surfaces.

It defines:

- what counts as an external tool;
- effect/risk classes;
- minimum authorization questions;
- least-capability discipline;
- Evidence expectations;
- external-runtime threat review;
- host-control, untrusted-content and prompt-injection posture;
- permission and exposure review;
- safe defaults, revocation and rollback.

It does not define:

- a tool runtime;
- a provider router;
- an installer;
- a plugin manager;
- a scheduler or queue;
- an MCP host;
- a browser-control runtime;
- an observability backend;
- an automatic approval or memory system;
- a product catalogue.

Tool- or project-specific evaluations belong to their reference reviews, capability/binding owners, `WATCHLIST.md`, `DISTILLATION_REGISTRY.md`, `EXTERNAL_TOOL_PLACEMENT_REGISTER.md` or other explicit candidate owners.

Historical inspiration catalogues formerly absorbed into this file remain available in the private Pantheon-Next archive; they are not current policy authority.

## 2. Definition

An external tool is any capability outside Pantheon governance that can materially:

```text
read
retrieve
transform
generate
write
send
publish
delete
install
configure
execute
call another service
alter repository or project state
store or recall information
influence a professional output
```

Examples include:

- web and browser retrieval;
- file/document/spreadsheet/image tools;
- repository tools;
- email, calendar and messaging tools;
- code execution and controlled terminal use;
- MCP servers;
- runtime-client functions, actions, plugins, pipes or pipelines;
- Hermes skills, tools and plugins;
- provider gateways;
- cloud APIs and local services;
- import/export/conversion tools;
- installers and configuration tools;
- connector gateways and browser-control adapters.

A capability being present, installed, reachable or displayed does not make it authorized.

## 3. Core rule

Tool use must be justified by the task and bounded by the applicable governance artifacts.

When a Task Contract or execution admission is required, the tool use must stay within it.

Tool output remains candidate material until its relevant status is reviewed.

```text
tool discovery != adoption
tool installed != approval
tool reachable != authorization
tool output != Evidence
```

## 4. Default posture

Default posture for consequential or insufficiently classified capability use:

```text
not authorized until scope, effect, Evidence and approval requirements are satisfied
```

Low-risk read-only capability may use lighter review when doctrine explicitly permits it.

Uncertainty about effect class must not silently widen authority.

## 5. Effect and risk classes

Risk is classified by possible effect, not product name.

Final approval remains governed by `APPROVALS.md` and the applicable capability/Task Contract path.

### T0 — no external or durable effect

Examples:

```text
local display
formatting without persistence
non-sensitive local transformation
read-only review of already supplied material
```

Expected posture:

```text
low Evidence burden
no durable mutation
no memory promotion
```

### T1 — read-only retrieval

Examples:

```text
web retrieval
repository read
document read
email read
calendar read
bounded Knowledge/source retrieval
```

Expected posture:

```text
source/provenance recorded when material
freshness and coverage considered
sensitive access checked
no write effect
```

### T2 — transformation or candidate generation

Examples:

```text
summarization
classification
diagram draft
document draft
patch draft
local artifact generation
```

Expected posture:

```text
output remains candidate
sources and assumptions recorded when relevant
no automatic external publication
no automatic memory promotion
```

### T3 — governed project/repository mutation candidate

Examples:

```text
repository update candidate
governance document change
project artifact revision
structured-data transformation affecting later decisions
```

Expected posture:

```text
Task Contract normally expected
Evidence Pack / review evidence expected
actual diff or changed-object review
protected-area checks
appropriate approval
rollback path
```

### T4 — external write or communication

Examples:

```text
send email or message
create external calendar event
publish or share artifact
write external system state
delete/archive external content
change live configuration
submit a form
```

Expected posture:

```text
explicit effect and destination
human intent / approval when required
Evidence and exact revision awareness
idempotency when retries can duplicate effects
rollback or correction path
```

### T5 — privileged, irreversible or governance-sensitive effect

Examples:

```text
credential or secret access
production configuration
runtime/plugin/provider installation
provider-routing change
canonical memory/Register promotion
doctrine mutation
protected repository area
irreversible deletion
financial/legal/professional consequence
host administration
```

Expected posture:

```text
explicit narrow scope
strong Evidence requirement
high approval burden
reversibility/mitigation reviewed
no silent or inferred execution
```

## 6. Authorization questions

Before consequential capability use, answer as applicable:

```text
What purpose does the tool serve?
What exact scope may it access?
What effect class can it produce?
What data is exposed?
What source/target is involved?
Can it write or transmit?
Can it affect memory or durable state?
What approval is required?
What Evidence must return?
What is the stop condition?
Can a retry duplicate the effect?
What rollback/mitigation exists?
```

For governed work, these answers belong in the Task Contract, capability/binding qualification, decision gate or Evidence Pack as appropriate.

## 7. Least capability

Use the smallest capability that can satisfy the task.

Prefer:

```text
read before write
bounded scope before broad access
candidate before mutation
local transformation before external write
explicit destination before transmission
explicit approval before consequential effect
source reference before memory proposal
```

Do not use a write-capable or admin-capable tool when a read-only capability is sufficient.

```text
more capability != better governance
```

## 8. Evidence discipline

A tool result that materially supports a decision must remain traceable.

Record as applicable:

```text
capability / binding identity
purpose
source or target
source version / locator
inputs or scope
material actions
output reference
limitations
risk
approval state
technical outcome
```

Tool output must not be self-validating.

```text
command succeeded != claim proven
HTTP 200 != professional success
trace exists != Evidence admitted
```

## 9. Read tools

Read tools may retrieve sources, project data or operational context.

Read access can still be consequential when the material is sensitive, private, stale, privileged or decision-critical.

Read results should preserve statuses such as:

```text
partial
stale
contradicted
unverified
sensitive
private
retrieved_only
coverage_unknown
```

Read access never implies write access.

Absence from a bounded read must not be interpreted as real-world absence unless declared coverage supports that inference.

## 10. Write and mutation tools

Write tools include:

```text
send
publish
create
update
delete
archive
share
commit
configure
install
submit
approve in an external system
```

A write action must not occur merely because a runtime has the button/tool/API available.

Consequential mutation should preserve:

```text
exact target
effect type
approved revision/digest when content matters
Task Contract / decision reference
idempotency key when needed
technical result
changed / unchanged objects when useful
```

```text
prepared != applied
applied != approved
```

## 11. Repository tools

Repository mutation is high risk when it touches canonical doctrine, code, schemas, CI or other protected areas.

Repository mutation requires the applicable protected-path discipline plus:

- scope clarity;
- current-state verification;
- actual diff awareness;
- Evidence/review record;
- rollback/correction awareness;
- approval appropriate to affected authority.

```text
Patch Candidate != merge decision
commit created != doctrine validated
CI green != deployment authorized
```

## 12. Communication tools

Email, chat, calendar, messaging, publication and filing channels create external effects when they reach another party/system.

A consequential send should preserve:

```text
recipient or destination
exact content revision/digest or bounded payload
intent/effect
approval reference when required
idempotency / duplicate-send protection when relevant
send status / technical outcome
```

```text
drafted != sent
sent != true
channel proximity != approval
```

## 13. Code and terminal tools

Code execution and controlled shell/terminal use belong to the external execution environment.

They must not turn Pantheon into an execution runtime.

They must not bypass repository, host, secret or capability policy.

Installation, privileged commands, dependency changes or service configuration require separate authorization appropriate to their effect.

## 14. MCP, gateways, plugins and provider-facing tools

MCP servers, connector gateways, plugins and provider/model surfaces are external capability bindings.

Pantheon may govern:

- eligibility;
- scope;
- binding qualification;
- allowed effects;
- Evidence expectations;
- approval requirements.

Pantheon must not become their hidden router, scheduler, dispatcher or installer.

```text
MCP tool listed != MCP tool authorized
plugin loaded != plugin adopted
provider configured != data exposure approved
```

## 15. Installation and configuration

Installation/configuration can alter runtime behavior, tool reach, security posture and external effects.

It is privileged by default when it changes a consequential runtime.

Pantheon must not automatically install external runtimes, clients, skills, plugins, providers or services merely because a candidate review accepts their conceptual placement.

```text
review accepted != installed
installed != activated
activated != task-authorized
```

## 16. Memory-affecting tools

Any capability that stores, indexes, retrieves, ranks, summarizes, synchronizes or edits long-lived information has memory implications.

Runtime/client memory remains distinct from Pantheon governed retention.

Such tools may produce Register Candidates when explicitly allowed.

They must not promote a Registre Probatoire entry automatically.

```text
stored != remembered by Pantheon
recalled != verified
repeated != promoted
```

## 17. Secrets and private data

Secrets, credentials, tokens, private data and sensitive professional information require strict minimization and custody boundaries.

External tools must not expose secrets in:

- prompts;
- client-visible traces;
- Evidence Packs;
- public artifacts;
- repository files;
- ordinary logs.

If secret exposure is suspected, treat it as a security incident/capability risk, not a normal Evidence Item.

Credential availability never grants task authorization.

## 18. External runtime review

A fuller external-runtime review is required when a runtime, client, mixed workspace, plugin/tool host or connector surface can materially touch:

```text
private/client material
professional source interpretation
repository/project files
email/calendar/messaging
long-lived memory or recall
provider/model selection
scheduled/background tasks
runtime installation/configuration
privileged local/host surfaces
MCP/gateway/connector access
external publication or mutation
```

The review asks:

```text
What consequential power does this surface expose,
and which Pantheon gate constrains it?
```

A low-risk, read-only, non-consequential surface may use a lighter review.

## 19. Review record

A review may use the following conceptual record or an equivalent governed template:

```yaml
external_runtime_review:
  runtime_name:
  reviewed_ref:
  reviewed_date:
  reviewed_by:
  system_role: exposure_surface | execution_runtime | observability_layer | connector_gateway | model_runtime | mixed_workspace | other
  binding_status: unbound | candidate | sandbox | project_scoped | organization_scoped | refused
  privileged_capabilities:
  data_access:
  external_effects:
  memory_effects:
  model_effects:
  scheduling_effects:
  host_control_surface:
  untrusted_content_paths:
  prompt_injection_posture:
  permission_granularity:
  exposure_posture:
  auditability:
  reversibility_or_mitigation:
  pantheon_gate_required:
  approval_ceiling:
  evidence_expectation:
  safe_default:
  decision: accepted | refused | to_verify | to_arbitrate
```

This is review information, not installation or runtime authorization.

The reusable candidate template may live outside this policy; template conformance does not make a runtime accepted.

## 20. Host-control surface

Host-control power is stronger than ordinary tool availability.

Use a vocabulary such as:

```text
none
scoped_filesystem
broad_filesystem
shell_user
shell_admin
container_host_control
remote_host_control
cloud_admin
```

Default posture:

```text
none                  -> ordinary capability review
scoped_filesystem     -> review scope/minimization
broad_filesystem      -> high risk
shell_user            -> high risk
shell_admin           -> critical risk
container_host_control-> critical risk
remote_host_control   -> critical risk
cloud_admin           -> critical risk
```

Critical host-control power requires, at minimum:

```text
explicit bounded scope
explicit approval path
strong Evidence expectation
isolation/sandbox posture when relevant
reversibility or mitigation
human-visible gate before consequential use
```

A runtime profile or client setting is not OS isolation.

## 21. Untrusted-content paths

Review untrusted data paths such as:

```text
web results
fetched pages
uploaded files
email bodies
notes
runtime memory
retrieved knowledge
connector output
MCP output
model output reused as context
third-party tool output
```

Core rule:

```text
Untrusted content enters as data.
It does not become instruction, proof, approval or memory by proximity.
```

An external adapter may wrap, delimit or sanitize content. Pantheon governs the requirement and the returned status; it does not implement the adapter merely by documenting the rule.

## 22. Prompt-injection posture

A reviewed execution/client surface should distinguish, where applicable:

```text
trusted operator/system instruction
Pantheon governance artifact
external source content
retrieved memory/knowledge
connector/tool output
model-generated content
```

If a runtime cannot preserve those distinctions, consequential outputs require a stricter posture or the binding must remain refused/limited.

```text
content says "do X" != X authorized
```

## 23. Permission granularity

Record whether permissions are approximately:

```text
coarse
role_based
capability_scoped
task_scoped
dossier_scoped
unknown
```

Coarse permissions are not automatically forbidden, but they increase exposure and approval burden.

The runtime/PEP must still constrain each consequential action to the admitted task/effect.

## 24. Exposure posture

Distinguish deployment exposure such as:

```text
local_only
private_network
vpn_or_tunnel
reverse_proxy
public_internet
unknown
```

Exposure state is risk information.

It does not authorize use.

Public or unknown exposure can block sensitive professional use until appropriately qualified.

## 25. Runtime clients and Hermes WebUI

A runtime client is one possible external capability surface.

It may expose chat, workspace files, session state, runtime controls, tool cards, attachments or runtime-side approval affordances.

Those features are reviewed under the same policy as any other capability.

Hermes WebUI is one optional/proposed client. If selected, its actual deployment/runtime behavior must be qualified rather than assumed from its UI role.

```text
Hermes WebUI available != Hermes WebUI selected
Hermes WebUI selected != Pantheon authority transferred
runtime approval card != human Pantheon approval
client workspace access != source admission
```

Pantheon Cockpit remains the governed projection owner for Cards, Evidence gaps, decisions and status. It is not a substitute generic runtime client.

## 26. PDP / PEP relationship

Pantheon policy decisions are data.

The external runtime/adapter that can cause the effect remains the Policy Enforcement Point.

For consequential effects, the PEP is responsible for enforcing the applicable policy/gate immediately before the effect and for fail-closed behavior when required policy is unavailable.

```text
PDP allow != effect executed
PEP executed != Evidence
technical success != professional acceptance
```

The protected HTTP policy contract is documented in `mcp-server/docs/HTTP_API_CONTRACT.md`.

## 27. Review outcomes

Useful outcomes include:

```text
accepted_for_reference
accepted_for_sandbox
accepted_for_adapter_design
accepted_for_project_scoped_use
needs_more_evidence
needs_sandbox
needs_adapter
needs_human_approval
blocked
refused
```

An accepted review outcome may justify continued evaluation or an adapter design.

It does not automatically install, activate or task-authorize a capability.

## 28. Safe defaults

If capability review is incomplete:

```text
no external effect
no canonical effect
no memory promotion
no privileged execution
no sensitive client-data use
candidate-only output
surface the Capability Gap
```

When a safer read-only or draft-only mode exists, prefer it over silent failure or broader authority.

## 29. Revocation and rollback

Tool/binding qualification can be revoked or narrowed.

A capability may be blocked when it becomes:

- unsafe;
- stale;
- misconfigured;
- overbroad;
- unreviewable;
- incompatible with current doctrine;
- unexpectedly more privileged;
- operationally different from its reviewed artifact.

For consequential capability use, rollback or mitigation should be considered before execution.

```text
previously qualified != permanently qualified
```

## 30. External inspiration and adoption boundary

External projects, methods and repositories may inform Pantheon but do not govern it.

Their detailed comparison belongs outside this policy in the relevant watchlist, reference review, distillation or capability owner.

Before adopting a concrete external tool, ask:

```text
Does it solve a demonstrated need?
Can an existing owner/binding already solve it?
Can it remain optional and replaceable?
Does it preserve source/Evidence/approval/memory distinctions?
What consequential effects can it produce?
Can the PEP enforce the required gates?
What does rollback look like?
```

Do not add a component merely because its architecture is interesting.

## 31. Forbidden drift

External-tool governance must never become:

- a tool runtime;
- provider router;
- automatic installer;
- unrestricted plugin manager;
- hidden workflow runner;
- scheduler or queue;
- autonomous execution engine;
- automatic skill installer;
- automatic memory promoter;
- self-evolution loop;
- approval bypass;
- product-specific UI authority;
- a catalogue that silently selects dependencies.

If tool availability becomes authorization, the boundary has failed.

If a runtime or client can canonize memory/doctrine by itself, the boundary has failed.

If Pantheon must execute the tool to govern the tool, the placement boundary has failed.

## 32. Final invariants

```text
external capability != authority
tool available != tool authorized
read != write
write prepared != write approved
runtime output != Evidence
trace != proof
retrieved != true
runtime/client memory != Registre Probatoire
client selected != authority transfer
projection != persistence
PDP decision != PEP execution
runtime success != professional acceptance
```

External tools may extend reach. Pantheon governs the conditions and status of that reach without becoming the execution engine.
